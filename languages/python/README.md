---
id: PY-PKG-001
status: baseline
title: Python Package
---

# Python Language Package

This package provides project-agnostic engineering standards for Python libraries, services, command-line tools, automation, and data-processing code.

It defines how coding agents should inspect, design, implement, test, secure, document, package, and report Python work. It does not choose a web framework, dependency manager, cloud platform, or production architecture for the adopting project.

## Package status

**Status:** `baseline`

The package is structurally complete and suitable for adoption. Projects must tailor runtime, environment, framework, deployment, and organization-specific requirements before treating it as a final production standard.

## Intended scope

- Python packages and modules
- web services and APIs
- command-line tools
- automation and scheduled jobs
- data-processing code
- tests and packaging metadata

## Runtime baseline

- Use a currently supported CPython release declared by the repository.
- Pin the exact interpreter version in project tooling.
- Do not rely on an unpinned system Python.
- Use isolated and reproducible dependency installation.
- Preserve existing compatibility unless migration is explicitly in scope.

## Package structure

| Path | Purpose |
|---|---|
| [`AGENTS.md`](AGENTS.md) | Mandatory Python-specific operating rules |
| [`MANIFEST.md`](MANIFEST.md) | Package inventory and adoption checklist |
| [`standards/`](standards/) | Coding, architecture, typing, packaging, security, testing, and evidence standards |
| [`templates/`](templates/) | Adoption templates |
| [`examples/`](examples/) | Example package composition |

## Required standards

| Standard | Governs |
|---|---|
| [`PYTHON_CODING_STANDARD.md`](standards/PYTHON_CODING_STANDARD.md) | Language structure, naming, exceptions, resources, data models, and maintainability |
| [`ARCHITECTURE_STANDARD.md`](standards/ARCHITECTURE_STANDARD.md) | Package boundaries, dependencies, configuration, and side effects |
| [`DOCUMENTATION_STANDARD.md`](standards/DOCUMENTATION_STANDARD.md) | Docstrings, public APIs, examples, and operator guidance |
| [`TESTING_STANDARD.md`](standards/TESTING_STANDARD.md) | Unit, integration, negative-path, and deterministic testing |
| [`SECURITY_STANDARD.md`](standards/SECURITY_STANDARD.md) | Input validation, serialization, subprocesses, files, secrets, and secure defaults |
| [`DEPENDENCY_MANAGEMENT_STANDARD.md`](standards/DEPENDENCY_MANAGEMENT_STANDARD.md) | Dependency selection, pinning, provenance, locking, and vulnerability review |
| [`OBSERVABILITY_STANDARD.md`](standards/OBSERVABILITY_STANDARD.md) | Structured logs, metrics, traces, correlation, and sensitive-data controls |
| [`PACKAGING_STANDARD.md`](standards/PACKAGING_STANDARD.md) | Build metadata, distributions, entry points, and release validation |
| [`TYPING_STANDARD.md`](standards/TYPING_STANDARD.md) | Type annotations, public contracts, checking boundaries, and exceptions |
| [`COMPLETION_EVIDENCE.md`](standards/COMPLETION_EVIDENCE.md) | Proof required before completion claims |

## Adoption procedure

1. Inventory Python versions, environments, package metadata, frameworks, tests, and deployment targets.
2. Pin the supported interpreter and document supported operating systems.
3. Select and document dependency and environment-management tooling.
4. Define formatting, linting, typing, testing, build, and package commands.
5. Define package boundaries, import behavior, configuration sources, and entry points.
6. Define trust boundaries for files, APIs, databases, messages, subprocesses, and serialized data.
7. Add framework, platform, virtualization, operating-system, networking, data, security, and project-profile overlays where applicable.
8. Review templates and examples before copying them.
9. Run repository and package validation.
10. Review the composed standard with an accountable Python maintainer.

## Project tailoring checklist

- [ ] Supported Python versions and platforms are declared.
- [ ] Virtual-environment and dependency tooling is defined.
- [ ] Locking, pinning, indexes, and package provenance are defined.
- [ ] Typing strictness and public API requirements are defined.
- [ ] Framework, service, automation, or data-processing boundaries are documented.
- [ ] Test frameworks, coverage, fixtures, and integration dependencies are defined.
- [ ] Packaging, publication, entry points, and release expectations are defined.
- [ ] Logging, metrics, tracing, error reporting, and redaction are defined.
- [ ] Secret-management and configuration sources are documented.
- [ ] Compatibility, migration, rollback, and deprecation requirements are defined.

## Python-specific safety expectations

- Do not deserialize untrusted data with unsafe loaders or formats.
- Use context managers and explicit cleanup for files, network connections, database connections, and temporary resources.
- Keep import-time side effects and hidden global state to a minimum.
- Pass subprocess arguments as structured lists and avoid shell interpretation unless explicitly required and safely constrained.
- Validate paths before reads, writes, extraction, deletion, or traversal.
- Do not suppress broad exceptions without preserving useful context and correct failure behavior.

## Validation baseline

Use repository-defined commands when they exist. Typical checks include:

```bash
python --version
python -m compileall .
python -m pytest
python -m pip check
```

Also run the repository-configured formatter, linter, type checker, package build, and security checks. Never claim a command passed unless it was actually run successfully.

## Testing expectations

Tests should cover expected behavior, invalid input, resource cleanup, subprocess and network failures, serialization boundaries, authorization, packaging, supported interpreter versions, and platform-specific behavior.

Use isolated temporary resources and controlled integration environments. Tests must not contact or mutate production systems.

## Completion evidence

A completion report must include:

- files and packages changed
- behavior and public contracts changed
- runtime, dependency, security, and compatibility impact
- validation commands and results
- package or distribution artifacts tested
- documentation updated
- checks not run and why
- limitations, untested paths, and remaining risk

## Templates and examples

- [`AGENTS_TEMPLATE.md`](templates/AGENTS_TEMPLATE.md): project-root language instruction template
- [`ADOPTION_CHECKLIST.md`](templates/ADOPTION_CHECKLIST.md): adoption and tailoring checklist
- [`ADOPTION_EXAMPLE.md`](examples/ADOPTION_EXAMPLE.md): example package composition

Templates are reference starting points. Replace placeholders and review toolchain, paths, dependencies, security controls, and compatibility before adoption.

## What this package does not decide

The adopting repository must still define business requirements, framework architecture, production environments, data ownership, identity, incident response, backup, recovery, release management, and organization-specific compliance.

This package improves agent behavior. It does not guarantee that generated Python software is secure, correct, compliant, or production ready.

## Authoritative starting points

- [Python documentation](https://docs.python.org/3/)
- [Python language reference](https://docs.python.org/3/reference/)
- [Python standard library](https://docs.python.org/3/library/)
- [Python Enhancement Proposals](https://peps.python.org/)
- [Python Packaging User Guide](https://packaging.python.org/)

Revalidate current Python, packaging, security, and support behavior before relying on version-specific guidance.
