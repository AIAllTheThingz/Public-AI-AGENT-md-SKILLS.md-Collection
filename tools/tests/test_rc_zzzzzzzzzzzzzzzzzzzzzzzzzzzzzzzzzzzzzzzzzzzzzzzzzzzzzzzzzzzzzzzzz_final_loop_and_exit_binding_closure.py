from __future__ import annotations

import ast
import importlib
import unittest
from pathlib import Path

import rc_finding_code_contracts_base as base


# Final post-emission closure for PR #71.
#
# This layer composes three narrow corrections without reopening the established
# finding/sink contracts:
# * context-manager exits must bind Python's implicit exit arguments before a
#   same-module exit body can be treated as safe;
# * the already-reviewed validate-all compatibility-history wrapper must retain
#   its authenticated projection instead of acquiring a synthetic exit-risk
#   point solely because the post-emission model learned about context exits;
# * a finding emitted in one loop iteration is not durable until later
#   iterations/loop-else execution have completed.
#
# The implementation remains a side-car risk analysis. It does not rewrite
# production code or broaden the public compatibility surface.


def _load_overlay(suffix: str):
    matches = sorted(Path(__file__).parent.glob(f"test_rc_*{suffix}.py"))
    if len(matches) != 1:
        raise RuntimeError(f"expected exactly one RC overlay for {suffix!r}")
    return importlib.import_module(matches[0].stem)


exit_layer = _load_overlay("_context_manager_exit_completion")
prior = exit_layer.prior
execution = _load_overlay("_final_execution_completion_closure")
projection = _load_overlay("_iteration_match_and_projection_closure")
async_execution = _load_overlay("_async_execution_regressions")

_SAFE = prior._SAFE
_UNKNOWN = prior._UNKNOWN
_RAISES = prior._RAISES


# ---------------------------------------------------------------------------
# Context-exit argument binding and approved history-wrapper projection.
# ---------------------------------------------------------------------------

def _implicit_exit_binding_state(
    method: ast.FunctionDef | ast.AsyncFunctionDef,
) -> str:
    """Classify binding of the descriptor receiver plus three exit arguments."""

    # Decorators can replace descriptor/binding behavior. Preserve risk rather
    # than pretending the undecorated signature proves the call shape.
    if method.decorator_list:
        return _UNKNOWN

    # Model the unbound function signature with four positional values:
    # self + (exc_type, exc, tb). Python's descriptor supplies self and the
    # context-management protocol supplies the remaining three.
    synthetic = ast.Call(
        func=ast.Name(id=method.name, ctx=ast.Load()),
        args=[ast.Constant(value=None) for _ in range(4)],
        keywords=[],
    )
    return execution._call_binding_state(method, synthetic)


def _context_exit_state(
    expression: ast.AST,
    definitions: dict[str, ast.AST],
    *,
    async_mode: bool,
    seen: set[str] | None = None,
) -> str:
    """Classify a pending __exit__/__aexit__ including implicit call binding."""

    if not isinstance(expression, ast.Call) or not isinstance(expression.func, ast.Name):
        return _UNKNOWN

    active = set() if seen is None else set(seen)
    name = expression.func.id
    if name in active:
        return _UNKNOWN
    active.add(name)

    definition = definitions.get(name)
    if isinstance(definition, ast.ClassDef):
        method = exit_layer._class_exit_method(
            definition,
            async_mode=async_mode,
        )
        if method is None:
            return _UNKNOWN

        binding_state = _implicit_exit_binding_state(method)
        if binding_state != _SAFE:
            return binding_state

        # A synchronous __aexit__ can be valid only if it returns an awaitable.
        # The narrow static model does not prove that protocol, so do not mark it
        # safe merely because its direct body returns an inert value.
        if async_mode and not isinstance(method, ast.AsyncFunctionDef):
            return _UNKNOWN

        # Conversely, calling an async __exit__ from a synchronous with creates
        # a coroutine object without executing the body. Binding succeeded, but
        # the unusual protocol is not promoted to a proven-safe semantic case.
        if not async_mode and isinstance(method, ast.AsyncFunctionDef):
            return _UNKNOWN

        outcome = exit_layer.context_entry._callable_direct_outcome(method)
        if outcome is exit_layer.context_entry._ENTRY_FAILS:
            return _RAISES
        if outcome is exit_layer.context_entry._ENTRY_SUCCEEDS:
            return _SAFE
        return _UNKNOWN

    if isinstance(definition, (ast.FunctionDef, ast.AsyncFunctionDef)):
        if (
            exit_layer.context_entry._callable_direct_outcome(definition)
            is exit_layer.context_entry._ENTRY_FAILS
        ):
            return _RAISES
        returned = exit_layer.context_entry._returned_expression(definition)
        if returned is not None:
            return _context_exit_state(
                returned,
                definitions,
                async_mode=async_mode,
                seen=active,
            )

    return _UNKNOWN


