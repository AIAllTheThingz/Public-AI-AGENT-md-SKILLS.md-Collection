---
id: DISC-PROD-REQUIREMENTS-ENGINEERING-STANDARD
title: Requirements Engineering Standard
version: 0.1.0
status: baseline
---

# Requirements Engineering Standard

## Purpose

Produce requirements that are uniquely identifiable, testable, reviewable, traceable, evidence-backed, and implementation-neutral where appropriate.

## Required behavior

- Assign each requirement a stable unique identifier, such as `REQ-FUNC-001`, `REQ-NFR-001`, `REQ-SEC-001`, or `REQ-PERF-001`.
- Record statement, rationale, source, owner, priority, applicability, acceptance criteria, dependencies, status, and links.
- Separate functional behavior from applicable quality, security, privacy, accessibility, performance, reliability, operational, and compatibility requirements.
- Avoid prescribing implementation unless the constraint is itself reviewed and justified.
- Version changed requirements; preserve decision history and assess downstream impact.
- Record missing evidence as `NotRun` or `Blocked` and inapplicability as `NotApplicable` with justification.

## Required evidence

Reviewed requirements set, identifier uniqueness, source and acceptance mappings, change history, dependencies, and unresolved unknowns.

## Completion gate

Do not approve the requirements gate until material requirements have identifiers, measurable acceptance criteria, dependencies, applicability, owners, and visible unknowns.
