---
id: PROFILE-DATA-PIPELINE-EX-001
title: Data Pipeline Project Profile Adoption Example
version: 0.2.0
status: baseline
---
# Data Pipeline Project Profile Adoption Example

## Fictitious project

This example models a non-production data pipeline.

No production systems, identities, credentials, endpoints, data, or approval are included.

## Profile decision

- Primary profile: [`../../DATA_PIPELINE.md`](../../DATA_PIPELINE.md)
- Typical starting risk: `high`
- Actual risk: must be assessed by the adopting project

## Selected disciplines

- [Architecture](../../../disciplines/architecture/)
- [Testing](../../../disciplines/testing/)
- [Integration](../../../disciplines/integration/)
- [Database](../../../disciplines/database/)
- [Data Engineering](../../../disciplines/data-engineering/)
- [Privacy](../../../disciplines/privacy/)
- [Observability](../../../disciplines/observability/)
- [Sre](../../../disciplines/sre/)

## Conditional review

- [Product Management](../../../disciplines/product-management/)
- [User Experience](../../../disciplines/user-experience/)
- [Application Security](../../../disciplines/application-security/)
- [Ci Cd](../../../disciplines/ci-cd/)
- [Supply Chain](../../../disciplines/supply-chain/)
- [Release Engineering](../../../disciplines/release-engineering/)
- [Documentation](../../../disciplines/documentation/)

## Project decisions

- data contracts and ownership
- lineage and metadata
- replay and backfill behavior
- quality gates
- retention and sensitive-data handling
- schema compatibility
- late, duplicate, and out-of-order data
- recovery, cost, and operational ownership

## Suggested scopes

- src/ingest
- src/transform
- src/publish
- tests
- docs
- orchestration

## Evidence boundary

The example demonstrates composition only. It does not prove implementation, validation, review, approval, operational verification, or production readiness.
