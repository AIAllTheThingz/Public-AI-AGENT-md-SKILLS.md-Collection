---
id: DISC-PROD
title: Product Management Agent Standard
version: 0.2.0
status: baseline
applies_to:
  - product-management
depends_on:
  - GOV-WORK
  - GOV-RISK
  - GOV-EVIDENCE
---

# Product Management Agent Standard

## Purpose

This file defines mandatory agent behavior for product definition, requirements, scope, prioritization, and product decisions.

> Make the smallest reviewable, testable, and evidence-backed product decision that satisfies the intended outcome.

## Scope

This discipline applies to product vision, problem definition, users or actors, outcomes, assumptions, constraints, requirements, MVP boundaries, prioritization, acceptance criteria, decisions, and traceability.

## Instruction priority

1. explicit user requirements
2. the nearest more-specific `AGENTS.md`
3. this discipline `AGENTS.md`
4. the supporting standards in this package
5. repository conventions
6. general agent preferences

Report material conflicts instead of resolving them silently.

## Required supporting standards

- [`PRODUCT_VISION_STANDARD.md`](standards/PRODUCT_VISION_STANDARD.md)
- [`PROBLEM_DEFINITION_STANDARD.md`](standards/PROBLEM_DEFINITION_STANDARD.md)
- [`USER_OUTCOME_STANDARD.md`](standards/USER_OUTCOME_STANDARD.md)
- [`REQUIREMENTS_ENGINEERING_STANDARD.md`](standards/REQUIREMENTS_ENGINEERING_STANDARD.md)
- [`MVP_SCOPE_STANDARD.md`](standards/MVP_SCOPE_STANDARD.md)
- [`PRIORITIZATION_STANDARD.md`](standards/PRIORITIZATION_STANDARD.md)
- [`ACCEPTANCE_CRITERIA_STANDARD.md`](standards/ACCEPTANCE_CRITERIA_STANDARD.md)
- [`TRACEABILITY_STANDARD.md`](standards/TRACEABILITY_STANDARD.md)
- [`PRODUCT_DECISION_STANDARD.md`](standards/PRODUCT_DECISION_STANDARD.md)

## Mandatory rules

### PROD-PROBLEM-001

**Requirement:** Separate evidence-backed facts, assumptions, constraints, and unknowns when defining the problem and intended users or actors.

**Evidence:** Reviewed product brief with sources, owners, and unresolved questions.

### PROD-REQ-002

**Requirement:** Give each material requirement a unique stable identifier and make it testable, reviewable, traceable, evidence-backed, and implementation-neutral where appropriate.

**Evidence:** Requirements record using identifiers such as `REQ-FUNC-001`, `REQ-NFR-001`, `REQ-SEC-001`, or `REQ-PERF-001`.

### PROD-SCOPE-003

**Requirement:** Define MVP inclusions, boundaries, and explicit exclusions without presenting deferred work as delivered.

**Evidence:** Approved scope record and prioritization rationale.

### PROD-ACCEPT-004

**Requirement:** Define measurable acceptance criteria before claiming a requirement is satisfied.

**Evidence:** Criteria mapped to requirements and validation evidence.

### PROD-TRACE-005

**Requirement:** Maintain traceability from idea through requirement, architecture decision, implementation, test, release or deployment, and production evidence; code existence alone does not establish completion.

**Evidence:** Traceability record with honest lifecycle states.

## Non-negotiable behavior

- Do not fabricate users, research, demand, approvals, outcomes, source evidence, test results, or operational results.
- Record missing evidence as `NotRun`, `Blocked`, or `NotApplicable` with rationale rather than inferring success.
- Keep product decisions distinct from architecture, security, accessibility, legal, and operational approval.
- Do not silently convert prototypes into architecture of record or production commitments.
- Preserve requirement identifiers and decision history when requirements change.
- Keep examples fictitious and disclose assumptions, exclusions, limitations, and residual risk.

## Required working method

1. Identify the problem, intended users or actors, desired outcome, facts, assumptions, constraints, and unknowns.
2. Define uniquely identified functional and applicable nonfunctional requirements.
3. Establish MVP boundaries, prioritization, acceptance criteria, dependencies, and exclusions.
4. Compose applicable UX, architecture, security, testing, reliability, and delivery disciplines.
5. Maintain traceability and record decisions as evidence evolves.
6. Report actual evidence state without overstating completion.

## Completion gate

Do not report product definition complete until applicable requirements and acceptance criteria are reviewed, traceability is current, evidence gaps are visible, and remaining assumptions, unknowns, exclusions, and risks have owners.

## References

- [ISO/IEC/IEEE 29148 Systems and software engineering — Life cycle processes — Requirements engineering](https://www.iso.org/standard/72089.html)
- [ISO/IEC/IEEE 15288 Systems and software engineering — System life cycle processes](https://www.iso.org/standard/81702.html)
- [ISO/IEC 25010 Systems and software Quality Requirements and Evaluation — Product quality model](https://www.iso.org/standard/78176.html)
