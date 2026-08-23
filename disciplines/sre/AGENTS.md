---
id: DISC-SRE
title: Site Reliability Engineering Agent Standard
version: 0.2.0
status: baseline
applies_to:
  - sre
depends_on:
  - GOV-WORK
  - GOV-RISK
  - GOV-EVIDENCE
---

# Site Reliability Engineering Agent Standard

## Purpose

This file defines mandatory agent behavior for work governed by the **Site Reliability Engineering** discipline.

Its objective is to connect reliability objectives to architecture, delivery, operations, incident learning, and capacity decisions.

> Make the smallest safe, reviewable, testable, and evidence-backed change that satisfies the requirement.

## Scope

This discipline applies to:

- service objectives and error budgets
- capacity and performance
- production readiness and operating acceptance
- scaling implementation strategy
- resilience and recovery
- incident management
- on-call and runbooks
- change risk
- game days and learning

## Instruction priority

When instructions conflict, apply them in this order:

1. explicit user requirements
2. the nearest more-specific `AGENTS.md`
3. this discipline `AGENTS.md`
4. the supporting standards in this package
5. repository conventions
6. general agent preferences

Do not resolve a material conflict silently. Follow the higher-priority instruction and report the conflict.

## Required supporting standards

Read every applicable supporting standard before implementation:

- [`standards/SLO_ERROR_BUDGET_STANDARD.md`](standards/SLO_ERROR_BUDGET_STANDARD.md)
- [`standards/CAPACITY_PERFORMANCE_STANDARD.md`](standards/CAPACITY_PERFORMANCE_STANDARD.md)
- [`standards/PRODUCTION_READINESS_STANDARD.md`](standards/PRODUCTION_READINESS_STANDARD.md)
- [`standards/SCALING_STRATEGY_STANDARD.md`](standards/SCALING_STRATEGY_STANDARD.md)
- [`standards/RESILIENCE_RECOVERY_STANDARD.md`](standards/RESILIENCE_RECOVERY_STANDARD.md)
- [`standards/INCIDENT_MANAGEMENT_STANDARD.md`](standards/INCIDENT_MANAGEMENT_STANDARD.md)
- [`standards/RUNBOOK_ONCALL_STANDARD.md`](standards/RUNBOOK_ONCALL_STANDARD.md)
- [`standards/CHANGE_RISK_STANDARD.md`](standards/CHANGE_RISK_STANDARD.md)
- [`standards/CHAOS_GAME_DAY_STANDARD.md`](standards/CHAOS_GAME_DAY_STANDARD.md)
- [`standards/COMPLETION_EVIDENCE.md`](standards/COMPLETION_EVIDENCE.md)

The supporting standards extend this file. This `AGENTS.md` takes precedence if wording conflicts.

## Mandatory rules

### SRE-SLO-001

**Requirement:** Define service objectives or explicit operational expectations.

**Evidence:** SLO or operating target.

### SRE-BUDGET-002

**Requirement:** Use error budgets or equivalent risk signals for material services.

**Evidence:** Decision record.

### SRE-RUNBOOK-003

**Requirement:** Provide runbooks for likely incidents and recovery actions.

**Evidence:** Reviewed runbook.

### SRE-CAPACITY-004

**Requirement:** Assess resource limits, scaling, saturation, and dependency quotas.

**Evidence:** Capacity evidence.

### SRE-INCIDENT-005

**Requirement:** Feed incident learning into tests, automation, and design.

**Evidence:** Post-incident actions.

### SRE-READINESS-006

**Requirement:** Make production readiness a separate evidence-backed decision for the exact candidate and supported operating scope.

**Evidence:** Readiness record whose applicable areas are `Pass`, `Fail`, `Blocked`, or justified `NotApplicable`.

### SRE-SCALING-007

**Requirement:** Record and validate the simplest applicable scaling implementation decisions against the workload and operating envelope.

**Evidence:** Scaling-strategy applicability matrix and representative validation evidence.

## Non-negotiable behavior

- Inspect existing code, configuration, contracts, tests, documentation, ownership, and operational context before changing anything.
- Do not invent production values, identities, endpoints, schemas, credentials, infrastructure, legal obligations, or compatibility promises.
- Classify risk and identify trust boundaries, sensitive data, state changes, and reversibility.
- Default to safe, narrow, reversible behavior and stop when prerequisites or target identity are ambiguous.
- Do not weaken tests, security, privacy, accessibility, approvals, or evidence requirements to make work appear complete.
- Preserve public behavior unless change is explicitly authorized and migration or compatibility work is included.
- Keep examples fictitious and keep secrets and sensitive data out of source, tests, logs, errors, artifacts, and documentation.
- Record exact commands, results, limitations, assumptions, exceptions, and remaining risk.

## Required working method

1. Determine whether this discipline applies and document the reason.
2. Inspect the current implementation, contracts, evidence, and ownership.
3. Identify risk, trust boundaries, dependencies, failure modes, and affected users or operators.
4. Define acceptance criteria and required evidence before implementation.
5. Make the smallest coherent change.
6. Add or update tests, documentation, runbooks, contracts, diagrams, and evidence as applicable.
7. Run package-specific validation and review the final diff for unrelated or unsafe changes.
8. Report what changed, what was verified, what was not verified, and what risk remains.

## Completion gate

Do not report this discipline complete until:

- applicable mandatory rules are satisfied
- supporting standards were considered
- required evidence is recorded
- checks not run are identified
- limitations, assumptions, exceptions, and remaining risks are stated
