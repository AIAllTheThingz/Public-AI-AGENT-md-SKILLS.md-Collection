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


def retry_sequence(
    attempts: dict,
    *,
    sequence_id: str = "sequence-1",
    non_consuming_actions: list[dict] | None = None,
    reset_authorization: dict | None = None,
) -> dict:
    sequence = {
        "sequenceId": sequence_id,
        "attempts": attempts,
        "nonConsumingActions": non_consuming_actions or [],
    }
    if reset_authorization is not None:
        sequence["resetAuthorization"] = reset_authorization
    return sequence


def retry_ledger(*sequences: dict) -> dict:
    if not sequences:
        return {}
    return {
        "fictitious objective": {
            "priorUnresolvedSequences": list(sequences[:-1]),
            "currentSequence": sequences[-1],
        }
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

    def test_authorized_retry_reset_fixture_is_valid(self):
        instance = json.loads(
            (REPO_ROOT / "schemas/examples/completion-result/valid-reset.example.json").read_text(
                encoding="utf-8"
            )
        )
        for relative in (
            "schemas/completion-result.schema.json",
            "schemas/v2/completion-result.schema.json",
        ):
            with self.subTest(schema=relative):
                schema = json.loads((REPO_ROOT / relative).read_text(encoding="utf-8"))
                self.assertEqual(
                    list(
                        Draft202012Validator(
                            schema, format_checker=FormatChecker()
                        ).iter_errors(instance)
                    ),
                    [],
                )

    def test_multiple_authorized_retry_resets_are_valid(self):
        schema, instance = completion_v2()
        instance["executionDiscipline"]["failedOrIndeterminateOutcomes"] = [
            "Two prior fictitious sequences reported the objective unresolved."
        ]
        reset = {
            "priorSequenceStopReport": "The prior sequence reported unresolved.",
            "authorizedBy": "fictitious-owner",
            "authorizationEvidence": "Fictitious authorization record.",
            "materialChange": "Fictitious material state change.",
        }
        instance["executionDiscipline"]["retryLedger"] = retry_ledger(
            retry_sequence(
                {
                    "initialAttempt": ledger_action(
                        "Failed", "initial-attempt", "reported-unresolved"
                    )
                }
            ),
            retry_sequence(
                {
                    "initialAttempt": ledger_action(
                        "Indeterminate", "initial-attempt", "reported-unresolved"
                    )
                },
                sequence_id="sequence-2",
                reset_authorization=reset,
            ),
            retry_sequence(
                {
                    "initialAttempt": ledger_action(
                        "Successful", "initial-attempt", "objective-completed"
                    )
                },
                sequence_id="sequence-3",
                reset_authorization=reset,
            ),
        )
        self.assertEqual(
            list(
                Draft202012Validator(
                    schema, format_checker=FormatChecker()
                ).iter_errors(instance)
            ),
            [],
        )

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
        instance["executionDiscipline"]["retryLedger"] = retry_ledger(
            retry_sequence(
                {},
                non_consuming_actions=[
                    ledger_action("Failed", "non-consuming", "not-terminal")
                ],
            )
        )
        self.assertTrue(list(Draft202012Validator(schema).iter_errors(instance)))

    def test_failed_initial_then_successful_retry_is_valid(self):
        schema, instance = completion_v2()
        instance["executionDiscipline"]["failedOrIndeterminateOutcomes"] = [
            "Fictitious initial validation failed before the retry succeeded."
        ]
        instance["executionDiscipline"]["retryLedger"] = retry_ledger(
            retry_sequence(
                {
                    "initialAttempt": ledger_action(
                        "Failed", "initial-attempt", "retry-authorized"
                    ),
                    "retry1": ledger_action(
                        "Successful", "retry-1", "objective-completed"
                    ),
                }
            )
        )
        self.assertEqual(
            list(Draft202012Validator(schema, format_checker=FormatChecker()).iter_errors(instance)),
            [],
        )

    def test_success_only_ledger_allows_an_empty_outcome_summary(self):
        schema, instance = completion_v2()
        instance["executionDiscipline"]["retryLedger"] = retry_ledger(
            retry_sequence(
                {
                    "initialAttempt": ledger_action(
                        "Successful", "initial-attempt", "objective-completed"
                    )
                }
            )
        )
        self.assertEqual(
            list(
                Draft202012Validator(
                    schema, format_checker=FormatChecker()
                ).iter_errors(instance)
            ),
            [],
        )

    def test_retry_authorized_requires_the_corresponding_retry(self):
        cases = (
            {
                "initialAttempt": ledger_action(
                    "Failed", "initial-attempt", "retry-authorized"
                )
            },
            {
                "initialAttempt": ledger_action(
                    "Failed", "initial-attempt", "retry-authorized"
                ),
                "retry1": ledger_action(
                    "Indeterminate", "retry-1", "retry-authorized"
                ),
            },
        )
        for attempts in cases:
            with self.subTest(attempts=tuple(attempts)):
                schema, instance = completion_v2()
                instance["executionDiscipline"]["retryLedger"] = retry_ledger(
                    retry_sequence(attempts)
                )
                self.assertTrue(
                    list(Draft202012Validator(schema).iter_errors(instance))
                )

    def test_failed_outcomes_require_a_nonempty_retry_ledger(self):
        schema, instance = completion_v2()
        instance["executionDiscipline"]["failedOrIndeterminateOutcomes"] = [
            "Fictitious validation failed."
        ]
        instance["executionDiscipline"]["retryLedger"] = {}
        self.assertTrue(list(Draft202012Validator(schema).iter_errors(instance)))

    def test_failed_attempt_requires_a_reported_outcome(self):
        schema, instance = completion_v2()
        instance["executionDiscipline"]["retryLedger"] = retry_ledger(
            retry_sequence(
                {
                    "initialAttempt": ledger_action(
                        "Failed", "initial-attempt", "reported-unresolved"
                    )
                }
            )
        )
        self.assertTrue(list(Draft202012Validator(schema).iter_errors(instance)))

    def test_reported_failures_require_a_failed_or_indeterminate_attempt(self):
        schema, instance = completion_v2()
        instance["executionDiscipline"]["failedOrIndeterminateOutcomes"] = [
            "Fictitious validation failed."
        ]
        instance["executionDiscipline"]["retryLedger"] = retry_ledger(
            retry_sequence(
                {
                    "initialAttempt": ledger_action(
                        "Successful", "initial-attempt", "objective-completed"
                    )
                }
            )
        )
        self.assertTrue(list(Draft202012Validator(schema).iter_errors(instance)))

    def test_delegation_boundaries_must_be_preserved(self):
        schema, instance = completion_v2()
        instance["executionDiscipline"]["delegationHandoff"][
            "boundariesPreserved"
        ] = False
        self.assertTrue(list(Draft202012Validator(schema).iter_errors(instance)))

    def test_failed_budgeted_attempt_cannot_claim_completion(self):
        schema, instance = completion_v2()
        instance["executionDiscipline"]["retryLedger"] = retry_ledger(
            retry_sequence(
                {
                    "initialAttempt": ledger_action(
                        "Failed", "initial-attempt", "objective-completed"
                    )
                }
            )
        )
        self.assertTrue(list(Draft202012Validator(schema).iter_errors(instance)))

    def test_retry2_without_retry1_is_invalid(self):
        schema, instance = completion_v2()
        instance["executionDiscipline"]["retryLedger"] = retry_ledger(
            retry_sequence(
                {
                    "initialAttempt": ledger_action(
                        "Failed", "initial-attempt", "retry-authorized"
                    ),
                    "retry2": ledger_action(
                        "Failed", "retry-2", "reported-unresolved"
                    ),
                }
            )
        )
        self.assertTrue(list(Draft202012Validator(schema).iter_errors(instance)))

    def test_retry1_after_successful_initial_is_invalid(self):
        schema, instance = completion_v2()
        instance["executionDiscipline"]["retryLedger"] = retry_ledger(
            retry_sequence(
                {
                    "initialAttempt": ledger_action(
                        "Successful", "initial-attempt", "objective-completed"
                    ),
                    "retry1": ledger_action(
                        "Failed", "retry-1", "retry-authorized"
                    ),
                }
            )
        )
        self.assertTrue(list(Draft202012Validator(schema).iter_errors(instance)))

    def test_retry_after_reported_unresolved_is_invalid(self):
        cases = (
            {
                "initialAttempt": ledger_action(
                    "Failed", "initial-attempt", "reported-unresolved"
                ),
                "retry1": ledger_action(
                    "Successful", "retry-1", "objective-completed"
                ),
            },
            {
                "initialAttempt": ledger_action(
                    "Failed", "initial-attempt", "retry-authorized"
                ),
                "retry1": ledger_action(
                    "Failed", "retry-1", "reported-unresolved"
                ),
                "retry2": ledger_action(
                    "Successful", "retry-2", "objective-completed"
                ),
            },
        )
        for attempts in cases:
            with self.subTest(attempts=tuple(attempts)):
                schema, instance = completion_v2()
                instance["executionDiscipline"]["retryLedger"] = retry_ledger(
                    retry_sequence(attempts)
                )
                self.assertTrue(list(Draft202012Validator(schema).iter_errors(instance)))

    def test_second_retry_sequence_requires_reset_authorization(self):
        schema, instance = completion_v2()
        instance["executionDiscipline"]["retryLedger"] = retry_ledger(
            retry_sequence(
                {
                    "initialAttempt": ledger_action(
                        "Failed", "initial-attempt", "reported-unresolved"
                    )
                }
            ),
            retry_sequence(
                {
                    "initialAttempt": ledger_action(
                        "Successful", "initial-attempt", "objective-completed"
                    )
                },
                sequence_id="sequence-2",
            ),
        )
        self.assertTrue(list(Draft202012Validator(schema).iter_errors(instance)))

    def test_retry_sequence_cannot_follow_a_successful_sequence(self):
        schema, instance = completion_v2()
        instance["executionDiscipline"]["retryLedger"] = retry_ledger(
            retry_sequence(
                {
                    "initialAttempt": ledger_action(
                        "Successful", "initial-attempt", "objective-completed"
                    )
                }
            ),
            retry_sequence(
                {
                    "initialAttempt": ledger_action(
                        "Successful", "initial-attempt", "objective-completed"
                    )
                },
                sequence_id="sequence-2",
                reset_authorization={
                    "priorSequenceStopReport": "Fictitious prior stop report.",
                    "authorizedBy": "fictitious-owner",
                    "authorizationEvidence": "Fictitious authorization record.",
                    "materialChange": "Fictitious material state change.",
                },
            ),
        )
        self.assertTrue(list(Draft202012Validator(schema).iter_errors(instance)))

    def test_unknown_attempt_position_is_invalid(self):
        schema, instance = completion_v2()
        instance["executionDiscipline"]["retryLedger"] = retry_ledger(
            retry_sequence(
                {
                    "initialAttempt": ledger_action(
                        "Failed", "initial-attempt", "retry-authorized"
                    ),
                    "retry3": ledger_action(
                        "Failed", "retry-2", "reported-unresolved"
                    ),
                }
            )
        )
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

    def test_unversioned_completion_uses_current_schema(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            shutil.copytree(REPO_ROOT / "schemas", root / "schemas")
            instance = json.loads(
                (root / "schemas/examples/completion-result/valid.example.json").read_text(
                    encoding="utf-8"
                )
            )
            del instance["schemaVersion"]
            del instance["executionDiscipline"]
            evidence = root / "evidence" / "completion-result.example.json"
            evidence.parent.mkdir()
            evidence.write_text(json.dumps(instance), encoding="utf-8")

            completed = run_tool(
                "tools/validate-schemas/validate_schemas.py", "--format", "json", root=root
            )
            self.assertEqual(completed.returncode, 1)
            matching = [
                item
                for item in json_result(completed)["findings"]
                if item["path"] == "evidence/completion-result.example.json"
            ]
            self.assertTrue(matching)
            self.assertTrue(
                all(
                    item["details"]["schema"]
                    == "schemas/v2/completion-result.schema.json"
                    for item in matching
                )
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

    def test_remote_ref_in_v1_completion_is_rejected_before_fixture_validation(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            shutil.copytree(REPO_ROOT / "schemas", root / "schemas")
            path = root / "schemas" / "v1" / "completion-result.schema.json"
            text = path.read_text(encoding="utf-8").replace(
                '"type": "object"',
                '"$ref": "https://example.invalid/remote.json",\n  "type": "object"',
                1,
            )
            path.write_text(text, encoding="utf-8")

            completed = run_tool(
                "tools/validate-schemas/validate_schemas.py",
                "--format",
                "json",
                "--skip-repository-instances",
                root=root,
            )
            self.assertEqual(completed.returncode, 1)
            result = json_result(completed)
            self.assertEqual(result["status"], "failed")
            self.assertNotIn(
                "INTERNAL_ERROR", {item["code"] for item in result["findings"]}
            )
            matching = [
                item
                for item in result["findings"]
                if item["code"] == "SCHEMA_REMOTE_REF"
                and item["path"] == "schemas/v1/completion-result.schema.json"
            ]
            self.assertEqual(len(matching), 1)

    def test_remote_ref_schema_is_skipped_for_discovered_repository_instance(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            shutil.copytree(REPO_ROOT / "schemas", root / "schemas")
            path = root / "schemas" / "v2" / "completion-result.schema.json"
            text = path.read_text(encoding="utf-8").replace(
                '"type": "object"',
                '"$ref": "https://example.invalid/remote.json",\n  "type": "object"',
                1,
            )
            path.write_text(text, encoding="utf-8")

            instance = json.loads(
                (
                    root / "schemas/examples/completion-result/valid.example.json"
                ).read_text(encoding="utf-8")
            )
            evidence = root / "evidence" / "completion-result.example.json"
            evidence.parent.mkdir()
            evidence.write_text(json.dumps(instance), encoding="utf-8")

            completed = run_tool(
                "tools/validate-schemas/validate_schemas.py",
                "--format",
                "json",
                root=root,
            )
            self.assertEqual(completed.returncode, 1)
            result = json_result(completed)
            self.assertEqual(result["status"], "failed")
            codes = {item["code"] for item in result["findings"]}
            self.assertIn("SCHEMA_REMOTE_REF", codes)
            self.assertNotIn("INTERNAL_ERROR", codes)
            self.assertEqual(result["summary"]["repositoryInstances"], 1)

    def test_remote_ref_is_scanned_before_schema_meta_validation(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            shutil.copytree(REPO_ROOT / "schemas", root / "schemas")
            path = root / "schemas" / "v2" / "completion-result.schema.json"
            schema = json.loads(path.read_text(encoding="utf-8"))
            schema["$ref"] = "https://example.invalid/remote.json"
            schema["properties"]["summary"]["type"] = 123
            path.write_text(json.dumps(schema), encoding="utf-8")

            instance = json.loads(
                (
                    root
                    / "schemas/examples/completion-result/valid.example.json"
                ).read_text(encoding="utf-8")
            )
            evidence = root / "evidence" / "completion-result.example.json"
            evidence.parent.mkdir()
            evidence.write_text(json.dumps(instance), encoding="utf-8")

            completed = run_tool(
                "tools/validate-schemas/validate_schemas.py",
                "--format",
                "json",
                root=root,
            )
            self.assertEqual(completed.returncode, 1)
            result = json_result(completed)
            self.assertEqual(result["status"], "failed")
            codes = {item["code"] for item in result["findings"]}
            self.assertIn("SCHEMA_INVALID", codes)
            self.assertIn("SCHEMA_REMOTE_REF", codes)
            self.assertNotIn("INTERNAL_ERROR", codes)
            self.assertEqual(result["summary"]["repositoryInstances"], 1)


if __name__ == "__main__":
    unittest.main()
