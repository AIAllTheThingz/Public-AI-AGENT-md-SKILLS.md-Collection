from __future__ import annotations

import json
import shutil
import tempfile
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker

from helpers import REPO_ROOT, json_result, run_tool


def completion_v2() -> tuple[dict, dict]:
    schema = json.loads(
        (REPO_ROOT / "schemas/v2/completion-result.schema.json").read_text(
            encoding="utf-8"
        )
    )
    instance = json.loads(
        (REPO_ROOT / "schemas/examples/completion-result/valid.example.json").read_text(
            encoding="utf-8"
        )
    )
    return schema, instance


def ledger_action(result: str, budget_position: str, terminal_disposition: str) -> dict:
    return {
        "action": "fictitious action",
        "actor": "fictitious-agent",
        "executionContext": {"tool": "fictitious-tool"},
        "startedAt": "2026-01-01T00:00:00Z",
        "endedAt": "2026-01-01T00:01:00Z",
        "effectsReconciliation": "No state changed.",
        "result": result,
        "budgetPosition": budget_position,
        "justification": "Fictitious test action.",
        "terminalDisposition": terminal_disposition,
    }


class ValidateSchemasTests(unittest.TestCase):
    def test_repository_schema_system_passes(self):
        completed = run_tool("tools/validate-schemas/validate_schemas.py", "--format", "json")
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
        self.assertEqual(json_result(completed)["status"], "passed")

    def test_completion_result_v1_fixture_remains_valid(self):
        schema = json.loads(
            (REPO_ROOT / "schemas/v1/completion-result.schema.json").read_text(
                encoding="utf-8"
            )
        )
        instance = json.loads(
            (REPO_ROOT / "schemas/examples/completion-result/valid-v1.example.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(
            list(Draft202012Validator(schema, format_checker=FormatChecker()).iter_errors(instance)),
            [],
        )

    def test_completion_result_v2_fixture_is_valid_and_matches_rolling_schema(self):
        schema = json.loads(
            (REPO_ROOT / "schemas/v2/completion-result.schema.json").read_text(
                encoding="utf-8"
            )
        )
        instance = json.loads(
            (REPO_ROOT / "schemas/examples/completion-result/valid.example.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(
            list(Draft202012Validator(schema, format_checker=FormatChecker()).iter_errors(instance)),
            [],
        )

        rolling = json.loads(
            (REPO_ROOT / "schemas/completion-result.schema.json").read_text(
                encoding="utf-8"
            )
        )
        for metadata in ("$id", "x-versionedSchema"):
            rolling.pop(metadata, None)
            schema.pop(metadata, None)
        self.assertEqual(rolling, schema)

    def test_completion_result_v2_requires_execution_discipline(self):
        schema = json.loads(
            (REPO_ROOT / "schemas/v2/completion-result.schema.json").read_text(
                encoding="utf-8"
            )
        )
        instance = json.loads(
            (REPO_ROOT / "schemas/examples/completion-result/valid.example.json").read_text(
                encoding="utf-8"
            )
        )
        del instance["executionDiscipline"]
        errors = list(Draft202012Validator(schema).iter_errors(instance))
        self.assertTrue(any(error.validator == "required" for error in errors))

    def test_failed_retry_cannot_be_non_consuming(self):
        schema, instance = completion_v2()
        instance["executionDiscipline"]["retryLedger"] = {
            "fictitious objective": {
                "attempts": {},
                "nonConsumingActions": [
                    ledger_action("Failed", "non-consuming", "not-terminal")
                ],
            }
        }
        self.assertTrue(list(Draft202012Validator(schema).iter_errors(instance)))

    def test_failed_initial_then_successful_retry_is_valid(self):
        schema, instance = completion_v2()
        instance["executionDiscipline"]["retryLedger"] = {
            "fictitious objective": {
                "attempts": {
                    "initialAttempt": ledger_action(
                        "Failed", "initial-attempt", "retry-authorized"
                    ),
                    "retry1": ledger_action(
                        "Successful", "retry-1", "objective-completed"
                    ),
                },
                "nonConsumingActions": [],
            }
        }
        self.assertEqual(
            list(Draft202012Validator(schema, format_checker=FormatChecker()).iter_errors(instance)),
            [],
        )

    def test_retry2_without_retry1_is_invalid(self):
        schema, instance = completion_v2()
        instance["executionDiscipline"]["retryLedger"] = {
            "fictitious objective": {
                "attempts": {
                    "initialAttempt": ledger_action(
                        "Failed", "initial-attempt", "retry-authorized"
                    ),
                    "retry2": ledger_action(
                        "Failed", "retry-2", "reported-unresolved"
                    ),
                },
                "nonConsumingActions": [],
            }
        }
        self.assertTrue(list(Draft202012Validator(schema).iter_errors(instance)))

    def test_retry1_after_successful_initial_is_invalid(self):
        schema, instance = completion_v2()
        instance["executionDiscipline"]["retryLedger"] = {
            "fictitious objective": {
                "attempts": {
                    "initialAttempt": ledger_action(
                        "Successful", "initial-attempt", "objective-completed"
                    ),
                    "retry1": ledger_action(
                        "Failed", "retry-1", "retry-authorized"
                    ),
                },
                "nonConsumingActions": [],
            }
        }
        self.assertTrue(list(Draft202012Validator(schema).iter_errors(instance)))

    def test_unknown_attempt_position_is_invalid(self):
        schema, instance = completion_v2()
        instance["executionDiscipline"]["retryLedger"] = {
            "fictitious objective": {
                "attempts": {
                    "initialAttempt": ledger_action(
                        "Failed", "initial-attempt", "retry-authorized"
                    ),
                    "retry3": ledger_action(
                        "Failed", "retry-2", "reported-unresolved"
                    ),
                },
                "nonConsumingActions": [],
            }
        }
        self.assertTrue(list(Draft202012Validator(schema).iter_errors(instance)))

    def test_unsupported_completion_major_uses_current_schema(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            shutil.copytree(REPO_ROOT / "schemas", root / "schemas")
            instance = json.loads(
                (root / "schemas/examples/completion-result/valid.example.json").read_text(
                    encoding="utf-8"
                )
            )
            instance["schemaVersion"] = "3.0.0"
            evidence = root / "evidence" / "completion-result.example.json"
            evidence.parent.mkdir()
            evidence.write_text(json.dumps(instance), encoding="utf-8")

            completed = run_tool(
                "tools/validate-schemas/validate_schemas.py", "--format", "json", root=root
            )
            self.assertEqual(completed.returncode, 1)
            findings = json_result(completed)["findings"]
            matching = [
                item
                for item in findings
                if item["path"] == "evidence/completion-result.example.json"
            ]
            self.assertEqual(len(matching), 1)
            self.assertEqual(
                matching[0]["details"]["schema"],
                "schemas/v2/completion-result.schema.json",
            )

    def test_remote_ref_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            shutil.copytree(REPO_ROOT / "schemas", root / "schemas")
            path = root / "schemas" / "v1" / "artifact-record.schema.json"
            text = path.read_text(encoding="utf-8").replace('"type": "object"', '"$ref": "https://example.invalid/remote.json",\n  "type": "object"', 1)
            path.write_text(text, encoding="utf-8")
            completed = run_tool("tools/validate-schemas/validate_schemas.py", "--format", "json", "--skip-repository-instances", root=root)
            self.assertEqual(completed.returncode, 1)
            codes = {item["code"] for item in json_result(completed)["findings"]}
            self.assertIn("SCHEMA_REMOTE_REF", codes)


if __name__ == "__main__":
    unittest.main()
