---
id: TOOL-TEST-001
title: Tool Testing Guide
version: 1.0.0
status: baseline
---

# Tool Testing Guide

## Unit tests

Run:

```bash
python -m unittest discover -s tools/tests -p "test_*.py"
```

Tests use temporary repositories and subprocess execution to verify public behavior.

Every published finding code in `tools/tests/test_published_finding_codes.py` must keep a test that runs the real tool and asserts the code (see `tools/tests/test_finding_codes_*.py`).

Compatibility tests read the published `v0.10.0` commits, so they need a full clone. In a shallow clone or an extracted source archive they are skipped with a reason; CI sets `PAG_REQUIRE_GIT_HISTORY=1` so missing history fails instead of skipping.

## Required test classes

Each tool should cover:

- successful execution
- validation failure
- malformed input
- missing files or dependencies where practical
- text output
- JSON output
- exit codes
- path handling
- deterministic output

Writing tools additionally require:

- dry-run
- overwrite refusal
- `--force`
- partial-output prevention
- schema validation of generated records

## Integration validation

Run:

```bash
python tools/validate-all/run_all.py --include-tests
```

## Test data safety

Fixtures must be fictitious and must not contain production endpoints, credentials, private keys, personal data, or confidential evidence.

## Failure evidence

A failing test must preserve enough stdout and stderr to diagnose the public contract failure without dumping sensitive repository content.
