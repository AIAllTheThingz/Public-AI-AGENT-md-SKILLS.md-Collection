---
id: PROFILE-AUTOMATION-EX-001
title: Internal Automation Project Profile Adoption Example
version: 0.2.0
status: baseline
---
# Internal Automation Project Profile Adoption Example

## Fictitious project

This example models a non-production internal automation.

No production systems, identities, credentials, endpoints, data, or approval are included.

## Profile decision

- Primary profile: [`../../INTERNAL_AUTOMATION.md`](../../INTERNAL_AUTOMATION.md)
- Typical starting risk: `high`
- Actual risk: must be assessed by the adopting project

## Selected disciplines

- [Application Security](../../../disciplines/application-security/)
- [Testing](../../../disciplines/testing/)
- [Documentation](../../../disciplines/documentation/)
- [Observability](../../../disciplines/observability/)
- [Ci Cd](../../../disciplines/ci-cd/)
- [Supply Chain](../../../disciplines/supply-chain/)

## Conditional review

- [Product Management](../../../disciplines/product-management/)
- [User Experience](../../../disciplines/user-experience/)
- [Architecture](../../../disciplines/architecture/)
- [Integration](../../../disciplines/integration/)
- [Release Engineering](../../../disciplines/release-engineering/)
- [Sre](../../../disciplines/sre/)
- [Privacy](../../../disciplines/privacy/)

## Project decisions

- discovery and validation phases
- dry-run, what-if, or preview behavior
- least privilege and credential handling
- target allowlists and identity confirmation
- approval for destructive and bulk changes
- audit trail and reports
- rollback, compensation, and partial failure
- scheduling, ownership, and recovery

## Suggested scopes

- src/discovery
- src/adapters
- src/orchestration
- tests
- docs
- config

## Evidence boundary

The example demonstrates composition only. It does not prove implementation, validation, review, approval, operational verification, or production readiness.
