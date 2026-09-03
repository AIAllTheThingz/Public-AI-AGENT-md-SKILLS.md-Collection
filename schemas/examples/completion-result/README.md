---
id: SCHEMA-EX-COMPLETION-RESULT-001
title: Completion Result Examples
version: 0.3.0
status: baseline
---

# Completion Result Examples

## Current v2 positive example

[`valid.example.json`](valid.example.json) must validate against:

- [`../../completion-result.schema.json`](../../completion-result.schema.json)
- [`../../v2/completion-result.schema.json`](../../v2/completion-result.schema.json)

It demonstrates `schemaVersion: "2.0.0"`, required `executionDiscipline` evidence, and a passed validation whose `objectiveId` matches the exact retry-ledger key for a current completion record.

## Authorized reset positive example

[`valid-reset.example.json`](valid-reset.example.json) must validate against the rolling and v2 schemas and pass the semantic validator. It uses one `retryLedger` map keyed by objective, stores the failure summary in that objective's `failedOrIndeterminateOutcomes` array, preserves successful evidence that ends before the terminal attempt starts in `preTerminalNonConsumingActions`, and retains the stopped first sequence and its delegated handoff under `priorUnresolvedSequences`. It then records a non-delegated current sequence whose reset authorization names `sequence-1` and occurs after its terminal end but before sequence 2 starts.

## Preserved v1 compatibility examples

The [`valid-v1.example.json`](valid-v1.example.json) compatibility fixture must validate against the unchanged [`../../v1/completion-result.schema.json`](../../v1/completion-result.schema.json). It remains available for historical records and pinned v1 consumers and is not expected to satisfy v2.

The [`invalid-v1.example.json`](invalid-v1.example.json) compatibility fixture must fail that same v1 schema because its `status` is outside the preserved enum. Together, the fixtures detect both accidental narrowing and accidental broadening of the historical contract.

## Negative examples

[`invalid.example.json`](invalid.example.json) is intentionally invalid under the current v2 contract because it duplicates the same objective across the removed top-level `failedOrIndeterminateOutcomes` map and the authoritative `retryLedger`. Current records use one `retryLedger` map keyed by objective, with each objective's own `failedOrIndeterminateOutcomes` array, so a failure ledger and a success-only ledger cannot split one objective and bypass reset authorization.

[`invalid-retry.example.json`](invalid-retry.example.json) is intentionally invalid because `retry1` repeats an action without the retry-specific `materialChange` and `causalRationale` evidence required to show why it may now succeed.

[`invalid-delegation.example.json`](invalid-delegation.example.json) is intentionally invalid because it marks a sequence handoff as delegated but omits `meaningfulValue`, `blocker`, `retryCount`, and `unresolvedState`; the containing objective's non-empty `failedOrIndeterminateOutcomes` array supplies the handoff's authoritative failure evidence.

[`invalid-delegation-count.example.json`](invalid-delegation-count.example.json) is intentionally invalid because the handoff is embedded in a sequence containing `retry2`, but it understates that same sequence's evidence with `retryCount: 0` instead of the required value `2`.

[`invalid-post-terminal-action.example.json`](invalid-post-terminal-action.example.json) is intentionally invalid because a sequence that ends `reported-unresolved` includes a later successful `nonConsumingActions` entry. Terminal unresolved sequences store only earlier evidence in `preTerminalNonConsumingActions` and require `nonConsumingActions` to be empty, so further action needs a separately authorized reset sequence.

[`invalid-pre-terminal-order.example.json`](invalid-pre-terminal-order.example.json) is structurally valid but semantically invalid because its alleged pre-terminal action ends after the unresolved terminal attempt starts. This fixture prevents a later action from being laundered into `preTerminalNonConsumingActions`.

[`invalid-validation-objective.example.json`](invalid-validation-objective.example.json) is structurally valid but semantically invalid because its passed validation names objective A while the only `Successful` action belongs to objective B. Each executed validation must correlate with action evidence under its exact `objectiveId` ledger key.

## Boundary

Direct JSON Schema evaluation demonstrates structural conformance only. The repository validator additionally exercises the documented completion-result semantic relationships. Neither result represents a production record, authorized decision, genuine artifact, executed command, or accepted risk.
