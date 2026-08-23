---
id: PROFILE-SECTOOL-EX-001
title: Security Tool Project Profile Adoption Example
version: 0.2.0
status: baseline
---
# Security Tool Project Profile Adoption Example

## Fictitious project

This example models a non-production security tool.

No production systems, identities, credentials, endpoints, data, or approval are included.

## Profile decision

- Primary profile: [`../../SECURITY_TOOL.md`](../../SECURITY_TOOL.md)
- Typical starting risk: `high`
- Actual risk: must be assessed by the adopting project

## Selected disciplines

- [Application Security](../../../disciplines/application-security/)
- [Architecture](../../../disciplines/architecture/)
- [Testing](../../../disciplines/testing/)
- [Privacy](../../../disciplines/privacy/)
- [Observability](../../../disciplines/observability/)
- [Documentation](../../../disciplines/documentation/)
- [Supply Chain](../../../disciplines/supply-chain/)
- [Release Engineering](../../../disciplines/release-engineering/)

## Conditional review

- [Product Management](../../../disciplines/product-management/)
- [User Experience](../../../disciplines/user-experience/)
- [Ci Cd](../../../disciplines/ci-cd/)
- [Integration](../../../disciplines/integration/)
- [Sre](../../../disciplines/sre/)
- [Data Engineering](../../../disciplines/data-engineering/)
- [Database](../../../disciplines/database/)

## Project decisions

- authorized scope and target identity
- safe handling of findings and evidence
- false-positive and false-negative limitations
- privilege and data sensitivity
- non-destructive defaults
- remediation authorization
- finding lifecycle and disclosure
- audit, retention, and chain of custody

## Suggested scopes

- src/collect
- src/analyze
- src/report
- src/remediate
- tests
- docs

## Evidence boundary

The example demonstrates composition only. It does not prove implementation, validation, review, approval, operational verification, or production readiness.
