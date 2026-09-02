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
- For completion-result v2, use one `retryLedger` map keyed by objective and store each objective's `failedOrIndeterminateOutcomes` array and `delegationHandoff` inside that objective's ledger. Require the array to be non-empty exactly when the same ledger contains a Failed or Indeterminate attempt; reject the obsolete second objective map so a failure ledger and success-only ledger cannot split one objective. Require every `retry1` and `retry2` action to record a causally relevant `materialChange` and `causalRationale`; generic justification without both fields is invalid. Store completed earlier sequences under `priorUnresolvedSequences` only when their final attempt is failed or indeterminate with `reported-unresolved`, and store the latest sequence under `currentSequence`. A sequence without `attempts` must contain at least one successful `nonConsumingActions` entry; reject an empty sequence. Require at least one `passed` validation for `status: "validated"`, at least one `Successful` action in the ledger whenever `validation` reports a `passed` result, and at least one objective ledger with failure evidence whenever validation reports `failed`. Require reset evidence, including causal rationale, on the current sequence when any prior sequence exists; require `retry-authorized` only with the corresponding next retry, reject execution after `reported-unresolved`, and reject another sequence after objective completion. Require every per-objective handoff to declare `delegated`; when true, use that same ledger's outcomes as authoritative failure evidence, require meaningful value, blocker, unresolved state, and `boundariesPreserved: true`, and require `retryCount` to equal the current sequence's actual 0/1/2 retry depth.
- For a delegated handoff, additionally require that objective's current sequence to end `reported-unresolved`; reject delegation records attached to completed or still-retrying sequences.

## Local consumer validation

Adopting repositories should add:

- representative contract tests
- producer tests
- consumer tests
- stored-record migration tests
- negative tests
- version compatibility tests
- CI gating for material records
