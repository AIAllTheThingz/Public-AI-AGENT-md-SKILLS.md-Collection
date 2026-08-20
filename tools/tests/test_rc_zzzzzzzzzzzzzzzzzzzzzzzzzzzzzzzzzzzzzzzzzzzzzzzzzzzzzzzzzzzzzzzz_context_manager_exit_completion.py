from __future__ import annotations

import ast
import importlib
import unittest
from pathlib import Path

import rc_finding_code_contracts_base as base


# Final context-manager exit completion closure for PR #71.
#
# A finding emitted from a with/async-with body is not durable until every
# acquired manager has completed __exit__/__aexit__. The preceding
# post-emission risk layer already composes lexical suffixes and enclosing
# finally blocks; this overlay adds only the still-pending context-manager exit
# obligations while preserving the established entry-contract traversal.


def _load_overlay(suffix: str):
    matches = sorted(Path(__file__).parent.glob(f"test_rc_*{suffix}.py"))
    if len(matches) != 1:
        raise RuntimeError(f"expected exactly one RC overlay for {suffix!r}")
    return importlib.import_module(matches[0].stem)


prior = _load_overlay("_post_emission_conditional_completion")
context_entry = _load_overlay("_context_manager_entry_execution")

_SAFE = prior._SAFE
_UNKNOWN = prior._UNKNOWN
_RAISES = prior._RAISES


def _class_exit_method(node: ast.ClassDef, *, async_mode: bool):
    method_name = "__aexit__" if async_mode else "__exit__"
    return next(
        (
            statement
            for statement in node.body
            if isinstance(statement, (ast.FunctionDef, ast.AsyncFunctionDef))
            and statement.name == method_name
        ),
        None,
    )


def _context_exit_state(
    expression: ast.AST,
    definitions: dict[str, ast.AST],
    *,
    async_mode: bool,
    seen: set[str] | None = None,
) -> str:
    """Classify the exit protocol that follows an already-emitted finding.

    Same-module classes and simple same-module factories are resolved narrowly.
    Unknown/external managers remain conditional risk instead of being assumed
    safe. This deliberately does not execute or import candidate code.
    """

    if not isinstance(expression, ast.Call) or not isinstance(expression.func, ast.Name):
        return _UNKNOWN

    active = set() if seen is None else set(seen)
    name = expression.func.id
    if name in active:
        return _UNKNOWN
    active.add(name)

    definition = definitions.get(name)
    if isinstance(definition, ast.ClassDef):
        method = _class_exit_method(definition, async_mode=async_mode)
        if method is None:
            # An inherited protocol may exist, but it is not proven here.
            return _UNKNOWN

        outcome = context_entry._callable_direct_outcome(method)
        if outcome is context_entry._ENTRY_FAILS:
            return _RAISES
        if outcome is context_entry._ENTRY_SUCCEEDS:
            return _SAFE
        return _UNKNOWN

    if isinstance(definition, (ast.FunctionDef, ast.AsyncFunctionDef)):
        # A simple factory that directly returns a manager can be followed to
        # the concrete manager without freezing the factory's private names.
        if context_entry._callable_direct_outcome(definition) is context_entry._ENTRY_FAILS:
            return _RAISES
        returned = context_entry._returned_expression(definition)
        if returned is not None:
            return _context_exit_state(
                returned,
                definitions,
                async_mode=async_mode,
                seen=active,
            )

    return _UNKNOWN


def _context_exit_risk_score(
    visitor,
    obligations: tuple[tuple[ast.AST, bool], ...],
) -> int:
    definitions = getattr(visitor, "_context_manager_definitions", {})
    score = 0

    # Managers leave in reverse acquisition order. A guaranteed failure is
    # strictly worse than any finite number of conditional failure points.
    for expression, async_mode in reversed(obligations):
        state = _context_exit_state(
            expression,
            definitions,
            async_mode=async_mode,
        )
        if state == _UNKNOWN:
            score += 1
        elif state == _RAISES:
            return score + 1_000_000
    return score


def _with_pending_exits(
    visitor,
    obligations: tuple[tuple[ast.AST, bool], ...],
    callback,
) -> None:
    previous = getattr(visitor, "_pending_context_exits", ())
    visitor._pending_context_exits = previous + obligations
    try:
        callback()
    finally:
        visitor._pending_context_exits = previous


