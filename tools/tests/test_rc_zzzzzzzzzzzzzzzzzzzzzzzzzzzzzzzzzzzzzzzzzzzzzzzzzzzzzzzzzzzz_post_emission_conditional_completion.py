from __future__ import annotations

import ast
import importlib
import unittest
from collections import defaultdict
from pathlib import Path

import rc_finding_code_contracts_base as base


# Final post-emission completion-risk closure for PR #71.
#
# A published Finding can be constructed and appended yet still disappear at the
# tool boundary if later execution raises. The earlier completion gate protected
# guaranteed failure; this layer also preserves conditional failure points. It
# deliberately reuses the final execution-risk classifier so a candidate may
# become safer, but it may not add new potentially failing execution after a
# published emission.


def _load_overlay(suffix: str):
    matches = sorted(Path(__file__).parent.glob(f"test_rc_*{suffix}.py"))
    if len(matches) != 1:
        raise RuntimeError(f"expected exactly one RC overlay for {suffix!r}")
    return importlib.import_module(matches[0].stem)


execution = _load_overlay("_final_execution_completion_closure")

_SAFE = execution._SAFE
_UNKNOWN = execution._UNKNOWN
_RAISES = execution._RAISES


def _statement_risk_state(visitor, statement: ast.stmt) -> str:
    """Classify execution after an emitted finding.

    Return-value evaluation happens before normal function completion, so it is
    classified explicitly. Other statements use the final composed execution
    prerequisite model, which already understands dynamic calls, assignments,
    compound statements, target binding, iteration, handler types, with-target
    binding, and other reviewed execution semantics.
    """

    if isinstance(statement, ast.Return):
        if statement.value is None:
            return _SAFE
        return execution._expression_state(
            visitor,
            statement.value,
            parameterized=False,
        )

    if isinstance(statement, ast.Raise):
        return _RAISES

    return execution._statement_exception_state(
        visitor,
        statement,
        parameterized=False,
    )


def _suffix_risk_score(visitor, statements: list[ast.stmt]) -> int:
    """Return a monotonic score for post-emission failure opportunities."""

    score = 0
    for statement in statements:
        state = _statement_risk_state(visitor, statement)
        if state == _UNKNOWN:
            score += 1
        elif state == _RAISES:
            # Guaranteed abnormal completion is strictly worse than any finite
            # number of conditional failure points and terminates the suffix.
            return score + 1_000_000

        if isinstance(statement, (ast.Return, ast.Raise, ast.Break, ast.Continue)):
            break

    return score


class _PostEmissionConditionalRiskVisitor(base.FindingSignatureVisitor):
    def __init__(self, definitions: dict[str, ast.AST], source_path: str) -> None:
        super().__init__(definitions, source_path)
        self._post_risk_score = 0
        self.risks: defaultdict[tuple[str, str, str], list[int]] = defaultdict(list)

    def _visit_block(self, statements: list[ast.stmt]) -> None:
        outer_risk = self._post_risk_score
        for index, statement in enumerate(statements):
            previous = self._post_risk_score
            self._post_risk_score = outer_risk + _suffix_risk_score(
                self,
                statements[index + 1 :],
            )
            try:
                self.visit(statement)
            finally:
                self._post_risk_score = previous

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        previous = self._post_risk_score
        self._post_risk_score = 0
        try:
            super().visit_FunctionDef(node)
        finally:
            self._post_risk_score = previous

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        previous = self._post_risk_score
        self._post_risk_score = 0
        try:
            super().visit_AsyncFunctionDef(node)
        finally:
            self._post_risk_score = previous

    def visit_Call(self, node: ast.Call) -> None:
        code = None
        before = 0
        if isinstance(node.func, ast.Name) and node.func.id == "Finding":
            code = base.finding_code(node)
            if code is not None:
                before = len(self.signatures.get(code, []))

        super().visit_Call(node)

        if code is None or len(self.signatures.get(code, [])) <= before:
            return

        key = (self.source_path, self.function, code)
        self.risks[key].append(self._post_risk_score)


def _risk_profile(text: str, source_path: str) -> dict[tuple[str, str, str], list[int]]:
    tree = base.normalize_bound_names(ast.parse(text))
    visitor = _PostEmissionConditionalRiskVisitor(
        base.module_semantic_bindings(tree),
        source_path,
    )
    visitor.visit(tree)
    return {key: list(values) for key, values in visitor.risks.items()}


def _aggregate_risk_profile(
    sources: list[tuple[str, str]],
) -> dict[tuple[str, str, str], list[int]]:
    result: defaultdict[tuple[str, str, str], list[int]] = defaultdict(list)
    for source_path, text in sources:
        for key, values in _risk_profile(text, source_path).items():
            result[key].extend(values)
    return dict(result)


