---
id: PROFILE-CLI
title: Command-Line Tool Project Profile
version: 0.2.0
status: baseline
applies_to:
  - cli-tool
depends_on:
  - GOV-CONTRACT
  - GOV-WORK
  - GOV-RISK
  - GOV-EVIDENCE
---
# Command-Line Tool Project Profile

## Purpose

Define the minimum standards composition for command-line tools used by humans or automation, including safe input, output, exit codes, configuration, and state-changing behavior.

## Complete package

Use the complete package at [`cli-tool/`](cli-tool/). This canonical file remains the stable profile entry point.

## Applicability

This profile applies to:

- administrative CLIs
- developer tools
- data-processing commands
- automation entry points
- local and remote operational utilities

It normally does not describe:

- embedded libraries with no command interface
- graphical desktop applications
- long-running background services

## Typical starting risk

`low`

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
- `disciplines/supply-chain/AGENTS.md`
- `disciplines/release-engineering/AGENTS.md`

## Conditionally required disciplines

- [Product Management](../disciplines/product-management/)
- [User Experience](../disciplines/user-experience/)
- `disciplines/architecture/AGENTS.md`
- `disciplines/integration/AGENTS.md`
- `disciplines/observability/AGENTS.md`
- `disciplines/ci-cd/AGENTS.md`
- `disciplines/privacy/AGENTS.md`

Conditional packages become required when their concern is present. Document every omission that would reasonably appear applicable.

Product Management becomes required when the CLI defines or materially changes a product capability, user outcome, requirement set, or supported scope. User Experience becomes required for material human task flows, prompts, interaction, error recovery, or usability validation; an automation-only interface maintaining an existing governed contract may justify omission.

## Required project decisions

- safe defaults and read-only behavior
- confirmation and simulation for destructive actions
- human-readable and machine-readable output
- exit-code contract
- configuration and credential sources
- local and remote target identity
- idempotency, rollback, and cleanup
- packaging, signing, and update model

## Architecture and trust boundaries

- command parsing and dispatch
- domain operations
- external adapters
- configuration and credential boundaries
- output and reporting
- packaging and distribution

## Security and privacy focus

- argument and path validation
- command and query injection prevention
- credential exposure prevention
- target confirmation
- least privilege
- safe temporary files and cleanup

## Testing and validation

- parser and validation tests
- exit codes and output formats
- dry-run and confirmation
- failure and cleanup paths
- cross-platform behavior where claimed
- packaging and installation

## Operations and release

- structured logs or diagnostics where appropriate
- supportable error messages
- version reporting
- rollback and recovery for modifying operations
- audit records for consequential work
- release and deprecation guidance

## Suggested nested instruction scopes

- `src/AGENTS.md`
- `tests/AGENTS.md`
- `docs/AGENTS.md`
- `packaging/AGENTS.md`
- `scripts/AGENTS.md`

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
