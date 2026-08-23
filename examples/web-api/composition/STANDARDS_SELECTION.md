---
id: EX-API-SELECT-001
title: Web API Composition Example Standards Selection
version: 0.2.0
status: baseline
---
# Web API Composition Example Standards Selection

## Purpose

This document explains why the example selects each standards package. It prevents `project-manifest.json` from becoming an unexplained shopping list.

## Selection principles

- Select packages based on architecture, users, data, trust boundaries, delivery, and operational obligations.
- Prefer explicit rationale over copying a familiar stack.
- Do not omit a discipline merely because it adds review work.
- Add stricter project-specific rules without weakening shared controls.
- Revisit the selection when architecture or risk changes.

## Selected packages

| Package | Rationale |
|---|---|
| Governance | Organization-wide behavior, risk, evidence, exceptions, security, and review apply to every example. |
| Governance: [Product Inception Lifecycle](../../../governance/PRODUCT_INCEPTION_LIFECYCLE.md) | Explicitly selected because the example models a fictitious new API product and its path from inception through build. The selection activates lifecycle gates for this scope but does not imply a gate result. |
| Profile: WEB_API | Defines the project-type overlay and common operational concerns. |
| Language: C# | Defines compiler/language, nullability, async, API, resource, security, interop, scripting, testing, and completion expectations. |
| Runtime: .NET | Defines SDK, target-framework, runtime, dependency, application-model, build, and publishing expectations. |
| Discipline: Product Management | Promoted from the profile's conditional overlays because the fictitious account API defines an externally consumable capability whose requirements, acceptance criteria, scope, decisions, and traceability must be explicit. |
| Discipline: Application Security | Selected because the fictitious architecture and change surface require this concern. |
| Discipline: Architecture and System Design | Selected because the fictitious architecture and change surface require this concern. |
| Discipline: Testing and Quality Engineering | Selected because the fictitious architecture and change surface require this concern. |
| Discipline: API Engineering | Selected because the fictitious architecture and change surface require this concern. |
| Discipline: Privacy and Data Governance | Selected because the fictitious architecture and change surface require this concern. |
| Discipline: Observability | Selected because the fictitious architecture and change surface require this concern. |
| Discipline: CI/CD | Selected because the fictitious architecture and change surface require this concern. |
| Discipline: Software Supply Chain | Selected because the fictitious architecture and change surface require this concern. |
| Discipline: Documentation | Selected because the fictitious architecture and change surface require this concern. |
| Discipline: Release Engineering | Selected because the fictitious architecture and change surface require this concern. |
| Platform: Containers | Selected because the example is packaged or operated on this platform. |
| Framework: ASP.NET Core | Adds framework-specific implementation and security expectations. |

The schema-compatible manifest extension `AIAllTheThingz.governanceSelections` records this selection as `governance/PRODUCT_INCEPTION_LIFECYCLE.md`. It supplements the standard package fields; it does not treat governance as a discipline or create a new top-level manifest field.

## Meaningful omissions

- **User Experience:** The example exposes an API contract but owns no developer portal, console, or other human workflow. API contract and documentation review are not represented as UX validation.
- **Database Engineering:** The composition describes a persistence adapter but does not define a concrete schema or migration surface. Add the discipline when a real database is selected.
- **SRE:** Moderate risk and illustrative operations do not establish an on-call service objective. Add SRE when availability and recovery targets exist.
- **Accessibility:** The example exposes an API only and has no user interface.
- **Virtualization:** The example owns a container boundary, not the underlying hypervisor or hosts.
- **Operating systems:** Host and endpoint administration are outside the fictitious API scope.
- **Networking:** Application connectivity is modeled, but network-device and fabric control planes are not.

An omission is valid only for the current fictitious scope. It is not a permanent exemption.

## Selection review questions

- Does the manifest match the actual architecture?
- Are all trust boundaries covered?
- Are data storage and movement concerns represented?
- Are user-facing accessibility obligations represented?
- Are build, dependency, artifact, deployment, and release concerns represented?
- Are availability, recovery, incident, or on-call expectations represented?
- Are documentation and accountable review represented?
- Would adding a real database, identity provider, cloud platform, hypervisor, managed operating system, network control plane, external API, or regulated data change the selection?

## Change triggers

Reassess the composition when:

- a new component, language, framework, platform, virtualization system, operating system, networking system, data store, or external system is added
- public contracts or compatibility obligations change
- personal, sensitive, confidential, or regulated data enters scope
- production deployment, on-call, availability, or recovery expectations are introduced
- risk classification changes
- a temporary exception expires
