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

- [Product Management](../../../disciplines/product-management/)
- [Application Security](../../../disciplines/application-security/)
- [Architecture](../../../disciplines/architecture/)
- [Testing](../../../disciplines/testing/)
- [Api Engineering](../../../disciplines/api-engineering/)
- [Privacy](../../../disciplines/privacy/)
- [Observability](../../../disciplines/observability/)
- [Supply Chain](../../../disciplines/supply-chain/)

## Conditional review

- [User Experience](../../../disciplines/user-experience/)
- [Integration](../../../disciplines/integration/)
- [Documentation](../../../disciplines/documentation/)
- [Sre](../../../disciplines/sre/)
- [Data Engineering](../../../disciplines/data-engineering/)
- [Ci Cd](../../../disciplines/ci-cd/)
- [Release Engineering](../../../disciplines/release-engineering/)

## Project decisions

- product problem, intended users or actors, desired outcomes, requirements, bounded MVP behavior, acceptance criteria, and traceability
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
