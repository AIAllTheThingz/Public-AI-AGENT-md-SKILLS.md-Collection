---
id: PROFILE-SECTOOL
title: Security Tool Project Profile
version: 0.2.0
status: baseline
applies_to:
  - security-tool
depends_on:
  - GOV-CONTRACT
  - GOV-WORK
  - GOV-RISK
  - GOV-EVIDENCE
---
# Security Tool Project Profile

## Purpose

Define the minimum standards composition for tools that inspect security posture, process findings, handle evidence, or perform authorized security-sensitive actions.

## Complete package

Use the complete package at [`security-tool/`](security-tool/). This canonical file remains the stable profile entry point.

## Applicability

This profile applies to:

- security scanners
- configuration assessors
- finding-management tools
- vulnerability utilities
- security automation
- forensic or evidence-processing tools

It normally does not describe:

- general monitoring tools with no security finding or privileged behavior
- malware or offensive tooling outside authorized defensive scope
- policy documents with no software implementation

## Typical starting risk

`high`

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
- `disciplines/privacy/AGENTS.md`
- `disciplines/observability/AGENTS.md`
- `disciplines/documentation/AGENTS.md`
- `disciplines/supply-chain/AGENTS.md`
- `disciplines/release-engineering/AGENTS.md`

## Conditionally required disciplines

- [Product Management](../disciplines/product-management/)
- [User Experience](../disciplines/user-experience/)
- `disciplines/ci-cd/AGENTS.md`
- `disciplines/integration/AGENTS.md`
- `disciplines/sre/AGENTS.md`
- `disciplines/data-engineering/AGENTS.md`
- `disciplines/database/AGENTS.md`

Conditional packages become required when their concern is present. Document every omission that would reasonably appear applicable.

Product Management becomes required when the tool defines or materially changes a product capability, analyst or operator outcome, requirement set, or supported scope. User Experience becomes required for material analyst, operator, remediation, approval, or recovery workflows; a headless scanner implementing an existing governed contract may justify omission.

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

- target and authorization boundary
- collection and analysis
- finding storage and classification
- reporting and disclosure
- optional remediation boundary
- audit and evidence retention

## Security and privacy focus

- strict authorization and scope
- least privilege
- sensitive finding and evidence handling
- safe parsers and file handling
- non-destructive defaults
- secret and credential protection

## Testing and validation

- known-positive and known-negative fixtures
- false-positive and false-negative characterization
- malformed and adversarial input
- privilege and target controls
- safe remediation simulation
- evidence integrity and redaction

## Operations and release

- finding severity and ownership
- confidential disclosure
- retention and deletion
- scanner and rule updates
- audit trails
- support and incident response

## Suggested nested instruction scopes

- `src/collect/AGENTS.md`
- `src/analyze/AGENTS.md`
- `src/report/AGENTS.md`
- `src/remediate/AGENTS.md`
- `tests/AGENTS.md`
- `docs/AGENTS.md`

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
