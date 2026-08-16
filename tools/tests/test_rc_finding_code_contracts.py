from __future__ import annotations

import ast
import copy
import hashlib
import json
import subprocess
import tempfile
import unittest

from helpers import REPO_ROOT, json_result, run_tool

CHECKPOINT_COMMIT = "83c73f3ab9a049ff2321d463164fcf98fb453a9c"
CHECKPOINT_PATH = REPO_ROOT / "releases" / "compatibility" / "0.10.0-finding-codes.json"
CHECKPOINT_SHA256 = "8c3fb59522f2230d32e8a3675c9f9bbf5113c671b29e3a90bc6193b3b4244e4d"


def git_object_sha(relative: str) -> str:
    completed = subprocess.run(
        ["git", "-C", str(REPO_ROOT), "rev-parse", f"HEAD:{relative}"],
        text=True,
        capture_output=True,
        check=False,
    )
    if completed.returncode != 0:
        raise AssertionError(completed.stderr.strip() or f"cannot resolve HEAD:{relative}")
    return completed.stdout.strip()


def git_source_at(commit: str, relative: str) -> str:
    completed = subprocess.run(
        ["git", "-C", str(REPO_ROOT), "show", f"{commit}:{relative}"],
        text=True,
        capture_output=True,
        check=False,
    )
    if completed.returncode != 0:
        raise AssertionError(
            completed.stderr.strip()
            or f"cannot resolve published source {commit}:{relative}; full Git history is required"
        )
    return completed.stdout


def canonical_ast(node: ast.AST | None) -> str:
    return "" if node is None else ast.dump(node, annotate_fields=False, include_attributes=False)


class FindingMessageNormalizer(ast.NodeTransformer):
    """Remove human-readable Finding message text from semantic dependency snapshots."""

    def visit_Call(self, node: ast.Call) -> ast.AST:
        node = self.generic_visit(node)
        if isinstance(node.func, ast.Name) and node.func.id == "Finding":
            if len(node.args) >= 2:
                node.args[1] = ast.Constant(value="<message>")
            for keyword in node.keywords:
                if keyword.arg == "message":
                    keyword.value = ast.Constant(value="<message>")
        return node


def normalized_semantic_ast(node: ast.AST | None) -> str:
    if node is None:
        return ""
    cloned = copy.deepcopy(node)
    cloned = FindingMessageNormalizer().visit(cloned)
    ast.fix_missing_locations(cloned)
    return canonical_ast(cloned)


def loaded_names(node: ast.AST | None) -> set[str]:
    if node is None:
        return set()
    return {
        item.id
        for item in ast.walk(node)
        if isinstance(item, ast.Name) and isinstance(item.ctx, ast.Load)
    }


def module_definitions(tree: ast.Module) -> dict[str, ast.AST]:
    definitions: dict[str, ast.AST] = {}
    for statement in tree.body:
        if isinstance(statement, ast.Assign):
            for target in statement.targets:
                if isinstance(target, ast.Name):
                    definitions[target.id] = statement.value
        elif isinstance(statement, ast.AnnAssign) and isinstance(statement.target, ast.Name):
            if statement.value is not None:
                definitions[statement.target.id] = statement.value
        elif isinstance(statement, (ast.FunctionDef, ast.AsyncFunctionDef)):
            definitions[statement.name] = statement
    return definitions


def finding_call_shape(node: ast.Call) -> dict[str, object]:
    # Finding(code, message, ...) exposes the code and semantic emission context as the
    # compatibility contract. Message wording is deliberately excluded because the
    # public tool contract permits editorial wording improvements.
    positional_tail = [canonical_ast(argument) for argument in node.args[2:]]
    keywords = sorted(
        (
            keyword.arg if keyword.arg is not None else "**",
            canonical_ast(keyword.value),
        )
        for keyword in node.keywords
        if keyword.arg != "message"
    )
    return {
        "positionalTail": positional_tail,
        "keywords": keywords,
    }


