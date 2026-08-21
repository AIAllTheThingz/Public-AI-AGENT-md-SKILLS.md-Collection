from __future__ import annotations

import ast
import json
import unittest
from collections import Counter

import rc_finding_code_contracts_base as literal_base
import rc_reachability_semantics as reachability_semantics
import test_rc_extended_finding_reachability as extended_reachability
import test_rc_finding_reachability as basic_reachability
import test_rc_parameterized_finding_codes as parameterized_active
import test_rc_parameterized_finding_reachability as parameterized_reachability
import test_rc_zzz_finding_emission_sink as sink_execution
import test_rc_zzzz_sink_rebinding_and_parameterized_multiplicity as sink_state
import test_rc_zzzzzzzzzzzzzzzzzzzz_post_emission_sink_and_codeowners as post_sink
import test_rc_zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz_assignment_rhs_and_bound_method_aliases as prior


# Final composition for the two review gaps exposed by the assignment/bound-
# method remediation, plus the exact-head CI regression from embedding raw RHS
# syntax in published finding signatures.
#
# Assignment execution is represented by stable risk classes instead of the
# implementation expression itself. This preserves the public fact that an
# emission has a prior potentially failing operation without freezing private
# variable names, subprocess details, or other compatible implementation edits.
# Assignment target binding is evaluated after the RHS and is independently able
# to fail (attribute/subscript stores and destructuring are the important cases).
#
# Bound destructive-method aliases are tracked only when the receiver alias,
# method binding, finding emission, rebinding, and eventual call can coexist on
# one branch path. This prevents mutually exclusive branches from fabricating a
# destructive sink history.


pre = prior.statement_prerequisites.prior
left_to_right = prior.left_to_right
final_composition = prior.final_composition

_ASSIGNMENT_MARKER_PREFIX = "assignment-execution:"
_SAFE = left_to_right._SAFE
_UNKNOWN = left_to_right._UNKNOWN
_RAISES = left_to_right._RAISES


# ---------------------------------------------------------------------------
# Stable assignment execution prerequisites
# ---------------------------------------------------------------------------


def _risk_marker(kind: str, detail: str = "") -> ast.Constant:
    suffix = f":{detail}" if detail else ""
    return ast.Constant(value=f"{_ASSIGNMENT_MARKER_PREFIX}{kind}{suffix}")


def _is_risk_marker(node: ast.AST) -> bool:
    return (
        isinstance(node, ast.Constant)
        and isinstance(node.value, str)
        and node.value.startswith(_ASSIGNMENT_MARKER_PREFIX)
    )


def _combine_prerequisites(nodes: list[ast.AST]) -> ast.AST | None:
    if not nodes:
        return None
    if len(nodes) == 1:
        return nodes[0]
    result = ast.Tuple(elts=nodes, ctx=ast.Load())
    ast.fix_missing_locations(result)
    return result


def _assignment_rhs(statement: ast.stmt) -> ast.AST | None:
    if isinstance(statement, (ast.Assign, ast.AnnAssign, ast.AugAssign)):
        return statement.value
    return None


def _assignment_targets(statement: ast.stmt) -> list[ast.AST]:
    if isinstance(statement, ast.Assign):
        return list(statement.targets)
    if isinstance(statement, (ast.AnnAssign, ast.AugAssign)):
        return [statement.target]
    return []


def _target_pattern(target: ast.AST) -> str:
    if isinstance(target, ast.Name):
        return "name"
    if isinstance(target, ast.Starred):
        return f"starred({_target_pattern(target.value)})"
    if isinstance(target, ast.Tuple):
        return "tuple(" + ",".join(_target_pattern(item) for item in target.elts) + ")"
    if isinstance(target, ast.List):
        return "list(" + ",".join(_target_pattern(item) for item in target.elts) + ")"
    if isinstance(target, ast.Attribute):
        return "attribute"
    if isinstance(target, ast.Subscript):
        return "subscript"
    return type(target).__name__.lower()


def _merge_states(states: list[str]) -> str:
    if _RAISES in states:
        return _RAISES
    if _UNKNOWN in states:
        return _UNKNOWN
    return _SAFE


def _literal_sequence_elements(node: ast.AST) -> list[ast.AST] | None:
    if isinstance(node, (ast.Tuple, ast.List)):
        return list(node.elts)
    return None


