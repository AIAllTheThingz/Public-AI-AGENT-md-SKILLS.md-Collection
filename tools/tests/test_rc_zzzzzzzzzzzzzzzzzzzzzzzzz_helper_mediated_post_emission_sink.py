from __future__ import annotations

import ast
import json
import unittest

import rc_finding_code_contracts_base as base
import test_rc_finding_helper_mutations as helper_mutations
import test_rc_zzz_finding_emission_sink as sink_execution
import test_rc_zzzz_sink_rebinding_and_parameterized_multiplicity as sink_state
import test_rc_zzzzzzzzzzzzzzzzzzzz_post_emission_sink_and_codeowners as post_sink
import test_rc_zzzzzzzzzzzzzzzzzzzzzzzz_class_construction_execution as _class_execution  # noqa: F401


# A published Finding can be emitted correctly and then erased indirectly by a
# same-module helper. The earlier post-emission sink layer intentionally tracked
# only direct/alias receiver mutations, so calls such as erase(findings), where
# erase() performs items.clear(), were invisible to the compatibility contract.

_previous_sink_contract = sink_execution._emission_sink_contract


def _module_for(node: ast.AST, parents: dict[int, ast.AST]) -> ast.Module | None:
    current = node
    while id(current) in parents:
        current = parents[id(current)]
    return current if isinstance(current, ast.Module) else None


def _helper_definitions(module: ast.Module) -> dict[str, ast.FunctionDef | ast.AsyncFunctionDef]:
    return {
        statement.name: statement
        for statement in module.body
        if isinstance(statement, (ast.FunctionDef, ast.AsyncFunctionDef))
    }


def _parameter_receiver(parameter: str) -> ast.Name:
    return ast.Name(id=parameter, ctx=ast.Load())


def _aliases_for_parameter(
    helper: ast.FunctionDef | ast.AsyncFunctionDef,
    parameter: str,
    parents: dict[int, ast.AST],
    cutoff: int,
) -> set[str]:
    return sink_state._receiver_aliases_before(
        helper,
        _parameter_receiver(parameter),
        parents,
        cutoff,
    )


def _direct_destructive_parameters(
    helper: ast.FunctionDef | ast.AsyncFunctionDef,
    parents: dict[int, ast.AST],
) -> set[str]:
    parameters = set(helper_mutations._parameter_names(helper))
    destructive: set[str] = set()

    for item in ast.walk(helper):
        if not sink_state._belongs_to_function(item, helper, parents):
            continue
        line = getattr(item, "lineno", 0)
        if line <= 0:
            continue

        for parameter in parameters:
            receiver = _parameter_receiver(parameter)
            aliases = _aliases_for_parameter(helper, parameter, parents, line + 1)

            if isinstance(item, ast.Assign):
                if any(
                    not isinstance(target, ast.Name)
                    and sink_state._target_touches_receiver(target, receiver, aliases)
                    for target in item.targets
                ):
                    destructive.add(parameter)
            elif isinstance(item, ast.AnnAssign):
                if (
                    not isinstance(item.target, ast.Name)
                    and sink_state._target_touches_receiver(item.target, receiver, aliases)
                ):
                    destructive.add(parameter)
            elif isinstance(item, ast.AugAssign):
                if sink_state._target_touches_receiver(item.target, receiver, aliases):
                    destructive.add(parameter)
            elif isinstance(item, ast.Delete):
                if any(
                    sink_state._target_touches_receiver(target, receiver, aliases)
                    for target in item.targets
                ):
                    destructive.add(parameter)
            elif (
                isinstance(item, ast.Call)
                and isinstance(item.func, ast.Attribute)
                and sink_state._root_name(item.func.value) in aliases
                and item.func.attr in sink_state._DESTRUCTIVE_SINK_METHODS
            ):
                destructive.add(parameter)

    return destructive


def _destructive_parameters(
    helper: ast.FunctionDef | ast.AsyncFunctionDef,
    helpers: dict[str, ast.FunctionDef | ast.AsyncFunctionDef],
    parents: dict[int, ast.AST],
    stack: frozenset[str] = frozenset(),
) -> set[str]:
    destructive = _direct_destructive_parameters(helper, parents)
    if helper.name in stack:
        return destructive

    next_stack = stack | {helper.name}
    parameters = helper_mutations._parameter_names(helper)

    for call in ast.walk(helper):
        if not (
            isinstance(call, ast.Call)
            and isinstance(call.func, ast.Name)
            and sink_state._belongs_to_function(call, helper, parents)
        ):
            continue
        callee = helpers.get(call.func.id)
        if callee is None or callee is helper:
            continue

        callee_destructive = _destructive_parameters(callee, helpers, parents, next_stack)
        if not callee_destructive:
            continue

        line = getattr(call, "lineno", 0)
        for callee_parameter in callee_destructive:
            arguments = helper_mutations._argument_for_parameter(
                call,
                callee,
                callee_parameter,
            )
            for parameter in parameters:
                aliases = _aliases_for_parameter(helper, parameter, parents, line + 1)
                if any(base.loaded_names(argument) & aliases for argument in arguments):
                    destructive.add(parameter)

    return destructive


