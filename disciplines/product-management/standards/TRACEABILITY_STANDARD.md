---
id: DISC-PROD-TRACEABILITY-STANDARD
title: Requirement Traceability Standard
version: 0.1.0
status: baseline
---

# Requirement Traceability Standard

## Purpose

Preserve an auditable evidence chain across the product and engineering lifecycle.

## Required behavior

- Trace each material requirement through `Idea -> Requirement -> Architecture Decision -> Implementation -> Test -> Release/Deployment -> Production Evidence` as applicable.
- Preserve stable identifiers and links to source records, decisions, changes, tests, artifacts, deployments, and operational evidence.
- Use only `Planned`, `Implemented`, `Tested`, `Reviewed`, `OperationallyVerified`, `NotRun`, `Blocked`, or `NotApplicable` for the traceability evidence state; justify `NotApplicable`.
- Treat states as independent claims: implementation does not prove testing, review, deployment, or operational verification.
- Identify gaps, stale evidence, changed artifacts, unsupported environments, owners, and follow-up.
- Reassess downstream links when a requirement, decision, implementation, artifact, environment, or production assumption changes.

## Required evidence

Traceability matrix or equivalent records tied to immutable commits, artifacts, tests, deployment records, and appropriately scoped production evidence where those stages apply.

## Completion gate

Code existence alone never establishes requirement completion. A completion claim is prohibited until the applicable chain is supported, reviewed, and any gaps or inapplicable stages are explicit.
