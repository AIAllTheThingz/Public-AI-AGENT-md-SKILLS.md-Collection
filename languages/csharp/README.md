---
id: CSHARP-README-001
title: C# Language Package
version: 0.1.0
status: baseline
---

# C# Language Package

## Purpose

Provide independently adoptable standards for advanced, safe, testable, compatible, and maintainable C# language engineering.

This package owns C# source semantics. The existing [.NET package](../dotnet/) owns the modern .NET SDK/runtime/application boundary. Most modern C# repositories should compose both packages; C# hosted by Unity, Godot, legacy .NET Framework, an embedded host, or another constrained environment must select the applicable framework/runtime standards and preserve that compiler boundary.

## Use this package for

- `.cs` and `.csx` code
- C# compiler and language-version behavior
- nullable reference types and type-system design
- async, tasks, cancellation, channels, and concurrent code
- public API and serialization compatibility
- generics, records, pattern matching, delegates, events, and LINQ
- deterministic resource lifetime and performance-sensitive code
- Roslyn analyzers, source generators, reflection, and expression trees
- native interoperability, marshalling, and unsafe code
- C# scripting and automation
- C# tests, review, refactoring, and migration

## Package contents

| Path | Purpose |
|---|---|
| [SKILL.md](SKILL.md) | Direct progressive-disclosure C# engineering skill |
| [AGENTS.md](AGENTS.md) | Mandatory scoped behavior and stable rules |
| [C# coding standard](standards/CSHARP_CODING_STANDARD.md) | Language structure, control flow, errors, LINQ, and maintainability |
| [Type system and nullability](standards/TYPE_SYSTEM_AND_NULLABILITY_STANDARD.md) | Types, generics, nullability, records, equality, and contracts |
| [Async and concurrency](standards/ASYNC_AND_CONCURRENCY_STANDARD.md) | Tasks, cancellation, timeouts, synchronization, and bounded parallelism |
| [API design and compatibility](standards/API_DESIGN_AND_COMPATIBILITY_STANDARD.md) | Public surface, versioning, serialization, and consumer compatibility |
| [Resource and performance](standards/RESOURCE_AND_PERFORMANCE_STANDARD.md) | Ownership, disposal, allocation, pooling, spans, and measurement |
| [Security](standards/SECURITY_STANDARD.md) | Trust boundaries, validation, secrets, deserialization, processes, paths, and cryptography |
| [Build and dependency](standards/BUILD_AND_DEPENDENCY_STANDARD.md) | SDK/compiler resolution, analyzers, generators, packages, and reproducibility |
| [Testing](standards/TESTING_STANDARD.md) | Behavior, negative paths, concurrency, compatibility, and evidence |
| [Documentation](standards/DOCUMENTATION_STANDARD.md) | XML documentation, decisions, examples, and operator guidance |
| [Interop, reflection, and generation](standards/INTEROP_REFLECTION_AND_GENERATION_STANDARD.md) | High-complexity and native boundaries |
| [Scripting and tooling](standards/SCRIPTING_AND_TOOLING_STANDARD.md) | `.csx`, file-based apps, automation phases, and exit behavior |
| [Observability](standards/OBSERVABILITY_STANDARD.md) | Structured diagnostics and sensitive-data control |
| [Completion evidence](standards/COMPLETION_EVIDENCE.md) | Proof required for completion claims |
| [Templates](templates/) | Adoption, class, async service, and unit-test starting points |
| [Adoption example](examples/ADOPTION_EXAMPLE.md) | Fictitious composition guidance |
| [Manifest](MANIFEST.md) | Required files and acceptance checks |

## Language and runtime boundary

The accountable C# source-review state is maintained in [`../../SOURCE_REVIEWS.json`](../../SOURCE_REVIEWS.json) with durable evidence under [`../../source-reviews/`](../../source-reviews/). The 2026-08-15 accountable review identifies C# 14 as the stable language associated with .NET 10. This package does not require every existing repository to migrate.

- New modern .NET work should use the stable language version associated with the selected supported target framework.
- Existing projects preserve their declared compiler, target, runtime, and consumer boundary unless migration is in scope.
- Do not use `LangVersion=latest`; it can resolve differently across environments.
- Preview features require explicit approval and documented isolation, support, rollback, and migration limitations.
- A newer C# version than the target framework's associated version is not assumed supported.

The adopting repository must record the effective SDK/compiler and prove CI uses the intended boundary.

## Composition

Apply additional packages based on actual ownership:

- [.NET](../dotnet/) for the SDK, CLR, target frameworks, MSBuild, NuGet, hosting, and publishing
- [ASP.NET Core](../../frameworks/aspnet-core/) for web applications and services
- application security, testing, architecture, API, database, integration, observability, SRE, CI/CD, supply-chain, and release disciplines as applicable
- platform, virtualization, operating-system, networking, and project-profile packages for the deployed boundary

The C# package may strengthen language-specific requirements. It does not weaken the .NET or framework package.

## Adoption questions

- Which SDK/compiler, language version, target frameworks, runtimes, operating systems, and architectures are supported?
- Is `LangVersion` defaulted from the target framework or explicitly pinned?
- Are nullable reference types enabled, and where are oblivious or suppressed boundaries allowed?
- Which public APIs, serialized shapes, configuration keys, events, and exception behaviors are contracts?
- Who owns asynchronous work, cancellation, resources, generated code, and native handles?
- Which analyzers, warning levels, formatting rules, generators, and dependency policies are enforced?
- Which code uses reflection, `dynamic`, expressions, interop, unsafe blocks, pooling, spans, or custom memory ownership?
- Which tests prove cancellation, concurrency, cleanup, compatibility, security, and negative behavior?
- Which validation commands run locally and in CI?

## Suggested validation

Use repository-pinned commands. For a typical modern .NET repository:

```bash
dotnet --info
dotnet restore --locked-mode
dotnet format --verify-no-changes
dotnet build --no-restore
dotnet test --no-build
dotnet package list --vulnerable --include-transitive
```

Add API compatibility, generated-file determinism, native-platform, performance, publish, and runtime checks where relevant. Do not claim these commands ran unless they actually ran against the final revision.

## Security and compatibility

Treat public APIs, serialization, interop layouts, generated code, source-generator inputs, reflection-discovered members, default parameter values, nullability annotations, and exception behavior as compatibility surfaces when consumers depend on them.

Do not disable TLS verification, use unsafe deserialization, concatenate shell commands or SQL, trust user-controlled paths, embed secrets, broadly suppress analyzers, or introduce unsafe/native code without explicit boundaries and evidence.

## Limitations

This package does not select an application architecture, framework, database, cloud, deployment method, identity provider, test framework, or production environment. It does not prove security, correctness, performance, portability, or compatibility. Those claims require project-specific evidence and accountable review.

## Authoritative starting points

- [Microsoft C# documentation](https://learn.microsoft.com/en-us/dotnet/csharp/)
- [Configure the C# language version](https://learn.microsoft.com/en-us/dotnet/csharp/language-reference/configure-language-version)
- [Nullable reference types](https://learn.microsoft.com/en-us/dotnet/csharp/nullable-references)
- [Asynchronous programming with C#](https://learn.microsoft.com/en-us/dotnet/csharp/asynchronous-programming/)
- [.NET code analysis](https://learn.microsoft.com/en-us/dotnet/fundamentals/code-analysis/overview)

Revalidate current language, SDK, analyzer, security, and support behavior before relying on version-specific guidance.
