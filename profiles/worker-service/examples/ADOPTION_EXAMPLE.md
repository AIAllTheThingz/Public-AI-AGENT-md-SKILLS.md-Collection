---
id: PROFILE-WORKER-EX-001
title: Worker Service Project Profile Adoption Example
version: 0.2.0
status: baseline
---
# Worker Service Project Profile Adoption Example

## Fictitious project

This example models a non-production worker service.

No production systems, identities, credentials, endpoints, data, or approval are included.

## Profile decision

- Primary profile: [`../../WORKER_SERVICE.md`](../../WORKER_SERVICE.md)
- Typical starting risk: `moderate`
- Actual risk: must be assessed by the adopting project

## Selected disciplines

- [Architecture](../../../disciplines/architecture/)
- [Testing](../../../disciplines/testing/)
- [Integration](../../../disciplines/integration/)
- [Observability](../../../disciplines/observability/)
- [Sre](../../../disciplines/sre/)
- [Ci Cd](../../../disciplines/ci-cd/)
- [Supply Chain](../../../disciplines/supply-chain/)
- [Release Engineering](../../../disciplines/release-engineering/)

## Conditional review

- [Product Management](../../../disciplines/product-management/)
- [User Experience](../../../disciplines/user-experience/)
- [Application Security](../../../disciplines/application-security/)
- [Database](../../../disciplines/database/)
- [Data Engineering](../../../disciplines/data-engineering/)
- [Privacy](../../../disciplines/privacy/)
- [Documentation](../../../disciplines/documentation/)

## Project decisions

- idempotency and replay behavior
- concurrency and ordering
- cancellation and graceful shutdown
- retry, backoff, poison-message, and dead-letter behavior
- checkpoint and state ownership
- dependency failure and partial success
- health and readiness
- operational ownership, scaling, and recovery

## Suggested scopes

- src/worker
- src/integrations
- src/storage
- tests
- docs
- deploy

## Evidence boundary

The example demonstrates composition only. It does not prove implementation, validation, review, approval, operational verification, or production readiness.
