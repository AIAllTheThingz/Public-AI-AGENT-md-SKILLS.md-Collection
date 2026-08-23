---
id: PROFILE-WEB-API-EX-001
title: Web API Project Profile Adoption Example
version: 0.2.0
status: baseline
---
# Web API Project Profile Adoption Example

## Fictitious project

This example models a non-production web api.

No production systems, identities, credentials, endpoints, data, or approval are included.

## Profile decision

- Primary profile: [`../../WEB_API.md`](../../WEB_API.md)
- Typical starting risk: `moderate`
- Actual risk: must be assessed by the adopting project

## Selected disciplines

- [Application Security](../../../disciplines/application-security/)
- [Architecture](../../../disciplines/architecture/)
- [Testing](../../../disciplines/testing/)
- [Api Engineering](../../../disciplines/api-engineering/)
- [Privacy](../../../disciplines/privacy/)
- [Observability](../../../disciplines/observability/)
- [Ci Cd](../../../disciplines/ci-cd/)
- [Supply Chain](../../../disciplines/supply-chain/)
- [Release Engineering](../../../disciplines/release-engineering/)

## Conditional review

- [Product Management](../../../disciplines/product-management/)
- [User Experience](../../../disciplines/user-experience/)
- [Database](../../../disciplines/database/)
- [Integration](../../../disciplines/integration/)
- [Sre](../../../disciplines/sre/)
- [Documentation](../../../disciplines/documentation/)
- [Data Engineering](../../../disciplines/data-engineering/)

## Project decisions

- authentication and authorization model
- request and response contract
- versioning and compatibility policy
- validation, size, pagination, and rate limits
- idempotency and retry semantics
- error contract and diagnostic boundary
- data classification and retention
- health, telemetry, deployment, rollback, and ownership

## Suggested scopes

- src/api
- src/domain
- src/infrastructure
- tests
- docs
- deploy

## Evidence boundary

The example demonstrates composition only. It does not prove implementation, validation, review, approval, operational verification, or production readiness.
