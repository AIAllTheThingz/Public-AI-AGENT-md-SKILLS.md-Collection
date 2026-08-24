---
id: DISC-MAN-PROD
title: Product Management Package Manifest
version: 0.1.0
status: baseline
---

# Product Management Package Manifest

## Required files

- `AGENTS.md`
- `README.md`
- `MANIFEST.md`
- `standards/PRODUCT_VISION_STANDARD.md`
- `standards/PROBLEM_DEFINITION_STANDARD.md`
- `standards/USER_OUTCOME_STANDARD.md`
- `standards/REQUIREMENTS_ENGINEERING_STANDARD.md`
- `standards/MVP_SCOPE_STANDARD.md`
- `standards/PRIORITIZATION_STANDARD.md`
- `standards/ACCEPTANCE_CRITERIA_STANDARD.md`
- `standards/TRACEABILITY_STANDARD.md`
- `standards/PRODUCT_DECISION_STANDARD.md`
- `templates/ADOPTION_CHECKLIST.md`
- `templates/REVIEW_CHECKLIST.md`
- `templates/EVIDENCE_RECORD_TEMPLATE.md`
- `templates/PRODUCT_BRIEF_TEMPLATE.md`
- `templates/REQUIREMENTS_TEMPLATE.md`
- `examples/ADOPTION_EXAMPLE.md`

## Package acceptance checks

- Stable requirement and rule identifiers are unique.
- Facts, assumptions, constraints, and unknowns are distinguishable.
- Requirements are testable, reviewable, traceable, and evidence-backed.
- Acceptance decisions are separate from evidence states, and `Tested` is not treated as `Pass`.
- MVP boundaries and exclusions are explicit.
- Traceability does not infer completion from code existence.
- Templates use placeholders and examples are fictitious.
- Relative links resolve and completion language matches evidence.

## Repository validation

Run `python tools/validate-standards/validate_repository.py` and `python tools/check-links/check_links.py` from the repository root.
