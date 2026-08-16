---
id: CSHARP-CODE-001
title: C# Coding Standard
version: 0.1.0
status: stable
---

# C# Coding Standard

## Purpose

Define language-level requirements for readable, analyzable, maintainable, and behaviorally explicit C# code.

## Structure and scope

- Follow the repository's established namespaces, file organization, naming, and formatting before introducing a new convention.
- Keep types and members focused on one coherent responsibility. Split code when ownership or change reasons differ, not merely to reduce line count.
- Prefer the narrowest useful accessibility. Do not expose implementation types by default.
- Keep mutable state local and private. Avoid global state, mutable statics, ambient context, and hidden service location.
- Use partial types only for generated/framework composition or a documented separation that tooling understands.
- Do not place substantial work in type initializers, property getters, module initializers, or constructors when callers cannot observe or control failure.

## Language features

- Use language features supported by the resolved compiler and target boundary.
- Prefer clear pattern matching, switch expressions, records, primary constructors, collection expressions, and other modern syntax only when they improve the actual contract.
- Do not convert established code to newer syntax without a requirement, material clarity benefit, or migration scope.
- Avoid clever operator overloads, implicit conversions, custom awaiters, metaprogramming, and reflection when ordinary members express behavior more clearly.
- Use `var` according to the repository convention and only when the type remains evident or repetition obscures intent.
- Avoid tuples in durable public contracts when named types provide clearer semantics and versioning.

## Methods and control flow

- Validate public and trust-boundary inputs before side effects.
- Use guard clauses when they make invalid preconditions explicit.
- Keep side effects visible in method names, return values, and documentation.
- Avoid boolean parameter lists that hide meaning; use named options or types when combinations form a domain contract.
- Prefer total handling for closed sets. If an enum or discriminated domain can evolve, define and test unknown-value behavior.
- Do not catch exceptions that cannot be handled meaningfully.
- Do not use exceptions for routine branching or return sentinel values whose meaning is undocumented.
- Preserve original exception context when translating errors and keep sensitive values out of exception messages.

## Collections and LINQ

- Select collection interfaces by required semantics, not habit.
- Do not return a mutable internal collection through a public contract.
- Be explicit about ordering, uniqueness, case comparison, equality, and duplicate behavior.
- Avoid repeated enumeration of lazy or remote sequences when it changes performance or behavior.
- Do not hide network, database, file, or high-cost work behind an apparently in-memory `IEnumerable<T>` contract.
- Avoid unbounded materialization and unbounded `GroupBy`, `ToList`, or `ToDictionary` operations on external input.
- Use explicit comparers for identifiers, paths, protocol values, or case-insensitive keys where culture-independent behavior is required.

## Values, time, and numbers

- Use invariant, ordinal, or explicitly selected culture semantics at machine boundaries.
- Use UTC or an explicit offset for durable timestamps. Inject a time provider when deterministic behavior matters.
- Define units in names or types. Do not pass ambiguous numeric durations, sizes, percentages, or identifiers.
- Select `decimal` for base-10 business precision and floating-point types for measured/scientific values based on actual requirements.
- Use checked arithmetic when overflow would violate a security, financial, allocation, indexing, or protocol invariant.
- Do not use mutable current culture, current directory, environment, or machine state as an undocumented dependency.

## Equality and immutability

- Define identity, value equality, ordering, and hashing consistently.
- Do not mutate values used as dictionary keys or set members.
- Prefer immutable data across threads and public boundaries where mutation has no clear owner.
- Validate record-generated equality against domain identity; records are not automatically correct entities.
- Keep `Equals`, `GetHashCode`, and equality operators consistent when customized.

## Comments and generated code

- Explain non-obvious invariants, compatibility constraints, security decisions, concurrency ownership, and failure behavior.
- Do not narrate self-evident syntax or preserve obsolete commented-out code.
- Mark generated files through the repository's recognized mechanism and regenerate them from committed inputs.
- Do not hand-edit generated output unless the generator contract explicitly requires it.

## Review evidence

Record formatting and analyzer results, effective language version, warnings introduced or suppressed, public surface changes, behavior tests, and any intentionally retained complexity.
