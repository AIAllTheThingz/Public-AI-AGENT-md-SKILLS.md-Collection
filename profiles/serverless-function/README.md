---
id: PROFILE-SERVERLESS-PKG-001
title: Serverless Function Project Profile Package
version: 0.2.0
status: baseline
---
# Serverless Function Project Profile Package

## Purpose

Define the minimum standards composition for event-driven functions whose execution, scaling, retries, identity, and lifecycle are controlled by a managed runtime.

This package is a project-shape overlay. It composes governance, language, discipline, framework, platform, virtualization, operating-system, networking, and project-specific standards into a coherent starting point.

Status: **baseline**

## Canonical profile

The stable profile entry point is [`../SERVERLESS_FUNCTION.md`](../SERVERLESS_FUNCTION.md).

The canonical file provides the normative summary. This package supplies the detailed adoption model, standards, templates, and example.

## When to adopt

Adopt this profile when:

- HTTP-triggered functions
- queue and event consumers
- scheduled functions
- stream processors
- event-driven integration handlers

Do not use it as the primary profile for:

- long-running worker services
- containerized services with explicit process lifecycle
- client-side functions

## Typical starting risk

`moderate`

Reclassify using actual project facts. Escalate for public exposure, privilege, destructive capability, sensitive data, tenant boundaries, weak rollback, availability, safety, or incomplete evidence.

## What this package does not replace

This package does not replace:

- governance authority and risk classification
- architecture and threat modeling
- language or framework standards
- platform ownership
- discipline packages
- organization policy or legal obligations
- project-specific tests and evidence
- production-readiness approval

## Package structure

```text
profiles/serverless-function/
├── AGENTS.md
├── README.md
├── MANIFEST.md
├── standards/
│   ├── PROJECT_BOUNDARY_STANDARD.md
│   ├── ARCHITECTURE_DECISION_STANDARD.md
│   ├── SECURITY_PRIVACY_STANDARD.md
│   ├── TESTING_VALIDATION_STANDARD.md
│   ├── OPERATIONS_RELEASE_STANDARD.md
│   └── COMPLETION_EVIDENCE.md
├── templates/
│   ├── ADOPTION_CHECKLIST.md
│   ├── REVIEW_CHECKLIST.md
│   └── EVIDENCE_RECORD_TEMPLATE.md
└── examples/
    └── ADOPTION_EXAMPLE.md
```

## Normative entry points

- [`AGENTS.md`](AGENTS.md)
- [`../SERVERLESS_FUNCTION.md`](../SERVERLESS_FUNCTION.md)
- [`MANIFEST.md`](MANIFEST.md)

## Required disciplines

- [Application Security](../../disciplines/application-security/)
- [Testing and Quality Engineering](../../disciplines/testing/)
- [Integration Engineering](../../disciplines/integration/)
- [Observability](../../disciplines/observability/)
- [CI/CD](../../disciplines/ci-cd/)
- [Software Supply Chain](../../disciplines/supply-chain/)

## Conditional disciplines

- [Product Management](../../disciplines/product-management/)
- [User Experience](../../disciplines/user-experience/)
- [Architecture and System Design](../../disciplines/architecture/)
- [Site Reliability Engineering](../../disciplines/sre/)
- [Release Engineering](../../disciplines/release-engineering/)
- [Privacy and Data Governance](../../disciplines/privacy/)
- [Data Engineering](../../disciplines/data-engineering/)

A conditional discipline becomes required when its concern exists. “Another team handles that” is a responsibility statement only when the boundary and evidence are explicit.

Product Management becomes required when the function defines or materially changes a product capability, actor outcome, requirement set, or supported scope. User Experience becomes required only when this scope owns a human workflow or interface; a bounded event handler implementing an existing governed contract may justify omission.

## Language, framework, and platform selection

This profile intentionally does not choose a language, framework, or platform.

The adopting project must declare:

- implementation languages
- frameworks
- execution and deployment platforms
- supported versions
- package and dependency management
- build and release tooling
- compatibility commitments
- operational ownership

## Required project decisions

- event validation and schema
- idempotency and duplicate delivery
- timeout, retry, and dead-letter behavior
- least-privilege execution identity
- concurrency and scaling limits
- cold-start and dependency behavior
- state and external side effects
- deployment, rollback, and observability

## Architecture and trust boundaries

Document:

