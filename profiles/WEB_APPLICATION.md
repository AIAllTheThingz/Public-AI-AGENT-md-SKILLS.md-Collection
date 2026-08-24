---
id: PROFILE-WEB-APP
title: Web Application Project Profile
version: 0.2.0
status: baseline
applies_to:
  - web-application
depends_on:
  - GOV-CONTRACT
  - GOV-WORK
  - GOV-RISK
  - GOV-EVIDENCE
---
# Web Application Project Profile

## Purpose

Define the minimum standards composition for browser-delivered applications with interactive user experiences, client and server trust boundaries, and accessibility obligations.

## Complete package

Use the complete package at [`web-application/`](web-application/). This canonical file remains the stable profile entry point.

## Applicability

This profile applies to:

- single-page applications
- server-rendered web applications
- progressive web applications
- browser-based administrative tools
- full-stack web applications

It normally does not describe:

- content-only static pages with no application behavior
- native desktop or mobile applications
- backend services with no browser interface

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
- `disciplines/observability/AGENTS.md`
- `disciplines/ci-cd/AGENTS.md`
- `disciplines/supply-chain/AGENTS.md`
- `disciplines/release-engineering/AGENTS.md`

## Conditionally required disciplines

- [Product Management](../disciplines/product-management/)
- [User Experience](../disciplines/user-experience/)
- `disciplines/api-engineering/AGENTS.md`
- `disciplines/database/AGENTS.md`
- `disciplines/integration/AGENTS.md`
- `disciplines/sre/AGENTS.md`
- `disciplines/documentation/AGENTS.md`

Conditional packages become required when their concern is present. Document every omission that would reasonably appear applicable.

Product Management becomes required when the application defines or materially changes a product capability, intended outcome, requirement set, MVP boundary, or acceptance criteria. User Experience becomes required when the scope defines or materially changes user journeys, tasks, interaction or recovery states, or UX-validation claims. Record each applicability decision; profile selection alone does not make either discipline mandatory.

## Required project decisions

- server-side authorization model
- client and server trust boundaries
- WCAG 2.2 AA or stricter accessibility target
- content security and safe rendering
- browser support and assistive-technology coverage
- session and state management
- privacy, analytics, and consent behavior
- deployment, rollback, caching, and asset compatibility

## Architecture and trust boundaries

- browser and server boundaries
- frontend state and routing
- API and identity integration
- content delivery and caching
- data stores and third-party scripts
- deployment and observability boundaries

## Security and privacy focus

- server-side authorization
- XSS and unsafe HTML controls
- CSRF or antiforgery where applicable
- content security policy and third-party script governance
- secret exclusion from client bundles
- privacy-safe analytics and diagnostics

## Testing and validation

- keyboard and focus testing
- screen-reader and semantic review
- unit and component tests
- browser integration and end-to-end tests
- negative authorization and security tests
- asset, cache, deployment, and rollback checks

## Operations and release

- client error and performance telemetry
- release compatibility across cached assets
- feature-flag and rollback behavior
- accessibility regression handling
- browser support ownership
- incident and support runbooks

## Suggested nested instruction scopes

- `src/frontend/AGENTS.md`
- `src/backend/AGENTS.md`
- `tests/AGENTS.md`
- `docs/AGENTS.md`
- `public/AGENTS.md`
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