def _relevant_helper_semantics(
    helper: ast.FunctionDef | ast.AsyncFunctionDef,
    helpers: dict[str, ast.FunctionDef | ast.AsyncFunctionDef],
    parents: dict[int, ast.AST],
    stack: frozenset[str] = frozenset(),
) -> dict[str, object]:
    if helper.name in stack:
        return {"helper": helper.name, "recursive": True}

    next_stack = stack | {helper.name}
    payload: dict[str, object] = {
        "helper": helper.name,
        "semantics": helper_mutations._helper_semantics(helper),
    }
    callees: list[dict[str, object]] = []
    helper_parameters = helper_mutations._parameter_names(helper)

    for call in ast.walk(helper):
        if not (
            isinstance(call, ast.Call)
            and isinstance(call.func, ast.Name)
            and sink_state._belongs_to_function(call, helper, parents)
        ):
            continue
        callee = helpers.get(call.func.id)
        if callee is None or callee is helper:
            continue

        destructive = _destructive_parameters(callee, helpers, parents, next_stack)
        if not destructive:
            continue

        line = getattr(call, "lineno", 0)
        touches_helper_parameter = False
        for callee_parameter in destructive:
            arguments = helper_mutations._argument_for_parameter(
                call,
                callee,
                callee_parameter,
            )
            for helper_parameter in helper_parameters:
                aliases = _aliases_for_parameter(
                    helper,
                    helper_parameter,
                    parents,
                    line + 1,
                )
                if any(base.loaded_names(argument) & aliases for argument in arguments):
                    touches_helper_parameter = True
                    break
            if touches_helper_parameter:
                break

        if touches_helper_parameter:
            callees.append(
                {
                    "call": base.canonical_ast(call),
                    "callee": _relevant_helper_semantics(
                        callee,
                        helpers,
                        parents,
                        next_stack,
                    ),
                }
            )

    if callees:
        payload["destructiveCallees"] = sorted(
            callees,
            key=lambda item: json.dumps(item, sort_keys=True),
        )
    return payload


def _helper_sink_effect(
    call: ast.Call,
    receiver_aliases: set[str],
    helpers: dict[str, ast.FunctionDef | ast.AsyncFunctionDef],
    parents: dict[int, ast.AST],
) -> dict[str, object] | None:
    if not isinstance(call.func, ast.Name):
        return None
    helper = helpers.get(call.func.id)
    if helper is None:
        return None

    destructive = _destructive_parameters(helper, helpers, parents)
    if not destructive:
        return None

    helper_parameters = helper_mutations._parameter_names(helper)
    matched_positions: set[int] = set()
    for parameter in destructive:
        arguments = helper_mutations._argument_for_parameter(call, helper, parameter)
        if any(base.loaded_names(argument) & receiver_aliases for argument in arguments):
            if parameter in helper_parameters:
                matched_positions.add(helper_parameters.index(parameter))

    if not matched_positions:
        return None

    return {
        "call": base.canonical_ast(call),
        "destructiveParameterPositions": sorted(matched_positions),
        "helperSemantics": _relevant_helper_semantics(helper, helpers, parents),
    }


def _post_emission_helper_history(
    node: ast.Call,
    receiver: ast.AST,
    parents: dict[int, ast.AST],
) -> list[str]:
    function = sink_state._enclosing_function(node, parents)
    module = _module_for(node, parents)
    if function is None or module is None:
        return []

    helpers = _helper_definitions(module)
    cutoff = getattr(node, "lineno", 10**9)
    changes: list[tuple[int, int, str]] = []

    for item in ast.walk(function):
        if not (
            isinstance(item, ast.Call)
            and isinstance(item.func, ast.Name)
            and sink_state._belongs_to_function(item, function, parents)
        ):
            continue
        line = getattr(item, "lineno", 0)
        if line <= cutoff:
            continue
        if not post_sink._can_share_execution_path(node, item, function, parents):
            continue

        aliases = sink_state._receiver_aliases_before(
            function,
            receiver,
            parents,
            line + 1,
        )
        effect = _helper_sink_effect(item, aliases, helpers, parents)
        if effect is None:
            continue

        changes.append(
            (
                line,
                getattr(item, "col_offset", 0),
                json.dumps(
                    {
                        "context": sink_state._sink_state_context(
                            item,
                            function,
                            parents,
                        ),
                        "operation": effect,
                    },
                    sort_keys=True,
                ),
            )
        )

    changes.sort()
    return [value for _, _, value in changes]


