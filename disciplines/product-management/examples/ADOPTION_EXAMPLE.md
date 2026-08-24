---
id: DISC-EX-PROD-ADOPTION
title: Product Management Adoption Example
version: 0.1.0
status: baseline
---

# Product Management Adoption Example

This example is fictitious and demonstrates composition, not evidence of a real product decision.

## Example context

The fictional **Northstar Community Library** is considering a self-service hold-renewal capability. It records the problem and intended patrons, but no direct research has occurred, so research evidence is `NotRun`. Assumptions about patron demand remain assumptions.

The project creates `REQ-FUNC-001` for eligible renewal behavior and `REQ-NFR-001` for applicable response expectations, each with acceptance criteria. It records a separate result for each criterion so `Tested` cannot imply `Pass`; a production-candidate claim would require every applicable criterion to have a current explicit `Pass` for the exact candidate and conditions. It excludes fee payment from MVP and records that exclusion explicitly.

## Composition and traceability

The project composes Product Management with User Experience, Accessibility, Architecture, Application Security, Testing, and SRE as applicable. Its traceability record links the brief, requirements, ADR, change, tests, candidate deployment, and later operational evidence. Before deployment, production evidence remains `NotRun`; implementation evidence is not promoted to `OperationallyVerified`.
