---
id: TOOL-PKG-GENERATE-MANIFEST-001
title: Generate Manifest Tool
version: 1.1.0
status: baseline
---

# Generate Manifest Tool

## Purpose

Generate a deterministic, schema-valid project manifest from explicit profile, language, discipline, framework, platform, virtualization, operating-system, and networking selections.

Status: **baseline**

## Stable entry point

[`generate_manifest.py`](generate_manifest.py)

The stable path is part of the repository tooling contract. Moving or renaming it requires migration guidance and CI updates.

## Operating mode

- Reads: profiles, package directories, optional input config, and the project-manifest schema
- Writes: one manifest file when not in dry-run mode
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
python tools/generate-manifest/generate_manifest.py --help
```

## Checks and behavior

- known profile
- known package slugs
- explicit virtualization, operating-system, and networking package selection
- at least one language
- optional profile-discipline expansion across the primary and selected secondary profiles
- schema validation
- overwrite protection

## Examples

```bash
python tools/generate-manifest/generate_manifest.py --name example --profile INTERNAL_AUTOMATION --language python --virtualization kvm-libvirt --operating-system ubuntu --networking cisco-networking --include-profile-required --dry-run
```

```bash
python tools/generate-manifest/generate_manifest.py --config manifest-input.json --manifest-output project-manifest.json
```

JSON configuration uses the manifest-style array keys `languages`, `disciplines`, `frameworks`, `platforms`, `virtualization`, `operatingSystems`, and `networking`. CLI selections are appended and then de-duplicated in first-seen order. When `--include-profile-required` is supplied, profile-linked disciplines are expanded from the primary profile and every selected secondary profile. This post-`0.10.0` correction deliberately preserves the published primary-profile expansion semantics and only adds the previously omitted secondary-profile expansion.

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
python -m unittest discover -s tools/tests -p "test_generate_manifest*.py"
```

Run the complete suite:

```bash
python tools/validate-all/run_all.py --include-tests
```

## Compatibility

Backward-compatible changes may add optional flags, summary fields, metadata, or new finding codes.

Version 1.1 adds repeatable `--virtualization`, `--operating-system`, and `--networking` flags and matching `virtualization`, `operatingSystems`, and `networking` configuration keys. Manifests without those selections retain schema version `1.0.0`; manifests using them emit `1.1.0`.

Breaking changes include:

- changing the stable entry path
- changing exit-code meaning
- removing JSON fields
- changing default write or overwrite behavior
- changing generated file semantics
- silently narrowing accepted input

## Limitations

- does not choose packages automatically
- does not classify risk
- does not approve omissions or exceptions

## Review checklist

Reviewers should confirm:

- documented behavior matches code
- positive and negative tests exist
- output and exit codes are stable
- filesystem and subprocess handling are safe
- dependency changes are pinned and justified
- compatibility impact is documented
- the complete pipeline passes

## Maintenance

Update the script, README, manifest, examples, tests, catalog, and CI together when behavior changes.

## Completion boundary

A successful execution establishes only the outcome of this tool's implemented checks or generation plan against the identified input. It does not grant authority, certify compliance, or prove production readiness.
