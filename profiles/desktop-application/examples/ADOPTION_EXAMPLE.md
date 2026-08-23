---
id: PROFILE-DESKTOP-EX-001
title: Desktop Application Project Profile Adoption Example
version: 0.2.0
status: baseline
---
# Desktop Application Project Profile Adoption Example

## Fictitious project

This example models a non-production desktop application.

No production systems, identities, credentials, endpoints, data, or approval are included.

## Profile decision

- Primary profile: [`../../DESKTOP_APPLICATION.md`](../../DESKTOP_APPLICATION.md)
- Typical starting risk: `moderate`
- Actual risk: must be assessed by the adopting project

## Selected disciplines

- [Application Security](../../../disciplines/application-security/)
- [Architecture](../../../disciplines/architecture/)
- [Testing](../../../disciplines/testing/)
- [Accessibility](../../../disciplines/accessibility/)
- [Privacy](../../../disciplines/privacy/)
- [Documentation](../../../disciplines/documentation/)
- [Release Engineering](../../../disciplines/release-engineering/)

## Conditional review

- [Product Management](../../../disciplines/product-management/)
- [User Experience](../../../disciplines/user-experience/)
- [Supply Chain](../../../disciplines/supply-chain/)
- [Ci Cd](../../../disciplines/ci-cd/)
- [Observability](../../../disciplines/observability/)
- [Integration](../../../disciplines/integration/)
- [Database](../../../disciplines/database/)

This base-profile example leaves Product Management and User Experience conditional. An adopter promotes them when the change defines material product outcomes or requirements, or owns material journeys, interactions, recovery states, or UX claims.

## Project decisions

- local data protection
- installer and update integrity
- privilege and elevation boundaries
- secure storage and credential integration
- accessibility and keyboard behavior
- offline and degraded operation
- telemetry and privacy
- supported operating systems and migration

## Suggested scopes

- src/ui
- src/core
- src/platform
- tests
- docs
- installer

## Evidence boundary

The example demonstrates composition only. It does not prove implementation, validation, review, approval, operational verification, or production readiness.
