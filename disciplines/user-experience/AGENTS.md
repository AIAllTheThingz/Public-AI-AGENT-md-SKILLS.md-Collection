---
id: DISC-UX
title: User Experience Agent Standard
version: 0.2.0
status: baseline
applies_to:
  - user-experience
depends_on:
  - GOV-WORK
  - GOV-RISK
  - GOV-EVIDENCE
---

# User Experience Agent Standard

## Purpose

This file defines mandatory agent behavior for evidence-backed user journeys, task flows, information architecture, interactions, prototypes, usability, consistency, and UX validation.

## Scope and boundary

This discipline governs `User -> Goal -> Journey -> Task -> Workflow / Interface -> Interaction -> Result`.

It complements but does not replace the [Accessibility](../accessibility/) discipline. UX evaluates whether intended users can understand and accomplish goals effectively in context; Accessibility supplies disability-inclusive conformance, semantic, keyboard, focus, content, visual, motion, media, and assistive-technology controls. Both apply to user-facing work where relevant.

## Instruction priority

1. explicit user requirements
2. the nearest more-specific `AGENTS.md`
3. this discipline `AGENTS.md`
4. the supporting standards in this package
5. repository conventions
6. general agent preferences

Report material conflicts instead of resolving them silently.

## Required supporting standards

- [`USER_RESEARCH_STANDARD.md`](standards/USER_RESEARCH_STANDARD.md)
- [`USER_JOURNEY_STANDARD.md`](standards/USER_JOURNEY_STANDARD.md)
- [`INFORMATION_ARCHITECTURE_STANDARD.md`](standards/INFORMATION_ARCHITECTURE_STANDARD.md)
- [`INTERACTION_DESIGN_STANDARD.md`](standards/INTERACTION_DESIGN_STANDARD.md)
- [`PROTOTYPING_STANDARD.md`](standards/PROTOTYPING_STANDARD.md)
- [`USABILITY_STANDARD.md`](standards/USABILITY_STANDARD.md)
- [`DESIGN_CONSISTENCY_STANDARD.md`](standards/DESIGN_CONSISTENCY_STANDARD.md)
- [`UX_VALIDATION_STANDARD.md`](standards/UX_VALIDATION_STANDARD.md)

## Mandatory rules

### UX-RESEARCH-001

**Requirement:** Never fabricate research, participants, observations, quotations, usability results, or user evidence; record absent research as `NotRun` or another accurate state.

**Evidence:** Research plan and consented research record, or explicit `NotRun`, `Blocked`, or `NotApplicable` rationale.

### UX-JOURNEY-002

**Requirement:** Trace each material experience from user and goal through journey, task, workflow or interface, interaction, and result, including failure and recovery paths.

**Evidence:** Reviewed journey and flow records linked to product requirements.

### UX-DESIGN-003

**Requirement:** Make navigation, information structure, interaction states, feedback, errors, and recovery explicit and consistent.

**Evidence:** Design specification, prototype, or implementation review.

### UX-ACCESS-004

**Requirement:** Apply the Accessibility discipline independently; a usability result is not accessibility conformance evidence, and automated accessibility results are not UX validation.

**Evidence:** Separate UX and accessibility applicability and validation records.

### UX-VALIDATE-005

**Requirement:** Match UX claims to representative evidence and distinguish assumptions, prototypes, implementation, testing, review, and operational use.

**Evidence:** Validation record with participants or methods, conditions, limitations, findings, and state.

## Non-negotiable behavior

- Protect participant privacy, consent, safety, and sensitive research data.
- Label synthetic personas, simulated feedback, heuristic reviews, and agent-generated journeys as assumptions or design artifacts, never observed user evidence.
- Do not allow prototype shortcuts to become production design or architecture without review.
- Include error, empty, loading, interruption, permission, timeout, and recovery states where applicable.
- Record conflicting findings, limitations, excluded users, and checks not run.
- Preserve public behavior unless change is authorized and compatibility, migration, and communication impacts are addressed.
- Keep examples fictitious and credentials, production identifiers, and sensitive data out of source, tests, evidence, and documentation.

## Required working method

1. Confirm intended users, goals, context, requirements, and accessibility applicability.
2. Select proportionate research and validation methods; record accurate evidence state.
3. Map journeys and tasks, then define information and interaction structure.
4. Prototype risky assumptions and preserve prototype boundaries.
5. Validate with representative methods and feed findings into requirements and decisions.
6. Report limitations, accessibility evidence separately, and unresolved risks.

## Completion gate

Do not report UX complete until applicable journeys and states are defined, evidence is attributable, accessibility boundaries are preserved, research status is honest, and material findings have decisions or owners.

## References

- [ISO 9241-210 Human-centred design for interactive systems](https://www.iso.org/standard/77520.html)
- [W3C Web Content Accessibility Guidelines 2.2](https://www.w3.org/TR/WCAG22/)
- [WAI-ARIA Authoring Practices Guide](https://www.w3.org/WAI/ARIA/apg/)
