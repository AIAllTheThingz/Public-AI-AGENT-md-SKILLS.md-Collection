from __future__ import annotations

import subprocess
import tempfile
import unittest
from pathlib import Path

from helpers import REPO_ROOT, json_result, run_tool


class ValidateAllTests(unittest.TestCase):
    def test_list_contains_all_validators(self):
        completed = run_tool("tools/validate-all/run_all.py", "--list")
        self.assertEqual(completed.returncode, 0)
        for validator in (
            "validate-standards",
            "check-links",
            "validate-skills",
            "validate-schemas",
            "validate-templates",
            "validate-tools",
            "validate-release",
        ):
            self.assertIn(validator, completed.stdout)

    def test_single_validator_aggregates(self):
        completed = run_tool("tools/validate-all/run_all.py", "--tool", "validate-standards", "--format", "json")
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
        payload = json_result(completed)
        self.assertEqual(payload["summary"]["validatorsCompleted"], 1)

    def test_release_validator_aggregates(self):
        completed = run_tool("tools/validate-all/run_all.py", "--tool", "validate-release", "--format", "json")
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
        payload = json_result(completed)
        self.assertEqual(payload["summary"]["validatorsCompleted"], 1)
        self.assertEqual(payload["metadata"]["results"][0]["tool"], "validate-release")

    def test_skill_validator_aggregates(self):
        completed = run_tool("tools/validate-all/run_all.py", "--tool", "validate-skills", "--format", "json")
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
        payload = json_result(completed)
        self.assertEqual(payload["summary"]["validatorsCompleted"], 1)
        self.assertEqual(payload["metadata"]["results"][0]["tool"], "validate-skills")

    def test_compatibility_history_uses_temporary_git_metadata_for_archives(self):
        import importlib.util
        import shutil

        module_path = REPO_ROOT / "tools" / "validate-all" / "run_all.py"
        spec = importlib.util.spec_from_file_location("validate_all_portability", module_path)
        module = importlib.util.module_from_spec(spec)
        assert spec.loader is not None
        spec.loader.exec_module(module)

        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            bundle_target = root / module.COMPATIBILITY_HISTORY_BUNDLE
            bundle_target.parent.mkdir(parents=True)
            shutil.copy2(REPO_ROOT / module.COMPATIBILITY_HISTORY_BUNDLE, bundle_target)

            self.assertFalse((root / ".git").exists())
            with module.compatibility_history(root):
                self.assertFalse(
                    (root / ".git").exists(),
                    "archive compatibility bootstrap must not create Git metadata in the source root",
                )
                for commit in module.COMPATIBILITY_HISTORY_REFS:
                    completed = subprocess.run(
                        ["git", "-C", str(root), "cat-file", "-e", f"{commit}^{{commit}}"],
                        text=True,
                        capture_output=True,
                        check=False,
                    )
                    self.assertEqual(completed.returncode, 0, completed.stderr)

            self.assertFalse(
                (root / ".git").exists(),
                "validation must leave an extracted source archive free of Git metadata",
            )


if __name__ == "__main__":
    unittest.main()
