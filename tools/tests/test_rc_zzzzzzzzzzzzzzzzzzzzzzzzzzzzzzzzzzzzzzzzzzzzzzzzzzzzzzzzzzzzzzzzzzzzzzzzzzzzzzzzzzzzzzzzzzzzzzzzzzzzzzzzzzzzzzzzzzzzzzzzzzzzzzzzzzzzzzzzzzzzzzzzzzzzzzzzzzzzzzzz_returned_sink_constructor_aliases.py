from __future__ import annotations

import ast
import importlib
import json
import unittest
from pathlib import Path

import rc_finding_code_contracts_base as literal_base


# Final returned-sink constructor-alias closure for PR #71.
#
# Returned-sink selection already protects direct ToolResult.from_findings(...)
# calls and **kwargs expansion. A local alias of that constructor is the same
# runtime boundary and must not bypass the sink contract. Track only simple
# local alias dataflow, join mutually exclusive branches conservatively, honor
# definite rebindings, and keep private alias names out of the public identity.


def _load_overlay(suffix: str):
    matches = sorted(Path(__file__).parent.glob(f"test_rc_*{suffix}.py"))
    if len(matches) != 1:
        raise RuntimeError(f"expected exactly one RC overlay for {suffix!r}")
    return importlib.import_module(matches[0].stem)


# Import the prior lexical end of the suite first so this layer wraps the fully
# composed sink contract rather than an earlier intermediate implementation.
suppression = _load_overlay("_context_exit_suppression_semantics")
expanded = _load_overlay("_expanded_keywords_handler_types_and_with_targets")
returned_selection = expanded.returned_selection
sink_execution = expanded.sink_execution
sink_state = expanded.sink_state
post_sink = expanded.post_sink

_ALIAS_NO = "not-alias"
_ALIAS_YES = "from-findings-alias"
_ALIAS_MAYBE = "may-be-from-findings-alias"

_ALIAS_SELECTION_PREFIX = "post-returned-local-sink-constructor-alias:"
_previous_emission_sink_contract = sink_execution._emission_sink_contract


def _join_alias_state(left: str, right: str) -> str:
    if left == right:
        return left
    if _ALIAS_MAYBE in {left, right}:
        return _ALIAS_MAYBE
    return _ALIAS_MAYBE


def _merge_alias_maps(
    left: dict[str, str] | None,
    right: dict[str, str] | None,
) -> dict[str, str] | None:
    if left is None:
        return None if right is None else dict(right)
    if right is None:
        return dict(left)

    merged: dict[str, str] = {}
    for name in set(left) | set(right):
        state = _join_alias_state(
            left.get(name, _ALIAS_NO),
            right.get(name, _ALIAS_NO),
        )
        if state != _ALIAS_NO:
            merged[name] = state
    return merged


def _literal_truth(node: ast.AST) -> bool | None:
    try:
        value = ast.literal_eval(node)
    except (ValueError, TypeError, SyntaxError):
        return None
    try:
        return bool(value)
    except Exception:
        return None


def _is_direct_from_findings(node: ast.AST) -> bool:
    return isinstance(node, ast.Attribute) and node.attr == "from_findings"


def _value_alias_state(node: ast.AST, aliases: dict[str, str]) -> str:
    if _is_direct_from_findings(node):
        return _ALIAS_YES
    if isinstance(node, ast.Name):
        return aliases.get(node.id, _ALIAS_NO)
    if isinstance(node, ast.NamedExpr) and isinstance(node.target, ast.Name):
        return _value_alias_state(node.value, aliases)
    return _ALIAS_NO


def _assigned_names(target: ast.AST) -> set[str]:
    if isinstance(target, ast.Name):
        return {target.id}
    if isinstance(target, (ast.Tuple, ast.List)):
        result: set[str] = set()
        for item in target.elts:
            result.update(_assigned_names(item))
        return result
    if isinstance(target, ast.Starred):
        return _assigned_names(target.value)
    return set()


