from __future__ import annotations

import ast
import subprocess
import unittest
from collections import Counter
from pathlib import Path
from typing import Any

from helpers import REPO_ROOT

CHECKPOINT_COMMIT = "83c73f3ab9a049ff2321d463164fcf98fb453a9c"
UNKNOWN = object()


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


def static_value(node: ast.AST, constants: dict[str, Any]) -> object:
    if isinstance(node, ast.Constant):
        return node.value
    if isinstance(node, ast.Name):
        return constants.get(node.id, UNKNOWN)
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.Not):
        value = static_value(node.operand, constants)
        return UNKNOWN if value is UNKNOWN else not bool(value)
    if isinstance(node, ast.BoolOp):
        values = [static_value(item, constants) for item in node.values]
        if isinstance(node.op, ast.And):
            if any(value is not UNKNOWN and not bool(value) for value in values):
                return False
            if all(value is not UNKNOWN for value in values):
                return all(bool(value) for value in values)
        if isinstance(node.op, ast.Or):
            if any(value is not UNKNOWN and bool(value) for value in values):
                return True
            if all(value is not UNKNOWN for value in values):
                return any(bool(value) for value in values)
        return UNKNOWN
    if (
        isinstance(node, ast.Compare)
        and len(node.ops) == 1
        and len(node.comparators) == 1
    ):
        left = static_value(node.left, constants)
        right = static_value(node.comparators[0], constants)
        if left is UNKNOWN or right is UNKNOWN:
            return UNKNOWN
        operator = node.ops[0]
        if isinstance(operator, ast.Eq):
            return left == right
        if isinstance(operator, ast.NotEq):
            return left != right
        if isinstance(operator, ast.Is):
            return left is right
        if isinstance(operator, ast.IsNot):
            return left is not right
    return UNKNOWN


def static_truth(node: ast.AST, constants: dict[str, Any]) -> bool | None:
    value = static_value(node, constants)
    return None if value is UNKNOWN else bool(value)


def update_known_constants(statement: ast.stmt, constants: dict[str, Any]) -> None:
    if isinstance(statement, ast.Assign):
        value = static_value(statement.value, constants)
        for target in statement.targets:
            if isinstance(target, ast.Name):
                if value is UNKNOWN:
                    constants.pop(target.id, None)
                else:
                    constants[target.id] = value
    elif isinstance(statement, ast.AnnAssign) and isinstance(statement.target, ast.Name):
        value = (
            UNKNOWN
            if statement.value is None
            else static_value(statement.value, constants)
        )
        if value is UNKNOWN:
            constants.pop(statement.target.id, None)
        else:
            constants[statement.target.id] = value
    elif isinstance(statement, (ast.AugAssign, ast.Delete)):
        for item in ast.walk(statement):
            if isinstance(item, ast.Name) and isinstance(item.ctx, (ast.Store, ast.Del)):
                constants.pop(item.id, None)


def statement_always_terminates(
    node: ast.stmt, constants: dict[str, Any] | None = None
) -> bool:
    constants = {} if constants is None else constants
    if isinstance(node, (ast.Return, ast.Raise, ast.Break, ast.Continue)):
        return True
    if isinstance(node, ast.If):
        truth = static_truth(node.test, constants)
        if truth is True:
            return block_always_terminates(node.body, constants)
        if truth is False:
            return bool(node.orelse) and block_always_terminates(
                node.orelse, constants
            )
        return bool(node.orelse) and block_always_terminates(
            node.body, constants
        ) and block_always_terminates(node.orelse, constants)
    return False


def block_always_terminates(
    statements: list[ast.stmt], constants: dict[str, Any] | None = None
) -> bool:
    state = dict(constants or {})
    for statement in statements:
        if statement_always_terminates(statement, state):
            return True
        update_known_constants(statement, state)
    return False


class ReachableFindingVisitor(ast.NodeVisitor):
    """Visit only statements that can be reached within a statically analyzable block."""

    def __init__(self, source_path: str) -> None:
        self.source_path = source_path
        self.function = "<module>"
        self.constants: dict[str, Any] = {}
        self.contracts: Counter[tuple[str, str, str]] = Counter()

    def _visit_block(self, statements: list[ast.stmt]) -> None:
        previous_constants = self.constants
        self.constants = dict(previous_constants)
        try:
            for statement in statements:
                self.visit(statement)
                if statement_always_terminates(statement, self.constants):
                    break
                update_known_constants(statement, self.constants)
        finally:
            self.constants = previous_constants

    def visit_Module(self, node: ast.Module) -> None:
        for statement in node.body:
            self.visit(statement)
            if statement_always_terminates(statement, self.constants):
                break
            update_known_constants(statement, self.constants)

    def _visit_function(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> None:
        previous_function = self.function
        previous_constants = self.constants
        self.function = node.name
        self.constants = dict(previous_constants)
        try:
            for statement in node.body:
                self.visit(statement)
                if statement_always_terminates(statement, self.constants):
                    break
                update_known_constants(statement, self.constants)
        finally:
            self.function = previous_function
            self.constants = previous_constants

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self._visit_function(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self._visit_function(node)

    def visit_If(self, node: ast.If) -> None:
        self.visit(node.test)
        truth = static_truth(node.test, self.constants)
        if truth is True:
            self._visit_block(node.body)
        elif truth is False:
            self._visit_block(node.orelse)
        else:
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
        truth = static_truth(node.test, self.constants)
        if truth is not False:
            self._visit_block(node.body)
        if truth is not True:
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
            reachable_literal_finding_contracts(
                path.read_text(encoding="utf-8"), relative
            )
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

    def test_constant_true_termination_suppresses_following_finding(self):
        literal = '''
def validate(value):
    if True:
        return
    Finding("PUBLIC_CODE", "unreachable")
'''
        module_flag = '''
STOP_VALIDATION = True
def validate(value):
    if STOP_VALIDATION:
        return
    Finding("PUBLIC_CODE", "unreachable")
'''
        local_flag = '''
def validate(value):
    stop_validation = True
    if stop_validation:
        return
    Finding("PUBLIC_CODE", "unreachable")
'''
        for source in (literal, module_flag, local_flag):
            with self.subTest(source=source):
                self.assertEqual(
                    reachable_literal_finding_contracts(source, "sample.py"),
                    Counter(),
                )


if __name__ == "__main__":
    unittest.main()
