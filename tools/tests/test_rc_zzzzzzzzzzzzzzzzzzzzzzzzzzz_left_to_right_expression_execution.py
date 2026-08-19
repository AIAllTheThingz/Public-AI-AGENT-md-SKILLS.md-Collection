from __future__ import annotations

import ast
import copy
import json
import unittest
from collections import Counter
from typing import Any, Callable

import rc_finding_code_contracts_base as literal_base
import test_rc_extended_finding_reachability as extended_reachability
import test_rc_finding_reachability as basic_reachability
import test_rc_parameterized_finding_codes as parameterized_active
import test_rc_parameterized_finding_reachability as parameterized_reachability
import test_rc_zzz_finding_emission_sink as sink_execution
import test_rc_zzzz_sink_rebinding_and_parameterized_multiplicity as parameterized_multiplicity
import test_rc_zzzzzzzzzzzz_execution_prerequisites as prerequisite_execution
import test_rc_zzzzzzzzzzzzzzzzzzzzzzzzzz_assigned_callable_sink_destructors as _latest_composition  # noqa: F401


# Python evaluates ordinary eager expression siblings from left to right. A
# Finding in a later tuple/list/set/dict element, binary operand, subscript
# slice, or call argument is never reached when an earlier prerequisite raises.
# Preserve that execution boundary in the semantic, sink, reachability, and
# caller-supplied finding scanners.

_SAFE = "safe"
_UNKNOWN = "unknown"
_RAISES = "raises"


def _known_constants(
    module_bindings: dict[str, ast.AST],
    local_bindings: dict[str, ast.AST],
) -> dict[str, Any]:
    pending = dict(module_bindings)
    pending.update(local_bindings)
    constants: dict[str, Any] = {}

    for _ in range(len(pending) + 1):
        progress = False
        for name, node in pending.items():
            if name in constants or isinstance(
                node,
                (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda, ast.ClassDef),
            ):
                continue
            value = prerequisite_execution._static_eval(node, constants)
            if value is prerequisite_execution._STATIC_UNKNOWN:
                continue
            if value is prerequisite_execution._STATIC_RAISES:
                continue
            constants[name] = value
            progress = True
        if not progress:
            break

    return constants


def _structurally_safe(node: ast.AST) -> bool:
    """Recognize simple eager expressions that add no new execution gate.

    Calls, subscripts, starred expansion, formatted values, and similar
    execution-bearing expressions deliberately remain prerequisites. The set is
    narrow enough to catch new failure opportunities without turning ordinary
    path/name expressions into compatibility noise.
    """

    if isinstance(node, (ast.Constant, ast.Name)):
        return True
    if isinstance(node, ast.Attribute):
        return _structurally_safe(node.value)
    if isinstance(node, ast.UnaryOp):
        return _structurally_safe(node.operand)
    if isinstance(node, ast.BinOp):
        return _structurally_safe(node.left) and _structurally_safe(node.right)
    if isinstance(node, (ast.Tuple, ast.List, ast.Set)):
        return all(_structurally_safe(item) for item in node.elts)
    if isinstance(node, ast.Dict):
        return all(
            (key is None or _structurally_safe(key)) and _structurally_safe(value)
            for key, value in zip(node.keys, node.values)
        )
    if isinstance(node, ast.Slice):
        return all(
            item is None or _structurally_safe(item)
            for item in (node.lower, node.upper, node.step)
        )
    return False


def _execution_state(node: ast.AST, constants: dict[str, Any]) -> str:
    value = prerequisite_execution._static_eval(node, constants)
    if value is prerequisite_execution._STATIC_RAISES:
        return _RAISES
    if value is not prerequisite_execution._STATIC_UNKNOWN:
        return _SAFE
    if _structurally_safe(node):
        return _SAFE
    return _UNKNOWN


def _literal_constants(visitor) -> dict[str, Any]:
    return _known_constants(visitor.module_definitions, visitor.local_bindings)


def _parameterized_constants(visitor) -> dict[str, Any]:
    return _known_constants(
        getattr(visitor, "module_values", {}),
        getattr(visitor, "local_bindings", {}),
    )


def _prerequisite_node(nodes: list[ast.AST]) -> ast.AST:
    if len(nodes) == 1:
        return copy.deepcopy(nodes[0])
    result = ast.Tuple(
        elts=[copy.deepcopy(node) for node in nodes],
        ctx=ast.Load(),
    )
    ast.fix_missing_locations(result)
    return result


