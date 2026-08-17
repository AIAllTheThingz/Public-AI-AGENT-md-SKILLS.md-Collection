from __future__ import annotations

import ast
import copy
import subprocess
import unittest
from collections import Counter
from pathlib import Path

from helpers import REPO_ROOT

CHECKPOINT_COMMIT = "83c73f3ab9a049ff2321d463164fcf98fb453a9c"


def git_output(*args: str) -> str:
    completed = subprocess.run(
        ["git", "-C", str(REPO_ROOT), *args],
        text=True,
        capture_output=True,
        check=False,
    )
    if completed.returncode != 0:
        raise AssertionError(completed.stderr.strip() or "git command failed")
    return completed.stdout


def git_source_at(commit: str, relative: str) -> str:
    return git_output("show", f"{commit}:{relative}")


def published_python_paths() -> list[str]:
    return sorted(
        path
        for path in git_output(
            "ls-tree", "-r", "--name-only", CHECKPOINT_COMMIT, "tools"
        ).splitlines()
        if path.endswith(".py")
        and not path.startswith("tools/tests/")
        and "/tests/" not in path
    )


def candidate_python_paths() -> list[Path]:
    return sorted(
        path
        for path in (REPO_ROOT / "tools").rglob("*.py")
        if "tests" not in path.relative_to(REPO_ROOT / "tools").parts
    )


def literal_finding_code(node: ast.Call) -> str | None:
    expression: ast.AST | None = node.args[0] if node.args else None
    if expression is None:
        for keyword in node.keywords:
            if keyword.arg == "code":
                expression = keyword.value
                break
    if isinstance(expression, ast.Constant) and isinstance(expression.value, str):
        return expression.value
    return None


def statement_always_terminates(node: ast.stmt) -> bool:
    if isinstance(node, (ast.Return, ast.Raise, ast.Break, ast.Continue)):
        return True
    if isinstance(node, ast.If) and node.orelse:
        return block_always_terminates(node.body) and block_always_terminates(node.orelse)
    return False


def block_always_terminates(statements: list[ast.stmt]) -> bool:
    for statement in statements:
        if statement_always_terminates(statement):
            return True
    return False


class ReachableFindingVisitor(ast.NodeVisitor):
    """Visit only statements that can be reached within a straight-line block."""

    def __init__(self, source_path: str) -> None:
        self.source_path = source_path
        self.function = "<module>"
        self.contracts: Counter[tuple[str, str, str]] = Counter()

    def _visit_block(self, statements: list[ast.stmt]) -> None:
        for statement in statements:
            self.visit(statement)
            if statement_always_terminates(statement):
                break

    def visit_Module(self, node: ast.Module) -> None:
        self._visit_block(node.body)

    def _visit_function(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> None:
        previous = self.function
        self.function = node.name
        try:
            self._visit_block(node.body)
        finally:
            self.function = previous

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self._visit_function(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self._visit_function(node)

    def visit_If(self, node: ast.If) -> None:
        self.visit(node.test)
        self._visit_block(node.body)
        self._visit_block(node.orelse)

    def visit_For(self, node: ast.For) -> None:
        self.visit(node.iter)
        self._visit_block(node.body)
        self._visit_block(node.orelse)

    def visit_AsyncFor(self, node: ast.AsyncFor) -> None:
        self.visit(node.iter)
        self._visit_block(node.body)
        self._visit_block(node.orelse)

    def visit_While(self, node: ast.While) -> None:
        self.visit(node.test)
        self._visit_block(node.body)
        self._visit_block(node.orelse)

    def visit_With(self, node: ast.With) -> None:
        for item in node.items:
            self.visit(item.context_expr)
        self._visit_block(node.body)

    def visit_AsyncWith(self, node: ast.AsyncWith) -> None:
        for item in node.items:
            self.visit(item.context_expr)
        self._visit_block(node.body)

    def visit_Try(self, node: ast.Try) -> None:
        self._visit_block(node.body)
        for handler in node.handlers:
            if handler.type is not None:
                self.visit(handler.type)
            self._visit_block(handler.body)
        self._visit_block(node.orelse)
        self._visit_block(node.finalbody)

    def visit_Match(self, node: ast.Match) -> None:
        self.visit(node.subject)
        for case in node.cases:
            if case.guard is not None:
                self.visit(case.guard)
            self._visit_block(case.body)

    def visit_Call(self, node: ast.Call) -> None:
        if isinstance(node.func, ast.Name) and node.func.id == "Finding":
            code = literal_finding_code(node)
            if code is not None:
                self.contracts[(self.source_path, self.function, code)] += 1
        self.generic_visit(node)


def reachable_literal_finding_contracts(
    text: str, source_path: str
) -> Counter[tuple[str, str, str]]:
    visitor = ReachableFindingVisitor(source_path)
    visitor.visit(ast.parse(text))
    return visitor.contracts


def published_contracts() -> Counter[tuple[str, str, str]]:
    result: Counter[tuple[str, str, str]] = Counter()
    for relative in published_python_paths():
        result.update(
            reachable_literal_finding_contracts(
                git_source_at(CHECKPOINT_COMMIT, relative), relative
            )
        )
    return result


def candidate_contracts() -> Counter[tuple[str, str, str]]:
    result: Counter[tuple[str, str, str]] = Counter()
    for path in candidate_python_paths():
        relative = path.relative_to(REPO_ROOT).as_posix()
        result.update(
            reachable_literal_finding_contracts(path.read_text(encoding="utf-8"), relative)
        )
    return result


class ReleaseCandidateFindingReachabilityTests(unittest.TestCase):
    def test_every_published_literal_finding_remains_reachable(self):
        published = published_contracts()
        candidate = candidate_contracts()
        self.assertGreater(sum(published.values()), 20)
        missing = {
            contract: count - candidate.get(contract, 0)
            for contract, count in published.items()
            if candidate.get(contract, 0) < count
        }
        self.assertEqual(
            missing,
            {},
            "published literal finding became unreachable or disappeared",
        )

    def test_unconditional_return_or_raise_suppression_is_detected(self):
        reachable = '''
def validate(value):
    Finding("PUBLIC_CODE", "visible")
'''
        returned = '''
def validate(value):
    return
    Finding("PUBLIC_CODE", "visible")
'''
        raised = '''
def validate(value):
    raise RuntimeError("stop")
    Finding("PUBLIC_CODE", "visible")
'''
        expected = reachable_literal_finding_contracts(reachable, "sample.py")
        self.assertEqual(expected[("sample.py", "validate", "PUBLIC_CODE")], 1)
        self.assertEqual(
            reachable_literal_finding_contracts(returned, "sample.py"), Counter()
        )
        self.assertEqual(
            reachable_literal_finding_contracts(raised, "sample.py"), Counter()
        )

    def test_both_terminating_if_branches_suppress_following_finding(self):
        source = '''
def validate(value):
    if value:
        return
    else:
        raise ValueError("stop")
    Finding("PUBLIC_CODE", "unreachable")
'''
        self.assertEqual(
            reachable_literal_finding_contracts(source, "sample.py"), Counter()
        )


if __name__ == "__main__":
    unittest.main()
