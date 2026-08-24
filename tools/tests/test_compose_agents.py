from __future__ import annotations

import json
import shutil
import tempfile
import unittest
from pathlib import Path

from helpers import REPO_ROOT, json_result, run_tool


class ComposeAgentsTests(unittest.TestCase):
    def test_dry_run_builds_traceable_plan(self):
        with tempfile.TemporaryDirectory(dir=REPO_ROOT) as temp:
            manifest = Path(temp) / "project-manifest.json"
            manifest.write_text(json.dumps({
                "schemaVersion": "1.0.0",
                "name": "example-service",
                "profile": "WEB_API",
                "languages": ["python"],
                "disciplines": ["testing"],
            }), encoding="utf-8")
            completed = run_tool(
                "tools/compose-agents/compose_agents.py",
                "--manifest", str(manifest),
                "--dry-run",
                "--format", "json",
            )
            self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
            payload = json_result(completed)
            self.assertGreater(payload["summary"]["sources"], 5)
            self.assertFalse(payload["summary"]["written"])

    def test_dry_run_includes_infrastructure_packages(self):
        with tempfile.TemporaryDirectory(dir=REPO_ROOT) as temp:
            manifest = Path(temp) / "project-manifest.json"
            manifest.write_text(json.dumps({
                "schemaVersion": "1.1.0",
                "name": "infrastructure-service",
                "profile": "INTERNAL_AUTOMATION",
                "languages": ["python"],
                "disciplines": ["testing"],
                "virtualization": ["kvm-libvirt"],
                "operatingSystems": ["ubuntu"],
                "networking": ["cisco-networking"],
            }), encoding="utf-8")
            completed = run_tool(
                "tools/compose-agents/compose_agents.py",
                "--manifest", str(manifest),
                "--dry-run",
                "--format", "json",
            )
            self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
            payload = json_result(completed)
            source_paths = {
                item["path"] for item in payload["metadata"]["composition"]["sources"]
            }
            self.assertIn("virtualization/kvm-libvirt/AGENTS.md", source_paths)
            self.assertIn("operating-systems/ubuntu/AGENTS.md", source_paths)
            self.assertIn("networking/cisco-networking/AGENTS.md", source_paths)

    def test_dry_run_includes_selected_governance_sources(self):
        completed = run_tool(
            "tools/compose-agents/compose_agents.py",
            "--manifest", "examples/full-stack/project-manifest.json",
            "--dry-run",
            "--format", "json",
        )
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
        payload = json_result(completed)
        source_paths = {
            item["path"] for item in payload["metadata"]["composition"]["sources"]
        }
        self.assertIn("governance/PRODUCT_INCEPTION_LIFECYCLE.md", source_paths)
        self.assertIn("governance/EXCEPTION_PROCESS.md", source_paths)
        for dependency in (
            "MATURITY_POLICY.md",
            "SOURCE_REVIEWS.json",
            "source-reviews/README.md",
            "disciplines/product-management/README.md",
            "disciplines/product-management/standards/TRACEABILITY_STANDARD.md",
            "disciplines/product-management/templates/EVIDENCE_RECORD_TEMPLATE.md",
            "disciplines/sre/README.md",
            "disciplines/sre/standards/CAPACITY_PERFORMANCE_STANDARD.md",
            "disciplines/sre/standards/PRODUCTION_READINESS_STANDARD.md",
            "disciplines/sre/standards/SCALING_STRATEGY_STANDARD.md",
            "disciplines/sre/templates/EVIDENCE_RECORD_TEMPLATE.md",
            "source-reviews/2026-08-15.md",
            "source-reviews/2026-08-23.md",
        ):
            with self.subTest(governance_dependency=dependency):
                self.assertIn(dependency, source_paths)

    def test_copy_sources_includes_lifecycle_required_contracts(self):
        with tempfile.TemporaryDirectory(dir=REPO_ROOT) as temp:
            output = Path(temp) / "bundle"
            completed = run_tool(
                "tools/compose-agents/compose_agents.py",
                "--manifest", "examples/web-api/project-manifest.json",
                "--output-dir", str(output),
                "--format", "json",
            )
            self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
            for dependency in (
                "disciplines/product-management/standards/TRACEABILITY_STANDARD.md",
                "disciplines/product-management/templates/EVIDENCE_RECORD_TEMPLATE.md",
                "disciplines/sre/standards/CAPACITY_PERFORMANCE_STANDARD.md",
                "disciplines/sre/standards/PRODUCTION_READINESS_STANDARD.md",
                "disciplines/sre/standards/SCALING_STRATEGY_STANDARD.md",
                "disciplines/sre/templates/EVIDENCE_RECORD_TEMPLATE.md",
                "source-reviews/2026-08-23.md",
            ):
                with self.subTest(copied_lifecycle_contract=dependency):
                    self.assertTrue((output / "sources" / dependency).is_file())

    def test_normalizes_governance_selection_before_dependency_lookup(self):
        with tempfile.TemporaryDirectory(dir=REPO_ROOT) as temp:
            manifest = Path(temp) / "project-manifest.json"
            output = Path(temp) / "bundle"
            manifest.write_text(json.dumps({
                "schemaVersion": "1.1.0",
                "name": "normalized-governance-selection",
                "profile": "WEB_API",
                "languages": ["python"],
                "disciplines": ["testing"],
                "extensions": {
                    "AIAllTheThingz.governanceSelections": [
                        "governance/sub/../PRODUCT_INCEPTION_LIFECYCLE.md"
                    ],
                },
            }), encoding="utf-8")
            completed = run_tool(
                "tools/compose-agents/compose_agents.py",
                "--manifest", str(manifest),
                "--output-dir", str(output),
                "--no-copy-sources",
                "--format", "json",
            )
            self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
            payload = json_result(completed)
            source_paths = {
                item["path"] for item in payload["metadata"]["composition"]["sources"]
            }
            self.assertIn(
                "disciplines/sre/standards/CAPACITY_PERFORMANCE_STANDARD.md",
                source_paths,
            )
            self.assertIn("source-reviews/2026-08-23.md", source_paths)
            index = (output / "AGENTS.md").read_text(encoding="utf-8")
            self.assertIn(
                "- Governance selections: "
                "`governance/PRODUCT_INCEPTION_LIFECYCLE.md`",
                index,
            )
            self.assertNotIn(
                "governance/sub/../PRODUCT_INCEPTION_LIFECYCLE.md",
                index,
            )

    def test_missing_lifecycle_dependency_is_an_input_error(self):
        with tempfile.TemporaryDirectory(dir=REPO_ROOT) as temp:
            temp_path = Path(temp)
            schema = temp_path / "schemas" / "v1" / "project-manifest.schema.json"
            schema.parent.mkdir(parents=True)
            shutil.copy2(
                REPO_ROOT / "schemas" / "v1" / "project-manifest.schema.json",
                schema,
            )
            for relative in (
                "governance/ORGANIZATION_CONTRACT.md",
                "governance/AGENT_WORKING_METHOD.md",
                "governance/RISK_CLASSIFICATION.md",
                "governance/COMPLETION_EVIDENCE.md",
                "governance/EXCEPTION_PROCESS.md",
                "governance/AI_GENERATED_CODE_POLICY.md",
                "governance/HUMAN_REVIEW_POLICY.md",
                "governance/PRODUCTION_READINESS.md",
                "governance/PRODUCT_INCEPTION_LIFECYCLE.md",
            ):
                path = temp_path / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("# Test source\n", encoding="utf-8")

            manifest = temp_path / "project-manifest.json"
            manifest.write_text(json.dumps({
                "schemaVersion": "1.1.0",
                "name": "missing-lifecycle-dependency",
                "profile": "WEB_API",
                "languages": ["python"],
                "disciplines": ["testing"],
                "extensions": {
                    "AIAllTheThingz.governanceSelections": [
                        "governance/PRODUCT_INCEPTION_LIFECYCLE.md"
                    ],
                },
            }), encoding="utf-8")
            completed = run_tool(
                "tools/compose-agents/compose_agents.py",
                "--manifest", str(manifest),
                "--dry-run",
                "--format", "json",
                root=temp_path,
            )
            self.assertEqual(completed.returncode, 2, completed.stdout + completed.stderr)
            payload = json_result(completed)
            self.assertEqual(payload["findings"][0]["code"], "INPUT_ERROR")
            self.assertIn(
                "Required dependency for selected governance source "
                "'governance/PRODUCT_INCEPTION_LIFECYCLE.md' is missing: "
                "MATURITY_POLICY.md",
                payload["findings"][0]["message"],
            )

    def test_written_index_reports_governance_selections(self):
        with tempfile.TemporaryDirectory(dir=REPO_ROOT) as temp:
            output = Path(temp) / "bundle"
            completed = run_tool(
                "tools/compose-agents/compose_agents.py",
                "--manifest", "examples/web-api/project-manifest.json",
                "--output-dir", str(output),
                "--no-copy-sources",
                "--format", "json",
            )
            self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
            index = (output / "AGENTS.md").read_text(encoding="utf-8")
            self.assertIn(
                "- Governance selections: "
                "`governance/PRODUCT_INCEPTION_LIFECYCLE.md`",
                index,
            )

    def test_rejects_governance_selection_outside_governance(self):
        with tempfile.TemporaryDirectory(dir=REPO_ROOT) as temp:
            manifest = Path(temp) / "project-manifest.json"
            manifest.write_text(json.dumps({
                "schemaVersion": "1.1.0",
                "name": "invalid-governance-selection",
                "profile": "WEB_API",
                "languages": ["python"],
                "disciplines": ["testing"],
                "extensions": {
                    "AIAllTheThingz.governanceSelections": ["README.md"],
                },
            }), encoding="utf-8")
            completed = run_tool(
                "tools/compose-agents/compose_agents.py",
                "--manifest", str(manifest),
                "--dry-run",
                "--format", "json",
            )
            self.assertEqual(completed.returncode, 2)

    def test_rejects_missing_governance_selection(self):
        with tempfile.TemporaryDirectory(dir=REPO_ROOT) as temp:
            manifest = Path(temp) / "project-manifest.json"
            manifest.write_text(json.dumps({
                "schemaVersion": "1.1.0",
                "name": "missing-governance-selection",
                "profile": "WEB_API",
                "languages": ["python"],
                "disciplines": ["testing"],
                "extensions": {
                    "AIAllTheThingz.governanceSelections": [
                        "governance/DOES_NOT_EXIST.md"
                    ],
                },
            }), encoding="utf-8")
            completed = run_tool(
                "tools/compose-agents/compose_agents.py",
                "--manifest", str(manifest),
                "--dry-run",
                "--format", "json",
            )
            self.assertEqual(completed.returncode, 2)

    def test_written_index_reports_infrastructure_selections(self):
        with tempfile.TemporaryDirectory(dir=REPO_ROOT) as temp:
            temp_path = Path(temp)
            manifest = temp_path / "project-manifest.json"
            output = temp_path / "bundle"
            manifest.write_text(json.dumps({
                "schemaVersion": "1.1.0",
                "name": "infrastructure-service",
                "profile": "INTERNAL_AUTOMATION",
                "languages": ["python"],
                "disciplines": ["testing"],
                "virtualization": ["kvm-libvirt"],
                "operatingSystems": ["ubuntu"],
                "networking": ["cisco-networking"],
            }), encoding="utf-8")
            completed = run_tool(
                "tools/compose-agents/compose_agents.py",
                "--manifest", str(manifest),
                "--output-dir", str(output),
                "--no-copy-sources",
                "--format", "json",
            )
            self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
            index = (output / "AGENTS.md").read_text(encoding="utf-8")
            self.assertIn("- Virtualization: `kvm-libvirt`", index)
            self.assertIn("- Operating systems: `ubuntu`", index)
            self.assertIn("- Networking: `cisco-networking`", index)

    def test_rejects_infrastructure_arrays_in_version_1_0_manifest(self):
        with tempfile.TemporaryDirectory(dir=REPO_ROOT) as temp:
            manifest = Path(temp) / "project-manifest.json"
            manifest.write_text(json.dumps({
                "schemaVersion": "1.0.0",
                "name": "invalid-infrastructure-service",
                "profile": "INTERNAL_AUTOMATION",
                "languages": ["python"],
                "disciplines": ["testing"],
                "operatingSystems": ["ubuntu"],
            }), encoding="utf-8")
            completed = run_tool(
                "tools/compose-agents/compose_agents.py",
                "--manifest", str(manifest),
                "--dry-run",
                "--format", "json",
            )
            self.assertEqual(completed.returncode, 2)


if __name__ == "__main__":
    unittest.main()
