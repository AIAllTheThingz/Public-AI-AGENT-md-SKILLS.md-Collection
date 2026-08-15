from __future__ import annotations

import shutil
import tempfile
import unittest
from pathlib import Path

from helpers import REPO_ROOT, json_result, run_tool


class ValidateToolsTests(unittest.TestCase):
    def test_tool_packages_pass(self):
        completed = run_tool("tools/validate-tools/validate_tools.py", "--format", "json")
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
        self.assertEqual(json_result(completed)["status"], "passed")

    def test_dependency_lock_requires_exact_direct_requirement(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "repo"
            shutil.copytree(
                REPO_ROOT,
                root,
                ignore=shutil.ignore_patterns(".git", "__pycache__", "*.pyc"),
            )
            (root / "tools" / "validate-schemas" / "requirements.txt").write_text(
                "jsonschema[format]==4.2\n",
                encoding="utf-8",
            )

            completed = run_tool(
                "tools/validate-tools/validate_tools.py",
                "--format",
                "json",
                root=root,
            )
            payload = json_result(completed)
            codes = {finding["code"] for finding in payload["findings"]}

            self.assertEqual(completed.returncode, 1, completed.stdout + completed.stderr)
            self.assertIn("DEPENDENCY_LOCK_OUT_OF_SYNC", codes)

    def test_quoted_workflow_action_sha_is_accepted(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "repo"
            shutil.copytree(
                REPO_ROOT,
                root,
                ignore=shutil.ignore_patterns(".git", "__pycache__", "*.pyc"),
            )
            workflow = root / ".github" / "workflows" / "quoted-action.yml"
            workflow.write_text(
                "name: Quoted action pin test\n"
                "on: workflow_dispatch\n"
                "permissions:\n"
                "  contents: read\n"
                "jobs:\n"
                "  test:\n"
                "    runs-on: 'ubuntu-24.04'\n"
                "    steps:\n"
                "      - uses: 'actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1'\n",
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


if __name__ == "__main__":
    unittest.main()
