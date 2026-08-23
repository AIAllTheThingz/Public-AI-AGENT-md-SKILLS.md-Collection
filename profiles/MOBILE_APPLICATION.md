---
id: PROFILE-MOBILE
title: Mobile Application Project Profile
version: 0.2.0
status: baseline
applies_to:
  - mobile-application
depends_on:
  - GOV-CONTRACT
  - GOV-WORK
  - GOV-RISK
  - GOV-EVIDENCE
---
# Mobile Application Project Profile

## Purpose

Define the minimum standards composition for mobile applications distributed through device ecosystems with constrained permissions, intermittent connectivity, local storage, and upgrade behavior.

## Complete package

Use the complete package at [`mobile-application/`](mobile-application/). This canonical file remains the stable profile entry point.

## Applicability

This profile applies to:

- native mobile applications
- cross-platform mobile applications
- tablet applications
- mobile clients for backend services

It normally does not describe:

- responsive browser applications
- desktop applications
- embedded firmware

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

- `disciplines/application-security/AGENTS.md`
- `disciplines/architecture/AGENTS.md`
- `disciplines/testing/AGENTS.md`
- `disciplines/accessibility/AGENTS.md`
- `disciplines/privacy/AGENTS.md`
- `disciplines/supply-chain/AGENTS.md`
- `disciplines/release-engineering/AGENTS.md`

## Conditionally required disciplines

- [Product Management](../disciplines/product-management/)
- [User Experience](../disciplines/user-experience/)
- `disciplines/observability/AGENTS.md`
- `disciplines/ci-cd/AGENTS.md`
- `disciplines/api-engineering/AGENTS.md`
- `disciplines/integration/AGENTS.md`
- `disciplines/documentation/AGENTS.md`

Conditional packages become required when their concern is present. Document every omission that would reasonably appear applicable.

Product Management becomes required when the application defines or materially changes a product capability, intended outcome, requirement set, MVP boundary, or acceptance criteria. User Experience becomes required when the scope defines or materially changes user journeys, tasks, interaction or recovery states, or UX-validation claims. Record each applicability decision; profile selection alone does not make either discipline mandatory.

## Required project decisions

- secure storage
- network trust and certificate behavior
- permission minimization
- offline and synchronization behavior
- biometric and device-authentication integration
- analytics, crash reporting, and privacy
- app-store signing and release
- minimum supported OS and upgrade path

## Architecture and trust boundaries

- device and backend trust boundaries
- local state and cache
- secure storage
- permissions and platform services
- offline synchronization
- distribution and update channels

## Security and privacy focus

- least permissions
- secure credential and token storage
- TLS and certificate handling
- deep-link and intent validation
- sensitive screen and clipboard behavior
- privacy-safe telemetry

## Testing and validation

- supported device and OS matrix
- permission-denied behavior
- offline and poor-network conditions
- upgrade and data migration
- accessibility and orientation
- backend compatibility and release rollout

## Operations and release

- crash and performance monitoring
- staged store rollout
- backward compatibility
- remote feature and kill controls where appropriate
- support and data-deletion workflows
- signing and release ownership

## Suggested nested instruction scopes

- `src/ui/AGENTS.md`
- `src/domain/AGENTS.md`
- `src/platform/AGENTS.md`
- `tests/AGENTS.md`
- `docs/AGENTS.md`
- `release/AGENTS.md`

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
