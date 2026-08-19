from __future__ import annotations

import ast
import unittest

import rc_finding_code_contracts_base as literal_base
import test_rc_parameterized_finding_codes as parameterized_active
import test_rc_parameterized_finding_reachability as parameterized_reachability
import test_rc_zzz_finding_emission_sink as sink_execution
import test_rc_zzzzzzzzzzzzzzzzzzzzzzzzzzz_left_to_right_expression_execution as left_to_right
import test_rc_zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz_definition_defaults_and_bound_names as bound_names_layer
import test_rc_zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz_final_p1_and_ci_composition as final_composition  # noqa: F401


# A Finding can be unreachable because an earlier *statement* fails, not only
# because an earlier sibling in the same expression fails. Preserve those
# execution prerequisites in literal, sink, and caller-supplied-code contracts.


def _statement_execution_expression(statement: ast.stmt) -> ast.AST | None:
    if isinstance(statement, ast.Expr):
        return statement.value
    if isinstance(statement, ast.Assign):
        return statement.value
    if isinstance(statement, ast.AnnAssign):
        return statement.value
    if isinstance(statement, ast.AugAssign):
        # Augmented assignment evaluates its target/value and dynamic operator.
        # The complete statement is retained when execution cannot be proven safe.
        return statement
    return None


def _literal_statement_execution_state(
    visitor,
    statement: ast.stmt,
) -> tuple[str, ast.AST | None]:
    expression = _statement_execution_expression(statement)
    if expression is None:
        return left_to_right._SAFE, None

    if isinstance(expression, ast.stmt):
        return left_to_right._UNKNOWN, statement

    constants = left_to_right._literal_constants(visitor)
    state = bound_names_layer._visitor_execution_state(visitor, expression, constants)
    return state, expression


def _parameterized_statement_execution_state(
    visitor,
    statement: ast.stmt,
) -> tuple[str, ast.AST | None]:
    expression = _statement_execution_expression(statement)
    if expression is None:
        return left_to_right._SAFE, None

    if isinstance(expression, ast.stmt):
        return left_to_right._UNKNOWN, statement

    constants = left_to_right._parameterized_constants(visitor)
    state = bound_names_layer._visitor_execution_state(visitor, expression, constants)
    return state, expression


def _visit_block_with_statement_prerequisites(self, statements: list[ast.stmt]) -> None:
    prerequisites: list[ast.AST] = []

    for statement in statements:
        if prerequisites:
            self.context.append("statement:requires-prior-execution")
            self.context_nodes.append(left_to_right._prerequisite_node(prerequisites))
            try:
                self.visit(statement)
            finally:
                self.context_nodes.pop()
                self.context.pop()
        else:
            self.visit(statement)

        state, expression = _literal_statement_execution_state(self, statement)
        if expression is not None and state in {
            left_to_right._UNKNOWN,
            left_to_right._RAISES,
        }:
            prerequisites.append(expression)


literal_base.FindingSignatureVisitor._visit_block = _visit_block_with_statement_prerequisites


_parameterized_visitor = parameterized_active.BranchAwareParameterizedCallSiteVisitor


def _parameterized_visit_block_with_statement_prerequisites(
    self,
    statements: list[ast.stmt],
) -> None:
    prerequisites: list[ast.AST] = []

    for statement in statements:
        if prerequisites:
            self.context_nodes.append(
                (
                    "statement:requires-prior-execution",
                    left_to_right._prerequisite_node(prerequisites),
                )
            )
            try:
                self.visit(statement)
            finally:
                self.context_nodes.pop()
        else:
            self.visit(statement)

        state, expression = _parameterized_statement_execution_state(self, statement)
        if expression is not None and state in {
            left_to_right._UNKNOWN,
            left_to_right._RAISES,
        }:
            prerequisites.append(expression)


