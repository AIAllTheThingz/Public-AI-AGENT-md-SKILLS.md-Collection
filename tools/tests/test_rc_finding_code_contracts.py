from __future__ import annotations

import ast
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


class FindingSignatureVisitor(ast.NodeVisitor):
    def __init__(self) -> None:
        self.function = "<module>"
        self.context: list[str] = []
        self.signatures: dict[str, list[str]] = {}

    def _visit_block(self, statements: list[ast.stmt]) -> None:
        for statement in statements:
            self.visit(statement)

    def _with_context(self, marker: str, statements: list[ast.stmt]) -> None:
        self.context.append(marker)
        try:
            self._visit_block(statements)
        finally:
            self.context.pop()

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        previous = self.function
        self.function = node.name
        try:
            self._visit_block(node.body)
        finally:
            self.function = previous

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        previous = self.function
        self.function = node.name
        try:
            self._visit_block(node.body)
        finally:
            self.function = previous

    def visit_If(self, node: ast.If) -> None:
        test = canonical_ast(node.test)
        self._with_context(f"if:{test}", node.body)
        if node.orelse:
            self._with_context(f"else:{test}", node.orelse)

    def visit_For(self, node: ast.For) -> None:
        marker = f"for:{canonical_ast(node.target)} in {canonical_ast(node.iter)}"
        self._with_context(marker, node.body)
        if node.orelse:
            self._with_context(f"for-else:{marker}", node.orelse)

    def visit_AsyncFor(self, node: ast.AsyncFor) -> None:
        marker = f"async-for:{canonical_ast(node.target)} in {canonical_ast(node.iter)}"
        self._with_context(marker, node.body)
        if node.orelse:
            self._with_context(f"async-for-else:{marker}", node.orelse)

    def visit_While(self, node: ast.While) -> None:
        test = canonical_ast(node.test)
        self._with_context(f"while:{test}", node.body)
        if node.orelse:
            self._with_context(f"while-else:{test}", node.orelse)

    def visit_Try(self, node: ast.Try) -> None:
        self._with_context("try", node.body)
        for handler in node.handlers:
            exception_type = canonical_ast(handler.type) if handler.type is not None else "bare"
            self._with_context(f"except:{exception_type}", handler.body)
        if node.orelse:
            self._with_context("try-else", node.orelse)
        if node.finalbody:
            self._with_context("finally", node.finalbody)

    def visit_Call(self, node: ast.Call) -> None:
        if (
            isinstance(node.func, ast.Name)
            and node.func.id == "Finding"
            and node.args
            and isinstance(node.args[0], ast.Constant)
            and isinstance(node.args[0].value, str)
        ):
            code = node.args[0].value
            signature = json.dumps(
                {
                    "function": self.function,
                    "context": list(self.context),
                    "call": canonical_ast(node),
                },
                sort_keys=True,
            )
            self.signatures.setdefault(code, []).append(signature)
        self.generic_visit(node)


def finding_semantic_signatures(text: str) -> dict[str, list[str]]:
    visitor = FindingSignatureVisitor()
    visitor.visit(ast.parse(text))
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
                        f"published semantic context changed or disappeared for {code}",
                    )

                    additional = current_signatures - published_signatures
                    if code == "RELEASE_STATE_INVALID":
                        self.assertEqual(len(additional), 3)
                        rendered = "\n".join(sorted(additional))
                        self.assertIn("publishedVersions must be an array of Semantic Version strings.", rendered)
                        self.assertIn(
                            "A version must not appear in both publishedVersions and preparedUnpublishedVersions.",
                            rendered,
                        )
                        self.assertIn(
                            "nextIntendedVersion must not already appear in publishedVersions.",
                            rendered,
                        )
                        self.assertTrue(
                            all('"function": "read_release_state"' in signature for signature in additional)
                        )
                    else:
                        self.assertEqual(
                            additional,
                            set(),
                            f"unreviewed additional semantic context reuses public code {code}",
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
