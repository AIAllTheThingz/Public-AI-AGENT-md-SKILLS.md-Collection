from __future__ import annotations

import copy
import hashlib
import json
import re
import sys
import tempfile
import unittest
from pathlib import Path

from helpers import REPO_ROOT, json_result, run_tool

TOOLS_LIB = REPO_ROOT / "tools" / "lib"
if str(TOOLS_LIB) not in sys.path:
    sys.path.insert(0, str(TOOLS_LIB))

from standards_tools import Finding, ToolResult  # noqa: E402

CANDIDATE = "1.0.0-rc.1"
CHECKPOINT = "0.10.0"
CHECKPOINT_COMMIT = "83c73f3ab9a049ff2321d463164fcf98fb453a9c"
CHECKPOINT_INVENTORY_SHA256 = "38605392a558e02178cab08aea51c9df14c634b1866cb687f646ce476e69b622"
TOOL_BEHAVIOR_SHA256 = "120f9869f67bb9dc900e05cd41c8bbee08bf96bd516f0a6ce527d1a43bc809a3"
INVENTORY_PATH = REPO_ROOT / "releases" / "compatibility" / f"{CANDIDATE}.json"
CHECKPOINT_PATH = REPO_ROOT / "releases" / "compatibility" / f"{CHECKPOINT}-checkpoint.json"
TOOL_BEHAVIOR_PATH = REPO_ROOT / "releases" / "compatibility" / f"{CHECKPOINT}-tool-behavior.json"

CHECKPOINT_GROUP_TO_CANDIDATE_KEY = {
    "root": "stableRootPaths",
    "schemas": "stableSchemaPaths",
    "templates": "stableTemplatePaths",
    "tools": "stableToolEntryPaths",
    "profiles": "stableProfileEntryPaths",
}


def checkpoint_compatibility_findings(checkpoint: dict, candidate: dict) -> list[str]:
    findings: list[str] = []
    for checkpoint_group, candidate_key in CHECKPOINT_GROUP_TO_CANDIDATE_KEY.items():
        published = set(checkpoint["stablePathGroups"][checkpoint_group])
        proposed = set(candidate[candidate_key])
        for missing in sorted(published - proposed):
            findings.append(f"MISSING_STABLE_PATH:{checkpoint_group}:{missing}")

    result_schema = candidate["stableToolContracts"]["resultSchema"]
    for required_contract in checkpoint["stableContractPaths"]:
        if required_contract != result_schema:
            findings.append(f"MISSING_STABLE_CONTRACT:{required_contract}")

    proposed_artifacts = set(candidate["stableToolContracts"]["releaseArtifacts"])
    for missing in sorted(set(checkpoint["releaseArtifactPatterns"]) - proposed_artifacts):
        findings.append(f"MISSING_RELEASE_ARTIFACT_CONTRACT:{missing}")
    return findings


class ReleaseCandidateCompatibilityGateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.inventory = json.loads(INVENTORY_PATH.read_text(encoding="utf-8"))
        cls.checkpoint_bytes = CHECKPOINT_PATH.read_bytes()
        cls.checkpoint = json.loads(cls.checkpoint_bytes.decode("utf-8"))
        cls.tool_behavior_bytes = TOOL_BEHAVIOR_PATH.read_bytes()
        cls.tool_behavior = json.loads(cls.tool_behavior_bytes.decode("utf-8"))

    def test_candidate_and_release_state_are_forward_only(self):
        self.assertEqual((REPO_ROOT / "VERSION").read_text(encoding="utf-8").strip(), CANDIDATE)
        state = json.loads((REPO_ROOT / "releases" / "release-state.json").read_text(encoding="utf-8"))
        self.assertEqual(state["nextIntendedVersion"], CANDIDATE)
        self.assertIn(CHECKPOINT, state["publishedVersions"])
        self.assertNotIn(CANDIDATE, state["publishedVersions"])
        self.assertIn("0.9.0", state["preparedUnpublishedVersions"])

    def test_inventory_pins_published_migration_checkpoint(self):
        source = self.inventory["sourceCheckpoint"]
        self.assertEqual(source["version"], CHECKPOINT)
        self.assertEqual(source["tag"], "v0.10.0")
        self.assertEqual(source["commit"], CHECKPOINT_COMMIT)
        self.assertEqual(self.inventory["candidateVersion"], CANDIDATE)
        self.assertEqual(self.inventory["compatibilityClassification"], "compatible")

        pinned = self.inventory["publishedCheckpointInventory"]
        self.assertEqual(pinned["path"], "releases/compatibility/0.10.0-checkpoint.json")
        self.assertEqual(pinned["sha256"], CHECKPOINT_INVENTORY_SHA256)
        self.assertEqual(hashlib.sha256(self.checkpoint_bytes).hexdigest(), CHECKPOINT_INVENTORY_SHA256)
        self.assertEqual(self.checkpoint["sourceCommit"], CHECKPOINT_COMMIT)
        self.assertEqual(self.checkpoint["tag"], "v0.10.0")

        behavior_pin = self.inventory["publishedToolBehaviorContract"]
        self.assertEqual(behavior_pin["path"], "releases/compatibility/0.10.0-tool-behavior.json")
        self.assertEqual(behavior_pin["sha256"], TOOL_BEHAVIOR_SHA256)
        self.assertEqual(hashlib.sha256(self.tool_behavior_bytes).hexdigest(), TOOL_BEHAVIOR_SHA256)
        self.assertEqual(self.tool_behavior["sourceCommit"], CHECKPOINT_COMMIT)
        self.assertEqual(self.tool_behavior["tag"], "v0.10.0")

    def test_candidate_preserves_every_published_checkpoint_contract(self):
        self.assertEqual(checkpoint_compatibility_findings(self.checkpoint, self.inventory), [])

    def test_checkpoint_comparison_detects_removed_published_stable_path(self):
        candidate = copy.deepcopy(self.inventory)
        removed = self.checkpoint["stablePathGroups"]["root"][0]
        candidate["stableRootPaths"].remove(removed)
        self.assertIn(
            f"MISSING_STABLE_PATH:root:{removed}",
            checkpoint_compatibility_findings(self.checkpoint, candidate),
        )

    def test_all_enumerated_stable_paths_exist(self):
        path_groups = (
            "stableRootPaths",
            "stableSchemaPaths",
            "stableTemplatePaths",
            "stableToolEntryPaths",
            "stableProfileEntryPaths",
        )
        for group in path_groups:
            entries = self.inventory[group]
            self.assertTrue(entries, group)
            self.assertEqual(len(entries), len(set(entries)), group)
            for relative in entries:
                with self.subTest(group=group, path=relative):
                    self.assertTrue((REPO_ROOT / relative).is_file(), relative)

        result_schema = self.inventory["stableToolContracts"]["resultSchema"]
        self.assertTrue((REPO_ROOT / result_schema).is_file(), result_schema)

    def test_schema_and_template_inventory_matches_declared_stable_contract(self):
        schema_names = {
            "artifact-record.schema.json",
            "completion-result.schema.json",
            "exception-record.schema.json",
            "project-manifest.schema.json",
            "risk-classification.schema.json",
            "test-evidence.schema.json",
        }
        expected_schemas = {f"schemas/{name}" for name in schema_names} | {
            f"schemas/v1/{name}" for name in schema_names
        }
        self.assertEqual(set(self.inventory["stableSchemaPaths"]), expected_schemas)

        templates_manifest = (REPO_ROOT / "templates" / "MANIFEST.md").read_text(encoding="utf-8")
        stable_section = templates_manifest.split("## Stable compatibility paths", 1)[1].split(
            "## Acceptance checks", 1
        )[0]
        manifest_stable_paths = {
            f"templates/{match}"
            for match in re.findall(r"^- `([^`]+)`\s*$", stable_section, flags=re.MULTILINE)
        }
        self.assertEqual(set(self.inventory["stableTemplatePaths"]), manifest_stable_paths)

    def test_tool_inventory_matches_catalog_stable_entry_points(self):
        catalog = (REPO_ROOT / "tools" / "TOOL_CATALOG.md").read_text(encoding="utf-8")
        for relative in self.inventory["stableToolEntryPaths"]:
            self.assertIn(relative, catalog)
        self.assertIn("SHA256SUMS.txt", self.inventory["stableToolContracts"]["releaseArtifacts"])
        self.assertIn("release-manifest.json", self.inventory["stableToolContracts"]["releaseArtifacts"])

    def test_published_tool_contract_and_result_schema_remain_compatible(self):
        source_documents = self.tool_behavior["sourceDocuments"]
        contract_path = REPO_ROOT / source_documents["toolContract"]["path"]
        result_schema_path = REPO_ROOT / source_documents["toolResultSchema"]["path"]

        self.assertEqual(
            hashlib.sha256(contract_path.read_bytes()).hexdigest(),
            source_documents["toolContract"]["sha256"],
        )
        self.assertEqual(
            hashlib.sha256(result_schema_path.read_bytes()).hexdigest(),
            source_documents["toolResultSchema"]["sha256"],
        )

        schema = json.loads(result_schema_path.read_text(encoding="utf-8"))
        result_contract = self.tool_behavior["resultContract"]
        self.assertEqual(schema["required"], result_contract["requiredTopLevelFields"])
        self.assertEqual(schema["properties"]["status"]["enum"], result_contract["statusValues"])
        finding_schema = schema["properties"]["findings"]["items"]
        self.assertEqual(finding_schema["required"], result_contract["requiredFindingFields"])
        self.assertEqual(
            finding_schema["properties"]["severity"]["enum"],
            result_contract["findingSeverityValues"],
        )

    def test_published_cli_options_remain_available(self):
        for relative in self.tool_behavior["commonCliToolPaths"]:
            completed = run_tool(relative, "--help")
            with self.subTest(tool=relative):
                self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
                for option in self.tool_behavior["commonCliOptions"]:
                    self.assertIn(option, completed.stdout)

        for relative, options in self.tool_behavior["legacyCliExceptions"].items():
            completed = run_tool(relative, "--help")
            with self.subTest(tool=relative):
                self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
                for option in options:
                    self.assertIn(option, completed.stdout)

        writer = self.tool_behavior["representativeWriterContract"]
        completed = run_tool(writer["toolPath"], "--help")
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
        for option in writer["requiredOptions"]:
            self.assertIn(option, completed.stdout)

    def test_published_exit_code_meanings_remain_executable(self):
        expected = self.tool_behavior["exitCodeContract"]
        self.assertEqual(
            ToolResult.from_findings(tool="compat", version="1", findings=[]).exit_code(),
            expected["success"],
        )
        self.assertEqual(
            ToolResult.from_findings(
                tool="compat",
                version="1",
                findings=[Finding(code="COMPAT_FAIL", message="failure")],
            ).exit_code(),
            expected["validationFailure"],
        )
        self.assertEqual(
            ToolResult.error(tool="compat", version="1", message="internal").exit_code(),
            expected["internalError"],
        )

        completed = run_tool(
            "tools/generate-manifest/generate_manifest.py",
            "--format",
            "json",
            "--name",
            "compat-input-error",
            "--profile",
            "NOT_A_PROFILE",
            "--language",
            "csharp",
            "--dry-run",
        )
        self.assertEqual(completed.returncode, expected["inputOrConfigurationError"])
        payload = json_result(completed)
        self.assertEqual(payload["status"], "error")
        self.assertEqual(payload["findings"][0]["code"], "INPUT_ERROR")

    def test_published_safe_overwrite_behavior_is_exercised(self):
        writer = self.tool_behavior["representativeWriterContract"]
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / "project-manifest.json"
            sentinel = "do-not-overwrite\n"
            output.write_text(sentinel, encoding="utf-8")
            base_args = (
                "--format",
                "json",
                "--name",
                "compat-writer",
                "--profile",
                "CLI_TOOL",
                "--language",
                "csharp",
                "--manifest-output",
                str(output),
            )

            blocked = run_tool(writer["toolPath"], *base_args)
            self.assertEqual(blocked.returncode, self.tool_behavior["exitCodeContract"]["inputOrConfigurationError"])
            self.assertEqual(output.read_text(encoding="utf-8"), sentinel)

            dry_run = run_tool(writer["toolPath"], *base_args, "--dry-run")
            self.assertEqual(dry_run.returncode, self.tool_behavior["exitCodeContract"]["success"])
            self.assertEqual(output.read_text(encoding="utf-8"), sentinel)

            forced = run_tool(writer["toolPath"], *base_args, "--force")
            self.assertEqual(forced.returncode, self.tool_behavior["exitCodeContract"]["success"])
            self.assertNotEqual(output.read_text(encoding="utf-8"), sentinel)
            generated = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(generated["name"], "compat-writer")
            self.assertEqual(generated["profile"], "CLI_TOOL")
            self.assertIn("csharp", generated["languages"])

    def test_stable_package_promise_is_narrow_and_csharp_is_stable(self):
        packages = self.inventory["stablePackages"]
        self.assertEqual([item["path"] for item in packages], ["languages/csharp"])
        self.assertEqual(packages[0]["maturity"], "stable")
        manifest = (REPO_ROOT / "languages" / "csharp" / "MANIFEST.md").read_text(encoding="utf-8")
        self.assertIn("status: stable", manifest)
        self.assertIn("`agents/openai.yaml`", manifest)
        self.assertIn("Every standards package not explicitly listed", self.inventory["baselineExclusionRule"])
        self.assertGreaterEqual(len(self.inventory["baselineExcludedFamilies"]), 8)

    def test_migration_exercise_preserves_checkpoint_contracts(self):
        migration = self.inventory["migrationFrom0100"]
        self.assertEqual(migration["breakingChanges"], [])
        self.assertGreaterEqual(len(migration["requiredActions"]), 3)
        self.assertGreaterEqual(len(migration["preservedContracts"]), 6)
        notes = (REPO_ROOT / "releases" / "migrations" / f"{CANDIDATE}.md").read_text(encoding="utf-8")
        self.assertIn("# Migration to 1.0.0-rc.1 from 0.10.0", notes)
        self.assertIn("## Required actions", notes)
        self.assertIn("None relative to published `v0.10.0`", notes)
        self.assertIn("Final `1.0.0` has not yet been approved or published", notes)

    def test_release_validator_accepts_rc_tag_contract(self):
        completed = run_tool(
            "tools/release/validate_release.py",
            "--format",
            "json",
            "--tag",
            f"v{CANDIDATE}",
        )
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
        payload = json_result(completed)
        self.assertEqual(payload["status"], "passed")
        self.assertEqual(payload["summary"]["repositoryVersion"], CANDIDATE)
        self.assertEqual(payload["summary"]["expectedTag"], f"v{CANDIDATE}")

    def test_final_100_gate_is_not_overclaimed(self):
        pending = "\n".join(self.inventory["final100GateNotYetClaimed"])
        self.assertIn("must be published and available for review", pending)
        self.assertIn("independently verified", pending)
        self.assertIn("independent specialist review", pending)

        release_notes = (REPO_ROOT / "releases" / f"{CANDIDATE}.md").read_text(encoding="utf-8")
        self.assertIn("not itself proof of a published `v1.0.0-rc.1`", release_notes)
        self.assertIn("Final `1.0.0` remains blocked", release_notes)


if __name__ == "__main__":
    unittest.main()
