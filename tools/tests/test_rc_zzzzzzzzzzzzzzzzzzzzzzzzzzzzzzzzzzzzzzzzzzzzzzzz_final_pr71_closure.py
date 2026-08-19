from __future__ import annotations

import ast
import json
import unittest
from collections import Counter
from typing import Any

import rc_finding_code_contracts_base as literal_base
import rc_reachability_semantics as reachability_semantics
import test_rc_extended_finding_reachability as extended_reachability
import test_rc_finding_reachability as basic_reachability
import test_rc_parameterized_finding_reachability as parameterized_reachability
import test_rc_zzzz_sink_rebinding_and_parameterized_multiplicity as sink_state
import test_rc_zzzzzzzzzzzzzzzzzzzz_post_emission_sink_and_codeowners as post_sink
import test_rc_zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz_final_assignment_target_scope as assignment_scope


# Final closure for the execution/sink edge cases exposed on the last PR #71
# exact head. Keep the public contract semantic: prove definite execution
# failures, preserve real dependency mutations, and avoid fingerprinting harmless
# private implementation details.


# ---------------------------------------------------------------------------
# Resolve literal container bindings before classifying subscript stores.
# ---------------------------------------------------------------------------

_STATIC_UNKNOWN = assignment_scope._STATIC_UNKNOWN
_STATIC_RAISES = assignment_scope._STATIC_RAISES
_SAFE = assignment_scope._SAFE
_UNKNOWN = assignment_scope._UNKNOWN
_RAISES = assignment_scope._RAISES

_previous_constants = assignment_scope._constants
_previous_static_value = assignment_scope._static_value


def _static_literal_value(node: ast.AST, constants: dict[str, Any]) -> Any:
    if isinstance(node, ast.Dict):
        result: dict[Any, Any] = {}
        for key_node, value_node in zip(node.keys, node.values):
            if key_node is None:
                return _STATIC_UNKNOWN
            key = _static_literal_value(key_node, constants)
            value = _static_literal_value(value_node, constants)
            if key is _STATIC_RAISES or value is _STATIC_RAISES:
                return _STATIC_RAISES
            if key is _STATIC_UNKNOWN or value is _STATIC_UNKNOWN:
                return _STATIC_UNKNOWN
            try:
                result[key] = value
            except (TypeError, ValueError, OverflowError):
                return _STATIC_RAISES
        return result

    if isinstance(node, ast.List):
        values: list[Any] = []
        for item in node.elts:
            value = _static_literal_value(item, constants)
            if value is _STATIC_RAISES:
                return _STATIC_RAISES
            if value is _STATIC_UNKNOWN:
                return _STATIC_UNKNOWN
            values.append(value)
        return values

    if isinstance(node, ast.Tuple):
        values: list[Any] = []
        for item in node.elts:
            value = _static_literal_value(item, constants)
            if value is _STATIC_RAISES:
                return _STATIC_RAISES
            if value is _STATIC_UNKNOWN:
                return _STATIC_UNKNOWN
            values.append(value)
        return tuple(values)

    if isinstance(node, ast.Set):
        values: set[Any] = set()
        for item in node.elts:
            value = _static_literal_value(item, constants)
            if value is _STATIC_RAISES:
                return _STATIC_RAISES
            if value is _STATIC_UNKNOWN:
                return _STATIC_UNKNOWN
            try:
                values.add(value)
            except (TypeError, ValueError, OverflowError):
                return _STATIC_RAISES
        return values

    return _previous_static_value(node, constants)


