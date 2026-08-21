from __future__ import annotations

import ast
import importlib
import unittest
from pathlib import Path


# Final refinement of loop-continuation risk for PR #71.
#
# A single UNKNOWN state for an entire compound statement loses information:
# `if item == 0: Finding(...); else: pass` and the same branch with
# `else: callback()` can both flatten to UNKNOWN because the comparison itself
# is dynamic. Preserve branch-local failure opportunities so a newly failing
# later iteration cannot hide behind an already-existing generic risk point.


def _load_overlay(suffix: str):
    matches = sorted(Path(__file__).parent.glob(f"test_rc_*{suffix}.py"))
    if len(matches) != 1:
        raise RuntimeError(f"expected exactly one RC overlay for {suffix!r}")
    return importlib.import_module(matches[0].stem)


loop_layer = _load_overlay("_final_loop_and_exit_binding_closure")
prior = loop_layer.prior
execution = loop_layer.execution
projection = loop_layer.projection

_SAFE = prior._SAFE


def _risk_point(state: str) -> int:
    return 0 if state == _SAFE else 1


def _future_expression_risk_score(visitor, node: ast.AST) -> int:
    return _risk_point(
        execution._expression_state(
            visitor,
            node,
            parameterized=False,
        )
    )


def _future_block_risk_score(visitor, statements: list[ast.stmt]) -> int:
    score = 0
    for statement in statements:
        score += _future_statement_risk_score(visitor, statement)
        if isinstance(statement, (ast.Return, ast.Raise, ast.Break, ast.Continue)):
            break
    return score


def _future_statement_risk_score(visitor, statement: ast.stmt) -> int:
    if isinstance(statement, ast.If):
        score = _future_expression_risk_score(visitor, statement.test)
        truth = execution._static_truth(
            visitor,
            statement.test,
            parameterized=False,
        )
        if truth is True:
            return score + _future_block_risk_score(visitor, statement.body)
        if truth is False:
            return score + _future_block_risk_score(visitor, statement.orelse)
        return score + max(
            _future_block_risk_score(visitor, statement.body),
            _future_block_risk_score(visitor, statement.orelse),
        )

    if isinstance(statement, (ast.For, ast.AsyncFor)):
        score = _risk_point(
            execution._statement_exception_state(
                visitor,
                statement,
                parameterized=False,
            )
        )
        score += _future_block_risk_score(visitor, statement.body)
        score += _future_block_risk_score(visitor, statement.orelse)
        return score

    if isinstance(statement, ast.While):
        score = _future_expression_risk_score(visitor, statement.test)
        score += _future_block_risk_score(visitor, statement.body)
        score += _future_block_risk_score(visitor, statement.orelse)
        return score

    try_types = (ast.Try,)
    if hasattr(ast, "TryStar"):
        try_types = (*try_types, ast.TryStar)
    if isinstance(statement, try_types):
        score = _risk_point(
            execution._statement_exception_state(
                visitor,
                statement,
                parameterized=False,
            )
        )
        alternatives = [
            _future_block_risk_score(visitor, statement.body),
            _future_block_risk_score(visitor, statement.orelse),
            *(
                _future_block_risk_score(visitor, handler.body)
                for handler in statement.handlers
            ),
        ]
        score += max(alternatives, default=0)
        score += _future_block_risk_score(visitor, statement.finalbody)
        return score

    if isinstance(statement, (ast.With, ast.AsyncWith)):
        score = _risk_point(
            execution._statement_exception_state(
                visitor,
                statement,
                parameterized=False,
            )
        )
        score += _future_block_risk_score(visitor, statement.body)
        return score

    if isinstance(statement, ast.Match):
        score = _risk_point(
            execution._statement_exception_state(
                visitor,
                statement,
                parameterized=False,
            )
        )
        score += max(
            (
                _future_block_risk_score(visitor, case.body)
                for case in statement.cases
            ),
            default=0,
        )
        return score

    return _risk_point(prior._statement_risk_state(visitor, statement))


def _loop_continuation_risk_score(
    visitor,
    loops: tuple[ast.For | ast.AsyncFor | ast.While, ...],
) -> int:
    total = 0
    for loop in loops:
        if isinstance(loop, ast.AsyncFor):
            total += 1
            total += _future_block_risk_score(visitor, loop.body)
            total += _future_block_risk_score(visitor, loop.orelse)
            continue

        if isinstance(loop, ast.For):
            count = loop_layer._known_iterable_count(visitor, loop.iter)
            future_possible = count is None or count > 1
            if future_possible:
                if count is None:
                    total += 1
                total += _risk_point(
                    projection._for_target_state(
                        visitor,
                        loop,
                        parameterized=False,
                    )
                )
                total += _future_block_risk_score(visitor, loop.body)
            total += _future_block_risk_score(visitor, loop.orelse)
            continue

        assert isinstance(loop, ast.While)
        truth = execution._static_truth(
            visitor,
            loop.test,
            parameterized=False,
        )
        if truth is not False:
            total += _future_expression_risk_score(visitor, loop.test)
            total += _future_block_risk_score(visitor, loop.body)
        total += _future_block_risk_score(visitor, loop.orelse)

    return total


# The installed loop visitor resolves this helper from loop_layer globals at
# test/runtime, so the refinement composes without replacing its side-car map.
loop_layer._loop_continuation_risk_score = _loop_continuation_risk_score


class ReleaseCandidateCompositionalLoopContinuationRiskTests(unittest.TestCase):
    def test_dynamic_if_risk_does_not_hide_later_callback(self) -> None:
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


if __name__ == "__main__":
    unittest.main()
