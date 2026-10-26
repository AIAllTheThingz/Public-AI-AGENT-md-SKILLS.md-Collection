from __future__ import annotations

import unittest

from helpers import json_result, run_tool


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


if __name__ == "__main__":
    unittest.main()