def _target_binding_state(target: ast.AST, rhs: ast.AST | None) -> str:
    """Conservatively classify binding the evaluated RHS into target."""

    if isinstance(target, ast.Name):
        return _SAFE
    if isinstance(target, ast.Starred):
        return _target_binding_state(target.value, rhs)
    if isinstance(target, (ast.Attribute, ast.Subscript)):
        return _UNKNOWN

    if isinstance(target, (ast.Tuple, ast.List)):
        values = None if rhs is None else _literal_sequence_elements(rhs)
        if values is None:
            if isinstance(rhs, ast.Constant) and not isinstance(
                rhs.value, (str, bytes, bytearray, tuple, list)
            ):
                return _RAISES
            return _UNKNOWN

        starred = [
            index for index, item in enumerate(target.elts) if isinstance(item, ast.Starred)
        ]
        if len(starred) > 1:
            return _RAISES

        if not starred:
            if len(values) != len(target.elts):
                return _RAISES
            return _merge_states(
                [
                    _target_binding_state(item, value)
                    for item, value in zip(target.elts, values)
                ]
            )

        star_index = starred[0]
        fixed = len(target.elts) - 1
        if len(values) < fixed:
            return _RAISES

        states: list[str] = []
        for index, item in enumerate(target.elts[:star_index]):
            states.append(_target_binding_state(item, values[index]))

        trailing = len(target.elts) - star_index - 1
        if trailing:
            for offset, item in enumerate(target.elts[star_index + 1 :], start=1):
                states.append(_target_binding_state(item, values[-trailing - 1 + offset]))

        star_target = target.elts[star_index]
        if isinstance(star_target, ast.Starred):
            states.append(_target_binding_state(star_target.value, ast.List(elts=[], ctx=ast.Load())))
        return _merge_states(states)

    return _UNKNOWN


def _expression_state(visitor, node: ast.AST, *, parameterized: bool) -> str:
    constants = (
        left_to_right._parameterized_constants(visitor)
        if parameterized
        else left_to_right._literal_constants(visitor)
    )
    return final_composition._visitor_execution_state(visitor, node, constants)


def _same_module_call_argument_state(visitor, node: ast.Call, *, parameterized: bool) -> str:
    # The preceding helper layer already owns whether the helper body itself may
    # abort. If it decided a same-module helper is safe, preserve that decision
    # but still honor execution-bearing call arguments evaluated before entry.
    states = [
        _expression_state(visitor, item, parameterized=parameterized)
        for item in [*node.args, *(keyword.value for keyword in node.keywords)]
    ]
    return _merge_states(states) if states else _SAFE


def _rhs_risk_marker(visitor, rhs: ast.AST | None, *, parameterized: bool) -> ast.AST | None:
    if rhs is None:
        return None

    if prior._known_same_module_function_call(visitor, rhs):
        assert isinstance(rhs, ast.Call)
        state = _same_module_call_argument_state(
            visitor,
            rhs,
            parameterized=parameterized,
        )
    else:
        state = _expression_state(visitor, rhs, parameterized=parameterized)

    if state == _RAISES:
        return _risk_marker("rhs-raises")
    if state == _UNKNOWN:
        return _risk_marker("rhs-may-fail")
    return None


def _target_risk_marker(statement: ast.stmt) -> ast.AST | None:
    rhs = _assignment_rhs(statement)
    risky: list[str] = []
    raising = False

    for target in _assignment_targets(statement):
        state = _target_binding_state(target, rhs)
        if state == _RAISES:
            raising = True
            risky.append(_target_pattern(target))
        elif state == _UNKNOWN:
            risky.append(_target_pattern(target))

    if isinstance(statement, ast.AugAssign):
        # AugAssign loads the target, applies an operator, then stores it. Even a
        # simple name target can invoke dynamic operator behavior.
        risky.append("augmented-assignment")

    if not risky:
        return None
    detail = ",".join(sorted(set(risky)))
    return _risk_marker("target-raises" if raising else "target-may-fail", detail)


def _literal_blocking_prerequisite(visitor, statement: ast.stmt) -> ast.AST | None:
    existing = prior._previous_literal_prerequisite(visitor, statement)
    parts: list[ast.AST] = []
    if existing is not None:
        parts.append(existing)

    # A same-module helper body already marked by the previous layer should not
    # be duplicated as an opaque RHS risk. Its call arguments still matter when
    # the helper itself was considered safe.
    if existing is None:
        rhs = _rhs_risk_marker(visitor, _assignment_rhs(statement), parameterized=False)
        if rhs is not None:
            parts.append(rhs)

    target = _target_risk_marker(statement)
    if target is not None:
        parts.append(target)
    return _combine_prerequisites(parts)


