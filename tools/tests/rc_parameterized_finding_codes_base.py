from __future__ import annotations

import ast
import copy
import json
import subprocess
import unittest
from pathlib import Path

from helpers import REPO_ROOT

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


def canonical_ast(node: ast.AST) -> str:
    return ast.dump(node, annotate_fields=False, include_attributes=False)


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


def module_bindings(tree: ast.Module) -> dict[str, ast.AST]:
    result: dict[str, ast.AST] = {}
    for statement in tree.body:
        if isinstance(statement, ast.Assign):
            for target in statement.targets:
                if isinstance(target, ast.Name):
                    result[target.id] = statement.value
        elif isinstance(statement, ast.AnnAssign) and isinstance(statement.target, ast.Name):
            if statement.value is not None:
                result[statement.target.id] = statement.value
    return result


def literal_string(node: ast.AST, bindings: dict[str, ast.AST]) -> str | None:
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    if isinstance(node, ast.Name):
        bound = bindings.get(node.id)
        if isinstance(bound, ast.Constant) and isinstance(bound.value, str):
            return bound.value
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


class ExpressionNormalizer(ast.NodeTransformer):
    def __init__(
        self,
        local_bindings: dict[str, ast.AST],
        module_values: dict[str, ast.AST],
        parameter_positions: dict[str, int],
    ) -> None:
        self.local_bindings = local_bindings
        self.module_values = module_values
        self.parameter_positions = parameter_positions
        self.expanding: set[str] = set()

    def visit_Name(self, node: ast.Name) -> ast.AST:
        if node.id in self.parameter_positions:
            return ast.copy_location(
                ast.Name(id=f"_p{self.parameter_positions[node.id]}", ctx=node.ctx), node
            )
        if isinstance(node.ctx, ast.Load):
            binding = self.local_bindings.get(node.id)
            if binding is None:
                binding = self.module_values.get(node.id)
            if binding is not None and node.id not in self.expanding:
                self.expanding.add(node.id)
                try:
                    replacement = self.visit(copy.deepcopy(binding))
                    return ast.copy_location(replacement, node)
                finally:
                    self.expanding.remove(node.id)
        return node


def semantic_expression(
    node: ast.AST,
    local_bindings: dict[str, ast.AST],
    module_values: dict[str, ast.AST],
    parameter_positions: dict[str, int],
) -> str:
    normalized = ExpressionNormalizer(
        local_bindings, module_values, parameter_positions
    ).visit(copy.deepcopy(node))
    ast.fix_missing_locations(normalized)
    return canonical_ast(normalized)


