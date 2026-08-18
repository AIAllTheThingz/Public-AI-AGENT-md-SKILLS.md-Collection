from __future__ import annotations

import ast
import copy
import json
import unittest
from collections import Counter
from typing import Any

import rc_finding_code_contracts_base as literal_base
import rc_parameterized_finding_codes_base as parameterized_base
import rc_reachability_semantics as reachability_semantics
import test_rc_extended_finding_reachability as extended_reachability
import test_rc_finding_reachability as basic_reachability
import test_rc_parameterized_finding_codes as parameterized_active
import test_rc_parameterized_finding_reachability as parameterized_reachability
import test_rc_zzzzzz_short_circuit_execution as short_circuit_execution
import test_rc_zzzzzzzzz_comprehension_execution as comprehension_execution  # noqa: F401


# Python chained comparisons evaluate operands left-to-right and stop as soon as
# one comparison is false. Generic AST traversal incorrectly visits every later
# comparator, which can keep dead Finding(...) and caller-supplied finding calls
# in the permanent compatibility inventory.

_VALUE_UNKNOWN = object()

_previous_semantic_static_scalar = short_circuit_execution._static_scalar
_previous_semantic_truth = short_circuit_execution._semantic_truth
_previous_reachability_static_value = reachability_semantics.static_value
_previous_reachability_truth = reachability_semantics.static_truth
_previous_basic_static_value = basic_reachability.static_value


def _semantic_literal_value(
    node: ast.AST,
    local_bindings: dict[str, ast.AST],
    module_bindings: dict[str, ast.AST],
    seen: set[str] | None = None,
) -> object:
    if isinstance(node, ast.Constant):
        return node.value

    if isinstance(node, ast.Name):
        active = set() if seen is None else set(seen)
        if node.id in active:
            return _VALUE_UNKNOWN
        binding = local_bindings.get(node.id)
        if binding is None:
            binding = module_bindings.get(node.id)
        if binding is None or isinstance(
            binding,
            (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda, ast.ClassDef),
        ):
            return _VALUE_UNKNOWN
        active.add(node.id)
        return _semantic_literal_value(
            binding,
            local_bindings,
            module_bindings,
            active,
        )

    if isinstance(node, ast.Tuple):
        values = [
            _semantic_literal_value(item, local_bindings, module_bindings, seen)
            for item in node.elts
        ]
        if any(value is _VALUE_UNKNOWN for value in values):
            return _VALUE_UNKNOWN
        return tuple(values)

    if isinstance(node, ast.List):
        values = [
            _semantic_literal_value(item, local_bindings, module_bindings, seen)
            for item in node.elts
        ]
        if any(value is _VALUE_UNKNOWN for value in values):
            return _VALUE_UNKNOWN
        return values

    if isinstance(node, ast.Set):
        values = [
            _semantic_literal_value(item, local_bindings, module_bindings, seen)
            for item in node.elts
        ]
        if any(value is _VALUE_UNKNOWN for value in values):
            return _VALUE_UNKNOWN
        try:
            return set(values)
        except TypeError:
            return _VALUE_UNKNOWN

    if isinstance(node, ast.Dict) and all(key is not None for key in node.keys):
        keys = [
            _semantic_literal_value(key, local_bindings, module_bindings, seen)
            for key in node.keys
        ]
        values = [
            _semantic_literal_value(value, local_bindings, module_bindings, seen)
            for value in node.values
        ]
        if any(value is _VALUE_UNKNOWN for value in [*keys, *values]):
            return _VALUE_UNKNOWN
        try:
            return dict(zip(keys, values))
        except (TypeError, ValueError):
            return _VALUE_UNKNOWN

    if isinstance(node, ast.UnaryOp):
        operand = _semantic_literal_value(
            node.operand,
            local_bindings,
            module_bindings,
            seen,
        )
        if operand is _VALUE_UNKNOWN:
            return _VALUE_UNKNOWN
        try:
            if isinstance(node.op, ast.Not):
                return not bool(operand)
            if isinstance(node.op, ast.UAdd):
                return +operand
            if isinstance(node.op, ast.USub):
                return -operand
            if isinstance(node.op, ast.Invert):
                return ~operand
        except (TypeError, ValueError, OverflowError):
            return _VALUE_UNKNOWN

    if (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "range"
        and not node.keywords
        and 1 <= len(node.args) <= 3
    ):
        values = [
            _semantic_literal_value(
                argument,
                local_bindings,
                module_bindings,
                seen,
            )
            for argument in node.args
        ]
        if any(
            value is _VALUE_UNKNOWN
            or not isinstance(value, int)
            or isinstance(value, bool)
            for value in values
        ):
            return _VALUE_UNKNOWN
        try:
            return range(*values)
        except (TypeError, ValueError):
            return _VALUE_UNKNOWN

    if isinstance(node, ast.Compare):
        truth = _semantic_compare_chain_truth(
            node,
            local_bindings,
            module_bindings,
        )
        return _VALUE_UNKNOWN if truth is None else truth

    previous = _previous_semantic_static_scalar(
        node,
        local_bindings,
        module_bindings,
        seen,
    )
    if previous is not short_circuit_execution._UNKNOWN:
        return previous
    return _VALUE_UNKNOWN


