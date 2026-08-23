---
id: DISC-SRE-PRODUCTION-READINESS-STANDARD
title: Production Readiness Standard
version: 0.1.0
status: baseline
---

# Production Readiness Standard

## Purpose

Require an evidence-backed operational decision for the exact candidate and supported production scope.

## Required behavior

- Define candidate artifact or revision, environments, traffic or workload boundary, data scope, owners, dependencies, limitations, and decision authority.
- Evaluate applicable deployment, rollback, backup, restore, recovery, observability, logging, monitoring, alerting, SLO, capacity, security, privacy, configuration, secret handling, ownership, runbook, incident-response, cost, and risk evidence.
- Test dependency failure behavior and recovery proportionate to risk; document untested or unsafe scenarios rather than simulating success.
- Verify configuration and secrets come from approved mechanisms without exposing values.
- Assess Privacy separately from Security when personal or sensitive data is in scope; security evidence must not be reused to imply privacy review.
- Identify operational and escalation owners, support windows, runbooks, known limitations, unresolved risks, follow-up, and re-review triggers.
- Assign each readiness area `Pass`, `Fail`, `Blocked`, or justified `NotApplicable`. `NotRun` is an evidence state and cannot support `Pass` for an applicable required area.
- Tie every pass to current evidence for the candidate, supported configuration, and representative environment. Prior or different-artifact evidence requires explicit applicability justification.

## Readiness areas

| Area | Minimum decision question |
|---|---|
| Deployment | Is deployment authorized, repeatable, observable, and bounded? |
| Rollback and recovery | Can the change, service, data, and dependencies be restored within approved expectations? |
| Backup and restore | Are applicable data/configuration backups protected and restoration verified? |
| Observability | Do logs, metrics, traces, health, dashboards, alerts, and SLOs support detection and diagnosis without unsafe disclosure? |
| Capacity | Is expected demand, headroom, saturation, quota, resource limit, and scaling behavior understood? |
| Security | Are threats, vulnerabilities, access, secrets, configuration, supply chain, and residual risks reviewed? |
| Privacy | Are applicable personal or sensitive data purpose, minimization, access, retention, disclosure, logging, deletion, and privacy review requirements addressed? |
| Failure behavior | Are dependency, timeout, retry, partial failure, degradation, and recovery behaviors known and tested where safe? |
| Operations | Are service ownership, on-call or escalation, runbooks, incident response, change windows, and support boundaries explicit? |
| Cost | Are material fixed, variable, scaling, telemetry, data-transfer, and recovery costs understood within authorized boundaries? |
| Limitations and risks | Are unresolved risks, exceptions, conditions, owners, and review dates visible? |

## Required evidence

Completed readiness record, exact artifact and configuration identity, test and deployment evidence, restore or recovery evidence, observability review, capacity decision, security review, applicable privacy review, runbooks, ownership, costs, limitations, risks, approvals, and checks not run.

## Decision gate

The overall result is:

- `Pass` only when every applicable required area passes and accountable approval conditions are satisfied.
- `Fail` when evidence shows an unacceptable unmet condition.
- `Blocked` when a prerequisite or decision prevents completion.
- `NotApplicable` only when production readiness is genuinely outside scope and the rationale is reviewed.

A readiness pass does not itself deploy, authorize an agent to approve production use, or establish operational verification.

## Completion gate

Do not report production readiness until the exact candidate and operating scope have a dated decision whose evidence, limitations, unresolved risks, owners, and checks not run are visible.