# The earlier score helper resolves _context_exit_state through its module
# globals at runtime, so installing the stronger classifier here upgrades all
# existing exit-risk regressions without duplicating their traversal.
exit_layer._context_exit_state = _context_exit_state

_previous_context_exit_risk_score = exit_layer._context_exit_risk_score


def _approved_history_obligation(visitor, expression: ast.AST) -> bool:
    """Identify only the reviewed validate-all history wrapper obligation."""

    if not (
        visitor.source_path == projection._RUN_ALL_PATH
        and visitor.function == "run"
        and isinstance(expression, ast.Name)
        and projection._run_all_core_matches_published()
    ):
        return False

    # The risk profile operates on alpha-normalized AST, so the local `history`
    # name is intentionally renamed. Resolve its normalized local binding and
    # require the exact reviewed selector shape instead of depending on spelling.
    binding = getattr(visitor, "local_bindings", {}).get(expression.id)
    if not isinstance(binding, ast.IfExp):
        return False

    def call_name(node: ast.AST) -> str | None:
        return (
            node.func.id
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
            else None
        )

    return {
        call_name(binding.body),
        call_name(binding.orelse),
    } == {"compatibility_history", "nullcontext"}


def _context_exit_risk_score(
    visitor,
    obligations: tuple[tuple[ast.AST, bool], ...],
) -> int:
    # Run #520 exposed a synthetic +1 on VALIDATOR_FAILED / UNIT_TESTS_FAILED:
    # the unwrapped run() core is authenticated as exactly v0.10, while the
    # reviewed history scaffold is a candidate-only wrapper. Preserve the same
    # projection already used by the literal/sink contract, but remove only the
    # specific local `with history:` exit obligation. Any nested or newly added
    # context manager remains visible.
    projected = tuple(
        (expression, async_mode)
        for expression, async_mode in obligations
        if not _approved_history_obligation(visitor, expression)
    )
    return _previous_context_exit_risk_score(visitor, projected)


exit_layer._context_exit_risk_score = _context_exit_risk_score


# ---------------------------------------------------------------------------
# Later loop iterations after an emission.
# ---------------------------------------------------------------------------

