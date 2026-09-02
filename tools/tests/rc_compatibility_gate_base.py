from __future__ import annotations

import copy
import hashlib
import json
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from helpers import REPO_ROOT, json_result, run_tool, sha256_utf8_text_file

TOOLS_LIB = REPO_ROOT / "tools" / "lib"
if str(TOOLS_LIB) not in sys.path:
    sys.path.insert(0, str(TOOLS_LIB))

from standards_tools import Finding, ToolResult  # noqa: E402

CANDIDATE = "1.0.0-rc.1"
CHECKPOINT = "0.10.0"
CHECKPOINT_COMMIT = "83c73f3ab9a049ff2321d463164fcf98fb453a9c"
CHECKPOINT_INVENTORY_SHA256 = "a8e3d3c68e4040cb4b6b8b878f4ac46f6a55bfe66e8b080f97ee57c860a81921"
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

SCHEMA_ANNOTATION_KEYS = {
    "title",
    "description",
    "$comment",
    "examples",
    "default",
    "$defs",
    "definitions",
}
SCHEMA_STRUCTURAL_KEYS = {"required", "properties", "items"}


def git_source_at(revision: str, relative: str) -> str:
    completed = subprocess.run(
        ["git", "-C", str(REPO_ROOT), "show", f"{revision}:{relative}"],
        text=True,
        encoding="utf-8",
        capture_output=True,
        check=False,
    )
    if completed.returncode != 0:
        raise AssertionError(completed.stderr.strip() or "git show failed")
    return completed.stdout


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


def markdown_frontmatter_id(path: Path) -> str | None:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        return None
    end = text.find("\n---\n", 4)
    if end < 0:
        return None
    match = re.search(r"^id:\s*(\S+)\s*$", text[:end], flags=re.MULTILINE)
    return match.group(1) if match else None


def observed_checkpoint_identifiers(checkpoint: dict) -> dict[str, dict[str, str]]:
    expected = checkpoint["stableIdentifiers"]
    markdown_ids: dict[str, str] = {}
    schema_ids: dict[str, str] = {}

    for relative in expected["markdownFrontMatterIds"]:
        observed = markdown_frontmatter_id(REPO_ROOT / relative)
        if observed is not None:
            markdown_ids[relative] = observed

    for relative in expected["schemaIds"]:
        schema = json.loads((REPO_ROOT / relative).read_text(encoding="utf-8"))
        observed = schema.get("$id")
        if isinstance(observed, str):
            schema_ids[relative] = observed

    return {
        "markdownFrontMatterIds": markdown_ids,
        "schemaIds": schema_ids,
    }


def identifier_compatibility_findings(expected: dict, observed: dict) -> list[str]:
    findings: list[str] = []
    for category in ("markdownFrontMatterIds", "schemaIds"):
        expected_values = expected[category]
        observed_values = observed[category]
        for path, expected_value in expected_values.items():
            if path not in observed_values:
                findings.append(f"IDENTIFIER_MISSING:{category}:{path}")
            elif observed_values[path] != expected_value:
                findings.append(
                    f"IDENTIFIER_CHANGED:{category}:{path}:{expected_value}->{observed_values[path]}"
                )
    return findings


