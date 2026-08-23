---
id: PROFILE-DESKTOP
title: Desktop Application Project Profile
version: 0.2.0
status: baseline
applies_to:
  - desktop-application
depends_on:
  - GOV-CONTRACT
  - GOV-WORK
  - GOV-RISK
  - GOV-EVIDENCE
---
# Desktop Application Project Profile

## Purpose

Define the minimum standards composition for installed desktop applications that execute on user-managed endpoints and may store data, integrate with the operating system, or update independently.

## Complete package

Use the complete package at [`desktop-application/`](desktop-application/). This canonical file remains the stable profile entry point.

## Applicability

This profile applies to:

- native desktop applications
- cross-platform desktop applications
- administrative consoles
- endpoint utilities with graphical interfaces

It normally does not describe:

- browser-only applications
- mobile applications
- headless command-line tools

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
- `disciplines/documentation/AGENTS.md`
- `disciplines/release-engineering/AGENTS.md`

## Conditionally required disciplines

- [Product Management](../disciplines/product-management/)
- [User Experience](../disciplines/user-experience/)
- `disciplines/supply-chain/AGENTS.md`
- `disciplines/ci-cd/AGENTS.md`
- `disciplines/observability/AGENTS.md`
- `disciplines/integration/AGENTS.md`
- `disciplines/database/AGENTS.md`

Conditional packages become required when their concern is present. Document every omission that would reasonably appear applicable.

Product Management becomes required when the application defines or materially changes a product capability, intended outcome, requirement set, MVP boundary, or acceptance criteria. User Experience becomes required when the scope defines or materially changes user journeys, tasks, interaction or recovery states, or UX-validation claims. Record each applicability decision; profile selection alone does not make either discipline mandatory.

## Required project decisions

- local data protection
- installer and update integrity
- privilege and elevation boundaries
- secure storage and credential integration
- accessibility and keyboard behavior
- offline and degraded operation
- telemetry and privacy
- supported operating systems and migration

## Architecture and trust boundaries

- user interface and process boundaries
- local storage
- OS integration and privileged helpers
- remote services and update channels
- plugin or extension boundaries
- installer and recovery model

## Security and privacy focus

- least privilege and elevation
- secure local storage
- signed packages and updates
- safe IPC, file, URI, and protocol handling
- secret exclusion from logs and crash reports
- tamper and rollback considerations

## Testing and validation

- supported OS coverage
- installation, upgrade, repair, and uninstall
- accessibility and keyboard behavior
- offline and network failure
- privilege boundaries
- data migration and recovery

## Operations and release

- crash and diagnostic collection
- update rollout and rollback
- support bundles and redaction
- version and compatibility support
- local data recovery
- release and end-of-support communication

## Suggested nested instruction scopes

- `src/ui/AGENTS.md`
- `src/core/AGENTS.md`
- `src/platform/AGENTS.md`
- `tests/AGENTS.md`
- `docs/AGENTS.md`
- `installer/AGENTS.md`

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
