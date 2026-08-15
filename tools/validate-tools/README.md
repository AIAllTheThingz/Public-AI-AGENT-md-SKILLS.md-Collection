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

`--help` remains available before PyYAML is installed. A real validation run without PyYAML reports a structured dependency/input error through the common CLI contract and exits with code `2`.

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
- statically declared matrix runner values evaluated after `exclude`; later `include` entries are also inspected because GitHub can add combinations back after exclusion

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
- `WORKFLOW_RUNNER_UNRESOLVED`

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

Input, configuration, and required-dependency failures produce status `error` and exit code `2`. Validation findings produce status `failed`. Unexpected exceptions produce status `error` and exit code `3`.

Do not catch and discard failures merely to keep CI green. Green output created by suppressing errors is not validation. It is interior decoration.

## Test coverage

Central tests live under [`../tests/`](../tests/).

The repository requires at least one test module per declared tool package. The release package is covered by `test_release.py`.

Regression coverage includes exact direct-dependency/lock comparison, per-resolved-dependency hash enforcement, inline requirement comments, missing-PyYAML CLI behavior, quoted YAML action values, YAML key-spacing variants, immutable Docker digests, local composite-action dependency traversal, effective matrix runner exclusions, and floating action/runner rejection.

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

## Limitations

- compilation is not runtime correctness
- unit tests run only when requested
- package presence does not prove every secondary script is fully exercised
- dependency hashes establish lock integrity, not package provenance, vulnerability status, or trustworthiness
- action pinning establishes immutable references, not third-party provenance or vulnerability status
- local composite-action traversal follows actions referenced by repository workflows; unreferenced local metadata is not treated as an executed CI dependency
- dynamic runner expressions that cannot be resolved from a static matrix are rejected as unresolved rather than guessed
- static matrix evaluation covers declared axes, partial-match `exclude`, and runner values supplied by later `include` entries; it does not execute arbitrary expressions to discover dynamically generated matrices
- does not inspect private GitHub workflow permissions, environment protection rules, or repository rulesets

## Review checklist

Reviewers should confirm:

- documented behavior matches code
- the declared package list is complete
- release scripts are compiled and tested
- positive, negative, and error-path tests exist
- `--help` remains usable before optional/runtime validation dependencies are installed
- dependency failures preserve structured output and exit code `2`
- every resolved lock entry has a valid SHA-256 hash and direct dependency drift is detected in both directions
- workflow action checks are limited to semantic action positions and recursively inspect referenced local composite actions
- matrix runner validation respects effective exclusions and rejects unresolved dynamic values
- output and exit codes are stable
- filesystem and subprocess handling are safe
- dependency changes are pinned and justified
- compatibility and release impact are documented
- the complete pipeline passes

## Maintenance

Update the script, README, manifest, examples, tests, catalog, changelog, release notes, and CI together when behavior changes. Regenerate the validation lock whenever the direct dependency set or hosted Python boundary changes.

## Completion boundary

A successful execution establishes only that the declared tool package structure, dependency-lock checks, workflow pinning checks, compilation checks, and other implemented structural validations passed. It does not prove runtime correctness, third-party provenance, vulnerability absence, release authority, repository-host configuration, compliance, or production readiness.
