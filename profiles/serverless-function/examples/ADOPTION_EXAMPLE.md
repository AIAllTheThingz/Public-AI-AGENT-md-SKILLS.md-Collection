---
id: PROFILE-SERVERLESS-EX-001
title: Serverless Function Project Profile Adoption Example
version: 0.2.0
status: baseline
---
# Serverless Function Project Profile Adoption Example

## Fictitious project

This example models a non-production serverless function.

No production systems, identities, credentials, endpoints, data, or approval are included.

## Profile decision

- Primary profile: [`../../SERVERLESS_FUNCTION.md`](../../SERVERLESS_FUNCTION.md)
- Typical starting risk: `moderate`
- Actual risk: must be assessed by the adopting project

## Selected disciplines

- [Application Security](../../../disciplines/application-security/)
- [Testing](../../../disciplines/testing/)
- [Integration](../../../disciplines/integration/)
- [Observability](../../../disciplines/observability/)
- [Ci Cd](../../../disciplines/ci-cd/)
- [Supply Chain](../../../disciplines/supply-chain/)

## Conditional review

- [Product Management](../../../disciplines/product-management/)
- [User Experience](../../../disciplines/user-experience/)
- [Architecture](../../../disciplines/architecture/)
- [Sre](../../../disciplines/sre/)
- [Release Engineering](../../../disciplines/release-engineering/)
- [Privacy](../../../disciplines/privacy/)
- [Data Engineering](../../../disciplines/data-engineering/)

## Project decisions

- event validation and schema
- idempotency and duplicate delivery
- timeout, retry, and dead-letter behavior
- least-privilege execution identity
- concurrency and scaling limits
- cold-start and dependency behavior
- state and external side effects
- deployment, rollback, and observability

## Suggested scopes

- src/function
- src/integrations
- tests
- docs
- infra

## Evidence boundary

The example demonstrates composition only. It does not prove implementation, validation, review, approval, operational verification, or production readiness.
