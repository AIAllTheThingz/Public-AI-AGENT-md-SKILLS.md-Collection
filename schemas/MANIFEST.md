---
id: SCHEMA-MANIFEST-001
title: Schema Package Manifest
version: 0.4.0
status: baseline
---

# Schema Package Manifest

## Required collection files

- `AGENTS.md`
- `README.md`
- `SCHEMA_CATALOG.md`
- `VERSIONING_POLICY.md`
- `COMPATIBILITY_POLICY.md`
- `EXTENSION_POLICY.md`
- `MIGRATION_GUIDE.md`
- `VALIDATION_GUIDE.md`
- `DESIGN_RULES.md`
- `CHANGE_CHECKLIST.md`

## Required schema files

Rolling and versioned copies are required for:

- artifact record
- completion result (current v2 and preserved historical v1)
- exception record
- project manifest
- risk classification
- test evidence

## Required examples

Each contract must have:

- `valid.example.json`
- `invalid.example.json`
- example README

## Required tooling

- `tools/validate-schemas/validate_schemas.py`
- `tools/validate-schemas/requirements.txt`
- `tools/validate-schemas/README.md`

## Acceptance checks

- Draft 2020-12 meta-validation passes.
- Each rolling schema matches its current versioned major except for identifier metadata.
- The rolling completion-result schema matches current v2, while the historical v1 completion schema remains present and unchanged.
- Other schemas remain current major version 1.
- All positive examples validate.
- All negative examples fail.
- Preserved completion-result v1 positive and negative compatibility fixtures validate and fail, respectively.
- All discovered repository instances validate.
- Format checking is enabled.
- Every JSON document parses.
- Relative Markdown links pass.
- No schema or example contains an unresolved placeholder.
- The six stable rolling filenames remain present.