def finding_dependency_nodes(node: ast.Call) -> list[ast.AST]:
    dependencies: list[ast.AST] = list(node.args[2:])
    dependencies.extend(
        keyword.value
        for keyword in node.keywords
        if keyword.arg != "message"
    )
    return dependencies


class FindingSignatureVisitor(ast.NodeVisitor):
    def __init__(self, definitions: dict[str, ast.AST]) -> None:
        self.module_definitions = definitions
        self.function = "<module>"
        self.context: list[str] = []
        self.context_nodes: list[ast.AST] = []
        self.local_bindings: dict[str, ast.AST] = {}
        self.signatures: dict[str, list[str]] = {}

    def _visit_block(self, statements: list[ast.stmt]) -> None:
        for statement in statements:
            self.visit(statement)

    def _with_context(
        self,
        marker: str,
        dependency_node: ast.AST | None,
        statements: list[ast.stmt],
    ) -> None:
        self.context.append(marker)
        if dependency_node is not None:
            self.context_nodes.append(dependency_node)
        try:
            self._visit_block(statements)
        finally:
            if dependency_node is not None:
                self.context_nodes.pop()
            self.context.pop()

    def _dependency_snapshot(self, nodes: list[ast.AST]) -> dict[str, str]:
        pending: set[str] = set()
        for node in nodes:
            pending.update(loaded_names(node))

        snapshot: dict[str, str] = {}
        visited: set[str] = set()
        while pending:
            name = pending.pop()
            if name in visited:
                continue
            visited.add(name)

            binding = self.local_bindings.get(name)
            if binding is None:
                binding = self.module_definitions.get(name)
            if binding is None:
                continue

            snapshot[name] = normalized_semantic_ast(binding)
            pending.update(loaded_names(binding) - visited)

        return dict(sorted(snapshot.items()))

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        previous_function = self.function
        previous_bindings = self.local_bindings
        self.function = node.name
        self.local_bindings = {}
        try:
            self._visit_block(node.body)
        finally:
            self.function = previous_function
            self.local_bindings = previous_bindings

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        previous_function = self.function
        previous_bindings = self.local_bindings
        self.function = node.name
        self.local_bindings = {}
        try:
            self._visit_block(node.body)
        finally:
            self.function = previous_function
            self.local_bindings = previous_bindings

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
        test = canonical_ast(node.test)
        self._with_context(f"if:{test}", node.test, node.body)
        if node.orelse:
            self._with_context(f"else:{test}", node.test, node.orelse)

    def visit_For(self, node: ast.For) -> None:
        marker = f"for:{canonical_ast(node.target)} in {canonical_ast(node.iter)}"
        self._with_context(marker, node.iter, node.body)
        if node.orelse:
            self._with_context(f"for-else:{marker}", node.iter, node.orelse)

    def visit_AsyncFor(self, node: ast.AsyncFor) -> None:
        marker = f"async-for:{canonical_ast(node.target)} in {canonical_ast(node.iter)}"
        self._with_context(marker, node.iter, node.body)
        if node.orelse:
            self._with_context(f"async-for-else:{marker}", node.iter, node.orelse)

    def visit_While(self, node: ast.While) -> None:
        test = canonical_ast(node.test)
        self._with_context(f"while:{test}", node.test, node.body)
        if node.orelse:
            self._with_context(f"while-else:{test}", node.test, node.orelse)

    def visit_Try(self, node: ast.Try) -> None:
        self._with_context("try", None, node.body)
        for handler in node.handlers:
            exception_type = canonical_ast(handler.type) if handler.type is not None else "bare"
            self._with_context(f"except:{exception_type}", handler.type, handler.body)
        if node.orelse:
            self._with_context("try-else", None, node.orelse)
        if node.finalbody:
            self._with_context("finally", None, node.finalbody)

    def visit_Call(self, node: ast.Call) -> None:
        if (
            isinstance(node.func, ast.Name)
            and node.func.id == "Finding"
            and node.args
            and isinstance(node.args[0], ast.Constant)
            and isinstance(node.args[0].value, str)
        ):
            code = node.args[0].value
            dependency_nodes = list(self.context_nodes) + finding_dependency_nodes(node)
            signature = json.dumps(
                {
                    "function": self.function,
                    "context": list(self.context),
                    "dependencies": self._dependency_snapshot(dependency_nodes),
                    "emission": finding_call_shape(node),
                },
                sort_keys=True,
            )
            self.signatures.setdefault(code, []).append(signature)
        self.generic_visit(node)