- event source and delivery guarantees
- runtime and execution identity
- external dependencies
- state and idempotency store
- network and secret boundaries
- deployment and telemetry

Use [`standards/PROJECT_BOUNDARY_STANDARD.md`](standards/PROJECT_BOUNDARY_STANDARD.md) and [`standards/ARCHITECTURE_DECISION_STANDARD.md`](standards/ARCHITECTURE_DECISION_STANDARD.md).

## Security and privacy expectations

- event and caller validation
- least-privilege role
- secret injection and rotation
- egress and dependency restrictions
- sensitive payload and logging boundaries
- abuse and cost controls

Use [`standards/SECURITY_PRIVACY_STANDARD.md`](standards/SECURITY_PRIVACY_STANDARD.md).

## Testing and validation expectations

- event schemas and malformed events
- duplicate delivery and retries
- timeout and partial failure
- concurrency and scaling
- dependency outage
- deployment and rollback

Use [`standards/TESTING_VALIDATION_STANDARD.md`](standards/TESTING_VALIDATION_STANDARD.md).

## Operations and release expectations

- invocation, error, retry, throttle, and dead-letter signals
- cost and concurrency monitoring
- runbooks for replay and poison events
- runtime and dependency updates
- release and rollback
- ownership of event sources and destinations

Use [`standards/OPERATIONS_RELEASE_STANDARD.md`](standards/OPERATIONS_RELEASE_STANDARD.md).

## Suggested nested instructions

Consider scoped `AGENTS.md` files under:

- src/function
- src/integrations
- tests
- docs
- infra

Nested instructions specialize local work. They may be stricter but may not silently weaken governance or the selected packages.

## Common failure modes

- assuming exactly-once delivery
- unbounded retries or concurrency
- blocking runtime threads
- secrets in environment dumps
- no dead-letter ownership
- treating managed runtime as managed application behavior

Other recurring failures include copying example facts, treating a profile as architecture approval, omitting conditional packages without justification, and claiming completion from partial evidence.

## Adoption workflow

1. Read root governance and the [profile collection guide](../README.md).
2. Confirm this is the primary or a scoped secondary profile.
3. Record profile-selection rationale.
4. Classify risk.
5. Select applicable language, discipline, framework, platform, virtualization, operating-system, and networking packages.
6. Complete the adoption checklist.
7. Document architecture, security, tests, operations, and release decisions.
8. Add nested instructions for distinct scopes.
9. Define exact validation commands and evidence.
10. Review exclusions and exceptions.
11. Validate links, IDs, manifests, and project behavior.
12. Obtain accountable review.

## Tailoring checklist

Before adoption, define:

- project purpose and non-goals
- users and operators
- interfaces and trust boundaries
- data and privacy
- identities and privileges
- state and storage
- dependencies and integrations
- deployment and environments
- supported versions
- validation and test environments
- observability and support
- recovery and migration
- release and compatibility
- evidence retention
- reviewers and approvers

## Evidence

Use [`templates/EVIDENCE_RECORD_TEMPLATE.md`](templates/EVIDENCE_RECORD_TEMPLATE.md) and [`standards/COMPLETION_EVIDENCE.md`](standards/COMPLETION_EVIDENCE.md).

Evidence should include:

- profile rationale
- selected and omitted packages
- risk
- changed scope
- decisions
- validation commands and results
- representative environments
- checks not run
- limitations and residual risk
- review and approval
- production-readiness status

## Common validation

From the standards repository root:

```bash
python tools/validate-standards/validate_repository.py
python tools/check-links/check_links.py
```

The adopting project must define executable checks for its real implementation.

## Templates and example

- [`ADOPTION_CHECKLIST.md`](templates/ADOPTION_CHECKLIST.md)
- [`REVIEW_CHECKLIST.md`](templates/REVIEW_CHECKLIST.md)
- [`EVIDENCE_RECORD_TEMPLATE.md`](templates/EVIDENCE_RECORD_TEMPLATE.md)
- [`ADOPTION_EXAMPLE.md`](examples/ADOPTION_EXAMPLE.md)

Examples are fictitious. Replace them with reviewed facts and actual evidence.

## Maintenance

Package changes must preserve stable IDs, update canonical and package files together, state migration impact, validate links, and disclose checks not run.

## Completion boundary

Adopting this package does not prove that the project is complete or production-ready. Completion requires implementation, validation, evidence, and accountable review.