def _reachability_literal_value(
    node: ast.AST,
    constants: dict[str, Any],
) -> object:
    if isinstance(node, ast.Constant):
        return node.value

    if isinstance(node, ast.Name):
        value = constants.get(node.id, _VALUE_UNKNOWN)
        if value is reachability_semantics.UNKNOWN or value is basic_reachability.UNKNOWN:
            return _VALUE_UNKNOWN
        return value

    if isinstance(node, ast.Tuple):
        values = [_reachability_literal_value(item, constants) for item in node.elts]
        if any(value is _VALUE_UNKNOWN for value in values):
            return _VALUE_UNKNOWN
        return tuple(values)

    if isinstance(node, ast.List):
        values = [_reachability_literal_value(item, constants) for item in node.elts]
        if any(value is _VALUE_UNKNOWN for value in values):
            return _VALUE_UNKNOWN
        return values

    if isinstance(node, ast.Set):
        values = [_reachability_literal_value(item, constants) for item in node.elts]
        if any(value is _VALUE_UNKNOWN for value in values):
            return _VALUE_UNKNOWN
        try:
            return set(values)
        except TypeError:
            return _VALUE_UNKNOWN

    if isinstance(node, ast.Dict) and all(key is not None for key in node.keys):
        keys = [_reachability_literal_value(key, constants) for key in node.keys]
        values = [_reachability_literal_value(value, constants) for value in node.values]
        if any(value is _VALUE_UNKNOWN for value in [*keys, *values]):
            return _VALUE_UNKNOWN
        try:
            return dict(zip(keys, values))
        except (TypeError, ValueError):
            return _VALUE_UNKNOWN

    if isinstance(node, ast.UnaryOp):
        operand = _reachability_literal_value(node.operand, constants)
        if operand is _VALUE_UNKNOWN:
            return _VALUE_UNKNOWN
        try:
            if isinstance(node.op, ast.Not):
                return not bool(operand)
            if isinstance(node.op, ast.UAdd):
                return +operand
            if isinstance(node.op, ast.USub):
                return -operand
            if isinstance(node.op, ast.Invert):
                return ~operand
        except (TypeError, ValueError, OverflowError):
            return _VALUE_UNKNOWN

    if (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "range"
        and not node.keywords
        and 1 <= len(node.args) <= 3
    ):
        values = [_reachability_literal_value(argument, constants) for argument in node.args]
        if any(
            value is _VALUE_UNKNOWN
            or not isinstance(value, int)
            or isinstance(value, bool)
            for value in values
        ):
            return _VALUE_UNKNOWN
        try:
            return range(*values)
        except (TypeError, ValueError):
            return _VALUE_UNKNOWN

    if isinstance(node, ast.Compare):
        truth = _reachability_compare_chain_truth(node, constants)
        return _VALUE_UNKNOWN if truth is None else truth

    previous = _previous_reachability_static_value(node, constants)
    if previous is not reachability_semantics.UNKNOWN:
        return previous
    return _VALUE_UNKNOWN


