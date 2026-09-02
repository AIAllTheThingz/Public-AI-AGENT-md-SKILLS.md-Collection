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
- For completion-result v2 retry ledgers, store completed earlier sequences under `priorUnresolvedSequences` only when their final attempt is failed or indeterminate with `reported-unresolved`, and store the latest sequence under `currentSequence`. A sequence without `attempts` must contain at least one successful `nonConsumingActions` entry; reject an empty sequence. Key every failure report by objective under `failedOrIndeterminateOutcomes`, require each value to carry non-empty outcome summaries and that objective's failure-bearing retry ledger, and reserve the separate `retryLedger` field for success/evidence-only objectives. Require at least one `passed` validation for `status: "validated"`, at least one `Successful` action across either ledger location whenever `validation` reports a `passed` result, and at least one keyed failure report whenever validation reports `failed`. Require reset evidence on the current sequence when any prior sequence exists, require `retry-authorized` only with the corresponding next retry, reject execution after `reported-unresolved`, and reject another sequence after objective completion. `delegationHandoff.boundariesPreserved` must be `true`.

## Local consumer validation

Adopting repositories should add:

- representative contract tests
- producer tests
- consumer tests
- stored-record migration tests
- negative tests
- version compatibility tests
- CI gating for material records
