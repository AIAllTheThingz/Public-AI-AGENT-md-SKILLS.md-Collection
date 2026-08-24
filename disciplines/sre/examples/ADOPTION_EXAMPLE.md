---
id: DISC-EX-SRE-ADOPTION
title: Site Reliability Engineering Adoption Example
version: 0.1.0
status: baseline
---
# Site Reliability Engineering Adoption Example

This example shows composition, not a universal project design.

## Example project

A fictitious project determines that the **Site Reliability Engineering** discipline applies because:

- a service or operational workflow has availability or recovery expectations
- on-call support exists
- dependency, scaling, saturation, or incident risk is material

The project composes:

- root governance standards
- one applicable language package
- one project profile
- this discipline package
- the [`Observability`](../../observability/) discipline
- the [`Architecture and System Design`](../../architecture/) discipline
- the [`CI/CD`](../../ci-cd/) discipline

## Tailored project instructions

The project `AGENTS.md` adds:

- named owners and reviewers
- exact supported environments and boundaries
- project-specific tools and validation commands
- required evidence locations
- compatibility, migration, rollback, recovery, and support constraints
- stricter rules required by the organization

It does not remove shared controls merely because they are inconvenient.

## Example evidence summary

- defined SLOs or operating targets
- capacity and saturation evidence
- recovery and failover tests
- reviewed runbooks and escalation
- documented reliability risks
- a production-readiness record tied to the fictitious candidate, with every applicable area assessed, Data migration, Security, and Privacy recorded separately when applicable, migration rehearsal plus irreversible-step handling and explicit go/no-go criteria where applicable, and no pass inferred from deployment, backup, or restore alone
- a scaling applicability matrix that justifies simple single-instance choices, records representative validation that misses criteria as `Failed`, leaves unexecuted scaling validation as `NotRun`, and therefore does not report the overall scaling strategy `Verified` while either state exists

The example does not claim `OperationallyVerified` or a `production` lifecycle state: no real production service, successful exact-artifact production deployment, post-deployment verification, or representative production workload exists. Its readiness record and any approval cannot substitute for those missing deployment facts.

The completion report also lists checks not run, known limitations, accepted exceptions, residual risks, and follow-up owners.

All project names, targets, users, and values in an adopted example must be fictitious or approved for public documentation.
