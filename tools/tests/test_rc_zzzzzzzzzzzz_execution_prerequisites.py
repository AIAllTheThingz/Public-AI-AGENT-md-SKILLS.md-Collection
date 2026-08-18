from __future__ import annotations

import ast
import copy
import hashlib
import json
import operator
import unittest
from collections import Counter
from typing import Any

import rc_finding_code_contracts_base as literal_base
import rc_reachability_semantics as reachability_semantics
import test_rc_extended_finding_reachability as extended_reachability
import test_rc_finding_reachability as basic_reachability
import test_rc_parameterized_finding_codes as parameterized_active
import test_rc_parameterized_finding_reachability as parameterized_reachability
import test_rc_zzz_finding_emission_sink as sink_execution
import test_rc_zzzzzzzzzzz_context_manager_entry_execution as context_manager_execution  # noqa: F401


# Final composition layer for PR #71. This module sorts after the preceding
# execution overlays and therefore strengthens the fully composed scanners.


# ---------------------------------------------------------------------------
# Keep the sink regression scoped to the sink contract it owns.
# ---------------------------------------------------------------------------

def _sink_fingerprint(signature: str) -> str:
    payload = json.loads(signature)
    return json.dumps(
        {
            key: payload[key]
            for key in ("sourcePath", "function", "emission", "sink")
            if key in payload
        },
        sort_keys=True,
    )


def _test_every_published_finding_sink_is_preserved(self) -> None:
    published = sink_execution.published_sink_signatures()
    current = sink_execution.candidate_sink_signatures()
    approved = self.contract["approvedAdditivePublishedCodeContexts"]

    self.assertGreater(len(published), 20)
    for code, expected_signatures in published.items():
        with self.subTest(code=code):
            if code in sink_execution.finding_contracts._BEHAVIOR_BOUND_FINDING_CONTEXTS:
                continue

            expected_sinks = {
                _sink_fingerprint(signature) for signature in expected_signatures
            }
            current_sinks = {
                _sink_fingerprint(signature)
                for signature in current.get(code, set())
            }
            self.assertEqual(
                expected_sinks - current_sinks,
                set(),
                f"published emission sink changed/disappeared for {code}",
            )
            if code not in approved:
                self.assertEqual(
                    current_sinks - expected_sinks,
                    set(),
                    f"unreviewed emission sink added for public code {code}",
                )


sink_execution.ReleaseCandidateFindingEmissionSinkRegressionTests.test_every_published_finding_sink_semantic_is_preserved = (
    _test_every_published_finding_sink_is_preserved
)


# ---------------------------------------------------------------------------
# Exception-handler execution prerequisites and handler order.
# ---------------------------------------------------------------------------

def _handler_is_catch_all(handler: ast.ExceptHandler) -> bool:
    node = handler.type
    if node is None:
        return True
    if isinstance(node, ast.Name):
        return node.id in {"Exception", "BaseException"}
    if isinstance(node, ast.Tuple):
        return any(
            isinstance(item, ast.Name)
            and item.id in {"Exception", "BaseException"}
            for item in node.elts
        )
    return False


def _handler_prerequisite_node(node: ast.AST, handler_index: int) -> ast.Module:
    statements: list[ast.stmt] = list(copy.deepcopy(getattr(node, "body")))
    handlers = list(getattr(node, "handlers"))
    for index, previous in enumerate(handlers[:handler_index]):
        type_node = (
            copy.deepcopy(previous.type)
            if previous.type is not None
            else ast.Constant(value="<bare-except>")
        )
        statements.append(
            ast.Expr(
                value=ast.Tuple(
                    elts=[
                        ast.Constant(value=f"prior-handler:{index}"),
                        type_node,
                    ],
                    ctx=ast.Load(),
                )
            )
        )
        statements.extend(copy.deepcopy(previous.body))
    module = ast.Module(body=statements, type_ignores=[])
    ast.fix_missing_locations(module)
    return module


