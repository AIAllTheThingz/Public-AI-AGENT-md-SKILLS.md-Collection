---
id: CSHARP-ASYNC-001
title: C# Async and Concurrency Standard
version: 0.1.0
status: stable
---

# C# Async and Concurrency Standard

## Purpose

Define safe ownership, cancellation, timeout, synchronization, and bounded-execution behavior for asynchronous and concurrent C# code.

## Asynchronous contracts

- Use `Task` or `Task<T>` for asynchronous operations unless streaming or allocation evidence justifies another abstraction.
- Use `ValueTask` only where profiling and consumption rules justify its additional contract complexity.
- Name asynchronous methods with the established `Async` suffix except where a framework contract dictates otherwise.
- Do not use `async void` except for event handlers required by a framework. Route their failure to an owned boundary.
- Do not block asynchronous code with `.Result`, `.Wait()`, or `.GetAwaiter().GetResult()` in normal application paths.
- Do not wrap naturally asynchronous I/O in `Task.Run`.
- Do not hide synchronous blocking work behind an asynchronous signature.

## Cancellation and deadlines

- Accept and propagate `CancellationToken` through genuinely cancellable operations.
- Check cancellation before consequential side effects and inside bounded long-running CPU loops where appropriate.
- Preserve cancellation as cancellation; do not report `OperationCanceledException` as an ordinary fault when the expected token caused it.
- Distinguish caller cancellation, application shutdown, and timeout in result and telemetry semantics.
- Define deadlines around external calls and waits. Do not rely on infinite defaults.
- After a timeout, treat server-side or background work as potentially continuing unless the underlying system confirms cancellation.

## Task ownership

- Every started task must have an owner responsible for awaiting, observing failure, cancellation, shutdown, and cleanup.
- Fire-and-forget work requires an explicit supervised queue or host lifecycle; discarding a task is not supervision.
- Do not let a scoped dependency escape into background work beyond its valid lifetime.
- Aggregate and report partial results without losing individual failures.
- Preserve structured concurrency where the parent operation owns its child work.

## Bounded concurrency

- Derive concurrency limits from downstream capacity, memory, rate limits, thread safety, and workload impact.
- Do not start unbounded tasks from unbounded input.
- Bound channels, queues, buffers, batches, retries, and producer/consumer imbalance.
- Define backpressure or rejection behavior when capacity is exhausted.
- Avoid holding locks across `await`.
- Use synchronization primitives that match the ownership model; do not lock publicly reachable objects or strings.

## Shared state

- Prefer immutability, message passing, partitioning, and ownership over shared mutation.
- Document thread safety for shared types and public members.
- Use concurrent collections only when their individual operation semantics satisfy the complete invariant.
- Protect compound read-modify-write behavior explicitly.
- Do not assume `volatile` makes a multi-step invariant atomic.
- Use interlocked operations only where the memory and state transition semantics are understood and tested.

## Async streams and channels

- Propagate cancellation into `IAsyncEnumerable<T>` production and consumption.
- Define enumeration ownership, disposal, single/multiple enumeration behavior, errors, and partial output.
- Bound channel capacity unless unbounded growth is proven safe.
- Complete channels on terminal producer outcomes and ensure consumers cannot wait forever after failure.
- Do not expose a hot or one-shot sequence through a contract that appears repeatable without documentation.

## Retries

- Retry only failures classified as transient and operations safe for repetition.
- Bound attempts, elapsed time, and concurrent retries.
- Add jitter where synchronized retry storms are possible.
- Revalidate state before retrying a non-idempotent or externally visible operation.
- Preserve the original failure and each retry outcome in structured evidence.

## Testing

Use deterministic synchronization rather than timing sleeps where practical. Test cancellation before and during work, timeout, race-sensitive invariants, bounded concurrency, channel completion, task failure observation, shutdown, resource cleanup, and partial results.

Do not claim thread safety from a single successful run. Use stress, repeated, or model-based checks proportionate to risk and disclose nondeterministic limitations.
