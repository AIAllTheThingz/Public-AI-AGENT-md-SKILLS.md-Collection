from __future__ import annotations

import hashlib
import json
import subprocess
import tempfile
import unittest

from helpers import REPO_ROOT, json_result, run_tool

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
        self.assertEqual(
            self.contract["sourceCommit"],
            "83c73f3ab9a049ff2321d463164fcf98fb453a9c",
        )
        self.assertEqual(self.contract["toolContractPath"], "tools/TOOL_CONTRACT.md")

    def test_unchanged_published_tool_sources_preserve_all_finding_codes_and_meanings(self):
        for relative, expected_tree in self.contract["unchangedPublishedSourceTrees"].items():
            with self.subTest(tree=relative):
                self.assertEqual(git_object_sha(relative), expected_tree)

    def test_changed_tool_sources_retain_every_checkpointed_public_code(self):
        for relative, codes in self.contract["changedSourceCodes"].items():
            source = (REPO_ROOT / relative).read_text(encoding="utf-8")
            for code, meaning in codes.items():
                with self.subTest(tool=relative, code=code):
                    self.assertIn(f'"{code}"', source)
                    self.assertTrue(meaning.strip())

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
