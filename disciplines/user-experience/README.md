---
id: DISC-PKG-UX
title: User Experience Discipline Package
version: 0.1.0
status: baseline
---

# User Experience Discipline Package

## Purpose

This package governs evidence-backed journeys, tasks, information structures, interaction behavior, prototypes, usability, design consistency, and validation. It does not claim that research occurred or that a design is universally usable.

## Experience model

```text
User -> Goal -> Journey -> Task -> Workflow / Interface -> Interaction -> Result
```

Adopt this package when users or operators must understand information, make decisions, or complete tasks through a workflow or interface.

## Accessibility boundary

UX and [Accessibility](../accessibility/) overlap at inclusive interaction but remain separate responsibilities. This package governs goal fit, comprehension, flow, feedback, efficiency, and usability evidence. Accessibility governs WCAG, semantics and ARIA, keyboard and focus, content and errors, visual and motion needs, media, assistive technology, testing, and remediation. Adopters must not use one discipline's evidence to claim the other completed.

## Package structure

```text
disciplines/user-experience/
├── AGENTS.md
├── README.md
├── MANIFEST.md
├── standards/
│   ├── USER_RESEARCH_STANDARD.md
│   ├── USER_JOURNEY_STANDARD.md
│   ├── INFORMATION_ARCHITECTURE_STANDARD.md
│   ├── INTERACTION_DESIGN_STANDARD.md
│   ├── PROTOTYPING_STANDARD.md
│   ├── USABILITY_STANDARD.md
│   ├── DESIGN_CONSISTENCY_STANDARD.md
│   └── UX_VALIDATION_STANDARD.md
├── templates/
│   ├── ADOPTION_CHECKLIST.md
│   ├── REVIEW_CHECKLIST.md
│   ├── EVIDENCE_RECORD_TEMPLATE.md
│   ├── USER_JOURNEY_TEMPLATE.md
│   └── USABILITY_REVIEW_TEMPLATE.md
└── examples/
    └── ADOPTION_EXAMPLE.md
```

## Supporting standards

| Standard | Purpose |
|---|---|
| [User Research](standards/USER_RESEARCH_STANDARD.md) | Govern research ethics, provenance, representativeness, and honest `NotRun` states. |
| [User Journey](standards/USER_JOURNEY_STANDARD.md) | Map goals, tasks, touchpoints, states, outcomes, and recovery. |
| [Information Architecture](standards/INFORMATION_ARCHITECTURE_STANDARD.md) | Organize, label, navigate, search, and disclose information coherently. |
| [Interaction Design](standards/INTERACTION_DESIGN_STANDARD.md) | Define actions, feedback, states, constraints, errors, and recovery. |
| [Prototyping](standards/PROTOTYPING_STANDARD.md) | Test assumptions without making the prototype architecture of record. |
| [Usability](standards/USABILITY_STANDARD.md) | Define contextual effectiveness, efficiency, comprehension, and satisfaction evidence. |
| [Design Consistency](standards/DESIGN_CONSISTENCY_STANDARD.md) | Reuse reviewed patterns while allowing justified contextual differences. |
| [UX Validation](standards/UX_VALIDATION_STANDARD.md) | Match claims to representative methods, evidence, and limitations. |

## Adoption and evidence

Compose this package with [Product Management](../product-management/), [Accessibility](../accessibility/), [Architecture](../architecture/), [Testing](../testing/), [Documentation](../documentation/), and security/privacy disciplines as applicable.

Actual research evidence must identify method, participants or source population without exposing sensitive identities, context, findings, limitations, date, and owner. If actual research did not occur, the state is `NotRun` unless `Blocked` or justified `NotApplicable` is more accurate. Synthetic assumptions never become observed evidence through confident wording.

## Authoritative starting points

- [ISO 9241-210](https://www.iso.org/standard/77520.html)
- [ISO 9241-11 Usability: Definitions and concepts](https://www.iso.org/standard/63500.html)
- [W3C WCAG 2.2](https://www.w3.org/TR/WCAG22/)
- [WAI-ARIA Authoring Practices Guide](https://www.w3.org/WAI/ARIA/apg/)

These links are starting points, not certification or compliance claims, and this package does not reproduce copyrighted standards text.

## Completion

Run repository validation and link checking. Adoption is incomplete until evidence states are honest, accessibility responsibilities remain intact, and findings, limitations, excluded populations, and unresolved risks are visible.
