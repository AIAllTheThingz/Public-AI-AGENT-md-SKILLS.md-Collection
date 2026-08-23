---
id: PROFILE-SAAS
title: Multi-Tenant SaaS Project Profile
version: 0.2.0
status: baseline
applies_to:
  - multi-tenant-saas
depends_on:
  - GOV-CONTRACT
  - GOV-WORK
  - GOV-RISK
  - GOV-EVIDENCE
---
# Multi-Tenant SaaS Project Profile

## Purpose

Define the minimum standards composition for hosted software serving multiple tenants with isolation, authorization, data lifecycle, quota, billing, and operational obligations.

## Complete package

Use the complete package at [`multi-tenant-saas/`](multi-tenant-saas/). This canonical file remains the stable profile entry point.

## Applicability

This profile applies to:

- shared-application multi-tenant SaaS
- shared-database or isolated-database tenant models
- tenant-aware APIs and web applications
- hosted platforms with tenant administration

It normally does not describe:

- single-tenant internal applications
- public libraries
- consumer applications without tenant boundaries

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
- `disciplines/api-engineering/AGENTS.md`
- `disciplines/database/AGENTS.md`
- `disciplines/privacy/AGENTS.md`
- `disciplines/observability/AGENTS.md`
- `disciplines/sre/AGENTS.md`
- `disciplines/ci-cd/AGENTS.md`
- `disciplines/supply-chain/AGENTS.md`
- `disciplines/release-engineering/AGENTS.md`

## Conditionally required disciplines

- [Product Management](../disciplines/product-management/)
- [User Experience](../disciplines/user-experience/)
- `disciplines/integration/AGENTS.md`
- `disciplines/data-engineering/AGENTS.md`
- `disciplines/accessibility/AGENTS.md`
- `disciplines/documentation/AGENTS.md`

Conditional packages become required when their concern is present. Document every omission that would reasonably appear applicable.

Product Management becomes required when the SaaS scope defines or materially changes a tenant or user outcome, requirement set, MVP boundary, acceptance criteria, or product decision. User Experience becomes required when tenants, end users, administrators, or support operators interact with a materially changed workflow or interface. API-only SaaS may justify UX omission, but must not infer UX validation from API testing. Profile selection alone does not make either discipline mandatory.

## Required project decisions

- tenant identity and isolation model
- authorization at every object boundary
- data partitioning and lifecycle
- tenant export and deletion
- noisy-neighbor and quota controls
- tenant-aware telemetry and support
- billing and entitlement boundaries
- migration, rollout, and recovery by tenant

## Architecture and trust boundaries

- tenant resolution
- authorization and policy enforcement
- data partitioning
- shared and tenant-specific services
- administration and support
- billing, telemetry, and deployment boundaries

## Security and privacy focus

- cross-tenant access prevention
- object-level authorization
- tenant-scoped keys and secrets where applicable
- support and impersonation controls
- safe tenant identifiers in logs
- abuse and quota controls

## Testing and validation

- cross-tenant negative tests
- tenant provisioning and deletion
- schema and migration by tenant
- quota and noisy-neighbor behavior
- support and admin access
- backup, restore, and export isolation

## Operations and release

- tenant-aware health and telemetry
- incident scoping and communication
- per-tenant rollout and rollback
- capacity and cost allocation
- data lifecycle operations
- support and escalation

## Suggested nested instruction scopes

- `src/tenant/AGENTS.md`
- `src/api/AGENTS.md`
- `src/data/AGENTS.md`
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
