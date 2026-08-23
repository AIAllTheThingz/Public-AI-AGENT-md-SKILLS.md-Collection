---
id: PROFILE-COMPOSE-001
title: Project Profile Composition Model
version: 0.2.0
status: baseline
---
# Project Profile Composition Model

## Purpose

Defines how project profiles compose with governance, languages, disciplines, frameworks, platforms, virtualization systems, operating systems, networking systems, and scoped instructions.

## Layer model

```text
external obligations
+ governance
+ primary project profile
+ secondary profiles
+ languages
+ disciplines
+ frameworks
+ platforms
+ virtualization
+ operating systems
+ networking
+ project facts
+ root and nested AGENTS.md
+ evidence
```

## Responsibilities

- Governance controls authority, risk, evidence, exceptions, review, and production readiness.
- Profiles describe project shape and expected package composition.
- Product Management governs product definition, requirements, scope, acceptance, decisions, and traceability when a product or material capability is in scope.
- User Experience governs research, journeys, tasks, workflows, interactions, usability, and UX validation when people pursue goals through an owned experience; Accessibility remains a separate applicable discipline.
- Languages control implementation conventions and runtime behavior.
- Disciplines control cross-cutting engineering work.
- Frameworks specialize application behavior.
- Platforms control execution and deployment boundaries.
- Virtualization packages control hypervisor, manager, cluster, host, guest, virtual-network, and virtual-storage boundaries.
- Operating-system packages control privileged host, endpoint, lifecycle, update, identity, service, security, and recovery boundaries.
- Networking packages control device, controller, routing, switching, policy, fabric, firmware, and network-recovery boundaries.
- Project instructions declare actual facts, targets, owners, and commands.
- Evidence records what was actually implemented, validated, reviewed, and approved.

## Primary profile

The primary profile represents the main operating shape and provides the default composition.

## Secondary profiles

A secondary profile adds obligations for a distinct component or behavior. It must not be used to weaken the primary profile.

Examples:

- a SaaS product with worker services
- a mobile application with a public API
- an AI agent exposed through a web application
- a security tool distributed as a CLI
- a data pipeline with serverless ingestion functions

## Conflict handling

When profiles appear to conflict:

1. apply governance
2. identify the distinct scopes
3. use nested instructions to separate scopes
4. apply the stricter compatible control
5. record unresolved material conflict
6. use the exception process only when authorized

## Required composition record

Record:

- primary profile
- secondary profiles
- rationale
- required packages
- conditional packages
- omitted packages
- applicable Product Inception gates and product lifecycle state when Product Management applies
- research state and separate UX/Accessibility evidence boundaries when User Experience applies
- scope boundaries
- nested instruction locations
- risk classification
- validation and evidence
- reviewer and approver

## Anti-patterns

- selecting profiles by repository name
- choosing the least demanding profile
- stacking every profile without scope
- using a profile as architecture approval
- omitting governance
- treating optional implementation technology as a project shape
- copying an example manifest without reassessment
