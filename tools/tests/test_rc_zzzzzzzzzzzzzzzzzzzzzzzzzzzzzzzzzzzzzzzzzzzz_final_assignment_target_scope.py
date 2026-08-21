from __future__ import annotations

import ast
import unittest
from typing import Any

import rc_finding_code_contracts_base as literal_base
import rc_reachability_semantics as reachability_semantics
import test_rc_extended_finding_reachability as extended_reachability
import test_rc_finding_reachability as basic_reachability
import test_rc_parameterized_finding_codes as parameterized_active
import test_rc_parameterized_finding_reachability as parameterized_reachability
import test_rc_zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz_branch_join_bound_method_aliases as _branch_join  # noqa: F401
import test_rc_zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz_assignment_target_binding_and_path_sensitive_bound_aliases as target_layer


# A subscript store is not uniformly safe or uniformly unsafe. The receiver and
# index expressions execute, and __setitem__ can fail even when both expressions
# evaluate normally. At the same time, treating every subscript store as a
# compatibility prerequisite freezes unrelated private implementation details.
#
# This final composition classifies the store from known execution state. It also
# recognizes the narrow case where an unknown dict-key hashability risk is already
# an unavoidable prerequisite of the immediately following finding-bearing
# statement (for example, the same key is tested with `key in mapping`). In that
# case the earlier store adds no new failure path and must remain compatible.

left_to_right = target_layer.left_to_right
prerequisite_execution = left_to_right.prerequisite_execution

_SAFE = target_layer._SAFE
_UNKNOWN = target_layer._UNKNOWN
_RAISES = target_layer._RAISES
_STATIC_UNKNOWN = prerequisite_execution._STATIC_UNKNOWN
_STATIC_RAISES = prerequisite_execution._STATIC_RAISES

_previous_target_binding_state = target_layer._target_binding_state


def _target_binding_state(target: ast.AST, rhs: ast.AST | None) -> str:
    # Subscript stores need visitor/local-binding context, which the historical
    # target-only helper does not receive. Defer them to the scoped classifier
    # below while retaining the established target logic for every other form.
    if isinstance(target, ast.Subscript):
        return _SAFE
    return _previous_target_binding_state(target, rhs)


target_layer._target_binding_state = _target_binding_state


def _constants(visitor, *, parameterized: bool) -> dict[str, Any]:
    if parameterized:
        return left_to_right._parameterized_constants(visitor)
    return left_to_right._literal_constants(visitor)


def _static_value(node: ast.AST, constants: dict[str, Any]) -> Any:
    return prerequisite_execution._static_eval(node, constants)


def _expression_state(node: ast.AST, constants: dict[str, Any]) -> str:
    return left_to_right._execution_state(node, constants)


def _known_subscript_store_state(
    target: ast.Subscript,
    rhs: ast.AST | None,
    constants: dict[str, Any],
) -> str:
    receiver_state = _expression_state(target.value, constants)
    index_state = _expression_state(target.slice, constants)
    if _RAISES in (receiver_state, index_state):
        return _RAISES
    if _UNKNOWN in (receiver_state, index_state):
        # Evaluation itself may fail before the store operation is attempted.
        return _UNKNOWN

    receiver = _static_value(target.value, constants)
    index = _static_value(target.slice, constants)
    if receiver is _STATIC_RAISES or index is _STATIC_RAISES:
        return _RAISES
    if receiver is _STATIC_UNKNOWN:
        return _UNKNOWN

    # A known dict has a well-defined store contract: the remaining execution
    # risk is whether the key is hashable. Unknown keys remain conservative and
    # are handled by the following-statement redundancy check below.
    if isinstance(receiver, dict):
        if index is _STATIC_UNKNOWN:
            return _UNKNOWN
        try:
            hash(index)
        except Exception:
            return _RAISES
        return _SAFE

    # For a known list, item assignment requires an integer in range. Slice
    # assignment has additional RHS-iterability semantics, so keep it conservative.
    if isinstance(receiver, list):
        if index is _STATIC_UNKNOWN:
            return _UNKNOWN
        if isinstance(index, int) and not isinstance(index, bool):
            if -len(receiver) <= index < len(receiver):
                return _SAFE
            return _RAISES
        if isinstance(index, slice):
            if rhs is None:
                return _UNKNOWN
            rhs_value = _static_value(rhs, constants)
            if rhs_value in (_STATIC_UNKNOWN, _STATIC_RAISES):
                return _UNKNOWN if rhs_value is _STATIC_UNKNOWN else _RAISES
            try:
                iter(rhs_value)
            except Exception:
                return _RAISES
            return _SAFE
        return _RAISES

    # Builtins without an item-assignment slot are guaranteed failures. For a
    # statically known object with a setitem slot that we do not model specially,
    # preserve the possibility of user-defined/runtime failure.
    if not hasattr(type(receiver), "__setitem__"):
        return _RAISES
    return _UNKNOWN


def _same_expression(left: ast.AST, right: ast.AST) -> bool:
    return ast.dump(left, annotate_fields=False, include_attributes=False) == ast.dump(
        right,
        annotate_fields=False,
        include_attributes=False,
    )


