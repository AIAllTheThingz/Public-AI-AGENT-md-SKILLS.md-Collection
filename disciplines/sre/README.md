---
id: DISC-PKG-SRE
title: Site Reliability Engineering Discipline Package
version: 0.1.0
status: baseline
---
# Site Reliability Engineering Discipline Package

## Purpose

This package provides project-agnostic, language-neutral standards for **Site Reliability Engineering** work.

It exists to connect reliability objectives to architecture, delivery, operations, incident learning, and capacity decisions. The package converts broad expectations into explicit agent instructions, review questions, required evidence, and completion gates.

This package is a **baseline**, not a claim of universal completeness. The adopting repository remains responsible for selecting applicable obligations, declaring its environment, assigning accountable owners, and adding stricter project or organizational requirements.

## What this package controls

- service objectives and error budgets
- capacity and performance
- production readiness
- explicit scaling implementation strategy
- resilience and recovery
- incident management
- on-call and runbooks
- change risk
- game days and learning

## When to adopt this package

Adopt this discipline when one or more of the following are true:

- a service or operational workflow has availability or recovery expectations
- on-call support exists
- dependency, scaling, saturation, or incident risk is material
- changes can affect production reliability

Do not omit the package merely because its controls add work. Omit it only when the discipline is genuinely inapplicable and the tailoring decision is documented.

## What this package does not replace

This package does not replace:

- accountable human review
- organization policy, law, regulation, contractual obligations, or professional judgment
- project-specific architecture, risk, data classification, support, or deployment decisions
- language, framework, platform, virtualization, operating-system, networking, and project-profile standards
- product, security, privacy, accessibility, legal, or operational specialists where their review is required

## Package structure

```text
disciplines/sre/
├── AGENTS.md
├── README.md
├── MANIFEST.md
├── standards/
│   ├── SLO_ERROR_BUDGET_STANDARD.md
│   ├── CAPACITY_PERFORMANCE_STANDARD.md
│   ├── PRODUCTION_READINESS_STANDARD.md
│   ├── SCALING_STRATEGY_STANDARD.md
│   ├── RESILIENCE_RECOVERY_STANDARD.md
│   ├── INCIDENT_MANAGEMENT_STANDARD.md
│   ├── RUNBOOK_ONCALL_STANDARD.md
│   ├── CHANGE_RISK_STANDARD.md
│   ├── CHAOS_GAME_DAY_STANDARD.md
│   └── COMPLETION_EVIDENCE.md
├── templates/
│   ├── ADOPTION_CHECKLIST.md
│   ├── REVIEW_CHECKLIST.md
│   └── EVIDENCE_RECORD_TEMPLATE.md
└── examples/
    └── ADOPTION_EXAMPLE.md
```

## Normative entry point

Start with [`AGENTS.md`](AGENTS.md). It contains the mandatory agent rules, preserves the discipline's stable rule identifiers, defines instruction precedence, and points to the supporting standards.

[`MANIFEST.md`](MANIFEST.md) defines the package inventory and acceptance checks.

## Supporting standards

| Standard | Purpose |
|---|---|
| [`SLO and Error Budget Standard`](standards/SLO_ERROR_BUDGET_STANDARD.md) | Define service indicators, objectives, measurement windows, exclusions, ownership, and decision use for reliability risk. |
| [`Capacity and Performance Standard`](standards/CAPACITY_PERFORMANCE_STANDARD.md) | Assess demand, saturation, quotas, bottlenecks, scaling, cost, and headroom using representative evidence. |
| [`Production Readiness Standard`](standards/PRODUCTION_READINESS_STANDARD.md) | Decide whether the exact candidate is operationally ready using deployment, recovery, observability, capacity, security, applicable privacy, ownership, cost, limitation, and risk evidence. |
| [`Scaling Strategy Standard`](standards/SCALING_STRATEGY_STANDARD.md) | Make applicable scaling implementation choices explicit without imposing complexity on simple systems. |
| [`Resilience and Recovery Standard`](standards/RESILIENCE_RECOVERY_STANDARD.md) | Define dependency failure, redundancy, degradation, backup, restore, RTO, RPO, failover, and recovery validation. |
| [`Incident Management Standard`](standards/INCIDENT_MANAGEMENT_STANDARD.md) | Define detection, severity, roles, communication, containment, recovery, evidence preservation, and learning. |
| [`Runbook and On-Call Standard`](standards/RUNBOOK_ONCALL_STANDARD.md) | Provide actionable diagnostics, safe procedures, escalation, access requirements, rollback, and ownership. |
| [`Change Risk Standard`](standards/CHANGE_RISK_STANDARD.md) | Use risk classification, progressive delivery, maintenance windows, approvals, rollback, and error-budget signals. |
| [`Game Day and Learning Standard`](standards/CHAOS_GAME_DAY_STANDARD.md) | Exercise credible failure and recovery scenarios safely, record observations, and feed findings into design and tests. |
| [`SRE Completion Evidence`](standards/COMPLETION_EVIDENCE.md) | Record objectives, capacity results, resilience tests, runbooks, incident actions, change controls, limitations, and residual risks. |

## Adoption workflow

