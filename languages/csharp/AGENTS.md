---
id: CSHARP-AGENT-001
title: C# Agent Standard
version: 0.1.0
status: baseline
applies_to:
  - csharp
depends_on:
  - GOV-RISK
  - GOV-SECDEV
---

# C# Agent Standard

## Purpose

Define mandatory behavior for agents that create, modify, review, test, secure, document, generate, or migrate C# source and C# scripting artifacts.

This package governs C# language engineering. Apply the [.NET package](../dotnet/) when work also affects the .NET SDK, target frameworks, CLR, MSBuild, NuGet, application models, hosting, publishing, or deployment.

## Scope

- `.cs` and `.csx` source
- compiler and language-version configuration
- nullable reference types and flow analysis
- generics, records, pattern matching, delegates, events, and LINQ
- asynchronous and concurrent code
- public and internal APIs
- resource ownership and disposal
- reflection, expression trees, source generators, analyzers, and generated code
- native interoperability, marshalling, and unsafe code
- C# scripting, file-based applications, and automation hosts
- C# tests, documentation, and examples

## Required reading

- [Package README](README.md)
- [Package manifest](MANIFEST.md)
- [C# coding standard](standards/CSHARP_CODING_STANDARD.md)
- [Type system and nullability standard](standards/TYPE_SYSTEM_AND_NULLABILITY_STANDARD.md)
- [Async and concurrency standard](standards/ASYNC_AND_CONCURRENCY_STANDARD.md)
- [API design and compatibility standard](standards/API_DESIGN_AND_COMPATIBILITY_STANDARD.md)
- [Resource and performance standard](standards/RESOURCE_AND_PERFORMANCE_STANDARD.md)
- [Security standard](standards/SECURITY_STANDARD.md)
- [Build and dependency standard](standards/BUILD_AND_DEPENDENCY_STANDARD.md)
- [Testing standard](standards/TESTING_STANDARD.md)
- [Documentation standard](standards/DOCUMENTATION_STANDARD.md)
- [Interop, reflection, and generation standard](standards/INTEROP_REFLECTION_AND_GENERATION_STANDARD.md)
- [Scripting and tooling standard](standards/SCRIPTING_AND_TOOLING_STANDARD.md) when scripting or automation is involved
- [Observability standard](standards/OBSERVABILITY_STANDARD.md) when operational telemetry is involved
- [Completion evidence standard](standards/COMPLETION_EVIDENCE.md)
- applicable governance, discipline, framework, platform, virtualization, operating-system, networking, profile, and project instructions

## Compiler and compatibility boundary

For new modern .NET development, use the stable C# version associated with the selected supported target framework. The accountable C# source-review state is maintained in [`../../SOURCE_REVIEWS.json`](../../SOURCE_REVIEWS.json) with durable evidence under [`../../source-reviews/`](../../source-reviews/); the 2026-08-15 review identifies C# 14 as the stable language associated with .NET 10.

Existing repositories must preserve their declared SDK, compiler, target framework, language version, runtime, and consumer compatibility unless migration is explicitly authorized.

Do not set `LangVersion` to `latest`. Do not use preview features, preview SDKs, or preview analyzer behavior unless the request explicitly requires them and the project documents isolation, upgrade, rollback, and support limitations.

Compiler success on one workstation is not compatibility evidence. Resolve and record the actual SDK/compiler used by local validation and CI.

## Non-negotiable behavior

- Make the smallest coherent change and preserve unrelated behavior.
- Model required, optional, and invalid states explicitly.
- Enable and honor nullable analysis; do not normalize broad suppression.
- Preserve public contracts unless a breaking change is explicitly authorized and documented.
- Use asynchronous APIs for asynchronous work and propagate cancellation.
- Bound concurrency, buffering, retries, polling, and memory growth.
- Dispose only resources the code owns, including failure and cancellation paths.
- Validate untrusted input at the boundary before parsing, deserializing, opening, invoking, or persisting it.
- Do not expose secrets or sensitive data in code, exceptions, logs, diagnostics, dumps, generated files, examples, or tests.
- Do not broadly disable compiler warnings, analyzers, nullable diagnostics, or security findings.
- Require evidence before introducing reflection-heavy, generated, unsafe, native, or allocation-sensitive complexity.
- Test negative, cancellation, concurrency, cleanup, and compatibility behavior where relevant.
- Report exact checks performed and checks not run.

## Product rules

### CSHARP-LANG-001

**Requirement:** Resolve the selected SDK/compiler and use a stable language version supported by the declared target; `latest` and unapproved preview settings are prohibited.

**Expected evidence:** SDK/compiler version, target framework or host, effective language version, configuration source, and CI parity result.

### CSHARP-NULL-002

**Requirement:** Nullable annotations and flow analysis must express the real contract; suppression requires a narrow, reviewable invariant.

**Expected evidence:** Nullable configuration, warning result, contract tests, and justification for each material suppression or oblivious boundary.

### CSHARP-ASYNC-003

**Requirement:** Asynchronous and concurrent code must propagate cancellation, avoid sync-over-async, bound concurrency, and define ownership of started work.

**Expected evidence:** Cancellation and timeout tests, concurrency bound, task ownership, shutdown behavior, and absence or justification of blocking bridges.

### CSHARP-API-004

**Requirement:** Public APIs, serialized shapes, generic constraints, default values, exception behavior, and binary/source compatibility must change only through reviewed versioning and migration decisions.

**Expected evidence:** API diff or contract comparison, compatibility tests, version impact, migration notes, and consumer review.

### CSHARP-RESOURCE-005

**Requirement:** Code must distinguish owned from borrowed resources and deterministically release owned synchronous and asynchronous resources on success, failure, and cancellation.

**Expected evidence:** Ownership documentation, disposal paths, failure/cancellation tests, and leak or lifetime analysis appropriate to risk.

### CSHARP-SEC-006

**Requirement:** C# code must validate trust boundaries and must not use insecure deserialization, command construction, path handling, cryptography, certificate bypass, or secret exposure as implementation shortcuts.

**Expected evidence:** Trust-boundary review, negative tests, analyzer/security results, redaction checks, and documented exceptions.

### CSHARP-TOOL-007

**Requirement:** Build, analyzer, formatter, generator, scripting-host, and dependency versions must be reproducible and reviewed; operational execution must not silently acquire floating code.

**Expected evidence:** Pinned or constrained toolchain, lock/restore strategy, provenance review, deterministic generation check, and dependency findings.

### CSHARP-TEST-008

**Requirement:** Tests must cover externally meaningful normal, boundary, invalid, cancellation, failure, concurrency, cleanup, and compatibility behavior appropriate to the change.

**Expected evidence:** Test inventory mapped to risks and exact focused plus repository-wide results.

### CSHARP-INTEROP-009

**Requirement:** Reflection, `dynamic`, expression compilation, source generation, native interop, and unsafe code require a documented boundary, minimized scope, validation, and fallback or failure behavior.

**Expected evidence:** Rationale, affected boundary, generated/native artifact review, platform assumptions, tests, and specialist review when risk warrants it.

### CSHARP-EVIDENCE-010

**Requirement:** Completion claims must identify the exact source and contracts changed, resolved compiler boundary, validation results, unavailable checks, and remaining limitations.

**Expected evidence:** A completion record conforming to [COMPLETION_EVIDENCE.md](standards/COMPLETION_EVIDENCE.md).

## Required working method

1. Read applicable instructions and define acceptance criteria.
2. Inventory projects, compiler settings, analyzers, generated code, tests, packages, public contracts, and supported consumers.
3. Classify security, compatibility, data, concurrency, performance, native, and operational risk.
4. Design types, invariants, ownership, cancellation, errors, and trust boundaries before implementation.
5. Implement the smallest coherent change using features supported by the resolved compiler.
6. Add tests from externally meaningful behavior and regression evidence.
7. Run formatting, analysis, compilation, tests, dependency/security checks, and representative build or publish as applicable.
8. Review the complete diff for accidental API changes, warnings, suppressions, secrets, generated drift, and unrelated edits.
9. Update documentation, examples, compatibility guidance, and evidence.

## Decision gates

Stop when the effective compiler or runtime is unknown, a target framework cannot support the proposed feature, public compatibility impact is unresolved, trust boundaries are unclear, a resource lifetime has no owner, generated output cannot be reproduced, or high-risk unsafe/native behavior lacks qualified review.

## Completion

Work is complete only when the requested behavior is implemented, contracts and compatibility are accounted for, security controls remain intact, relevant validation passes against the intended toolchain, unavailable checks are disclosed, and the final evidence does not exceed what was actually proven.
