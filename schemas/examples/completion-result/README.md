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

[`valid-reset.example.json`](valid-reset.example.json) must validate against the rolling and v2 schemas. Under one `failedOrIndeterminateOutcomes` objective key, it co-locates the failure summary and complete retry ledger, preserves the stopped and reported first sequence under `priorUnresolvedSequences`, then records separate authorization and material-change evidence on `currentSequence` before completing the objective.

## Preserved v1 compatibility examples

The [`valid-v1.example.json`](valid-v1.example.json) compatibility fixture must validate against the unchanged [`../../v1/completion-result.schema.json`](../../v1/completion-result.schema.json). It remains available for historical records and pinned v1 consumers and is not expected to satisfy v2.

The [`invalid-v1.example.json`](invalid-v1.example.json) compatibility fixture must fail that same v1 schema because its `status` is outside the preserved enum. Together, the fixtures detect both accidental narrowing and accidental broadening of the historical contract.

## Negative example

[`invalid.example.json`](invalid.example.json) is intentionally invalid under the current v2 contract because it reports failures for two objectives but supplies the required per-objective retry ledger for only one. Every failed-or-indeterminate outcome key must carry its own non-empty summaries and failure-bearing retry evidence.

## Boundary

A positive example demonstrates structural conformance only. It does not represent a production record, authorized decision, genuine artifact, executed command, or accepted risk.
