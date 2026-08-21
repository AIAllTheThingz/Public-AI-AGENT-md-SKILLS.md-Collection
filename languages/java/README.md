---
id: JAVA-PKG-001
status: baseline
title: Java Package
---

# Java Language Package

This package provides project-agnostic engineering standards for Java applications, JVM services, reusable libraries, build files, tests, database access, and deployment artifacts.

It defines how coding agents should inspect, design, implement, test, secure, document, build, package, and report Java work. It does not choose Spring, Jakarta EE, a database provider, or a deployment platform for the adopting project.

## Package status

**Status:** `baseline`

The package is structurally complete and suitable for adoption. Projects must tailor runtime, build, framework, platform, virtualization, operating-system, networking, deployment, and organization-specific requirements before treating it as a final production standard.

## Intended scope

- Java applications and libraries
- JVM services and background workers
- build configuration and dependency metadata
- database-access code
- tests and quality tooling
- deployment packaging

## Runtime baseline

- For new work, prefer a currently supported Java LTS release.
- Declare the exact Java toolchain in the build.
- Use repository wrappers for Maven or Gradle where applicable.
- Preserve existing source, bytecode, and runtime compatibility unless migration is explicitly in scope.
- Do not introduce preview features without explicit approval and validation.

## Package structure

| Path | Purpose |
|---|---|
| [`AGENTS.md`](AGENTS.md) | Mandatory Java-specific operating rules |
| [`MANIFEST.md`](MANIFEST.md) | Package inventory and adoption checklist |
| [`standards/`](standards/) | Coding, JVM, build, architecture, security, testing, and evidence standards |
| [`templates/`](templates/) | Adoption templates |
| [`examples/`](examples/) | Example package composition |

## Required standards

| Standard | Governs |
|---|---|
| [`JAVA_CODING_STANDARD.md`](standards/JAVA_CODING_STANDARD.md) | Language structure, APIs, exceptions, resources, concurrency, and maintainability |
| [`ARCHITECTURE_STANDARD.md`](standards/ARCHITECTURE_STANDARD.md) | Module and package boundaries, dependencies, configuration, and design decisions |
| [`DOCUMENTATION_STANDARD.md`](standards/DOCUMENTATION_STANDARD.md) | Javadoc, package documentation, examples, and operational guidance |
| [`TESTING_STANDARD.md`](standards/TESTING_STANDARD.md) | Unit, integration, contract, packaging, and negative-path testing |
| [`SECURITY_STANDARD.md`](standards/SECURITY_STANDARD.md) | Input validation, deserialization, identity, secrets, and secure defaults |
| [`DEPENDENCY_MANAGEMENT_STANDARD.md`](standards/DEPENDENCY_MANAGEMENT_STANDARD.md) | Maven or Gradle dependencies, provenance, versions, plugins, and vulnerabilities |
| [`OBSERVABILITY_STANDARD.md`](standards/OBSERVABILITY_STANDARD.md) | Structured logging, metrics, traces, health, and sensitive-data controls |
| [`JVM_RUNTIME_STANDARD.md`](standards/JVM_RUNTIME_STANDARD.md) | JVM compatibility, memory, startup, shutdown, and runtime assumptions |
| [`BUILD_TOOLING_STANDARD.md`](standards/BUILD_TOOLING_STANDARD.md) | Maven and Gradle wrappers, plugins, reproducibility, and lifecycle |
| [`COMPLETION_EVIDENCE.md`](standards/COMPLETION_EVIDENCE.md) | Proof required before completion claims |

## Adoption procedure

1. Inventory Java versions, build files, wrappers, modules, frameworks, tests, and deployment targets.
2. Declare supported Java releases, JVM vendors, and operating systems.
3. Define Maven or Gradle conventions and wrapper policy.
4. Define compiler, formatting, static-analysis, test, package, and verification commands.
5. Define module and package boundaries, configuration sources, and public APIs.
6. Define database, messaging, serialization, authentication, authorization, and secret-management requirements.
7. Add framework, platform, virtualization, operating-system, networking, database, API, security, and project-profile overlays.
8. Review build plugins, annotation processors, code generators, and executable dependency hooks.
9. Run repository and package validation.
10. Review the composed standard with an accountable Java maintainer.

## Project tailoring checklist

- [ ] Java release, JVM vendor, and supported platforms are declared.
- [ ] Maven or Gradle wrapper and repository policies are defined.
- [ ] Compiler, formatting, static-analysis, and warning policies are defined.
- [ ] Dependency, plugin, annotation processor, and repository provenance are defined.
- [ ] Module, package, API, and framework boundaries are documented.
- [ ] Test libraries, integration environments, and evidence requirements are defined.
- [ ] Serialization, database, messaging, and transaction requirements are documented.
- [ ] Logging, metrics, tracing, health, shutdown, and redaction are defined.
- [ ] Packaging, deployment, rollback, migration, and compatibility expectations are defined.
- [ ] Secret-management, authentication, and authorization requirements are defined.

## Java-specific safety expectations

- Use try-with-resources for closeable resources.
- Treat serialization, reflection, class loading, expression languages, and template engines as trust-boundary concerns.
- Preserve interrupt status and cancellation behavior where required.
- Do not introduce build plugins or annotation processors without reviewing their execution and provenance.
- Do not catch broad exceptions merely to continue with corrupted or ambiguous state.
- Keep secrets out of system properties, command lines, logs, stack traces, and committed configuration.

## Validation baseline

Use repository-defined commands. Typical checks include:

```text
java -version
./mvnw verify
./gradlew check
```

Use the wrapper and build system actually declared by the repository, not both. Also run configured static analysis and test the packaged artifact in its supported runtime.

## Testing expectations

Tests should cover expected behavior, invalid input, authorization, serialization, database transactions, messaging, concurrency, timeouts, external dependency failures, shutdown, packaging, and supported runtime behavior.

## Completion evidence

A completion report must include:

- files, modules, and artifacts changed
- behavior and public contracts changed
- runtime, dependency, security, and compatibility impact
- build, test, package, and static-analysis commands actually run
- results or CI evidence
- documentation updated
- checks not run and why
- limitations, untested paths, and remaining risk

## Templates and examples

- [`AGENTS_TEMPLATE.md`](templates/AGENTS_TEMPLATE.md): project-root language instruction template
- [`ADOPTION_CHECKLIST.md`](templates/ADOPTION_CHECKLIST.md): adoption and tailoring checklist
- [`ADOPTION_EXAMPLE.md`](examples/ADOPTION_EXAMPLE.md): example package composition

## What this package does not decide

The adopting repository must still define business requirements, framework architecture, production topology, identity, data ownership, database operations, incident response, release management, backup, recovery, and organization-specific compliance.

This package improves agent behavior. It does not guarantee that generated Java software is secure, correct, compliant, or production ready.

## Authoritative starting points

- [OpenJDK documentation](https://openjdk.org/)
- [Java SE specifications, including the language and JVM specifications](https://docs.oracle.com/javase/specs/)
- [Java SE API documentation index](https://docs.oracle.com/en/java/javase/)
- [Apache Maven guides](https://maven.apache.org/guides/)
- [Gradle user manual](https://docs.gradle.org/current/userguide/userguide.html)

Revalidate current Java, JVM, build-tool, security, and support behavior before relying on version-specific guidance.