def _bind_assignment(
    statement: ast.Assign | ast.AnnAssign,
    aliases: dict[str, str],
) -> dict[str, str]:
    result = dict(aliases)

    if isinstance(statement, ast.AnnAssign):
        if statement.value is None:
            return result
        targets = [statement.target]
        value = statement.value
    else:
        targets = list(statement.targets)
        value = statement.value

    state = _value_alias_state(value, aliases)
    simple_targets = [
        target.id
        for target in targets
        if isinstance(target, ast.Name)
    ]

    if len(simple_targets) == len(targets):
        for name in simple_targets:
            if state == _ALIAS_NO:
                result.pop(name, None)
            else:
                result[name] = state
        return result

    # Destructuring can bind several unrelated values. Do not preserve stale
    # constructor aliases through a target shape this narrow model cannot prove.
    for target in targets:
        for name in _assigned_names(target):
            result.pop(name, None)
    return result


def _kill_bound_names(statement: ast.AST, aliases: dict[str, str]) -> dict[str, str]:
    result = dict(aliases)
    names: set[str] = set()

    if isinstance(statement, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
        names.add(statement.name)
    elif isinstance(statement, (ast.Import, ast.ImportFrom)):
        for item in statement.names:
            names.add(item.asname or item.name.split(".", 1)[0])
    elif isinstance(statement, ast.Delete):
        for target in statement.targets:
            names.update(_assigned_names(target))
    elif isinstance(statement, ast.AugAssign):
        names.update(_assigned_names(statement.target))

    for name in names:
        result.pop(name, None)
    return result


def _flow_block(
    statements: list[ast.stmt],
    aliases: dict[str, str],
    return_states: dict[int, dict[str, str]],
) -> dict[str, str] | None:
    current: dict[str, str] | None = dict(aliases)

    for statement in statements:
        if current is None:
            break

        if isinstance(statement, ast.Return):
            return_states[id(statement)] = dict(current)
            return None

        if isinstance(statement, ast.Raise):
            return None

        if isinstance(statement, (ast.Break, ast.Continue)):
            return None

        if isinstance(statement, (ast.Assign, ast.AnnAssign)):
            current = _bind_assignment(statement, current)
            continue

        if isinstance(
            statement,
            (
                ast.FunctionDef,
                ast.AsyncFunctionDef,
                ast.ClassDef,
                ast.Import,
                ast.ImportFrom,
                ast.Delete,
                ast.AugAssign,
            ),
        ):
            current = _kill_bound_names(statement, current)
            continue

        if isinstance(statement, ast.If):
            truth = _literal_truth(statement.test)
            if truth is True:
                current = _flow_block(statement.body, current, return_states)
                continue
            if truth is False:
                current = _flow_block(statement.orelse, current, return_states)
                continue

            body_state = _flow_block(statement.body, dict(current), return_states)
            else_state = (
                _flow_block(statement.orelse, dict(current), return_states)
                if statement.orelse
                else dict(current)
            )
            current = _merge_alias_maps(body_state, else_state)
            continue

        if isinstance(statement, (ast.With, ast.AsyncWith)):
            current = _flow_block(statement.body, current, return_states)
            continue

        if isinstance(statement, (ast.For, ast.AsyncFor, ast.While)):
            truth = (
                _literal_truth(statement.test)
                if isinstance(statement, ast.While)
                else None
            )
            if isinstance(statement, ast.While) and truth is False:
                current = (
                    _flow_block(statement.orelse, current, return_states)
                    if statement.orelse
                    else current
                )
                continue

            body_state = _flow_block(statement.body, dict(current), return_states)
            joined = _merge_alias_maps(current, body_state)
            if joined is None:
                joined = dict(current)
            current = (
                _flow_block(statement.orelse, joined, return_states)
                if statement.orelse
                else joined
            )
            continue

        try_types = (ast.Try,)
        if hasattr(ast, "TryStar"):
            try_types = (*try_types, ast.TryStar)
        if isinstance(statement, try_types):
            body_state = _flow_block(statement.body, dict(current), return_states)
            normal_state = (
                _flow_block(statement.orelse, body_state, return_states)
                if body_state is not None and statement.orelse
                else body_state
            )

            merged = normal_state
            for handler in statement.handlers:
                handler_state = _flow_block(
                    handler.body,
                    dict(current),
                    return_states,
                )
                merged = _merge_alias_maps(merged, handler_state)

            current = (
                _flow_block(statement.finalbody, merged, return_states)
                if statement.finalbody and merged is not None
                else merged
            )
            continue

        if isinstance(statement, ast.Match):
            merged: dict[str, str] | None = None
            has_unguarded_catchall = False
            for case in statement.cases:
                case_state = _flow_block(
                    case.body,
                    dict(current),
                    return_states,
                )
                merged = _merge_alias_maps(merged, case_state)
                if (
                    case.guard is None
                    and isinstance(case.pattern, ast.MatchAs)
                    and case.pattern.pattern is None
                ):
                    has_unguarded_catchall = True

            if not has_unguarded_catchall:
                merged = _merge_alias_maps(merged, current)
            current = merged
            continue

        # Other statements do not create or destroy a simple local alias in this
        # deliberately narrow dataflow. Assignment expressions in a return-call
        # callee are handled by _callee_alias_state below.

    return current


def _return_alias_states(
    function: ast.FunctionDef | ast.AsyncFunctionDef,
) -> dict[int, dict[str, str]]:
    states: dict[int, dict[str, str]] = {}
    _flow_block(function.body, {}, states)
    return states


def _callee_alias_state(
    node: ast.AST,
    aliases: dict[str, str],
) -> str:
    if isinstance(node, ast.Name):
        return aliases.get(node.id, _ALIAS_NO)
    if isinstance(node, ast.NamedExpr) and isinstance(node.target, ast.Name):
        return _value_alias_state(node.value, aliases)
    return _ALIAS_NO


def _synthetic_direct_call(call: ast.Call) -> ast.Call:
    return ast.Call(
        func=ast.Attribute(
            value=ast.Name(id="ToolResult", ctx=ast.Load()),
            attr="from_findings",
            ctx=ast.Load(),
        ),
        args=list(call.args),
        keywords=list(call.keywords),
    )


def _aliased_sink_selection(
    call: ast.Call,
    receiver_name: str,
) -> tuple[str, ast.AST | None] | None:
    synthetic = _synthetic_direct_call(call)

    # Reuse the already-composed **kwargs semantics first. Dynamic expansion,
    # duplicate findings values, and statically supplied findings mappings keep
    # exactly the same meaning when the callable was reached through an alias.
    expanded_state = expanded._expanded_keyword_state(
        synthetic,
        receiver_name,
    )
    if expanded_state is not None:
        return expanded_state

    explicit = next(
        (
            keyword.value
            for keyword in call.keywords
            if keyword.arg == "findings"
        ),
        None,
    )
    if explicit is not None:
        return returned_selection._selection_state(
            explicit,
            receiver_name,
        )

    # Preserve the compact positional compatibility fixtures used by the
    # established returned-sink layer.
    candidates = [
        argument
        for argument in call.args
        if returned_selection._contains_name(argument, receiver_name)
    ]
    if len(candidates) == 1:
        return returned_selection._selection_state(
            candidates[0],
            receiver_name,
        )

    return "missing-or-unresolved-findings", None


def _aliased_return_markers(
    finding: ast.Call,
    receiver: ast.AST,
    parents: dict[int, ast.AST],
) -> list[str]:
    function = sink_state._enclosing_function(finding, parents)
    if function is None:
        return []

    receiver_name = sink_state._root_name(receiver)
    if (
        receiver_name is None
        or receiver_name in returned_selection._function_parameter_names(function)
    ):
        return []

    finding_line = getattr(finding, "lineno", 10**9)
    return_states = _return_alias_states(function)
    markers: list[tuple[int, int, str]] = []

    for returned in ast.walk(function):
        if not (
            isinstance(returned, ast.Return)
            and returned.value is not None
            and sink_state._belongs_to_function(returned, function, parents)
            and getattr(returned, "lineno", 0) > finding_line
            and post_sink._can_share_execution_path(
                finding,
                returned,
                function,
                parents,
            )
        ):
            continue

        aliases = return_states.get(id(returned), {})
        for call in ast.walk(returned.value):
            if not isinstance(call, ast.Call):
                continue
            if _is_direct_from_findings(call.func):
                # Direct calls are already handled by the established selection
                # and expanded-keyword layers.
                continue

            alias_state = _callee_alias_state(call.func, aliases)
            if alias_state == _ALIAS_NO:
                continue

            selection = _aliased_sink_selection(call, receiver_name)
            if selection is None:
                continue

            state, selector = selection
            if state == "kept":
                continue

            payload: dict[str, object] = {
                "context": sink_state._sink_state_context(
                    returned,
                    function,
                    parents,
                ),
                # Do not expose the private alias name. Preserve only whether
                # constructor identity is definite or path-joined.
                "constructor": (
                    "definite-alias"
                    if alias_state == _ALIAS_YES
                    else "possible-alias"
                ),
                "selection": state,
            }
            if selector is not None:
                payload["selector"] = literal_base.canonical_ast(selector)

            markers.append(
                (
                    getattr(returned, "lineno", 0),
                    getattr(returned, "col_offset", 0),
                    json.dumps(payload, sort_keys=True),
                )
            )

    markers.sort()
    return [value for _, _, value in markers]


def _emission_sink_contract_with_constructor_aliases(
    node: ast.Call,
    parents: dict[int, ast.AST],
) -> list[str]:
    contract = list(_previous_emission_sink_contract(node, parents))
    receiver = sink_state._finding_sink_receiver(node, parents)
    if receiver is None:
        return contract

    markers = _aliased_return_markers(node, receiver, parents)
    if markers:
        contract.append(
            _ALIAS_SELECTION_PREFIX + json.dumps(markers, sort_keys=True)
        )
    return contract


sink_execution._emission_sink_contract = (
    _emission_sink_contract_with_constructor_aliases
)


class ReleaseCandidateReturnedSinkConstructorAliasTests(unittest.TestCase):
    def _sink(self, source: str) -> list[str]:
        signature = literal_base.finding_semantic_signatures(
            source,
            "sample.py",
        )["PUBLIC_CODE"][0]
        return json.loads(signature)["sink"]

    def test_local_constructor_alias_discard_changes_contract(self) -> None:
        kept = """
from standards_tools import Finding, ToolResult

def validate():
    findings = []
    maker = ToolResult.from_findings
    findings.append(Finding("PUBLIC_CODE", "visible"))
    return maker(tool="validate", version="1", findings=findings)
"""
        discarded = """
from standards_tools import Finding, ToolResult

def validate():
    findings = []
    maker = ToolResult.from_findings
    findings.append(Finding("PUBLIC_CODE", "visible"))
    return maker(tool="validate", version="1", findings=[])
"""
        self.assertNotEqual(
            literal_base.finding_semantic_signatures(kept, "sample.py"),
            literal_base.finding_semantic_signatures(discarded, "sample.py"),
        )
        self.assertFalse(
            any(item.startswith(_ALIAS_SELECTION_PREFIX) for item in self._sink(kept))
        )
        self.assertTrue(
            any(item.startswith(_ALIAS_SELECTION_PREFIX) for item in self._sink(discarded))
        )

    def test_chained_constructor_alias_discard_is_tracked(self) -> None:
        source = """
from standards_tools import Finding, ToolResult

def validate():
    findings = []
    maker = ToolResult.from_findings
    other = maker
    findings.append(Finding("PUBLIC_CODE", "visible"))
    return other(tool="validate", version="1", findings=[])
"""
        self.assertTrue(
            any(item.startswith(_ALIAS_SELECTION_PREFIX) for item in self._sink(source))
        )

    def test_definite_rebinding_removes_constructor_alias(self) -> None:
        source = """
from standards_tools import Finding, ToolResult

def harmless(**kwargs):
    return kwargs

def validate():
    findings = []
    maker = ToolResult.from_findings
    maker = harmless
    findings.append(Finding("PUBLIC_CODE", "visible"))
    return maker(tool="validate", version="1", findings=[])
"""
        self.assertFalse(
            any(item.startswith(_ALIAS_SELECTION_PREFIX) for item in self._sink(source))
        )

    def test_branch_join_retains_possible_constructor_alias(self) -> None:
        source = """
from standards_tools import Finding, ToolResult

def harmless(**kwargs):
    return kwargs

def validate(flag):
    findings = []
    if flag:
        maker = ToolResult.from_findings
    else:
        maker = harmless
    findings.append(Finding("PUBLIC_CODE", "visible"))
    return maker(tool="validate", version="1", findings=[])
"""
        self.assertTrue(
            any(item.startswith(_ALIAS_SELECTION_PREFIX) for item in self._sink(source))
        )

    def test_statically_dead_alias_does_not_create_sink_risk(self) -> None:
        source = """
from standards_tools import Finding, ToolResult

def harmless(**kwargs):
    return kwargs

def validate():
    findings = []
    maker = harmless
    if False:
        maker = ToolResult.from_findings
    findings.append(Finding("PUBLIC_CODE", "visible"))
    return maker(tool="validate", version="1", findings=[])
"""
        self.assertFalse(
            any(item.startswith(_ALIAS_SELECTION_PREFIX) for item in self._sink(source))
        )


if __name__ == "__main__":
    unittest.main()
