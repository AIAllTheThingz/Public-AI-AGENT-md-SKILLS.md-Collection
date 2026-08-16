---
id: TOOL-MANIFEST-001
title: Toolchain Manifest
version: 1.3.0
status: baseline
---

# Toolchain Manifest

## Required collection files

- `AGENTS.md`
- `README.md`
- `MANIFEST.md`
- `TOOL_CATALOG.md`
- `TOOL_CONTRACT.md`
- `DEVELOPMENT_GUIDE.md`
- `TESTING_GUIDE.md`
- `SECURITY_BOUNDARIES.md`
- `RELEASE_AND_COMPATIBILITY.md`
- `TROUBLESHOOTING.md`

## Required executable packages

- `validate-standards`
- `check-links`
- `check-freshness`
- `validate-skills`
- `validate-schemas`
- `validate-templates`
- `validate-tools`
- `generate-manifest`
- `compose-agents`
- `validate-all`
- `release`

Each package requires:

- stable Python entry point
- useful README
- package manifest
- examples README
- central unit-test coverage
- text and JSON output where applicable
- documented exit codes
- documented limitations

The `check-freshness` package additionally requires `SOURCE_REVIEWS.json`, explicit offline behavior, `Passed`/`Warning`/`NotRun` maintenance-state reporting, and truthful `NotRun` reporting for live source verification.

The release package additionally contains a deterministic artifact builder and tag-driven publication workflow.

## Shared support

- `lib/standards_tools/`
- `contracts/tool-result.schema.json`
- `tests/`

## Acceptance checks

- every Python entry point compiles
- every validator entry point supports `--help`
- all package READMEs meet minimum depth
- no tool remains documentation-only or marked planned
- unit tests pass
- repository, link, freshness, skill, schema, template, tool, and release validators pass
- source-review metadata is structurally valid and never treats missing review dates as live verification success
- generation tools support dry-run or overwrite protection as appropriate
- release tooling validates tags and builds deterministic archives
- release checksums and manifests are produced
- JSON reports conform to the tool-result contract
- no bootstrap or temporary diagnostic artifact remains
