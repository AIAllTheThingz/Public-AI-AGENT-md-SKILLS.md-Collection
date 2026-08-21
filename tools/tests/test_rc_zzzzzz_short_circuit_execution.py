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
import test_rc_zzzzz_lexical_function_execution as lexical_execution  # noqa: F401


_UNKNOWN = object()


def _static_scalar(
    node: ast.AST,
    local_bindings: dict[str, ast.AST],
    module_bindings: dict[str, ast.AST],
    seen: set[str] | None = None,
) -> object:
    """Resolve simple side-effect-free truth inputs used by semantic visitors."""

    if isinstance(node, ast.Constant):
        return node.value

    if isinstance(node, ast.Name):
        active = set() if seen is None else set(seen)
        if node.id in active:
            return _UNKNOWN
        binding = local_bindings.get(node.id)
        if binding is None:
            binding = module_bindings.get(node.id)
        if binding is None or isinstance(
            binding,
            (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda, ast.ClassDef),
        ):
            return _UNKNOWN
        active.add(node.id)
        return _static_scalar(binding, local_bindings, module_bindings, active)

    if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.Not):
        value = _semantic_truth(node.operand, local_bindings, module_bindings)
        return _UNKNOWN if value is None else not value

    if (
        isinstance(node, ast.Compare)
        and len(node.ops) == 1
        and len(node.comparators) == 1
    ):
        left = _static_scalar(node.left, local_bindings, module_bindings, seen)
        right = _static_scalar(
            node.comparators[0],
            local_bindings,
            module_bindings,
            seen,
        )
        if left is _UNKNOWN or right is _UNKNOWN:
            return _UNKNOWN
        operator = node.ops[0]
        if isinstance(operator, ast.Eq):
            return left == right
        if isinstance(operator, ast.NotEq):
            return left != right
        if isinstance(operator, ast.Is):
            return left is right
        if isinstance(operator, ast.IsNot):
            return left is not right

    return _UNKNOWN


def _semantic_truth(
    node: ast.AST,
    local_bindings: dict[str, ast.AST],
    module_bindings: dict[str, ast.AST],
) -> bool | None:
    """Evaluate only truth that is statically certain without running user code."""

    if isinstance(node, ast.BoolOp):
        if isinstance(node.op, ast.And):
            unknown = False
            for value in node.values:
                truth = _semantic_truth(value, local_bindings, module_bindings)
                if truth is False:
                    return False
                if truth is None:
                    unknown = True
            return None if unknown else True

        if isinstance(node.op, ast.Or):
            unknown = False
            for value in node.values:
                truth = _semantic_truth(value, local_bindings, module_bindings)
                if truth is True:
                    return True
                if truth is None:
                    unknown = True
            return None if unknown else False

    value = _static_scalar(node, local_bindings, module_bindings)
    return None if value is _UNKNOWN else bool(value)


def _short_circuits(node: ast.BoolOp, truth: bool | None) -> bool:
    if isinstance(node.op, ast.And):
        return truth is False
    if isinstance(node.op, ast.Or):
        return truth is True
    return False


def _boolop_marker(node: ast.BoolOp, index: int) -> str:
    if isinstance(node.op, ast.And):
        condition = "requires-prior-truthy"
        operator = "and"
    else:
        condition = "requires-prior-falsy"
        operator = "or"
    return f"boolop:{operator}:operand:{index}:{condition}"


def _boolop_condition_node(prefix: list[ast.AST]) -> ast.AST:
    if len(prefix) == 1:
        return prefix[0]
    return ast.Tuple(elts=list(prefix), ctx=ast.Load())


# ---------------------------------------------------------------------------
# Literal finding semantic signatures
# ---------------------------------------------------------------------------


def _literal_visit_boolop(self, node: ast.BoolOp) -> None:
    conditional_prefix: list[ast.AST] = []

    for index, value in enumerate(node.values):
        if conditional_prefix:
            marker = _boolop_marker(node, index)
            self.context.append(marker)
            self.context_nodes.append(_boolop_condition_node(conditional_prefix))
            try:
                self.visit(value)
            finally:
                self.context_nodes.pop()
                self.context.pop()
        else:
            self.visit(value)

        truth = _semantic_truth(
            value,
            self.local_bindings,
            self.module_definitions,
        )
        if _short_circuits(node, truth):
            break
        if truth is None:
            conditional_prefix.append(value)


literal_base.FindingSignatureVisitor.visit_BoolOp = _literal_visit_boolop


# ---------------------------------------------------------------------------
# Literal finding reachability, including sink-aware reachability subclasses
# ---------------------------------------------------------------------------


def _patch_reachability_boolops(visitor_type) -> None:
    def visit_boolop(self, node: ast.BoolOp) -> None:
        for value in node.values:
            self.visit(value)
            truth = reachability_semantics.static_truth(value, self.constants)
            if _short_circuits(node, truth):
                break

    visitor_type.visit_BoolOp = visit_boolop


_patch_reachability_boolops(basic_reachability.ReachableFindingVisitor)
_patch_reachability_boolops(extended_reachability.ExtendedReachableFindingVisitor)


# ---------------------------------------------------------------------------
# Caller-supplied / parameterized finding semantics
# ---------------------------------------------------------------------------

_parameterized_visitor = parameterized_active.BranchAwareParameterizedCallSiteVisitor


