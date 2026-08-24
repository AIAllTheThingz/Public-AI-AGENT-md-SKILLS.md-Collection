---
id: DISC-MAN-TEST
title: Testing and Quality Engineering Package Manifest
version: 0.1.0
status: baseline
---
# Testing and Quality Engineering Package Manifest

## Required files

- `AGENTS.md`
- `README.md`
- `MANIFEST.md`
- `standards/TEST_STRATEGY_STANDARD.md`
- `standards/UNIT_COMPONENT_STANDARD.md`
- `standards/INTEGRATION_CONTRACT_STANDARD.md`
- `standards/END_TO_END_STANDARD.md`
- `standards/NONFUNCTIONAL_TESTING_STANDARD.md`
- `standards/TEST_DATA_ENVIRONMENT_STANDARD.md`
- `standards/DEFECT_REGRESSION_STANDARD.md`
- `standards/COMPLETION_EVIDENCE.md`
- `templates/ADOPTION_CHECKLIST.md`
- `templates/REVIEW_CHECKLIST.md`
- `templates/EVIDENCE_RECORD_TEMPLATE.md`
- `examples/ADOPTION_EXAMPLE.md`

## Package acceptance checks

- `AGENTS.md` preserves stable discipline rule identifiers and references the supporting standards.
- `README.md` explains scope, adoption, tailoring, evidence, validation, companion disciplines, and limitations.
- Every supporting standard has unique front matter and a completion gate.
- Performance-test execution states and outcomes are recorded separately, and a validated claim requires every applicable outcome to be `Pass`.
- Templates contain placeholders rather than environment-specific production values.
- The example uses fictitious context and demonstrates composition rather than claiming universal applicability.
- Relative Markdown links resolve.
- No credentials, tokens, private keys, internal hostnames, production endpoints, or sensitive identifiers are present.
- The package status and version are consistent across maintained entry points.
- Changes include validation evidence and disclose checks not run.

## Repository validation

Run from the repository root:

```bash
python tools/validate-standards/validate_repository.py
python tools/check-links/check_links.py
```

## Adoption validation

The adopting repository must also verify:

- applicable requirements were selected and omissions were documented
- project owners and reviewers are named
- language, framework, platform, virtualization, operating-system, networking, profile, and companion-discipline packages are composed correctly
- project validation and evidence requirements are executable
- exceptions are reviewed, time-bounded, and traceable
- remaining risks and unsupported claims are visible