def _emission_sink_contract_with_helper_post_state(
    node: ast.Call,
    parents: dict[int, ast.AST],
) -> list[str]:
    contract = list(_previous_sink_contract(node, parents))
    receiver = sink_state._finding_sink_receiver(node, parents)
    if receiver is None:
        return contract

    helper_state = _post_emission_helper_history(node, receiver, parents)
    if helper_state:
        contract.append(
            "post-helper-receiver-state:"
            + json.dumps(helper_state, sort_keys=True)
        )
    return contract


sink_execution._emission_sink_contract = _emission_sink_contract_with_helper_post_state


class ReleaseCandidateHelperMediatedPostEmissionSinkTests(unittest.TestCase):
    def test_helper_mediated_clear_after_emission_changes_contract(self) -> None:
        emitted = '''
def validate(findings):
    findings.append(Finding("PUBLIC_CODE", "visible"))
'''
        helper_cleared = '''
def erase(items):
    items.clear()

def validate(findings):
    findings.append(Finding("PUBLIC_CODE", "visible"))
    erase(findings)
'''
        expected = base.finding_semantic_signatures(emitted)
        actual = base.finding_semantic_signatures(helper_cleared)
        self.assertNotEqual(expected, actual)
        sink = json.loads(actual["PUBLIC_CODE"][0])["sink"]
        self.assertTrue(
            any(item.startswith("post-helper-receiver-state:") for item in sink),
            sink,
        )

    def test_helper_body_change_to_destructive_mutation_changes_contract(self) -> None:
        safe = '''
def erase(items):
    return len(items)

def validate(findings):
    findings.append(Finding("PUBLIC_CODE", "visible"))
    erase(findings)
'''
        destructive = safe.replace("    return len(items)\n", "    items.clear()\n")
        safe_payload = json.loads(
            base.finding_semantic_signatures(safe)["PUBLIC_CODE"][0]
        )
        destructive_payload = json.loads(
            base.finding_semantic_signatures(destructive)["PUBLIC_CODE"][0]
        )
        self.assertNotEqual(safe_payload["sink"], destructive_payload["sink"])

    def test_transitive_helper_destruction_is_tracked(self) -> None:
        direct = '''
def validate(findings):
    findings.append(Finding("PUBLIC_CODE", "visible"))
'''
        transitive = '''
def wipe(items):
    items.clear()

def erase(items):
    wipe(items)

def validate(findings):
    findings.append(Finding("PUBLIC_CODE", "visible"))
    erase(findings)
'''
        self.assertNotEqual(
            base.finding_semantic_signatures(direct),
            base.finding_semantic_signatures(transitive),
        )

    def test_additive_helper_mutation_does_not_destroy_existing_sink(self) -> None:
        original = '''
def validate(findings):
    findings.append(Finding("PUBLIC_CODE", "visible"))
'''
        additive = '''
def add_note(items):
    items.append("note")

def validate(findings):
    findings.append(Finding("PUBLIC_CODE", "visible"))
    add_note(findings)
'''
        expected_sink = json.loads(
            base.finding_semantic_signatures(original)["PUBLIC_CODE"][0]
        )["sink"]
        actual_sink = json.loads(
            base.finding_semantic_signatures(additive)["PUBLIC_CODE"][0]
        )["sink"]
        self.assertEqual(expected_sink, actual_sink)

    def test_mutually_exclusive_helper_clear_does_not_freeze_contract(self) -> None:
        original = '''
def validate(findings, enabled):
    if enabled:
        findings.append(Finding("PUBLIC_CODE", "visible"))
'''
        exclusive = '''
def erase(items):
    items.clear()

def validate(findings, enabled):
    if enabled:
        findings.append(Finding("PUBLIC_CODE", "visible"))
    if not enabled:
        erase(findings)
'''
        expected_sink = json.loads(
            base.finding_semantic_signatures(original)["PUBLIC_CODE"][0]
        )["sink"]
        actual_sink = json.loads(
            base.finding_semantic_signatures(exclusive)["PUBLIC_CODE"][0]
        )["sink"]
        self.assertEqual(expected_sink, actual_sink)


if __name__ == "__main__":
    unittest.main()
