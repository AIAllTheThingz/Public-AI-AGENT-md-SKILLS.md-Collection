---
id: DISC-PKG-PROD
title: Product Management Discipline Package
version: 0.1.0
status: baseline
---

# Product Management Discipline Package

## Purpose

This package governs the evidence-backed path from an idea to reviewable product requirements, scope, acceptance criteria, decisions, and end-to-end traceability. It is a baseline, not proof that a product is desirable, compliant, approved, or ready for production.

## What this package controls

- vision, problem, intended users or actors, and desired outcomes
- facts, assumptions, constraints, dependencies, and unknowns
- functional and nonfunctional requirements
- MVP scope, exclusions, and prioritization
- acceptance criteria, decisions, and traceability

## When to adopt this package

Adopt it for new products, material capabilities, significant outcome or scope changes, and work whose implementation needs requirements or acceptance decisions. Tailoring may mark a control inapplicable only with justification.

## Package structure

```text
disciplines/product-management/
├── AGENTS.md
├── README.md
├── MANIFEST.md
├── standards/
│   ├── PRODUCT_VISION_STANDARD.md
│   ├── PROBLEM_DEFINITION_STANDARD.md
│   ├── USER_OUTCOME_STANDARD.md
│   ├── REQUIREMENTS_ENGINEERING_STANDARD.md
│   ├── MVP_SCOPE_STANDARD.md
│   ├── PRIORITIZATION_STANDARD.md
│   ├── ACCEPTANCE_CRITERIA_STANDARD.md
│   ├── TRACEABILITY_STANDARD.md
│   └── PRODUCT_DECISION_STANDARD.md
├── templates/
│   ├── ADOPTION_CHECKLIST.md
│   ├── REVIEW_CHECKLIST.md
│   ├── EVIDENCE_RECORD_TEMPLATE.md
│   ├── PRODUCT_BRIEF_TEMPLATE.md
│   └── REQUIREMENTS_TEMPLATE.md
└── examples/
    └── ADOPTION_EXAMPLE.md
```

## Supporting standards

| Standard | Purpose |
|---|---|
| [Product Vision](standards/PRODUCT_VISION_STANDARD.md) | Define direction, intended value, boundaries, and success signals. |
| [Problem Definition](standards/PROBLEM_DEFINITION_STANDARD.md) | Distinguish the problem and evidence from assumptions and proposed solutions. |
| [User Outcome](standards/USER_OUTCOME_STANDARD.md) | Link users or actors, goals, outcomes, and measurable signals. |
| [Requirements Engineering](standards/REQUIREMENTS_ENGINEERING_STANDARD.md) | Create identifiable, testable, reviewable, traceable requirements. |
| [MVP Scope](standards/MVP_SCOPE_STANDARD.md) | Define the minimum coherent outcome and explicit exclusions. |
| [Prioritization](standards/PRIORITIZATION_STANDARD.md) | Make priority criteria and trade-offs visible. |
| [Acceptance Criteria](standards/ACCEPTANCE_CRITERIA_STANDARD.md) | Define measurable evidence needed for acceptance. |
| [Traceability](standards/TRACEABILITY_STANDARD.md) | Preserve the evidence chain from idea to production evidence. |
| [Product Decision](standards/PRODUCT_DECISION_STANDARD.md) | Record material decisions, alternatives, owners, and review triggers. |

## Adoption and tailoring

1. Read root governance and decide whether to explicitly select the optional [`PRODUCT_INCEPTION_LIFECYCLE.md`](../../governance/PRODUCT_INCEPTION_LIFECYCLE.md); adopting Product Management alone does not activate it.
2. Select the applicable project profile and companion disciplines.
3. Assign owners for requirements, decisions, evidence, review, and unknowns.
4. Tailor identifiers, evidence locations, gates, and decision authority without weakening traceability.
5. Complete the adoption and review checklists and validate links.

Typical companions are [User Experience](../user-experience/), [Architecture](../architecture/), [Testing](../testing/), [Application Security](../application-security/), [Accessibility](../accessibility/), and [SRE](../sre/).

## Evidence model

Traceability records must distinguish `Planned`, `Implemented`, `Tested`, `Reviewed`, `OperationallyVerified`, `NotRun`, `Blocked`, and `NotApplicable`. A state describes available evidence; it is not approval and must not be inferred from another state. Acceptance is a separate per-criterion decision: `Tested` or `Reviewed` does not imply `Pass`, and a requirement is accepted only when every applicable criterion has a current explicit `Pass` for the exact reviewed artifact and conditions.

Product Management research provenance uses `Performed`, `NotRun`, `Blocked`, or justified `NotApplicable`. `Performed` requires completed actual research with attributable evidence. These standalone states do not silently select User Experience; apply the UX package independently when its documented predicate is satisfied.

## Authoritative starting points

- [ISO/IEC/IEEE 29148](https://www.iso.org/standard/72089.html)
- [ISO/IEC/IEEE 15288](https://www.iso.org/standard/81702.html)
- [ISO/IEC 25010](https://www.iso.org/standard/78176.html)

These are starting points only. This package summarizes selected engineering concepts, does not reproduce standards text, and does not claim certification or compliance.

Accountable review dates and sources are recorded in [`SOURCE_REVIEWS.json`](../../SOURCE_REVIEWS.json), with durable findings under [`source-reviews/`](../../source-reviews/).

## Validation and completion

Run the repository standards validator and link checker. Adoption is incomplete until requirements and decisions have owners, evidence states are honest, unresolved unknowns are visible, and completion claims do not exceed traceability evidence.
