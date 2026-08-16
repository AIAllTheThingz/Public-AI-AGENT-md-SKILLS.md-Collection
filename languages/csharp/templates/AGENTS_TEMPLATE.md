---
id: CSHARP-TEMPLATE-AGENT-001
title: C# Project Agent Template
version: 0.1.0
status: stable
---

# C# Project Agent Instructions

## Inherited standards

This project adopts the Public-Access-Agents C# package at the recorded repository version or commit. It also adopts the .NET package when SDK, target framework, CLR, MSBuild, NuGet, application model, or publishing behavior is in scope.

Project-specific rules may strengthen inherited requirements but must not silently weaken them.

## Declared boundary

Record:

- C# package source version or commit
- SDK/compiler and effective language version
- target frameworks, runtimes, operating systems, and architectures
- nullable, warning, analyzer, formatter, generator, and unsafe-code settings
- supported consumers and public/serialized contracts
- build, test, package, publish, and security commands
- dependency sources and lock strategy
- framework, platform, discipline, and profile overlays

## Required behavior

- Preserve the declared compiler and compatibility boundary unless migration is explicitly requested.
- Do not use `LangVersion=latest` or unapproved preview features.
- Honor nullable analysis and avoid broad diagnostic suppression.
- Propagate cancellation, bound concurrency, and own every started task.
- Dispose only owned resources and test cleanup on failure/cancellation.
- Validate untrusted input and protect secrets and sensitive diagnostics.
- Review public API, serialization, generated-code, reflection, native, and unsafe impacts.
- Add meaningful tests and report exact validation evidence.

## Project commands

Replace this section with the repository's real, pinned commands for restore, format, analysis, build, test, compatibility, dependency/security, package, publish, and runtime validation.

## Completion

Report changed files and contracts, toolchain, security and compatibility impact, exact command results, checks not run, limitations, residual risks, and required reviewers.
