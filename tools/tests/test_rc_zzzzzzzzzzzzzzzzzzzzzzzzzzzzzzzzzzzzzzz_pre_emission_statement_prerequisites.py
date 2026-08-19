from __future__ import annotations

import ast
import unittest

import rc_finding_code_contracts_base as literal_base
import test_rc_zzz_finding_emission_sink as sink_execution
import test_rc_zzzzzzzzzzzzzzzzzzzzzzzzzzz_left_to_right_expression_execution as left_to_right
import test_rc_zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz_definition_defaults_and_bound_names as bound_names_layer
import test_rc_zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz_final_p1_and_ci_composition as final_composition  # noqa: F401


# A Finding can be unreachable because an earlier *statement* fails, not only
# because an earlier sibling in the same expression fails. Preserve those
# execution prerequisites in the literal semantic contract. The sink-aware
# visitor inherits this block traversal, so it receives the same prerequisite
# identity without duplicating the implementation.


def _statement_execution_expression(statement: ast.stmt) -> ast.AST | None:
    if isinstance(statement, ast.Expr):
        return statement.value
    if isinstance(statement, ast.Assign):
        return statement.value
    if isinstance(statement, ast.AnnAssign):
        return statement.value
    if isinstance(statement, ast.AugAssign):
        # Augmented assignment evaluates both the target and value and may invoke
        # dynamic operator behavior, so retain the whole statement as the
        # prerequisite node when execution cannot be proven safe.
        return statement
    return None


def _statement_execution_state(visitor, statement: ast.stmt) -> tuple[str, ast.AST | None]:
    expression = _statement_execution_expression(statement)
    if expression is None:
        return left_to_right._SAFE, None

    constants = left_to_right._literal_constants(visitor)
    if isinstance(expression, ast.stmt):
        # _visitor_execution_state operates on expressions. For AugAssign, model
        # its value and target as one synthetic left-to-right prerequisite.
        assert isinstance(statement, ast.AugAssign)
        synthetic = ast.Tuple(
            elts=[ast.copy_location(ast.Name(id="__aug_target__", ctx=ast.Load()), statement.target), statement.value],
            ctx=ast.Load(),
        )
        ast.fix_missing_locations(synthetic)
        return left_to_right._UNKNOWN, statement

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

        state, expression = _statement_execution_state(self, statement)
        if expression is None:
            continue
        if state in {left_to_right._UNKNOWN, left_to_right._RAISES}:
            prerequisites.append(expression)


literal_base.FindingSignatureVisitor._visit_block = _visit_block_with_statement_prerequisites


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
