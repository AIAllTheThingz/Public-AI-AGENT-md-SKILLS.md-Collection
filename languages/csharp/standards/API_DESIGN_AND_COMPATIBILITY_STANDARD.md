---
id: CSHARP-API-001
title: C# API Design and Compatibility Standard
version: 0.1.0
status: stable
---

# C# API Design and Compatibility Standard

## Purpose

Protect C# source, binary, behavioral, and serialized contracts while keeping APIs clear and difficult to misuse.

## Contract inventory

Treat these as contracts when consumers depend on them:

- public and protected types and members
- type kind, inheritance, interfaces, accessibility, generic constraints, and variance
- nullability annotations and required initialization
- parameter order, names where named arguments are used, optional defaults, and `params` behavior
- return types, exceptions, cancellation, enumeration, ordering, and concurrency behavior
- attributes used by frameworks, serializers, analyzers, linkers, native interop, or reflection
- serialized member names, shapes, defaults, discriminators, and unknown-member behavior
- event names, event order, delegate shapes, and lifecycle
- assembly names, namespaces, package identity, strong naming, trimming/AOT annotations, and generated public surface

## Design requirements

- Make preconditions and invalid state visible in types, names, validation, and documentation.
- Keep the public surface minimal and cohesive.
- Prefer abstractions that represent real substitution or ownership boundaries.
- Do not expose mutable implementation collections, persistence entities, service locators, or internal framework objects by default.
- Define cancellation, timeout, thread-safety, ownership, disposal, and partial-result behavior.
- Avoid optional parameters in contracts where changing the default would create source/binary or behavioral ambiguity.
- Do not use exceptions, booleans, or null as undocumented multi-state protocols.

## Compatibility analysis

Before changing a published or shared contract:

- identify supported consumers and distribution channels
- compare source and binary API surface
- evaluate reflection, serialization, dependency injection, configuration, and framework discovery
- evaluate default values, overload resolution, generic inference, extension-method selection, and exception behavior
- evaluate trimming, AOT, linker, native, and platform assumptions where applicable
- define semantic version, deprecation, migration, and rollback impact

Compiler success for the producer does not prove consumer compatibility.

## Deprecation and migration

- Prefer additive migration where it does not create ambiguous overloads or permanent duplication.
- Mark deprecated APIs with an actionable replacement and planned support boundary.
- Keep obsolete members long enough for the adopting project's compatibility policy.
- Do not silently repurpose an existing member, enum value, serialized field, or exception.
- Provide contract tests or compatibility tooling evidence for supported consumers.

## Serialization

- Use explicit durable names and version-tolerant shapes for persisted or exchanged data.
- Define missing, unknown, duplicate, null, default, and future member behavior.
- Do not bind untrusted type metadata to arbitrary runtime types.
- Separate wire/storage contracts from mutable domain and persistence implementation where their lifecycles differ.
- Test round trip, forward/backward compatibility, malformed input, size limits, and sensitive-data exposure.

## Evidence

Record the old and new surface, affected consumers, compatibility classification, version decision, migration guidance, deprecation window, contract tests, serializer data, and any compatibility checks not run.
