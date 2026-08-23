---
id: PROFILE-WEB-API
title: Web API Project Profile
version: 0.2.0
status: baseline
applies_to:
  - web-api
depends_on:
  - GOV-CONTRACT
  - GOV-WORK
  - GOV-RISK
  - GOV-EVIDENCE
---
# Web API Project Profile

## Purpose

Define the minimum standards composition for HTTP, RPC, event-facing, or other programmatic service interfaces that expose business or operational capabilities.

## Complete package

Use the complete package at [`web-api/`](web-api/). This canonical file remains the stable profile entry point.

## Applicability

This profile applies to:

- public and internal HTTP APIs
- RPC or service interfaces
- backend-for-frontend services
- webhook receivers and callback endpoints
- API gateways when application behavior is implemented in the repository

It normally does not describe:

- a public library with no deployed service boundary
- static documentation or content-only sites
- a worker with no externally callable interface

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
- `disciplines/api-engineering/AGENTS.md`
- `disciplines/privacy/AGENTS.md`
- `disciplines/observability/AGENTS.md`
- `disciplines/ci-cd/AGENTS.md`
- `disciplines/supply-chain/AGENTS.md`
- `disciplines/release-engineering/AGENTS.md`

## Conditionally required disciplines

- `disciplines/product-management/AGENTS.md`
- `disciplines/user-experience/AGENTS.md`
- `disciplines/database/AGENTS.md`
- `disciplines/integration/AGENTS.md`
- `disciplines/sre/AGENTS.md`
- `disciplines/documentation/AGENTS.md`
- `disciplines/data-engineering/AGENTS.md`

Conditional packages become required when their concern is present. Document every omission that would reasonably appear applicable.

Product Management becomes required when the API defines or materially changes a product capability, user or actor outcome, requirement set, or MVP boundary. User Experience becomes required when human consumers pursue governed goals through developer portals, consoles, interactive workflows, or other interfaces; ordinary maintenance against existing approved requirements does not force either discipline.

## Required project decisions

- authentication and authorization model
- request and response contract
- versioning and compatibility policy
- validation, size, pagination, and rate limits
- idempotency and retry semantics
- error contract and diagnostic boundary
- data classification and retention
- health, telemetry, deployment, rollback, and ownership

## Architecture and trust boundaries

- client and caller boundaries
- routing and endpoint ownership
- business-service boundaries
- data stores and external dependencies
- identity provider and authorization boundary
- deployment and observability boundaries

## Security and privacy focus

- server-side authorization for every protected operation
- input validation at the trust boundary
- safe serialization and error behavior
- abuse, rate, resource, and automation controls
- secret and credential handling
- privacy and logging boundaries

## Testing and validation

- contract and compatibility tests
- positive and negative authorization tests
- validation and boundary tests
- integration and dependency-failure tests
- idempotency, retry, timeout, and cancellation tests
- deployment and health validation

## Operations and release

- versioned deployment and rollback
- health, metrics, logs, traces, and correlation
- rate-limit and abuse monitoring
- dependency and quota ownership
- runbooks and escalation
- release notes and migration guidance

## Suggested nested instruction scopes

- `src/api/AGENTS.md`
- `src/domain/AGENTS.md`
- `src/infrastructure/AGENTS.md`
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
