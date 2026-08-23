---
id: PROFILE-WEB-APP-EX-001
title: Web Application Project Profile Adoption Example
version: 0.2.0
status: baseline
---
# Web Application Project Profile Adoption Example

## Fictitious project

This example models a non-production web application.

No production systems, identities, credentials, endpoints, data, or approval are included.

## Profile decision

- Primary profile: [`../../WEB_APPLICATION.md`](../../WEB_APPLICATION.md)
- Typical starting risk: `moderate`
- Actual risk: must be assessed by the adopting project

## Selected disciplines

- [Application Security](../../../disciplines/application-security/)
- [Architecture](../../../disciplines/architecture/)
- [Testing](../../../disciplines/testing/)
- [Accessibility](../../../disciplines/accessibility/)
- [Privacy](../../../disciplines/privacy/)
- [Observability](../../../disciplines/observability/)
- [Ci Cd](../../../disciplines/ci-cd/)
- [Supply Chain](../../../disciplines/supply-chain/)
- [Release Engineering](../../../disciplines/release-engineering/)

## Conditional review

- [Product Management](../../../disciplines/product-management/)
- [User Experience](../../../disciplines/user-experience/)
- [Api Engineering](../../../disciplines/api-engineering/)
- [Database](../../../disciplines/database/)
- [Integration](../../../disciplines/integration/)
- [Sre](../../../disciplines/sre/)
- [Documentation](../../../disciplines/documentation/)

This base-profile example leaves Product Management and User Experience conditional. An adopter promotes them when the change defines material product outcomes or requirements, or owns material journeys, interactions, recovery states, or UX claims.

## Project decisions

- server-side authorization model
- client and server trust boundaries
- WCAG 2.2 AA or stricter accessibility target
- content security and safe rendering
- browser support and assistive-technology coverage
- session and state management
- privacy, analytics, and consent behavior
- deployment, rollback, caching, and asset compatibility

## Suggested scopes

- src/frontend
- src/backend
- tests
- docs
- public
- deploy

## Evidence boundary

The example demonstrates composition only. It does not prove implementation, validation, review, approval, operational verification, or production readiness.
