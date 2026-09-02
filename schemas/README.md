---
id: SCHEMA-INDEX-001
title: Schema Contracts
version: 0.4.0
status: baseline
---

# Schema Contracts

## Purpose

This directory defines the repository's machine-readable contracts for standards composition, risk, exceptions, testing, artifacts, and completion evidence.

Schemas make records structurally testable. They do not prove that the record is truthful, complete, authorized, secure, compliant, or tied to the correct artifact. A beautifully valid lie remains a lie, merely one with matching braces.

## Current dialect and implementation baseline

The schemas use JSON Schema Draft 2020-12.

The repository validator uses Python and the `jsonschema` package. The pinned validation dependency is documented under [`tools/validate-schemas/`](../tools/validate-schemas/).

Official references:

- [JSON Schema specification](https://json-schema.org/specification)
- [Draft 2020-12 meta-schema](https://json-schema.org/draft/2020-12/schema)
- [Python jsonschema documentation](https://python-jsonschema.readthedocs.io/)

## Schema catalog

| Schema | Purpose | Common repository instances |
|---|---|---|
| [`artifact-record.schema.json`](artifact-record.schema.json) | Identify an artifact, source revision, digest, provenance, and signing state. | `artifact-record*.json` |
| [`completion-result.schema.json`](completion-result.schema.json) | Record completion state, validation, execution discipline, limitations, risk, and review under current major v2. | `completion-result*.json` |
| [`exception-record.schema.json`](exception-record.schema.json) | Record time-bounded standards exceptions and compensating controls. | `exception-record*.json` |
| [`project-manifest.schema.json`](project-manifest.schema.json) | Declare profile and package composition for a project. | `project-manifest.json` |
| [`risk-classification.schema.json`](risk-classification.schema.json) | Record risk level, rationale, factors, reviewers, and rollback need. | `risk-classification*.json` |
| [`test-evidence.schema.json`](test-evidence.schema.json) | Record exact validation commands, results, environment, and limitations. | `test-evidence*.json` |

See [`SCHEMA_CATALOG.md`](SCHEMA_CATALOG.md) for field-level ownership and instance discovery.

## Stable paths and versioned paths

Rolling and versioned paths are provided for each contract:

- `schemas/<name>.schema.json` is the rolling convenience entry point.
- `schemas/v2/completion-result.schema.json` is the current major-version 2 completion-result contract.
- `schemas/v1/completion-result.schema.json` is the unchanged historical major-version 1 completion-result contract.
- `schemas/v1/<name>.schema.json` remains the current major-version 1 contract for the other five schemas.

Long-lived automation should use the applicable major-version path. Consumers requiring an exact immutable contract must also pin a repository tag or commit. The rolling path may advance according to the compatibility policy; the completion-result rolling path follows v2.

The six original filenames remain intact.

## Compatibility objective

The current completion-result rolling and v2 contracts require `executionDiscipline` and use `schemaVersion: "2.0.0"`. The v1 completion-result contract remains supported and unchanged for historical or pinned consumers. The other five contracts remain version 1.

Within a v2 retry ledger, each objective separates zero or more `priorUnresolvedSequences` from exactly one `currentSequence`. Only a sequence whose final attempt is failed or indeterminate with `reported-unresolved` may be preserved as a prior sequence; a current sequence after any prior sequence requires reset evidence for the prior stop/report, separate accountable authorization, and the material blocker or relevant scope or system-state change. A sequence may omit `attempts` only when it contains at least one successful `nonConsumingActions` entry, so evidence-only activity is recorded without fabricating a budgeted attempt; `status: "validated"` requires at least one reported `passed` validation, and any reported `passed` validation requires at least one `Successful` ledger action, while a reported `failed` validation requires a non-empty failed-or-indeterminate outcome. `retry-authorized` requires the corresponding next retry to be present. Non-empty failed or indeterminate outcomes require at least one objective ledger containing an actual failed or indeterminate attempt, while separate success-only objective ledgers remain permitted; an empty outcomes array permits only ledgers without failed or indeterminate attempts. Delegated work must record `boundariesPreserved: true`. Successful objective-clearing actions remain recorded at their current retry position and cannot be followed by another sequence for that objective.

The completion-result v1-to-v2 upgrade is breaking because it adds required execution-discipline evidence. Existing v1 completion records remain valid when evaluated against the preserved v1 contract; they are not silently reinterpreted as v2.

See:

- [`VERSIONING_POLICY.md`](VERSIONING_POLICY.md)
- [`COMPATIBILITY_POLICY.md`](COMPATIBILITY_POLICY.md)
- [`MIGRATION_GUIDE.md`](MIGRATION_GUIDE.md)

## Extension model

All six schemas remain closed by default with `additionalProperties: false`.

Projects may add organization-specific data only inside the optional `extensions` object. Extension keys must be namespaced and must not redefine standard fields.

Completion-result v2 instances use `schemaVersion: "2.0.0"`; preserved v1 completion records use `1.0.0` or omit the property only when directly validated against the pinned v1 contract. Repository instance discovery routes an omitted `schemaVersion` to the current major, so retained v1 completion records discovered by the repository validator must explicitly declare `1.0.0`. The other version 1 contracts use `1.0.0`, except project manifests using infrastructure package arrays, which use `1.1.0`.

See [`EXTENSION_POLICY.md`](EXTENSION_POLICY.md).

## Validation

Install the pinned dependency:

```bash
python -m pip install -r tools/validate-schemas/requirements.txt
```

Run all repository schema validation:

```bash
python tools/validate-schemas/validate_schemas.py
```

The validator:

- validates every schema against Draft 2020-12
- verifies each rolling schema matches its current versioned major except for identifier metadata (completion-result v2; other schemas v1)
- validates positive examples
- confirms negative examples fail
- discovers and validates repository instances by filename
- enables format checking for dates and date-times
- reports the instance path and failing JSON pointer

Use the rolling or v2 completion-result schema for new/current records and the v1 completion-result schema for retained historical or pinned v1 records. The current validator must select the schema that matches the record's declared or pinned major; it must not silently validate a historical v1 record against v2.

See [`VALIDATION_GUIDE.md`](VALIDATION_GUIDE.md).

## Examples

Each schema has:

- one positive example that must validate
- one negative example that must fail
- a README explaining what the example proves and does not prove

Examples are under [`examples/`](examples/).

The completion-result examples include a current v2 positive/negative pair and preserved v1 positive/negative compatibility fixtures.

Negative examples are intentionally invalid. Do not copy them into production unless the production goal is to test whether anyone is awake.

## Required change process

Before changing a schema:

1. Identify affected instances and consumers.
2. Classify the change as compatible, conditionally compatible, or breaking.
3. Update rolling and versioned contracts deliberately.
4. Add or update positive and negative examples.
5. Update migration and compatibility guidance.
6. Run schema meta-validation and instance validation.
7. Review whether formats, enums, required fields, or closed-object behavior changed.
8. Record checks not run and unresolved consumer impact.
9. Obtain accountable review for breaking or evidence-affecting changes.

## Completion boundary

Schema validation proves only that an instance conforms to the selected structural contract under the validator used.

It does not prove:

- the evidence is genuine
- the command actually ran
- the reviewer has authority
- the risk classification is correct
- the artifact digest matches the deployed artifact
- the exception remains acceptable
- the project is production-ready
- a compliance obligation has been satisfied