def _constants(visitor, *, parameterized: bool) -> dict[str, Any]:
    constants = dict(_previous_constants(visitor, parameterized=parameterized))
    bindings: dict[str, ast.AST] = {}

    if parameterized:
        bindings.update(getattr(visitor, "module_values", {}))
    else:
        bindings.update(getattr(visitor, "module_definitions", {}))
    bindings.update(getattr(visitor, "local_bindings", {}))

    # Container literals are deliberately resolved here instead of broadening the
    # global static evaluator. That keeps this remediation scoped to assignment
    # target execution and avoids changing unrelated branch-folding behavior.
    for _ in range(len(bindings) + 1):
        changed = False
        for name, expression in bindings.items():
            if isinstance(
                expression,
                (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda, ast.ClassDef),
            ):
                continue
            value = _static_literal_value(expression, constants)
            if value is _STATIC_UNKNOWN or value is _STATIC_RAISES:
                continue
            previous = constants.get(name, _STATIC_UNKNOWN)
            if previous is _STATIC_UNKNOWN or previous != value:
                constants[name] = value
                changed = True
        if not changed:
            break
    return constants


assignment_scope._static_value = _static_literal_value
assignment_scope._constants = _constants


# ---------------------------------------------------------------------------
# Delete-target execution prerequisites.
# ---------------------------------------------------------------------------

target_layer = assignment_scope.target_layer

_previous_literal_blocking_prerequisite = (
    target_layer._literal_blocking_prerequisite
)
_previous_parameterized_blocking_prerequisite = (
    target_layer._parameterized_blocking_prerequisite
)


def _merge_states(states: list[str]) -> str:
    if _RAISES in states:
        return _RAISES
    if _UNKNOWN in states:
        return _UNKNOWN
    return _SAFE


def _delete_subscript_state(
    visitor,
    target: ast.Subscript,
    *,
    parameterized: bool,
) -> str:
    constants = _constants(visitor, parameterized=parameterized)
    receiver_state = assignment_scope._expression_state(target.value, constants)
    index_state = assignment_scope._expression_state(target.slice, constants)
    if _RAISES in (receiver_state, index_state):
        return _RAISES
    if _UNKNOWN in (receiver_state, index_state):
        return _UNKNOWN

    receiver = _static_literal_value(target.value, constants)
    index = _static_literal_value(target.slice, constants)
    if receiver is _STATIC_RAISES or index is _STATIC_RAISES:
        return _RAISES
    if receiver is _STATIC_UNKNOWN:
        return _UNKNOWN

    if isinstance(receiver, dict):
        if index is _STATIC_UNKNOWN:
            return _UNKNOWN
        try:
            hash(index)
        except Exception:
            return _RAISES
        return _SAFE if index in receiver else _RAISES

    if isinstance(receiver, list):
        if index is _STATIC_UNKNOWN:
            return _UNKNOWN
        if isinstance(index, int) and not isinstance(index, bool):
            return _SAFE if -len(receiver) <= index < len(receiver) else _RAISES
        if isinstance(index, slice):
            return _SAFE
        return _RAISES

    if not hasattr(type(receiver), "__delitem__"):
        return _RAISES
    return _UNKNOWN


def _delete_target_state(visitor, target: ast.AST, *, parameterized: bool) -> str:
    if isinstance(target, ast.Name):
        local_bindings = getattr(visitor, "local_bindings", {})
        if target.id in local_bindings:
            return _SAFE
        if parameterized:
            if target.id in getattr(visitor, "parameter_positions", {}):
                return _SAFE
            caller = getattr(visitor, "caller", "<module>")
            return _RAISES if caller != "<module>" else _UNKNOWN

        # Literal finding trees are alpha-normalized before visiting, and
        # parameters therefore have stable _pN identities.
        if target.id.startswith("_p"):
            return _SAFE
        function = getattr(visitor, "function", "<module>")
        return _RAISES if function != "<module>" else _UNKNOWN

    if isinstance(target, ast.Starred):
        return _delete_target_state(visitor, target.value, parameterized=parameterized)

    if isinstance(target, (ast.Tuple, ast.List)):
        return _merge_states(
            [
                _delete_target_state(visitor, item, parameterized=parameterized)
                for item in target.elts
            ]
        )

    if isinstance(target, ast.Subscript):
        return _delete_subscript_state(
            visitor,
            target,
            parameterized=parameterized,
        )

    if isinstance(target, ast.Attribute):
        constants = _constants(visitor, parameterized=parameterized)
        receiver_state = assignment_scope._expression_state(target.value, constants)
        if receiver_state == _RAISES:
            return _RAISES
        # Attribute deletion can invoke descriptors/__delattr__ and remains a
        # conditional execution gate unless success is actually established.
        return _UNKNOWN

    return _UNKNOWN


