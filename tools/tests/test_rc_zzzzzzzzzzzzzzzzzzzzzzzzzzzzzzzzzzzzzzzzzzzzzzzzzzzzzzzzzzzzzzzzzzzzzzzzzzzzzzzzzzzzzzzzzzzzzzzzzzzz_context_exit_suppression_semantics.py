from __future__ import annotations

import ast
import importlib
import unittest
from pathlib import Path

import rc_finding_code_contracts_base as base


# Final context-exit suppression closure for PR #71.
#
# A successful __exit__/__aexit__ is not semantically uniform when an exception
# can still occur after a published finding has been emitted. A truthy exit
# result suppresses that in-body exception; a falsy result lets it escape to the
# tool boundary, where execute_tool can replace the published diagnostic with an
# INTERNAL_ERROR. Preserve that distinction without making harmless True/False
# changes relevant when no post-emission exception can occur before the exit.


def _load_overlay(suffix: str):
    matches = sorted(Path(__file__).parent.glob(f"test_rc_*{suffix}.py"))
    if len(matches) != 1:
        raise RuntimeError(f"expected exactly one RC overlay for {suffix!r}")
    return importlib.import_module(matches[0].stem)


loop_risk = _load_overlay("_compositional_loop_continuation_risk")
loop_layer = loop_risk.loop_layer
prior = loop_layer.prior
exit_layer = loop_layer.exit_layer

_SAFE = prior._SAFE

_SUPPRESSES = "suppresses"
_PROPAGATES = "propagates"
_SUPPRESSION_UNKNOWN = "unknown"


def _literal_truth(node: ast.AST | None) -> bool | None:
    """Return literal truthiness without executing candidate code."""

    if node is None:
        return False
    try:
        value = ast.literal_eval(node)
    except (ValueError, TypeError, SyntaxError):
        return None
    try:
        return bool(value)
    except Exception:
        return None


def _context_exit_suppression_state(
    expression: ast.AST,
    definitions: dict[str, ast.AST],
    *,
    async_mode: bool,
    seen: set[str] | None = None,
) -> str:
    """Classify whether a proven-safe context exit suppresses an exception."""

    if not isinstance(expression, ast.Call) or not isinstance(expression.func, ast.Name):
        return _SUPPRESSION_UNKNOWN

    active = set() if seen is None else set(seen)
    name = expression.func.id
    if name in active:
        return _SUPPRESSION_UNKNOWN
    active.add(name)

    definition = definitions.get(name)
    if isinstance(definition, ast.ClassDef):
        # Suppression meaning is trusted only after the existing final classifier
        # has proved protocol binding, sync/async shape, and direct exit execution
        # safe. Raising/unknown exits remain governed by their existing risk.
        if (
            loop_layer._context_exit_state(
                expression,
                definitions,
                async_mode=async_mode,
            )
            != _SAFE
        ):
            return _SUPPRESSION_UNKNOWN

        method = exit_layer._class_exit_method(definition, async_mode=async_mode)
        if method is None:
            return _SUPPRESSION_UNKNOWN

        statement = exit_layer.context_entry._first_effective_statement(method.body)
        if statement is None:
            # Falling off __exit__ returns None, which is falsy.
            return _PROPAGATES
        if not isinstance(statement, ast.Return):
            return _SUPPRESSION_UNKNOWN

        truth = _literal_truth(statement.value)
        if truth is None:
            return _SUPPRESSION_UNKNOWN
        return _SUPPRESSES if truth else _PROPAGATES

    if isinstance(definition, (ast.FunctionDef, ast.AsyncFunctionDef)):
        returned = exit_layer.context_entry._returned_expression(definition)
        if returned is not None:
            return _context_exit_suppression_state(
                returned,
                definitions,
                async_mode=async_mode,
                seen=active,
            )

    return _SUPPRESSION_UNKNOWN