def _parameterized_visit_boolop(self, node: ast.BoolOp) -> None:
    conditional_prefix: list[ast.AST] = []

    for index, value in enumerate(node.values):
        if conditional_prefix:
            marker = _boolop_marker(node, index)
            condition = _boolop_condition_node(conditional_prefix)
            self.context_nodes.append((marker, condition))
            try:
                self.visit(value)
            finally:
                self.context_nodes.pop()
        else:
            self.visit(value)

        truth = _semantic_truth(
            value,
            self.local_bindings,
            self.module_values,
        )
        if _short_circuits(node, truth):
            break
        if truth is None:
            conditional_prefix.append(value)


_parameterized_visitor.visit_BoolOp = _parameterized_visit_boolop
parameterized_active.base.ParameterizedCallSiteVisitor = _parameterized_visitor


# ---------------------------------------------------------------------------
# Reachable caller-supplied finding call sites
# ---------------------------------------------------------------------------


def _reachable_parameterized_visit_boolop(self, node: ast.BoolOp) -> None:
    for value in node.values:
        self.visit(value)
        truth = reachability_semantics.static_truth(value, self.constants)
        if _short_circuits(node, truth):
            break


parameterized_reachability.ReachableParameterizedCallSiteVisitor.visit_BoolOp = (
    _reachable_parameterized_visit_boolop
)


class ReleaseCandidateShortCircuitExecutionTests(unittest.TestCase):
    def test_false_and_true_or_hide_literal_finding(self):
        sources = {
            "false-and": """
def validate(findings):
    False and findings.append(Finding("PUBLIC_CODE", "hidden"))
""",
            "true-or": """
def validate(findings):
    True or findings.append(Finding("PUBLIC_CODE", "hidden"))
""",
        }

        for name, source in sources.items():
            with self.subTest(name=name):
                self.assertNotIn(
                    "PUBLIC_CODE",
                    literal_base.finding_semantic_signatures(source),
                )
                self.assertEqual(
                    extended_reachability.reachable_contracts(
                        source,
                        "sample.py",
                    ),
                    Counter(),
                )

    def test_pass_through_boolops_preserve_literal_execution(self):
        direct = """
def validate(findings):
    findings.append(Finding("PUBLIC_CODE", "visible"))
"""
        true_and = """
def validate(findings):
    True and findings.append(Finding("PUBLIC_CODE", "visible"))
"""
        false_or = """
def validate(findings):
    False or findings.append(Finding("PUBLIC_CODE", "visible"))
"""

        expected = literal_base.finding_semantic_signatures(direct)
        self.assertEqual(
            expected,
            literal_base.finding_semantic_signatures(true_and),
        )
        self.assertEqual(
            expected,
            literal_base.finding_semantic_signatures(false_or),
        )

    def test_unknown_boolop_operand_adds_literal_condition(self):
        direct = """
def validate(flag, findings):
    findings.append(Finding("PUBLIC_CODE", "visible"))
"""
        conditional = """
def validate(flag, findings):
    flag and findings.append(Finding("PUBLIC_CODE", "conditional"))
"""

        expected = literal_base.finding_semantic_signatures(direct)
        actual = literal_base.finding_semantic_signatures(conditional)
        self.assertNotEqual(expected, actual)

        payload = json.loads(actual["PUBLIC_CODE"][0])
        self.assertTrue(
            any(
                marker.startswith("boolop:and:")
                for marker in payload["context"]
            ),
            payload,
        )

    def test_false_and_true_or_hide_parameterized_finding_call(self):
        template = """
def read_text(path, findings, code):
    Finding(code, "decode failed", path="sample")
def validate(root, findings):
    {expression}
"""
        expressions = {
            "false-and": 'False and read_text(root / "LICENSE", findings, "LICENSE_ENCODING")',
            "true-or": 'True or read_text(root / "LICENSE", findings, "LICENSE_ENCODING")',
        }

        for name, expression in expressions.items():
            source = template.format(expression=expression)
            with self.subTest(name=name):
                self.assertEqual(
                    parameterized_active.parameterized_finding_contracts(
                        source,
                        "sample.py",
                    ),
                    set(),
                )
                self.assertEqual(
                    parameterized_reachability.reachable_parameterized_contracts(
                        source,
                        "sample.py",
                    ),
                    set(),
                )

    def test_unknown_boolop_operand_adds_parameterized_condition(self):
        direct = """
def read_text(path, findings, code):
    Finding(code, "decode failed", path="sample")
def validate(flag, root, findings):
    read_text(root / "LICENSE", findings, "LICENSE_ENCODING")
"""
        conditional = """
def read_text(path, findings, code):
    Finding(code, "decode failed", path="sample")
def validate(flag, root, findings):
    flag and read_text(root / "LICENSE", findings, "LICENSE_ENCODING")
"""

        expected = parameterized_active.parameterized_finding_contracts(
            direct,
            "sample.py",
        )
        actual = parameterized_active.parameterized_finding_contracts(
            conditional,
            "sample.py",
        )
        self.assertNotEqual(expected, actual)

        payload = json.loads(next(iter(actual)))
        self.assertTrue(
            any(
                item["branch"].startswith("boolop:and:")
                for item in payload["context"]
            ),
            payload,
        )


if __name__ == "__main__":
    unittest.main()