def finding_semantic_signatures(text: str) -> dict[str, list[str]]:
    tree = ast.parse(text)
    visitor = FindingSignatureVisitor(module_definitions(tree))
    visitor.visit(tree)
    return {code: sorted(signatures) for code, signatures in visitor.signatures.items()}


def finding_map(payload: dict) -> dict[str, list[str]]:
    result: dict[str, list[str]] = {}
    for finding in payload.get("findings", []):
        result.setdefault(finding["code"], []).append(finding["message"])
    return result


class ReleaseCandidateFindingCodeContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.checkpoint_bytes = CHECKPOINT_PATH.read_bytes()
        cls.contract = json.loads(cls.checkpoint_bytes.decode("utf-8"))

    def test_checkpoint_is_pinned_to_published_source(self):
        self.assertEqual(hashlib.sha256(self.checkpoint_bytes).hexdigest(), CHECKPOINT_SHA256)
        self.assertEqual(self.contract["releaseVersion"], "0.10.0")
        self.assertEqual(self.contract["tag"], "v0.10.0")
        self.assertEqual(self.contract["sourceCommit"], CHECKPOINT_COMMIT)
        self.assertEqual(self.contract["toolContractPath"], "tools/TOOL_CONTRACT.md")

    def test_unchanged_published_tool_sources_preserve_all_finding_codes_and_meanings(self):
        for relative, expected_tree in self.contract["unchangedPublishedSourceTrees"].items():
            with self.subTest(tree=relative):
                self.assertEqual(git_object_sha(relative), expected_tree)

    def test_changed_tool_sources_preserve_checkpointed_finding_semantics(self):
        for relative, codes in self.contract["changedSourceCodes"].items():
            published = finding_semantic_signatures(git_source_at(CHECKPOINT_COMMIT, relative))
            current = finding_semantic_signatures((REPO_ROOT / relative).read_text(encoding="utf-8"))

            for code in codes:
                with self.subTest(tool=relative, code=code):
                    published_signatures = set(published.get(code, []))
                    current_signatures = set(current.get(code, []))
                    self.assertTrue(published_signatures, f"published source did not emit {code}")
                    self.assertEqual(
                        published_signatures - current_signatures,
                        set(),
                        f"published semantic context or referenced data changed/disappeared for {code}",
                    )

                    additional = current_signatures - published_signatures
                    if code == "RELEASE_STATE_INVALID":
                        self.assertEqual(len(additional), 3)
                        payloads = [json.loads(signature) for signature in additional]
                        self.assertTrue(
                            all(payload["function"] == "read_release_state" for payload in payloads)
                        )
                        contexts = ["\n".join(payload["context"]) for payload in payloads]
                        self.assertTrue(
                            any(
                                "Name('published', Load())" in context
                                and "Name('SEMVER', Load())" in context
                                for context in contexts
                            )
                        )
                        self.assertTrue(
                            any(
                                "Name('published', Load())" in context
                                and "Name('blocked', Load())" in context
                                for context in contexts
                            )
                        )
                        self.assertTrue(
                            any(
                                "Name('next_intended', Load())" in context
                                and "Name('published', Load())" in context
                                for context in contexts
                            )
                        )
                    else:
                        self.assertEqual(
                            additional,
                            set(),
                            f"unreviewed additional semantic context reuses public code {code}",
                        )

    def test_semantic_signature_allows_message_rewording_but_tracks_condition_and_data(self):
        original = '''
REQUIRED_HEADINGS = ("A", "B")
def run(text):
    for heading in REQUIRED_HEADINGS:
        if heading not in text:
            Finding("PUBLIC_CODE", "Original wording.", path="sample")
'''
        reworded = '''
REQUIRED_HEADINGS = ("A", "B")
def run(text):
    for heading in REQUIRED_HEADINGS:
        if heading not in text:
            Finding("PUBLIC_CODE", "Improved human-readable wording.", path="sample")
'''
        changed_data = '''
REQUIRED_HEADINGS = ("A",)
def run(text):
    for heading in REQUIRED_HEADINGS:
        if heading not in text:
            Finding("PUBLIC_CODE", "Original wording.", path="sample")
'''
        reused = '''
REQUIRED_HEADINGS = ("A", "B")
def run(other_text):
    for heading in REQUIRED_HEADINGS:
        if heading not in other_text:
            Finding("PUBLIC_CODE", "Original wording.", path="sample")
'''
        self.assertEqual(
            finding_semantic_signatures(original),
            finding_semantic_signatures(reworded),
        )
        self.assertNotEqual(
            finding_semantic_signatures(original),
            finding_semantic_signatures(changed_data),
        )
        self.assertNotEqual(
            finding_semantic_signatures(original),
            finding_semantic_signatures(reused),
        )

    def test_template_validator_emits_published_stable_path_code(self):
        with tempfile.TemporaryDirectory() as temp:
            completed = run_tool(
                "tools/validate-templates/validate_templates.py",
                "--format",
                "json",
                "--root",
                temp,
            )
        self.assertEqual(completed.returncode, 1, completed.stdout + completed.stderr)
        findings = finding_map(json_result(completed))
        self.assertIn("TEMPLATE_STABLE_PATH_MISSING", findings)
        self.assertIn("Missing stable template path.", findings["TEMPLATE_STABLE_PATH_MISSING"])

    def test_generate_manifest_emits_published_warning_and_input_codes(self):
        warning = run_tool(
            "tools/generate-manifest/generate_manifest.py",
            "--format",
            "json",
            "--name",
            "finding-code-contract",
            "--profile",
            "CLI_TOOL",
            "--language",
            "csharp",
            "--dry-run",
        )
        self.assertEqual(warning.returncode, 0, warning.stdout + warning.stderr)
        warning_findings = finding_map(json_result(warning))
        self.assertIn("MANIFEST_NO_DISCIPLINES", warning_findings)

        invalid = run_tool(
            "tools/generate-manifest/generate_manifest.py",
            "--format",
            "json",
            "--name",
            "finding-code-contract",
            "--profile",
            "NOT_A_PROFILE",
            "--language",
            "csharp",
            "--dry-run",
        )
        self.assertEqual(invalid.returncode, 2, invalid.stdout + invalid.stderr)
        invalid_findings = finding_map(json_result(invalid))
        self.assertIn("INPUT_ERROR", invalid_findings)

    def test_release_validator_emits_published_tag_mismatch_code(self):
        completed = run_tool(
            "tools/release/validate_release.py",
            "--format",
            "json",
            "--tag",
            "v0.0.0",
        )
        self.assertEqual(completed.returncode, 1, completed.stdout + completed.stderr)
        findings = finding_map(json_result(completed))
        self.assertIn("RELEASE_TAG_MISMATCH", findings)

    def test_representative_checkpoint_codes_are_explicit(self):
        representatives = {
            item["code"]: item["meaning"]
            for item in self.contract["representativeEmittedFindings"]
        }
        self.assertEqual(
            set(representatives),
            {
                "TEMPLATE_STABLE_PATH_MISSING",
                "MANIFEST_NO_DISCIPLINES",
                "RELEASE_TAG_MISMATCH",
                "INPUT_ERROR",
            },
        )
        self.assertTrue(all(value.strip() for value in representatives.values()))


if __name__ == "__main__":
    unittest.main()
