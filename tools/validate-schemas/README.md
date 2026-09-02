---
id: TOOL-PKG-VALIDATE-SCHEMAS-001
title: Validate Schemas Tool
version: 1.2.0
status: baseline
---

# Validate Schemas Tool

## Purpose

Validate Draft 2020-12 schemas, versioned equivalence, positive and negative examples, formats, and repository instances.

Status: **baseline**

## Stable entry point

[`validate_schemas.py`](validate_schemas.py)

The stable path is part of the repository tooling contract. Moving or renaming it requires migration guidance and CI updates.

## Operating mode

- Reads: schema files and matching JSON instances
- Writes: only an optional result file
- Network: none
- Default behavior: safe and non-destructive

## Dependencies

[`requirements.txt`](requirements.txt) records the small direct dependency intent for maintainers and dependency-update tooling.

[`requirements.lock`](requirements.lock) is the generated, fully resolved, SHA-256-hashed dependency set used by hosted validation and release workflows. It is generated with Python 3.13 and must be refreshed whenever the direct requirement changes.

Hosted CI installs the lock with `pip --require-hashes`. The tool validator checks that direct requirements remain represented in the lock and that the lock contains SHA-256 hashes.

## Common options

```text
--root PATH
--format text|json
--output PATH
--quiet
--help
```

Tool-specific options are shown by:

```bash
python tools/validate-schemas/validate_schemas.py --help
```

## Checks and behavior

- schema meta-validation
- unique $id values
- remote $ref rejection
- rolling and versioned equivalence
- positive examples
- negative examples
- repository instance discovery
- current-major selection for unversioned records; retained completion-result v1 records must explicitly declare `schemaVersion: "1.0.0"`

## Examples

For the same dependency boundary used by hosted CI:

```bash
python -m pip install --require-hashes -r tools/validate-schemas/requirements.lock
python tools/validate-schemas/validate_schemas.py
```

```bash
python tools/validate-schemas/validate_schemas.py --skip-repository-instances
```

## Text and JSON results

Text output is for interactive use. JSON output conforms to [`../contracts/tool-result.schema.json`](../contracts/tool-result.schema.json).

Finding codes are intended for automation. Message wording may improve, but a finding code must not silently change meaning.

## Exit codes

- `0`: completed and passed
- `1`: completed with validation failures
- `2`: invalid input, missing configuration, or dependency issue
- `3`: unexpected internal failure

## Safety requirements

- Repository paths are resolved from `--root`.
- The tool does not fetch external content.
- Sensitive values must not be included in findings.
- A passed result must not be described as proof beyond the implemented checks.
- Wrappers must preserve nonzero exit codes.

## Failure behavior

Input and configuration failures produce status `error`. Validation findings produce status `failed`. Unexpected exceptions produce status `error` and exit code `3`.

Do not catch and discard failures merely to keep CI green. Green output created by suppressing errors is not validation. It is interior decoration.

## Test coverage

Central tests live under [`../tests/`](../tests/).

Run focused tests:

```bash
python -m unittest discover -s tools/tests -p "test_validate_schemas*.py"
```

Run the complete suite:

```bash
python tools/validate-all/run_all.py --include-tests
```

## Compatibility

Backward-compatible changes may add optional flags, summary fields, metadata, or new finding codes.

Breaking changes include:

- changing the stable entry path
- changing exit-code meaning
- removing JSON fields
- changing default write or overwrite behavior
- changing generated file semantics
- silently narrowing accepted input

## Limitations

- structural validity is not semantic truth
- instance discovery is filename-based
- remote schema resolution is intentionally unsupported
- the checked-in lock represents the hosted Python/runtime boundary and must be regenerated when that boundary changes

## Review checklist

Reviewers should confirm:

- documented behavior matches code
- positive and negative tests exist
- output and exit codes are stable
- filesystem and subprocess handling are safe
- dependency changes are pinned, hash-locked for hosted CI, and justified
- compatibility impact is documented
- the complete pipeline passes

## Maintenance

Update the script, dependency input and lock, README, manifest, examples, tests, catalog, and CI together when behavior changes.

## Completion boundary

A successful execution establishes only the outcome of this tool's implemented checks or generation plan against the identified input. It does not grant authority, certify compliance, or prove production readiness.