def _parameterized_blocking_prerequisite(visitor, statement: ast.stmt) -> ast.AST | None:
    existing = prior._previous_parameterized_prerequisite(visitor, statement)
    parts: list[ast.AST] = []
    if existing is not None:
        parts.append(existing)

    if existing is None:
        rhs = _rhs_risk_marker(visitor, _assignment_rhs(statement), parameterized=True)
        if rhs is not None:
            parts.append(rhs)

    target = _target_risk_marker(statement)
    if target is not None:
        parts.append(target)
    return _combine_prerequisites(parts)


_previous_prerequisite_marker = pre._prerequisite_marker


def _prerequisite_marker(node: ast.AST) -> str:
    if _is_risk_marker(node):
        assert isinstance(node, ast.Constant)
        return f"statement:requires-{node.value}"
    return _previous_prerequisite_marker(node)


# Coalesce identical synthetic risk classes across nested blocks. A private
# implementation may contain several operations in the same risk class; the
# public contract is that execution has such a prerequisite, not the number or
# spelling of private statements. Concrete helper/import prerequisites remain
# uncoalesced and retain their detailed dependency semantics.
def _literal_visit_block(self, statements: list[ast.stmt]) -> None:
    blocker: ast.AST | None = None
    for statement in statements:
        if blocker is None:
            self.visit(statement)
        else:
            marker = _prerequisite_marker(blocker)
            coalesced = _is_risk_marker(blocker) and marker in self.context
            if coalesced:
                self.visit(statement)
            else:
                self.context.append(marker)
                self.context_nodes.append(blocker)
                try:
                    self.visit(statement)
                finally:
                    self.context_nodes.pop()
                    self.context.pop()

        candidate = _literal_blocking_prerequisite(self, statement)
        if candidate is not None:
            blocker = candidate


def _parameterized_visit_block(self, statements: list[ast.stmt]) -> None:
    blocker: ast.AST | None = None
    for statement in statements:
        if blocker is None:
            self.visit(statement)
        else:
            marker = _prerequisite_marker(blocker)
            existing_markers = [item[0] for item in self.context_nodes]
            coalesced = _is_risk_marker(blocker) and marker in existing_markers
            if coalesced:
                self.visit(statement)
            else:
                self.context_nodes.append((marker, blocker))
                try:
                    self.visit(statement)
                finally:
                    self.context_nodes.pop()

        candidate = _parameterized_blocking_prerequisite(self, statement)
        if candidate is not None:
            blocker = candidate


def _reachable_parameterized_visit_block(self, statements: list[ast.stmt]) -> None:
    previous_constants = self.constants
    self.constants = dict(previous_constants)
    blocker: ast.AST | None = None
    try:
        for statement in statements:
            if blocker is None:
                self.visit(statement)
            else:
                marker = _prerequisite_marker(blocker)
                existing_markers = [item[0] for item in self.context_nodes]
                coalesced = _is_risk_marker(blocker) and marker in existing_markers
                if coalesced:
                    self.visit(statement)
                else:
                    self.context_nodes.append((marker, blocker))
                    try:
                        self.visit(statement)
                    finally:
                        self.context_nodes.pop()

            candidate = _parameterized_blocking_prerequisite(self, statement)
            if candidate is not None:
                blocker = candidate

            if parameterized_reachability.statement_always_terminates(
                statement,
                self.constants,
            ):
                break
            parameterized_reachability.update_known_constants(statement, self.constants)
    finally:
        self.constants = previous_constants


# Install through every name the previously composed block visitors resolve.
pre._prerequisite_marker = _prerequisite_marker
pre._literal_blocking_prerequisite = _literal_blocking_prerequisite
pre._parameterized_blocking_prerequisite = _parameterized_blocking_prerequisite
prior.statement_prerequisites._literal_blocking_prerequisite = _literal_blocking_prerequisite
prior.statement_prerequisites._parameterized_blocking_prerequisite = _parameterized_blocking_prerequisite
prior._literal_blocking_prerequisite = _literal_blocking_prerequisite
prior._parameterized_blocking_prerequisite = _parameterized_blocking_prerequisite

literal_base.FindingSignatureVisitor._visit_block = _literal_visit_block
parameterized_active.BranchAwareParameterizedCallSiteVisitor._visit_block = _parameterized_visit_block
parameterized_active.base.ParameterizedCallSiteVisitor = parameterized_active.BranchAwareParameterizedCallSiteVisitor
parameterized_reachability.ReachableParameterizedCallSiteVisitor._visit_block = _reachable_parameterized_visit_block


# Statically impossible target binding should also terminate the conservative
# reachability scanners, just as a statically raising RHS already does.
_previous_statement_always_terminates = parameterized_reachability.statement_always_terminates