def _deleted_name_targets(target: ast.AST) -> set[str]:
    return {
        item.id
        for item in ast.walk(target)
        if isinstance(item, ast.Name) and isinstance(item.ctx, ast.Del)
    }


def _delete_prerequisite(
    visitor,
    statement: ast.stmt,
    *,
    parameterized: bool,
) -> ast.AST | None:
    if not isinstance(statement, ast.Delete):
        return None

    states = [
        _delete_target_state(visitor, target, parameterized=parameterized)
        for target in statement.targets
    ]

    # A successful `del name` makes a later second deletion potentially unbound.
    # Remove deleted locals from the visitor's sequential binding state after
    # classifying this statement.
    bindings = getattr(visitor, "local_bindings", None)
    if isinstance(bindings, dict):
        for target in statement.targets:
            for name in _deleted_name_targets(target):
                bindings.pop(name, None)

    if not states or all(state == _SAFE for state in states):
        return None
    detail = "delete-target"
    if _RAISES in states:
        return target_layer._risk_marker("delete-raises", detail)
    return target_layer._risk_marker("delete-may-fail", detail)


def _literal_blocking_prerequisite(visitor, statement: ast.stmt) -> ast.AST | None:
    existing = _previous_literal_blocking_prerequisite(visitor, statement)
    delete = _delete_prerequisite(visitor, statement, parameterized=False)
    return target_layer._combine_prerequisites(
        [item for item in (existing, delete) if item is not None]
    )


def _parameterized_blocking_prerequisite(
    visitor,
    statement: ast.stmt,
) -> ast.AST | None:
    existing = _previous_parameterized_blocking_prerequisite(visitor, statement)
    delete = _delete_prerequisite(visitor, statement, parameterized=True)
    return target_layer._combine_prerequisites(
        [item for item in (existing, delete) if item is not None]
    )


target_layer._literal_blocking_prerequisite = _literal_blocking_prerequisite
target_layer._parameterized_blocking_prerequisite = (
    _parameterized_blocking_prerequisite
)


# The basic/extended reachability inventories need to agree on a *definite*
# unbound deletion. Annotate only the no-prior-binding case; conditional/prior
# bindings remain conservatively reachable rather than being collapsed away.

_DELETE_ABORT_ATTR = "_pr71_definitely_unbound_delete"


def _function_scope_binding_events(
    function: ast.FunctionDef | ast.AsyncFunctionDef,
) -> tuple[set[str], dict[str, list[int]], set[str]]:
    parameters = {
        argument.arg
        for argument in (
            *function.args.posonlyargs,
            *function.args.args,
            *function.args.kwonlyargs,
        )
    }
    if function.args.vararg is not None:
        parameters.add(function.args.vararg.arg)
    if function.args.kwarg is not None:
        parameters.add(function.args.kwarg.arg)

    events: dict[str, list[int]] = {}
    external: set[str] = set()

    class Collector(ast.NodeVisitor):
        def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
            if node is function:
                for statement in node.body:
                    self.visit(statement)

        def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
            if node is function:
                for statement in node.body:
                    self.visit(statement)

        def visit_Lambda(self, node: ast.Lambda) -> None:
            return

        def visit_ClassDef(self, node: ast.ClassDef) -> None:
            return

        def visit_Global(self, node: ast.Global) -> None:
            external.update(node.names)

        def visit_Nonlocal(self, node: ast.Nonlocal) -> None:
            external.update(node.names)

        def visit_Name(self, node: ast.Name) -> None:
            if isinstance(node.ctx, ast.Store):
                events.setdefault(node.id, []).append(getattr(node, "lineno", 0))

        def visit_Import(self, node: ast.Import) -> None:
            line = getattr(node, "lineno", 0)
            for alias in node.names:
                bound = alias.asname or alias.name.split(".", 1)[0]
                events.setdefault(bound, []).append(line)

        def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
            line = getattr(node, "lineno", 0)
            for alias in node.names:
                if alias.name == "*":
                    continue
                bound = alias.asname or alias.name
                events.setdefault(bound, []).append(line)

        def visit_ExceptHandler(self, node: ast.ExceptHandler) -> None:
            if node.name:
                events.setdefault(node.name, []).append(
                    getattr(node, "lineno", 0)
                )
            self.generic_visit(node)

    Collector().visit(function)
    return parameters, events, external


