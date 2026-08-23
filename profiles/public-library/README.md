---
id: PROFILE-LIB-PKG-001
title: Public Library Project Profile Package
version: 0.2.0
status: baseline
---
# Public Library Project Profile Package

## Purpose

Define the minimum standards composition for libraries, SDKs, packages, and reusable components consumed outside the repository's direct control.

This package is a project-shape overlay. It composes governance, language, discipline, framework, platform, virtualization, operating-system, networking, and project-specific standards into a coherent starting point.

Status: **baseline**

## Canonical profile

The stable profile entry point is [`../PUBLIC_LIBRARY.md`](../PUBLIC_LIBRARY.md).

The canonical file provides the normative summary. This package supplies the detailed adoption model, standards, templates, and example.

## When to adopt

Adopt this profile when:

- public packages
- internal shared libraries with compatibility commitments
- SDKs
- plugins and extension libraries
- reusable modules published to registries

Do not use it as the primary profile for:

- private application code with no consumer contract
- single-repository implementation details
- deployment-only configuration

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
profiles/public-library/
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
- [`../PUBLIC_LIBRARY.md`](../PUBLIC_LIBRARY.md)
- [`MANIFEST.md`](MANIFEST.md)

## Required disciplines

- [Product Management](../../disciplines/product-management/)
- [Architecture and System Design](../../disciplines/architecture/)
- [Testing and Quality Engineering](../../disciplines/testing/)
- [Documentation](../../disciplines/documentation/)
- [Software Supply Chain](../../disciplines/supply-chain/)
- [Release Engineering](../../disciplines/release-engineering/)

## Conditional disciplines

- [User Experience](../../disciplines/user-experience/)
- [Application Security](../../disciplines/application-security/)
- [API Engineering](../../disciplines/api-engineering/)
- [CI/CD](../../disciplines/ci-cd/)
- [Accessibility](../../disciplines/accessibility/)
- [Privacy and Data Governance](../../disciplines/privacy/)

A conditional discipline becomes required when its concern exists. “Another team handles that” is a responsibility statement only when the boundary and evidence are explicit.

User Experience becomes required when consumers pursue material goals through interactive documentation, tooling, samples, or other governed workflows; API and documentation review alone must not be presented as observed UX evidence.

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

- consumer problem, intended adopters, desired outcomes, requirements, supported scope, acceptance criteria, and traceability
- public API compatibility
- supported runtimes and platforms
- dependency minimization
- semantic versioning
- examples and migration guidance
- deprecation and end-of-support
- package signing and provenance
- security reporting and release process

## Architecture and trust boundaries

Document:

- public API surface
- internal implementation boundary
- dependency and extension points
- serialization and compatibility
- build and package artifacts
- consumer documentation and migration

Use [`standards/PROJECT_BOUNDARY_STANDARD.md`](standards/PROJECT_BOUNDARY_STANDARD.md) and [`standards/ARCHITECTURE_DECISION_STANDARD.md`](standards/ARCHITECTURE_DECISION_STANDARD.md).

## Security and privacy expectations

- safe defaults
- input and data handling
- dependency and provenance review
- secret-free examples
- security advisory process
- unsupported-version handling

Use [`standards/SECURITY_PRIVACY_STANDARD.md`](standards/SECURITY_PRIVACY_STANDARD.md).

## Testing and validation expectations

- public contract tests
- compatibility matrix
- consumer integration tests
- packaging and installation
- documentation examples
- performance and concurrency where promised

Use [`standards/TESTING_VALIDATION_STANDARD.md`](standards/TESTING_VALIDATION_STANDARD.md).

## Operations and release expectations

- release notes and changelog
- package registry ownership
- deprecation communication
- vulnerability response
- support policy
- artifact provenance and retention

Use [`standards/OPERATIONS_RELEASE_STANDARD.md`](standards/OPERATIONS_RELEASE_STANDARD.md).

## Suggested nested instructions

Consider scoped `AGENTS.md` files under:

- src/public
- src/internal
- tests
- docs
- packaging
- examples

Nested instructions specialize local work. They may be stricter but may not silently weaken governance or the selected packages.

## Common failure modes

- breaking changes in patch releases
- undocumented public behavior
- unnecessary transitive dependencies
- examples that do not compile
- unsupported compatibility claims
- publishing untraceable artifacts

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