class ParameterizedCallSiteVisitor(ast.NodeVisitor):
    def __init__(
        self,
        source_path: str,
        definitions: dict[str, ast.FunctionDef | ast.AsyncFunctionDef],
        parameterized_helpers: dict[str, set[str]],
        module_values: dict[str, ast.AST],
    ) -> None:
        self.source_path = source_path
        self.definitions = definitions
        self.parameterized_helpers = parameterized_helpers
        self.module_values = module_values
        self.caller = "<module>"
        self.parameter_positions: dict[str, int] = {}
        self.local_bindings: dict[str, ast.AST] = {}
        self.context_nodes: list[ast.AST] = []
        self.contracts: set[str] = set()

    def _visit_block(self, statements: list[ast.stmt]) -> None:
        for statement in statements:
            self.visit(statement)

    def _with_context(self, node: ast.AST, statements: list[ast.stmt]) -> None:
        self.context_nodes.append(node)
        try:
            self._visit_block(statements)
        finally:
            self.context_nodes.pop()

    def _visit_function(
        self, node: ast.FunctionDef | ast.AsyncFunctionDef
    ) -> None:
        previous_caller = self.caller
        previous_parameters = self.parameter_positions
        previous_bindings = self.local_bindings
        self.caller = node.name
        self.parameter_positions = {
            name: index for index, name in enumerate(function_parameter_order(node))
        }
        self.local_bindings = {}
        try:
            self._visit_block(node.body)
        finally:
            self.caller = previous_caller
            self.parameter_positions = previous_parameters
            self.local_bindings = previous_bindings

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self._visit_function(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self._visit_function(node)

    def visit_Assign(self, node: ast.Assign) -> None:
        for target in node.targets:
            if isinstance(target, ast.Name):
                self.local_bindings[target.id] = node.value
        self.generic_visit(node)

    def visit_AnnAssign(self, node: ast.AnnAssign) -> None:
        if isinstance(node.target, ast.Name) and node.value is not None:
            self.local_bindings[node.target.id] = node.value
        self.generic_visit(node)

    def visit_If(self, node: ast.If) -> None:
        self._with_context(node.test, node.body)
        if node.orelse:
            self._with_context(node.test, node.orelse)

    def visit_For(self, node: ast.For) -> None:
        self._with_context(node.iter, node.body)
        if node.orelse:
            self._with_context(node.iter, node.orelse)

    def visit_While(self, node: ast.While) -> None:
        self._with_context(node.test, node.body)
        if node.orelse:
            self._with_context(node.test, node.orelse)

    def visit_Call(self, node: ast.Call) -> None:
        if not (isinstance(node.func, ast.Name) and node.func.id in self.parameterized_helpers):
            self.generic_visit(node)
            return

        helper_name = node.func.id
        definition = self.definitions[helper_name]
        for code_parameter in self.parameterized_helpers[helper_name]:
            code_argument = call_argument(node, definition, code_parameter)
            if code_argument is None:
                continue
            code = literal_string(code_argument, self.module_values)
            if code is None:
                continue

            arguments: dict[str, str] = {}
            all_parameters = function_parameter_order(definition) + [
                argument.arg for argument in definition.args.kwonlyargs
            ]
            for parameter in all_parameters:
                if parameter == code_parameter:
                    continue
                argument = call_argument(node, definition, parameter)
                if argument is None:
                    continue
                arguments[parameter] = semantic_expression(
                    argument,
                    self.local_bindings,
                    self.module_values,
                    self.parameter_positions,
                )

            context = [
                semantic_expression(
                    item,
                    self.local_bindings,
                    self.module_values,
                    self.parameter_positions,
                )
                for item in self.context_nodes
            ]
            self.contracts.add(
                json.dumps(
                    {
                        "sourcePath": self.source_path,
                        "helper": helper_name,
                        "caller": self.caller,
                        "code": code,
                        "context": context,
                        "arguments": arguments,
                    },
                    sort_keys=True,
                )
            )
        self.generic_visit(node)


def parameterized_finding_contracts(text: str, source_path: str) -> set[str]:
    tree = ast.parse(text)
    helpers = parameterized_finding_parameters(tree)
    if not helpers:
        return set()
    definitions = {
        statement.name: statement
        for statement in tree.body
        if isinstance(statement, (ast.FunctionDef, ast.AsyncFunctionDef))
    }
    visitor = ParameterizedCallSiteVisitor(
        source_path, definitions, helpers, module_bindings(tree)
    )
    visitor.visit(tree)
    return visitor.contracts


def published_contracts() -> set[str]:
    result: set[str] = set()
    for relative in published_python_paths():
        result.update(
            parameterized_finding_contracts(
                git_source_at(CHECKPOINT_COMMIT, relative), relative
            )
        )
    return result


def candidate_contracts() -> set[str]:
    result: set[str] = set()
    for path in candidate_python_paths():
        relative = path.relative_to(REPO_ROOT).as_posix()
        result.update(
            parameterized_finding_contracts(path.read_text(encoding="utf-8"), relative)
        )
    return result


def matching_contract(contracts: set[str], code: str) -> dict:
    matches = [json.loads(item) for item in contracts if json.loads(item)["code"] == code]
    if len(matches) != 1:
        raise AssertionError(f"expected one contract for {code}, found {len(matches)}")
    return matches[0]


class ReleaseCandidateParameterizedFindingCodeTests(unittest.TestCase):
    def test_every_published_caller_supplied_finding_contract_is_preserved(self):
        published = published_contracts()
        candidate = candidate_contracts()
        license_contract = matching_contract(published, "LICENSE_ENCODING")
        self.assertEqual(
            license_contract["sourcePath"],
            "tools/validate-standards/validate_repository.py",
        )
        self.assertEqual(license_contract["helper"], "read_text")
        self.assertIn("LICENSE", " ".join(license_contract["arguments"].values()))
        self.assertEqual(
            published - candidate,
            set(),
            "published caller-supplied finding call-site semantics changed or disappeared",
        )

    def test_swapping_codes_between_call_sites_is_detected(self):
        published = '''
def read_text(path, findings, code):
    Finding(code, "decode failed", path="sample")
def validate(root, findings):
    license_path = root / "LICENSE"
    notice_path = root / "NOTICE"
    read_text(license_path, findings, "LICENSE_ENCODING")
    read_text(notice_path, findings, "NOTICE_ENCODING")
'''
        swapped = published.replace("LICENSE_ENCODING", "SWAP").replace(
            "NOTICE_ENCODING", "LICENSE_ENCODING"
        ).replace("SWAP", "NOTICE_ENCODING")
        expected = parameterized_finding_contracts(published, "sample.py")
        actual = parameterized_finding_contracts(swapped, "sample.py")
        self.assertNotEqual(expected, actual)
        expected_license = matching_contract(expected, "LICENSE_ENCODING")
        actual_license = matching_contract(actual, "LICENSE_ENCODING")
        self.assertNotEqual(expected_license["arguments"], actual_license["arguments"])

    def test_private_local_rename_keeps_call_site_semantics(self):
        original = '''
def read_text(path, findings, code):
    Finding(code, "decode failed", path="sample")
def validate(root, findings):
    license_path = root / "LICENSE"
    read_text(license_path, findings, "LICENSE_ENCODING")
'''
        renamed = original.replace("license_path", "candidate_path")
        self.assertEqual(
            parameterized_finding_contracts(original, "sample.py"),
            parameterized_finding_contracts(renamed, "sample.py"),
        )


if __name__ == "__main__":
    unittest.main()
