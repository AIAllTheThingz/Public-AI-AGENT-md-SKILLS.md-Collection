---
id: EX-MIN-SELECT-001
title: Minimal CLI Composition Example Standards Selection
version: 0.1.0
status: baseline
---
# Minimal CLI Composition Example Standards Selection

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
| Profile: CLI_TOOL | Defines the project-type overlay and common operational concerns. |
| Language: PowerShell | Defines implementation, dependency, testing, security, documentation, and completion expectations. |
| Discipline: Testing and Quality Engineering | Selected because the fictitious architecture and change surface require this concern. |
| Discipline: Documentation | Selected because the fictitious architecture and change surface require this concern. |
| Discipline: Software Supply Chain | Selected because the fictitious architecture and change surface require this concern. |

## Meaningful omissions

- **Product Management:** The example is a bounded transformation implementing an existing fictional command contract; it does not define a new product, material capability, outcome, requirement set, or MVP boundary.
- **User Experience:** The example has no material interactive journey beyond explicit command arguments and structured output. If prompts, multi-step human workflows, or usability claims enter scope, UX becomes required.
- **Application Security:** The example has no network service or protected business operation, but input validation and secret handling still apply through language and governance standards.
- **Observability:** A local CLI may use structured output and exit codes without adopting a service telemetry package.
- **SRE:** No service availability, on-call, or recovery objective is claimed.
- **Virtualization:** The example does not administer a hypervisor, manager, host, or guest.
- **Operating systems:** The example uses PowerShell but performs no Windows or other operating-system administration.
- **Networking:** The example does not configure network devices, controllers, routing, switching, or fabrics.

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
