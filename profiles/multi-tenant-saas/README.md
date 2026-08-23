---
id: PROFILE-SAAS-PKG-001
title: Multi-Tenant SaaS Project Profile Package
version: 0.2.0
status: baseline
---
# Multi-Tenant SaaS Project Profile Package

## Purpose

Define the minimum standards composition for hosted software serving multiple tenants with isolation, authorization, data lifecycle, quota, billing, and operational obligations.

This package is a project-shape overlay. It composes governance, language, discipline, framework, platform, virtualization, operating-system, networking, and project-specific standards into a coherent starting point.

Status: **baseline**

## Canonical profile

The stable profile entry point is [`../MULTI_TENANT_SAAS.md`](../MULTI_TENANT_SAAS.md).

The canonical file provides the normative summary. This package supplies the detailed adoption model, standards, templates, and example.

## When to adopt

Adopt this profile when:

- shared-application multi-tenant SaaS
- shared-database or isolated-database tenant models
- tenant-aware APIs and web applications
- hosted platforms with tenant administration

Do not use it as the primary profile for:

- single-tenant internal applications
- public libraries
- consumer applications without tenant boundaries

## Typical starting risk

`high`

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
profiles/multi-tenant-saas/
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
- [`../MULTI_TENANT_SAAS.md`](../MULTI_TENANT_SAAS.md)
- [`MANIFEST.md`](MANIFEST.md)

## Required disciplines

- [Application Security](../../disciplines/application-security/)
- [Architecture and System Design](../../disciplines/architecture/)
- [Testing and Quality Engineering](../../disciplines/testing/)
- [API Engineering](../../disciplines/api-engineering/)
- [Database Engineering](../../disciplines/database/)
- [Privacy and Data Governance](../../disciplines/privacy/)
- [Observability](../../disciplines/observability/)
- [Site Reliability Engineering](../../disciplines/sre/)
- [CI/CD](../../disciplines/ci-cd/)
- [Software Supply Chain](../../disciplines/supply-chain/)
- [Release Engineering](../../disciplines/release-engineering/)

## Conditional disciplines

- [Product Management](../../disciplines/product-management/)
- [User Experience](../../disciplines/user-experience/)
- [Integration Engineering](../../disciplines/integration/)
- [Data Engineering](../../disciplines/data-engineering/)
- [Accessibility](../../disciplines/accessibility/)
- [Documentation](../../disciplines/documentation/)

A conditional discipline becomes required when its concern exists. “Another team handles that” is a responsibility statement only when the boundary and evidence are explicit.

Product Management becomes required when the SaaS scope defines or materially changes a tenant or user outcome, requirement set, MVP boundary, acceptance criteria, or product decision. User Experience becomes required when tenants, end users, administrators, or support operators interact with a materially changed workflow or interface. API-only SaaS may justify UX omission, but must not infer UX validation from API testing. Profile selection alone does not make either discipline mandatory.

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

- tenant identity and isolation model
- authorization at every object boundary
- data partitioning and lifecycle
- tenant export and deletion
- noisy-neighbor and quota controls
- tenant-aware telemetry and support
- billing and entitlement boundaries
- migration, rollout, and recovery by tenant

## Architecture and trust boundaries

Document:

- tenant resolution
- authorization and policy enforcement
- data partitioning
- shared and tenant-specific services
- administration and support
- billing, telemetry, and deployment boundaries

Use [`standards/PROJECT_BOUNDARY_STANDARD.md`](standards/PROJECT_BOUNDARY_STANDARD.md) and [`standards/ARCHITECTURE_DECISION_STANDARD.md`](standards/ARCHITECTURE_DECISION_STANDARD.md).

## Security and privacy expectations

- cross-tenant access prevention
- object-level authorization
- tenant-scoped keys and secrets where applicable
- support and impersonation controls
- safe tenant identifiers in logs
- abuse and quota controls

Use [`standards/SECURITY_PRIVACY_STANDARD.md`](standards/SECURITY_PRIVACY_STANDARD.md).

## Testing and validation expectations

- cross-tenant negative tests
- tenant provisioning and deletion
- schema and migration by tenant
- quota and noisy-neighbor behavior
- support and admin access
- backup, restore, and export isolation

Use [`standards/TESTING_VALIDATION_STANDARD.md`](standards/TESTING_VALIDATION_STANDARD.md).

## Operations and release expectations

- tenant-aware health and telemetry
- incident scoping and communication
- per-tenant rollout and rollback
- capacity and cost allocation
- data lifecycle operations
- support and escalation

Use [`standards/OPERATIONS_RELEASE_STANDARD.md`](standards/OPERATIONS_RELEASE_STANDARD.md).

## Suggested nested instructions

Consider scoped `AGENTS.md` files under:

- src/tenant
- src/api
- src/data
- tests
- docs
- deploy

Nested instructions specialize local work. They may be stricter but may not silently weaken governance or the selected packages.

## Common failure modes

- filtering by tenant only in the UI
- shared caches without tenant keys
- global admin access without controls
- cross-tenant logs or exports
- migrations with no tenant rollback
- unbounded tenant resource consumption

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
