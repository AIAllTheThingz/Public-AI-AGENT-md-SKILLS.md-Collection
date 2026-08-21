from __future__ import annotations

import ast
import unittest

import test_rc_zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz_final_pr71_closure as prior


# Final composition for the exact-head failures and the subsequent assert P1.
#
# The preceding execution layers intentionally distinguish true compatibility
# prerequisites from harmless private implementation detail. Two details were
# still missing from that composition:
#
# * bindings established by straight-line statements were not being added to
#   the path's "definitely bound" set, so a later `alias = ids` could be
#   misclassified as a potentially failing name load even after `ids = {}`;
# * `assert` executes before a following emission and can either fail while
#   evaluating its test or raise AssertionError when the test is false.
#
# This layer adds path-local sequential binding proof and assert prerequisites
# without weakening the existing assignment-target or sink checks.


assignment_scope = prior.assignment_scope
target_layer = assignment_scope.target_layer
literal_base = assignment_scope.literal_base
parameterized_active = assignment_scope.parameterized_active
parameterized_reachability = assignment_scope.parameterized_reachability
sink_execution = target_layer.sink_execution

_SAFE = assignment_scope._SAFE
_UNKNOWN = assignment_scope._UNKNOWN
_RAISES = assignment_scope._RAISES
_STATIC_UNKNOWN = prior._STATIC_UNKNOWN
_STATIC_RAISES = prior._STATIC_RAISES


# ---------------------------------------------------------------------------
# Assert execution prerequisites
# ---------------------------------------------------------------------------

_previous_literal_blocking_prerequisite = target_layer._literal_blocking_prerequisite
_previous_parameterized_blocking_prerequisite = (
    target_layer._parameterized_blocking_prerequisite
)


def _assert_static_state(visitor, statement: ast.Assert, *, parameterized: bool) -> str:
    constants = prior._constants(visitor, parameterized=parameterized)
    value = prior._static_literal_value(statement.test, constants)
    if value is _STATIC_RAISES:
        return _RAISES
    if value is _STATIC_UNKNOWN:
        return _UNKNOWN
    try:
        return _SAFE if bool(value) else _RAISES
    except Exception:
        return _UNKNOWN


def _assert_message_dependency(
    visitor,
    message: ast.AST | None,
    *,
    parameterized: bool,
) -> ast.AST | None:
    if message is None or isinstance(message, ast.Constant):
        return None

    # Keep literal/editorial assertion wording out of the compatibility identity,
    # but preserve executable message evaluation. The message is evaluated only
    # on the failing assertion path, so its role is dependency identity rather
    # than reachability of the subsequent finding.
    constants = prior._constants(visitor, parameterized=parameterized)
    value = prior._static_literal_value(message, constants)
    if value is not _STATIC_UNKNOWN and value is not _STATIC_RAISES:
        return None
    return message


def _assert_prerequisite(
    visitor,
    statement: ast.stmt,
    *,
    parameterized: bool,
) -> ast.AST | None:
    if not isinstance(statement, ast.Assert):
        return None

    state = _assert_static_state(visitor, statement, parameterized=parameterized)
    if state == _SAFE:
        return None

    message = _assert_message_dependency(
        visitor,
        statement.msg,
        parameterized=parameterized,
    )
    prerequisite = ast.Assert(test=statement.test, msg=message)
    ast.copy_location(prerequisite, statement)
    ast.fix_missing_locations(prerequisite)
    return prerequisite


def _literal_blocking_prerequisite(visitor, statement: ast.stmt) -> ast.AST | None:
    existing = _previous_literal_blocking_prerequisite(visitor, statement)
    assertion = _assert_prerequisite(visitor, statement, parameterized=False)
    return target_layer._combine_prerequisites(
        [item for item in (existing, assertion) if item is not None]
    )


def _parameterized_blocking_prerequisite(
    visitor,
    statement: ast.stmt,
) -> ast.AST | None:
    existing = _previous_parameterized_blocking_prerequisite(visitor, statement)
    assertion = _assert_prerequisite(visitor, statement, parameterized=True)
    return target_layer._combine_prerequisites(
        [item for item in (existing, assertion) if item is not None]
    )


target_layer._literal_blocking_prerequisite = _literal_blocking_prerequisite
target_layer._parameterized_blocking_prerequisite = (
    _parameterized_blocking_prerequisite
)


# ---------------------------------------------------------------------------
# Sequential definite-binding proof
# ---------------------------------------------------------------------------


def _bound_names_from_target(target: ast.AST) -> set[str]:
    if isinstance(target, ast.Name):
        return {target.id}
    if isinstance(target, ast.Starred):
        return _bound_names_from_target(target.value)
    if isinstance(target, (ast.Tuple, ast.List)):
        result: set[str] = set()
        for item in target.elts:
            result.update(_bound_names_from_target(item))
        return result
    return set()


def _deleted_names_from_target(target: ast.AST) -> set[str]:
    if isinstance(target, ast.Name):
        return {target.id}
    if isinstance(target, ast.Starred):
        return _deleted_names_from_target(target.value)
    if isinstance(target, (ast.Tuple, ast.List)):
        result: set[str] = set()
        for item in target.elts:
            result.update(_deleted_names_from_target(item))
        return result
    return set()


