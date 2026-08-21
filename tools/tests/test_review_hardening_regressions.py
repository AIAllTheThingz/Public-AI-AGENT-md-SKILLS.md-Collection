from __future__ import annotations

import os
import shutil
import tempfile
import unittest
from pathlib import Path

from helpers import REPO_ROOT, json_result, run_tool


class ReviewHardeningRegressionTests(unittest.TestCase):
    def copy_repo(self, temp: str) -> Path:
        root = Path(temp) / "repo"
        shutil.copytree(
            REPO_ROOT,
            root,
            ignore=shutil.ignore_patterns(".git", "__pycache__", "*.pyc"),
        )
        return root

    def test_dependency_lock_accepts_canonical_equivalent_project_name(self):
        with tempfile.TemporaryDirectory() as temp:
            root = self.copy_repo(temp)
            requirements = root / "tools" / "validate-schemas" / "requirements.txt"
            lock = root / "tools" / "validate-schemas" / "requirements.lock"

            requirements.write_text(
                requirements.read_text(encoding="utf-8") + "example_package==1.0\n",
                encoding="utf-8",
            )
            lock.write_text(
                lock.read_text(encoding="utf-8")
                + "\nexample-package==1.0 \\\n"
                + f"    --hash=sha256:{'a' * 64}\n"
                + "    # via -r tools/validate-schemas/requirements.txt\n",
                encoding="utf-8",
            )

            completed = run_tool(
                "tools/validate-tools/validate_tools.py",
                "--format",
                "json",
                root=root,
            )

            self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
            self.assertEqual(json_result(completed)["status"], "passed")

    def test_self_hosted_latest_suffix_label_is_not_treated_as_hosted_alias(self):
        with tempfile.TemporaryDirectory() as temp:
            root = self.copy_repo(temp)
            workflow = root / ".github" / "workflows" / "self-hosted-label.yml"
            workflow.write_text(
                "name: Self-hosted label test\n"
                "on: workflow_dispatch\n"
                "permissions:\n"
                "  contents: read\n"
                "jobs:\n"
                "  test:\n"
                "    runs-on: [self-hosted, build-latest]\n"
                "    steps:\n"
                "      - uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1\n",
                encoding="utf-8",
            )

            completed = run_tool(
                "tools/validate-tools/validate_tools.py",
                "--format",
                "json",
                root=root,
            )

            self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
            self.assertEqual(json_result(completed)["status"], "passed")

    def test_workflow_symlink_outside_root_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            root = self.copy_repo(temp)
            outside = Path(temp) / "outside-workflow.yml"
            outside.write_text(
                "name: Outside workflow\n"
                "on: workflow_dispatch\n"
                "permissions:\n"
                "  contents: read\n"
                "jobs:\n"
                "  test:\n"
                "    runs-on: ubuntu-24.04\n"
                "    steps:\n"
                "      - uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1\n",
                encoding="utf-8",
            )
            linked = root / ".github" / "workflows" / "outside-link.yml"
            try:
                linked.symlink_to(outside)
            except OSError as exc:
                if os.name == "nt" and exc.winerror == 1314:
                    self.skipTest("symlink creation requires a Windows privilege not available here")
                raise

            completed = run_tool(
                "tools/validate-tools/validate_tools.py",
                "--format",
                "json",
                root=root,
            )
            payload = json_result(completed)

            self.assertEqual(completed.returncode, 1, completed.stdout + completed.stderr)
            self.assertTrue(
                any(
                    finding["code"] == "WORKFLOW_YAML_OUTSIDE_ROOT"
                    and finding["path"] == ".github/workflows/outside-link.yml"
                    for finding in payload["findings"]
                ),
                payload["findings"],
            )

    def test_validate_schemas_structured_version_matches_package_metadata(self):
        completed = run_tool("tools/validate-schemas/validate_schemas.py", "--format", "json")
        payload = json_result(completed)

        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
        self.assertEqual(payload["version"], "1.1.0")


if __name__ == "__main__":
    unittest.main()
