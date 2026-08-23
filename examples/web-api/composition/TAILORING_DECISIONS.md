---
id: EX-API-TAILOR-001
title: Web API Composition Example Tailoring Decisions
version: 0.1.0
status: baseline
---
# Web API Composition Example Tailoring Decisions

## Purpose

This record shows how shared standards are tailored to the fictitious **Web API Composition Example** project.

Tailoring records project facts and stricter requirements. It must not quietly delete inconvenient controls.

## Declared project facts

- Project name: `example-web-api`
- Profile: `WEB_API`
- Risk: `moderate`
- Product Inception Lifecycle: explicitly selected for this fictitious new-product scope
- Production environments: none
- Production access: prohibited
- Data: The fictitious API processes account identifiers and operational metadata. No real personal data, secrets, or internal endpoints are included.
- Owners: fictitious maintainers
- Approval authority: not assigned
- Evidence storage: this example directory
- Exception process: no active exceptions

## Scope

In scope:

- standards composition
- root and nested agent instructions
- architecture and trust-boundary documentation
- risk and test planning
- operations and completion-evidence examples
- schema-shaped JSON evidence

Out of scope:

- deployable application code
- production credentials, endpoints, accounts, clusters, databases, or users
- legal, regulatory, contractual, or compliance approval
- production performance, availability, recovery, or incident evidence
- real artifact publication

## Tailored requirements

- All example values must be fictitious.
- No state-changing production operation is permitted.
- Example evidence must be clearly illustrative.
- `not-run` must be used when a validation was not executed.
- Root and nested instructions must remain consistent.
- Any real adoption must replace project facts and evidence.
- The example must pass repository structure and link validation.
- Lifecycle selection must not be represented as a gate pass; each gate remains blocked until its required evidence receives accountable review.

## Conditionally applicable controls

Controls tied to real deployment, identity, data classification, recovery, performance, or external systems remain illustrative until an adopting project supplies reviewed facts.

## Inapplicable controls

No control is marked permanently inapplicable. Controls omitted from the manifest are omitted only for the current example shape and must be reconsidered when scope changes.

## Open decisions

- Exact runtime patch versions
- Hosting and deployment environment
- Identity and secret providers
- Data-store technology
- Monitoring backend
- Release and approval workflow
- Support ownership
- Recovery objectives
- Compliance obligations
- Product Inception Lifecycle gate evidence and accountable decision authority

## Exceptions

None.

## Review and expiration

This tailoring record must be reviewed when the example's manifest, architecture, risk, or directory structure changes.