class _EnclosingLoopCollector(ast.NodeVisitor):
    """Bind Finding calls in loop bodies to loops that may execute again."""

    def __init__(self) -> None:
        self._pending: list[ast.For | ast.AsyncFor | ast.While] = []
        self.by_call: dict[
            int,
            tuple[ast.For | ast.AsyncFor | ast.While, ...],
        ] = {}

    def _visit_body(
        self,
        node: ast.For | ast.AsyncFor | ast.While,
    ) -> None:
        self._pending.append(node)
        try:
            for statement in node.body:
                self.visit(statement)
        finally:
            self._pending.pop()

    def visit_For(self, node: ast.For) -> None:
        self.visit(node.iter)
        self._visit_body(node)
        for statement in node.orelse:
            self.visit(statement)

    def visit_AsyncFor(self, node: ast.AsyncFor) -> None:
        self.visit(node.iter)
        self._visit_body(node)
        for statement in node.orelse:
            self.visit(statement)

    def visit_While(self, node: ast.While) -> None:
        # The test can itself emit a finding. If it does, body execution and a
        # later test evaluation are still loop-continuation obligations.
        self._pending.append(node)
        try:
            self.visit(node.test)
        finally:
            self._pending.pop()
        self._visit_body(node)
        for statement in node.orelse:
            self.visit(statement)

    def _visit_deferred_function(
        self,
        node: ast.FunctionDef | ast.AsyncFunctionDef,
    ) -> None:
        # A nested function body executes when that function is invoked, not as
        # another iteration of the loop that happened to define it.
        previous = self._pending
        self._pending = []
        try:
            self.generic_visit(node)
        finally:
            self._pending = previous

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self._visit_deferred_function(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self._visit_deferred_function(node)

    def visit_Lambda(self, node: ast.Lambda) -> None:
        previous = self._pending
        self._pending = []
        try:
            self.generic_visit(node)
        finally:
            self._pending = previous

    def visit_Call(self, node: ast.Call) -> None:
        if isinstance(node.func, ast.Name) and node.func.id == "Finding":
            self.by_call[id(node)] = tuple(self._pending)
        self.generic_visit(node)


def _known_iterable_count(visitor, node: ast.AST) -> int | None:
    try:
        known = projection._known_iterable(visitor, node)
    except Exception:
        known = None
    if known is None:
        return None
    elements, _ordered = known
    return len(elements)


def _loop_continuation_state(
    visitor,
    loop: ast.For | ast.AsyncFor | ast.While,
) -> str:
    """Classify execution that can still happen after a body emission."""

    states: list[str] = []

    if isinstance(loop, ast.AsyncFor):
        # If another async item is requested, __anext__, target binding, and the
        # body are executable boundaries. A particular emitted occurrence is
        # not proof that a later request will succeed.
        states.append(_UNKNOWN)
        body_state = execution._block_exception_state(
            visitor,
            loop.body,
            parameterized=False,
        )
        if body_state != _SAFE:
            states.append(_UNKNOWN)
        else_state = execution._block_exception_state(
            visitor,
            loop.orelse,
            parameterized=False,
        )
        if else_state != _SAFE:
            states.append(_UNKNOWN)
        return execution._sequence_state(states) if states else _SAFE

    if isinstance(loop, ast.For):
        count = _known_iterable_count(visitor, loop.iter)

        # Unknown iteration count can request another item and execute arbitrary
        # iterator protocol code after a finding has already been appended.
        future_possible = count is None or count > 1
        if future_possible:
            if count is None:
                states.append(_UNKNOWN)

            target_state = projection._for_target_state(
                visitor,
                loop,
                parameterized=False,
            )
            if target_state != _SAFE:
                states.append(_UNKNOWN)

            body_state = execution._block_exception_state(
                visitor,
                loop.body,
                parameterized=False,
            )
            if body_state != _SAFE:
                # A whole-body guaranteed raise is still only conditional for a
                # specific emitted occurrence because that occurrence may have
                # happened on the final iteration or before a break.
                states.append(_UNKNOWN)

        # A loop-else executes after normal exhaustion. It is another
        # post-emission completion obligation even for a one-element iterable.
        else_state = execution._block_exception_state(
            visitor,
            loop.orelse,
            parameterized=False,
        )
        if else_state != _SAFE:
            states.append(_UNKNOWN)

        return execution._sequence_state(states) if states else _SAFE

    assert isinstance(loop, ast.While)
    test_state = execution._expression_state(
        visitor,
        loop.test,
        parameterized=False,
    )
    truth = execution._static_truth(
        visitor,
        loop.test,
        parameterized=False,
    )

    # A finding from the body proves the loop entered at least once. Unless the
    # condition is statically false (which would make the body unreachable),
    # another condition/body cycle can occur. Preserve only whether that future
    # cycle may fail, not private loop syntax.
    if truth is not False:
        if test_state != _SAFE:
            states.append(_UNKNOWN)
        body_state = execution._block_exception_state(
            visitor,
            loop.body,
            parameterized=False,
        )
        if body_state != _SAFE:
            states.append(_UNKNOWN)

    else_state = execution._block_exception_state(
        visitor,
        loop.orelse,
        parameterized=False,
    )
    if else_state != _SAFE:
        states.append(_UNKNOWN)

    return execution._sequence_state(states) if states else _SAFE


def _loop_continuation_risk_score(
    visitor,
    loops: tuple[ast.For | ast.AsyncFor | ast.While, ...],
) -> int:
    score = 0
    for loop in loops:
        if _loop_continuation_state(visitor, loop) != _SAFE:
            # Continuation is potential, not guaranteed for a particular
            # emitted occurrence, so one semantic risk point is sufficient.
            score += 1
    return score


_previous_visit_call = prior._PostEmissionConditionalRiskVisitor.visit_Call


def _visit_call_with_loop_continuation(self, node: ast.Call) -> None:
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

    loops = getattr(self, "_enclosing_post_emission_loops", {}).get(id(node), ())
    if loops:
        self.risks[key][-1] += _loop_continuation_risk_score(self, loops)


prior._PostEmissionConditionalRiskVisitor.visit_Call = (
    _visit_call_with_loop_continuation
)


def _risk_profile(
    text: str,
    source_path: str,
) -> dict[tuple[str, str, str], list[int]]:
    tree = base.normalize_bound_names(ast.parse(text))

    finally_collector = prior._EnclosingFinallyCollector()
    finally_collector.visit(tree)

    loop_collector = _EnclosingLoopCollector()
    loop_collector.visit(tree)

    visitor = prior._PostEmissionConditionalRiskVisitor(
        base.module_semantic_bindings(tree),
        source_path,
        finally_collector.by_call,
    )
    visitor._enclosing_post_emission_loops = loop_collector.by_call
    visitor.visit(tree)
    return {key: list(values) for key, values in visitor.risks.items()}


# Aggregate/published/candidate profile helpers resolve this name through module
# globals at runtime, as do the earlier context-exit tests.
prior._risk_profile = _risk_profile


# ---------------------------------------------------------------------------
# Correct the async regression identity from run #520.
# ---------------------------------------------------------------------------

def _test_async_exit_raise_adds_post_emission_risk(self) -> None:
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
    key = (
        "sample.py",
        f"run{async_execution.COROUTINE_SUFFIX}",
        "PUBLIC_CODE",
    )
    safe_risk = prior._risk_profile(safe, "sample.py")[key][0]
    risky_score = prior._risk_profile(risky, "sample.py")[key][0]
    self.assertGreater(risky_score, safe_risk)


exit_layer.ReleaseCandidateContextManagerExitCompletionTests.test_async_exit_raise_adds_post_emission_risk = (
    _test_async_exit_raise_adds_post_emission_risk
)


# ---------------------------------------------------------------------------
# Permanent regressions for the two fresh review findings.
# ---------------------------------------------------------------------------

class ReleaseCandidateFinalLoopAndExitBindingClosureTests(unittest.TestCase):
    def test_invalid_sync_exit_signature_adds_post_emission_risk(self) -> None:
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
        invalid = """
from standards_tools import Finding, ToolResult

class Manager:
    def __enter__(self):
        return self
    def __exit__(self):
        return False

def run(findings):
    with Manager():
        findings.append(Finding("PUBLIC_CODE", "message"))
    return ToolResult.from_findings("validate", findings)
"""
        key = ("sample.py", "run", "PUBLIC_CODE")
        safe_risk = prior._risk_profile(safe, "sample.py")[key][0]
        invalid_risk = prior._risk_profile(invalid, "sample.py")[key][0]
        self.assertGreater(invalid_risk, safe_risk)

    def test_invalid_async_exit_signature_adds_post_emission_risk(self) -> None:
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
        invalid = """
from standards_tools import Finding, ToolResult

class Manager:
    async def __aenter__(self):
        return self
    async def __aexit__(self):
        return False

async def run(findings):
    async with Manager():
        findings.append(Finding("PUBLIC_CODE", "message"))
    return ToolResult.from_findings("validate", findings)
"""
        key = (
            "sample.py",
            f"run{async_execution.COROUTINE_SUFFIX}",
            "PUBLIC_CODE",
        )
        safe_risk = prior._risk_profile(safe, "sample.py")[key][0]
        invalid_risk = prior._risk_profile(invalid, "sample.py")[key][0]
        self.assertGreater(invalid_risk, safe_risk)

    def test_later_for_iteration_failure_adds_post_emission_risk(self) -> None:
        safe = """
from standards_tools import Finding, ToolResult

def run(findings):
    for item in [0, 1]:
        if item == 0:
            findings.append(Finding("PUBLIC_CODE", "message"))
        else:
            pass
    return ToolResult.from_findings("validate", findings)
"""
        risky = """
from standards_tools import Finding, ToolResult

def run(findings, callback):
    for item in [0, 1]:
        if item == 0:
            findings.append(Finding("PUBLIC_CODE", "message"))
        else:
            callback()
    return ToolResult.from_findings("validate", findings)
"""
        key = ("sample.py", "run", "PUBLIC_CODE")
        safe_risk = prior._risk_profile(safe, "sample.py")[key][0]
        risky_score = prior._risk_profile(risky, "sample.py")[key][0]
        self.assertGreater(risky_score, safe_risk)

    def test_later_while_iteration_failure_adds_post_emission_risk(self) -> None:
        safe = """
from standards_tools import Finding

def run(findings, flag):
    while flag:
        pass
        findings.append(Finding("PUBLIC_CODE", "message"))
"""
        risky = """
from standards_tools import Finding

def run(findings, flag, callback):
    while flag:
        callback()
        findings.append(Finding("PUBLIC_CODE", "message"))
"""
        key = ("sample.py", "run", "PUBLIC_CODE")
        safe_risk = prior._risk_profile(safe, "sample.py")[key][0]
        risky_score = prior._risk_profile(risky, "sample.py")[key][0]
        self.assertGreater(risky_score, safe_risk)

    def test_single_static_for_iteration_does_not_add_continuation_risk(self) -> None:
        direct = """
from standards_tools import Finding

def run(findings):
    findings.append(Finding("PUBLIC_CODE", "message"))
"""
        looped = """
from standards_tools import Finding

def run(findings):
    for item in [0]:
        findings.append(Finding("PUBLIC_CODE", "message"))
"""
        key = ("sample.py", "run", "PUBLIC_CODE")
        direct_risk = prior._risk_profile(direct, "sample.py")[key][0]
        looped_risk = prior._risk_profile(looped, "sample.py")[key][0]
        self.assertEqual(looped_risk, direct_risk)


if __name__ == "__main__":
    unittest.main()
