---
id: TOOL-PKG-VALIDATE-SCHEMAS-001-MANIFEST
title: Validate Schemas Tool Manifest
version: 1.2.0
status: baseline
---

# Validate Schemas Tool Manifest

## Required files

- `validate_schemas.py`
- `completion_semantics.py`
- `requirements.txt`
- `requirements.lock`
- `README.md`
- `MANIFEST.md`
- `examples/README.md`

## Shared contracts

- `../TOOL_CONTRACT.md`
- `../contracts/tool-result.schema.json`
- `../tests/`

## Acceptance checks

- entry point compiles
- `--help` exits successfully
- text output is readable
- JSON output conforms to the result contract
- exit codes match the common contract
- direct dependencies are represented in the SHA-256-hashed lock
- hosted workflows use the checked-in lock with hash enforcement
- positive and negative tests pass
- completion-result exact validation-action correlation, terminal-boundary, and RFC 3339 chronology tests pass
- stable path remains unchanged
- documentation and examples match behavior