def _literal_visit_sequence(
    visitor,
    nodes: list[ast.AST],
    marker_prefix: str,
) -> bool:
    prerequisites: list[ast.AST] = []
    constants = _literal_constants(visitor)

    for index, node in enumerate(nodes):
        if prerequisites:
            visitor.context.append(
                f"{marker_prefix}:{index}:requires-prior-evaluation"
            )
            visitor.context_nodes.append(_prerequisite_node(prerequisites))
            try:
                visitor.visit(node)
            finally:
                visitor.context_nodes.pop()
                visitor.context.pop()
        else:
            visitor.visit(node)

        state = _execution_state(node, constants)
        if state == _RAISES:
            return False
        if state == _UNKNOWN:
            prerequisites.append(node)
    return True


def _parameterized_visit_sequence(
    visitor,
    nodes: list[ast.AST],
    marker_prefix: str,
) -> bool:
    prerequisites: list[ast.AST] = []
    constants = _parameterized_constants(visitor)

    for index, node in enumerate(nodes):
        if prerequisites:
            visitor.context_nodes.append(
                (
                    f"{marker_prefix}:{index}:requires-prior-evaluation",
                    _prerequisite_node(prerequisites),
                )
            )
            try:
                visitor.visit(node)
            finally:
                visitor.context_nodes.pop()
        else:
            visitor.visit(node)

        state = _execution_state(node, constants)
        if state == _RAISES:
            return False
        if state == _UNKNOWN:
            prerequisites.append(node)
    return True


def _reachability_visit_sequence(visitor, nodes: list[ast.AST]) -> bool:
    constants = getattr(visitor, "constants", {})
    for node in nodes:
        visitor.visit(node)
        if _execution_state(node, constants) == _RAISES:
            return False
    return True


def _dict_evaluation_nodes(node: ast.Dict) -> list[ast.AST]:
    items: list[ast.AST] = []
    for key, value in zip(node.keys, node.values):
        if key is not None:
            items.append(key)
        items.append(value)
    return items


def _call_evaluation_nodes(node: ast.Call) -> list[ast.AST]:
    # The callable expression is evaluated before positional and keyword values.
    return [
        node.func,
        *node.args,
        *(keyword.value for keyword in node.keywords),
    ]


def _install_literal_sequence_methods(visitor_type) -> None:
    def visit_tuple(self, node: ast.Tuple) -> None:
        _literal_visit_sequence(self, list(node.elts), "tuple")

    def visit_list(self, node: ast.List) -> None:
        _literal_visit_sequence(self, list(node.elts), "list")

    def visit_set(self, node: ast.Set) -> None:
        _literal_visit_sequence(self, list(node.elts), "set")

    def visit_dict(self, node: ast.Dict) -> None:
        _literal_visit_sequence(self, _dict_evaluation_nodes(node), "dict")

    def visit_binop(self, node: ast.BinOp) -> None:
        _literal_visit_sequence(self, [node.left, node.right], "binop")

    def visit_subscript(self, node: ast.Subscript) -> None:
        _literal_visit_sequence(self, [node.value, node.slice], "subscript")

    def visit_slice(self, node: ast.Slice) -> None:
        _literal_visit_sequence(
            self,
            [
                item
                for item in (node.lower, node.upper, node.step)
                if item is not None
            ],
            "slice",
        )

    def visit_joined_str(self, node: ast.JoinedStr) -> None:
        _literal_visit_sequence(self, list(node.values), "joined-str")

    visitor_type.visit_Tuple = visit_tuple
    visitor_type.visit_List = visit_list
    visitor_type.visit_Set = visit_set
    visitor_type.visit_Dict = visit_dict
    visitor_type.visit_BinOp = visit_binop
    visitor_type.visit_Subscript = visit_subscript
    visitor_type.visit_Slice = visit_slice
    visitor_type.visit_JoinedStr = visit_joined_str


_install_literal_sequence_methods(literal_base.FindingSignatureVisitor)

_previous_literal_visit_call = literal_base.FindingSignatureVisitor.visit_Call


def _literal_visit_call(self, node: ast.Call) -> None:
    if isinstance(node.func, ast.Name) and node.func.id == "Finding":
        _previous_literal_visit_call(self, node)
        return
    _literal_visit_sequence(self, _call_evaluation_nodes(node), "call")


literal_base.FindingSignatureVisitor.visit_Call = _literal_visit_call


# Sink-aware semantic scanning captured an earlier literal visit_Call at import
# time, so its non-Finding traversal needs the same execution-order patch.
_previous_sink_visit_call = sink_execution.SinkAwareFindingSignatureVisitor.visit_Call


def _sink_visit_call(self, node: ast.Call) -> None:
    if isinstance(node.func, ast.Name) and node.func.id == "Finding":
        _previous_sink_visit_call(self, node)
        return
    _literal_visit_sequence(self, _call_evaluation_nodes(node), "call")


