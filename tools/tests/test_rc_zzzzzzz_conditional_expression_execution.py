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
import test_rc_zzzzzz_short_circuit_execution as short_circuit_execution  # noqa: F401


# Conditional expressions (`body if test else orelse`) share the same execution
# concern as boolean short-circuiting: the test always runs, but exactly one arm
# runs. Build on the already-composed short-circuit/lexical/sink execution
# layers rather than introducing a separate scanner.


def _literal_visit_ifexp(self, node: ast.IfExp) -> None:
    self.visit(node.test)
    truth = short_circuit_execution._semantic_truth(
        node.test,
        self.local_bindings,
        self.module_definitions,
    )
    if truth is True:
        self.visit(node.body)
        return
    if truth is False:
        self.visit(node.orelse)
        return

    self.context.append("ifexp:true")
    self.context_nodes.append(node.test)
    try:
        self.visit(node.body)
    finally:
        self.context_nodes.pop()
        self.context.pop()

    self.context.append("ifexp:false")
    self.context_nodes.append(node.test)
    try:
        self.visit(node.orelse)
    finally:
        self.context_nodes.pop()
        self.context.pop()


literal_base.FindingSignatureVisitor.visit_IfExp = _literal_visit_ifexp


def _patch_reachability_ifexp(visitor_type) -> None:
    def visit_ifexp(self, node: ast.IfExp) -> None:
        self.visit(node.test)
        truth = reachability_semantics.static_truth(node.test, self.constants)
        if truth is True:
            self.visit(node.body)
        elif truth is False:
            self.visit(node.orelse)
        else:
            self.visit(node.body)
            self.visit(node.orelse)

    visitor_type.visit_IfExp = visit_ifexp


_patch_reachability_ifexp(basic_reachability.ReachableFindingVisitor)
_patch_reachability_ifexp(extended_reachability.ExtendedReachableFindingVisitor)


_parameterized_visitor = parameterized_active.BranchAwareParameterizedCallSiteVisitor


def _parameterized_visit_ifexp(self, node: ast.IfExp) -> None:
    self.visit(node.test)
    truth = short_circuit_execution._semantic_truth(
        node.test,
        self.local_bindings,
        self.module_values,
    )
    if truth is True:
        self.visit(node.body)
        return
    if truth is False:
        self.visit(node.orelse)
        return

    self.context_nodes.append(("ifexp:true", node.test))
    try:
        self.visit(node.body)
    finally:
        self.context_nodes.pop()

    self.context_nodes.append(("ifexp:false", node.test))
    try:
        self.visit(node.orelse)
    finally:
        self.context_nodes.pop()


_parameterized_visitor.visit_IfExp = _parameterized_visit_ifexp
parameterized_active.base.ParameterizedCallSiteVisitor = _parameterized_visitor


def _reachable_parameterized_visit_ifexp(self, node: ast.IfExp) -> None:
    self.visit(node.test)
    truth = reachability_semantics.static_truth(node.test, self.constants)
    if truth is True:
        self.visit(node.body)
    elif truth is False:
        self.visit(node.orelse)
    else:
        self._with_context("ifexp:true", node.test, [ast.Expr(value=node.body)])
        self._with_context("ifexp:false", node.test, [ast.Expr(value=node.orelse)])


parameterized_reachability.ReachableParameterizedCallSiteVisitor.visit_IfExp = (
    _reachable_parameterized_visit_ifexp
)


