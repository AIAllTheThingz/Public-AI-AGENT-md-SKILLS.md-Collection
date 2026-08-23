---
id: PROFILE-LIB
title: Public Library Project Profile
version: 0.2.0
status: baseline
applies_to:
  - public-library
depends_on:
  - GOV-CONTRACT
  - GOV-WORK
  - GOV-RISK
  - GOV-EVIDENCE
---
# Public Library Project Profile

## Purpose

Define the minimum standards composition for libraries, SDKs, packages, and reusable components consumed outside the repository's direct control.

## Complete package

Use the complete package at [`public-library/`](public-library/). This canonical file remains the stable profile entry point.

## Applicability

This profile applies to:

- public packages
- internal shared libraries with compatibility commitments
- SDKs
- plugins and extension libraries
- reusable modules published to registries

It normally does not describe:

- private application code with no consumer contract
- single-repository implementation details
- deployment-only configuration

## Typical starting risk

`moderate`

This is a starting point only. The actual project or change must be classified under governance.

## Required governance

- `governance/ORGANIZATION_CONTRACT.md`
- `governance/AGENT_WORKING_METHOD.md`
- `governance/RISK_CLASSIFICATION.md`
- `governance/COMPLETION_EVIDENCE.md`
- `governance/HUMAN_REVIEW_POLICY.md`
- `governance/PRODUCTION_READINESS.md` when deployed or operated

## Required discipline overlays

- `disciplines/product-management/AGENTS.md`
- `disciplines/architecture/AGENTS.md`
- `disciplines/testing/AGENTS.md`
- `disciplines/documentation/AGENTS.md`
- `disciplines/supply-chain/AGENTS.md`
- `disciplines/release-engineering/AGENTS.md`

## Conditionally required disciplines

- `disciplines/user-experience/AGENTS.md`
- `disciplines/application-security/AGENTS.md`
- `disciplines/api-engineering/AGENTS.md`
- `disciplines/ci-cd/AGENTS.md`
- `disciplines/accessibility/AGENTS.md`
- `disciplines/privacy/AGENTS.md`

Conditional packages become required when their concern is present. Document every omission that would reasonably appear applicable.

User Experience becomes required when consumers pursue material goals through interactive documentation, tooling, samples, or other governed workflows; API and documentation review alone must not be presented as observed UX evidence.

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

- public API surface
- internal implementation boundary
- dependency and extension points
- serialization and compatibility
- build and package artifacts
- consumer documentation and migration

## Security and privacy focus

- safe defaults
- input and data handling
- dependency and provenance review
- secret-free examples
- security advisory process
- unsupported-version handling

## Testing and validation

- public contract tests
- compatibility matrix
- consumer integration tests
- packaging and installation
- documentation examples
- performance and concurrency where promised

## Operations and release

- release notes and changelog
- package registry ownership
- deprecation communication
- vulnerability response
- support policy
- artifact provenance and retention

## Suggested nested instruction scopes

- `src/public/AGENTS.md`
- `src/internal/AGENTS.md`
- `tests/AGENTS.md`
- `docs/AGENTS.md`
- `packaging/AGENTS.md`
- `examples/AGENTS.md`

## Completion evidence

Record:

- profile selection rationale
- risk classification
- required and conditional package decisions
- architecture and trust boundaries
- project decisions
- validation commands and outcomes
- checks not run
- operational and production-readiness status
- limitations and residual risk
- accountable reviewers and approvers

## Completion gate

The project must satisfy applicable governance, language, discipline, framework, platform, virtualization, operating-system, networking, and profile standards. Document exclusions, exceptions, and unvalidated behavior.

Selecting this profile does not prove the project is secure, tested, accessible, private, reliable, compatible, supportable, or production-ready.
