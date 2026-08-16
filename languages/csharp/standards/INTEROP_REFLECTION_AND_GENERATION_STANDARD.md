---
id: CSHARP-INTEROP-001
title: C# Interop, Reflection, and Generation Standard
version: 0.1.0
status: stable
---

# C# Interop, Reflection, and Generation Standard

## Purpose

Control C# mechanisms that bypass ordinary static contracts, cross native boundaries, or produce executable source at build/runtime.

## Selection gate

Use reflection, `dynamic`, expression compilation, source generation, runtime code generation, native interop, or unsafe code only when a supported requirement cannot be met more safely and simply with ordinary typed code.

Record the requirement, rejected alternatives, scope, supported environments, failure behavior, security impact, and specialist-review need.

## Reflection and dynamic behavior

- Restrict discovery to an explicit assembly/type/member boundary.
- Do not instantiate or invoke attacker-selected types or members.
- Validate signatures, accessibility, attributes, generic constraints, nullability, and expected ownership before invocation.
- Define trimming and AOT behavior; reflection success in an untrimmed development build is insufficient.
- Cache metadata only with bounded lifetime and correct unload/context behavior.
- Translate reflection exceptions without losing the underlying failure context.
- Avoid `dynamic` where a generic, interface, union, adapter, or generated contract can be statically checked.

## Source generators and analyzers

- Treat generators and analyzers as executable build dependencies.
- Pin their versions and review provenance, inputs, diagnostics, and generated public surface.
- Generate deterministic output from controlled inputs.
- Validate escaping, identifiers, namespaces, nullability, encoding, and hostile metadata used in generated source.
- Report generator diagnostics and do not broadly disable them without an evidence-backed exception.
- Test both generation success and diagnostic/failure cases.

## Expression and runtime code generation

- Do not compile untrusted expressions, templates, or source.
- Bound expression complexity and inputs when expressions are constructed from external metadata.
- Prefer interpretation or predeclared operations when dynamic compilation is unavailable under AOT or restricted hosts.
- Define cache, unload, memory, concurrency, and failure behavior.

## Native interop

- Prefer maintained managed APIs or `SafeHandle` over raw handles and pointers.
- Verify calling convention, character encoding, layout, packing, ownership, pinning, lifetime, error propagation, and platform architecture.
- Use source-generated interop when supported and appropriate, but review generated/native boundaries.
- Do not marshal unbounded attacker-controlled buffers.
- Capture native error state at the correct boundary before another call overwrites it.
- Test supported operating systems and architectures or explicitly narrow support.

## Unsafe code

- Keep `unsafe` blocks and pointer arithmetic in the smallest reviewed boundary.
- Validate lengths, offsets, alignment, overflow, aliasing, lifetime, and pinning.
- Use checked arithmetic where integer wrap could escape a buffer or violate layout.
- Do not return references, spans, or pointers beyond the lifetime of their storage.
- Add fuzz, property, boundary, and platform tests proportionate to memory-safety risk.

## Evidence

Record the boundary, rationale, dependency and platform versions, generated/native artifacts, trimming/AOT results, hostile-input tests, memory/lifetime analysis, failure behavior, and independent specialist review when required.