def _pending_suppression_state(
    visitor,
    obligations: tuple[tuple[ast.AST, bool], ...],
) -> str:
    """Classify whether the exits still pending for one lexical segment suppress."""

    definitions = getattr(visitor, "_context_manager_definitions", {})
    saw_unknown = False

    # Context managers leave in reverse acquisition order. If any proven-safe
    # pending exit definitely suppresses the current exception, the exception
    # does not escape that context stack. Unknown exits remain conservative.
    for expression, async_mode in reversed(obligations):
        if loop_layer._approved_history_obligation(visitor, expression):
            continue

        state = _context_exit_suppression_state(
            expression,
            definitions,
            async_mode=async_mode,
        )
        if state == _SUPPRESSES:
            return _SUPPRESSES
        if state == _SUPPRESSION_UNKNOWN:
            saw_unknown = True

    return _SUPPRESSION_UNKNOWN if saw_unknown else _PROPAGATES


# ---------------------------------------------------------------------------
# Track lexical risk segments that occur before each still-pending context exit.
# ---------------------------------------------------------------------------

_previous_with_context = prior._PostEmissionConditionalRiskVisitor._with_context


def _with_context_with_exit_frames(
    self,
    marker: str,
    dependency_node: ast.AST | None,
    statements: list[ast.stmt],
) -> None:
    is_context_body = marker.startswith(
        "with:body:requires-entry:"
    ) or marker.startswith("async-with:body:requires-entry:")
    if not is_context_body:
        return _previous_with_context(self, marker, dependency_node, statements)

    frames = getattr(self, "_context_suppression_frames", None)
    if frames is None:
        frames = []
        self._context_suppression_frames = frames

    # _post_risk_score at body entry is exactly the risk that occurs after this
    # context has already exited. During nested _visit_block traversal, the
    # difference from this baseline is therefore lexical exception risk that
    # still occurs before this exit obligation is discharged.
    frame = (
        self._post_risk_score,
        tuple(getattr(self, "_pending_context_exits", ())),
    )
    frames.append(frame)
    try:
        return _previous_with_context(self, marker, dependency_node, statements)
    finally:
        frames.pop()


prior._PostEmissionConditionalRiskVisitor._with_context = (
    _with_context_with_exit_frames
)


def _suppressed_lexical_risk(self) -> int:
    frames = getattr(self, "_context_suppression_frames", ())
    if not frames:
        return 0

    current = self._post_risk_score
    inner_delta = 0
    suppressed = 0

    # Frames are outer -> inner. Work back out so each delta is counted only in
    # the lexical segment before the corresponding exit. This handles nested
    # contexts without letting an inner suppressor incorrectly cancel a failure
    # that occurs after that inner context has already exited.
    for outer_risk, obligations in reversed(frames):
        delta = max(0, current - outer_risk)
        segment_risk = max(0, delta - inner_delta)
        if segment_risk and _pending_suppression_state(self, obligations) == _SUPPRESSES:
            suppressed += segment_risk
        inner_delta = delta

    return suppressed


_previous_visit_call = prior._PostEmissionConditionalRiskVisitor.visit_Call


def _visit_call_with_exit_suppression(self, node: ast.Call) -> None:
    code = None
    key = None
    before = 0
    if isinstance(node.func, ast.Name) and node.func.id == "Finding":
        code = base.finding_code(node)
        if code is not None:
            key = (self.source_path, self.function, code)
            before = len(self.risks.get(key, []))

    _previous_visit_call(self, node)

    if code is None or key is None or len(self.risks.get(key, [])) <= before:
        return

    suppressed = _suppressed_lexical_risk(self)
    if suppressed:
        # Existing exit-execution, enclosing-finally, and loop-continuation risk
        # remains intact. Remove only lexical exception risk proven to occur
        # before a definitely suppressing pending exit.
        self.risks[key][-1] = max(0, self.risks[key][-1] - suppressed)


prior._PostEmissionConditionalRiskVisitor.visit_Call = (
    _visit_call_with_exit_suppression
)


