---
id: CSHARP-EVIDENCE-001
title: C# Completion Evidence Standard
version: 0.1.0
status: stable
---

# C# Completion Evidence Standard

## Purpose

Define the minimum proof required before claiming C# work is complete, compatible, secure, tested, or ready for review.

## Required completion record

### Scope

- files, projects, generated artifacts, packages, and public contracts changed
- requested behavior implemented
- behavior intentionally unchanged
- selected C# and companion packages

### Toolchain

- operating system and architecture
- SDK/compiler and effective C# language version
- target frameworks, runtimes, or scripting hosts
- analyzer, formatter, generator, and relevant tool versions
- local/CI parity or known differences

### Normative behavior and compatibility

- source, binary, serialized, configuration, reflection, native, and behavioral contracts affected
- nullability, required initialization, exception, cancellation, ordering, and thread-safety changes
- semantic version or migration impact
- supported consumers/targets tested and not tested

### Security and operations

- trust boundaries and side effects affected
- input validation and authorization behavior
- secret, redaction, process, path, deserialization, transport, and cryptography impact
- concurrency, timeout, retry, cleanup, rerun, and unknown-outcome behavior
- analyzer, dependency, and suppression findings

### Validation

Record exact commands, working directory, configuration/target, result, and relevant counts for:

- SDK/compiler resolution
- restore or dependency resolution
- formatting/generated-file verification
- analyzers and compilation
- focused unit/regression tests
- complete applicable tests
- integration/contract/negative tests
- API or serialization compatibility checks
- dependency/security checks
- benchmark/performance checks
- build, package, publish, or representative runtime checks

Do not use “tests passed” without the command and scope.

### Not performed

List every material check not run and why. Distinguish unavailable tooling, out-of-scope environments, missing authorization, cost, time, and intentionally deferred validation.

### Limitations and review

- assumptions and untested paths
- known defects, warnings, suppressions, or flaky behavior
- platform, native, trimming/AOT, generated, concurrency, and performance limitations
- remaining risks and owners
- required C#/.NET, security, compatibility, native, or operational reviewers

## Claim boundaries

Do not claim:

- production ready from unit tests alone
- cross-platform without representative platform evidence
- thread safe from a single successful execution
- allocation-free or faster without measurement
- backward compatible without contract analysis
- secure because analyzers are clean
- compatible with all C# or .NET versions
- live-environment behavior from mocks

Use precise states such as implemented, compiled, statically analyzed, unit tested, integration tested, compatibility checked, benchmarked, published, executed, verified, or not validated.

## Typical modern .NET evidence commands

Use repository-defined commands first. Examples include:

```bash
dotnet --info
dotnet restore --locked-mode
dotnet format --verify-no-changes
dotnet build --no-restore
dotnet test --no-build
dotnet package list --vulnerable --include-transitive
dotnet publish --configuration Release --no-restore
```

These examples are not evidence until executed successfully against the relevant final revision.