def _literal_visit_try_regions(self, node: ast.AST, *, star: bool) -> None:
    prefix = "try-star" if star else "try"
    handler_prefix = "except-star" if star else "except"

    self._with_context(prefix, None, getattr(node, "body"))
    for index, handler in enumerate(getattr(node, "handlers")):
        prerequisite = _handler_prerequisite_node(node, index)
        material = literal_base.normalized_semantic_ast(prerequisite)
        digest = hashlib.sha256(material.encode("utf-8")).hexdigest()[:16]
        exception_type = (
            literal_base.canonical_ast(handler.type)
            if handler.type is not None
            else "bare"
        )
        self._with_context(
            f"{handler_prefix}:{index}:{exception_type}:requires-prior:{digest}",
            prerequisite,
            handler.body,
        )
        if _handler_is_catch_all(handler):
            break

    orelse = getattr(node, "orelse")
    finalbody = getattr(node, "finalbody")
    if orelse:
        self._with_context(f"{prefix}-else", None, orelse)
    if finalbody:
        self._with_context(f"{prefix}-finally", None, finalbody)


literal_base.FindingSignatureVisitor._visit_try_regions = _literal_visit_try_regions


def _parameterized_prerequisite_marker(
    visitor,
    node: ast.AST,
    handler_index: int,
) -> ast.Constant:
    prerequisite = _handler_prerequisite_node(node, handler_index)
    material = parameterized_active.base.semantic_expression(
        prerequisite,
        visitor.local_bindings,
        visitor.module_values,
        visitor.parameter_positions,
    )
    digest = hashlib.sha256(material.encode("utf-8")).hexdigest()[:16]
    return ast.Constant(value=f"handler-prerequisite:{digest}")


def _parameterized_visit_try_regions(
    self,
    node: ast.AST,
    prefix: str = "try",
) -> None:
    self._with_context(
        f"{prefix}:body",
        ast.Constant(value=prefix),
        getattr(node, "body"),
    )
    for index, handler in enumerate(getattr(node, "handlers")):
        self._with_context(
            f"{prefix}:except:{index}:requires-prior",
            _parameterized_prerequisite_marker(self, node, index),
            handler.body,
        )
        if _handler_is_catch_all(handler):
            break

    orelse = getattr(node, "orelse")
    finalbody = getattr(node, "finalbody")
    if orelse:
        self._with_context(
            f"{prefix}:else",
            ast.Constant(value=prefix),
            orelse,
        )
    if finalbody:
        self._with_context(
            f"{prefix}:finally",
            ast.Constant(value=prefix),
            finalbody,
        )


parameterized_active.BranchAwareParameterizedCallSiteVisitor._visit_try_regions = (
    _parameterized_visit_try_regions
)
parameterized_active.base.ParameterizedCallSiteVisitor = (
    parameterized_active.BranchAwareParameterizedCallSiteVisitor
)


def _visit_try_reachability(self, node: ast.AST) -> None:
    self._visit_block(getattr(node, "body"))
    for handler in getattr(node, "handlers"):
        if handler.type is not None:
            self.visit(handler.type)
        self._visit_block(handler.body)
        if _handler_is_catch_all(handler):
            break
    self._visit_block(getattr(node, "orelse"))
    self._visit_block(getattr(node, "finalbody"))


for _visitor_type in (
    basic_reachability.ReachableFindingVisitor,
    extended_reachability.ExtendedReachableFindingVisitor,
):
    _visitor_type.visit_Try = _visit_try_reachability
    if hasattr(ast, "TryStar"):
        _visitor_type.visit_TryStar = _visit_try_reachability


def _visit_parameterized_try(self, node: ast.Try) -> None:
    _parameterized_visit_try_regions(self, node, "try")


def _visit_parameterized_try_star(self, node: ast.AST) -> None:
    _parameterized_visit_try_regions(self, node, "try*")


parameterized_reachability.ReachableParameterizedCallSiteVisitor.visit_Try = (
    _visit_parameterized_try
)
if hasattr(ast, "TryStar"):
    parameterized_reachability.ReachableParameterizedCallSiteVisitor.visit_TryStar = (
        _visit_parameterized_try_star
    )


# ---------------------------------------------------------------------------
# Guaranteed static exceptions terminate the current block.
# ---------------------------------------------------------------------------

_STATIC_UNKNOWN = object()
_STATIC_RAISES = object()

_BINOPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.LShift: operator.lshift,
    ast.RShift: operator.rshift,
    ast.BitOr: operator.or_,
    ast.BitXor: operator.xor,
    ast.BitAnd: operator.and_,
}

_UNARYOPS = {
    ast.UAdd: operator.pos,
    ast.USub: operator.neg,
    ast.Invert: operator.invert,
}


