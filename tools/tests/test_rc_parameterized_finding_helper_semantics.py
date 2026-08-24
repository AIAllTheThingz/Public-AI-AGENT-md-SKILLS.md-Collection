from __future__ import annotations

import ast
import subprocess
import unittest
from pathlib import Path

from helpers import REPO_ROOT
from test_rc_finding_code_contracts import normalized_semantic_ast

CHECKPOINT_COMMIT = "83c73f3ab9a049ff2321d463164fcf98fb453a9c"


def git_output(*args: str) -> str:
    completed = subprocess.run(
        ["git", "-C", str(REPO_ROOT), *args],
        text=True,
        encoding="utf-8",
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


def function_parameter_names(node: ast.FunctionDef | ast.AsyncFunctionDef) -> set[str]:
    args = node.args
    names = {
        argument.arg
        for argument in (*args.posonlyargs, *args.args, *args.kwonlyargs)
    }
    if args.vararg is not None:
        names.add(args.vararg.arg)
    if args.kwarg is not None:
        names.add(args.kwarg.arg)
    return names


def parameterized_finding_helpers(
    text: str, source_path: str
) -> dict[tuple[str, str], str]:
    tree = ast.parse(text)
    result: dict[tuple[str, str], str] = {}
    for statement in tree.body:
        if not isinstance(statement, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        parameters = function_parameter_names(statement)
        uses_parameterized_code = False
        for node in ast.walk(statement):
            if not (
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Name)
                and node.func.id == "Finding"
            ):
                continue
            expression = finding_code_expression(node)
            if isinstance(expression, ast.Name) and expression.id in parameters:
                uses_parameterized_code = True
                break
        if uses_parameterized_code:
            result[(source_path, statement.name)] = normalized_semantic_ast(statement)
    return result


def published_contracts() -> dict[tuple[str, str], str]:
    result: dict[tuple[str, str], str] = {}
    for relative in published_python_paths():
        result.update(
            parameterized_finding_helpers(
                git_source_at(CHECKPOINT_COMMIT, relative), relative
            )
        )
    return result


def candidate_contracts() -> dict[tuple[str, str], str]:
    result: dict[tuple[str, str], str] = {}
    for path in candidate_python_paths():
        relative = path.relative_to(REPO_ROOT).as_posix()
        result.update(
            parameterized_finding_helpers(path.read_text(encoding="utf-8"), relative)
        )
    return result


class ReleaseCandidateParameterizedFindingHelperSemanticTests(unittest.TestCase):
    def test_every_published_parameterized_helper_semantic_is_preserved(self):
        published = published_contracts()
        candidate = candidate_contracts()
        key = ("tools/validate-standards/validate_repository.py", "read_text")
        self.assertIn(key, published)
        missing_or_changed = {
            contract: semantic
            for contract, semantic in published.items()
            if candidate.get(contract) != semantic
        }
        self.assertEqual(
            missing_or_changed,
            {},
            "published parameterized finding helper behavior changed or disappeared",
        )

    def test_exception_behavior_change_is_detected(self):
        original = '''
def read_text(path, findings, code):
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError as exc:
        findings.append(Finding(code, str(exc), path="sample"))
        return None
'''
        changed = original.replace("UnicodeDecodeError", "ValueError")
        original_contract = parameterized_finding_helpers(original, "sample.py")
        changed_contract = parameterized_finding_helpers(changed, "sample.py")
        self.assertNotEqual(original_contract, changed_contract)

    def test_message_and_private_parameter_renames_remain_compatible(self):
        original = '''
def read_text(path, findings, code):
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError as exc:
        findings.append(Finding(code, "original wording", path="sample"))
        return None
'''
        compatible = original.replace("path, findings, code", "candidate, results, finding_code")
        compatible = compatible.replace("path.read_text", "candidate.read_text")
        compatible = compatible.replace("findings.append", "results.append")
        compatible = compatible.replace("Finding(code,", "Finding(finding_code,")
        compatible = compatible.replace("original wording", "improved wording")
        self.assertEqual(
            parameterized_finding_helpers(original, "sample.py"),
            parameterized_finding_helpers(compatible, "sample.py"),
        )


if __name__ == "__main__":
    unittest.main()