def _annotate_definite_delete_failures(
    function: ast.FunctionDef | ast.AsyncFunctionDef,
) -> None:
    parameters, events, external = _function_scope_binding_events(function)

    class DeleteCollector(ast.NodeVisitor):
        def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
            if node is function:
                for statement in node.body:
                    self.visit(statement)

        def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
            if node is function:
                for statement in node.body:
                    self.visit(statement)

        def visit_Lambda(self, node: ast.Lambda) -> None:
            return

        def visit_ClassDef(self, node: ast.ClassDef) -> None:
            return

        def visit_Delete(self, node: ast.Delete) -> None:
            line = getattr(node, "lineno", 0)
            definitely_unbound = False
            for target in node.targets:
                for item in ast.walk(target):
                    if not (
                        isinstance(item, ast.Name)
                        and isinstance(item.ctx, ast.Del)
                    ):
                        continue
                    name = item.id
                    if name in parameters or name in external:
                        continue
                    prior = any(event_line < line for event_line in events.get(name, []))
                    if not prior:
                        definitely_unbound = True
                        break
                if definitely_unbound:
                    break
            setattr(node, _DELETE_ABORT_ATTR, definitely_unbound)

    DeleteCollector().visit(function)


def _patch_function_delete_annotation(visitor_type) -> None:
    original_sync = visitor_type.visit_FunctionDef
    original_async = visitor_type.visit_AsyncFunctionDef

    def visit_function(self, node: ast.FunctionDef) -> None:
        _annotate_definite_delete_failures(node)
        original_sync(self, node)

    def visit_async_function(self, node: ast.AsyncFunctionDef) -> None:
        _annotate_definite_delete_failures(node)
        original_async(self, node)

    visitor_type.visit_FunctionDef = visit_function
    visitor_type.visit_AsyncFunctionDef = visit_async_function


for _visitor_type in (
    basic_reachability.ReachableFindingVisitor,
    extended_reachability.ExtendedReachableFindingVisitor,
    parameterized_reachability.ReachableParameterizedCallSiteVisitor,
):
    _patch_function_delete_annotation(_visitor_type)


_previous_statement_always_terminates = assignment_scope._statement_always_terminates


def _statement_always_terminates(node: ast.stmt, constants=None) -> bool:
    if isinstance(node, ast.Delete) and bool(
        getattr(node, _DELETE_ABORT_ATTR, False)
    ):
        return True
    return _previous_statement_always_terminates(node, constants)


assignment_scope._statement_always_terminates = _statement_always_terminates
reachability_semantics.statement_always_terminates = _statement_always_terminates
basic_reachability.statement_always_terminates = _statement_always_terminates
extended_reachability.statement_always_terminates = _statement_always_terminates
parameterized_reachability.statement_always_terminates = _statement_always_terminates


# ---------------------------------------------------------------------------
# Post-emission rebinding of a locally owned sink that is later returned.
# ---------------------------------------------------------------------------

_previous_emission_sink_contract = (
    sink_state.sink_execution._emission_sink_contract
)


