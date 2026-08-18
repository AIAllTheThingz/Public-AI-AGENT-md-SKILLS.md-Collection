from __future__ import annotations

import ast
import unittest
from collections import Counter

import rc_finding_code_contracts_base as base
import rc_reachability_semantics as reachability
import test_rc_zzzzzzzzzzzzzzzzzz_literal_finding_multiplicity as _multiplicity  # noqa: F401


# A Finding is not observably emitted merely because its constructor/append runs.
# The surrounding finding-producing function must still be able to complete and
# return control to the tool boundary. A guaranteed exception after an append is
# converted by execute_tool into INTERNAL_ERROR and replaces the public finding.
# Preserve that completion property without freezing harmless trailing statements.


def _call_is_explicit_process_exit(node: ast.Call) -> bool:
    function = node.func
    return (
        isinstance(function, ast.Attribute)
        and isinstance(function.value, ast.Name)
        and (
            (function.value.id == "sys" and function.attr == "exit")
            or (function.value.id == "os" and function.attr == "_exit")
        )
    )


def _expression_guaranteed_abnormal(
    node: ast.AST, constants: dict[str, object]
) -> bool:
    if isinstance(node, ast.Call) and _call_is_explicit_process_exit(node):
        return True
    if isinstance(node, ast.BinOp) and isinstance(
        node.op, (ast.Div, ast.FloorDiv, ast.Mod)
    ):
        denominator = reachability.static_value(node.right, constants)
        if denominator is not reachability.UNKNOWN and denominator == 0:
            return True
    return False


def _sequence_can_complete_normally(
    statements: list[ast.stmt],
    outer_can_complete_normally: bool,
    constants: dict[str, object] | None = None,
) -> bool:
    """Conservatively answer whether an execution path can return normally.

    False is returned only when the suffix is statically forced into abnormal
    termination. Unknown control flow stays True, preventing this compatibility
    gate from freezing ordinary implementation choices.
    """

    state = dict(constants or {})
    for index, statement in enumerate(statements):
        rest = statements[index + 1 :]

        if isinstance(statement, ast.Return):
            return True
        if isinstance(statement, ast.Raise):
            return False
        if isinstance(statement, ast.Assert):
            truth = reachability.static_truth(statement.test, state)
            if truth is False:
                return False
            continue
        if isinstance(statement, ast.Expr) and _expression_guaranteed_abnormal(
            statement.value, state
        ):
            return False

        if isinstance(statement, ast.If):
            truth = reachability.static_truth(statement.test, state)
            if truth is True:
                return _sequence_can_complete_normally(
                    [*statement.body, *rest], outer_can_complete_normally, state
                )
            if truth is False:
                return _sequence_can_complete_normally(
                    [*statement.orelse, *rest], outer_can_complete_normally, state
                )

            true_path = _sequence_can_complete_normally(
                [*statement.body, *rest], outer_can_complete_normally, state
            )
            false_path = _sequence_can_complete_normally(
                [*statement.orelse, *rest], outer_can_complete_normally, state
            )
            return true_path or false_path

        # A finally block that is itself guaranteed to terminate abnormally
        # overrides every pending return/exception from the try regions.
        if isinstance(statement, ast.Try) or (
            hasattr(ast, "TryStar") and isinstance(statement, ast.TryStar)
        ):
            if statement.finalbody and not _sequence_can_complete_normally(
                statement.finalbody, True, state
            ):
                return False
            # Otherwise remain conservative about exceptions and handlers and
            # continue to the statements following the try.

        reachability.update_known_constants(statement, state)

    return outer_can_complete_normally


