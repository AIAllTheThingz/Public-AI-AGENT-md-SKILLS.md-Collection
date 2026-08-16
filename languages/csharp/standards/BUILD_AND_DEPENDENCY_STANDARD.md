---
id: CSHARP-BUILD-001
title: C# Build and Dependency Standard
version: 0.1.0
status: stable
---

# C# Build and Dependency Standard

## Purpose

Make C# compiler, analyzer, generator, formatting, dependency, and build behavior reproducible and reviewable.

## Toolchain resolution

- Record the actual SDK/compiler, language version, target framework or scripting host, operating system, architecture, and CI image.
- Pin or constrain SDK feature bands using the repository's approved mechanism.
- Do not use `LangVersion=latest`; use the target framework default or an explicit supported stable version.
- Preview language, SDK, workload, analyzer, or generator behavior requires explicit approval and isolated support/migration documentation.
- Keep local and CI tool resolution aligned. Report when exact parity is unavailable.

## Compiler and analyzer configuration

- Enable nullable analysis for new code and define migration boundaries for existing code.
- Use an explicit warning and analyzer policy appropriate to the repository.
- Do not globally suppress warnings, nullable diagnostics, or analyzer categories to make a build pass.
- Scope suppressions narrowly and include justification where the invariant is not obvious.
- Treat editor configuration, rulesets, global analyzer configuration, `Directory.Build.*`, and project files as reviewed code.
- Review changes to implicit usings, conditional compilation, constants, optimization, deterministic build, trimming, AOT, and unsafe settings for behavior impact.

## Dependencies

- Add a dependency only when its maintained capability materially exceeds a small, safe local implementation.
- Verify identity, source, publisher/maintainer, license, release activity, supported frameworks, transitive graph, advisories, and operational behavior.
- Pin or constrain versions according to repository policy and use lock files or locked restore where supported and appropriate.
- Do not acquire floating packages, tools, analyzers, generators, scripts, or binaries during ordinary operational execution.
- Remove unused direct dependencies and explain material transitive additions.
- Review build-time packages with the same seriousness as runtime packages because analyzers and generators execute during builds.

## Source generators and generated files

- Pin generator inputs and versions.
- Make generation deterministic for the same inputs or document unavoidable nondeterminism.
- Keep generated output out of review only when it is reproducibly generated and the repository policy permits omission.
- Validate generated public APIs, nullability, serialization, trimming/AOT behavior, and sensitive-data handling.
- Do not hand-edit generated files unless that is the explicit generator contract.

## Conditional compilation and multi-targeting

- Keep conditions small, named, and tied to a supported target or feature.
- Test each supported target and meaningful conditional branch.
- Do not let untested target-specific code silently compile only in a different environment.
- Define the lowest supported language/API surface for shared source.
- Record platform and runtime differences that affect consumers.

## Restore and build integrity

- Use approved package sources and prevent unintended fallback sources.
- Preserve signature, checksum, provenance, or repository controls available to the environment.
- Keep credentials out of package-source configuration committed to the repository.
- Verify restore, compile, tests, and packaging from a clean checkout or equivalent controlled state for release claims.
- Detect generated or formatted drift in CI.

## Evidence

Record resolved tool versions, effective properties, restore sources, lock status, new dependency rationale, license/security review, analyzer/generator changes, supported target builds, deterministic-generation results, and checks not run.
