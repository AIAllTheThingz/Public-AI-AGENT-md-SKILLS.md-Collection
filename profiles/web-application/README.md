---
id: PROFILE-WEB-APP-PKG-001
title: Web Application Project Profile Package
version: 0.2.0
status: baseline
---
# Web Application Project Profile Package

## Purpose

Define the minimum standards composition for browser-delivered applications with interactive user experiences, client and server trust boundaries, and accessibility obligations.

This package is a project-shape overlay. It composes governance, language, discipline, framework, platform, virtualization, operating-system, networking, and project-specific standards into a coherent starting point.

Status: **baseline**

## Canonical profile

The stable profile entry point is [`../WEB_APPLICATION.md`](../WEB_APPLICATION.md).

The canonical file provides the normative summary. This package supplies the detailed adoption model, standards, templates, and example.

## When to adopt

Adopt this profile when:

- single-page applications
- server-rendered web applications
- progressive web applications
- browser-based administrative tools
- full-stack web applications

Do not use it as the primary profile for:

- content-only static pages with no application behavior
- native desktop or mobile applications
- backend services with no browser interface

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
profiles/web-application/
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
- [`../WEB_APPLICATION.md`](../WEB_APPLICATION.md)
- [`MANIFEST.md`](MANIFEST.md)

## Required disciplines

- [Product Management](../../disciplines/product-management/)
- [User Experience](../../disciplines/user-experience/)
- [Application Security](../../disciplines/application-security/)
- [Architecture and System Design](../../disciplines/architecture/)
- [Testing and Quality Engineering](../../disciplines/testing/)
- [Accessibility](../../disciplines/accessibility/)
- [Privacy and Data Governance](../../disciplines/privacy/)
- [Observability](../../disciplines/observability/)
- [CI/CD](../../disciplines/ci-cd/)
- [Software Supply Chain](../../disciplines/supply-chain/)
- [Release Engineering](../../disciplines/release-engineering/)

## Conditional disciplines

- [API Engineering](../../disciplines/api-engineering/)
- [Database Engineering](../../disciplines/database/)
- [Integration Engineering](../../disciplines/integration/)
- [Site Reliability Engineering](../../disciplines/sre/)
- [Documentation](../../disciplines/documentation/)

A conditional discipline becomes required when its concern exists. “Another team handles that” is a responsibility statement only when the boundary and evidence are explicit.

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

- product problem, intended users, desired outcomes, requirements, MVP boundary, acceptance criteria, and traceability
- research evidence state, user journeys, interaction and recovery states, UX validation, and the separate Accessibility boundary
- server-side authorization model
- client and server trust boundaries
- WCAG 2.2 AA or stricter accessibility target
- content security and safe rendering
- browser support and assistive-technology coverage
- session and state management
- privacy, analytics, and consent behavior
- deployment, rollback, caching, and asset compatibility

## Architecture and trust boundaries

Document:

- browser and server boundaries
- frontend state and routing
- API and identity integration
- content delivery and caching
- data stores and third-party scripts
- deployment and observability boundaries

Use [`standards/PROJECT_BOUNDARY_STANDARD.md`](standards/PROJECT_BOUNDARY_STANDARD.md) and [`standards/ARCHITECTURE_DECISION_STANDARD.md`](standards/ARCHITECTURE_DECISION_STANDARD.md).

## Security and privacy expectations

- server-side authorization
- XSS and unsafe HTML controls
- CSRF or antiforgery where applicable
- content security policy and third-party script governance
- secret exclusion from client bundles
- privacy-safe analytics and diagnostics

Use [`standards/SECURITY_PRIVACY_STANDARD.md`](standards/SECURITY_PRIVACY_STANDARD.md).

## Testing and validation expectations

- keyboard and focus testing
- screen-reader and semantic review
- unit and component tests
- browser integration and end-to-end tests
- negative authorization and security tests
- asset, cache, deployment, and rollback checks

Use [`standards/TESTING_VALIDATION_STANDARD.md`](standards/TESTING_VALIDATION_STANDARD.md).

## Operations and release expectations

- client error and performance telemetry
- release compatibility across cached assets
- feature-flag and rollback behavior
- accessibility regression handling
- browser support ownership
- incident and support runbooks

Use [`standards/OPERATIONS_RELEASE_STANDARD.md`](standards/OPERATIONS_RELEASE_STANDARD.md).

## Suggested nested instructions

Consider scoped `AGENTS.md` files under:

- src/frontend
- src/backend
- tests
- docs
- public
- deploy

Nested instructions specialize local work. They may be stricter but may not silently weaken governance or the selected packages.

## Common failure modes

- client-side authorization
- inaccessible custom controls
- unsafe HTML injection
- unreviewed third-party scripts
- sensitive data in analytics
- deploying incompatible frontend and backend versions

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
