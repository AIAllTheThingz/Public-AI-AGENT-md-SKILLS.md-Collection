---
id: SCHEMA-VALIDATE-001
title: Schema Validation Guide
version: 0.3.0
status: baseline
---

# Schema Validation Guide

## Install

```bash
python -m pip install -r tools/validate-schemas/requirements.txt
```

## Run

```bash
python tools/validate-schemas/validate_schemas.py
```

## Validation layers

1. JSON parsing
2. Draft 2020-12 meta-schema validation
3. rolling-versus-versioned equivalence
4. positive example validation
5. negative example rejection
6. repository instance discovery and validation
7. date and date-time format checking
8. current-major schema selection (completion-result v2; other contracts v1) with preserved positive and negative v1 completion compatibility fixtures
9. completion-result v2 semantic consistency after structural validation succeeds

## Error interpretation

Validation output identifies:

- instance file
- schema file
- JSON pointer to the failing value
- validator rule
- human-readable error

A validation error should be resolved by one of:

- correcting the instance
- correcting an unintended schema defect
- performing an approved versioned schema change
- documenting an explicit migration

Disabling validation is not remediation.

## Schema selection

- Validate new or current completion-result records against the rolling or `schemas/v2/completion-result.schema.json` contract, including required `executionDiscipline` and `schemaVersion: "2.0.0"`.
- Validate retained historical or pinned v1 completion-result records against the unchanged `schemas/v1/completion-result.schema.json` contract and explicitly declare `schemaVersion: "1.0.0"` when repository instance discovery is used.
- Validate the other contracts against their current `schemas/v1/` major paths.
- Repository instance discovery selects the current major when `schemaVersion` is omitted; do not rely on omission to identify a v1 historical record.
- For completion-result v2, use one `retryLedger` map keyed by objective, store each objective's `failedOrIndeterminateOutcomes` array inside that objective's ledger, and store `delegationHandoff` inside every prior and current sequence. Require the outcome array to be non-empty exactly when the same ledger contains a Failed or Indeterminate attempt; reject the obsolete second objective map so a failure ledger and success-only ledger cannot split one objective. Require every `retry1` and `retry2` action to record a causally relevant `materialChange` and `causalRationale`; generic justification without both fields is invalid. Store completed earlier sequences under `priorUnresolvedSequences` only when their final attempt is failed or indeterminate with `reported-unresolved`; store successful evidence gathered before that stop in `preTerminalNonConsumingActions`, require `nonConsumingActions` to be empty, and store the latest sequence under `currentSequence`. For sequences that do not end unresolved, require `preTerminalNonConsumingActions` to be empty. A sequence without `attempts` must contain at least one successful `nonConsumingActions` entry; reject an empty sequence. Require at least one `passed` validation for `status: "validated"`. Every `passed` or `failed` validation must set `objectiveId` to the exact key of its objective ledger and `actionId` to the unique action that performed that check. The semantic validator requires the referenced action to exist exactly once and carry a result compatible with the validation; an unrelated action in the same objective cannot satisfy it. Require reset evidence on every sequence after the first, including `priorSequenceId`, `authorizedAt`, prior stop/report, accountable authorizer, authorization evidence, material change, and causal rationale. The semantic validator requires unique per-objective sequence IDs, the reset to identify the immediately prior sequence, prior terminal end <= authorization time <= new sequence start, each action start <= end, retries ordered after their predecessors, every pre-terminal action to end before the terminal unresolved attempt starts, and every other action to end before an objective-completing attempt starts. Accepted RFC 3339 leap seconds are normalized for these comparisons. Require `retry-authorized` only with the corresponding next retry, reject actions after `reported-unresolved` or `objective-completed`, and reject another sequence after objective completion. Require every per-sequence handoff to declare `delegated`; when true, use the containing objective ledger's outcomes as authoritative failure evidence, require meaningful value, blocker, unresolved state, and `boundariesPreserved: true`, and require `retryCount` to equal that sequence's actual 0/1/2 retry depth.
- Direct use of the JSON Schema validates structure only. Completion-result v2 conformance requires `python tools/validate-schemas/validate_schemas.py` (or an equivalent implementation of the documented semantic rules) so cross-record and temporal contradictions cannot pass as valid evidence.
- For a delegated handoff, additionally require its containing sequence to end `reported-unresolved`; reject delegation records attached to completed or still-retrying sequences. Retain a prior sequence's handoff when a separately authorized reset creates a new current sequence.

## Local consumer validation

Adopting repositories should add:

- representative contract tests
- producer tests
- consumer tests
- stored-record migration tests
- negative tests
- version compatibility tests
- CI gating for material records