def _safe_compare_values(
    left: object,
    operator: ast.cmpop,
    right: object,
) -> bool | None:
    try:
        if isinstance(operator, ast.Eq):
            return left == right
        if isinstance(operator, ast.NotEq):
            return left != right
        if isinstance(operator, ast.Lt):
            return left < right
        if isinstance(operator, ast.LtE):
            return left <= right
        if isinstance(operator, ast.Gt):
            return left > right
        if isinstance(operator, ast.GtE):
            return left >= right
        if isinstance(operator, ast.In):
            return left in right
        if isinstance(operator, ast.NotIn):
            return left not in right
    except (TypeError, ValueError, AttributeError):
        return None
    return None


def _single_compare(
    left: ast.AST,
    operator: ast.cmpop,
    right: ast.AST,
) -> ast.Compare:
    return ast.Compare(
        left=copy.deepcopy(left),
        ops=[copy.deepcopy(operator)],
        comparators=[copy.deepcopy(right)],
    )


def _semantic_pair_truth(
    left: ast.AST,
    operator: ast.cmpop,
    right: ast.AST,
    local_bindings: dict[str, ast.AST],
    module_bindings: dict[str, ast.AST],
) -> bool | None:
    pair = _single_compare(left, operator, right)
    previous = _previous_semantic_static_scalar(
        pair,
        local_bindings,
        module_bindings,
    )
    if previous is not short_circuit_execution._UNKNOWN:
        return bool(previous)

    left_value = _semantic_literal_value(left, local_bindings, module_bindings)
    right_value = _semantic_literal_value(right, local_bindings, module_bindings)
    if left_value is _VALUE_UNKNOWN or right_value is _VALUE_UNKNOWN:
        return None
    return _safe_compare_values(left_value, operator, right_value)


def _reachability_pair_truth(
    left: ast.AST,
    operator: ast.cmpop,
    right: ast.AST,
    constants: dict[str, Any],
) -> bool | None:
    pair = _single_compare(left, operator, right)
    previous = _previous_reachability_static_value(pair, constants)
    if previous is not reachability_semantics.UNKNOWN:
        return bool(previous)

    left_value = _reachability_literal_value(left, constants)
    right_value = _reachability_literal_value(right, constants)
    if left_value is _VALUE_UNKNOWN or right_value is _VALUE_UNKNOWN:
        return None
    return _safe_compare_values(left_value, operator, right_value)


def _semantic_compare_chain_truth(
    node: ast.Compare,
    local_bindings: dict[str, ast.AST],
    module_bindings: dict[str, ast.AST],
) -> bool | None:
    previous_operand = node.left
    unknown = False
    for operator, comparator in zip(node.ops, node.comparators):
        truth = _semantic_pair_truth(
            previous_operand,
            operator,
            comparator,
            local_bindings,
            module_bindings,
        )
        if truth is False:
            return False
        if truth is None:
            unknown = True
        previous_operand = comparator
    return None if unknown else True


def _reachability_compare_chain_truth(
    node: ast.Compare,
    constants: dict[str, Any],
) -> bool | None:
    previous_operand = node.left
    unknown = False
    for operator, comparator in zip(node.ops, node.comparators):
        truth = _reachability_pair_truth(
            previous_operand,
            operator,
            comparator,
            constants,
        )
        if truth is False:
            return False
        if truth is None:
            unknown = True
        previous_operand = comparator
    return None if unknown else True


def _semantic_static_scalar_with_chained_compare(
    node: ast.AST,
    local_bindings: dict[str, ast.AST],
    module_bindings: dict[str, ast.AST],
    seen: set[str] | None = None,
) -> object:
    if isinstance(node, ast.Compare):
        truth = _semantic_compare_chain_truth(node, local_bindings, module_bindings)
        return short_circuit_execution._UNKNOWN if truth is None else truth
    return _previous_semantic_static_scalar(
        node,
        local_bindings,
        module_bindings,
        seen,
    )


