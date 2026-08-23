---
id: PROFILE-AUTOMATION-PKG-001
title: Internal Automation Project Profile Package
version: 0.2.0
status: baseline
---
# Internal Automation Project Profile Package

## Purpose

Define the minimum standards composition for automation that inspects or changes internal systems, infrastructure, applications, accounts, or data.

This package is a project-shape overlay. It composes governance, language, discipline, framework, platform, virtualization, operating-system, networking, and project-specific standards into a coherent starting point.

Status: **baseline**

## Canonical profile

The stable profile entry point is [`../INTERNAL_AUTOMATION.md`](../INTERNAL_AUTOMATION.md).

The canonical file provides the normative summary. This package supplies the detailed adoption model, standards, templates, and example.

## When to adopt

Adopt this profile when:

- administrative scripts
- operational workflows
- infrastructure automation
- remediation tools
- scheduled internal jobs
- cross-system orchestration

Do not use it as the primary profile for:

- public end-user applications
- read-only reporting with no privileged access unless sensitive data is involved
- developer-only local helpers with no shared operational use

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
profiles/internal-automation/
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
- [`../INTERNAL_AUTOMATION.md`](../INTERNAL_AUTOMATION.md)
- [`MANIFEST.md`](MANIFEST.md)

## Required disciplines

- [Application Security](../../disciplines/application-security/)
- [Testing and Quality Engineering](../../disciplines/testing/)
- [Documentation](../../disciplines/documentation/)
- [Observability](../../disciplines/observability/)
- [CI/CD](../../disciplines/ci-cd/)
- [Software Supply Chain](../../disciplines/supply-chain/)

## Conditional disciplines

- [Product Management](../../disciplines/product-management/)
- [User Experience](../../disciplines/user-experience/)
- [Architecture and System Design](../../disciplines/architecture/)
- [Integration Engineering](../../disciplines/integration/)
- [Release Engineering](../../disciplines/release-engineering/)
- [Site Reliability Engineering](../../disciplines/sre/)
- [Privacy and Data Governance](../../disciplines/privacy/)

A conditional discipline becomes required when its concern exists. “Another team handles that” is a responsibility statement only when the boundary and evidence are explicit.

Product Management becomes required when the automation defines or materially changes a governed internal product, operator outcome, requirement set, or supported scope. User Experience becomes required for material operator journeys, approvals, prompts, dashboards, or recovery workflows; bounded automation implementing an existing authorized procedure may justify omission.

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

- discovery and validation phases
- dry-run, what-if, or preview behavior
- least privilege and credential handling
- target allowlists and identity confirmation
- approval for destructive and bulk changes
- audit trail and reports
- rollback, compensation, and partial failure
- scheduling, ownership, and recovery

## Architecture and trust boundaries

Document:

- input and target selection
- credential and identity boundary
- system adapters
- orchestration and checkpoints
- reporting and evidence
- scheduling and operational ownership

Use [`standards/PROJECT_BOUNDARY_STANDARD.md`](standards/PROJECT_BOUNDARY_STANDARD.md) and [`standards/ARCHITECTURE_DECISION_STANDARD.md`](standards/ARCHITECTURE_DECISION_STANDARD.md).

## Security and privacy expectations

- target allowlists
- least privilege
- credential sources and redaction
- command, path, and query injection prevention
- explicit destructive authorization
- safe temporary files and artifacts

Use [`standards/SECURITY_PRIVACY_STANDARD.md`](standards/SECURITY_PRIVACY_STANDARD.md).

## Testing and validation expectations

- discovery-only behavior
- validation and prerequisite failures
- dry-run fidelity
- idempotency and reruns
- partial failure and compensation
- target identity and allowlist tests

Use [`standards/TESTING_VALIDATION_STANDARD.md`](standards/TESTING_VALIDATION_STANDARD.md).

## Operations and release expectations

- audit and report retention
- scheduled execution ownership
- status, progress, and alerting
- resume and recovery
- change windows and stop criteria
- manual intervention and escalation

Use [`standards/OPERATIONS_RELEASE_STANDARD.md`](standards/OPERATIONS_RELEASE_STANDARD.md).

## Suggested nested instructions

Consider scoped `AGENTS.md` files under:

- src/discovery
- src/adapters
- src/orchestration
- tests
- docs
- config

Nested instructions specialize local work. They may be stricter but may not silently weaken governance or the selected packages.

## Common failure modes

- destructive default mode
- implicit target expansion
- credentials in configuration or logs
- dry-run that still mutates
- no partial-failure report
- unattended execution without owner or stop criteria

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
