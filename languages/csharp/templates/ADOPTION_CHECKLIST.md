---
id: CSHARP-TEMPLATE-ADOPT-001
title: C# Adoption Checklist
version: 0.1.0
status: stable
---

# C# Adoption Checklist

## Toolchain and composition

- [ ] C# package source version or commit is recorded
- [ ] SDK/compiler, effective C# version, target frameworks/hosts, runtimes, platforms, and architectures are declared
- [ ] `LangVersion` uses the target default or an explicit supported stable value, not `latest`
- [ ] Preview features and tools are absent or explicitly approved with migration/support limits
- [ ] .NET, framework, discipline, platform, and profile packages are composed where applicable
- [ ] Local and CI compiler/tool resolution is aligned or differences are documented

## Language contracts

- [ ] Nullable context and suppression policy are defined
- [ ] Public APIs, serialized shapes, generic constraints, defaults, exceptions, cancellation, and compatibility surfaces are inventoried
- [ ] Required/optional state, equality, ordering, culture, time, units, and numeric behavior are explicit
- [ ] Async task ownership, cancellation, timeout, concurrency, backpressure, retry, and shutdown behavior are defined
- [ ] Resource ownership and synchronous/asynchronous disposal are defined
- [ ] Reflection, dynamic, generated, trimming/AOT, native, unsafe, and performance-sensitive boundaries are inventoried

## Security and supply chain

- [ ] Trust boundaries and validation/authorization rules are defined
- [ ] Secret sources and diagnostic redaction are documented
- [ ] Process, path, file, deserialization, cryptography, certificate, and remote-call controls are defined where applicable
- [ ] Package, analyzer, generator, and tool sources/versions are approved and constrained
- [ ] Restore locking, generated-file determinism, and vulnerability review are configured

## Validation and evidence

- [ ] Formatting, analyzer, build, test, compatibility, security, package/publish, and runtime commands are real and documented
- [ ] Tests cover negative, cancellation, concurrency, cleanup, compatibility, and security behavior appropriate to risk
- [ ] Supported target/platform branches are validated or explicitly excluded
- [ ] Documentation and examples use fictitious nonsensitive values
- [ ] Completion evidence and required C#/.NET specialist review are integrated