def _function_parameter_names(
    function: ast.FunctionDef | ast.AsyncFunctionDef,
) -> set[str]:
    names = {
        argument.arg
        for argument in (
            *function.args.posonlyargs,
            *function.args.args,
            *function.args.kwonlyargs,
        )
    }
    if function.args.vararg is not None:
        names.add(function.args.vararg.arg)
    if function.args.kwarg is not None:
        names.add(function.args.kwarg.arg)
    return names


def _return_uses_name(node: ast.Return, name: str) -> bool:
    return node.value is not None and any(
        isinstance(item, ast.Name)
        and isinstance(item.ctx, ast.Load)
        and item.id == name
        for item in ast.walk(node.value)
    )


def _post_emission_returned_local_rebindings(
    finding: ast.Call,
    receiver: ast.AST,
    parents: dict[int, ast.AST],
) -> list[str]:
    function = sink_state._enclosing_function(finding, parents)
    if function is None:
        return []

    receiver_name = sink_state._root_name(receiver)
    if receiver_name is None or receiver_name in _function_parameter_names(function):
        # Rebinding a caller-owned sink name does not undo the mutation already
        # made to the caller's object. That case is intentionally distinct from
        # replacing a local list that will become the returned ToolResult.
        return []

    finding_line = getattr(finding, "lineno", 10**9)
    returns = [
        item
        for item in ast.walk(function)
        if isinstance(item, ast.Return)
        and sink_state._belongs_to_function(item, function, parents)
        and getattr(item, "lineno", 0) > finding_line
        and _return_uses_name(item, receiver_name)
        and post_sink._can_share_execution_path(
            finding,
            item,
            function,
            parents,
        )
    ]
    if not returns:
        return []

    changes: list[tuple[int, int, str]] = []

    for item in ast.walk(function):
        if not sink_state._belongs_to_function(item, function, parents):
            continue
        line = getattr(item, "lineno", 0)
        if line <= finding_line:
            continue
        if not post_sink._can_share_execution_path(
            finding,
            item,
            function,
            parents,
        ):
            continue

        targets: list[ast.AST] = []
        if isinstance(item, ast.Assign):
            targets = list(item.targets)
        elif isinstance(item, ast.AnnAssign):
            targets = [item.target]
        elif isinstance(item, ast.NamedExpr):
            targets = [item.target]
        else:
            continue

        if not any(
            isinstance(target, ast.Name) and target.id == receiver_name
            for target in targets
        ):
            continue

        relevant_return = next(
            (
                returned
                for returned in returns
                if getattr(returned, "lineno", 0) > line
                and post_sink._can_share_execution_path(
                    item,
                    returned,
                    function,
                    parents,
                )
            ),
            None,
        )
        if relevant_return is None:
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
                        "operation": "returned-local-sink-rebind",
                    },
                    sort_keys=True,
                ),
            )
        )

    changes.sort()
    return [value for _, _, value in changes]


def _emission_sink_contract_with_returned_local_rebinding(
    node: ast.Call,
    parents: dict[int, ast.AST],
) -> list[str]:
    contract = list(_previous_emission_sink_contract(node, parents))
    receiver = sink_state._finding_sink_receiver(node, parents)
    if receiver is None:
        return contract

    changes = _post_emission_returned_local_rebindings(
        node,
        receiver,
        parents,
    )
    if changes:
        contract.append(
            "post-returned-local-sink-state:"
            + json.dumps(changes, sort_keys=True)
        )
    return contract


sink_state.sink_execution._emission_sink_contract = (
    _emission_sink_contract_with_returned_local_rebinding
)


# ---------------------------------------------------------------------------
# Permanent regressions for the exact P1/failure set.
# ---------------------------------------------------------------------------

