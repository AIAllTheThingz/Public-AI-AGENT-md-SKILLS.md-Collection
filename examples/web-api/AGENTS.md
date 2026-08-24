---
id: EX-API-AGENT-001
title: Web API Composition Example Root Agent Instructions
version: 0.2.0
status: baseline
---
# Web API Composition Example Root Agent Instructions

## Purpose

These are the root agent instructions for the fictitious **Web API Composition Example** composition.

The example demonstrates how shared standards are tailored into project instructions. It does not authorize production work and contains no executable application.

## Instruction precedence

When instructions conflict, apply them in this order:

1. Explicit user requirements
2. The nearest more-specific `AGENTS.md`
3. This root example `AGENTS.md`
4. Referenced governance, profile, language, discipline, framework, platform, virtualization, operating-system, and networking standards
5. Repository conventions
6. General agent preferences

Report material conflicts instead of silently choosing the convenient interpretation.

## Project facts

- Profile: `WEB_API`
- Risk: `moderate`
- Data: The fictitious API processes account identifiers and operational metadata. No real personal data, secrets, or internal endpoints are included.
- Environments: fictitious local and CI environments only
- Production access: prohibited
- Credentials: prohibited
- Destructive operations: prohibited
- Completion claims: evidence-based only

## Selected standards

### Governance

- [Governance index](../../governance/README.md)
- [Organization Contract](../../governance/ORGANIZATION_CONTRACT.md)
- [Agent Working Method](../../governance/AGENT_WORKING_METHOD.md)
- [Risk Classification](../../governance/RISK_CLASSIFICATION.md)
- [Completion Evidence](../../governance/COMPLETION_EVIDENCE.md)
- [Human Review Policy](../../governance/HUMAN_REVIEW_POLICY.md)
- Explicitly selected for this fictitious new-product scope: [Product Inception Lifecycle](../../governance/PRODUCT_INCEPTION_LIFECYCLE.md)

### Profile

- [WEB_API](../../profiles/WEB_API.md)

### Languages

- [`csharp`](../../languages/csharp/)
- [`dotnet`](../../languages/dotnet/)

### Disciplines

- [`product-management`](../../disciplines/product-management/)
- [`application-security`](../../disciplines/application-security/)
- [`architecture`](../../disciplines/architecture/)
- [`testing`](../../disciplines/testing/)
- [`api-engineering`](../../disciplines/api-engineering/)
- [`privacy`](../../disciplines/privacy/)
- [`observability`](../../disciplines/observability/)
- [`ci-cd`](../../disciplines/ci-cd/)
- [`supply-chain`](../../disciplines/supply-chain/)
- [`documentation`](../../disciplines/documentation/)
- [`release-engineering`](../../disciplines/release-engineering/)

### Platforms

- [`containers`](../../platforms/containers/)

### Frameworks

- [`aspnet-core`](../../frameworks/aspnet-core/)

## Mandatory behavior

- Inspect the current example, selected standards, and nested instructions before editing.
- Make the smallest coherent change.
- Keep every value fictitious and obviously non-production.
- Do not add credentials, tokens, internal endpoints, personal data, or sensitive identifiers.
- Do not claim that example commands were run unless they were actually run.
- Preserve public contracts represented by manifests and documentation unless change is intentional.
- Validate external input and trust-boundary data in any illustrative design.
- Preserve cancellation, idempotency, rollback, cleanup, and safe-failure expectations where applicable.
- Update tests and documentation with behavior changes.
- Keep telemetry free of secrets and unnecessarily sensitive data.
- Record checks not run and limitations.
- Stop when prerequisites or target identity are ambiguous.

## Required working method

1. Discover the affected scope and inherited instructions.
2. Classify the change and risk.
3. Define acceptance criteria and required evidence.
4. Update the smallest set of files.
5. Keep manifests, README, architecture, tailoring, and evidence synchronized.
6. Add or update negative and failure-path test expectations.
7. Run repository validation and link checking.
8. Review the diff for unrelated changes, unresolved placeholders, false claims, and production values.
9. Report exact evidence and limitations.

## Scope rules

- `composition/` explains selection and tailoring.
- `docs/` contains architecture, risk, test, operations, and completion material.
- `evidence/` contains schema-shaped example evidence.
- Nested implementation, test, deployment, and documentation directories add stricter local instructions.

Do not introduce application source code merely to make the example look busy.

## Completion gate

Work is incomplete until:

- the README and manifest describe the actual file set
- project-manifest selections match the narrative
- nested instructions are consistent
- evidence files parse
- relative links resolve
- repository validation passes
- limitations and checks not run are stated
- no unresolved placeholders or real production values remain