class ReleaseCandidateContextExitSuppressionSemanticsTests(unittest.TestCase):
    def test_truthy_exit_suppresses_post_emission_callback_failure(self) -> None:
        suppressing = """
from standards_tools import Finding, ToolResult

class Manager:
    def __enter__(self):
        return self
    def __exit__(self, exc_type, exc, tb):
        return True

def run(findings, callback):
    with Manager():
        findings.append(Finding("PUBLIC_CODE", "message"))
        callback()
    return ToolResult.from_findings("validate", findings)
"""
        propagating = suppressing.replace("return True", "return False")
        key = ("sample.py", "run", "PUBLIC_CODE")
        suppressing_risk = prior._risk_profile(suppressing, "sample.py")[key][0]
        propagating_risk = prior._risk_profile(propagating, "sample.py")[key][0]
        self.assertGreater(propagating_risk, suppressing_risk)

    def test_truthy_async_exit_suppresses_post_emission_callback_failure(self) -> None:
        suppressing = """
from standards_tools import Finding, ToolResult

class Manager:
    async def __aenter__(self):
        return self
    async def __aexit__(self, exc_type, exc, tb):
        return True

async def run(findings, callback):
    async with Manager():
        findings.append(Finding("PUBLIC_CODE", "message"))
        callback()
    return ToolResult.from_findings("validate", findings)
"""
        propagating = suppressing.replace("return True", "return False")
        key = (
            "sample.py",
            f"run{loop_layer.async_execution.COROUTINE_SUFFIX}",
            "PUBLIC_CODE",
        )
        suppressing_risk = prior._risk_profile(suppressing, "sample.py")[key][0]
        propagating_risk = prior._risk_profile(propagating, "sample.py")[key][0]
        self.assertGreater(propagating_risk, suppressing_risk)

    def test_exit_truthiness_is_irrelevant_without_in_body_failure_risk(self) -> None:
        truthy = """
from standards_tools import Finding, ToolResult

class Manager:
    def __enter__(self):
        return self
    def __exit__(self, exc_type, exc, tb):
        return True

def run(findings):
    with Manager():
        findings.append(Finding("PUBLIC_CODE", "message"))
    return ToolResult.from_findings("validate", findings)
"""
        falsy = truthy.replace("return True", "return False")
        key = ("sample.py", "run", "PUBLIC_CODE")
        truthy_risk = prior._risk_profile(truthy, "sample.py")[key][0]
        falsy_risk = prior._risk_profile(falsy, "sample.py")[key][0]
        self.assertEqual(truthy_risk, falsy_risk)

    def test_inner_suppressor_does_not_hide_failure_after_inner_exit(self) -> None:
        suppressing_inner = """
from standards_tools import Finding, ToolResult

class Outer:
    def __enter__(self):
        return self
    def __exit__(self, exc_type, exc, tb):
        return False

class Inner:
    def __enter__(self):
        return self
    def __exit__(self, exc_type, exc, tb):
        return True

def run(findings, callback):
    with Outer():
        with Inner():
            findings.append(Finding("PUBLIC_CODE", "message"))
        callback()
    return ToolResult.from_findings("validate", findings)
"""
        propagating_inner = suppressing_inner.replace(
            "class Inner:\n    def __enter__(self):\n        return self\n    def __exit__(self, exc_type, exc, tb):\n        return True",
            "class Inner:\n    def __enter__(self):\n        return self\n    def __exit__(self, exc_type, exc, tb):\n        return False",
        )
        key = ("sample.py", "run", "PUBLIC_CODE")
        suppressing_risk = prior._risk_profile(suppressing_inner, "sample.py")[key][0]
        propagating_risk = prior._risk_profile(propagating_inner, "sample.py")[key][0]
        # The callback occurs after Inner has already exited, so Inner's return
        # value must not alter the risk of that later failure.
        self.assertEqual(suppressing_risk, propagating_risk)


if __name__ == "__main__":
    unittest.main()
