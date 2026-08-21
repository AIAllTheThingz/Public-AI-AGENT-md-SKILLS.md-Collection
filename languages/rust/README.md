---
id: RUST-PKG-001
status: baseline
title: Rust Package
---

# Rust Language Package

This package provides project-agnostic engineering standards for Rust crates, workspaces, services, command-line tools, reusable libraries, systems components, and FFI boundaries.

It defines how coding agents should inspect, design, implement, test, secure, document, package, and report Rust work. It does not choose an async runtime, web framework, target platform, or production architecture for the adopting project.

## Package status

**Status:** `baseline`

The package is structurally complete and suitable for adoption. Projects must tailor toolchain, target, feature, unsafe-code, deployment, and organization-specific requirements before treating it as a final production standard.

## Intended scope

- Rust crates and workspaces
- services and command-line tools
- reusable libraries and public crates
- systems and platform components
- FFI and unsafe-code boundaries
- tests, examples, benchmarks, fuzzing, and Cargo metadata

## Runtime and toolchain baseline

- Declare a supported stable Rust toolchain.
- Define a minimum supported Rust version where compatibility matters.
- Use Cargo-managed builds and an explicit lockfile policy.
- Enforce `rustfmt` and `clippy` according to repository policy.
- Declare supported targets, operating systems, architectures, and feature combinations.

## Package structure

| Path | Purpose |
|---|---|
| [`AGENTS.md`](AGENTS.md) | Mandatory Rust-specific operating rules |
| [`MANIFEST.md`](MANIFEST.md) | Package inventory and adoption checklist |
| [`standards/`](standards/) | Coding, Cargo, ownership, unsafe, architecture, security, testing, and evidence standards |
| [`templates/`](templates/) | Adoption templates |
| [`examples/`](examples/) | Example package composition |

## Required standards

| Standard | Governs |
|---|---|
| [`RUST_CODING_STANDARD.md`](standards/RUST_CODING_STANDARD.md) | Language structure, errors, APIs, traits, ownership, and maintainability |
| [`ARCHITECTURE_STANDARD.md`](standards/ARCHITECTURE_STANDARD.md) | Crate boundaries, dependencies, features, configuration, and side effects |
| [`DOCUMENTATION_STANDARD.md`](standards/DOCUMENTATION_STANDARD.md) | rustdoc, public APIs, examples, safety notes, and operator guidance |
| [`TESTING_STANDARD.md`](standards/TESTING_STANDARD.md) | Unit, integration, documentation, property, and platform testing |
| [`SECURITY_STANDARD.md`](standards/SECURITY_STANDARD.md) | Untrusted input, safety assumptions, secrets, cryptography, and secure defaults |
| [`DEPENDENCY_MANAGEMENT_STANDARD.md`](standards/DEPENDENCY_MANAGEMENT_STANDARD.md) | Crates, features, provenance, audits, updates, and lockfiles |
| [`OBSERVABILITY_STANDARD.md`](standards/OBSERVABILITY_STANDARD.md) | Diagnostics, metrics, tracing, context, and sensitive-data controls |
| [`CARGO_STANDARD.md`](standards/CARGO_STANDARD.md) | Workspaces, profiles, features, build scripts, and release configuration |
| [`OWNERSHIP_UNSAFE_STANDARD.md`](standards/OWNERSHIP_UNSAFE_STANDARD.md) | Ownership design, interior mutability, unsafe code, FFI, and invariants |
| [`COMPLETION_EVIDENCE.md`](standards/COMPLETION_EVIDENCE.md) | Proof required before completion claims |

## Adoption procedure

1. Inventory crates, workspaces, features, targets, build scripts, proc macros, tests, and release artifacts.
2. Declare the toolchain channel, minimum supported Rust version, and target platforms.
3. Define workspace, crate, feature, public API, and FFI boundaries.
4. Define formatting, linting, test, documentation, benchmark, fuzz, audit, and build commands.
5. Define unsafe-code policy and required safety documentation.
6. Define async runtime, cancellation, shutdown, thread, and synchronization behavior where applicable.
7. Add applicable discipline, framework, platform, virtualization, operating-system, networking, and project-profile overlays.
8. Review build scripts, proc macros, native dependencies, and executable tooling.
9. Run repository and package validation.
10. Review the composed standard with an accountable Rust maintainer.

## Project tailoring checklist

- [ ] Toolchain, minimum supported Rust version, and targets are declared.
- [ ] Workspace, crate, feature, and public API boundaries are documented.
- [ ] Dependency, feature, source, audit, and lockfile policies are defined.
- [ ] Unsafe code, FFI, native libraries, and safety-invariant requirements are defined.
- [ ] Async runtime, cancellation, shutdown, and concurrency behavior are defined.
- [ ] Test, documentation-test, fuzz, benchmark, sanitizer, and platform expectations are defined.
- [ ] Logging, metrics, tracing, diagnostics, and redaction are defined.
- [ ] Packaging, release, deployment, rollback, and compatibility requirements are defined.

## Rust-specific safety expectations

- Unsafe code requires a narrow boundary, documented invariants, and targeted tests.
- Every `unsafe` block should explain the safety conditions it relies on.
- Avoid `unwrap` and `expect` in recoverable production paths without explicit rationale.
- Treat feature combinations as compatibility surfaces and test them deliberately.
- Build scripts and proc macros are executable supply-chain dependencies.
- Review FFI ownership, lifetimes, thread safety, error mapping, and cleanup explicitly.

## Validation baseline

Use repository-defined commands when available:

```bash
rustc --version
cargo fmt --check
cargo clippy --all-targets --all-features -- -D warnings
cargo test --all-features
cargo audit
```

Only run `cargo audit` when the tool is configured and available. Add documentation tests, target builds, feature-matrix tests, fuzzing, benchmarks, and sanitizer checks as required.

## Testing expectations

Tests should cover expected behavior, invalid input, error propagation, resource cleanup, feature combinations, concurrency, unsafe boundaries, FFI, supported targets, and public API compatibility.

## Completion evidence

A completion report must identify files and crates changed, public API and feature changes, unsafe or FFI impact, dependency and compatibility impact, validation commands and results, checks not run, documentation updated, limitations, and remaining risk.

## Templates and examples

- [`AGENTS_TEMPLATE.md`](templates/AGENTS_TEMPLATE.md)
- [`ADOPTION_CHECKLIST.md`](templates/ADOPTION_CHECKLIST.md)
- [`ADOPTION_EXAMPLE.md`](examples/ADOPTION_EXAMPLE.md)

## What this package does not decide

The adopting repository must still define business requirements, runtime architecture, supported targets, deployment environments, identity, data ownership, incident response, release management, backup, recovery, and organization-specific compliance.

This package improves agent behavior. It does not guarantee that generated Rust software is secure, correct, compliant, or production ready.

## Authoritative starting points

- [The Rust Reference](https://doc.rust-lang.org/reference/)
- [Rust standard library](https://doc.rust-lang.org/std/)
- [The Cargo Book](https://doc.rust-lang.org/cargo/)
- [The rustc Book](https://doc.rust-lang.org/rustc/)

Revalidate current Rust, toolchain, standard library, Cargo, security, and support behavior before relying on version-specific guidance.