def _statement_always_terminates(node: ast.stmt, constants=None) -> bool:
    if isinstance(node, (ast.Assign, ast.AnnAssign)):
        rhs = _assignment_rhs(node)
        if any(_target_binding_state(target, rhs) == _RAISES for target in _assignment_targets(node)):
            return True
    return _previous_statement_always_terminates(node, constants)


reachability_semantics.statement_always_terminates = _statement_always_terminates
basic_reachability.statement_always_terminates = _statement_always_terminates
extended_reachability.statement_always_terminates = _statement_always_terminates
parameterized_reachability.statement_always_terminates = _statement_always_terminates


# ---------------------------------------------------------------------------
# Path-sensitive aliases of destructive bound methods
# ---------------------------------------------------------------------------


def _path_requirements(
    node: ast.AST,
    function: ast.FunctionDef | ast.AsyncFunctionDef,
    parents: dict[int, ast.AST],
) -> dict[str, bool]:
    return post_sink._if_requirements(node, function, parents)


def _paths_compatible(
    nodes: list[ast.AST],
    function: ast.FunctionDef | ast.AsyncFunctionDef,
    parents: dict[int, ast.AST],
) -> bool:
    merged: dict[str, bool] = {}
    for node in nodes:
        for key, value in _path_requirements(node, function, parents).items():
            previous = merged.get(key)
            if previous is not None and previous != value:
                return False
            merged[key] = value
    return True


def _path_receiver_aliases_before(
    function: ast.FunctionDef | ast.AsyncFunctionDef,
    receiver: ast.AST,
    finding: ast.Call,
    binding: ast.AST,
    call: ast.Call,
    parents: dict[int, ast.AST],
    cutoff: int,
) -> set[str]:
    receiver_name = sink_state._root_name(receiver)
    if receiver_name is None:
        return set()

    aliases = {receiver_name}
    assignments = sorted(
        (
            item
            for item in ast.walk(function)
            if isinstance(item, (ast.Assign, ast.AnnAssign))
            and sink_state._belongs_to_function(item, function, parents)
            and getattr(item, "lineno", cutoff + 1) < cutoff
        ),
        key=lambda item: (getattr(item, "lineno", 0), getattr(item, "col_offset", 0)),
    )

    for item in assignments:
        if not _paths_compatible([finding, item, binding, call], function, parents):
            continue
        value = item.value
        value_root = sink_state._root_name(value)
        targets = item.targets if isinstance(item, ast.Assign) else [item.target]
        target_names = [target.id for target in targets if isinstance(target, ast.Name)]
        for name in target_names:
            if value_root in aliases:
                aliases.add(name)
            elif name != receiver_name:
                aliases.discard(name)
    return aliases


def _bound_destructive_aliases_before(
    function: ast.FunctionDef | ast.AsyncFunctionDef,
    receiver: ast.AST,
    finding: ast.Call,
    call: ast.Call,
    parents: dict[int, ast.AST],
) -> dict[str, str]:
    cutoff = getattr(call, "lineno", 10**9)
    aliases: dict[str, str] = {}

    bindings = sorted(
        (
            item
            for item in ast.walk(function)
            if isinstance(item, (ast.Assign, ast.AnnAssign, ast.Delete))
            and sink_state._belongs_to_function(item, function, parents)
            and getattr(item, "lineno", cutoff + 1) < cutoff
        ),
        key=lambda item: (getattr(item, "lineno", 0), getattr(item, "col_offset", 0)),
    )

    for item in bindings:
        if not _paths_compatible([finding, item, call], function, parents):
            continue

        if isinstance(item, ast.Delete):
            for target in item.targets:
                if isinstance(target, ast.Name):
                    aliases.pop(target.id, None)
            continue

        value = prior._assignment_value(item)
        target_names = prior._simple_assignment_targets(item)
        if value is None or not target_names:
            continue

        method: str | None = None
        if isinstance(value, ast.Attribute) and value.attr in sink_state._DESTRUCTIVE_SINK_METHODS:
            receiver_aliases = _path_receiver_aliases_before(
                function,
                receiver,
                finding,
                item,
                call,
                parents,
                getattr(item, "lineno", 0) + 1,
            )
            if sink_state._root_name(value.value) in receiver_aliases:
                method = value.attr
        elif isinstance(value, ast.Name):
            method = aliases.get(value.id)

        for target_name in target_names:
            if method is None:
                aliases.pop(target_name, None)
            else:
                aliases[target_name] = method

    return aliases


# The existing post-emission scanner resolves this helper by module-global name.
prior._bound_destructive_aliases_before = _bound_destructive_aliases_before


