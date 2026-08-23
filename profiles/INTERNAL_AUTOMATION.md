---
id: PROFILE-AUTOMATION
title: Internal Automation Project Profile
version: 0.2.0
status: baseline
applies_to:
  - internal-automation
depends_on:
  - GOV-CONTRACT
  - GOV-WORK
  - GOV-RISK
  - GOV-EVIDENCE
---
# Internal Automation Project Profile

## Purpose

Define the minimum standards composition for automation that inspects or changes internal systems, infrastructure, applications, accounts, or data.

## Complete package

Use the complete package at [`internal-automation/`](internal-automation/). This canonical file remains the stable profile entry point.

## Applicability

This profile applies to:

- administrative scripts
- operational workflows
- infrastructure automation
- remediation tools
- scheduled internal jobs
- cross-system orchestration

It normally does not describe:

- public end-user applications
- read-only reporting with no privileged access unless sensitive data is involved
- developer-only local helpers with no shared operational use

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
- `disciplines/testing/AGENTS.md`
- `disciplines/documentation/AGENTS.md`
- `disciplines/observability/AGENTS.md`
- `disciplines/ci-cd/AGENTS.md`
- `disciplines/supply-chain/AGENTS.md`

## Conditionally required disciplines

- [Product Management](../disciplines/product-management/)
- [User Experience](../disciplines/user-experience/)
- `disciplines/architecture/AGENTS.md`
- `disciplines/integration/AGENTS.md`
- `disciplines/release-engineering/AGENTS.md`
- `disciplines/sre/AGENTS.md`
- `disciplines/privacy/AGENTS.md`

Conditional packages become required when their concern is present. Document every omission that would reasonably appear applicable.

Product Management becomes required when the automation defines or materially changes a governed internal product, operator outcome, requirement set, or supported scope. User Experience becomes required for material operator journeys, approvals, prompts, dashboards, or recovery workflows; bounded automation implementing an existing authorized procedure may justify omission.

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

- input and target selection
- credential and identity boundary
- system adapters
- orchestration and checkpoints
- reporting and evidence
- scheduling and operational ownership

## Security and privacy focus

- target allowlists
- least privilege
- credential sources and redaction
- command, path, and query injection prevention
- explicit destructive authorization
- safe temporary files and artifacts

## Testing and validation

- discovery-only behavior
- validation and prerequisite failures
- dry-run fidelity
- idempotency and reruns
- partial failure and compensation
- target identity and allowlist tests

## Operations and release

- audit and report retention
- scheduled execution ownership
- status, progress, and alerting
- resume and recovery
- change windows and stop criteria
- manual intervention and escalation

## Suggested nested instruction scopes

- `src/discovery/AGENTS.md`
- `src/adapters/AGENTS.md`
- `src/orchestration/AGENTS.md`
- `tests/AGENTS.md`
- `docs/AGENTS.md`
- `config/AGENTS.md`

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