def _semantic_truth_with_chained_compare(
    node: ast.AST,
    local_bindings: dict[str, ast.AST],
    module_bindings: dict[str, ast.AST],
) -> bool | None:
    if isinstance(node, ast.Compare):
        return _semantic_compare_chain_truth(node, local_bindings, module_bindings)

    if isinstance(node, ast.BoolOp):
        unknown = False
        if isinstance(node.op, ast.And):
            for value in node.values:
                truth = _semantic_truth_with_chained_compare(
                    value,
                    local_bindings,
                    module_bindings,
                )
                if truth is False:
                    return False
                if truth is None:
                    unknown = True
            return None if unknown else True

        if isinstance(node.op, ast.Or):
            for value in node.values:
                truth = _semantic_truth_with_chained_compare(
                    value,
                    local_bindings,
                    module_bindings,
                )
                if truth is True:
                    return True
                if truth is None:
                    unknown = True
            return None if unknown else False

    if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.Not):
        truth = _semantic_truth_with_chained_compare(
            node.operand,
            local_bindings,
            module_bindings,
        )
        return None if truth is None else not truth

    return _previous_semantic_truth(node, local_bindings, module_bindings)


def _reachability_static_value_with_chained_compare(
    node: ast.AST,
    constants: dict[str, Any],
) -> object:
    if isinstance(node, ast.Compare):
        truth = _reachability_compare_chain_truth(node, constants)
        return reachability_semantics.UNKNOWN if truth is None else truth
    return _previous_reachability_static_value(node, constants)


def _basic_static_value_with_chained_compare(
    node: ast.AST,
    constants: dict[str, Any],
) -> object:
    if isinstance(node, ast.Compare):
        truth = _reachability_compare_chain_truth(node, constants)
        return basic_reachability.UNKNOWN if truth is None else truth
    return _previous_basic_static_value(node, constants)


def _reachability_truth_with_chained_compare(
    node: ast.AST,
    constants: dict[str, Any],
) -> bool | None:
    if isinstance(node, ast.Compare):
        return _reachability_compare_chain_truth(node, constants)

    if isinstance(node, ast.BoolOp):
        unknown = False
        if isinstance(node.op, ast.And):
            for value in node.values:
                truth = _reachability_truth_with_chained_compare(value, constants)
                if truth is False:
                    return False
                if truth is None:
                    unknown = True
            return None if unknown else True

        if isinstance(node.op, ast.Or):
            for value in node.values:
                truth = _reachability_truth_with_chained_compare(value, constants)
                if truth is True:
                    return True
                if truth is None:
                    unknown = True
            return None if unknown else False

    if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.Not):
        truth = _reachability_truth_with_chained_compare(node.operand, constants)
        return None if truth is None else not truth

    return _previous_reachability_truth(node, constants)


# Make the stronger truth/value evaluator visible to all later-composed expression
# visitors and to control-flow visitors that imported the shared functions by name.
short_circuit_execution._static_scalar = _semantic_static_scalar_with_chained_compare
short_circuit_execution._semantic_truth = _semantic_truth_with_chained_compare
reachability_semantics.static_value = _reachability_static_value_with_chained_compare
reachability_semantics.static_truth = _reachability_truth_with_chained_compare
basic_reachability.static_value = _basic_static_value_with_chained_compare
basic_reachability.static_truth = _reachability_truth_with_chained_compare
extended_reachability.static_truth = _reachability_truth_with_chained_compare
parameterized_reachability.static_truth = _reachability_truth_with_chained_compare


def _comparison_condition_node(pairs: list[ast.Compare]) -> ast.AST:
    if len(pairs) == 1:
        return copy.deepcopy(pairs[0])
    return ast.BoolOp(
        op=ast.And(),
        values=[copy.deepcopy(pair) for pair in pairs],
    )


def _compare_marker(index: int) -> str:
    return f"compare:comparator:{index}:requires-prior-comparisons-true"


def _literal_visit_compare(self, node: ast.Compare) -> None:
    self.visit(node.left)
    previous_operand = node.left
    conditional_pairs: list[ast.Compare] = []

    for index, (operator, comparator) in enumerate(zip(node.ops, node.comparators)):
        if conditional_pairs:
            self.context.append(_compare_marker(index))
            self.context_nodes.append(_comparison_condition_node(conditional_pairs))
            try:
                self.visit(comparator)
            finally:
                self.context_nodes.pop()
                self.context.pop()
        else:
            self.visit(comparator)

        truth = _semantic_pair_truth(
            previous_operand,
            operator,
            comparator,
            self.local_bindings,
            self.module_definitions,
        )
        if truth is False:
            break
        if truth is None:
            conditional_pairs.append(
                _single_compare(previous_operand, operator, comparator)
            )
        previous_operand = comparator


