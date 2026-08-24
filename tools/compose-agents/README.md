---
id: TOOL-PKG-COMPOSE-AGENTS-001
title: Compose Agents Tool
version: 1.1.0
status: baseline
---

# Compose Agents Tool

## Purpose

Create a traceable standards bundle from a reviewed project manifest, including repository-defined governance selections and selected virtualization, operating-system, and networking standards, without concatenating or rewriting source standards.

Status: **baseline**

## Stable entry point

[`compose_agents.py`](compose_agents.py)

The stable path is part of the repository tooling contract. Moving or renaming it requires migration guidance and CI updates.

## Operating mode

- Reads: a project manifest and selected standards entry points
- Writes: an atomic bundle directory when not in dry-run mode
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
python tools/compose-agents/compose_agents.py --help
```

## Checks and behavior

- manifest schema validity
- selected package existence
- selected `AIAllTheThingz.governanceSelections` path existence and containment under `governance/`
- canonicalized governance selections in dependency lookup, source inventory, copied paths, and the generated index, with transitive closure including the Product Inception Lifecycle's Product Management traceability, SRE capacity, readiness, and scaling contracts, and referenced source-review evidence
- selected virtualization, operating-system, and networking package entry points
- required governance sources
- root-contained source paths
- source SHA-256 records
- overwrite protection

## Examples

```bash
python tools/compose-agents/compose_agents.py --manifest project-manifest.json --dry-run
```

```bash
python tools/compose-agents/compose_agents.py --manifest project-manifest.json --output-dir generated/standards-bundle
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
python -m unittest discover -s tools/tests -p "test_compose_agents*.py"
```

Run the complete suite:

```bash
python tools/validate-all/run_all.py --include-tests
```

## Compatibility

Backward-compatible changes may add optional flags, summary fields, metadata, or new finding codes.

Version 1.1 recognizes the optional `virtualization`, `operatingSystems`, and `networking` manifest arrays, includes each selected package's `AGENTS.md`, `README.md`, and `MANIFEST.md`, and reports those selections in the generated composition index. It also recognizes the repository-defined `AIAllTheThingz.governanceSelections` extension, validates and canonicalizes each repository-relative Markdown path under `governance/`, and includes every selected governance source plus the transitive dependency closure for recognized selections in the bundle and generated index. For the Product Inception Lifecycle, that closure includes the Product Management traceability contract, SRE capacity, production-readiness and scaling contracts, their evidence templates and package entry points, and referenced maturity and durable source-review records; copying those dependencies does not silently select a discipline package or establish a gate result. Version 1.0 manifests remain valid.

Breaking changes include:

- changing the stable entry path
- changing exit-code meaning
- removing JSON fields
- changing default write or overwrite behavior
- changing generated file semantics
- silently narrowing accepted input

## Limitations

- does not resolve policy conflicts automatically
- does not generate complete project facts
- does not authorize adoption or production use

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
