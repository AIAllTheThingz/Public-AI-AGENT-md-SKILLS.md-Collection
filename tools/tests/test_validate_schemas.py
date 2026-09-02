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
    action = {
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
    if budget_position in {"retry-1", "retry-2"}:
        action["materialChange"] = "Fictitious causally relevant material change."
        action["causalRationale"] = (
            "The recorded change creates a concrete reason this retry may succeed."
        )
    return action


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


def retry_ledger(*sequences: dict, outcomes: tuple[str, ...] = ()) -> dict:
    if not sequences:
        return {}
    return {
        "fictitious objective": {
            "failedOrIndeterminateOutcomes": list(outcomes),
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

    def test_completion_result_v1_negative_fixture_remains_invalid(self):
        schema = json.loads(
            (REPO_ROOT / "schemas/v1/completion-result.schema.json").read_text(
                encoding="utf-8"
            )
        )
        instance = json.loads(
            (
                REPO_ROOT
                / "schemas/examples/completion-result/invalid-v1.example.json"
            ).read_text(encoding="utf-8")
        )
        self.assertTrue(
            list(
                Draft202012Validator(
                    schema, format_checker=FormatChecker()
                ).iter_errors(instance)
            )
        )

    def test_missing_completion_result_v1_compatibility_fixture_is_reported(self):
        cases = (
            ("valid-v1.example.json", "SCHEMA_POSITIVE_EXAMPLE_MISSING"),
            ("invalid-v1.example.json", "SCHEMA_NEGATIVE_EXAMPLE_MISSING"),
        )
        for filename, code in cases:
            with self.subTest(filename=filename), tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                shutil.copytree(REPO_ROOT / "schemas", root / "schemas")
                missing = root / "schemas/examples/completion-result" / filename
                missing.unlink()

                completed = run_tool(
                    "tools/validate-schemas/validate_schemas.py",
                    "--format",
                    "json",
                    "--skip-repository-instances",
                    root=root,
                )
                self.assertEqual(completed.returncode, 1)
                result = json_result(completed)
                matching = [
                    item
                    for item in result["findings"]
                    if item["code"] == code
                    and item["path"]
                    == f"schemas/examples/completion-result/{filename}"
                ]
                self.assertEqual(len(matching), 1)

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

    def test_split_objective_negative_fixture_is_rejected(self):
        schema, _ = completion_v2()
        instance = json.loads(
            (REPO_ROOT / "schemas/examples/completion-result/invalid.example.json").read_text(
                encoding="utf-8"
            )
        )
        errors = list(Draft202012Validator(schema).iter_errors(instance))
        self.assertTrue(
            any(
                error.validator == "additionalProperties"
                and list(error.absolute_path) == ["executionDiscipline"]
                for error in errors
            )
        )

    def test_multiple_authorized_retry_resets_are_valid(self):
        schema, instance = completion_v2()
        reset = {
            "priorSequenceStopReport": "The prior sequence reported unresolved.",
            "authorizedBy": "fictitious-owner",
            "authorizationEvidence": "Fictitious authorization record.",
            "materialChange": "Fictitious material state change.",
            "causalRationale": "The state change removes the prior blocker.",
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
            outcomes=(
                "Two prior fictitious sequences reported the objective unresolved.",
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

    def test_validated_status_requires_a_passing_validation(self):
        schema, instance = completion_v2()
        instance["status"] = "validated"
        cases = (
            [],
            [{"name": "Fictitious check", "result": "not-run"}],
            [{"name": "Fictitious check", "result": "failed"}],
        )
        for validation in cases:
            with self.subTest(validation=validation):
                candidate = json.loads(json.dumps(instance))
                candidate["validation"] = validation
                self.assertTrue(
                    list(Draft202012Validator(schema).iter_errors(candidate))
                )

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
            ),
            outcomes=(
                "Fictitious initial validation failed before the retry succeeded.",
            ),
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

    def test_non_consuming_only_sequence_is_valid(self):
        schema, instance = completion_v2()
        sequence = retry_sequence(
            {},
            non_consuming_actions=[
                ledger_action("Successful", "non-consuming", "not-terminal")
            ],
        )
        del sequence["attempts"]
        instance["executionDiscipline"]["retryLedger"] = retry_ledger(sequence)
        self.assertEqual(
            list(
                Draft202012Validator(
                    schema, format_checker=FormatChecker()
                ).iter_errors(instance)
            ),
            [],
        )

    def test_passed_validation_requires_a_nonempty_execution_ledger(self):
        schema, instance = completion_v2()
        instance["executionDiscipline"]["retryLedger"] = {}
        self.assertTrue(list(Draft202012Validator(schema).iter_errors(instance)))

    def test_passed_validation_requires_a_successful_ledger_action(self):
        schema, instance = completion_v2()
        instance["executionDiscipline"]["retryLedger"] = retry_ledger(
            retry_sequence(
                {
                    "initialAttempt": ledger_action(
                        "Failed", "initial-attempt", "reported-unresolved"
                    )
                }
            ),
            outcomes=(
                "Fictitious validation attempt failed.",
            ),
        )
        self.assertTrue(list(Draft202012Validator(schema).iter_errors(instance)))

    def test_failed_validation_requires_a_reported_failure(self):
        schema, instance = completion_v2()
        instance["validation"][0]["result"] = "failed"
        self.assertTrue(list(Draft202012Validator(schema).iter_errors(instance)))

    def test_failure_and_success_only_objective_ledgers_can_coexist(self):
        schema, instance = completion_v2()
        evidence_sequence = retry_sequence(
            {},
            sequence_id="evidence-sequence-1",
            non_consuming_actions=[
                ledger_action("Successful", "non-consuming", "not-terminal")
            ],
        )
        del evidence_sequence["attempts"]
        instance["executionDiscipline"]["retryLedger"] = {
            "failing objective": {
                "failedOrIndeterminateOutcomes": ["Fictitious validation failed."],
                "priorUnresolvedSequences": [],
                "currentSequence": retry_sequence(
                    {
                        "initialAttempt": ledger_action(
                            "Failed", "initial-attempt", "reported-unresolved"
                        )
                    }
                ),
            },
            "evidence-only objective": {
                "failedOrIndeterminateOutcomes": [],
                "priorUnresolvedSequences": [],
                "currentSequence": evidence_sequence,
            },
        }
        self.assertEqual(
            list(
                Draft202012Validator(
                    schema, format_checker=FormatChecker()
                ).iter_errors(instance)
            ),
            [],
        )

    def test_sequence_without_any_execution_action_is_invalid(self):
        schema, instance = completion_v2()
        sequence = retry_sequence({})
        del sequence["attempts"]
        instance["executionDiscipline"]["retryLedger"] = retry_ledger(sequence)
        self.assertTrue(list(Draft202012Validator(schema).iter_errors(instance)))

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
                    retry_sequence(attempts),
                    outcomes=("Fictitious execution attempt failed.",),
                )
                self.assertTrue(
                    list(Draft202012Validator(schema).iter_errors(instance))
                )

    def test_retry_requires_material_change_and_causal_rationale(self):
        for missing in ("materialChange", "causalRationale"):
            with self.subTest(missing=missing):
                schema, instance = completion_v2()
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
                    ),
                    outcomes=("Fictitious initial attempt failed.",),
                )
                del instance["executionDiscipline"]["retryLedger"][
                    "fictitious objective"
                ]["currentSequence"]["attempts"]["retry1"][missing]
                errors = list(Draft202012Validator(schema).iter_errors(instance))
                self.assertTrue(any(error.validator == "required" for error in errors))

    def test_unchanged_retry_negative_fixture_is_rejected(self):
        schema, _ = completion_v2()
        instance = json.loads(
            (
                REPO_ROOT
                / "schemas/examples/completion-result/invalid-retry.example.json"
            ).read_text(encoding="utf-8")
        )
        errors = list(Draft202012Validator(schema).iter_errors(instance))
        self.assertTrue(any(error.validator == "required" for error in errors))

    def test_each_objective_ledger_requires_its_outcome_array(self):
        schema, instance = completion_v2()
        instance["executionDiscipline"]["retryLedger"] = {
            "first objective": {
                "failedOrIndeterminateOutcomes": [
                    "Fictitious first validation failed."
                ],
                "priorUnresolvedSequences": [],
                "currentSequence": retry_sequence(
                    {
                        "initialAttempt": ledger_action(
                            "Failed", "initial-attempt", "reported-unresolved"
                        )
                    }
                ),
            },
            "second objective": {
                "priorUnresolvedSequences": [],
                "currentSequence": retry_sequence(
                    {
                        "initialAttempt": ledger_action(
                            "Successful", "initial-attempt", "objective-completed"
                        )
                    }
                ),
            },
        }
        self.assertTrue(list(Draft202012Validator(schema).iter_errors(instance)))

    def test_multiple_failed_outcomes_each_with_a_retry_ledger_are_valid(self):
        schema, instance = completion_v2()
        instance["validation"][0]["result"] = "failed"
        failure_evidence = retry_ledger(
            retry_sequence(
                {
                    "initialAttempt": ledger_action(
                        "Failed", "initial-attempt", "reported-unresolved"
                    )
                }
            ),
            outcomes=("Fictitious validation failed.",),
        )["fictitious objective"]
        second_failure_evidence = json.loads(json.dumps(failure_evidence))
        second_failure_evidence["failedOrIndeterminateOutcomes"] = [
            "Fictitious second validation failed."
        ]
        instance["executionDiscipline"]["retryLedger"] = {
            "first objective": failure_evidence,
            "second objective": second_failure_evidence,
        }
        self.assertEqual(
            list(
                Draft202012Validator(
                    schema, format_checker=FormatChecker()
                ).iter_errors(instance)
            ),
            [],
        )

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
        instance["executionDiscipline"]["retryLedger"] = retry_ledger(
            retry_sequence(
                {
                    "initialAttempt": ledger_action(
                        "Successful", "initial-attempt", "objective-completed"
                    )
                }
            ),
            outcomes=("Fictitious validation failed.",),
        )
        self.assertTrue(list(Draft202012Validator(schema).iter_errors(instance)))

    def test_delegation_boundaries_must_be_preserved(self):
        schema, instance = completion_v2()
        instance["executionDiscipline"]["delegationHandoff"][
            "boundariesPreserved"
        ] = False
        self.assertTrue(list(Draft202012Validator(schema).iter_errors(instance)))

    def test_incomplete_delegated_handoff_is_invalid(self):
        schema, _ = completion_v2()
        instance = json.loads(
            (
                REPO_ROOT
                / "schemas/examples/completion-result/invalid-delegation.example.json"
            ).read_text(encoding="utf-8")
        )
        errors = list(Draft202012Validator(schema).iter_errors(instance))
        self.assertTrue(any(error.validator == "required" for error in errors))

    def test_complete_delegated_handoff_is_valid(self):
        schema, instance = completion_v2()
        instance["validation"][0]["result"] = "failed"
        instance["executionDiscipline"]["retryLedger"] = retry_ledger(
            retry_sequence(
                {
                    "initialAttempt": ledger_action(
                        "Failed", "initial-attempt", "reported-unresolved"
                    )
                }
            ),
            outcomes=("Fictitious validation failed.",),
        )
        instance["executionDiscipline"]["delegationHandoff"] = {
            "delegated": True,
            "summary": "Fictitious unresolved work was delegated.",
            "meaningfulValue": "Independent validation specialization.",
            "failureEvidence": ["Fictitious validation failed."],
            "blocker": "Fictitious validation blocker.",
            "retryCount": 0,
            "unresolvedState": "unresolved",
            "boundariesPreserved": True,
        }
        self.assertEqual(
            list(
                Draft202012Validator(
                    schema, format_checker=FormatChecker()
                ).iter_errors(instance)
            ),
            [],
        )

    def test_failed_budgeted_attempt_cannot_claim_completion(self):
        schema, instance = completion_v2()
        instance["executionDiscipline"]["retryLedger"] = retry_ledger(
            retry_sequence(
                {
                    "initialAttempt": ledger_action(
                        "Failed", "initial-attempt", "objective-completed"
                    )
                }
            ),
            outcomes=("Fictitious execution attempt failed.",),
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
            ),
            outcomes=("Fictitious execution attempts failed.",),
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
            ),
            outcomes=("Fictitious retry failed.",),
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
                    retry_sequence(attempts),
                    outcomes=("Fictitious execution attempt failed.",),
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
            outcomes=("Fictitious first sequence failed.",),
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
                    "causalRationale": "The state change removes the prior blocker.",
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
            ),
            outcomes=("Fictitious execution attempts failed.",),
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

    def test_malformed_completion_major_uses_current_schema_without_crashing(self):
        versions = ("².0.0", f"{'9' * 5000}.0.0")
        for version in versions:
            with self.subTest(version=version[:20]), tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                shutil.copytree(REPO_ROOT / "schemas", root / "schemas")
                instance = json.loads(
                    (
                        root
                        / "schemas/examples/completion-result/valid.example.json"
                    ).read_text(encoding="utf-8")
                )
                instance["schemaVersion"] = version
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
                codes = {item["code"] for item in result["findings"]}
                self.assertNotIn("INTERNAL_ERROR", codes)
                matching = [
                    item
                    for item in result["findings"]
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

    def test_meta_invalid_schema_is_skipped_for_repository_instances(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            shutil.copytree(REPO_ROOT / "schemas", root / "schemas")
            path = root / "schemas" / "v2" / "completion-result.schema.json"
            schema = json.loads(path.read_text(encoding="utf-8"))
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
            codes = {item["code"] for item in result["findings"]}
            self.assertIn("SCHEMA_INVALID", codes)
            self.assertNotIn("INTERNAL_ERROR", codes)
            self.assertEqual(result["summary"]["repositoryInstances"], 1)

    def test_meta_invalid_v1_schema_does_not_hide_invalid_v2_instance(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            shutil.copytree(REPO_ROOT / "schemas", root / "schemas")
            path = root / "schemas" / "v1" / "completion-result.schema.json"
            schema = json.loads(path.read_text(encoding="utf-8"))
            schema["properties"]["summary"]["type"] = 123
            path.write_text(json.dumps(schema), encoding="utf-8")

            instance = json.loads(
                (
                    root
                    / "schemas/examples/completion-result/valid.example.json"
                ).read_text(encoding="utf-8")
            )
            del instance["executionDiscipline"]
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
            codes = {item["code"] for item in result["findings"]}
            self.assertIn("SCHEMA_INVALID", codes)
            self.assertNotIn("INTERNAL_ERROR", codes)
            matching = [
                item
                for item in result["findings"]
                if item["code"] == "SCHEMA_INSTANCE_INVALID"
                and item["path"] == "evidence/completion-result.example.json"
            ]
            self.assertEqual(len(matching), 1)
            self.assertEqual(
                matching[0]["details"]["schema"],
                "schemas/v2/completion-result.schema.json",
            )
            self.assertEqual(result["summary"]["repositoryInstances"], 1)

    def test_boolean_schema_returns_structured_findings(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            shutil.copytree(REPO_ROOT / "schemas", root / "schemas")
            path = root / "schemas" / "v2" / "completion-result.schema.json"
            path.write_text("true\n", encoding="utf-8")

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
            codes = {item["code"] for item in result["findings"]}
            self.assertIn("SCHEMA_ID_MISSING", codes)
            self.assertIn("SCHEMA_VERSION_MISMATCH", codes)
            self.assertNotIn("INTERNAL_ERROR", codes)
            self.assertEqual(result["summary"]["repositoryInstances"], 1)


if __name__ == "__main__":
    unittest.main()
