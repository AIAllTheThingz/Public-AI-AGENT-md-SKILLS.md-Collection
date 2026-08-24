---
id: PROFILE-AI-AGENT-EX-001
title: AI Agent Application Project Profile Adoption Example
version: 0.2.0
status: baseline
---
# AI Agent Application Project Profile Adoption Example

## Fictitious project

This example models a non-production ai agent application.

No production systems, identities, credentials, endpoints, data, or approval are included.

## Profile decision

- Primary profile: [`../../AI_AGENT_APPLICATION.md`](../../AI_AGENT_APPLICATION.md)
- Typical starting risk: `high`
- Actual risk: must be assessed by the adopting project

## Selected disciplines

- [Application Security](../../../disciplines/application-security/)
- [Architecture](../../../disciplines/architecture/)
- [Testing](../../../disciplines/testing/)
- [Api Engineering](../../../disciplines/api-engineering/)
- [Privacy](../../../disciplines/privacy/)
- [Observability](../../../disciplines/observability/)
- [Supply Chain](../../../disciplines/supply-chain/)

## Conditional review

- [Product Management](../../../disciplines/product-management/)
- [User Experience](../../../disciplines/user-experience/)
- [Integration](../../../disciplines/integration/)
- [Documentation](../../../disciplines/documentation/)
- [Sre](../../../disciplines/sre/)
- [Data Engineering](../../../disciplines/data-engineering/)
- [Ci Cd](../../../disciplines/ci-cd/)
- [Release Engineering](../../../disciplines/release-engineering/)

This base-profile example leaves Product Management and User Experience conditional. Promote Product Management for material agent outcomes, requirements, bounded behavior, or product decisions, and User Experience when the changed scope owns human goals, approval, interaction, or recovery.

## Project decisions

- tool authorization and allowlists
- prompt and retrieved-content trust boundaries
- human approval for consequential actions
- identity and credential delegation
- traceable model decisions, outputs, and tool calls
- evaluation for unsafe, incorrect, or deceptive behavior
- data retention and training boundaries
- fallback, stop, and incident behavior

## Suggested scopes

- src/agent
- src/tools
- src/retrieval
- src/policy
- tests
- evals
- docs

## Evidence boundary

The example demonstrates composition only. It does not prove implementation, validation, review, approval, operational verification, or production readiness.
