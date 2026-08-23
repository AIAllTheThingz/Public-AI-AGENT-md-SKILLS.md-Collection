---
id: PROFILE-WORKER
title: Worker Service Project Profile
version: 0.2.0
status: baseline
applies_to:
  - worker-service
depends_on:
  - GOV-CONTRACT
  - GOV-WORK
  - GOV-RISK
  - GOV-EVIDENCE
---
# Worker Service Project Profile

## Purpose

Define the minimum standards composition for long-running or scheduled background processes that consume work, coordinate dependencies, and operate without an interactive user request.

## Complete package

Use the complete package at [`worker-service/`](worker-service/). This canonical file remains the stable profile entry point.

## Applicability

This profile applies to:

- message consumers
- queue workers
- scheduled services
- background processors
- batch coordinators and durable jobs

It normally does not describe:

- single-use administrative scripts
- interactive command-line tools
- request-only web APIs without background work

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

- `disciplines/architecture/AGENTS.md`
- `disciplines/testing/AGENTS.md`
- `disciplines/integration/AGENTS.md`
- `disciplines/observability/AGENTS.md`
- `disciplines/sre/AGENTS.md`
- `disciplines/ci-cd/AGENTS.md`
- `disciplines/supply-chain/AGENTS.md`
- `disciplines/release-engineering/AGENTS.md`

## Conditionally required disciplines

- [Product Management](../disciplines/product-management/)
- [User Experience](../disciplines/user-experience/)
- `disciplines/application-security/AGENTS.md`
- `disciplines/database/AGENTS.md`
- `disciplines/data-engineering/AGENTS.md`
- `disciplines/privacy/AGENTS.md`
- `disciplines/documentation/AGENTS.md`

Conditional packages become required when their concern is present. Document every omission that would reasonably appear applicable.

Product Management becomes required when the worker defines or materially changes a product capability, user or operator outcome, requirement set, or MVP boundary. User Experience becomes required only when a human-facing operational or product workflow is part of this scope; a headless worker maintaining an existing governed contract may justify omission.

## Required project decisions

- idempotency and replay behavior
- concurrency and ordering
- cancellation and graceful shutdown
- retry, backoff, poison-message, and dead-letter behavior
- checkpoint and state ownership
- dependency failure and partial success
- health and readiness
- operational ownership, scaling, and recovery

## Architecture and trust boundaries

- work source and delivery semantics
- worker ownership and concurrency model
- external dependency boundaries
- state, checkpoint, and deduplication stores
- deployment and scaling model
- telemetry and operational control plane

## Security and privacy focus

- work-item validation
- least-privilege workload identity
- secret handling
- sensitive payload and log boundaries
- authorization for consequential actions
- resource exhaustion and abuse controls

## Testing and validation

- idempotency and duplicate delivery
- reordering and concurrency
- retry and dead-letter paths
- cancellation and shutdown
- dependency outages and timeouts
- scaling, recovery, and operational checks

## Operations and release

- lag, throughput, error, retry, and dead-letter metrics
- health and readiness semantics
- capacity and backpressure
- runbooks and replay procedures
- deployment drain and rollback
- incident ownership and recovery

## Suggested nested instruction scopes

- `src/worker/AGENTS.md`
- `src/integrations/AGENTS.md`
- `src/storage/AGENTS.md`
- `tests/AGENTS.md`
- `docs/AGENTS.md`
- `deploy/AGENTS.md`

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
