---
id: CSHARP-DOC-001
title: C# Documentation Standard
version: 0.1.0
status: stable
---

# C# Documentation Standard

## Purpose

Document C# contracts, decisions, safety boundaries, and operational behavior so maintainers and consumers do not need to reverse engineer intent.

## XML documentation

Document public APIs according to repository policy. Documentation must explain the contract rather than restate the identifier.

Include as applicable:

- purpose and observable behavior
- type parameter, parameter, return, and nullability semantics
- units, ranges, formats, ordering, and duplicate behavior
- exceptions callers are expected to handle
- cancellation and timeout behavior
- thread safety, concurrency, ownership, and disposal
- enumeration and deferred-execution behavior
- security, authorization, and sensitive-data constraints
- platform, runtime, language, trimming/AOT, and native limitations
- examples for non-obvious use

Keep `<param>`, `<typeparam>`, `<returns>`, `<exception>`, `<remarks>`, and `<example>` content synchronized with code.

## Inline comments

Use comments for non-obvious invariants, algorithm choices, race prevention, compatibility constraints, suppression justification, protocol behavior, unsafe/native assumptions, and measured performance tradeoffs.

Do not narrate syntax, preserve dead commented code, or add comments that contradict compiler-visible contracts.

## Repository documentation

Update relevant README, architecture decisions, API references, migration notes, configuration guidance, runbooks, and examples when behavior changes.

Document:

- supported SDK/compiler, language version, target frameworks, runtimes, platforms, and architectures
- build, format, analyze, test, package, publish, and security commands
- public or serialized compatibility changes
- dependencies, analyzers, generators, scripts, and native prerequisites
- configuration and secret sources without secret values
- failure, recovery, rollback, and support boundaries
- generated-file ownership and regeneration commands

## Examples

- Use fictitious values and non-production endpoints.
- Make safety mode and side effects visible.
- Ensure examples compile or clearly label pseudocode/non-executable fragments.
- Do not demonstrate certificate bypass, hardcoded credentials, unvalidated input, arbitrary command execution, or insecure deserialization.
- Keep examples compatible with the documented compiler boundary.

## Evidence

Report documentation changed, generated API documentation checks, example validation, unresolved documentation gaps, and any behavior that remains intentionally undocumented for security reasons.
