from __future__ import annotations

import ast
import subprocess
import unittest
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


def finding_code_expression(node: ast.Call) -> ast.AST | None:
    if node.args:
        return node.args[0]
    for keyword in node.keywords:
        if keyword.arg == "code":
            return keyword.value
    return None


def function_parameter_order(node: ast.FunctionDef | ast.AsyncFunctionDef) -> list[str]:
    args = node.args
    return [argument.arg for argument in (*args.posonlyargs, *args.args)]


def parameterized_finding_parameters(tree: ast.Module) -> dict[str, set[str]]:
    result: dict[str, set[str]] = {}
    for statement in tree.body:
        if not isinstance(statement, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        parameters = set(function_parameter_order(statement)) | {
            argument.arg for argument in statement.args.kwonlyargs
        }
        used: set[str] = set()
        for node in ast.walk(statement):
            if not (
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Name)
                and node.func.id == "Finding"
            ):
                continue
            expression = finding_code_expression(node)
            if isinstance(expression, ast.Name) and expression.id in parameters:
                used.add(expression.id)
        if used:
            result[statement.name] = used
    return result


def module_string_bindings(tree: ast.Module) -> dict[str, str]:
    result: dict[str, str] = {}
    for statement in tree.body:
        if not isinstance(statement, ast.Assign):
            continue
        if not (
            isinstance(statement.value, ast.Constant)
            and isinstance(statement.value.value, str)
        ):
            continue
        for target in statement.targets:
            if isinstance(target, ast.Name):
                result[target.id] = statement.value.value
    return result


def literal_string(node: ast.AST, constants: dict[str, str]) -> str | None:
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    if isinstance(node, ast.Name):
        return constants.get(node.id)
    return None


def call_argument(
    call: ast.Call,
    function: ast.FunctionDef | ast.AsyncFunctionDef,
    parameter: str,
) -> ast.AST | None:
    positional = function_parameter_order(function)
    if parameter in positional:
        index = positional.index(parameter)
        if index < len(call.args):
            return call.args[index]
    for keyword in call.keywords:
        if keyword.arg == parameter:
            return keyword.value
    return None


def parameterized_finding_codes(text: str, source_path: str) -> set[tuple[str, str, str]]:
    tree = ast.parse(text)
    helpers = parameterized_finding_parameters(tree)
    if not helpers:
        return set()

    definitions = {
        statement.name: statement
        for statement in tree.body
        if isinstance(statement, (ast.FunctionDef, ast.AsyncFunctionDef))
    }
    constants = module_string_bindings(tree)
    result: set[tuple[str, str, str]] = set()

    for node in ast.walk(tree):
        if not (isinstance(node, ast.Call) and isinstance(node.func, ast.Name)):
            continue
        helper_name = node.func.id
        if helper_name not in helpers:
            continue
        definition = definitions[helper_name]
        for parameter in helpers[helper_name]:
            argument = call_argument(node, definition, parameter)
            if argument is None:
                continue
            code = literal_string(argument, constants)
            if code is not None:
                result.add((source_path, helper_name, code))
    return result


def published_contracts() -> set[tuple[str, str, str]]:
    result: set[tuple[str, str, str]] = set()
    for relative in published_python_paths():
        result.update(
            parameterized_finding_codes(
                git_source_at(CHECKPOINT_COMMIT, relative), relative
            )
        )
    return result


def candidate_contracts() -> set[tuple[str, str, str]]:
    result: set[tuple[str, str, str]] = set()
    for path in candidate_python_paths():
        relative = path.relative_to(REPO_ROOT).as_posix()
        result.update(parameterized_finding_codes(path.read_text(encoding="utf-8"), relative))
    return result


class ReleaseCandidateParameterizedFindingCodeTests(unittest.TestCase):
    def test_every_published_caller_supplied_finding_code_is_preserved(self):
        published = published_contracts()
        candidate = candidate_contracts()
        self.assertIn(
            ("tools/validate-standards/validate_repository.py", "read_text", "LICENSE_ENCODING"),
            published,
        )
        self.assertEqual(
            published - candidate,
            set(),
            "published caller-supplied finding code was removed or renamed",
        )

    def test_caller_supplied_code_rename_is_detected(self):
        published = '''
def read_text(path, findings, code):
    Finding(code, "decode failed", path="sample")
def validate(path, findings):
    read_text(path, findings, "LICENSE_ENCODING")
'''
        renamed = published.replace("LICENSE_ENCODING", "LICENSE_ENCODING_V2")
        expected = parameterized_finding_codes(published, "sample.py")
        actual = parameterized_finding_codes(renamed, "sample.py")
        self.assertIn(("sample.py", "read_text", "LICENSE_ENCODING"), expected)
        self.assertNotEqual(expected, actual)
        self.assertEqual(
            expected - actual,
            {("sample.py", "read_text", "LICENSE_ENCODING")},
        )


if __name__ == "__main__":
    unittest.main()
