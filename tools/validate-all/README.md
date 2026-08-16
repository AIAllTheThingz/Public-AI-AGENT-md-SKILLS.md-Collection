---
id: TOOL-PKG-VALIDATE-ALL-001
title: Validate All Tool
version: 1.3.0
status: baseline
---

# Validate All Tool

## Purpose

Run the complete repository validation pipeline in a stable order and aggregate structured results.

Status: **baseline**

## Stable entry point

[`run_all.py`](run_all.py)

The stable path is part of the repository tooling contract. Moving or renaming it requires migration guidance, release classification, and CI updates.

## Operating mode

- Reads: validator entry points and repository content
- Writes: only an optional aggregate result file
- Network: none
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
python tools/validate-all/run_all.py --help
```

## Validators

The runner executes:

1. `validate-standards`
2. `check-links`
3. `check-freshness`
4. `validate-skills`
5. `validate-schemas`
6. `validate-templates`
7. `validate-tools`
8. `validate-release`
9. unit tests when `--include-tests` is supplied

`check-freshness` validates the source-review registry and reports recorded review-date state. It is offline and warning-oriented by default, so a `Warning` or `NotRun` maintenance state does not become an aggregate failure unless the child tool itself has error-severity findings.

Release validation checks the repository version, changelog, release notes, migration notes, release and maturity policies, publication state, tag workflow, and optional tag matching.

## Checks and behavior

- validator discovery
- JSON result parsing
- exit-code propagation
- aggregate status
- source-review metadata validation
- skill entry-point and package-routing validation
- repository release-contract validation
- optional unit tests
- optional fail-fast behavior

## Examples

```bash
python tools/validate-all/run_all.py
```

```bash
python tools/validate-all/run_all.py --include-tests --format json --output reports/validation.json
```

Run only source freshness through the aggregator:

```bash
python tools/validate-all/run_all.py \
  --tool check-freshness \
  --format json
```

Run only release validation through the aggregator:

```bash
python tools/validate-all/run_all.py \
  --tool validate-release \
  --format json
```

List validators:

```bash
python tools/validate-all/run_all.py --list
```

## Text and JSON results

Text output is for interactive use. JSON output conforms to [`../contracts/tool-result.schema.json`](../contracts/tool-result.schema.json).

Each child validator result is retained in aggregate metadata with its exit code. Child failures are not converted into wrapper success.

Child summary fields remain available in aggregate metadata. For source freshness, consumers should inspect the child `summary.freshnessState` and `summary.liveSourceVerification` fields rather than treating aggregate success as proof that all external sources were reviewed live.

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
- The runner does not build artifacts, create tags, publish releases, or perform live source verification.

## Failure behavior

Input and configuration failures produce status `error`. Validation findings produce status `failed`. Unexpected exceptions produce status `error` and exit code `3`.

Warning-only child results remain child status `passed` and therefore do not become aggregate failures. This is used by `check-freshness` to surface stale or NotRun maintenance state while keeping structural validation separate from maintenance due dates.

Do not catch and discard failures merely to keep CI green. Green output created by suppressing errors is not validation. It is interior decoration.

## Permanent CI

The permanent repository workflow runs:

```bash
python tools/validate-all/run_all.py --include-tests
```

Tool order remains in this Python entry point rather than being duplicated in workflow YAML.

The freshness checker is included offline in permanent CI. The scheduled source-freshness workflow runs the same checker directly to surface periodic maintenance state.

The tag-driven release workflow runs the same complete pipeline before validating the tag and building release artifacts.

## Test coverage

Central tests live under [`../tests/`](../tests/).

Run focused aggregate tests:

```bash
python -m unittest discover -s tools/tests -p "test_validate_all*.py"
```

Freshness-specific tests are under:

```text
tools/tests/test_check_freshness.py
```

Release-specific tests are under:

```text
tools/tests/test_release.py
```

Run the complete suite:

```bash
python tools/validate-all/run_all.py --include-tests
```

## Compatibility

Backward-compatible changes may add optional flags, summary fields, metadata, validators, or new finding codes.

Adding a validator is normally backward-compatible but may expose repository defects that previously escaped automated checks. The release impact must still be classified.

Breaking changes include:

- changing the stable entry path
- changing exit-code meaning
- removing JSON fields
- changing validator ordering in a way that changes observable contract behavior
- silently removing a validator from the complete pipeline
- changing default test inclusion behavior
- silently narrowing accepted input
- converting warning-only maintenance state into aggregate failure without an explicit contract change

## Limitations

- does not replace tool-specific diagnostics
- captures only bounded subprocess output
- cannot prove checks omitted by underlying validators
- source freshness evaluates recorded review dates but does not fetch external sources
- validates release files but does not verify private GitHub repository settings
- does not create tags or prove release authority
- cannot establish semantic correctness from structural success

## Review checklist

Reviewers should confirm:

- documented behavior matches code
- the validator list is complete
- source freshness remains offline and truthful about NotRun live verification
- release validation remains in the permanent pipeline
- positive, warning, NotRun, negative, and error-path tests exist where applicable
- output and exit codes are stable
- filesystem and subprocess handling are safe
- dependency changes are pinned and justified
- compatibility and release impact are documented
- the complete pipeline passes

## Maintenance

Update the script, README, manifest, examples, tests, catalog, changelog, source metadata, release notes, and CI together when behavior changes.

## Completion boundary

A successful execution establishes only the outcome of the implemented child checks against the identified input. It does not grant authority, certify compliance, prove live external-source currency, publish a release, promote package maturity, or prove production readiness.