# ---------------------------------------------------------------------------
# Permanent regressions
# ---------------------------------------------------------------------------


class ReleaseCandidateAssignmentTargetBindingTests(unittest.TestCase):
    def test_attribute_assignment_target_changes_literal_and_sink_contracts(self) -> None:
        direct = '''
from standards_tools import Finding

def run(findings, obj):
    findings.append(Finding("PUBLIC_CODE", "message"))
'''
        blocked = '''
from standards_tools import Finding

def run(findings, obj):
    obj.missing = 1
    findings.append(Finding("PUBLIC_CODE", "message"))
'''
        self.assertNotEqual(
            literal_base.finding_semantic_signatures(direct),
            literal_base.finding_semantic_signatures(blocked),
        )
        self.assertNotEqual(
            sink_execution.finding_semantic_signatures_with_sink(direct),
            sink_execution.finding_semantic_signatures_with_sink(blocked),
        )

    def test_unknown_destructuring_target_changes_contract(self) -> None:
        direct = '''
from standards_tools import Finding

def run(findings, value):
    findings.append(Finding("PUBLIC_CODE", "message"))
'''
        blocked = '''
from standards_tools import Finding

def run(findings, value):
    left, right = value
    findings.append(Finding("PUBLIC_CODE", "message"))
'''
        self.assertNotEqual(
            literal_base.finding_semantic_signatures(direct),
            literal_base.finding_semantic_signatures(blocked),
        )

    def test_known_safe_destructuring_does_not_freeze_implementation(self) -> None:
        direct = '''
from standards_tools import Finding

def run(findings):
    findings.append(Finding("PUBLIC_CODE", "message"))
'''
        safe = '''
from standards_tools import Finding

def run(findings):
    left, right = (1, 2)
    findings.append(Finding("PUBLIC_CODE", "message"))
'''
        self.assertEqual(
            literal_base.finding_semantic_signatures(direct),
            literal_base.finding_semantic_signatures(safe),
        )

    def test_statically_impossible_unpack_hides_later_reachability(self) -> None:
        source = '''
def run():
    left, right = (1,)
    Finding("PUBLIC_CODE", "unreachable")
'''
        self.assertEqual(basic_reachability.reachable_contracts(source, "sample.py"), Counter())
        self.assertEqual(extended_reachability.reachable_contracts(source, "sample.py"), Counter())


class ReleaseCandidatePathSensitiveBoundMethodAliasTests(unittest.TestCase):
    def test_mutually_exclusive_alias_binding_and_call_do_not_change_sink(self) -> None:
        direct = '''
def validate(findings, flag):
    findings.append(Finding("PUBLIC_CODE", "visible"))
'''
        exclusive = '''
def validate(findings, flag):
    if flag:
        clear = findings.clear
    findings.append(Finding("PUBLIC_CODE", "visible"))
    if not flag:
        clear()
'''
        expected = json.loads(
            literal_base.finding_semantic_signatures(direct)["PUBLIC_CODE"][0]
        )["sink"]
        actual = json.loads(
            literal_base.finding_semantic_signatures(exclusive)["PUBLIC_CODE"][0]
        )["sink"]
        self.assertEqual(expected, actual)

    def test_mutually_exclusive_receiver_alias_does_not_create_bound_destructor(self) -> None:
        direct = '''
def validate(findings, flag):
    findings.append(Finding("PUBLIC_CODE", "visible"))
'''
        exclusive = '''
def validate(findings, flag):
    if flag:
        sink_alias = findings
    findings.append(Finding("PUBLIC_CODE", "visible"))
    if not flag:
        clear = sink_alias.clear
        clear()
'''
        expected = json.loads(
            literal_base.finding_semantic_signatures(direct)["PUBLIC_CODE"][0]
        )["sink"]
        actual = json.loads(
            literal_base.finding_semantic_signatures(exclusive)["PUBLIC_CODE"][0]
        )["sink"]
        self.assertEqual(expected, actual)

    def test_same_path_bound_destructor_remains_tracked(self) -> None:
        direct = '''
def validate(findings, flag):
    findings.append(Finding("PUBLIC_CODE", "visible"))
'''
        destructive = '''
def validate(findings, flag):
    if flag:
        clear = findings.clear
        findings.append(Finding("PUBLIC_CODE", "visible"))
        clear()
'''
        self.assertNotEqual(
            literal_base.finding_semantic_signatures(direct),
            literal_base.finding_semantic_signatures(destructive),
        )


if __name__ == "__main__":
    unittest.main()
