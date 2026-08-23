---
id: DISC-PKG-TEST
title: Testing and Quality Engineering Discipline Package
version: 0.1.0
status: baseline
---
# Testing and Quality Engineering Discipline Package

## Purpose

This package provides project-agnostic, language-neutral standards for **Testing and Quality Engineering** work.

It exists to produce meaningful evidence that behavior, failure handling, security, compatibility, and operational expectations are satisfied. The package converts broad expectations into explicit agent instructions, review questions, required evidence, and completion gates.

This package is a **baseline**, not a claim of universal completeness. The adopting repository remains responsible for selecting applicable obligations, declaring its environment, assigning accountable owners, and adding stricter project or organizational requirements.

## What this package controls

- test strategy and risk coverage
- unit and component tests
- integration and contract tests
- end-to-end and acceptance tests
- nonfunctional tests
- test data and environments
- defect regression

## When to adopt this package

Adopt this discipline when one or more of the following are true:

- software behavior changes
- a defect is fixed
- a contract or dependency changes
- risk warrants performance, security, recovery, or compatibility evidence

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
disciplines/testing/
├── AGENTS.md
├── README.md
├── MANIFEST.md
├── standards/
│   ├── TEST_STRATEGY_STANDARD.md
│   ├── UNIT_COMPONENT_STANDARD.md
│   ├── INTEGRATION_CONTRACT_STANDARD.md
│   ├── END_TO_END_STANDARD.md
│   ├── NONFUNCTIONAL_TESTING_STANDARD.md
│   ├── TEST_DATA_ENVIRONMENT_STANDARD.md
│   ├── DEFECT_REGRESSION_STANDARD.md
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
| [`Test Strategy Standard`](standards/TEST_STRATEGY_STANDARD.md) | Map test levels and evidence to requirements, risk, trust boundaries, failure modes, and supported environments. |
| [`Unit and Component Testing Standard`](standards/UNIT_COMPONENT_STANDARD.md) | Test cohesive behavior, boundaries, errors, state transitions, and invariants with deterministic isolated tests. |
| [`Integration and Contract Testing Standard`](standards/INTEGRATION_CONTRACT_STANDARD.md) | Validate schemas, protocols, authentication, authorization, timeouts, retries, compatibility, and representative dependency behavior. |
| [`End-to-End Testing Standard`](standards/END_TO_END_STANDARD.md) | Use focused end-to-end scenarios for critical user and operational journeys without replacing lower-level diagnostics. |
| [`Nonfunctional Testing Standard`](standards/NONFUNCTIONAL_TESTING_STANDARD.md) | Define contextual baseline, load, stress, spike, soak, scaling, failure-under-load, recovery-under-load, resilience, security, accessibility, and compatibility evidence. |
| [`Test Data and Environment Standard`](standards/TEST_DATA_ENVIRONMENT_STANDARD.md) | Use controlled, synthetic, minimal, isolated, reproducible data and environments; protect secrets and personal data. |
| [`Defect and Regression Standard`](standards/DEFECT_REGRESSION_STANDARD.md) | Capture fail-before and pass-after evidence, add durable regression coverage, and avoid weakening assertions or skipping tests. |
| [`Testing Completion Evidence`](standards/COMPLETION_EVIDENCE.md) | Record requirements covered, test commands, results, environments, skipped checks, flaky behavior, limitations, and residual risk. |

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

- risk-based test strategy
- repeatable test results
- performance-test applicability decisions, representative workload and environment, selected latency/throughput/error/resource/saturation/cost evidence, and supported operating envelope
- negative and failure-path coverage
- regression evidence
- documented gaps and unsupported environments
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

## Authoritative starting points for performance validation

- [Google Site Reliability Engineering book](https://sre.google/sre-book/table-of-contents/)
- [Google Site Reliability Workbook](https://sre.google/workbook/table-of-contents/)
- [Kubernetes resource management](https://kubernetes.io/docs/concepts/configuration/manage-resources-containers/) and [Horizontal Pod Autoscaling](https://kubernetes.io/docs/concepts/workloads/autoscaling/horizontal-pod-autoscale/) when Kubernetes is the system under test

Use current official runtime, framework, database, queue, cloud-service, or load-tool documentation for technology-specific metrics and limits. These links are starting points; they do not establish certification, compliance, representative test execution, or production performance.

Accountable review dates and sources are recorded in [`SOURCE_REVIEWS.json`](../../SOURCE_REVIEWS.json), with durable findings under [`source-reviews/`](../../source-reviews/).

## Common failure modes

- equating coverage percentage with quality
- mocking away the behavior under test
- using production data casually
- skipping negative and failure cases
- weakening tests to make CI green
- claiming performance from an unrepresentative happy-path benchmark
- reporting averages while hiding tail latency, errors, saturation, or incomplete recovery

Other common mistakes include copying only selected controls without documenting omissions, declaring success without evidence, treating a scanner or checklist as proof by itself, and assuming the package removes the need for human accountability.

## Companion disciplines

This package commonly composes with:

- [`Application Security`](../application-security/)
- [`Architecture and System Design`](../architecture/)
- [`CI/CD`](../ci-cd/)
- [`API Engineering`](../api-engineering/)
- [`Integration Engineering`](../integration/)
- [`Site Reliability Engineering`](../sre/)

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

Adopting this package does not prove that testing and quality engineering work is complete. Completion requires implementation, verification, evidence, accountable review, and explicit disclosure of remaining limitations.