class _PostEmissionCompletionVisitor(base.FindingSignatureVisitor):
    def __init__(self, definitions: dict[str, ast.AST], source_path: str) -> None:
        super().__init__(definitions, source_path)
        self._post_can_complete_normally = True
        self.normal_completions: Counter[tuple[str, str, str]] = Counter()
        self.abnormal_completions: Counter[tuple[str, str, str]] = Counter()

    def _visit_block(self, statements: list[ast.stmt]) -> None:
        outer = self._post_can_complete_normally
        for index, statement in enumerate(statements):
            previous = self._post_can_complete_normally
            self._post_can_complete_normally = _sequence_can_complete_normally(
                statements[index + 1 :],
                outer,
            )
            try:
                self.visit(statement)
            finally:
                self._post_can_complete_normally = previous

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        previous = self._post_can_complete_normally
        self._post_can_complete_normally = True
        try:
            super().visit_FunctionDef(node)
        finally:
            self._post_can_complete_normally = previous

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        previous = self._post_can_complete_normally
        self._post_can_complete_normally = True
        try:
            super().visit_AsyncFunctionDef(node)
        finally:
            self._post_can_complete_normally = previous

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
        if self._post_can_complete_normally:
            self.normal_completions[key] += 1
        else:
            self.abnormal_completions[key] += 1


def _completion_counts(text: str, source_path: str) -> tuple[Counter, Counter]:
    tree = base.normalize_bound_names(ast.parse(text))
    visitor = _PostEmissionCompletionVisitor(
        base.module_semantic_bindings(tree), source_path
    )
    visitor.visit(tree)
    return visitor.normal_completions, visitor.abnormal_completions


def _aggregate_normal_completions(
    sources: list[tuple[str, str]],
) -> Counter[tuple[str, str, str]]:
    result: Counter[tuple[str, str, str]] = Counter()
    for source_path, text in sources:
        normal, _abnormal = _completion_counts(text, source_path)
        result.update(normal)
    return result


def _published_normal_completions() -> Counter[tuple[str, str, str]]:
    return _aggregate_normal_completions(
        [
            (relative, base.git_source_at(base.CHECKPOINT_COMMIT, relative))
            for relative in base.published_python_paths()
        ]
    )


def _candidate_normal_completions() -> Counter[tuple[str, str, str]]:
    return _aggregate_normal_completions(
        [
            (
                path.relative_to(base.REPO_ROOT).as_posix(),
                path.read_text(encoding="utf-8"),
            )
            for path in base.candidate_python_paths()
        ]
    )


class ReleaseCandidatePostEmissionCompletionTests(unittest.TestCase):
    def test_published_literal_findings_can_still_complete_normally(self) -> None:
        published = _published_normal_completions()
        candidate = _candidate_normal_completions()
        self.assertGreater(len(published), 20)

        for key, count in published.items():
            with self.subTest(source=key[0], function=key[1], code=key[2]):
                self.assertGreaterEqual(
                    candidate[key],
                    count,
                    "published finding can no longer reach normal tool completion",
                )

    def test_trailing_raise_after_emission_is_abnormal(self) -> None:
        direct = '''
from standards_tools import Finding

def run(findings):
    findings.append(Finding("PUBLIC_CODE", "message"))
'''
        broken = '''
from standards_tools import Finding

def run(findings):
    findings.append(Finding("PUBLIC_CODE", "message"))
    raise RuntimeError("after emission")
'''
        direct_normal, direct_abnormal = _completion_counts(direct, "sample.py")
        broken_normal, broken_abnormal = _completion_counts(broken, "sample.py")
        key = ("sample.py", "run", "PUBLIC_CODE")

        self.assertEqual(direct_normal[key], 1)
        self.assertEqual(direct_abnormal[key], 0)
        self.assertEqual(broken_normal[key], 0)
        self.assertEqual(broken_abnormal[key], 1)

    def test_normal_return_after_emission_remains_compatible(self) -> None:
        source = '''
from standards_tools import Finding

def run(findings):
    findings.append(Finding("PUBLIC_CODE", "message"))
    return None
'''
        normal, abnormal = _completion_counts(source, "sample.py")
        key = ("sample.py", "run", "PUBLIC_CODE")
        self.assertEqual(normal[key], 1)
        self.assertEqual(abnormal[key], 0)

    def test_conditional_raise_keeps_a_normal_completion_path(self) -> None:
        source = '''
from standards_tools import Finding

def run(findings, fail):
    findings.append(Finding("PUBLIC_CODE", "message"))
    if fail:
        raise RuntimeError("conditional")
'''
        normal, abnormal = _completion_counts(source, "sample.py")
        key = ("sample.py", "run", "PUBLIC_CODE")
        self.assertEqual(normal[key], 1)
        self.assertEqual(abnormal[key], 0)


if __name__ == "__main__":
    unittest.main()
