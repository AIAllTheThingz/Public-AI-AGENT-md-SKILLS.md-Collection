---
id: CSHARP-RESOURCE-001
title: C# Resource and Performance Standard
version: 0.1.0
status: stable
---

# C# Resource and Performance Standard

## Purpose

Define ownership, deterministic cleanup, allocation, pooling, and evidence requirements for resource- or performance-sensitive C# code.

## Resource ownership

- State whether a stream, handle, client, buffer, enumerator, registration, timer, scope, or other disposable is owned or borrowed.
- The creator normally owns disposal unless the API explicitly transfers ownership.
- Dispose owned `IDisposable` and `IAsyncDisposable` instances on success, failure, and cancellation.
- Do not dispose borrowed dependencies, shared clients, injected singletons, or objects whose lifetime belongs to another scope.
- Use `using`/`await using` when lexical scope matches ownership; otherwise make lifecycle explicit and test it.
- Preserve the primary exception when cleanup also fails, and report cleanup failure without hiding either outcome.

## Streams and buffers

- Define stream position, seekability, readability/writability, ownership, and maximum size.
- Avoid reading untrusted or remote streams fully into memory without a validated limit.
- Return rented buffers in `finally`, clear them first when they held sensitive data, and never use them after return.
- Do not expose pooled memory beyond its valid lease.
- Use `Span<T>`, `Memory<T>`, sequences, and pipelines only when lifetime and async boundaries are correct.

## Performance decisions

- Establish a representative baseline before optimizing nontrivial code.
- Measure throughput, latency distribution, allocation, memory high-water mark, CPU, I/O, and contention as applicable.
- Optimize the observed bottleneck, not a stylistic preference.
- Preserve readability and correctness unless the measured benefit and operational requirement justify complexity.
- Record workload, data shape, runtime, platform, warmup, iteration method, and variance for benchmark claims.
- Do not generalize microbenchmark results to end-to-end production behavior without representative validation.

## Allocation and lifetime

- Avoid accidental retention through static events, closures, caches, task continuations, long-lived scopes, and unbounded collections.
- Bound caches and define eviction, expiration, concurrency, and sensitive-data behavior.
- Do not pool objects with complex ownership or secret state unless reset and isolation are proven.
- Avoid finalizers unless directly owning an unmanaged resource and following a reviewed safe-handle pattern.
- Prefer `SafeHandle` or an established managed owner for native handles.

## High-performance features

Use ref-like types, stack allocation, pooling, SIMD, source generation, custom serializers, or unsafe memory only when:

- a measured requirement exists
- supported runtime/platform boundaries are explicit
- ownership and lifetime are locally reviewable
- malformed and boundary inputs are tested
- fallback or failure behavior is defined
- the optimization is benchmarked and regression-protected

Stack allocation and buffer sizes must be bounded. Do not derive large stack allocations directly from untrusted input.

## Evidence

Record ownership decisions, disposal tests, allocation or leak analysis, benchmark method and results, supported platforms, regression thresholds, and complexity that remains intentionally.