_parameterized_visitor._visit_block = _parameterized_visit_block_with_statement_prerequisites
parameterized_active.base.ParameterizedCallSiteVisitor = _parameterized_visitor


_reachable_parameterized_visitor = (
    parameterized_reachability.ReachableParameterizedCallSiteVisitor
)


def _reachable_parameterized_visit_block_with_statement_prerequisites(
    self,
    statements: list[ast.stmt],
) -> None:
    previous_constants = self.constants
    self.constants = dict(previous_constants)
    prerequisites: list[ast.AST] = []
    try:
        for statement in statements:
            if prerequisites:
                self.context_nodes.append(
                    (
                        "statement:requires-prior-execution",
                        left_to_right._prerequisite_node(prerequisites),
                    )
                )
                try:
                    self.visit(statement)
                finally:
                    self.context_nodes.pop()
            else:
                self.visit(statement)

            state, expression = _parameterized_statement_execution_state(
                self,
                statement,
            )
            if expression is not None and state in {
                left_to_right._UNKNOWN,
                left_to_right._RAISES,
            }:
                prerequisites.append(expression)

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


_reachable_parameterized_visitor._visit_block = (
    _reachable_parameterized_visit_block_with_statement_prerequisites
)


class ReleaseCandidatePreEmissionStatementPrerequisiteTests(unittest.TestCase):
    def test_raising_helper_statement_changes_literal_contract(self) -> None:
        direct = '''
from standards_tools import Finding

def run(findings):
    findings.append(Finding("PUBLIC_CODE", "message"))
'''
        preceded = '''
from standards_tools import Finding

def explode():
    raise RuntimeError("stop")

def run(findings):
    explode()
    findings.append(Finding("PUBLIC_CODE", "message"))
'''

        expected = literal_base.finding_semantic_signatures(direct)
        actual = literal_base.finding_semantic_signatures(preceded)
        self.assertNotEqual(expected, actual)
        self.assertTrue(
            any(
                "statement:requires-prior-execution" in signature
                and "explode" in signature
                for signature in actual["PUBLIC_CODE"]
            )
        )

    def test_raising_helper_statement_changes_sink_contract(self) -> None:
        direct = '''
from standards_tools import Finding

def run(findings):
    findings.append(Finding("PUBLIC_CODE", "message"))
'''
        preceded = '''
from standards_tools import Finding

def explode():
    raise RuntimeError("stop")

def run(findings):
    explode()
    findings.append(Finding("PUBLIC_CODE", "message"))
'''
        self.assertNotEqual(
            sink_execution.finding_semantic_signatures_with_sink(direct),
            sink_execution.finding_semantic_signatures_with_sink(preceded),
        )

    def test_raising_helper_statement_changes_parameterized_contract(self) -> None:
        direct = '''
def read_text(path, findings, code):
    Finding(code, "decode failed", path="sample")
def validate(root, findings):
    read_text(root / "LICENSE", findings, "LICENSE_ENCODING")
'''
        preceded = '''
def read_text(path, findings, code):
    Finding(code, "decode failed", path="sample")
def explode():
    raise RuntimeError("stop")
def validate(root, findings):
    explode()
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
        self.assertNotEqual(
            parameterized_reachability.reachable_parameterized_contracts(
                direct,
                "sample.py",
            ),
            parameterized_reachability.reachable_parameterized_contracts(
                preceded,
                "sample.py",
            ),
        )

    def test_statically_safe_prior_statement_does_not_add_contract_noise(self) -> None:
        direct = '''
from standards_tools import Finding

def run(findings):
    findings.append(Finding("PUBLIC_CODE", "message"))
'''
        preceded = '''
from standards_tools import Finding

def run(findings):
    0
    findings.append(Finding("PUBLIC_CODE", "message"))
'''
        self.assertEqual(
            literal_base.finding_semantic_signatures(direct),
            literal_base.finding_semantic_signatures(preceded),
        )


if __name__ == "__main__":
    unittest.main()