def _statement_bound_names(statement: ast.stmt) -> set[str]:
    if isinstance(statement, ast.Assign):
        result: set[str] = set()
        for target in statement.targets:
            result.update(_bound_names_from_target(target))
        return result

    if isinstance(statement, ast.AnnAssign):
        if statement.value is None:
            return set()
        return _bound_names_from_target(statement.target)

    if isinstance(statement, ast.AugAssign):
        return _bound_names_from_target(statement.target)

    if isinstance(statement, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
        return {statement.name}

    if isinstance(statement, ast.Import):
        return {
            alias.asname or alias.name.split(".", 1)[0]
            for alias in statement.names
        }

    if isinstance(statement, ast.ImportFrom):
        return {
            alias.asname or alias.name
            for alias in statement.names
            if alias.name != "*"
        }

    return set()


def _record_sequential_binding_state(visitor, statement: ast.stmt) -> None:
    bound = getattr(visitor, "_definitely_bound_names", None)
    if not isinstance(bound, set):
        return

    if isinstance(statement, ast.Delete):
        for target in statement.targets:
            bound.difference_update(_deleted_names_from_target(target))
        return

    bound.update(_statement_bound_names(statement))


def _push_block_binding_scope(visitor):
    previous = getattr(visitor, "_definitely_bound_names", None)
    if isinstance(previous, set):
        visitor._definitely_bound_names = set(previous)
    return previous


def _pop_block_binding_scope(visitor, previous) -> None:
    if isinstance(previous, set):
        visitor._definitely_bound_names = previous
    else:
        visitor.__dict__.pop("_definitely_bound_names", None)


# Recompose the final scoped subscript block visitors with one addition:
# after a straight-line statement has executed, bindings it establishes are
# provably available to the next statement on that same execution path.
def _literal_visit_block(self, statements: list[ast.stmt]) -> None:
    previous_bound = _push_block_binding_scope(self)
    blocker: ast.AST | None = None
    try:
        for index, statement in enumerate(statements):
            following = statements[index + 1] if index + 1 < len(statements) else None

            if blocker is None:
                self.visit(statement)
            else:
                marker = target_layer._prerequisite_marker(blocker)
                coalesced = (
                    target_layer._is_risk_marker(blocker)
                    and marker in self.context
                )
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
            subscript = assignment_scope._subscript_store_prerequisite(
                self,
                statement,
                following,
                parameterized=False,
            )
            candidate = assignment_scope._combined_candidate(existing, subscript)
            if candidate is not None:
                blocker = candidate

            _record_sequential_binding_state(self, statement)
    finally:
        _pop_block_binding_scope(self, previous_bound)


def _parameterized_visit_block(self, statements: list[ast.stmt]) -> None:
    previous_bound = _push_block_binding_scope(self)
    blocker: ast.AST | None = None
    try:
        for index, statement in enumerate(statements):
            following = statements[index + 1] if index + 1 < len(statements) else None

            if blocker is None:
                self.visit(statement)
            else:
                marker = target_layer._prerequisite_marker(blocker)
                existing_markers = [item[0] for item in self.context_nodes]
                coalesced = (
                    target_layer._is_risk_marker(blocker)
                    and marker in existing_markers
                )
                if coalesced:
                    self.visit(statement)
                else:
                    self.context_nodes.append((marker, blocker))
                    try:
                        self.visit(statement)
                    finally:
                        self.context_nodes.pop()

            existing = target_layer._parameterized_blocking_prerequisite(
                self,
                statement,
            )
            subscript = assignment_scope._subscript_store_prerequisite(
                self,
                statement,
                following,
                parameterized=True,
            )
            candidate = assignment_scope._combined_candidate(existing, subscript)
            if candidate is not None:
                blocker = candidate

            _record_sequential_binding_state(self, statement)
    finally:
        _pop_block_binding_scope(self, previous_bound)


def _reachable_parameterized_visit_block(self, statements: list[ast.stmt]) -> None:
    previous_constants = self.constants
    previous_bound = _push_block_binding_scope(self)
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
                coalesced = (
                    target_layer._is_risk_marker(blocker)
                    and marker in existing_markers
                )
                if coalesced:
                    self.visit(statement)
                else:
                    self.context_nodes.append((marker, blocker))
                    try:
                        self.visit(statement)
                    finally:
                        self.context_nodes.pop()

            existing = target_layer._parameterized_blocking_prerequisite(
                self,
                statement,
            )
            subscript = assignment_scope._subscript_store_prerequisite(
                self,
                statement,
                following,
                parameterized=True,
            )
            candidate = assignment_scope._combined_candidate(existing, subscript)
            if candidate is not None:
                blocker = candidate

            _record_sequential_binding_state(self, statement)

            if parameterized_reachability.statement_always_terminates(
                statement,
                self.constants,
            ):
                break
            parameterized_reachability.update_known_constants(
                statement,
                self.constants,
            )
    finally:
        self.constants = previous_constants
        _pop_block_binding_scope(self, previous_bound)


literal_base.FindingSignatureVisitor._visit_block = _literal_visit_block
parameterized_active.BranchAwareParameterizedCallSiteVisitor._visit_block = (
    _parameterized_visit_block
)
parameterized_active.base.ParameterizedCallSiteVisitor = (
    parameterized_active.BranchAwareParameterizedCallSiteVisitor
)
parameterized_reachability.ReachableParameterizedCallSiteVisitor._visit_block = (
    _reachable_parameterized_visit_block
)


# ---------------------------------------------------------------------------
# Permanent regressions
# ---------------------------------------------------------------------------


class ReleaseCandidateAssertAndStraightlineBindingClosureTests(unittest.TestCase):
    def test_rebound_private_alias_write_remains_compatible(self) -> None:
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

    def test_straightline_bound_name_is_not_rhs_risk(self) -> None:
        direct = '''
def run(findings):
    findings.append(Finding("PUBLIC_CODE", "message"))
'''
        with_local = '''
def run(findings):
    local = {}
    alias = local
    findings.append(Finding("PUBLIC_CODE", "message"))
'''
        self.assertEqual(
            literal_base.finding_semantic_signatures(direct),
            literal_base.finding_semantic_signatures(with_local),
        )

    def test_conditionally_bound_name_stays_a_prerequisite(self) -> None:
        direct = '''
def run(findings, enabled):
    findings.append(Finding("PUBLIC_CODE", "message"))
'''
        conditional = '''
def run(findings, enabled):
    if enabled:
        local = {}
    alias = local
    findings.append(Finding("PUBLIC_CODE", "message"))
'''
        self.assertNotEqual(
            literal_base.finding_semantic_signatures(direct),
            literal_base.finding_semantic_signatures(conditional),
        )

    def test_assert_flag_changes_literal_contract(self) -> None:
        direct = '''
def run(findings, flag):
    findings.append(Finding("PUBLIC_CODE", "message"))
'''
        guarded = '''
def run(findings, flag):
    assert flag
    findings.append(Finding("PUBLIC_CODE", "message"))
'''
        expected = literal_base.finding_semantic_signatures(direct)
        actual = literal_base.finding_semantic_signatures(guarded)
        self.assertNotEqual(expected, actual)
        self.assertTrue(
            any("statement:requires-prior-execution" in item for item in actual["PUBLIC_CODE"])
        )

    def test_assert_flag_changes_sink_contract(self) -> None:
        direct = '''
def run(findings, flag):
    findings.append(Finding("PUBLIC_CODE", "message"))
'''
        guarded = '''
def run(findings, flag):
    assert flag
    findings.append(Finding("PUBLIC_CODE", "message"))
'''
        self.assertNotEqual(
            sink_execution.finding_semantic_signatures_with_sink(direct),
            sink_execution.finding_semantic_signatures_with_sink(guarded),
        )

    def test_assert_flag_changes_parameterized_contract(self) -> None:
        direct = '''
def read_text(path, findings, code):
    Finding(code, "decode failed", path="sample")
def validate(root, findings, flag):
    read_text(root / "LICENSE", findings, "LICENSE_ENCODING")
'''
        guarded = '''
def read_text(path, findings, code):
    Finding(code, "decode failed", path="sample")
def validate(root, findings, flag):
    assert flag
    read_text(root / "LICENSE", findings, "LICENSE_ENCODING")
'''
        self.assertNotEqual(
            parameterized_active.parameterized_finding_contracts(
                direct,
                "sample.py",
            ),
            parameterized_active.parameterized_finding_contracts(
                guarded,
                "sample.py",
            ),
        )

    def test_assert_true_does_not_freeze_implementation(self) -> None:
        direct = '''
def run(findings):
    findings.append(Finding("PUBLIC_CODE", "message"))
'''
        guarded = '''
def run(findings):
    assert True, explode()
    findings.append(Finding("PUBLIC_CODE", "message"))
'''
        self.assertEqual(
            literal_base.finding_semantic_signatures(direct),
            literal_base.finding_semantic_signatures(guarded),
        )

    def test_literal_assert_message_rewording_is_compatible(self) -> None:
        first = '''
def run(findings, flag):
    assert flag, "first wording"
    findings.append(Finding("PUBLIC_CODE", "message"))
'''
        second = first.replace("first wording", "second wording")
        self.assertEqual(
            literal_base.finding_semantic_signatures(first),
            literal_base.finding_semantic_signatures(second),
        )

    def test_executable_assert_message_is_preserved(self) -> None:
        safe = '''
def build_message():
    return "message"
def run(findings, flag):
    assert flag, build_message()
    findings.append(Finding("PUBLIC_CODE", "message"))
'''
        raising = '''
def build_message():
    raise RuntimeError("message construction failed")
def run(findings, flag):
    assert flag, build_message()
    findings.append(Finding("PUBLIC_CODE", "message"))
'''
        self.assertNotEqual(
            literal_base.finding_semantic_signatures(safe),
            literal_base.finding_semantic_signatures(raising),
        )


if __name__ == "__main__":
    unittest.main()