def _visit_with_with_exit_risk(
    visitor,
    node: ast.With | ast.AsyncWith,
    *,
    async_mode: bool,
) -> None:
    """Preserve the established entry traversal and add pending exit scope."""

    definitions = getattr(visitor, "_context_manager_definitions", {})
    prefix = "async-with" if async_mode else "with"
    acquired: list[ast.withitem] = []

    for index, item in enumerate(node.items):
        # A finding emitted while acquiring a later manager is already inside
        # every earlier manager, so those earlier exits are pending too.
        prior_exits = tuple(
            (acquired_item.context_expr, async_mode)
            for acquired_item in acquired
        )

        def visit_context_expression() -> None:
            if acquired:
                digest = context_entry._entry_digest(
                    acquired,
                    definitions,
                    async_mode=async_mode,
                )
                context_entry._literal_expression_context(
                    visitor,
                    context_entry._marker(
                        prefix,
                        f"item:{index}:requires-prior",
                        digest,
                    ),
                    context_entry._acquisition_dependency(acquired),
                    item.context_expr,
                )
            else:
                visitor.visit(item.context_expr)

        _with_pending_exits(visitor, prior_exits, visit_context_expression)

        acquired.append(item)
        if (
            context_entry._context_entry_outcome(
                item.context_expr,
                definitions,
                async_mode=async_mode,
            )
            is context_entry._ENTRY_FAILS
        ):
            return

    digest = context_entry._entry_digest(
        acquired,
        definitions,
        async_mode=async_mode,
    )
    body_exits = tuple(
        (item.context_expr, async_mode)
        for item in acquired
    )

    def visit_body() -> None:
        visitor._with_context(
            context_entry._marker(
                prefix,
                "body:requires-entry",
                digest,
            ),
            context_entry._acquisition_dependency(acquired),
            node.body,
        )

    _with_pending_exits(visitor, body_exits, visit_body)


_previous_visit_call = prior._PostEmissionConditionalRiskVisitor.visit_Call


def _visit_call_with_exit_risk(self, node: ast.Call) -> None:
    code = None
    before = 0
    key = None
    if isinstance(node.func, ast.Name) and node.func.id == "Finding":
        code = base.finding_code(node)
        if code is not None:
            key = (self.source_path, self.function, code)
            before = len(self.risks.get(key, []))

    _previous_visit_call(self, node)

    if code is None or key is None or len(self.risks.get(key, [])) <= before:
        return

    pending = getattr(self, "_pending_context_exits", ())
    if pending:
        self.risks[key][-1] += _context_exit_risk_score(self, pending)


prior._PostEmissionConditionalRiskVisitor.visit_With = (
    lambda self, node: _visit_with_with_exit_risk(
        self,
        node,
        async_mode=False,
    )
)
prior._PostEmissionConditionalRiskVisitor.visit_AsyncWith = (
    lambda self, node: _visit_with_with_exit_risk(
        self,
        node,
        async_mode=True,
    )
)
prior._PostEmissionConditionalRiskVisitor.visit_Call = _visit_call_with_exit_risk


