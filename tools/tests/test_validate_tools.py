from __future__ import annotations

import shutil
import tempfile
import unittest
from pathlib import Path

from helpers import REPO_ROOT, json_result, run_tool


class ValidateToolsTests(unittest.TestCase):
    def copy_repo(self, temp: str) -> Path:
        root = Path(temp) / "repo"
        shutil.copytree(
            REPO_ROOT,
            root,
            ignore=shutil.ignore_patterns(".git", "__pycache__", "*.pyc"),
        )
        return root

    def test_tool_packages_pass(self):
        completed = run_tool("tools/validate-tools/validate_tools.py", "--format", "json")
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
        self.assertEqual(json_result(completed)["status"], "passed")

    def test_dependency_lock_requires_exact_direct_requirement(self):
        with tempfile.TemporaryDirectory() as temp:
            root = self.copy_repo(temp)
            (root / "tools" / "validate-schemas" / "requirements.txt").write_text(
                "jsonschema[format]==4.2\nPyYAML==6.0.3\n",
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

    def test_dependency_lock_detects_removed_direct_requirement(self):
        with tempfile.TemporaryDirectory() as temp:
            root = self.copy_repo(temp)
            (root / "tools" / "validate-schemas" / "requirements.txt").write_text(
                "jsonschema[format]==4.26.0\n",
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
            self.assertTrue(
                any("pyyaml==6.0.3" in finding["message"] for finding in payload["findings"]),
                payload["findings"],
            )

    def test_dependency_lock_accepts_inline_comment_on_direct_requirement(self):
        with tempfile.TemporaryDirectory() as temp:
            root = self.copy_repo(temp)
            (root / "tools" / "validate-schemas" / "requirements.txt").write_text(
                "jsonschema[format]==4.26.0  # schema validation\n"
                "PyYAML==6.0.3  # workflow parsing\n",
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

    def test_quoted_workflow_action_sha_is_accepted(self):
        with tempfile.TemporaryDirectory() as temp:
            root = self.copy_repo(temp)
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

    def test_workflow_yaml_key_spacing_cannot_bypass_pin_checks(self):
        with tempfile.TemporaryDirectory() as temp:
            root = self.copy_repo(temp)
            workflow = root / ".github" / "workflows" / "spaced-keys.yml"
            workflow.write_text(
                "name: Spaced key test\n"
                "on: workflow_dispatch\n"
                "permissions:\n"
                "  contents: read\n"
                "jobs:\n"
                "  test:\n"
                "    runs-on : ubuntu-latest\n"
                "    steps:\n"
                "      - uses : actions/checkout@v7\n",
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
            self.assertIn("WORKFLOW_ACTION_NOT_PINNED", codes)
            self.assertIn("WORKFLOW_RUNNER_FLOATING", codes)

    def test_matrix_runner_expression_checks_declared_values(self):
        with tempfile.TemporaryDirectory() as temp:
            root = self.copy_repo(temp)
            workflow = root / ".github" / "workflows" / "matrix-runner.yml"
            workflow.write_text(
                "name: Matrix runner pin test\n"
                "on: workflow_dispatch\n"
                "permissions:\n"
                "  contents: read\n"
                "jobs:\n"
                "  test:\n"
                "    strategy:\n"
                "      matrix:\n"
                "        os: [ubuntu-24.04, ubuntu-latest]\n"
                "    runs-on: ${{ matrix.os }}\n"
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
            payload = json_result(completed)
            codes = {finding["code"] for finding in payload["findings"]}

            self.assertEqual(completed.returncode, 1, completed.stdout + completed.stderr)
            self.assertIn("WORKFLOW_RUNNER_FLOATING", codes)

    def test_unresolved_runner_expression_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            root = self.copy_repo(temp)
            workflow = root / ".github" / "workflows" / "dynamic-runner.yml"
            workflow.write_text(
                "name: Dynamic runner test\n"
                "on:\n"
                "  workflow_dispatch:\n"
                "    inputs:\n"
                "      runner:\n"
                "        required: true\n"
                "        type: string\n"
                "permissions:\n"
                "  contents: read\n"
                "jobs:\n"
                "  test:\n"
                "    runs-on: ${{ inputs.runner }}\n"
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
            payload = json_result(completed)
            codes = {finding["code"] for finding in payload["findings"]}

            self.assertEqual(completed.returncode, 1, completed.stdout + completed.stderr)
            self.assertIn("WORKFLOW_RUNNER_UNRESOLVED", codes)

    def test_non_action_uses_key_is_ignored(self):
        with tempfile.TemporaryDirectory() as temp:
            root = self.copy_repo(temp)
            workflow = root / ".github" / "workflows" / "input-named-uses.yml"
            workflow.write_text(
                "name: Non-action uses key test\n"
                "on:\n"
                "  workflow_dispatch:\n"
                "    inputs:\n"
                "      uses:\n"
                "        description: Not an action reference\n"
                "        required: false\n"
                "        type: string\n"
                "permissions:\n"
                "  contents: read\n"
                "jobs:\n"
                "  test:\n"
                "    runs-on: ubuntu-24.04\n"
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

    def test_docker_action_sha256_digest_is_accepted(self):
        with tempfile.TemporaryDirectory() as temp:
            root = self.copy_repo(temp)
            workflow = root / ".github" / "workflows" / "docker-action.yml"
            digest = "a" * 64
            workflow.write_text(
                "name: Docker digest test\n"
                "on: workflow_dispatch\n"
                "permissions:\n"
                "  contents: read\n"
                "jobs:\n"
                "  test:\n"
                "    runs-on: ubuntu-24.04\n"
                "    steps:\n"
                f"      - uses: docker://alpine@sha256:{digest}\n",
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