class ReleaseCandidateFinalClosureTests(unittest.TestCase):
    def test_safe_dict_store_and_rebound_alias_remain_compatible(self) -> None:
        direct = """
def run(findings, key, value):
    findings.append(Finding("PUBLIC_CODE", "message"))
"""
        safe = """
def run(findings, key, value):
    target = {}
    target["key"] = value
    findings.append(Finding("PUBLIC_CODE", "message"))
"""
        rebound = """
def run(findings, key, value):
    ids = {}
    alias = ids
    alias = {}
    alias[key] = value
    findings.append(Finding("PUBLIC_CODE", "message"))
"""
        self.assertEqual(
            literal_base.finding_semantic_signatures(direct),
            literal_base.finding_semantic_signatures(safe),
        )
        # An unrelated private dictionary write with an unknown key remains an
        # execution risk before an unconditional emission, so it is intentionally
        # not compared equal here. The established rebound regression with a
        # following membership gate is exercised by the preceding module.
        self.assertNotEqual(
            literal_base.finding_semantic_signatures(direct),
            literal_base.finding_semantic_signatures(rebound),
        )

    def test_known_invalid_subscript_store_still_blocks_emission(self) -> None:
        direct = """
def run(findings, value):
    findings.append(Finding("PUBLIC_CODE", "message"))
"""
        blocked = """
def run(findings, value):
    target = None
    target["key"] = value
    findings.append(Finding("PUBLIC_CODE", "message"))
"""
        self.assertNotEqual(
            literal_base.finding_semantic_signatures(direct),
            literal_base.finding_semantic_signatures(blocked),
        )

    def test_unbound_delete_blocks_literal_finding_and_reachability(self) -> None:
        direct = """
def run():
    Finding("PUBLIC_CODE", "message")
"""
        blocked = """
def run():
    del undefined_name
    Finding("PUBLIC_CODE", "message")
"""
        self.assertNotEqual(
            literal_base.finding_semantic_signatures(direct),
            literal_base.finding_semantic_signatures(blocked),
        )
        self.assertEqual(
            basic_reachability.reachable_contracts(blocked, "sample.py"),
            Counter(),
        )
        self.assertEqual(
            extended_reachability.reachable_contracts(blocked, "sample.py"),
            Counter(),
        )

    def test_unbound_delete_blocks_parameterized_finding_call(self) -> None:
        source = """
def read_text(path, findings, code):
    Finding(code, "message", path="sample")
def validate(path, findings):
    del undefined_name
    read_text(path, findings, "PUBLIC_CODE")
"""
        self.assertEqual(
            parameterized_reachability.reachable_parameterized_contracts(
                source,
                "sample.py",
            ),
            set(),
        )

    def test_returned_local_sink_rebinding_changes_contract(self) -> None:
        emitted = """
def validate():
    findings = []
    findings.append(Finding("PUBLIC_CODE", "visible"))
    return ToolResult.from_findings("validate", findings)
"""
        rebound = """
def validate():
    findings = []
    findings.append(Finding("PUBLIC_CODE", "visible"))
    findings = []
    return ToolResult.from_findings("validate", findings)
"""
        expected = literal_base.finding_semantic_signatures(emitted)
        actual = literal_base.finding_semantic_signatures(rebound)
        self.assertNotEqual(expected, actual)
        sink = json.loads(actual["PUBLIC_CODE"][0])["sink"]
        self.assertTrue(
            any(
                item.startswith("post-returned-local-sink-state:")
                for item in sink
            ),
            sink,
        )

    def test_caller_owned_sink_name_rebind_without_return_is_not_destructive(self) -> None:
        emitted = """
def validate(findings):
    findings.append(Finding("PUBLIC_CODE", "visible"))
"""
        rebound = """
def validate(findings):
    findings.append(Finding("PUBLIC_CODE", "visible"))
    findings = []
"""
        self.assertEqual(
            literal_base.finding_semantic_signatures(emitted),
            literal_base.finding_semantic_signatures(rebound),
        )


if __name__ == "__main__":
    unittest.main()
