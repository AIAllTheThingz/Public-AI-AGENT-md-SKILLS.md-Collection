---
id: PROFILE-LIB-EX-001
title: Public Library Project Profile Adoption Example
version: 0.2.0
status: baseline
---
# Public Library Project Profile Adoption Example

## Fictitious project

This example models a non-production public library.

No production systems, identities, credentials, endpoints, data, or approval are included.

## Profile decision

- Primary profile: [`../../PUBLIC_LIBRARY.md`](../../PUBLIC_LIBRARY.md)
- Typical starting risk: `moderate`
- Actual risk: must be assessed by the adopting project

## Selected disciplines

- [Architecture](../../../disciplines/architecture/)
- [Testing](../../../disciplines/testing/)
- [Documentation](../../../disciplines/documentation/)
- [Supply Chain](../../../disciplines/supply-chain/)
- [Release Engineering](../../../disciplines/release-engineering/)

## Conditional review

- [Product Management](../../../disciplines/product-management/)
- [User Experience](../../../disciplines/user-experience/)
- [Application Security](../../../disciplines/application-security/)
- [Api Engineering](../../../disciplines/api-engineering/)
- [Ci Cd](../../../disciplines/ci-cd/)
- [Accessibility](../../../disciplines/accessibility/)
- [Privacy](../../../disciplines/privacy/)

This base-profile example leaves Product Management and User Experience conditional. Promote Product Management for material consumer outcomes, requirements, supported scope, or product decisions, and User Experience for an owned interactive consumer workflow.

## Project decisions

- public API compatibility
- supported runtimes and platforms
- dependency minimization
- semantic versioning
- examples and migration guidance
- deprecation and end-of-support
- package signing and provenance
- security reporting and release process

## Suggested scopes

- src/public
- src/internal
- tests
- docs
- packaging
- examples

## Evidence boundary

The example demonstrates composition only. It does not prove implementation, validation, review, approval, operational verification, or production readiness.
