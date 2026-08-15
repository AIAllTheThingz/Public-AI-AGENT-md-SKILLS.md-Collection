---
id: TOOL-PKG-VALIDATE-TOOLS-001-MANIFEST
title: Validate Tools Tool Manifest
version: 1.3.2
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
- `../../.github/workflows/`

## Runtime dependency

- `PyYAML==6.0.3`, installed through the repository hash-locked validation dependency set, is used to parse workflow YAML structurally.

## Acceptance checks

- primary entry point compiles
- declared package Python entry points compile
- `--help` exits successfully
- text output is readable
- JSON output conforms to the result contract
- exit codes match the common contract
- required tool package files are present
- central unit-test module count covers declared tool packages
- every direct validation dependency is represented exactly in the SHA-256-hashed resolved lock
- ordinary inline requirement comments do not create false lock-drift findings
- GitHub Actions workflow YAML parses successfully
- third-party repository actions use full 40-character Git commit SHAs
- `docker://` actions use immutable `sha256:<64-hex>` OCI digests
- hosted runners do not use floating `*-latest` images
- quoted YAML scalars and legal key-spacing variants cannot bypass or falsely trigger workflow pin checks
- positive and negative regression tests pass
- stable path remains unchanged
- documentation, catalog, examples, and behavior remain synchronized
