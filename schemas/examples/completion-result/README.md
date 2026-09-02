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

[`valid-reset.example.json`](valid-reset.example.json) must validate against the rolling and v2 schemas. It preserves the stopped and reported first sequence, then records separate authorization and material-change evidence on the second sequence before completing the objective.

## Preserved v1 compatibility example

The [`valid-v1.example.json`](valid-v1.example.json) compatibility fixture must validate against the unchanged [`../../v1/completion-result.schema.json`](../../v1/completion-result.schema.json). It remains available for historical records and pinned v1 consumers and is not expected to satisfy v2.

## Negative example

[`invalid.example.json`](invalid.example.json) is intentionally invalid under the current v2 contract because it records a retry after the preceding attempt reported the objective unresolved. A subsequent retry requires the preceding failed or indeterminate attempt to use `retry-authorized`.

## Boundary

A positive example demonstrates structural conformance only. It does not represent a production record, authorized decision, genuine artifact, executed command, or accepted risk.