1. Read the repository root `AGENTS.md` and governance standards.
2. Confirm that this discipline applies to the project or change.
3. Copy or compose the complete package, not just the README.
4. Preserve the package `AGENTS.md` and stable rule identifiers.
5. Declare project-specific scope, owners, environments, constraints, and required evidence.
6. Select companion language, framework, platform, virtualization, operating-system, networking, profile, and discipline packages.
7. Add stricter nested `AGENTS.md` files where directories require more specific controls.
8. Complete the adoption checklist and review checklist.
9. Run the repository validator and relative-link checker.
10. Obtain accountable review before promoting the tailored package for normal use.

## Project tailoring checklist

Before adoption, the project must answer:

- What work, components, data, environments, and users are in scope?
- Who owns implementation, review, approval, operations, exceptions, and follow-up?
- What risk classification applies?
- What trust boundaries, external dependencies, and sensitive data are involved?
- Which requirements are mandatory, conditionally applicable, or provably inapplicable?
- What tools, tests, review methods, environments, and evidence are required?
- What compatibility, migration, rollback, recovery, and support constraints exist?
- What laws, regulations, contracts, organization policies, or external standards apply?
- Where will evidence, decisions, exceptions, and residual risk be recorded?
- What would prevent the work from being reported complete?

## Required evidence

Typical completion evidence includes:

- defined SLOs or operating targets
- capacity and saturation evidence
- production-readiness per-area results, including Privacy separately when applicable, plus a separate overall result and decision authority for the exact candidate and supported operating scope
- scaling-strategy applicability decisions and representative verification where claimed
- recovery and failover tests
- reviewed runbooks and escalation
- documented reliability risks
- exact validation commands and results
- checks not run and the reason
- affected environments and representative test conditions
- accepted exceptions and expiration or review dates
- known limitations, unresolved risks, owners, and follow-up actions

Evidence must distinguish **planned**, **implemented**, **tested**, **reviewed**, and **operationally verified**. These are not interchangeable states, despite humanity's recurring attempts to treat them as synonyms.

## Validation

Validate the standards repository itself with:

```bash
python tools/validate-standards/validate_repository.py
python tools/check-links/check_links.py
```

The adopting project must also define discipline-specific validation commands and review procedures. This package intentionally does not invent tool names, environments, credentials, endpoints, data sets, or production targets.

## Authoritative starting points

- [Google Site Reliability Engineering book](https://sre.google/sre-book/table-of-contents/)
- [Google Site Reliability Workbook](https://sre.google/workbook/table-of-contents/)
- [Kubernetes resource management](https://kubernetes.io/docs/concepts/configuration/manage-resources-containers/) and [Horizontal Pod Autoscaling](https://kubernetes.io/docs/concepts/workloads/autoscaling/horizontal-pod-autoscale/) when Kubernetes applies
- [AWS Well-Architected Reliability Pillar](https://docs.aws.amazon.com/wellarchitected/latest/reliability-pillar/welcome.html), [Azure Well-Architected Reliability guidance](https://learn.microsoft.com/en-us/azure/well-architected/reliability/), or [Google Cloud Well-Architected Reliability pillar](https://docs.cloud.google.com/architecture/framework/reliability) only for the applicable cloud context

These sources are starting points, not certification, compliance, vendor endorsement, or operational evidence. Technology-specific decisions also require the current official runtime, framework, platform, and service documentation for the selected boundary.

Accountable review dates and sources are recorded in [`SOURCE_REVIEWS.json`](../../SOURCE_REVIEWS.json), with durable findings under [`source-reviews/`](../../source-reviews/).

## Common failure modes

- creating SLOs that do not drive decisions
- monitoring resources without user outcomes
- assuming backups are recoverable
- writing runbooks that require tribal knowledge
- treating every incident as operator error
- treating deployment success as production readiness
- forcing distributed infrastructure onto a workload that does not require it

Other common mistakes include copying only selected controls without documenting omissions, declaring success without evidence, treating a scanner or checklist as proof by itself, and assuming the package removes the need for human accountability.

## Companion disciplines

This package commonly composes with:

- [`Observability`](../observability/)
- [`Architecture and System Design`](../architecture/)
- [`CI/CD`](../ci-cd/)
- [`Release Engineering`](../release-engineering/)
- [`Testing and Quality Engineering`](../testing/)
- [`Documentation`](../documentation/)
- [`Privacy`](../privacy/)

Companion disciplines supplement this package. They do not replace its applicable rules.

## Templates and example

- [`ADOPTION_CHECKLIST.md`](templates/ADOPTION_CHECKLIST.md) helps tailor the package to a repository.
- [`REVIEW_CHECKLIST.md`](templates/REVIEW_CHECKLIST.md) supports change and package review.
- [`EVIDENCE_RECORD_TEMPLATE.md`](templates/EVIDENCE_RECORD_TEMPLATE.md) provides a repeatable evidence structure.
- [`ADOPTION_EXAMPLE.md`](examples/ADOPTION_EXAMPLE.md) shows how to compose this discipline with governance and other standards.

Templates are starting points. Replace placeholders with reviewed project facts and never insert production secrets or sensitive identifiers.

## Maturity and maintenance

Status: **baseline**

A baseline package is usable for adoption and review but should be expected to evolve. Changes must:

- preserve stable identifiers unless a documented breaking change is approved
- update the README, manifest, templates, and examples when package behavior changes
- keep requirements specific, testable, risk-proportionate, and evidence-based
- avoid duplicating shared governance when a reference is sufficient
- run repository validation and link checking
- state compatibility, migration, and deprecation impact

## Completion statement

Adopting this package does not prove that site reliability engineering work is complete. Completion requires implementation, verification, evidence, accountable review, and explicit disclosure of remaining limitations.
