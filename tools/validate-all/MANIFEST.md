---
id: TOOL-PKG-VALIDATE-ALL-001-MANIFEST
title: Validate All Tool Manifest
version: 1.3.0
status: baseline
---

# Validate All Tool Manifest

## Required files

- `run_all.py`
- `README.md`
- `MANIFEST.md`
- `examples/README.md`

## Shared contracts

- `../TOOL_CONTRACT.md`
- `../contracts/tool-result.schema.json`
- `../tests/`
- `../../RELEASE_POLICY.md`
- `../../SOURCE_REVIEWS.json`

## Required validators

- `validate-standards`
- `check-links`
- `check-freshness`
- `validate-skills`
- `validate-schemas`
- `validate-templates`
- `validate-tools`
- `validate-release`

## Acceptance checks

- entry point compiles
- `--help` exits successfully
- `--list` includes every required validator
- text output is readable
- JSON output conforms to the result contract
- child results and exit codes are preserved
- warning-only source freshness state remains visible without becoming an aggregate failure
- live source verification remains explicitly `NotRun` for the offline freshness checker
- release validation remains in the complete pipeline
- exit codes match the common contract
- positive, warning, NotRun, negative, and error-path tests pass
- stable path remains unchanged
- documentation and examples match behavior
- permanent CI invokes this runner with unit tests
