"""Semantic validation for completion-result v2 evidence."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


RFC3339_TIMESTAMP = re.compile(
    r"^(?P<date>\d{4}-\d{2}-\d{2})[Tt]"
    r"(?P<hour>\d{2}):(?P<minute>\d{2}):(?P<second>\d{2})"
    r"(?:\.(?P<fraction>\d+))?"
    r"(?P<offset>[Zz]|[+-]\d{2}:\d{2})$"
)


@dataclass(frozen=True)
class SemanticIssue:
    """One logically inconsistent completion-result relationship."""

    code: str
    message: str
    pointer: str
    details: dict[str, Any] = field(default_factory=dict)


def _sequences(objective_ledger: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        *objective_ledger["priorUnresolvedSequences"],
        objective_ledger["currentSequence"],
    ]


def _actions(sequence: dict[str, Any]) -> list[dict[str, Any]]:
    attempts = sequence.get("attempts", {})
    return [
        *(
            attempts[name]
            for name in ("initialAttempt", "retry1", "retry2")
            if name in attempts
        ),
        *sequence["preTerminalNonConsumingActions"],
        *sequence["nonConsumingActions"],
    ]


def _timestamp(value: str) -> tuple[int, str]:
    """Return an exact UTC instant for a structurally valid RFC 3339 value."""

    match = RFC3339_TIMESTAMP.fullmatch(value)
    if match is None:
        raise ValueError(f"Unsupported RFC 3339 timestamp: {value}")

    second = int(match.group("second"))
    leap_second = second == 60
    offset = match.group("offset")
    if offset in {"Z", "z"}:
        offset = "+00:00"
    parsed = datetime.fromisoformat(
        f"{match.group('date')}T{match.group('hour')}:"
        f"{match.group('minute')}:{59 if leap_second else second:02d}{offset}"
    ).astimezone(timezone.utc)
    whole_seconds = (
        (parsed.toordinal() - 1) * 86_400
        + parsed.hour * 3_600
        + parsed.minute * 60
        + parsed.second
        + int(leap_second)
    )
    # With insignificant trailing zeroes removed, lexicographic comparison of
    # the remaining digits is exact even when the fraction exceeds Python's
    # datetime microsecond precision or integer-conversion safety limit.
    fraction = (match.group("fraction") or "").rstrip("0")
    return whole_seconds, fraction


def _pointer(*parts: str | int) -> str:
    return "/" + "/".join(
        str(part).replace("~", "~0").replace("/", "~1") for part in parts
    )


def _sequence_locations(
    objective_id: str, objective_ledger: dict[str, Any]
) -> list[tuple[dict[str, Any], tuple[str | int, ...]]]:
    prefix: tuple[str | int, ...] = (
        "executionDiscipline",
        "retryLedger",
        objective_id,
    )
    return [
        *(
            (sequence, (*prefix, "priorUnresolvedSequences", index))
            for index, sequence in enumerate(
                objective_ledger["priorUnresolvedSequences"]
            )
        ),
        (objective_ledger["currentSequence"], (*prefix, "currentSequence")),
    ]


def _action_locations(
    sequence: dict[str, Any], location: tuple[str | int, ...]
) -> list[tuple[dict[str, Any], tuple[str | int, ...]]]:
    attempts = sequence.get("attempts", {})
    return [
        *(
            (attempts[name], (*location, "attempts", name))
            for name in ("initialAttempt", "retry1", "retry2")
            if name in attempts
        ),
        *(
            (action, (*location, "preTerminalNonConsumingActions", index))
            for index, action in enumerate(
                sequence["preTerminalNonConsumingActions"]
            )
        ),
        *(
            (action, (*location, "nonConsumingActions", index))
            for index, action in enumerate(sequence["nonConsumingActions"])
        ),
    ]


def _reported_unresolved_attempt(sequence: dict[str, Any]) -> dict[str, Any]:
    attempts = sequence["attempts"]
    return next(
        attempts[name]
        for name in ("initialAttempt", "retry1", "retry2")
        if attempts.get(name, {}).get("terminalDisposition") == "reported-unresolved"
    )


def _sequence_started_at(sequence: dict[str, Any]) -> datetime:
    return _timestamp(_sequence_first_action(sequence)["startedAt"])


def _sequence_first_action(sequence: dict[str, Any]) -> dict[str, Any]:
    return min(_actions(sequence), key=lambda action: _timestamp(action["startedAt"]))


def validate_completion_semantics(instance: dict[str, Any]) -> list[SemanticIssue]:
    """Return cross-record completion-result v2 consistency issues.

    The caller first validates the instance against the structural JSON Schema,
    so this pass can evaluate relationships between already well-formed records.
    """

    retry_ledger = instance["executionDiscipline"]["retryLedger"]
    issues: list[SemanticIssue] = []
    required_action_results = {
        "passed": ("Successful",),
        "failed": ("Failed", "Indeterminate"),
    }

    for index, validation in enumerate(instance["validation"]):
        expected_results = required_action_results.get(validation["result"])
        if expected_results is None:
            continue
        objective_id = validation["objectiveId"]
        action_id = validation["actionId"]
        objective_ledger = retry_ledger.get(objective_id)
        if objective_ledger is None:
            issues.append(
                SemanticIssue(
                    code="COMPLETION_VALIDATION_OBJECTIVE_MISMATCH",
                    message=(
                        f"{validation['result'].title()} validation must reference an "
                        "existing retry-ledger objective."
                    ),
                    pointer=f"/validation/{index}/objectiveId",
                    details={
                        "objectiveId": objective_id,
                    },
                )
            )
            continue
        matching_actions = [
            action
            for sequence in _sequences(objective_ledger)
            for action in _actions(sequence)
            if action.get("actionId") == action_id
        ]
        if (
            len(matching_actions) != 1
            or matching_actions[0]["result"] not in expected_results
        ):
            issues.append(
                SemanticIssue(
                    code="COMPLETION_VALIDATION_ACTION_MISMATCH",
                    message=(
                        f"{validation['result'].title()} validation must uniquely "
                        "reference its corresponding ledger action with a compatible "
                        "result."
                    ),
                    pointer=f"/validation/{index}/actionId",
                    details={
                        "objectiveId": objective_id,
                        "actionId": action_id,
                        "matchingActions": len(matching_actions),
                        "requiredActionResults": list(expected_results),
                    },
                )
            )

    for objective_id, objective_ledger in retry_ledger.items():
        sequence_locations = _sequence_locations(objective_id, objective_ledger)
        seen_sequence_ids: set[str] = set()
        for sequence, location in sequence_locations:
            sequence_id = sequence["sequenceId"]
            if sequence_id in seen_sequence_ids:
                issues.append(
                    SemanticIssue(
                        code="COMPLETION_SEQUENCE_ID_DUPLICATE",
                        message=(
                            "Sequence IDs must be unique within one retry-ledger "
                            "objective."
                        ),
                        pointer=_pointer(*location, "sequenceId"),
                        details={"sequenceId": sequence_id},
                    )
                )
            seen_sequence_ids.add(sequence_id)

        for (previous, _), (current, current_location) in zip(
            sequence_locations, sequence_locations[1:]
        ):
            reset_authorization = current["resetAuthorization"]
            if reset_authorization["priorSequenceId"] != previous["sequenceId"]:
                issues.append(
                    SemanticIssue(
                        code="COMPLETION_RESET_SEQUENCE_MISMATCH",
                        message=(
                            "Reset authorization must identify the immediately "
                            "preceding unresolved sequence."
                        ),
                        pointer=_pointer(
                            *current_location,
                            "resetAuthorization",
                            "priorSequenceId",
                        ),
                        details={
                            "expectedPriorSequenceId": previous["sequenceId"],
                            "recordedPriorSequenceId": reset_authorization[
                                "priorSequenceId"
                            ],
                        },
                    )
                )
            previous_terminal = _reported_unresolved_attempt(previous)
            authorized_at = _timestamp(reset_authorization["authorizedAt"])
            if not (
                _timestamp(previous_terminal["endedAt"])
                <= authorized_at
                <= _sequence_started_at(current)
            ):
                issues.append(
                    SemanticIssue(
                        code="COMPLETION_RESET_ORDER_INVALID",
                        message=(
                            "Reset authorization must occur after the preceding "
                            "unresolved attempt ends and before the new sequence starts."
                        ),
                        pointer=_pointer(
                            *current_location,
                            "resetAuthorization",
                            "authorizedAt",
                        ),
                        details={
                            "priorSequenceEndedAt": previous_terminal["endedAt"],
                            "authorizedAt": reset_authorization["authorizedAt"],
                            "currentSequenceStartedAt": _sequence_first_action(current)[
                                "startedAt"
                            ],
                        },
                    )
                )

        for sequence, location in sequence_locations:
            for action, action_location in _action_locations(sequence, location):
                if _timestamp(action["endedAt"]) < _timestamp(action["startedAt"]):
                    issues.append(
                        SemanticIssue(
                            code="COMPLETION_ACTION_TIME_INVALID",
                            message="A completion action cannot end before it starts.",
                            pointer=_pointer(*action_location),
                            details={
                                "startedAt": action["startedAt"],
                                "endedAt": action["endedAt"],
                            },
                        )
                    )

            attempts = sequence.get("attempts", {})
            ordered_attempts = [
                (name, attempts[name])
                for name in ("initialAttempt", "retry1", "retry2")
                if name in attempts
            ]
            for (previous_name, previous), (current_name, current) in zip(
                ordered_attempts, ordered_attempts[1:]
            ):
                if _timestamp(current["startedAt"]) < _timestamp(previous["endedAt"]):
                    issues.append(
                        SemanticIssue(
                            code="COMPLETION_ACTION_ORDER_INVALID",
                            message=(
                                "A retry must start no earlier than the preceding "
                                "attempt ends."
                            ),
                            pointer=_pointer(*location, "attempts", current_name),
                            details={
                                "previousActionPointer": _pointer(
                                    *location, "attempts", previous_name
                                )
                            },
                        )
                    )

            terminal_name = next(
                (
                    name
                    for name in ("initialAttempt", "retry1", "retry2")
                    if attempts.get(name, {}).get("terminalDisposition")
                    in {"reported-unresolved", "objective-completed"}
                ),
                None,
            )
            if terminal_name is None:
                continue
            terminal_action = attempts[terminal_name]
            terminal_started_at = _timestamp(terminal_action["startedAt"])
            terminal_pointer = _pointer(*location, "attempts", terminal_name)
            if terminal_action["terminalDisposition"] == "reported-unresolved":
                for index, action in enumerate(
                    sequence["preTerminalNonConsumingActions"]
                ):
                    if _timestamp(action["endedAt"]) <= terminal_started_at:
                        continue
                    issues.append(
                        SemanticIssue(
                            code="COMPLETION_PRE_TERMINAL_ORDER_INVALID",
                            message=(
                                "A pre-terminal non-consuming action must end no later "
                                "than the terminal unresolved attempt starts."
                            ),
                            pointer=_pointer(
                                *location,
                                "preTerminalNonConsumingActions",
                                index,
                            ),
                            details={"terminalAttemptPointer": terminal_pointer},
                        )
                    )
                continue
            for action, action_location in _action_locations(sequence, location):
                if action is terminal_action:
                    continue
                if _timestamp(action["endedAt"]) <= terminal_started_at:
                    continue
                issues.append(
                    SemanticIssue(
                        code="COMPLETION_POST_TERMINAL_ACTION",
                        message=(
                            "Every other action must end no later than the "
                            "objective-completing attempt starts."
                        ),
                        pointer=_pointer(*action_location),
                        details={"terminalAttemptPointer": terminal_pointer},
                    )
                )

    return issues