def _dict_membership_replays_key_risk(
    following_statement: ast.stmt | None,
    target: ast.Subscript,
    constants: dict[str, Any],
) -> bool:
    """Return True when following execution already requires the same key hash.

    This is intentionally narrow. It exists to keep a private, rebound temporary
    mapping write from becoming a published compatibility fingerprint when the
    finding-bearing statement already performs `same_key in known_dict` before
    it can emit. Unknown-key stores before unconditional emissions remain risky.
    """

    if following_statement is None:
        return False
    receiver = _static_value(target.value, constants)
    index = _static_value(target.slice, constants)
    if not isinstance(receiver, dict) or index is not _STATIC_UNKNOWN:
        return False

    for node in ast.walk(following_statement):
        if not isinstance(node, ast.Compare):
            continue
        left = node.left
        for operator, right in zip(node.ops, node.comparators):
            if isinstance(operator, (ast.In, ast.NotIn)) and _same_expression(
                left, target.slice
            ):
                right_value = _static_value(right, constants)
                if isinstance(right_value, dict):
                    return True
            left = right
    return False


def _subscript_store_prerequisite(
    visitor,
    statement: ast.stmt,
    following_statement: ast.stmt | None,
    *,
    parameterized: bool,
) -> ast.AST | None:
    rhs = target_layer._assignment_rhs(statement)
    constants = _constants(visitor, parameterized=parameterized)
    states: list[str] = []

    for target in target_layer._assignment_targets(statement):
        for item in ast.walk(target):
            if not isinstance(item, ast.Subscript) or not isinstance(item.ctx, ast.Store):
                continue
            state = _known_subscript_store_state(item, rhs, constants)
            if state == _UNKNOWN and _dict_membership_replays_key_risk(
                following_statement,
                item,
                constants,
            ):
                state = _SAFE
            states.append(state)

    if not states or all(state == _SAFE for state in states):
        return None
    if _RAISES in states:
        return target_layer._risk_marker("target-raises", "subscript-store")
    return target_layer._risk_marker("target-may-fail", "subscript-store")


def _combined_candidate(existing: ast.AST | None, extra: ast.AST | None) -> ast.AST | None:
    parts = [item for item in (existing, extra) if item is not None]
    return target_layer._combine_prerequisites(parts)


def _literal_visit_block(self, statements: list[ast.stmt]) -> None:
    blocker: ast.AST | None = None
    for index, statement in enumerate(statements):
        following = statements[index + 1] if index + 1 < len(statements) else None
        if blocker is None:
            self.visit(statement)
        else:
            marker = target_layer._prerequisite_marker(blocker)
            coalesced = target_layer._is_risk_marker(blocker) and marker in self.context
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

        existing = target_layer._literal_blocking_prerequisite(self, statement)
        subscript = _subscript_store_prerequisite(
            self,
            statement,
            following,
            parameterized=False,
        )
        candidate = _combined_candidate(existing, subscript)
        if candidate is not None:
            blocker = candidate


def _parameterized_visit_block(self, statements: list[ast.stmt]) -> None:
    blocker: ast.AST | None = None
    for index, statement in enumerate(statements):
        following = statements[index + 1] if index + 1 < len(statements) else None
        if blocker is None:
            self.visit(statement)
        else:
            marker = target_layer._prerequisite_marker(blocker)
            existing_markers = [item[0] for item in self.context_nodes]
            coalesced = target_layer._is_risk_marker(blocker) and marker in existing_markers
            if coalesced:
                self.visit(statement)
            else:
                self.context_nodes.append((marker, blocker))
                try:
                    self.visit(statement)
                finally:
                    self.context_nodes.pop()

        existing = target_layer._parameterized_blocking_prerequisite(self, statement)
        subscript = _subscript_store_prerequisite(
            self,
            statement,
            following,
            parameterized=True,
        )
        candidate = _combined_candidate(existing, subscript)
        if candidate is not None:
            blocker = candidate


def _reachable_parameterized_visit_block(self, statements: list[ast.stmt]) -> None:
    previous_constants = self.constants
    self.constants = dict(previous_constants)
    blocker: ast.AST | None = None
    try:
        for index, statement in enumerate(statements):
            following = statements[index + 1] if index + 1 < len(statements) else None
            if blocker is None:
                self.visit(statement)
            else:
                marker = target_layer._prerequisite_marker(blocker)
                existing_markers = [item[0] for item in self.context_nodes]
                coalesced = target_layer._is_risk_marker(blocker) and marker in existing_markers
                if coalesced:
                    self.visit(statement)
                else:
                    self.context_nodes.append((marker, blocker))
                    try:
                        self.visit(statement)
                    finally:
                        self.context_nodes.pop()

            existing = target_layer._parameterized_blocking_prerequisite(self, statement)
            subscript = _subscript_store_prerequisite(
                self,
                statement,
                following,
                parameterized=True,
            )
            candidate = _combined_candidate(existing, subscript)
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


