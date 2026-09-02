---
id: SCHEMA-MIGRATE-001
title: Schema Migration Guide
version: 0.4.0
status: baseline
---

# Schema Migration Guide

## Migration from the original baseline

The original six rolling filenames remain available.

Version 1 adds:

- versioned copies under `schemas/v1/`
- descriptions and stronger non-empty constraints
- optional `schemaVersion`
- optional namespaced `extensions`
- additional optional evidence metadata
- executable positive and negative validation
- format checking for dates and date-times

Existing records remain valid against their selected preserved major; completion records selected against the new v2 rolling/current contract require the migration below.

## Recommended consumer migration

1. Inventory every producer and consumer.
2. Use the current major-version path (`schemas/v2/` for completion-result and `schemas/v1/` for other contracts), and pin a repository tag or commit when exact immutability is required. Use `schemas/v1/completion-result.schema.json` for retained v1 records or pinned v1 consumers.
3. Install or configure a Draft 2020-12 validator.
4. Enable format checking.
5. Validate stored representative records.
6. Add the current supported `schemaVersion` to newly produced records (`2.0.0` for completion-result v2, `1.1.0` for project manifests using infrastructure package arrays, otherwise `1.0.0`); explicitly mark repository-discovered retained completion-result v1 records as `1.0.0` because omission selects the current major.
7. Move non-standard fields under `extensions`.
8. Record failures and correct producers rather than weakening the contract.
9. Add contract tests to CI.
10. Retain the schema version with archived evidence.

## Rolling-path consumers

Consumers using `schemas/<name>.schema.json` should follow the current major for that contract: completion-result rolling is v2, while the other rolling contracts remain v1. Consumers requiring an exact immutable artifact should resolve the applicable major path from a pinned repository tag or commit. Retained v1 completion records must use `schemas/v1/completion-result.schema.json`.

## Completion-result v2 migration

Moving the rolling/current completion-result contract from v1 to v2 is a breaking change because v2 requires `executionDiscipline` and `schemaVersion: "2.0.0"`.

Producers of new or current records must emit v2 records and populate failed or indeterminate outcomes, authorization and recovery continuity, the per-action retry ledger and terminal/reset evidence, progress or blocker narrowing, delegation handoff and boundary continuity, and authorized out-of-scope routing. For each objective, store zero or more completed earlier sequences under `priorUnresolvedSequences` only when their final attempt is failed or indeterminate with `reported-unresolved`, then store exactly one latest sequence under `currentSequence`. The current sequence has no reset authorization when no prior sequence exists; otherwise it records the prior stop/report, separate accountable authorization, and material blocker or relevant scope or system-state change. Record successful evidence-only activity under `nonConsumingActions`; a sequence may omit `attempts` only when that array contains at least one action, preventing both fabricated budgeted attempts and empty sequences, and any reported `passed` validation requires a non-empty ledger. Record each successful objective-clearing action at its current retry position, require `retry-authorized` only when the corresponding next retry is present, do not create another sequence after objective completion, and include at least one objective ledger whenever failed or indeterminate outcomes are reported. Every supplied ledger must contain an actual failed or indeterminate attempt, and any failed or indeterminate ledger attempt requires a non-empty outcomes array. Delegated work must set `delegationHandoff.boundariesPreserved` to `true`. Consumers must update schema selection and bindings to read `executionDiscipline` and validate current records against the rolling or v2 schema.

Retain existing v1 records and validate them against `schemas/v1/completion-result.schema.json`; pinned v1 consumers may remain on that major path. Repository-discovered retained v1 records must explicitly declare `schemaVersion: "1.0.0"`, while direct consumers pinned to v1 may continue accepting omission as the unchanged v1 contract permits. The current validator selects v2 for omitted, current, or new completion records and v1 only for records explicitly marked or pinned at v1. The compatibility class is breaking for completion-result consumers; all other schemas remain v1.

## Project manifest 1.1

Project-manifest version `1.1.0` adds three optional standard package arrays:

- `virtualization`
- `operatingSystems`
- `networking`

Version `1.0.0` manifests remain valid and require no migration when these package classes are not selected. The schema requires `schemaVersion: "1.1.0"` whenever any new array is present. Producers must verify each slug against the corresponding repository package directory and update composition consumers to include the selected package entry points.

The repository's `generate-manifest` and `compose-agents` tools version `1.1.0` implement these selections. Consumers pinned to an earlier tool version must upgrade before relying on the new fields.

## Identifier note

Schema `$id` values now use repository-backed canonical URLs. Consumers that cached the former placeholder completion-result identifier should update their registry mapping and record the migration.