def _static_eval(node: ast.AST, constants: dict[str, Any]) -> object:
    if isinstance(node, ast.Constant):
        return node.value

    if isinstance(node, ast.Name):
        value = constants.get(node.id, _STATIC_UNKNOWN)
        if value is reachability_semantics.UNKNOWN or value is basic_reachability.UNKNOWN:
            return _STATIC_UNKNOWN
        return value

    if isinstance(node, ast.UnaryOp):
        operand = _static_eval(node.operand, constants)
        if operand is _STATIC_RAISES:
            return _STATIC_RAISES
        if operand is _STATIC_UNKNOWN:
            return _STATIC_UNKNOWN
        try:
            if isinstance(node.op, ast.Not):
                return not bool(operand)
            for operation_type, operation in _UNARYOPS.items():
                if isinstance(node.op, operation_type):
                    return operation(operand)
        except (ArithmeticError, TypeError, ValueError, OverflowError):
            return _STATIC_RAISES
        return _STATIC_UNKNOWN

    if isinstance(node, ast.BoolOp):
        if isinstance(node.op, ast.And):
            last: object = True
            for item in node.values:
                last = _static_eval(item, constants)
                if last is _STATIC_RAISES:
                    return _STATIC_RAISES
                if last is _STATIC_UNKNOWN:
                    return _STATIC_UNKNOWN
                if not bool(last):
                    return last
            return last
        if isinstance(node.op, ast.Or):
            last = False
            for item in node.values:
                last = _static_eval(item, constants)
                if last is _STATIC_RAISES:
                    return _STATIC_RAISES
                if last is _STATIC_UNKNOWN:
                    return _STATIC_UNKNOWN
                if bool(last):
                    return last
            return last

    if isinstance(node, ast.IfExp):
        test = _static_eval(node.test, constants)
        if test is _STATIC_RAISES:
            return _STATIC_RAISES
        if test is _STATIC_UNKNOWN:
            return _STATIC_UNKNOWN
        return _static_eval(node.body if bool(test) else node.orelse, constants)

    if isinstance(node, ast.BinOp):
        left = _static_eval(node.left, constants)
        if left is _STATIC_RAISES:
            return _STATIC_RAISES
        if left is _STATIC_UNKNOWN:
            return _STATIC_UNKNOWN

        right = _static_eval(node.right, constants)
        if right is _STATIC_RAISES:
            return _STATIC_RAISES
        if right is _STATIC_UNKNOWN:
            return _STATIC_UNKNOWN

        try:
            if isinstance(node.op, ast.Pow):
                if (
                    isinstance(right, int)
                    and not isinstance(right, bool)
                    and abs(right) <= 32
                ):
                    return operator.pow(left, right)
                return _STATIC_UNKNOWN

            for operation_type, operation in _BINOPS.items():
                if isinstance(node.op, operation_type):
                    if isinstance(node.op, (ast.LShift, ast.RShift)) and (
                        not isinstance(right, int)
                        or isinstance(right, bool)
                        or abs(right) > 4096
                    ):
                        return _STATIC_UNKNOWN
                    return operation(left, right)
        except (ArithmeticError, TypeError, ValueError, OverflowError):
            return _STATIC_RAISES
        return _STATIC_UNKNOWN

    existing = reachability_semantics.static_value(node, constants)
    if existing is not reachability_semantics.UNKNOWN:
        return existing
    return _STATIC_UNKNOWN


def _expression_statically_raises(
    node: ast.AST | None,
    constants: dict[str, Any],
) -> bool:
    return node is not None and _static_eval(node, constants) is _STATIC_RAISES


_previous_statement_always_terminates = (
    reachability_semantics.statement_always_terminates
)


def _statement_always_terminates(
    node: ast.stmt,
    constants: dict[str, Any] | None = None,
) -> bool:
    state = dict(constants or {})
    expression: ast.AST | None = None

    if isinstance(node, ast.Expr):
        expression = node.value
    elif isinstance(node, (ast.Assign, ast.AnnAssign, ast.AugAssign)):
        expression = node.value
    elif isinstance(node, (ast.If, ast.While, ast.Assert)):
        expression = node.test
    elif isinstance(node, (ast.For, ast.AsyncFor)):
        expression = node.iter
    elif isinstance(node, ast.Match):
        expression = node.subject

    if _expression_statically_raises(expression, state):
        return True
    return _previous_statement_always_terminates(node, state)