sink_execution.SinkAwareFindingSignatureVisitor.visit_Call = _sink_visit_call


def _install_reachability_sequence_methods(visitor_type) -> None:
    def visit_tuple(self, node: ast.Tuple) -> None:
        _reachability_visit_sequence(self, list(node.elts))

    def visit_list(self, node: ast.List) -> None:
        _reachability_visit_sequence(self, list(node.elts))

    def visit_set(self, node: ast.Set) -> None:
        _reachability_visit_sequence(self, list(node.elts))

    def visit_dict(self, node: ast.Dict) -> None:
        _reachability_visit_sequence(self, _dict_evaluation_nodes(node))

    def visit_binop(self, node: ast.BinOp) -> None:
        _reachability_visit_sequence(self, [node.left, node.right])

    def visit_subscript(self, node: ast.Subscript) -> None:
        _reachability_visit_sequence(self, [node.value, node.slice])

    def visit_slice(self, node: ast.Slice) -> None:
        _reachability_visit_sequence(
            self,
            [
                item
                for item in (node.lower, node.upper, node.step)
                if item is not None
            ],
        )

    def visit_joined_str(self, node: ast.JoinedStr) -> None:
        _reachability_visit_sequence(self, list(node.values))

    visitor_type.visit_Tuple = visit_tuple
    visitor_type.visit_List = visit_list
    visitor_type.visit_Set = visit_set
    visitor_type.visit_Dict = visit_dict
    visitor_type.visit_BinOp = visit_binop
    visitor_type.visit_Subscript = visit_subscript
    visitor_type.visit_Slice = visit_slice
    visitor_type.visit_JoinedStr = visit_joined_str


for _visitor_type in (
    basic_reachability.ReachableFindingVisitor,
    extended_reachability.ExtendedReachableFindingVisitor,
):
    _install_reachability_sequence_methods(_visitor_type)

_previous_basic_visit_call = basic_reachability.ReachableFindingVisitor.visit_Call
_previous_extended_visit_call = (
    extended_reachability.ExtendedReachableFindingVisitor.visit_Call
)


def _make_reachability_visit_call(previous: Callable):
    def visit_call(self, node: ast.Call) -> None:
        if isinstance(node.func, ast.Name) and node.func.id == "Finding":
            previous(self, node)
            return
        _reachability_visit_sequence(self, _call_evaluation_nodes(node))

    return visit_call


basic_reachability.ReachableFindingVisitor.visit_Call = (
    _make_reachability_visit_call(_previous_basic_visit_call)
)
extended_reachability.ExtendedReachableFindingVisitor.visit_Call = (
    _make_reachability_visit_call(_previous_extended_visit_call)
)

_previous_sink_reachable_visit_call = (
    sink_execution.SinkAwareReachableFindingVisitor.visit_Call
)


def _sink_reachable_visit_call(self, node: ast.Call) -> None:
    if isinstance(node.func, ast.Name) and node.func.id == "Finding":
        _previous_sink_reachable_visit_call(self, node)
        return
    _reachability_visit_sequence(self, _call_evaluation_nodes(node))


sink_execution.SinkAwareReachableFindingVisitor.visit_Call = (
    _sink_reachable_visit_call
)


_parameterized_visitor = parameterized_active.BranchAwareParameterizedCallSiteVisitor


def _install_parameterized_sequence_methods(visitor_type) -> None:
    def visit_tuple(self, node: ast.Tuple) -> None:
        _parameterized_visit_sequence(self, list(node.elts), "tuple")

    def visit_list(self, node: ast.List) -> None:
        _parameterized_visit_sequence(self, list(node.elts), "list")

    def visit_set(self, node: ast.Set) -> None:
        _parameterized_visit_sequence(self, list(node.elts), "set")

    def visit_dict(self, node: ast.Dict) -> None:
        _parameterized_visit_sequence(self, _dict_evaluation_nodes(node), "dict")

    def visit_binop(self, node: ast.BinOp) -> None:
        _parameterized_visit_sequence(self, [node.left, node.right], "binop")

    def visit_subscript(self, node: ast.Subscript) -> None:
        _parameterized_visit_sequence(
            self,
            [node.value, node.slice],
            "subscript",
        )

    def visit_slice(self, node: ast.Slice) -> None:
        _parameterized_visit_sequence(
            self,
            [
                item
                for item in (node.lower, node.upper, node.step)
                if item is not None
            ],
            "slice",
        )

    def visit_joined_str(self, node: ast.JoinedStr) -> None:
        _parameterized_visit_sequence(
            self,
            list(node.values),
            "joined-str",
        )

    visitor_type.visit_Tuple = visit_tuple
    visitor_type.visit_List = visit_list
    visitor_type.visit_Set = visit_set
    visitor_type.visit_Dict = visit_dict
    visitor_type.visit_BinOp = visit_binop
    visitor_type.visit_Subscript = visit_subscript
    visitor_type.visit_Slice = visit_slice
    visitor_type.visit_JoinedStr = visit_joined_str


