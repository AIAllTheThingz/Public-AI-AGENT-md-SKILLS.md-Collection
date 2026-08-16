---
id: TOOL-PKG-CHECK-FRESHNESS-001-MANIFEST
title: Check Freshness Tool Manifest
version: 1.0.0
status: baseline
---

# Check Freshness Tool Manifest

## Required files

- `check_freshness.py`
- `README.md`
- `MANIFEST.md`
- `examples/README.md`

## Shared contracts

- `../TOOL_CONTRACT.md`
- `../contracts/tool-result.schema.json`
- `../tests/test_check_freshness.py`
- `../../SOURCE_REVIEWS.json`
- `../../SOURCES.md`
- `../../MATURITY_POLICY.md`

## Required repository inputs

- `SOURCE_REVIEWS.json`
- repository scopes referenced by each registry record

## Operating boundary

- read-only by default
- no network access
- public source metadata only
- warning findings for stale or not-run review dates by default
- strict mode may convert stale or not-run review state into blocking errors
- live external-source verification is always reported as `NotRun` by this tool

## Acceptance checks

- entry point compiles
- shared CLI contract is preserved
- registry format version is validated
- record IDs are unique
- repository scopes are contained within the declared root
- authoritative sources use absolute HTTPS URLs
- future review dates are rejected
- fresh records report `Passed`
- stale records report `Warning`
- missing review dates report `NotRun`
- strict mode blocks stale and not-run records
- offline execution never claims live source verification
- scheduled/manual workflow uses immutable action pins and an explicit hosted runner
- positive, warning, not-run, invalid, and strict tests pass
- documentation matches executable behavior
- complete repository validation passes