literal_base.FindingSignatureVisitor._visit_block = _literal_visit_block
parameterized_active.BranchAwareParameterizedCallSiteVisitor._visit_block = _parameterized_visit_block
parameterized_active.base.ParameterizedCallSiteVisitor = parameterized_active.BranchAwareParameterizedCallSiteVisitor
parameterized_reachability.ReachableParameterizedCallSiteVisitor._visit_block = _reachable_parameterized_visit_block


_previous_statement_always_terminates = parameterized_reachability.statement_always_terminates


def _statement_always_terminates(node: ast.stmt, constants=None) -> bool:
    known = {} if constants is None else constants
    if isinstance(node, (ast.Assign, ast.AnnAssign, ast.AugAssign)):
        rhs = target_layer._assignment_rhs(node)
        for target in target_layer._assignment_targets(node):
            for item in ast.walk(target):
                if isinstance(item, ast.Subscript) and isinstance(item.ctx, ast.Store):
                    if _known_subscript_store_state(item, rhs, known) == _RAISES:
                        return True
    return _previous_statement_always_terminates(node, constants)


reachability_semantics.statement_always_terminates = _statement_always_terminates
basic_reachability.statement_always_terminates = _statement_always_terminates
extended_reachability.statement_always_terminates = _statement_always_terminates
parameterized_reachability.statement_always_terminates = _statement_always_terminates


class ReleaseCandidateScopedSubscriptTargetTests(unittest.TestCase):
    def test_rebound_private_subscript_write_remains_compatible(self) -> None:
        original = '''
def run(document_id):
    ids = {}
    if document_id in ids:
        Finding("DUPLICATE_ID", "duplicate", path="sample")
'''
        unrelated = '''
def run(document_id):
    ids = {}
    alias = ids
    alias = {}
    alias[document_id] = "unrelated"
    if document_id in ids:
        Finding("DUPLICATE_ID", "duplicate", path="sample")
'''
        self.assertEqual(
            literal_base.finding_semantic_signatures(original),
            literal_base.finding_semantic_signatures(unrelated),
        )

    def test_dependency_subscript_mutation_is_still_semantic(self) -> None:
        original = '''
def run(document_id):
    ids = {}
    if document_id in ids:
        Finding("DUPLICATE_ID", "duplicate", path="sample")
'''
        mutated = '''
def run(document_id):
    ids = {}
    ids[document_id] = "seen"
    if document_id in ids:
        Finding("DUPLICATE_ID", "duplicate", path="sample")
'''
        self.assertNotEqual(
            literal_base.finding_semantic_signatures(original),
            literal_base.finding_semantic_signatures(mutated),
        )

    def test_known_non_subscriptable_receiver_blocks_emission(self) -> None:
        direct = '''
def run(findings, value):
    findings.append(Finding("PUBLIC_CODE", "message"))
'''
        blocked = '''
def run(findings, value):
    target = None
    target["key"] = value
    findings.append(Finding("PUBLIC_CODE", "message"))
'''
        self.assertNotEqual(
            literal_base.finding_semantic_signatures(direct),
            literal_base.finding_semantic_signatures(blocked),
        )

    def test_known_safe_dict_store_does_not_freeze_implementation(self) -> None:
        direct = '''
def run(findings, value):
    findings.append(Finding("PUBLIC_CODE", "message"))
'''
        safe = '''
def run(findings, value):
    target = {}
    target["key"] = value
    findings.append(Finding("PUBLIC_CODE", "message"))
'''
        self.assertEqual(
            literal_base.finding_semantic_signatures(direct),
            literal_base.finding_semantic_signatures(safe),
        )

    def test_known_unhashable_dict_key_blocks_emission(self) -> None:
        direct = '''
def run(findings, value):
    findings.append(Finding("PUBLIC_CODE", "message"))
'''
        blocked = '''
def run(findings, value):
    target = {}
    target[[]] = value
    findings.append(Finding("PUBLIC_CODE", "message"))
'''
        self.assertNotEqual(
            literal_base.finding_semantic_signatures(direct),
            literal_base.finding_semantic_signatures(blocked),
        )

    def test_unknown_dict_key_before_unconditional_emission_is_prerequisite(self) -> None:
        direct = '''
def run(findings, key, value):
    findings.append(Finding("PUBLIC_CODE", "message"))
'''
        risky = '''
def run(findings, key, value):
    target = {}
    target[key] = value
    findings.append(Finding("PUBLIC_CODE", "message"))
'''
        self.assertNotEqual(
            literal_base.finding_semantic_signatures(direct),
            literal_base.finding_semantic_signatures(risky),
        )

    def test_same_key_membership_replays_unknown_dict_hashability_risk(self) -> None:
        direct = '''
def run(key):
    ids = {}
    if key in ids:
        Finding("PUBLIC_CODE", "message")
'''
        redundant = '''
def run(key):
    ids = {}
    temp = {}
    temp[key] = "unrelated"
    if key in ids:
        Finding("PUBLIC_CODE", "message")
'''
        self.assertEqual(
            literal_base.finding_semantic_signatures(direct),
            literal_base.finding_semantic_signatures(redundant),
        )


if __name__ == "__main__":
    unittest.main()
