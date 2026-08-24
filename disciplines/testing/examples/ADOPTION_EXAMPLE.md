---
id: DISC-EX-TEST-ADOPTION
title: Testing and Quality Engineering Adoption Example
version: 0.1.0
status: baseline
---
# Testing and Quality Engineering Adoption Example

This example shows composition, not a universal project design.

## Example project

A fictitious project determines that the **Testing and Quality Engineering** discipline applies because:

- software behavior changes
- a defect is fixed
- a contract or dependency changes

The project composes:

- root governance standards
- one applicable language package
- one project profile
- this discipline package
- the [`Application Security`](../../application-security/) discipline
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

- risk-based test strategy
- repeatable test results
- negative and failure-path coverage
- regression evidence
- documented gaps and unsupported environments
- a contextual performance-test matrix whose rows distinguish execution state from `Pass`, `Fail`, `Blocked`, or justified `NotApplicable` outcome and identify the test owner, explicit execution authorization and safeguards, and safe stop conditions; the fictitious project aligns spike and soak state/outcome as `NotApplicable` with rationale, records production-scale recovery as state `NotRun` and outcome `Blocked`, and does not generalize a local passing baseline beyond its environment
- representative evidence selected from throughput, p95/p99 latency, error rate, CPU, memory, connection count, queue depth, database utilization, saturation, and cost rather than requiring every possible metric

The completion report also lists checks not run, known limitations, accepted exceptions, residual risks, and follow-up owners.

All project names, targets, users, and values in an adopted example must be fictitious or approved for public documentation.