literal_base.FindingSignatureVisitor.visit_Compare = _literal_visit_compare


def _patch_reachability_compare(visitor_type) -> None:
    def visit_compare(self, node: ast.Compare) -> None:
        self.visit(node.left)
        previous_operand = node.left
        for operator, comparator in zip(node.ops, node.comparators):
            self.visit(comparator)
            truth = _reachability_pair_truth(
                previous_operand,
                operator,
                comparator,
                self.constants,
            )
            if truth is False:
                break
            previous_operand = comparator

    visitor_type.visit_Compare = visit_compare


_patch_reachability_compare(basic_reachability.ReachableFindingVisitor)
_patch_reachability_compare(extended_reachability.ExtendedReachableFindingVisitor)


_parameterized_visitor = parameterized_active.BranchAwareParameterizedCallSiteVisitor


def _parameterized_visit_compare(self, node: ast.Compare) -> None:
    self.visit(node.left)
    previous_operand = node.left
    conditional_pairs: list[ast.Compare] = []

    for index, (operator, comparator) in enumerate(zip(node.ops, node.comparators)):
        if conditional_pairs:
            self.context_nodes.append(
                (
                    _compare_marker(index),
                    _comparison_condition_node(conditional_pairs),
                )
            )
            try:
                self.visit(comparator)
            finally:
                self.context_nodes.pop()
        else:
            self.visit(comparator)

        truth = _semantic_pair_truth(
            previous_operand,
            operator,
            comparator,
            self.local_bindings,
            self.module_values,
        )
        if truth is False:
            break
        if truth is None:
            conditional_pairs.append(
                _single_compare(previous_operand, operator, comparator)
            )
        previous_operand = comparator


_parameterized_visitor.visit_Compare = _parameterized_visit_compare
parameterized_active.base.ParameterizedCallSiteVisitor = _parameterized_visitor


def _reachable_parameterized_visit_compare(self, node: ast.Compare) -> None:
    self.visit(node.left)
    previous_operand = node.left
    for operator, comparator in zip(node.ops, node.comparators):
        self.visit(comparator)
        truth = _reachability_pair_truth(
            previous_operand,
            operator,
            comparator,
            self.constants,
        )
        if truth is False:
            break
        previous_operand = comparator


parameterized_reachability.ReachableParameterizedCallSiteVisitor.visit_Compare = (
    _reachable_parameterized_visit_compare
)


# Parameterized helper discovery already has execution-aware lambda/generator/
# comprehension pruning. Feed that composed implementation an AST with only the
# definitely unreachable tail of chained comparisons removed.
_previous_parameterized_finding_parameters = (
    parameterized_active.parameterized_finding_parameters
)


class _PruneDeadChainedComparisons(ast.NodeTransformer):
    def __init__(self, module_bindings: dict[str, ast.AST]) -> None:
        self.module_bindings = module_bindings

    def visit_Compare(self, node: ast.Compare) -> ast.AST:
        node.left = self.visit(node.left)
        previous_operand = node.left
        operators: list[ast.cmpop] = []
        comparators: list[ast.AST] = []

        for operator, comparator in zip(node.ops, node.comparators):
            transformed = self.visit(comparator)
            operators.append(operator)
            comparators.append(transformed)

            truth = _semantic_pair_truth(
                previous_operand,
                operator,
                transformed,
                {},
                self.module_bindings,
            )
            previous_operand = transformed
            if truth is False:
                break

        node.ops = operators
        node.comparators = comparators
        return node


def _comparison_aware_parameterized_finding_parameters(
    tree: ast.Module,
) -> dict[str, set[str]]:
    transformed = copy.deepcopy(tree)
    module_bindings = parameterized_active.module_bindings(transformed)
    transformed = _PruneDeadChainedComparisons(module_bindings).visit(transformed)
    ast.fix_missing_locations(transformed)
    return _previous_parameterized_finding_parameters(transformed)


parameterized_base.parameterized_finding_parameters = (
    _comparison_aware_parameterized_finding_parameters
)
parameterized_active.base.parameterized_finding_parameters = (
    _comparison_aware_parameterized_finding_parameters
)
parameterized_active.parameterized_finding_parameters = (
    _comparison_aware_parameterized_finding_parameters
)