class ReleaseCandidateConditionalExpressionExecutionTests(unittest.TestCase):
    def test_static_ifexp_hides_literal_finding_in_unselected_arm(self):
        sources = {
            "false-body": """
def validate(findings):
    findings.append(Finding("PUBLIC_CODE", "hidden")) if False else None
""",
            "true-else": """
def validate(findings):
    None if True else findings.append(Finding("PUBLIC_CODE", "hidden"))
""",
        }

        for name, source in sources.items():
            with self.subTest(name=name):
                self.assertNotIn(
                    "PUBLIC_CODE",
                    literal_base.finding_semantic_signatures(source),
                )
                self.assertEqual(
                    extended_reachability.reachable_contracts(source, "sample.py"),
                    Counter(),
                )

    def test_static_selected_ifexp_arm_preserves_literal_execution(self):
        direct = """
def validate(findings):
    findings.append(Finding("PUBLIC_CODE", "visible"))
"""
        true_body = """
def validate(findings):
    findings.append(Finding("PUBLIC_CODE", "visible")) if True else None
"""
        false_else = """
def validate(findings):
    None if False else findings.append(Finding("PUBLIC_CODE", "visible"))
"""

        expected_semantics = literal_base.finding_semantic_signatures(direct)
        expected_reachability = extended_reachability.reachable_contracts(
            direct, "sample.py"
        )
        for source in (true_body, false_else):
            self.assertEqual(
                expected_semantics,
                literal_base.finding_semantic_signatures(source),
            )
            self.assertEqual(
                expected_reachability,
                extended_reachability.reachable_contracts(source, "sample.py"),
            )

    def test_unknown_ifexp_adds_literal_branch_identity(self):
        direct = """
def validate(flag, findings):
    findings.append(Finding("PUBLIC_CODE", "visible"))
"""
        conditional = """
def validate(flag, findings):
    findings.append(Finding("PUBLIC_CODE", "conditional")) if flag else None
"""
        expected = literal_base.finding_semantic_signatures(direct)
        actual = literal_base.finding_semantic_signatures(conditional)
        self.assertNotEqual(expected, actual)
        payload = json.loads(actual["PUBLIC_CODE"][0])
        self.assertIn("ifexp:true", payload["context"])

    def test_static_ifexp_hides_parameterized_call_in_unselected_arm(self):
        template = """
def read_text(path, findings, code):
    Finding(code, "decode failed", path="sample")
def validate(root, findings):
    {expression}
"""
        expressions = {
            "false-body": (
                'read_text(root / "LICENSE", findings, "LICENSE_ENCODING") '
                "if False else None"
            ),
            "true-else": (
                'None if True else read_text(root / "LICENSE", findings, '
                '"LICENSE_ENCODING")'
            ),
        }

        for name, expression in expressions.items():
            source = template.format(expression=expression)
            with self.subTest(name=name):
                self.assertEqual(
                    parameterized_active.parameterized_finding_contracts(
                        source, "sample.py"
                    ),
                    set(),
                )
                self.assertEqual(
                    parameterized_reachability.reachable_parameterized_contracts(
                        source, "sample.py"
                    ),
                    set(),
                )

    def test_static_selected_ifexp_arm_preserves_parameterized_call(self):
        direct = """
def read_text(path, findings, code):
    Finding(code, "decode failed", path="sample")
def validate(root, findings):
    read_text(root / "LICENSE", findings, "LICENSE_ENCODING")
"""
        true_body = """
def read_text(path, findings, code):
    Finding(code, "decode failed", path="sample")
def validate(root, findings):
    read_text(root / "LICENSE", findings, "LICENSE_ENCODING") if True else None
"""
        false_else = """
def read_text(path, findings, code):
    Finding(code, "decode failed", path="sample")
def validate(root, findings):
    None if False else read_text(root / "LICENSE", findings, "LICENSE_ENCODING")
"""
        expected_semantics = parameterized_active.parameterized_finding_contracts(
            direct, "sample.py"
        )
        expected_reachability = (
            parameterized_reachability.reachable_parameterized_contracts(
                direct, "sample.py"
            )
        )
        for source in (true_body, false_else):
            self.assertEqual(
                expected_semantics,
                parameterized_active.parameterized_finding_contracts(
                    source, "sample.py"
                ),
            )
            self.assertEqual(
                expected_reachability,
                parameterized_reachability.reachable_parameterized_contracts(
                    source, "sample.py"
                ),
            )

    def test_unknown_ifexp_adds_parameterized_branch_identity(self):
        direct = """
def read_text(path, findings, code):
    Finding(code, "decode failed", path="sample")
def validate(flag, root, findings):
    read_text(root / "LICENSE", findings, "LICENSE_ENCODING")
"""
        true_arm = """
def read_text(path, findings, code):
    Finding(code, "decode failed", path="sample")
def validate(flag, root, findings):
    read_text(root / "LICENSE", findings, "LICENSE_ENCODING") if flag else None
"""
        false_arm = """
def read_text(path, findings, code):
    Finding(code, "decode failed", path="sample")
def validate(flag, root, findings):
    None if flag else read_text(root / "LICENSE", findings, "LICENSE_ENCODING")
"""

        expected = parameterized_active.parameterized_finding_contracts(
            direct, "sample.py"
        )
        true_contracts = parameterized_active.parameterized_finding_contracts(
            true_arm, "sample.py"
        )
        false_contracts = parameterized_active.parameterized_finding_contracts(
            false_arm, "sample.py"
        )
        self.assertNotEqual(expected, true_contracts)
        self.assertNotEqual(expected, false_contracts)

        true_payload = json.loads(next(iter(true_contracts)))
        false_payload = json.loads(next(iter(false_contracts)))
        self.assertTrue(
            any(item["branch"] == "ifexp:true" for item in true_payload["context"])
        )
        self.assertTrue(
            any(item["branch"] == "ifexp:false" for item in false_payload["context"])
        )


if __name__ == "__main__":
    unittest.main()
