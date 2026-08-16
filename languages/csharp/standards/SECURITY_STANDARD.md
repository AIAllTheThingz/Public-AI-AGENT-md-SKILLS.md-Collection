---
id: CSHARP-SECURITY-001
title: C# Security Standard
version: 0.1.0
status: stable
---

# C# Security Standard

## Purpose

Require secure defaults at C# trust boundaries and prohibit common implementation shortcuts that create injection, disclosure, deserialization, cryptographic, or authorization risk.

## Trust boundaries

Identify and validate data entering from HTTP, messaging, files, configuration, environment variables, command lines, databases, native code, serialization, reflection, plugins, remote services, user interfaces, and generated sources.

Validation must cover type, length, range, format, allowed values, encoding, canonical form, authorization, resource cost, and operational safety as applicable. Validation is not authorization.

## Secrets and sensitive data

- Do not embed credentials, tokens, private keys, connection strings, certificate material, or production identifiers in source, tests, examples, generated files, attributes, or defaults.
- Acquire secrets through an approved provider and minimize lifetime and access.
- Do not put secrets in process arguments, exception text, structured log properties, metrics, traces, test snapshots, dumps, or CI artifacts.
- Redact before data reaches a logger or serializer; do not rely only on a downstream sink.
- Clear mutable buffers containing sensitive data when the threat model requires it.

## Injection and process execution

- Use parameterized database APIs and structured command arguments.
- Do not construct shell command text from untrusted input or invoke a shell when direct process arguments suffice.
- Validate executable identity, working directory, environment, argument boundaries, timeout, exit code, and output limits.
- Treat stdout and stderr as untrusted and potentially sensitive.
- Do not compile, evaluate, reflectively invoke, or dynamically load untrusted code.

## Paths and files

- Normalize and validate paths against an allowed root before file access.
- Reject traversal, alternate data streams where relevant, unsafe links, ambiguous encodings, and unexpected device or network paths according to platform risk.
- Use exclusive creation or atomic replacement when race conditions matter.
- Enforce size, count, type, and decompression limits before processing uploads or archives.
- Do not trust an extension or content type as proof of content.

## Serialization

- Use serializers with an explicit schema or bounded known types.
- Do not enable arbitrary type metadata or instantiate attacker-selected runtime types.
- Limit depth, size, collection counts, recursion, and processing time for untrusted data.
- Validate deserialized objects before use and do not assume constructors or invariants ran as expected.
- Avoid obsolete or unsafe binary serialization mechanisms.

## Cryptography and transport

- Use platform cryptography and reviewed protocols; do not invent algorithms or modes.
- Use cryptographically secure randomness for secrets and security tokens.
- Authenticate encrypted data where the selected construction requires it.
- Define key generation, storage, access, rotation, revocation, and disposal outside ordinary source code.
- Do not disable TLS or certificate validation, accept every certificate, or weaken hostname verification.
- Compare authentication material using appropriate fixed-time mechanisms where timing exposure is material.

## Authentication and authorization

- Enforce authorization at the operation and resource boundary, not only in UI, routing, or caller convention.
- Distinguish unauthenticated, unauthorized, not found, conflict, and validation outcomes without leaking sensitive existence data.
- Do not infer authorization from possession of an identifier or successful model binding.
- Apply least privilege to filesystem, process, network, database, native, and cloud access.

## Denial of service and concurrency

- Bound input, parsing, regular expressions, memory, recursion, parallelism, queues, retries, and external calls.
- Use timeouts and cancellation at remote and long-running boundaries.
- Avoid catastrophic regular expressions; use generated/nonbacktracking options or timeouts when appropriate and supported.
- Prevent attacker-controlled keys from creating unbounded cache or telemetry cardinality.

## Analyzer and dependency findings

- Run configured compiler and security analyzers and review dependency vulnerabilities.
- Do not broadly suppress findings. A suppression must identify scope, invariant, risk, owner, and review condition.
- Treat generated code and analyzer/source-generator packages as supply-chain inputs.

## Exceptions

Any exception to this standard requires explicit authorization, threat/risk analysis, minimized scope, compensating controls, tests, an owner, and a time or condition for re-review.

## Evidence

Record trust boundaries, validation and authorization tests, secret/redaction review, analyzer results, dependency findings, process/path/deserialization checks, cryptographic decisions, suppressions, and residual risks.
