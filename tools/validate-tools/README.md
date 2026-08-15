---
id: TOOL-PKG-VALIDATE-TOOLS-001
title: Validate Tools Tool
version: 1.3.2
status: baseline
---

# Validate Tools Tool

## Purpose

Validate tool package structure, stable entry points, Python compilation, contracts, dependency-lock integrity, GitHub Actions workflow pinning, documentation, and unit-test coverage.

Status: **baseline**

## Stable entry point

[`validate_tools.py`](validate_tools.py)

The stable path is part of the repository tooling contract. Moving or renaming it requires migration guidance, release classification, and CI updates.

## Operating mode

- Reads: the tools collection, tests, validation dependency files, GitHub Actions workflows, and referenced local composite-action metadata
- Writes: only an optional result file
- Network: none
- External dependency: `PyYAML` for structural workflow and local action metadata parsing
- Default behavior: safe and non-destructive

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
python tools/validate-tools/validate_tools.py --help
```

## Tool packages checked

The validator requires these packages:

- `validate-standards`
- `check-links`
- `validate-skills`
- `validate-schemas`
- `validate-templates`
- `validate-tools`
- `generate-manifest`
- `compose-agents`
- `validate-all`
- `release`

The release package contains both `validate_release.py` and `build_release.py`. Every Python entry point in a package is compiled, not merely the primary validator path.

## Checks and behavior

- required tools collection documents
- package README, manifest, examples, and primary entry point
- unique front-matter IDs
- README depth
- planned-tool remnants
- Python compilation for package entry points
- test-module count
- JSON result contract
- release-package presence
- at least one valid SHA-256 hash for every resolved dependency in the validation lock
- exact normalized representation of each direct validation dependency in the resolved lock
- ordinary inline comments in direct requirement files without treating comments as requirement text
- structural parsing of GitHub Actions YAML rather than line-oriented pattern matching
- third-party repository actions pinned to full 40-character Git commit SHAs
- `docker://` actions pinned to immutable `sha256:<64-hex>` OCI digests
- referenced local composite actions recursively checked for nested external `uses` dependencies
- hosted runners using explicit image families rather than `*-latest`

Local workflow action references such as `./path/to/action` do not require a Git commit pin themselves. When they resolve to composite-action metadata, external `uses` references inside that metadata are inspected recursively and must satisfy the same immutable-pin rules.

## Examples

```bash
python tools/validate-tools/validate_tools.py
```

```bash
python tools/validate-tools/validate_tools.py --run-unit-tests
```

## Text and JSON results

Text output is for interactive use. JSON output conforms to [`../contracts/tool-result.schema.json`](../contracts/tool-result.schema.json).

Finding codes are intended for automation. Message wording may improve, but a finding code must not silently change meaning.

Workflow/dependency findings include:

- `DEPENDENCY_INPUT_MISSING`
- `DEPENDENCY_LOCK_MISSING`
- `DEPENDENCY_LOCK_UNHASHED`
- `DEPENDENCY_LOCK_OUT_OF_SYNC`
- `WORKFLOW_YAML_INVALID`
- `WORKFLOW_ACTION_INVALID`
- `WORKFLOW_ACTION_NOT_PINNED`
- `WORKFLOW_DOCKER_NOT_PINNED`
- `WORKFLOW_RUNNER_FLOATING`

## Exit codes

- `0`: completed and passed
- `1`: completed with validation failures
- `2`: invalid input, missing configuration, or dependency issue
- `3`: unexpected internal failure

## Safety requirements

- Repository paths are resolved from `--root`.
- The tool does not fetch external content.
- Workflow YAML and referenced local action metadata are parsed locally; parsed content is inspected but never executed.
- Compilation checks must not execute the target scripts.
- Sensitive values must not be included in findings.
- A passed result must not be described as proof beyond the implemented checks.
- Wrappers must preserve nonzero exit codes.

## Failure behavior

Input and configuration failures produce status `error`. Validation findings produce status `failed`. Unexpected exceptions produce status `error` and exit code `3`.

Do not catch and discard failures merely to keep CI green. Green output created by suppressing errors is not validation. It is interior decoration.

## Test coverage

Central tests live under [`../tests/`](../tests/).

The repository requires at least one test module per declared tool package. The release package is covered by `test_release.py`.

Regression coverage includes exact direct-dependency/lock comparison, per-resolved-dependency hash enforcement, inline requirement comments, quoted YAML action values, YAML key-spacing variants, immutable Docker digests, local composite-action dependency traversal, and floating action/runner rejection.

Run focused tests:

```bash
python -m unittest discover -s tools/tests -p "test_validate_tools*.py"
```

Run the complete suite:

```bash
python tools/validate-all/run_all.py --include-tests
```

## Compatibility

Backward-compatible changes may add optional flags, summary fields, metadata, package checks, or new finding codes.

Breaking changes include:

- changing the stable entry path
- changing exit-code meaning
- removing JSON fields
- removing a required package without migration
- changing how executable entry points are identified
- changing default write or overwrite behavior
- changing generated file semantics
- silently narrowing accepted input

Changes to the required package set or validation dependency contract must be classified under [`../../RELEASE_POLICY.md`](../../RELEASE_POLICY.md).
