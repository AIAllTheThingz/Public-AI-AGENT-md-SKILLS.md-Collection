---
id: CSHARP-TEST-001
title: C# Testing Standard
version: 0.1.0
status: stable
---

# C# Testing Standard

## Purpose

Require C# tests that validate externally meaningful behavior, failure semantics, compatibility, and difficult language/runtime boundaries.

## Test strategy

- Map tests to acceptance criteria, contracts, risks, and regressions.
- Use unit tests for pure behavior and controlled boundaries; use integration or contract tests when framework, serializer, database, filesystem, network, native, generator, or runtime fidelity matters.
- Keep tests deterministic, isolated, parallel-safe, and independent of production systems.
- Do not weaken an assertion, remove a test, or over-mock the behavior merely to obtain a pass.
- Avoid tests that duplicate implementation steps without testing a stable result.

## Required behavior coverage

As applicable, cover:

- normal and boundary behavior
- null, empty, malformed, duplicate, oversized, and hostile input
- authorization denied and sensitive-data redaction
- exception type/context and partial failure
- cancellation before and during work
- timeout and unknown external outcome
- bounded concurrency, races, ordering, backpressure, and shutdown
- owned-resource disposal on success, failure, and cancellation
- serialization round trip and forward/backward compatibility
- public API and generic/nullability contracts
- culture, time zone, clock, numeric, path, and platform differences
- generated-code and analyzer behavior
- reflection, trimming/AOT, native interop, and unsafe boundaries
- idempotent rerun or documented recovery for side effects

## Test design

- Use clear arrange/act/assert or equivalent structure without obscuring intent.
- Name tests by observable condition and result.
- Prefer deterministic clocks, identifiers, random seeds, and synchronization hooks.
- Do not use arbitrary sleeps as the primary concurrency coordination mechanism.
- Keep fixtures minimal and synthetic. Do not copy production secrets or sensitive datasets.
- Assert structured results and state, not incidental log text, unless the log contract itself is under test.
- Verify mocks/fakes preserve the boundary semantics important to the test; a fake that cannot fail is not evidence for failure handling.

## Compatibility and generated code

- Compare public API or serialized contracts when a shared library or durable payload changes.
- Test every supported target framework/platform branch or disclose the untested target.
- Regenerate source and compare deterministic output where generators are used.
- Test reflection-discovered members, linker preservation, or AOT behavior when those mechanisms are supported contracts.

## Coverage and mutation

Coverage percentages are diagnostics, not proof. Use risk-based coverage and inspect untested branches around security, errors, cancellation, compatibility, and cleanup.

Mutation or property-based testing may strengthen evidence for parsers, validators, algorithms, and invariants, but it does not replace representative integration or contract tests.

## Validation sequence

Run focused tests during implementation, then the repository's complete applicable suite against the final revision. Compile test projects with the intended warnings/analyzers and record exact filters, configurations, target frameworks, and environments.

## Evidence

Report test files changed, behavior and risks covered, exact commands, counts/results, flakes/retries, excluded categories, environment dependencies, checks not run, and what the tests do not prove.