_install_parameterized_sequence_methods(_parameterized_visitor)

_previous_parameterized_visit_call = _parameterized_visitor.visit_Call


def _parameterized_visit_call(self, node: ast.Call) -> None:
    is_helper = (
        isinstance(node.func, ast.Name)
        and node.func.id in self.parameterized_helpers
    )

    if is_helper:
        constants = _parameterized_constants(self)
        states = [
            _execution_state(item, constants)
            for item in _call_evaluation_nodes(node)
        ]
        if _RAISES in states:
            _parameterized_visit_sequence(
                self,
                _call_evaluation_nodes(node),
                "call",
            )
            return

        prerequisites = [
            item
            for item, state in zip(_call_evaluation_nodes(node), states)
            if state == _UNKNOWN
        ]
        if prerequisites:
            self.context_nodes.append(
                (
                    "call:invocation:requires-argument-evaluation",
                    _prerequisite_node(prerequisites),
                )
            )
            try:
                _previous_parameterized_visit_call(self, node)
            finally:
                self.context_nodes.pop()
        else:
            _previous_parameterized_visit_call(self, node)
        return

    _parameterized_visit_sequence(self, _call_evaluation_nodes(node), "call")


_parameterized_visitor.visit_Call = _parameterized_visit_call
parameterized_active.base.ParameterizedCallSiteVisitor = _parameterized_visitor


_install_reachability_sequence_methods(
    parameterized_reachability.ReachableParameterizedCallSiteVisitor
)
_previous_reachable_parameterized_visit_call = (
    parameterized_reachability.ReachableParameterizedCallSiteVisitor.visit_Call
)


def _reachable_parameterized_visit_call(self, node: ast.Call) -> None:
    is_helper = (
        isinstance(node.func, ast.Name)
        and node.func.id in self.parameterized_helpers
    )
    if is_helper:
        constants = getattr(self, "constants", {})
        if any(
            _execution_state(item, constants) == _RAISES
            for item in _call_evaluation_nodes(node)
        ):
            _reachability_visit_sequence(self, _call_evaluation_nodes(node))
            return
        _previous_reachable_parameterized_visit_call(self, node)
        return

    _reachability_visit_sequence(self, _call_evaluation_nodes(node))


parameterized_reachability.ReachableParameterizedCallSiteVisitor.visit_Call = (
    _reachable_parameterized_visit_call
)


# Parameterized multiplicity visitors have their own helper-call fast path.
# Prevent a helper whose arguments cannot finish evaluating from being counted.
_previous_counting_visit_call = (
    parameterized_multiplicity._CountingParameterizedCallSiteVisitor.visit_Call
)
_previous_counting_reachable_visit_call = (
    parameterized_multiplicity._CountingReachableParameterizedCallSiteVisitor.visit_Call
)


def _counting_parameterized_visit_call(self, node: ast.Call) -> None:
    is_helper = parameterized_multiplicity._is_parameterized_helper_call(
        self,
        node,
    )
    if is_helper and any(
        _execution_state(item, _parameterized_constants(self)) == _RAISES
        for item in _call_evaluation_nodes(node)
    ):
        _parameterized_visit_sequence(
            self,
            _call_evaluation_nodes(node),
            "call",
        )
        return
    if not is_helper:
        _parameterized_visit_call(self, node)
        return
    _previous_counting_visit_call(self, node)


def _counting_reachable_parameterized_visit_call(self, node: ast.Call) -> None:
    is_helper = parameterized_multiplicity._is_parameterized_helper_call(
        self,
        node,
    )
    if is_helper and any(
        _execution_state(item, getattr(self, "constants", {})) == _RAISES
        for item in _call_evaluation_nodes(node)
    ):
        _reachability_visit_sequence(self, _call_evaluation_nodes(node))
        return
    if not is_helper:
        _reachable_parameterized_visit_call(self, node)
        return
    _previous_counting_reachable_visit_call(self, node)


parameterized_multiplicity._CountingParameterizedCallSiteVisitor.visit_Call = (
    _counting_parameterized_visit_call
)
parameterized_multiplicity._CountingReachableParameterizedCallSiteVisitor.visit_Call = (
    _counting_reachable_parameterized_visit_call
)


