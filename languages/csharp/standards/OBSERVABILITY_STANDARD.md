---
id: CSHARP-OBS-001
title: C# Observability Standard
version: 0.1.0
status: stable
---

# C# Observability Standard

## Purpose

Define language-level diagnostic behavior that supports operations without leaking sensitive data or changing program contracts accidentally.

## Structured diagnostics

- Use structured properties with stable names and types.
- Keep presentation formatting out of reusable domain logic.
- Include correlation context at owned boundaries and propagate it through asynchronous work where applicable.
- Use appropriate severity and avoid duplicate logging of the same exception at every layer.
- Preserve exception context without returning internal stack traces or secrets to untrusted callers.

## Data control

- Classify log, metric, trace, event, dump, and diagnostic payloads.
- Do not record credentials, tokens, cookies, authorization headers, connection strings, certificate secrets, full sensitive objects, or regulated data.
- Redact before emission and test the redaction path.
- Bound message size, collection expansion, exception serialization, and telemetry cardinality.
- Do not use user-controlled values as metric names or unbounded dimensions.

## Async and operation state

- Distinguish success, unchanged, skipped, validation failure, authorization refusal, cancellation, timeout, partial failure, execution failure, and unknown outcome.
- Record start/end UTC timestamps and duration for material operations.
- Preserve task/job/request identifiers without exposing sensitive session values.
- Do not report success until actual-state verification required by the operation is complete.

## Performance

- Avoid expensive message construction when the diagnostic level is disabled.
- Do not add synchronous blocking I/O to hot or asynchronous paths for logging.
- Measure high-volume diagnostic overhead and apply sampling deliberately.
- Keep source-generated logging or other optimized paths synchronized with the documented event contract.

## Evidence

Record events and properties added or changed, redaction tests, cardinality/volume assessment, correlation behavior, failure-state coverage, and operational dashboards or alerts affected when applicable.
