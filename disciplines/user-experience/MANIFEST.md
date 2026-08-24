---
id: DISC-MAN-UX
title: User Experience Package Manifest
version: 0.1.0
status: baseline
---

# User Experience Package Manifest

## Required files

- `AGENTS.md`
- `README.md`
- `MANIFEST.md`
- `standards/USER_RESEARCH_STANDARD.md`
- `standards/USER_JOURNEY_STANDARD.md`
- `standards/INFORMATION_ARCHITECTURE_STANDARD.md`
- `standards/INTERACTION_DESIGN_STANDARD.md`
- `standards/PROTOTYPING_STANDARD.md`
- `standards/USABILITY_STANDARD.md`
- `standards/DESIGN_CONSISTENCY_STANDARD.md`
- `standards/UX_VALIDATION_STANDARD.md`
- `templates/ADOPTION_CHECKLIST.md`
- `templates/REVIEW_CHECKLIST.md`
- `templates/EVIDENCE_RECORD_TEMPLATE.md`
- `templates/USER_JOURNEY_TEMPLATE.md`
- `templates/USABILITY_REVIEW_TEMPLATE.md`
- `examples/ADOPTION_EXAMPLE.md`

## Package acceptance checks

- Research evidence is attributable or carries an accurate incomplete state.
- UX-validation state and outcome are independent, and a validated claim requires an overall `Pass` supported by every applicable method and claim.
- Synthetic assumptions cannot masquerade as observed users or research.
- Journeys cover goal, task, workflow, interaction, result, failure, and recovery as applicable.
- UX does not duplicate or weaken Accessibility.
- Prototypes cannot silently become architecture of record.
- Templates contain placeholders, examples are fictitious, and links resolve.

## Repository validation

Run `python tools/validate-standards/validate_repository.py` and `python tools/check-links/check_links.py` from the repository root.
