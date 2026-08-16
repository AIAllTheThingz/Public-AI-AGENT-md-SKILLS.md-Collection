from __future__ import annotations

import copy
import json
import re
import tempfile
import unittest
from pathlib import Path

from helpers import REPO_ROOT, json_result, run_tool


CANDIDATES_PATH = REPO_ROOT / "adoption-tests" / "candidates.json"
FIXTURES_ROOT = REPO_ROOT / "adoption-tests" / "fixtures"
HEX_SHA256 = re.compile(r"^[0-9a-f]{64}$")


def load_candidates() -> dict:
    return json.loads(CANDIDATES_PATH.read_text(encoding="utf-8"))


def load_fixture(candidate_id: str) -> dict:
    return json.loads((FIXTURES_ROOT / f"{candidate_id}.json").read_text(encoding="utf-8"))


def candidate_findings(candidate: dict, manifest: dict, evidence: dict) -> list[str]:
    findings: list[str] = []
    selected_languages = set(manifest.get("languages", []))
    for language in candidate.get("languages", []):
        if language not in selected_languages:
            findings.append(f"LANGUAGE_MISSING:{language}")
    for language in candidate.get("requiredCompanionLanguages", []):
        if language not in selected_languages:
            findings.append(f"COMPANION_LANGUAGE_MISSING:{language}")
    if not manifest.get("disciplines"):
        findings.append("DISCIPLINES_MISSING")
    for key in candidate.get("requiredEvidence", []):
        value = evidence.get(key)
        if value is None or value == "" or value == []:
            findings.append(f"EVIDENCE_MISSING:{key}")
    for key, allowed in candidate.get("allowedEvidenceValues", {}).items():
        value = evidence.get(key)
        if value not in allowed:
            findings.append(f"EVIDENCE_INVALID:{key}")
    return findings


def manifest_args(candidate: dict, *, languages: list[str] | None = None) -> list[str]:
    args = [
        "--name", f"adoption-{candidate['id']}",
        "--profile", candidate["profile"],
    ]
    for language in languages if languages is not None else candidate["languages"]:
        args.extend(["--language", language])
    args.extend(["--include-profile-required", "--format", "json"])
    return args


class PackageAdoptionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.registry = load_candidates()
        cls.candidates = cls.registry["candidates"]
        cls.source_reviews = {
            record["id"]: record
            for record in json.loads((REPO_ROOT / "SOURCE_REVIEWS.json").read_text(encoding="utf-8"))["records"]
        }

    def test_registry_pins_published_release_boundary(self):
        self.assertEqual(self.registry["publishedRelease"], "v0.10.0")
        self.assertEqual(
            self.registry["publishedSourceCommit"],
            "83c73f3ab9a049ff2321d463164fcf98fb453a9c",
        )
        self.assertEqual(
            {item["id"] for item in self.candidates},
            {"csharp-modern-dotnet", "powershell-internal-automation", "terraform-opentofu-infrastructure"},
        )

    def test_candidate_source_reviews_are_accountable(self):
        for candidate in self.candidates:
            for record_id in candidate["sourceReviewIds"]:
                with self.subTest(candidate=candidate["id"], source_review=record_id):
                    record = self.source_reviews[record_id]
                    self.assertIsNotNone(record["lastReviewed"])
                    evidence = REPO_ROOT / record["reviewEvidence"]
                    self.assertTrue(evidence.is_file(), record)
                    self.assertIn(record["lastReviewed"], evidence.name)

    def test_positive_selection_and_composition_are_traceable(self):
        for candidate in self.candidates:
            with self.subTest(candidate=candidate["id"]):
                dry_run = run_tool(
                    "tools/generate-manifest/generate_manifest.py",
                    *manifest_args(candidate),
                    "--dry-run",
                )
                self.assertEqual(dry_run.returncode, 0, dry_run.stdout + dry_run.stderr)
                manifest = json_result(dry_run)["metadata"]["manifest"]
                fixture = load_fixture(candidate["id"])
                self.assertEqual(candidate_findings(candidate, manifest, fixture), [])
                self.assertTrue(manifest["disciplines"])

                with tempfile.TemporaryDirectory(dir=REPO_ROOT) as temp:
                    temp_root = Path(temp)
                    manifest_path = temp_root / "project-manifest.json"
                    bundle_path = temp_root / "bundle"
                    generated = run_tool(
                        "tools/generate-manifest/generate_manifest.py",
                        *manifest_args(candidate),
                        "--manifest-output", str(manifest_path),
                    )
                    self.assertEqual(generated.returncode, 0, generated.stdout + generated.stderr)
                    composed = run_tool(
                        "tools/compose-agents/compose_agents.py",
                        "--manifest", str(manifest_path),
                        "--output-dir", str(bundle_path),
                        "--format", "json",
                    )
                    self.assertEqual(composed.returncode, 0, composed.stdout + composed.stderr)
                    composition = json.loads((bundle_path / "COMPOSITION_MANIFEST.json").read_text(encoding="utf-8"))
                    source_records = {record["path"]: record["sha256"] for record in composition["sources"]}
                    for required_path in candidate["requiredSourcePaths"]:
                        self.assertIn(required_path, source_records)
                        self.assertRegex(source_records[required_path], HEX_SHA256)
                    self.assertTrue((bundle_path / "AGENTS.md").is_file())
                    self.assertTrue((bundle_path / "TAILORING_CHECKLIST.md").is_file())

    def test_missing_candidate_evidence_is_incomplete(self):
        for candidate in self.candidates:
            completed = run_tool(
                "tools/generate-manifest/generate_manifest.py",
                *manifest_args(candidate),
                "--dry-run",
            )
            self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
            manifest = json_result(completed)["metadata"]["manifest"]
            fixture = load_fixture(candidate["id"])
            for key in candidate["requiredEvidence"]:
                with self.subTest(candidate=candidate["id"], missing=key):
                    incomplete = copy.deepcopy(fixture)
                    incomplete.pop(key, None)
                    self.assertIn(f"EVIDENCE_MISSING:{key}", candidate_findings(candidate, manifest, incomplete))

    def test_csharp_modern_candidate_requires_dotnet_companion(self):
        candidate = next(item for item in self.candidates if item["id"] == "csharp-modern-dotnet")
        completed = run_tool(
            "tools/generate-manifest/generate_manifest.py",
            *manifest_args(candidate, languages=["csharp"]),
            "--dry-run",
        )
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
        manifest = json_result(completed)["metadata"]["manifest"]
        findings = candidate_findings(candidate, manifest, load_fixture(candidate["id"]))
        self.assertIn("COMPANION_LANGUAGE_MISSING:dotnet", findings)

    def test_invalid_package_selection_is_rejected_for_each_candidate(self):
        for candidate in self.candidates:
            bad_slug = f"{candidate['languages'][0]}-missing-package"
            with self.subTest(candidate=candidate["id"]):
                completed = run_tool(
                    "tools/generate-manifest/generate_manifest.py",
                    "--name", f"invalid-{candidate['id']}",
                    "--profile", candidate["profile"],
                    "--language", bad_slug,
                    "--include-profile-required",
                    "--dry-run",
                    "--format", "json",
                )
                self.assertEqual(completed.returncode, 2, completed.stdout + completed.stderr)

    def test_bundle_overwrite_requires_force_for_each_candidate(self):
        for candidate in self.candidates:
            with self.subTest(candidate=candidate["id"]), tempfile.TemporaryDirectory(dir=REPO_ROOT) as temp:
                temp_root = Path(temp)
                manifest_path = temp_root / "project-manifest.json"
                bundle_path = temp_root / "bundle"
                generated = run_tool(
                    "tools/generate-manifest/generate_manifest.py",
                    *manifest_args(candidate),
                    "--manifest-output", str(manifest_path),
                )
                self.assertEqual(generated.returncode, 0, generated.stdout + generated.stderr)
                first = run_tool(
                    "tools/compose-agents/compose_agents.py",
                    "--manifest", str(manifest_path),
                    "--output-dir", str(bundle_path),
                    "--format", "json",
                )
                self.assertEqual(first.returncode, 0, first.stdout + first.stderr)
                second = run_tool(
                    "tools/compose-agents/compose_agents.py",
                    "--manifest", str(manifest_path),
                    "--output-dir", str(bundle_path),
                    "--format", "json",
                )
                self.assertEqual(second.returncode, 2, second.stdout + second.stderr)

    def test_invalid_terraform_engine_evidence_is_rejected(self):
        candidate = next(item for item in self.candidates if item["id"] == "terraform-opentofu-infrastructure")
        completed = run_tool(
            "tools/generate-manifest/generate_manifest.py",
            *manifest_args(candidate),
            "--dry-run",
        )
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
        manifest = json_result(completed)["metadata"]["manifest"]
        fixture = load_fixture(candidate["id"])
        fixture["engine"] = "both"
        self.assertIn("EVIDENCE_INVALID:engine", candidate_findings(candidate, manifest, fixture))


if __name__ == "__main__":
    unittest.main()