reachability_semantics.statement_always_terminates = _statement_always_terminates
basic_reachability.statement_always_terminates = _statement_always_terminates
extended_reachability.statement_always_terminates = _statement_always_terminates
parameterized_reachability.statement_always_terminates = _statement_always_terminates


# ---------------------------------------------------------------------------
# Permanent regression coverage.
# ---------------------------------------------------------------------------

class ReleaseCandidateExecutionPrerequisiteRegressionTests(unittest.TestCase):
    def test_try_handler_signature_tracks_try_body_helper_semantics(self) -> None:
        raising = """
def load_json(path):
    raise ValueError("invalid")
def validate(path):
    try:
        load_json(path)
    except ValueError:
        Finding("PUBLIC_CODE", "invalid")
"""
        non_raising = """
def load_json(path):
    return {}
def validate(path):
    try:
        load_json(path)
    except ValueError:
        Finding("PUBLIC_CODE", "invalid")
"""
        expected = literal_base.finding_semantic_signatures(raising)
        actual = literal_base.finding_semantic_signatures(non_raising)
        self.assertNotEqual(expected, actual)
        payload = json.loads(expected["PUBLIC_CODE"][0])
        self.assertTrue(
            any("requires-prior" in marker for marker in payload["context"])
        )
        self.assertIn("load_json", payload["dependencies"])

    def test_earlier_broad_handler_hides_later_literal_finding(self) -> None:
        source = """
def validate(value):
    try:
        int(value)
    except Exception:
        pass
    except ValueError:
        Finding("PUBLIC_CODE", "unreachable")
"""
        self.assertNotIn(
            "PUBLIC_CODE",
            literal_base.finding_semantic_signatures(source),
        )
        self.assertEqual(
            extended_reachability.reachable_contracts(source, "sample.py"),
            Counter(),
        )

    def test_parameterized_handler_contract_tracks_try_prerequisite(self) -> None:
        first = """
def read_text(path, findings, code):
    Finding(code, "decode failed", path="sample")
def parse_one(path):
    return path
def validate(path, findings):
    try:
        parse_one(path)
    except ValueError:
        read_text(path, findings, "PUBLIC_CODE")
"""
        second = first.replace("parse_one(path)", "parse_two(path)").replace(
            "def parse_one(path):", "def parse_two(path):"
        )
        expected = parameterized_active.parameterized_finding_contracts(
            first, "sample.py"
        )
        actual = parameterized_active.parameterized_finding_contracts(
            second, "sample.py"
        )
        self.assertNotEqual(expected, actual)

    def test_guaranteed_division_by_zero_hides_literal_finding(self) -> None:
        source = """
def validate():
    1 / 0
    Finding("PUBLIC_CODE", "unreachable")
"""
        self.assertEqual(
            extended_reachability.reachable_contracts(source, "sample.py"),
            Counter(),
        )

    def test_guaranteed_division_by_zero_hides_parameterized_call(self) -> None:
        source = """
def read_text(path, findings, code):
    Finding(code, "decode failed", path="sample")
def validate(path, findings):
    1 / 0
    read_text(path, findings, "PUBLIC_CODE")
"""
        self.assertEqual(
            parameterized_reachability.reachable_parameterized_contracts(
                source, "sample.py"
            ),
            set(),
        )

    def test_unknown_division_remains_conservatively_reachable(self) -> None:
        source = """
def validate(value):
    1 / value
    Finding("PUBLIC_CODE", "possibly reachable")
"""
        contracts = extended_reachability.reachable_contracts(
            source, "sample.py"
        )
        self.assertEqual(
            contracts[("sample.py", "validate", "PUBLIC_CODE")],
            1,
        )

    def test_sink_fingerprint_ignores_execution_prerequisite_only(self) -> None:
        direct = """
def validate(findings):
    findings.append(Finding("PUBLIC_CODE", "visible"))
"""
        wrapped = """
def manager():
    return unknown_context_manager()
def validate(findings):
    with manager():
        findings.append(Finding("PUBLIC_CODE", "visible"))
"""
        direct_signature = literal_base.finding_semantic_signatures(direct)[
            "PUBLIC_CODE"
        ][0]
        wrapped_signature = literal_base.finding_semantic_signatures(wrapped)[
            "PUBLIC_CODE"
        ][0]
        self.assertNotEqual(direct_signature, wrapped_signature)
        self.assertEqual(
            _sink_fingerprint(direct_signature),
            _sink_fingerprint(wrapped_signature),
        )


if __name__ == "__main__":
    unittest.main()