def _published_risk_profile() -> dict[tuple[str, str, str], list[int]]:
    return _aggregate_risk_profile(
        [
            (relative, base.git_source_at(base.CHECKPOINT_COMMIT, relative))
            for relative in base.published_python_paths()
        ]
    )


def _candidate_risk_profile() -> dict[tuple[str, str, str], list[int]]:
    return _aggregate_risk_profile(
        [
            (
                path.relative_to(base.REPO_ROOT).as_posix(),
                path.read_text(encoding="utf-8"),
            )
            for path in base.candidate_python_paths()
        ]
    )


class ReleaseCandidatePostEmissionConditionalCompletionTests(unittest.TestCase):
    def test_published_findings_do_not_gain_post_emission_failure_risk(self) -> None:
        published = _published_risk_profile()
        candidate = _candidate_risk_profile()
        self.assertGreater(len(published), 20)

        for key, expected_values in published.items():
            with self.subTest(source=key[0], function=key[1], code=key[2]):
                expected = sorted(expected_values)
                actual = sorted(candidate.get(key, []))
                self.assertGreaterEqual(
                    len(actual),
                    len(expected),
                    "published finding occurrence disappeared from completion-risk contract",
                )

                # Match the safest candidate occurrences first. Removing risk is
                # compatible; adding risk to a published occurrence is not.
                for candidate_risk, published_risk in zip(
                    actual[: len(expected)],
                    expected,
                ):
                    self.assertLessEqual(
                        candidate_risk,
                        published_risk,
                        "published finding gained post-emission failure risk",
                    )

    def test_dynamic_callback_after_emission_adds_failure_risk(self) -> None:
        direct = '''
from standards_tools import Finding, ToolResult

def run(findings):
    findings.append(Finding("PUBLIC_CODE", "message"))
    return ToolResult.from_findings("validate", findings)
'''
        risky = '''
from standards_tools import Finding, ToolResult

def run(findings, callback):
    findings.append(Finding("PUBLIC_CODE", "message"))
    callback()
    return ToolResult.from_findings("validate", findings)
'''
        key = ("sample.py", "run", "PUBLIC_CODE")
        direct_risk = _risk_profile(direct, "sample.py")[key][0]
        risky_score = _risk_profile(risky, "sample.py")[key][0]
        self.assertGreater(risky_score, direct_risk)

    def test_harmless_same_module_helper_does_not_add_failure_risk(self) -> None:
        direct = '''
from standards_tools import Finding, ToolResult

def run(findings):
    findings.append(Finding("PUBLIC_CODE", "message"))
    return ToolResult.from_findings("validate", findings)
'''
        harmless = '''
from standards_tools import Finding, ToolResult

def helper():
    return 1

def run(findings):
    findings.append(Finding("PUBLIC_CODE", "message"))
    helper()
    return ToolResult.from_findings("validate", findings)
'''
        key = ("sample.py", "run", "PUBLIC_CODE")
        direct_risk = _risk_profile(direct, "sample.py")[key][0]
        harmless_risk = _risk_profile(harmless, "sample.py")[key][0]
        self.assertEqual(harmless_risk, direct_risk)

    def test_dynamic_return_expression_adds_failure_risk(self) -> None:
        direct = '''
from standards_tools import Finding

def run(findings):
    findings.append(Finding("PUBLIC_CODE", "message"))
    return None
'''
        risky = '''
from standards_tools import Finding

def run(findings, callback):
    findings.append(Finding("PUBLIC_CODE", "message"))
    return callback()
'''
        key = ("sample.py", "run", "PUBLIC_CODE")
        direct_risk = _risk_profile(direct, "sample.py")[key][0]
        risky_score = _risk_profile(risky, "sample.py")[key][0]
        self.assertGreater(risky_score, direct_risk)

    def test_guaranteed_raising_return_is_worse_than_conditional_call(self) -> None:
        conditional = '''
from standards_tools import Finding

def run(findings, callback):
    findings.append(Finding("PUBLIC_CODE", "message"))
    callback()
    return None
'''
        guaranteed = '''
from standards_tools import Finding

def run(findings):
    findings.append(Finding("PUBLIC_CODE", "message"))
    return 1 / 0
'''
        key = ("sample.py", "run", "PUBLIC_CODE")
        conditional_risk = _risk_profile(conditional, "sample.py")[key][0]
        guaranteed_risk = _risk_profile(guaranteed, "sample.py")[key][0]
        self.assertGreater(guaranteed_risk, conditional_risk)


if __name__ == "__main__":
    unittest.main()
