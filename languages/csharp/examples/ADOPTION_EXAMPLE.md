---
id: CSHARP-EXAMPLE-001
title: C# Adoption Example
version: 0.1.0
status: stable
---

# C# Adoption Example

## Boundary

This fictitious example demonstrates composition only. It does not represent a production system or a validated live deployment.

- Project: `sample-worker.example.invalid`
- Source: C# application code under `src/`
- Language: stable C# associated with the project's pinned supported SDK
- Runtime: modern .NET, so both `languages/csharp` and `languages/dotnet` are selected
- Mode: code generation, static validation, and non-production tests only

## Selected packages

- root governance
- C# language package and direct C# skill
- .NET package for SDK/runtime/MSBuild/NuGet behavior
- worker-service project profile
- architecture, application-security, testing, observability, SRE, CI/CD, supply-chain, and documentation disciplines
- applicable operating-system and deployment-platform packages

## Project declarations

The adopting project records:

- pinned SDK/compiler and effective stable language version
- target framework, runtime, platforms, and architectures
- nullable analysis enabled
- warning and analyzer policy
- package lock and approved sources
- public/serialized contract inventory
- cancellation, timeout, task ownership, concurrency, resource lifetime, and shutdown behavior
- real format, analyze, build, test, security, package, and publish commands

## Example change

A fictitious change adds a cancellable worker operation. The implementation:

- validates identifiers before I/O
- propagates the caller's cancellation token
- bounds parallel work and queue capacity
- owns and observes every started task
- disposes only resources it creates
- returns structured per-item outcomes
- redacts sensitive values before logging
- preserves the existing public and serialized contract

## Validation evidence

The fictitious record would include exact SDK resolution, restore, formatting, analyzer, compilation, unit, cancellation, concurrency, cleanup, integration, dependency, publish, and runtime results.

It would also state which supported platforms and live external services were not tested. This repository example does not claim that any C# compiler or .NET command was executed.

## Adaptation warning

Replace the fictitious project identity and assumptions only inside an adopting repository. Revalidate current Microsoft language/runtime support, package compatibility, platform behavior, and project-specific authorization before implementation or execution.
