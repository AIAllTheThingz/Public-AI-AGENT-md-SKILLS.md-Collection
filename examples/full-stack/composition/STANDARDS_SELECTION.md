---
id: EX-FULL-SELECT-001
title: Full-Stack Web Application Composition Example Standards Selection
version: 0.2.0
status: baseline
---
# Full-Stack Web Application Composition Example Standards Selection

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
| Profile: WEB_APPLICATION | Defines the project-type overlay and common operational concerns. |
| Language: C# | Defines compiler/language, nullability, async, API, resource, security, interop, scripting, testing, and completion expectations. |
| Runtime: .NET | Defines SDK, target-framework, runtime, dependency, application-model, build, and publishing expectations. |
| Language: JavaScript and TypeScript | Defines implementation, dependency, testing, security, documentation, and completion expectations. |
| Discipline: Product Management | Defines the fictitious product problem, intended users, requirements, MVP boundary, acceptance criteria, decisions, and traceability. |
| Discipline: User Experience | Governs the browser journey, interaction and recovery states, honest research state, and UX validation separately from Accessibility. |
| Discipline: Application Security | Selected because the fictitious architecture and change surface require this concern. |
| Discipline: Architecture and System Design | Selected because the fictitious architecture and change surface require this concern. |
| Discipline: Testing and Quality Engineering | Selected because the fictitious architecture and change surface require this concern. |
| Discipline: API Engineering | Selected because the fictitious architecture and change surface require this concern. |
| Discipline: Database Engineering | Selected because the fictitious architecture and change surface require this concern. |
| Discipline: Accessibility | Selected because the fictitious architecture and change surface require this concern. |
| Discipline: Privacy and Data Governance | Selected because the fictitious architecture and change surface require this concern. |
| Discipline: Observability | Selected because the fictitious architecture and change surface require this concern. |
| Discipline: Site Reliability Engineering | Selected because the fictitious architecture and change surface require this concern. |
| Discipline: Documentation | Selected because the fictitious architecture and change surface require this concern. |
| Discipline: CI/CD | Selected because the fictitious architecture and change surface require this concern. |
| Discipline: Software Supply Chain | Selected because the fictitious architecture and change surface require this concern. |
| Discipline: Release Engineering | Selected because the fictitious architecture and change surface require this concern. |
| Discipline: Integration Engineering | Selected because the fictitious architecture and change surface require this concern. |
| Platform: Containers | Selected because the example is packaged or operated on this platform. |
| Platform: Kubernetes | Selected because the example is packaged or operated on this platform. |
| Framework: ASP.NET Core | Adds framework-specific implementation and security expectations. |
| Framework: React | Adds framework-specific implementation and security expectations. |

## Meaningful omissions

- **Data Engineering:** The example stores application records but does not define analytical pipelines, lineage, or publication workflows.
- **No major omission:** This high-risk composition intentionally adopts a broad set of disciplines.
- **Virtualization:** The example does not administer the infrastructure beneath Kubernetes.
- **Operating systems:** Node and endpoint operating-system management remains outside the application scope.
- **Networking:** Application and Kubernetes networking are modeled, but external device and fabric control planes are not selected.

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
