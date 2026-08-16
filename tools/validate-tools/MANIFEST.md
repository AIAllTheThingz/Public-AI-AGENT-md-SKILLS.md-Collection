---
id: TOOL-PKG-VALIDATE-TOOLS-001-MANIFEST
title: Validate Tools Tool Manifest
version: 1.3.3
status: baseline
---

# Validate Tools Tool Manifest

## Required files

- `validate_tools.py`
- `README.md`
- `MANIFEST.md`
- `examples/README.md`

## Shared contracts

- `../TOOL_CONTRACT.md`
- `../contracts/tool-result.schema.json`
- `../tests/`
- `../validate-schemas/requirements.txt`
- `../validate-schemas/requirements.lock`
- `../check-freshness/`
- `../../SOURCE_REVIEWS.json`
- `../../.github/workflows/`
- referenced local composite-action `action.yml` / `action.yaml` metadata

## Runtime dependency

- `PyYAML==6.0.3`, installed through the repository hash-locked validation dependency set, is used to parse workflow and local composite-action YAML structurally.
- CLI help remains available before PyYAML is installed; validation without the dependency must report a structured error and exit through the common code-`2` dependency/input path.

## Acceptance checks

- primary entry point compiles
- declared package Python entry points compile
- `check-freshness` is part of the declared tool package set
- `check-freshness` includes its executable, README, manifest, examples, and central test coverage
- `--help` exits successfully even when PyYAML is unavailable
- missing PyYAML during validation produces structured error output and exit code `2`
- text output is readable
- JSON output conforms to the result contract
- exit codes match the common contract
- required tool package files are present
- central unit-test module count covers all declared tool packages, including freshness checking
- every resolved validation dependency carries at least one valid SHA-256 hash
- every direct validation dependency is represented exactly in the resolved lock
- ordinary inline requirement comments do not create false lock-drift findings
- GitHub Actions workflow YAML parses successfully
- third-party repository actions use full 40-character Git commit SHAs
- `docker://` actions use immutable `sha256:<64-hex>` OCI digests
- referenced local composite actions are traversed recursively and nested external `uses` references satisfy immutable-pin rules
- hosted runners do not use floating `*-latest` images
- static matrix runner validation applies partial-match `exclude` entries before evaluating effective runner values and inspects later `include` runner values
- scheduled source-freshness workflow is subject to the same action-pin and runner validation as permanent and release workflows
- quoted YAML scalars and legal key-spacing variants cannot bypass or falsely trigger workflow pin checks
- positive, warning, NotRun, negative, and error-path regression tests pass where applicable
- stable path remains unchanged
- README limitations, review checklist, maintenance guidance, and completion boundary remain present and synchronized
- documentation, catalog, examples, and behavior remain synchronized
