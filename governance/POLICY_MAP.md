---
id: GOV-MAP-001
title: Governance Policy Map
version: 0.2.0
status: baseline
---

# Governance Policy Map

## Purpose

This map shows how governance policies interact, which records they produce, and which decisions they control.

## Dependency map

```text
Organization Contract
├── Agent Working Method
├── Risk Classification
├── Human Review Policy
└── Exception Process

Risk Classification
├── Completion Evidence
├── Threat Modeling Policy
├── Secure Development Policy
├── Production Readiness
└── Vulnerability Response

Completion Evidence
├── Human Review Policy
├── Production Readiness
├── AI-Generated Code Policy
└── Vulnerability Response

Secure Development Policy
├── Threat Modeling Policy
└── Vulnerability Response
```

Dependencies indicate conceptual control, not permission to ignore a policy that is not shown beneath another.

When explicitly selected, the [Product Inception Lifecycle](PRODUCT_INCEPTION_LIFECYCLE.md) composes the Agent Working Method, Risk Classification, Completion Evidence, Human Review, Secure Development, and Production Readiness policies into Concept, Requirements, Design, Build, and product-state transitions. It is optional lifecycle guidance, not a repository-wide default, replacement policy, or parallel maturity system.

## Policy-to-record map

| Policy | Primary records |
|---|---|
| Organization Contract | authority, ownership, obligation, and authorization records |
| Agent Working Method | scope, assumptions, plan, validation, and final diff review |
| Risk Classification | risk record, required controls, reviewers, rollback requirement |
| Completion Evidence | completion result, validation output, limitations |
| Exception Process | exception request, approval, controls, expiration, closure |
| AI-Generated Code Policy | AI review, dependency verification, security tests |
| Human Review Policy | review record, approval, requested changes, conditions |
| Production Readiness | readiness review, deployment, rollback, operations, recovery |
| Secure Development Policy | threat, security tests, dependency and residual-risk evidence |
| Threat Modeling Policy | threat model, mitigations, validation, residual risk |
| Vulnerability Response | triage, affected scope, containment, fix, closure, lessons |

## Decision relationships

- Risk determines review, testing, authorization, evidence, and rollout depth.
- Working method controls how evidence is produced.
- Completion evidence constrains what may be claimed.
- Human review determines whether evidence is accepted.
- Exceptions alter selected controls temporarily but do not erase risk.
- Production readiness is a separate decision from implementation completion.
- When the optional Product Inception Lifecycle is selected, its gates constrain when normal production implementation may begin; bounded prototypes require explicit authorization and cannot silently become architecture of record.
- Product lifecycle state is evidence-backed and remains distinct from repository component maturity.
- Threat modeling feeds secure-development requirements.
- Vulnerability response feeds remediation, regression, and policy improvement.

## Change triggers

Revisit governance decisions when:

- scope expands
- architecture changes
- data classification changes
- privilege increases
- public exposure changes
- rollback becomes harder
- dependency or platform assumptions change
- a vulnerability or incident invalidates assumptions
- an exception expires
- evidence belongs to a different artifact or environment
- an approver or owner changes