class ReleaseCandidateContextManagerExitCompletionTests(unittest.TestCase):
    def test_sync_exit_raise_adds_post_emission_risk(self) -> None:
        safe = """
from standards_tools import Finding, ToolResult

class Manager:
    def __enter__(self):
        return self
    def __exit__(self, exc_type, exc, tb):
        return False

def run(findings):
    with Manager():
        findings.append(Finding("PUBLIC_CODE", "message"))
    return ToolResult.from_findings("validate", findings)
"""
        risky = """
from standards_tools import Finding, ToolResult

class Manager:
    def __enter__(self):
        return self
    def __exit__(self, exc_type, exc, tb):
        raise RuntimeError("exit failed")

def run(findings):
    with Manager():
        findings.append(Finding("PUBLIC_CODE", "message"))
    return ToolResult.from_findings("validate", findings)
"""
        key = ("sample.py", "run", "PUBLIC_CODE")
        safe_risk = prior._risk_profile(safe, "sample.py")[key][0]
        risky_score = prior._risk_profile(risky, "sample.py")[key][0]
        self.assertGreater(risky_score, safe_risk)

    def test_async_exit_raise_adds_post_emission_risk(self) -> None:
        safe = """
from standards_tools import Finding, ToolResult

class Manager:
    async def __aenter__(self):
        return self
    async def __aexit__(self, exc_type, exc, tb):
        return False

async def run(findings):
    async with Manager():
        findings.append(Finding("PUBLIC_CODE", "message"))
    return ToolResult.from_findings("validate", findings)
"""
        risky = """
from standards_tools import Finding, ToolResult

class Manager:
    async def __aenter__(self):
        return self
    async def __aexit__(self, exc_type, exc, tb):
        raise RuntimeError("exit failed")

async def run(findings):
    async with Manager():
        findings.append(Finding("PUBLIC_CODE", "message"))
    return ToolResult.from_findings("validate", findings)
"""
        key = ("sample.py", "run", "PUBLIC_CODE")
        safe_risk = prior._risk_profile(safe, "sample.py")[key][0]
        risky_score = prior._risk_profile(risky, "sample.py")[key][0]
        self.assertGreater(risky_score, safe_risk)

    def test_conditional_exit_failure_is_worse_than_safe_exit(self) -> None:
        safe = """
from standards_tools import Finding, ToolResult

class Manager:
    def __enter__(self):
        return self
    def __exit__(self, exc_type, exc, tb):
        return False

def run(findings):
    with Manager():
        findings.append(Finding("PUBLIC_CODE", "message"))
    return ToolResult.from_findings("validate", findings)
"""
        conditional = """
from standards_tools import Finding, ToolResult

class Manager:
    def __enter__(self):
        return self
    def __exit__(self, exc_type, exc, tb):
        callback()
        return False

def run(findings):
    with Manager():
        findings.append(Finding("PUBLIC_CODE", "message"))
    return ToolResult.from_findings("validate", findings)
"""
        key = ("sample.py", "run", "PUBLIC_CODE")
        safe_risk = prior._risk_profile(safe, "sample.py")[key][0]
        conditional_risk = prior._risk_profile(conditional, "sample.py")[key][0]
        self.assertGreater(conditional_risk, safe_risk)

    def test_simple_factory_exit_semantics_are_followed(self) -> None:
        safe = """
from standards_tools import Finding, ToolResult

class Manager:
    def __enter__(self):
        return self
    def __exit__(self, exc_type, exc, tb):
        return False

def manager():
    return Manager()

def run(findings):
    with manager():
        findings.append(Finding("PUBLIC_CODE", "message"))
    return ToolResult.from_findings("validate", findings)
"""
        risky = """
from standards_tools import Finding, ToolResult

class Manager:
    def __enter__(self):
        return self
    def __exit__(self, exc_type, exc, tb):
        raise RuntimeError("exit failed")

def manager():
    return Manager()

def run(findings):
    with manager():
        findings.append(Finding("PUBLIC_CODE", "message"))
    return ToolResult.from_findings("validate", findings)
"""
        key = ("sample.py", "run", "PUBLIC_CODE")
        safe_risk = prior._risk_profile(safe, "sample.py")[key][0]
        risky_score = prior._risk_profile(risky, "sample.py")[key][0]
        self.assertGreater(risky_score, safe_risk)

    def test_multiple_context_exit_risks_compose(self) -> None:
        one = """
from standards_tools import Finding, ToolResult

class Safe:
    def __enter__(self):
        return self
    def __exit__(self, exc_type, exc, tb):
        return False

class Risky:
    def __enter__(self):
        return self
    def __exit__(self, exc_type, exc, tb):
        callback()
        return False

def run(findings):
    with Safe(), Risky():
        findings.append(Finding("PUBLIC_CODE", "message"))
    return ToolResult.from_findings("validate", findings)
"""
        two = """
from standards_tools import Finding, ToolResult

class RiskyA:
    def __enter__(self):
        return self
    def __exit__(self, exc_type, exc, tb):
        callback()
        return False

class RiskyB:
    def __enter__(self):
        return self
    def __exit__(self, exc_type, exc, tb):
        cleanup()
        return False

def run(findings):
    with RiskyA(), RiskyB():
        findings.append(Finding("PUBLIC_CODE", "message"))
    return ToolResult.from_findings("validate", findings)
"""
        key = ("sample.py", "run", "PUBLIC_CODE")
        one_risk = prior._risk_profile(one, "sample.py")[key][0]
        two_risk = prior._risk_profile(two, "sample.py")[key][0]
        self.assertGreater(two_risk, one_risk)


if __name__ == "__main__":
    unittest.main()
