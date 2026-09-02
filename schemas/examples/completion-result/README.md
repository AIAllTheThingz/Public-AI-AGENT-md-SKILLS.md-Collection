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

It demonstrates `schemaVersion: "2.0.0"` and required `executionDiscipline` evidence for a current completion record.

## Authorized reset positive example

[`valid-reset.example.json`](valid-reset.example.json) must validate against the rolling and v2 schemas. It uses one `retryLedger` map keyed by objective, stores the failure summary in that objective's `failedOrIndeterminateOutcomes` array, preserves the stopped and reported first sequence under `priorUnresolvedSequences`, then records separate authorization and material-change evidence on `currentSequence` before completing the objective.

## Preserved v1 compatibility examples

The [`valid-v1.example.json`](valid-v1.example.json) compatibility fixture must validate against the unchanged [`../../v1/completion-result.schema.json`](../../v1/completion-result.schema.json). It remains available for historical records and pinned v1 consumers and is not expected to satisfy v2.

The [`invalid-v1.example.json`](invalid-v1.example.json) compatibility fixture must fail that same v1 schema because its `status` is outside the preserved enum. Together, the fixtures detect both accidental narrowing and accidental broadening of the historical contract.

## Negative example

[`invalid.example.json`](invalid.example.json) is intentionally invalid under the current v2 contract because it duplicates the same objective across the removed top-level `failedOrIndeterminateOutcomes` map and the authoritative `retryLedger`. Current records use one `retryLedger` map keyed by objective, with each objective's own `failedOrIndeterminateOutcomes` array, so a failure ledger and a success-only ledger cannot split one objective and bypass reset authorization.

## Boundary

A positive example demonstrates structural conformance only. It does not represent a production record, authorized decision, genuine artifact, executed command, or accepted risk.
