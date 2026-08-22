---
id: GO-PKG-001
status: baseline
title: Go Package
---

# Go Language Package

This package provides project-agnostic engineering standards for Go services, command-line tools, reusable libraries, modules, workspaces, and concurrent systems.

It defines how coding agents should inspect, design, implement, test, secure, document, package, and report Go work. It does not choose a web framework, RPC framework, deployment platform, or production architecture for the adopting project.

## Package status

**Status:** `baseline`

The package is structurally complete and suitable for adoption. Projects must tailor toolchain, module, platform, deployment, and organization-specific requirements before treating it as a final production standard.

## Intended scope

- Go modules and packages
- HTTP, RPC, and background services
- command-line tools
- libraries and internal packages
- concurrent processing
- tests, benchmarks, fuzzing, and module metadata

## Runtime baseline

- Declare the supported Go toolchain in the repository.
- Use module-aware builds with committed `go.mod` and `go.sum`.
- Apply standard formatting and vetting.
- Declare supported operating systems and architectures.
- Preserve existing module and API compatibility unless migration is explicitly in scope.

## Package structure

| Path | Purpose |
|---|---|
| [`AGENTS.md`](AGENTS.md) | Mandatory Go-specific operating rules |
| [`MANIFEST.md`](MANIFEST.md) | Package inventory and adoption checklist |
| [`standards/`](standards/) | Coding, modules, concurrency, architecture, security, testing, and evidence standards |
| [`templates/`](templates/) | Adoption templates |
| [`examples/`](examples/) | Example package composition |

## Required standards

| Standard | Governs |
|---|---|
| [`GO_CODING_STANDARD.md`](standards/GO_CODING_STANDARD.md) | Naming, errors, interfaces, resources, packages, and maintainability |
| [`ARCHITECTURE_STANDARD.md`](standards/ARCHITECTURE_STANDARD.md) | Package boundaries, dependencies, configuration, and side effects |
| [`DOCUMENTATION_STANDARD.md`](standards/DOCUMENTATION_STANDARD.md) | Package comments, exported APIs, examples, and operator guidance |
| [`TESTING_STANDARD.md`](standards/TESTING_STANDARD.md) | Unit, integration, table-driven, race, fuzz, and benchmark testing |
| [`SECURITY_STANDARD.md`](standards/SECURITY_STANDARD.md) | Input validation, files, networks, secrets, cryptography, and secure defaults |
| [`DEPENDENCY_MANAGEMENT_STANDARD.md`](standards/DEPENDENCY_MANAGEMENT_STANDARD.md) | Module sources, versions, checksums, provenance, and vulnerability review |
| [`OBSERVABILITY_STANDARD.md`](standards/OBSERVABILITY_STANDARD.md) | Structured logs, metrics, traces, context, and sensitive-data controls |
| [`MODULES_STANDARD.md`](standards/MODULES_STANDARD.md) | Module layout, workspaces, replace directives, checksums, and releases |
| [`CONCURRENCY_STANDARD.md`](standards/CONCURRENCY_STANDARD.md) | Goroutine ownership, cancellation, synchronization, backpressure, and leak prevention |
| [`COMPLETION_EVIDENCE.md`](standards/COMPLETION_EVIDENCE.md) | Proof required before completion claims |

## Adoption procedure

1. Inventory modules, workspaces, packages, services, tests, generators, and deployment targets.
2. Declare the supported Go toolchain and target platforms.
3. Define module, workspace, internal package, and public API boundaries.
4. Define formatting, vetting, static-analysis, test, race, fuzz, build, and release commands.
5. Define context propagation, cancellation, timeout, retry, and shutdown behavior.
6. Define network, file, database, message, authentication, authorization, and secret boundaries.
7. Add applicable discipline, framework, platform, virtualization, operating-system, networking, and project-profile overlays.
8. Review code generators and executable tooling dependencies.
9. Run repository and package validation.
10. Review the composed standard with an accountable Go maintainer.

## Project tailoring checklist

- [ ] Go toolchain and supported platforms are declared.
- [ ] Module, workspace, package, and public API boundaries are documented.
- [ ] Dependency sources, checksums, update policy, and `replace` usage are defined.
- [ ] Context, cancellation, timeout, retry, and shutdown behavior are defined.
- [ ] Concurrency limits, goroutine ownership, synchronization, and backpressure are defined.
- [ ] Test, race-detector, fuzzing, benchmark, and integration expectations are defined.
- [ ] Logging, metrics, tracing, health, and redaction requirements are defined.
- [ ] Packaging, release, deployment, rollback, and compatibility requirements are defined.
- [ ] Secret-management, authentication, and authorization requirements are defined.

## Go-specific safety expectations

- Every started goroutine requires an owner and a shutdown path.
- Propagate `context.Context` across cancellable request and operation boundaries.
- Avoid storing contexts in long-lived structs unless a framework contract requires it.
- Wrap errors only when additional context is useful and preserve inspectability.
- Close response bodies, files, database rows, and other resources on all paths.
- Do not use `replace` directives as an undocumented permanent dependency strategy.

## Validation baseline

Use repository-defined commands when available:

```bash
go version
gofmt -l .
go vet ./...
go test ./...
go test -race ./...
```

Run the race detector only on supported targets. Add repository-configured static analysis, fuzzing, benchmarks, vulnerability review, and build checks.

## Testing expectations

Tests should cover expected behavior, invalid input, cancellation, deadlines, concurrency, races, leaks, network and file failures, external dependencies, platform behavior, and public API compatibility.

## Completion evidence

A completion report must include files and packages changed, behavior and public contracts changed, concurrency and compatibility impact, validation commands and results, checks not run, documentation updated, limitations, and remaining risk.

## Templates and examples

- [`AGENTS_TEMPLATE.md`](templates/AGENTS_TEMPLATE.md)
- [`ADOPTION_CHECKLIST.md`](templates/ADOPTION_CHECKLIST.md)
- [`ADOPTION_EXAMPLE.md`](examples/ADOPTION_EXAMPLE.md)

## What this package does not decide

The adopting repository must still define business requirements, service architecture, deployment environments, identity, data ownership, incident response, release management, backup, recovery, and organization-specific compliance.

This package improves agent behavior. It does not guarantee that generated Go software is secure, correct, compliant, or production ready.

## Authoritative starting points

- [Go command documentation](https://go.dev/cmd/go/)
- [The Go programming language specification](https://go.dev/ref/spec)
- [Go modules reference](https://go.dev/ref/mod)
- [Go standard library](https://pkg.go.dev/std)
- [Go release policy](https://go.dev/doc/devel/release)

Revalidate current Go, module, toolchain, security, and support behavior before relying on version-specific guidance.
