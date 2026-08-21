from __future__ import annotations

import ast
import copy
import json
import unittest

import rc_finding_code_contracts_base as base
import test_rc_finding_helper_mutations as helper_mutations
import test_rc_zzzzzzzzzzzzzzzzzzzzzzzzz_helper_mediated_post_emission_sink as helper_sink


# Module-level callables are not limited to def/async def.  An assigned lambda or
# a simple alias to one can erase the published finding sink just as effectively
# as a named helper.  Extend the composed post-emission scanner without changing
# the earlier checkpoint layers.

_original_helper_definitions = helper_sink._helper_definitions


def _helper_definitions(module: ast.Module) -> dict[str, ast.AST]:
    helpers: dict[str, ast.AST] = dict(_original_helper_definitions(module))
    aliases: dict[str, str] = {}

    def bind(name: str, value: ast.AST) -> None:
        if isinstance(value, ast.Lambda):
            helpers[name] = value
        elif isinstance(value, ast.Name):
            aliases[name] = value.id

    for statement in module.body:
        if isinstance(statement, ast.Assign):
            for target in statement.targets:
                if isinstance(target, ast.Name):
                    bind(target.id, statement.value)
        elif (
            isinstance(statement, ast.AnnAssign)
            and isinstance(statement.target, ast.Name)
            and statement.value is not None
        ):
            bind(statement.target.id, statement.value)

    # Resolve simple module-level callable aliases transitively.  Python requires
    # the referenced callable to exist when the assignment executes, but the AST
    # inventory can safely resolve from the complete module definition map.
    pending = dict(aliases)
    while pending:
        progress = False
        for name, target in list(pending.items()):
            resolved = helpers.get(target)
            if resolved is not None:
                helpers[name] = resolved
                del pending[name]
                progress = True
        if not progress:
            break

    return helpers


def _helper_label(helper: ast.AST, helpers: dict[str, ast.AST]) -> str:
    names = sorted(name for name, candidate in helpers.items() if candidate is helper)
    if names:
        return names[0]
    return getattr(helper, "name", "<callable>")


def _callable_semantics(helper: ast.AST) -> str:
    if not isinstance(helper, ast.Lambda):
        return helper_mutations._helper_semantics(helper)

    # Re-express a lambda as a synthetic function solely for alpha-normalization,
    # so a private parameter rename does not become a compatibility break.
    synthetic = ast.FunctionDef(
        name="_helper",
        args=copy.deepcopy(helper.args),
        body=[ast.Return(value=copy.deepcopy(helper.body))],
        decorator_list=[],
        returns=None,
        type_comment=None,
    )
    ast.fix_missing_locations(synthetic)
    return base.normalized_semantic_ast(synthetic)


def _destructive_parameters(
    helper: ast.AST,
    helpers: dict[str, ast.AST],
    parents: dict[int, ast.AST],
    stack: frozenset[int] = frozenset(),
) -> set[str]:
    destructive = helper_sink._direct_destructive_parameters(helper, parents)
    identity = id(helper)
    if identity in stack:
        return destructive

    next_stack = stack | {identity}
    parameters = helper_mutations._parameter_names(helper)

    for call in ast.walk(helper):
        if not (
            isinstance(call, ast.Call)
            and isinstance(call.func, ast.Name)
            and helper_sink.sink_state._belongs_to_function(call, helper, parents)
        ):
            continue
        callee = helpers.get(call.func.id)
        if callee is None or callee is helper:
            continue

        callee_destructive = _destructive_parameters(
            callee,
            helpers,
            parents,
            next_stack,
        )
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
                aliases = helper_sink._aliases_for_parameter(
                    helper,
                    parameter,
                    parents,
                    line + 1,
                )
                if any(base.loaded_names(argument) & aliases for argument in arguments):
                    destructive.add(parameter)

    return destructive


def _relevant_helper_semantics(
    helper: ast.AST,
    helpers: dict[str, ast.AST],
    parents: dict[int, ast.AST],
    stack: frozenset[int] = frozenset(),
) -> dict[str, object]:
    identity = id(helper)
    label = _helper_label(helper, helpers)
    if identity in stack:
        return {"helper": label, "recursive": True}

    next_stack = stack | {identity}
    payload: dict[str, object] = {
        "helper": label,
        "semantics": _callable_semantics(helper),
    }
    callees: list[dict[str, object]] = []
    helper_parameters = helper_mutations._parameter_names(helper)

    for call in ast.walk(helper):
        if not (
            isinstance(call, ast.Call)
            and isinstance(call.func, ast.Name)
            and helper_sink.sink_state._belongs_to_function(call, helper, parents)
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
                aliases = helper_sink._aliases_for_parameter(
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


helper_sink._helper_definitions = _helper_definitions
helper_sink._destructive_parameters = _destructive_parameters
helper_sink._relevant_helper_semantics = _relevant_helper_semantics


class ReleaseCandidateAssignedCallableSinkDestructorTests(unittest.TestCase):
    def test_assigned_lambda_clear_after_emission_changes_contract(self) -> None:
        emitted = '''
def validate(findings):
    findings.append(Finding("PUBLIC_CODE", "visible"))
'''
        cleared = '''
erase = lambda items: items.clear()

def validate(findings):
    findings.append(Finding("PUBLIC_CODE", "visible"))
    erase(findings)
'''
        expected = base.finding_semantic_signatures(emitted)
        actual = base.finding_semantic_signatures(cleared)
        self.assertNotEqual(expected, actual)
        sink = json.loads(actual["PUBLIC_CODE"][0])["sink"]
        self.assertTrue(
            any(item.startswith("post-helper-receiver-state:") for item in sink),
            sink,
        )

    def test_assigned_callable_alias_is_tracked(self) -> None:
        direct = '''
def validate(findings):
    findings.append(Finding("PUBLIC_CODE", "visible"))
'''
        aliased = '''
wipe = lambda items: items.clear()
erase = wipe

def validate(findings):
    findings.append(Finding("PUBLIC_CODE", "visible"))
    erase(findings)
'''
        self.assertNotEqual(
            base.finding_semantic_signatures(direct),
            base.finding_semantic_signatures(aliased),
        )

    def test_transitive_assigned_callable_destruction_is_tracked(self) -> None:
        direct = '''
def validate(findings):
    findings.append(Finding("PUBLIC_CODE", "visible"))
'''
        transitive = '''
def wipe(items):
    items.clear()

erase = lambda items: wipe(items)

def validate(findings):
    findings.append(Finding("PUBLIC_CODE", "visible"))
    erase(findings)
'''
        self.assertNotEqual(
            base.finding_semantic_signatures(direct),
            base.finding_semantic_signatures(transitive),
        )

    def test_additive_assigned_callable_does_not_destroy_sink(self) -> None:
        original = '''
def validate(findings):
    findings.append(Finding("PUBLIC_CODE", "visible"))
'''
        additive = '''
add_note = lambda items: items.append("note")

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

    def test_lambda_parameter_rename_remains_alpha_equivalent(self) -> None:
        first = '''
erase = lambda items: items.clear()

def validate(findings):
    findings.append(Finding("PUBLIC_CODE", "visible"))
    erase(findings)
'''
        renamed = first.replace(
            "lambda items: items.clear()",
            "lambda values: values.clear()",
        )
        self.assertEqual(
            base.finding_semantic_signatures(first),
            base.finding_semantic_signatures(renamed),
        )


if __name__ == "__main__":
    unittest.main()
