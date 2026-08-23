---
id: PROFILE-SERVERLESS
title: Serverless Function Project Profile
version: 0.2.0
status: baseline
applies_to:
  - serverless-function
depends_on:
  - GOV-CONTRACT
  - GOV-WORK
  - GOV-RISK
  - GOV-EVIDENCE
---
# Serverless Function Project Profile

## Purpose

Define the minimum standards composition for event-driven functions whose execution, scaling, retries, identity, and lifecycle are controlled by a managed runtime.

## Complete package

Use the complete package at [`serverless-function/`](serverless-function/). This canonical file remains the stable profile entry point.

## Applicability

This profile applies to:

- HTTP-triggered functions
- queue and event consumers
- scheduled functions
- stream processors
- event-driven integration handlers

It normally does not describe:

- long-running worker services
- containerized services with explicit process lifecycle
- client-side functions

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
- `disciplines/testing/AGENTS.md`
- `disciplines/integration/AGENTS.md`
- `disciplines/observability/AGENTS.md`
- `disciplines/ci-cd/AGENTS.md`
- `disciplines/supply-chain/AGENTS.md`

## Conditionally required disciplines

- `disciplines/product-management/AGENTS.md`
- `disciplines/user-experience/AGENTS.md`
- `disciplines/architecture/AGENTS.md`
- `disciplines/sre/AGENTS.md`
- `disciplines/release-engineering/AGENTS.md`
- `disciplines/privacy/AGENTS.md`
- `disciplines/data-engineering/AGENTS.md`

Conditional packages become required when their concern is present. Document every omission that would reasonably appear applicable.

Product Management becomes required when the function defines or materially changes a product capability, actor outcome, requirement set, or supported scope. User Experience becomes required only when this scope owns a human workflow or interface; a bounded event handler implementing an existing governed contract may justify omission.

## Required project decisions

- event validation and schema
- idempotency and duplicate delivery
- timeout, retry, and dead-letter behavior
- least-privilege execution identity
- concurrency and scaling limits
- cold-start and dependency behavior
- state and external side effects
- deployment, rollback, and observability

## Architecture and trust boundaries

- event source and delivery guarantees
- runtime and execution identity
- external dependencies
- state and idempotency store
- network and secret boundaries
- deployment and telemetry

## Security and privacy focus

- event and caller validation
- least-privilege role
- secret injection and rotation
- egress and dependency restrictions
- sensitive payload and logging boundaries
- abuse and cost controls

## Testing and validation

- event schemas and malformed events
- duplicate delivery and retries
- timeout and partial failure
- concurrency and scaling
- dependency outage
- deployment and rollback

## Operations and release

- invocation, error, retry, throttle, and dead-letter signals
- cost and concurrency monitoring
- runbooks for replay and poison events
- runtime and dependency updates
- release and rollback
- ownership of event sources and destinations

## Suggested nested instruction scopes

- `src/function/AGENTS.md`
- `src/integrations/AGENTS.md`
- `tests/AGENTS.md`
- `docs/AGENTS.md`
- `infra/AGENTS.md`

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