def schema_contract_findings(published: object, candidate: object, path: str = "$") -> list[str]:
    """Compare stable JSON Schema assertions while allowing optional compatible additions."""

    findings: list[str] = []
    if not isinstance(published, dict) or not isinstance(candidate, dict):
        if published != candidate:
            findings.append(f"SCHEMA_VALUE_CHANGED:{path}")
        return findings

    published_required = published.get("required")
    if published_required is not None:
        candidate_required = candidate.get("required")
        if (
            not isinstance(published_required, list)
            or not isinstance(candidate_required, list)
            or set(candidate_required) != set(published_required)
        ):
            findings.append(f"SCHEMA_REQUIRED_CHANGED:{path}")

    published_properties = published.get("properties")
    if published_properties is not None:
        candidate_properties = candidate.get("properties")
        if not isinstance(published_properties, dict) or not isinstance(candidate_properties, dict):
            findings.append(f"SCHEMA_PROPERTIES_MISSING:{path}")
        else:
            for name, published_property in published_properties.items():
                if name not in candidate_properties:
                    findings.append(f"SCHEMA_PROPERTY_MISSING:{path}.{name}")
                else:
                    findings.extend(
                        schema_contract_findings(
                            published_property,
                            candidate_properties[name],
                            f"{path}.properties.{name}",
                        )
                    )

    if "items" in published:
        if "items" not in candidate:
            findings.append(f"SCHEMA_ITEMS_MISSING:{path}")
        else:
            findings.extend(
                schema_contract_findings(published["items"], candidate["items"], f"{path}.items")
            )

    for key, published_value in published.items():
        if key in SCHEMA_STRUCTURAL_KEYS or key in SCHEMA_ANNOTATION_KEYS:
            continue
        if key not in candidate:
            findings.append(f"SCHEMA_KEY_MISSING:{path}:{key}")
        elif key == "enum":
            candidate_value = candidate[key]
            if not isinstance(candidate_value, list) or set(candidate_value) != set(published_value):
                findings.append(f"SCHEMA_ENUM_CHANGED:{path}")
        elif candidate[key] != published_value:
            findings.append(f"SCHEMA_CONTRACT_CHANGED:{path}:{key}")

    # A new optional property is a documented minor-compatible extension. Other
    # candidate-only assertion keywords narrow or otherwise alter an existing
    # published schema node and therefore require explicit compatibility review.
    for key in candidate:
        if key in published or key in SCHEMA_ANNOTATION_KEYS or key == "properties":
            continue
        findings.append(f"SCHEMA_CONSTRAINT_ADDED:{path}:{key}")

    return sorted(findings)


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
        self.assertEqual(self.inventory["compatibilityClassification"], "breaking")

        pinned = self.inventory["publishedCheckpointInventory"]
        self.assertEqual(pinned["path"], "releases/compatibility/0.10.0-checkpoint.json")
        self.assertEqual(pinned["sha256"], CHECKPOINT_INVENTORY_SHA256)
        self.assertEqual(sha256_utf8_text_file(CHECKPOINT_PATH), CHECKPOINT_INVENTORY_SHA256)
        self.assertEqual(self.checkpoint["sourceCommit"], CHECKPOINT_COMMIT)
        self.assertEqual(self.checkpoint["tag"], "v0.10.0")
        self.assertEqual(
            self.inventory["stableIdentifierContracts"]["publishedCheckpoint"]["source"],
            "releases/compatibility/0.10.0-checkpoint.json#stableIdentifiers",
        )

        behavior_pin = self.inventory["publishedToolBehaviorContract"]
        self.assertEqual(behavior_pin["path"], "releases/compatibility/0.10.0-tool-behavior.json")
        self.assertEqual(behavior_pin["sha256"], TOOL_BEHAVIOR_SHA256)
        self.assertEqual(sha256_utf8_text_file(TOOL_BEHAVIOR_PATH), TOOL_BEHAVIOR_SHA256)
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

    def test_profile_checkpoint_preserves_both_published_entry_points(self):
        entries = set(self.checkpoint["stablePathGroups"]["profiles"])
        canonical_files = {entry for entry in entries if entry.endswith(".md")}
        package_directories = entries - canonical_files
        self.assertEqual(len(canonical_files), 13)
        self.assertEqual(len(package_directories), 13)

        for canonical in canonical_files:
            slug = Path(canonical).stem.lower().replace("_", "-")
            package = f"profiles/{slug}"
            with self.subTest(canonical=canonical, package=package):
                self.assertIn(package, package_directories)
                self.assertTrue((REPO_ROOT / canonical).is_file(), canonical)
                self.assertTrue((REPO_ROOT / package).is_dir(), package)

    def test_published_identifier_checkpoint_matches_candidate_tree(self):
        expected = self.checkpoint["stableIdentifiers"]
        observed = observed_checkpoint_identifiers(self.checkpoint)
        self.assertEqual(identifier_compatibility_findings(expected, observed), [])

    def test_identifier_checkpoint_detects_markdown_mutation_and_schema_removal(self):
        expected = self.checkpoint["stableIdentifiers"]
        observed = observed_checkpoint_identifiers(self.checkpoint)

        markdown_path = next(iter(expected["markdownFrontMatterIds"]))
        mutated = copy.deepcopy(observed)
        mutated["markdownFrontMatterIds"][markdown_path] = "MUTATED-ID"
        self.assertTrue(
            any(
                finding.startswith(f"IDENTIFIER_CHANGED:markdownFrontMatterIds:{markdown_path}:")
                for finding in identifier_compatibility_findings(expected, mutated)
            )
        )

        schema_path = next(iter(expected["schemaIds"]))
        removed = copy.deepcopy(observed)
        del removed["schemaIds"][schema_path]
        self.assertIn(
            f"IDENTIFIER_MISSING:schemaIds:{schema_path}",
            identifier_compatibility_findings(expected, removed),
        )

    def test_csharp_identifiers_promoted_stable_are_enforced(self):
        additions = self.inventory["stableIdentifierContracts"]["rcStableAdditions"]
        skill = (REPO_ROOT / "languages" / "csharp" / "SKILL.md").read_text(encoding="utf-8")
        skill_name = re.search(r"^name:\s*(\S+)\s*$", skill, flags=re.MULTILINE)
        self.assertIsNotNone(skill_name)
        self.assertEqual(skill_name.group(1), additions["csharpDirectSkillName"])

        for relative, expected_id in additions["csharpFrontMatterIds"].items():
            with self.subTest(path=relative):
                self.assertEqual(markdown_frontmatter_id(REPO_ROOT / relative), expected_id)

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
                path = REPO_ROOT / relative
                with self.subTest(group=group, path=relative):
                    if group == "stableProfileEntryPaths" and not relative.endswith(".md"):
                        self.assertTrue(path.is_dir(), relative)
                    else:
                        self.assertTrue(path.is_file(), relative)

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
        } | {"schemas/v2/completion-result.schema.json"}
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
        contract_relative = source_documents["toolContract"]["path"]
        result_schema_relative = source_documents["toolResultSchema"]["path"]
        contract_path = REPO_ROOT / contract_relative
        result_schema_path = REPO_ROOT / result_schema_relative

        # The checkpoint hashes identify the exact published v0.10.0 source. They
        # must not require the current candidate documents to remain byte-identical.
        published_contract = git_source_at(CHECKPOINT_COMMIT, contract_relative)
        published_schema_text = git_source_at(CHECKPOINT_COMMIT, result_schema_relative)
        self.assertEqual(
            hashlib.sha256(published_contract.encode("utf-8")).hexdigest(),
            source_documents["toolContract"]["sha256"],
        )
        self.assertEqual(
            hashlib.sha256(published_schema_text.encode("utf-8")).hexdigest(),
            source_documents["toolResultSchema"]["sha256"],
        )
        self.assertTrue(contract_path.is_file())
        self.assertTrue(result_schema_path.is_file())

        published_schema = json.loads(published_schema_text)
        schema = json.loads(result_schema_path.read_text(encoding="utf-8"))
        self.assertEqual(schema_contract_findings(published_schema, schema), [])

        result_contract = self.tool_behavior["resultContract"]
        self.assertEqual(set(schema["required"]), set(result_contract["requiredTopLevelFields"]))
        self.assertEqual(set(schema["properties"]["status"]["enum"]), set(result_contract["statusValues"]))
        finding_schema = schema["properties"]["findings"]["items"]
        self.assertEqual(set(finding_schema["required"]), set(result_contract["requiredFindingFields"]))
        self.assertEqual(
            set(finding_schema["properties"]["severity"]["enum"]),
            set(result_contract["findingSeverityValues"]),
        )

    def test_result_schema_allows_optional_additions_but_rejects_breaking_changes(self):
        source = self.tool_behavior["sourceDocuments"]["toolResultSchema"]["path"]
        published = json.loads(git_source_at(CHECKPOINT_COMMIT, source))

        compatible = copy.deepcopy(published)
        compatible["description"] = "Editorial clarification."
        compatible["properties"]["traceId"] = {
            "type": "string",
            "description": "Optional correlation metadata.",
        }
        compatible["properties"]["findings"]["items"]["properties"]["ruleId"] = {
            "type": "string"
        }
        self.assertEqual(schema_contract_findings(published, compatible), [])

        newly_required = copy.deepcopy(compatible)
        newly_required["required"].append("traceId")
        self.assertIn("SCHEMA_REQUIRED_CHANGED:$", schema_contract_findings(published, newly_required))

        changed_type = copy.deepcopy(published)
        changed_type["properties"]["tool"]["type"] = "integer"
        self.assertIn(
            "SCHEMA_CONTRACT_CHANGED:$.properties.tool:type",
            schema_contract_findings(published, changed_type),
        )

        changed_enum = copy.deepcopy(published)
        changed_enum["properties"]["status"]["enum"].append("partial")
        self.assertIn(
            "SCHEMA_ENUM_CHANGED:$.properties.status",
            schema_contract_findings(published, changed_enum),
        )

        changed_extension = copy.deepcopy(published)
        changed_extension["additionalProperties"] = True
        self.assertIn(
            "SCHEMA_CONTRACT_CHANGED:$:additionalProperties",
            schema_contract_findings(published, changed_extension),
        )

        narrowed_existing_property = copy.deepcopy(published)
        narrowed_existing_property["properties"]["tool"]["pattern"] = "^[A-Z]+$"
        self.assertIn(
            "SCHEMA_CONSTRAINT_ADDED:$.properties.tool:pattern",
            schema_contract_findings(published, narrowed_existing_property),
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
        self.assertEqual(self.inventory["compatibilityClassification"], "breaking")
        self.assertTrue(migration["breakingChanges"])
        breaking = "\n".join(migration["breakingChanges"])
        self.assertIn("Site Reliability Engineering", breaking)
        self.assertIn("Testing and Quality Engineering", breaking)
        self.assertIn("Product Management", breaking)
        self.assertIn("User Experience", breaking)
        self.assertIn("GOV-WORK-011", breaking)
        self.assertIn("GOV-WORK-014", breaking)
        self.assertIn("completion-result", breaking)
        self.assertIn("schemaVersion 2.0.0", breaking)
        self.assertGreaterEqual(len(migration["requiredActions"]), 5)
        required_actions = "\n".join(migration["requiredActions"])
        self.assertIn("stop all further execution attempts", required_actions)
        self.assertIn("report unresolved", required_actions)
        self.assertIn(
            "separate authorization from an accountable requester or owner",
            required_actions,
        )
        self.assertIn(
            "material blocker or relevant scope or system-state change",
            required_actions,
        )
        self.assertIn(
            "Failed or Indeterminate read-only execution",
            required_actions,
        )
        self.assertIn("any execution action", required_actions)
        self.assertNotIn("consequential execution action", required_actions)
        self.assertIn("successful evidence-only", required_actions)
        self.assertIn("executionDiscipline", required_actions)
        self.assertIn(
            "at least one passed validation before using validated status",
            required_actions,
        )
        self.assertIn(
            "at least one Successful ledger action for any reported passed validation",
            required_actions,
        )
        self.assertIn("per-objective sequences", required_actions)
        self.assertIn("prior sequence stop/report", required_actions)
        self.assertIn("separate accountable authorization", required_actions)
        self.assertIn("material blocker or relevant scope or system-state change", required_actions)
        review_actions = "\n".join(migration["reviewActions"])
        self.assertIn("completion-result v2", review_actions)
        preserved_contracts = "\n".join(migration["preservedContracts"])
        self.assertIn(
            "schemas/v1/completion-result.schema.json", preserved_contracts
        )
        self.assertGreaterEqual(len(migration["preservedContracts"]), 6)
        notes = (REPO_ROOT / "releases" / "migrations" / f"{CANDIDATE}.md").read_text(encoding="utf-8")
        self.assertIn("# Migration to 1.0.0-rc.1 from 0.10.0", notes)
        self.assertIn("## Required actions", notes)
        self.assertIn("GOV-WORK-011", notes)
        self.assertIn("GOV-WORK-014", notes)
        self.assertIn("The candidate is breaking", notes)
        self.assertNotIn("declares no breaking change", notes)
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
