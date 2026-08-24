---
id: EX-WRK-SELECT-001
title: Worker Service Composition Example Standards Selection
version: 0.1.0
status: baseline
---
# Worker Service Composition Example Standards Selection

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
| Profile: WORKER_SERVICE | Defines the project-type overlay and common operational concerns. |
| Language: JavaScript and TypeScript | Defines implementation, dependency, testing, security, documentation, and completion expectations. |
| Discipline: Architecture and System Design | Selected because the fictitious architecture and change surface require this concern. |
| Discipline: Testing and Quality Engineering | Selected because the fictitious architecture and change surface require this concern. |
| Discipline: Integration Engineering | Selected because the fictitious architecture and change surface require this concern. |
| Discipline: Application Security | Selected because the fictitious architecture and change surface require this concern. |
| Discipline: Observability | Selected because the fictitious architecture and change surface require this concern. |
| Discipline: Site Reliability Engineering | Selected because the fictitious architecture and change surface require this concern. |
| Discipline: CI/CD | Selected because the fictitious architecture and change surface require this concern. |
| Discipline: Software Supply Chain | Selected because the fictitious architecture and change surface require this concern. |
| Discipline: Documentation | Selected because the fictitious architecture and change surface require this concern. |
| Discipline: Release Engineering | Selected because the fictitious architecture and change surface require this concern. |
| Platform: Containers | Selected because the example is packaged or operated on this platform. |
| Platform: Kubernetes | Selected because the example is packaged or operated on this platform. |

## Meaningful omissions

- **Product Management:** The example worker implements an existing fictional message-processing contract and does not define a new product, material user outcome, requirement set, or MVP boundary.
- **User Experience:** The worker is headless and owns no human workflow or interface; operational runbooks and telemetry are not represented as UX validation.
- **API Engineering:** The worker consumes messages and calls APIs but does not expose a public API contract. Integration Engineering governs its boundaries.
- **Database Engineering:** No persistent relational schema is defined.
- **Privacy:** The fictitious payload is synthetic. Add Privacy whenever personal, sensitive, or regulated data is processed.
- **Virtualization:** Kubernetes is selected, but the underlying hypervisor and hosts are not administered by the example.
- **Operating systems:** Node and endpoint operating-system management remains outside scope.
- **Networking:** Kubernetes service networking is covered by the platform package; external network-device control planes are not selected.

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