class ReleaseCandidateChainedComparisonExecutionTests(unittest.TestCase):
    def test_false_first_comparison_hides_literal_finding_in_later_operand(self):
        source = '''
def validate(findings):
    1 > 2 > findings.append(Finding("PUBLIC_CODE", "hidden"))
'''
        self.assertNotIn(
            "PUBLIC_CODE",
            literal_base.finding_semantic_signatures(source),
        )
        self.assertEqual(
            extended_reachability.reachable_contracts(source, "sample.py"),
            Counter(),
        )

    def test_true_first_comparison_preserves_later_literal_execution(self):
        direct = '''
def validate(findings):
    findings.append(Finding("PUBLIC_CODE", "visible"))
'''
        chained = '''
def validate(findings):
    1 < 2 < findings.append(Finding("PUBLIC_CODE", "visible"))
'''
        self.assertEqual(
            literal_base.finding_semantic_signatures(direct),
            literal_base.finding_semantic_signatures(chained),
        )
        self.assertEqual(
            extended_reachability.reachable_contracts(direct, "sample.py"),
            extended_reachability.reachable_contracts(chained, "sample.py"),
        )

    def test_unknown_prior_comparison_adds_literal_execution_identity(self):
        direct = '''
def validate(value, findings):
    findings.append(Finding("PUBLIC_CODE", "visible"))
'''
        chained = '''
def validate(value, findings):
    value > 0 > findings.append(Finding("PUBLIC_CODE", "conditional"))
'''
        expected = literal_base.finding_semantic_signatures(direct)
        actual = literal_base.finding_semantic_signatures(chained)
        self.assertNotEqual(expected, actual)
        payload = json.loads(actual["PUBLIC_CODE"][0])
        self.assertTrue(
            any(
                item.startswith("compare:comparator:1:")
                for item in payload["context"]
            )
        )

    def test_false_first_comparison_hides_parameterized_call(self):
        source = '''
def read_text(path, findings, code):
    Finding(code, "decode failed", path="sample")
def validate(root, findings):
    1 > 2 > read_text(root / "LICENSE", findings, "LICENSE_ENCODING")
'''
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

    def test_unknown_prior_comparison_adds_parameterized_execution_identity(self):
        direct = '''
def read_text(path, findings, code):
    Finding(code, "decode failed", path="sample")
def validate(value, root, findings):
    read_text(root / "LICENSE", findings, "LICENSE_ENCODING")
'''
        chained = '''
def read_text(path, findings, code):
    Finding(code, "decode failed", path="sample")
def validate(value, root, findings):
    value > 0 > read_text(root / "LICENSE", findings, "LICENSE_ENCODING")
'''
        expected = parameterized_active.parameterized_finding_contracts(
            direct,
            "sample.py",
        )
        actual = parameterized_active.parameterized_finding_contracts(
            chained,
            "sample.py",
        )
        self.assertNotEqual(expected, actual)
        payload = json.loads(next(iter(actual)))
        self.assertTrue(
            any(
                item["branch"].startswith("compare:comparator:1:")
                for item in payload["context"]
            )
        )

    def test_dead_chained_comparison_does_not_publish_parameterized_helper(self):
        source = '''
def emit(findings, code):
    1 > 2 > Finding(code, "hidden", path="sample")
def validate(findings):
    emit(findings, "PUBLIC_CODE")
'''
        self.assertEqual(
            parameterized_active.parameterized_finding_contracts(
                source,
                "sample.py",
            ),
            set(),
        )

    def test_membership_and_ordering_short_circuit_are_statically_recognized(self):
        sources = (
            '''
def validate(findings):
    3 in (1, 2) < findings.append(Finding("PUBLIC_CODE", "hidden"))
''',
            '''
def validate(findings):
    4 <= 3 < findings.append(Finding("PUBLIC_CODE", "hidden"))
''',
        )
        for source in sources:
            with self.subTest(source=source):
                self.assertNotIn(
                    "PUBLIC_CODE",
                    literal_base.finding_semantic_signatures(source),
                )


if __name__ == "__main__":
    unittest.main()
