---
id: CSHARP-TYPE-001
title: C# Type System and Nullability Standard
version: 0.1.0
status: stable
---

# C# Type System and Nullability Standard

## Purpose

Use C# types, generics, nullable analysis, and equality semantics to make contracts explicit and prevent invalid or ambiguous state.

## Nullable reference types

- Enable nullable reference analysis for new code and preserve or deliberately migrate existing nullable contexts.
- Treat nullable annotations as part of the source contract. `T` and `T?` must match real required/optional behavior.
- Resolve nullable warnings through correct initialization, validation, flow, annotations, or API design.
- Use the null-forgiving operator only where a local invariant proves the compiler is missing information. Document non-obvious uses.
- Do not place broad `#nullable disable`, warning suppression, or analyzer exclusion around code merely to silence migration work.
- Model oblivious third-party, reflection, serializer, native, and generated boundaries explicitly and validate values when they enter analyzed code.
- Use nullable analysis attributes only when their declared relationship is true for every supported path.

## Required initialization

- Use constructors, factory methods, or required members according to the actual initialization contract.
- Do not use `default!` as a general substitute for initialization.
- Framework-created types may use narrowly scoped suppression only when lifecycle tests prove initialization before access.
- Keep deserialization and object-mapping behavior aligned with required members and nullable annotations.

## Generics

- Use the narrowest correct generic constraints and preserve them as compatibility surfaces.
- Avoid generic abstraction when supported types are closed and a simpler explicit contract is clearer.
- Do not rely on runtime casts to enforce constraints that the type system can express.
- Define variance deliberately for public interfaces and delegates.
- Document ownership, nullability, lifetime, and thread-safety expectations of generic parameters when they affect correctness.

## Value and reference semantics

- Choose class, struct, record class, or record struct from identity, mutability, copying, size, boxing, and equality requirements.
- Keep nontrivial structs small, immutable where practical, and safe under copying.
- Do not use mutable structs in public APIs or asynchronous state without a documented necessity.
- Treat `ref`, `in`, `out`, `ref struct`, and `scoped` lifetimes as advanced contracts that require tests and clear ownership.
- Do not allow ref-like values to escape their valid lifetime or cross unsupported async, iterator, boxing, or heap boundaries.

## Domain modeling

- Use dedicated types for values with validation, units, sensitivity, or distinct identity when primitive interchange would permit invalid combinations.
- Validate at creation and prevent partially valid instances from escaping.
- Do not use enums as unchecked integers. Define unknown, persisted, and forward-compatible behavior.
- Use discriminated modeling patterns that force exhaustive handling when the domain is closed.
- Avoid inheritance when composition or a closed union better expresses the valid state space.

## Equality and comparison

- State whether equality is identity, structural value, key-based, reference, ordinal, culture-aware, or domain-specific.
- Use stable hash inputs for values placed in hash collections.
- Keep comparer behavior consistent across validation, lookup, persistence, serialization, and authorization.
- Do not use culture-sensitive comparison for protocol tokens, identifiers, security decisions, file extensions, or configuration keys unless the protocol explicitly requires it.

## Migration evidence

Nullable or type-model migration must record the starting warning baseline, incremental boundary, suppressions, public annotation changes, serializer/framework effects, consumer compatibility, and tests proving runtime behavior remains correct.
