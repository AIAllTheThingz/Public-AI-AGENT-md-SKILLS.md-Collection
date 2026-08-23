---
id: PROFILE-RISK-001
title: Project Profile Risk and Evidence Matrix
version: 0.2.0
status: baseline
---
# Project Profile Risk and Evidence Matrix

## Purpose

Provides starting evidence expectations by profile. Actual governance risk classification controls.

Product Management and User Experience evidence in this matrix is conditional. It becomes relevant only when that discipline is selected for the scoped project or change; the profile alone does not make either package mandatory.

| Profile | Typical start | High-value evidence |
|---|---:|---|
| Web API | `moderate` | authentication and authorization model, request and response contract, versioning and compatibility policy |
| Web Application | `moderate` | when applicable, product requirements and traceability plus user journeys and honest research state; server-side authorization model, client and server trust boundaries, separate WCAG 2.2 AA or stricter accessibility evidence |
| Worker Service | `moderate` | idempotency and replay behavior, concurrency and ordering, cancellation and graceful shutdown |
| Command-Line Tool | `low` | safe defaults and read-only behavior, confirmation and simulation for destructive actions, human-readable and machine-readable output |
| Desktop Application | `moderate` | when applicable, product requirements and traceability plus user journeys and honest research state; local data protection, installer and update integrity, privilege and elevation boundaries |
| Mobile Application | `moderate` | when applicable, product requirements and traceability plus user journeys and honest research state; secure storage, network trust and certificate behavior, permission minimization |
| Serverless Function | `moderate` | event validation and schema, idempotency and duplicate delivery, timeout, retry, and dead-letter behavior |
| Data Pipeline | `high` | data contracts and ownership, lineage and metadata, replay and backfill behavior |
| Public Library | `moderate` | when Product Management applies, consumer outcomes, requirements, and traceability; public API compatibility, supported runtimes and platforms, dependency minimization |
| Internal Automation | `high` | discovery and validation phases, dry-run, what-if, or preview behavior, least privilege and credential handling |
| Multi-Tenant SaaS | `high` | product requirements and traceability when Product Management applies, tenant identity and isolation model, authorization at every object boundary, data partitioning and lifecycle, UX evidence when a tenant or operator interface applies |
| Security Tool | `high` | authorized scope and target identity, safe handling of findings and evidence, false-positive and false-negative limitations |
| AI Agent Application | `high` | product requirements and traceability when Product Management applies, tool authorization and allowlists, prompt and retrieved-content trust boundaries, human approval for consequential actions, UX evidence when people interact with the agent |

## Escalation factors

Escalate risk for:

- production targets
- privileged or destructive actions
- public exposure
- sensitive or regulated data
- tenant boundaries
- irreversible migration
- broad blast radius
- weak rollback
- safety impact
- consequential AI tool use
- unsupported runtime or dependency
- missing operational owner
- incomplete evidence

## Minimum evidence across profiles

- profile selection rationale
- architecture and trust boundaries
- risk classification
- required project decisions
- package selection
- validation commands and results
- checks not run
- limitations and residual risk
- review and approval evidence

## Decision rule

When the project shape or risk is uncertain, choose the higher plausible control set until evidence supports reduction.
