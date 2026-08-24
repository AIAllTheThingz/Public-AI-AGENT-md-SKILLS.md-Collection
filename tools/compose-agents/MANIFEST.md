---
id: TOOL-PKG-COMPOSE-AGENTS-001-MANIFEST
title: Compose Agents Tool Manifest
version: 1.1.0
status: baseline
---

# Compose Agents Tool Manifest

## Required files

- `compose_agents.py`
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
- positive and negative tests pass
- stable path remains unchanged
- documentation and examples match behavior
- repository-defined governance selections are validated, included, and reported
- recognized governance selections are canonicalized and include their transitive required linked contracts without implying additional package selection
- virtualization, operating-system, and networking package entry points are included when selected
- version 1.0 manifests remain supported
