---
id: TOOL-PKG-COMPOSE-AGENTS-001-EXAMPLE
title: Compose Agents Tool Examples
version: 1.1.0
status: baseline
---

# Compose Agents Tool Examples

## Commands

```bash
python tools/compose-agents/compose_agents.py --manifest project-manifest.json --dry-run
```

```bash
python tools/compose-agents/compose_agents.py --manifest project-manifest.json --output-dir generated/standards-bundle
```

## Expected behavior

Examples use fictitious or repository-local inputs. Schema 1.1 manifests may select virtualization, operating-system, and networking packages. The repository-defined `AIAllTheThingz.governanceSelections` extension may select repository-relative Markdown sources under `governance/`. The composed bundle records and copies those selected governance sources and package entry points. Review the command before execution and use dry-run for writing tools.

## Boundary

The examples demonstrate command shape and result handling. They do not authorize changes, select production targets, or provide genuine evidence.
