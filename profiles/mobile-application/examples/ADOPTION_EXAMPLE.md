---
id: PROFILE-MOBILE-EX-001
title: Mobile Application Project Profile Adoption Example
version: 0.2.0
status: baseline
---
# Mobile Application Project Profile Adoption Example

## Fictitious project

This example models a non-production mobile application.

No production systems, identities, credentials, endpoints, data, or approval are included.

## Profile decision

- Primary profile: [`../../MOBILE_APPLICATION.md`](../../MOBILE_APPLICATION.md)
- Typical starting risk: `moderate`
- Actual risk: must be assessed by the adopting project

## Selected disciplines

- [Application Security](../../../disciplines/application-security/)
- [Architecture](../../../disciplines/architecture/)
- [Testing](../../../disciplines/testing/)
- [Accessibility](../../../disciplines/accessibility/)
- [Privacy](../../../disciplines/privacy/)
- [Supply Chain](../../../disciplines/supply-chain/)
- [Release Engineering](../../../disciplines/release-engineering/)

## Conditional review

- [Product Management](../../../disciplines/product-management/)
- [User Experience](../../../disciplines/user-experience/)
- [Observability](../../../disciplines/observability/)
- [Ci Cd](../../../disciplines/ci-cd/)
- [Api Engineering](../../../disciplines/api-engineering/)
- [Integration](../../../disciplines/integration/)
- [Documentation](../../../disciplines/documentation/)

This base-profile example leaves Product Management and User Experience conditional. An adopter promotes them when the change defines material product outcomes or requirements, or owns material journeys, interactions, recovery states, or UX claims.

## Project decisions

- secure storage
- network trust and certificate behavior
- permission minimization
- offline and synchronization behavior
- biometric and device-authentication integration
- analytics, crash reporting, and privacy
- app-store signing and release
- minimum supported OS and upgrade path

## Suggested scopes

- src/ui
- src/domain
- src/platform
- tests
- docs
- release

## Evidence boundary

The example demonstrates composition only. It does not prove implementation, validation, review, approval, operational verification, or production readiness.
