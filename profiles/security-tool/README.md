---
id: PROFILE-SECTOOL-PKG-001
title: Security Tool Project Profile Package
version: 0.2.0
status: baseline
---
# Security Tool Project Profile Package

## Purpose

Define the minimum standards composition for tools that inspect security posture, process findings, handle evidence, or perform authorized security-sensitive actions.

This package is a project-shape overlay. It composes governance, language, discipline, framework, platform, virtualization, operating-system, networking, and project-specific standards into a coherent starting point.

Status: **baseline**

## Canonical profile

The stable profile entry point is [`../SECURITY_TOOL.md`](../SECURITY_TOOL.md).

The canonical file provides the normative summary. This package supplies the detailed adoption model, standards, templates, and example.

## When to adopt

Adopt this profile when:

- security scanners
- configuration assessors
- finding-management tools
- vulnerability utilities
- security automation
- forensic or evidence-processing tools

Do not use it as the primary profile for:

- general monitoring tools with no security finding or privileged behavior
- malware or offensive tooling outside authorized defensive scope
- policy documents with no software implementation

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
profiles/security-tool/
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
- [`../SECURITY_TOOL.md`](../SECURITY_TOOL.md)
- [`MANIFEST.md`](MANIFEST.md)

## Required disciplines

- [Application Security](../../disciplines/application-security/)
- [Architecture and System Design](../../disciplines/architecture/)
- [Testing and Quality Engineering](../../disciplines/testing/)
- [Privacy and Data Governance](../../disciplines/privacy/)
- [Observability](../../disciplines/observability/)
- [Documentation](../../disciplines/documentation/)
- [Software Supply Chain](../../disciplines/supply-chain/)
- [Release Engineering](../../disciplines/release-engineering/)

## Conditional disciplines

- [Product Management](../../disciplines/product-management/)
- [User Experience](../../disciplines/user-experience/)
- [CI/CD](../../disciplines/ci-cd/)
- [Integration Engineering](../../disciplines/integration/)
- [Site Reliability Engineering](../../disciplines/sre/)
- [Data Engineering](../../disciplines/data-engineering/)
- [Database Engineering](../../disciplines/database/)

A conditional discipline becomes required when its concern exists. “Another team handles that” is a responsibility statement only when the boundary and evidence are explicit.

Product Management becomes required when the tool defines or materially changes a product capability, analyst or operator outcome, requirement set, or supported scope. User Experience becomes required for material analyst, operator, remediation, approval, or recovery workflows; a headless scanner implementing an existing governed contract may justify omission.

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

- authorized scope and target identity
- safe handling of findings and evidence
- false-positive and false-negative limitations
- privilege and data sensitivity
- non-destructive defaults
- remediation authorization
- finding lifecycle and disclosure
- audit, retention, and chain of custody

## Architecture and trust boundaries

Document:

- target and authorization boundary
- collection and analysis
- finding storage and classification
- reporting and disclosure
- optional remediation boundary
- audit and evidence retention

Use [`standards/PROJECT_BOUNDARY_STANDARD.md`](standards/PROJECT_BOUNDARY_STANDARD.md) and [`standards/ARCHITECTURE_DECISION_STANDARD.md`](standards/ARCHITECTURE_DECISION_STANDARD.md).

## Security and privacy expectations

- strict authorization and scope
- least privilege
- sensitive finding and evidence handling
- safe parsers and file handling
- non-destructive defaults
- secret and credential protection

Use [`standards/SECURITY_PRIVACY_STANDARD.md`](standards/SECURITY_PRIVACY_STANDARD.md).

## Testing and validation expectations

- known-positive and known-negative fixtures
- false-positive and false-negative characterization
- malformed and adversarial input
- privilege and target controls
- safe remediation simulation
- evidence integrity and redaction

Use [`standards/TESTING_VALIDATION_STANDARD.md`](standards/TESTING_VALIDATION_STANDARD.md).

## Operations and release expectations

- finding severity and ownership
- confidential disclosure
- retention and deletion
- scanner and rule updates
- audit trails
- support and incident response

Use [`standards/OPERATIONS_RELEASE_STANDARD.md`](standards/OPERATIONS_RELEASE_STANDARD.md).

## Suggested nested instructions

Consider scoped `AGENTS.md` files under:

- src/collect
- src/analyze
- src/report
- src/remediate
- tests
- docs

Nested instructions specialize local work. They may be stricter but may not silently weaken governance or the selected packages.

## Common failure modes

- scanning unauthorized targets
- presenting heuristics as certainty
- exposing exploitable details
- modifying systems by default
- storing raw secrets or evidence insecurely
- closing findings because a scanner went quiet

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
