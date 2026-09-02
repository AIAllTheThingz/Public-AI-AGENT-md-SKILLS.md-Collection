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
8. current-major schema selection (completion-result v2; other contracts v1) with preserved v1 completion compatibility

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
- For completion-result v2 retry sequences, require `retry-authorized` on the preceding failed or indeterminate attempt before `retry1` or `retry2`; reject execution after `reported-unresolved`.

## Local consumer validation

Adopting repositories should add:

- representative contract tests
- producer tests
- consumer tests
- stored-record migration tests
- negative tests
- version compatibility tests
- CI gating for material records
