from __future__ import annotations

import ast
import unittest

import test_rc_zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz_assert_and_straightline_binding_closure as prior


# A standalone expression statement executes before the next statement just as
# an assignment RHS does.  The earlier statement-prerequisite layer deliberately
# special-cases calls so helper semantics can be modeled without freezing every
# private call site, but that left non-call expressions such as `value + 1`
# invisible.  Reuse the already-composed expression-state classifier here and
# record only the semantic risk class, not the private expression spelling.

assignment_scope = prior.assignment_scope
target_layer = prior.target_layer
literal_base = prior.literal_base
parameterized_active = prior.parameterized_active
sink_execution = prior.sink_execution

_SAFE = prior._SAFE
_UNKNOWN = prior._UNKNOWN
_RAISES = prior._RAISES

_STATEMENT_MARKER_PREFIX = "statement-execution:"

_previous_literal_blocking_prerequisite = target_layer._literal_blocking_prerequisite
_previous_parameterized_blocking_prerequisite = (
    target_layer._parameterized_blocking_prerequisite
)
_previous_prerequisite_marker = target_layer._prerequisite_marker
_previous_is_risk_marker = target_layer._is_risk_marker


def _statement_risk_marker(kind: str) -> ast.Constant:
    return ast.Constant(value=f"{_STATEMENT_MARKER_PREFIX}{kind}")


def _is_statement_risk_marker(node: ast.AST) -> bool:
    return (
        isinstance(node, ast.Constant)
        and isinstance(node.value, str)
        and node.value.startswith(_STATEMENT_MARKER_PREFIX)
    )


def _is_risk_marker(node: ast.AST) -> bool:
    return _previous_is_risk_marker(node) or _is_statement_risk_marker(node)


def _prerequisite_marker(node: ast.AST) -> str:
    if _is_statement_risk_marker(node):
        assert isinstance(node, ast.Constant)
        return f"statement:requires-{node.value}"
    return _previous_prerequisite_marker(node)


# The latest block visitors resolve these helpers from target_layer at runtime,
# so teach their existing risk-marker coalescing about this new semantic class.
target_layer._is_risk_marker = _is_risk_marker
target_layer._prerequisite_marker = _prerequisite_marker


def _expression_statement_prerequisite(
    visitor,
    statement: ast.stmt,
    *,
    parameterized: bool,
) -> ast.AST | None:
    if not isinstance(statement, ast.Expr):
        return None

    value = statement.value

    # Calls already have dedicated same-module helper, invocation-argument,
    # process-exit, and parameterized-helper semantics.  Broadly reclassifying
    # every call here would recreate the implementation-detail churn that the
    # previous layers intentionally avoided.  This closure is for the uncovered
    # non-call expression-statement boundary reported by review.
    if isinstance(value, ast.Call):
        return None

    state = assignment_scope.target_layer._expression_state(
        visitor,
        value,
        parameterized=parameterized,
    )
    if state == _RAISES:
        return _statement_risk_marker("expr-raises")
    if state == _UNKNOWN:
        return _statement_risk_marker("expr-may-fail")
    return None


def _literal_blocking_prerequisite(visitor, statement: ast.stmt) -> ast.AST | None:
    existing = _previous_literal_blocking_prerequisite(visitor, statement)
    expression = None
    if existing is None:
        expression = _expression_statement_prerequisite(
            visitor,
            statement,
            parameterized=False,
        )
    return target_layer._combine_prerequisites(
        [item for item in (existing, expression) if item is not None]
    )


def _parameterized_blocking_prerequisite(
    visitor,
    statement: ast.stmt,
) -> ast.AST | None:
    existing = _previous_parameterized_blocking_prerequisite(visitor, statement)
    expression = None
    if existing is None:
        expression = _expression_statement_prerequisite(
            visitor,
            statement,
            parameterized=True,
        )
    return target_layer._combine_prerequisites(
        [item for item in (existing, expression) if item is not None]
    )


target_layer._literal_blocking_prerequisite = _literal_blocking_prerequisite
target_layer._parameterized_blocking_prerequisite = (
    _parameterized_blocking_prerequisite
)


class ReleaseCandidateExpressionStatementPrerequisiteTests(unittest.TestCase):
    def test_dynamic_expression_statement_changes_literal_contract(self) -> None:
        direct = '''
def run(findings, value):
    findings.append(Finding("PUBLIC_CODE", "message"))
'''
        preceded = '''
def run(findings, value):
    value + 1
    findings.append(Finding("PUBLIC_CODE", "message"))
'''
        expected = literal_base.finding_semantic_signatures(direct)
        actual = literal_base.finding_semantic_signatures(preceded)
        self.assertNotEqual(expected, actual)
        self.assertTrue(
            any(
                "statement-execution:expr-may-fail" in signature
                for signature in actual["PUBLIC_CODE"]
            )
        )

    def test_dynamic_expression_statement_changes_sink_contract(self) -> None:
        direct = '''
def run(findings, value):
    findings.append(Finding("PUBLIC_CODE", "message"))
'''
        preceded = '''
def run(findings, value):
    value + 1
    findings.append(Finding("PUBLIC_CODE", "message"))
'''
        self.assertNotEqual(
            sink_execution.finding_semantic_signatures_with_sink(direct),
            sink_execution.finding_semantic_signatures_with_sink(preceded),
        )

    def test_dynamic_expression_statement_changes_parameterized_contract(self) -> None:
        direct = '''
def read_text(path, findings, code):
    Finding(code, "decode failed", path="sample")
def validate(root, findings, value):
    read_text(root / "LICENSE", findings, "LICENSE_ENCODING")
'''
        preceded = '''
def read_text(path, findings, code):
    Finding(code, "decode failed", path="sample")
def validate(root, findings, value):
    value + 1
    read_text(root / "LICENSE", findings, "LICENSE_ENCODING")
'''
        self.assertNotEqual(
            parameterized_active.parameterized_finding_contracts(
                direct,
                "sample.py",
            ),
            parameterized_active.parameterized_finding_contracts(
                preceded,
                "sample.py",
            ),
        )

    def test_statically_safe_expression_statement_does_not_freeze_detail(self) -> None:
        direct = '''
def run(findings):
    findings.append(Finding("PUBLIC_CODE", "message"))
'''
        preceded = '''
def run(findings):
    1 + 1
    findings.append(Finding("PUBLIC_CODE", "message"))
'''
        self.assertEqual(
            literal_base.finding_semantic_signatures(direct),
            literal_base.finding_semantic_signatures(preceded),
        )

    def test_straightline_constant_expression_statement_is_safe(self) -> None:
        direct = '''
def run(findings):
    findings.append(Finding("PUBLIC_CODE", "message"))
'''
        preceded = '''
def run(findings):
    value = 1
    value + 1
    findings.append(Finding("PUBLIC_CODE", "message"))
'''
        self.assertEqual(
            literal_base.finding_semantic_signatures(direct),
            literal_base.finding_semantic_signatures(preceded),
        )


if __name__ == "__main__":
    unittest.main()
