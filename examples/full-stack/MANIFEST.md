---
id: EX-FULL-MAN-001
title: Full-Stack Web Application Composition Example Manifest
version: 0.2.0
status: baseline
---
# Full-Stack Web Application Composition Example Manifest

## Purpose

This manifest defines the complete file inventory and acceptance checks for the **Full-Stack Web Application Composition Example** example.

## Required files

- `AGENTS.md`
- `MANIFEST.md`
- `README.md`
- `composition/STANDARDS_SELECTION.md`
- `composition/TAILORING_DECISIONS.md`
- `deploy/AGENTS.md`
- `docs/ACCESSIBILITY_PLAN.md`
- `docs/AGENTS.md`
- `docs/ARCHITECTURE.md`
- `docs/COMPLETION_EVIDENCE.md`
- `docs/DATA_HANDLING.md`
- `docs/OPERATIONS.md`
- `docs/RELEASE_PLAN.md`
- `docs/RISK_ASSESSMENT.md`
- `docs/TEST_STRATEGY.md`
- `docs/THREAT_MODEL.md`
- `evidence/artifact-record.example.json`
- `evidence/completion-result.example.json`
- `evidence/test-evidence.example.json`
- `project-manifest.json`
- `src/backend/AGENTS.md`
- `src/frontend/AGENTS.md`
- `tests/AGENTS.md`

## Composition

- Explicit governance selection: [Product Inception Lifecycle](../../governance/PRODUCT_INCEPTION_LIFECYCLE.md)
- Profile: `WEB_APPLICATION`
- Languages: `csharp`, `dotnet`, `javascript-typescript`
- Disciplines: `product-management`, `user-experience`, `application-security`, `architecture`, `testing`, `api-engineering`, `database`, `accessibility`, `privacy`, `observability`, `sre`, `documentation`, `ci-cd`, `supply-chain`, `release-engineering`, `integration`
- Platforms: `containers`, `kubernetes`
- Frameworks: `aspnet-core`, `react`
- Risk: `high`

## Acceptance checks

- [ ] Every listed file exists.
- [ ] `project-manifest.json` matches the documented composition.
- [ ] The namespaced governance selection matches `AGENTS.md`, `README.md`, the selection rationale, tailoring decisions, and completion evidence.
- [ ] Root and nested `AGENTS.md` files are consistent.
- [ ] Standards selection explains inclusion and meaningful omission.
- [ ] Tailoring decisions identify fictitious facts, owners, assumptions, and open decisions.
- [ ] Architecture, risk, testing, and operations documents agree.
- [ ] Evidence JSON parses and uses the repository schema shape.
- [ ] No production values, credentials, or sensitive data are present.
- [ ] No unresolved placeholders remain.
- [ ] Relative Markdown links resolve.
- [ ] Repository validation passes.