class ReleaseCandidateLeftToRightExpressionExecutionTests(unittest.TestCase):
    def test_raising_tuple_element_hides_later_literal_finding(self) -> None:
        source = '''
def validate(findings):
    (1 / 0, findings.append(Finding("PUBLIC_CODE", "hidden")))
'''
        self.assertNotIn(
            "PUBLIC_CODE",
            literal_base.finding_semantic_signatures(source),
        )
        self.assertNotIn(
            "PUBLIC_CODE",
            sink_execution.finding_semantic_signatures_with_sink(source),
        )
        self.assertEqual(
            basic_reachability.reachable_contracts(source, "sample.py"),
            Counter(),
        )
        self.assertEqual(
            extended_reachability.reachable_contracts(source, "sample.py"),
            Counter(),
        )
        self.assertEqual(
            sink_execution.reachable_emission_contracts(source, "sample.py"),
            Counter(),
        )

    def test_raising_call_argument_hides_later_literal_finding(self) -> None:
        source = '''
def emit(*args):
    return args
def validate(findings):
    emit(1 / 0, findings.append(Finding("PUBLIC_CODE", "hidden")))
'''
        self.assertNotIn(
            "PUBLIC_CODE",
            literal_base.finding_semantic_signatures(source),
        )
        self.assertNotIn(
            "PUBLIC_CODE",
            sink_execution.finding_semantic_signatures_with_sink(source),
        )
        self.assertEqual(
            extended_reachability.reachable_contracts(source, "sample.py"),
            Counter(),
        )
        self.assertEqual(
            sink_execution.reachable_emission_contracts(source, "sample.py"),
            Counter(),
        )

    def test_raising_left_binary_operand_hides_later_literal_finding(self) -> None:
        source = '''
def validate(findings):
    (1 / 0) + findings.append(Finding("PUBLIC_CODE", "hidden"))
'''
        self.assertNotIn(
            "PUBLIC_CODE",
            literal_base.finding_semantic_signatures(source),
        )
        self.assertEqual(
            extended_reachability.reachable_contracts(source, "sample.py"),
            Counter(),
        )

    def test_safe_prior_tuple_element_does_not_change_literal_contract(self) -> None:
        direct = '''
def validate(findings):
    findings.append(Finding("PUBLIC_CODE", "visible"))
'''
        wrapped = '''
def validate(findings):
    (0, findings.append(Finding("PUBLIC_CODE", "visible")))
'''
        self.assertEqual(
            literal_base.finding_semantic_signatures(direct),
            literal_base.finding_semantic_signatures(wrapped),
        )

    def test_unknown_prior_expression_adds_execution_prerequisite(self) -> None:
        direct = '''
def validate(findings):
    findings.append(Finding("PUBLIC_CODE", "visible"))
'''
        guarded = '''
def maybe_fail():
    return None
def validate(findings):
    (maybe_fail(), findings.append(Finding("PUBLIC_CODE", "visible")))
'''
        expected = literal_base.finding_semantic_signatures(direct)
        actual = literal_base.finding_semantic_signatures(guarded)
        self.assertNotEqual(expected, actual)
        payload = json.loads(actual["PUBLIC_CODE"][0])
        self.assertTrue(
            any(
                marker.startswith("tuple:1:requires-prior-evaluation")
                for marker in payload["context"]
            )
        )
        self.assertIn("maybe_fail", payload["dependencies"])

    def test_raising_tuple_element_hides_parameterized_finding_call(self) -> None:
        source = '''
def read_text(path, findings, code):
    Finding(code, "decode failed", path="sample")
def validate(root, findings):
    (1 / 0, read_text(root / "LICENSE", findings, "LICENSE_ENCODING"))
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

    def test_raising_outer_call_argument_hides_parameterized_finding_call(self) -> None:
        source = '''
def wrapper(*args):
    return args
def read_text(path, findings, code):
    Finding(code, "decode failed", path="sample")
def validate(root, findings):
    wrapper(1 / 0, read_text(root / "LICENSE", findings, "LICENSE_ENCODING"))
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

    def test_raising_parameterized_helper_argument_prevents_invocation(self) -> None:
        source = '''
def read_text(path, findings, code):
    Finding(code, "decode failed", path="sample")
def validate(findings):
    read_text(1 / 0, findings, "LICENSE_ENCODING")
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
        self.assertEqual(
            parameterized_multiplicity._reachable_parameterized_counts(
                source,
                "sample.py",
            ),
            Counter(),
        )


if __name__ == "__main__":
    unittest.main()
