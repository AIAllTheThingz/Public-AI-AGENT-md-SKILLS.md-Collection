# .NET Agent Standard Package

This package provides project-agnostic engineering standards for modern .NET applications, ASP.NET Core services, worker services, libraries, and data-access components.

It defines how coding agents should inspect, design, implement, test, secure, document, and report .NET work. It does not define the adopting project's business requirements, production architecture, or organization-specific approval process.

For C# source and compiler/language behavior, compose this package with the dedicated [`csharp` package](../csharp/) and its direct [`SKILL.md`](../csharp/SKILL.md). The C# package governs language semantics; this package governs the .NET SDK/runtime/application boundary. Existing adopters remain valid and can add the C# package without replacing this package.

## Intended scope

- .NET solutions and C# projects
- ASP.NET Core applications and APIs
- worker services and background processing
- reusable libraries and NuGet packages
- Entity Framework Core and other data access
- unit, integration, functional, and architecture tests
- build, packaging, publishing, and deployment configuration

## Runtime baseline

For new development this package currently targets:

- .NET 10 LTS
- `net10.0`
- stable C# supported by the selected SDK
- the `dotnet` CLI
- no preview SDKs, workloads, packages, or language features unless explicitly approved

Existing repositories must preserve their declared target frameworks unless migration is explicitly in scope.

## Package structure

| Path | Purpose |
|---|---|
| [`AGENTS.md`](AGENTS.md) | Mandatory .NET-specific operating rules |
| [`MANIFEST.md`](MANIFEST.md) | Package inventory and adoption validation |
| [`standards/`](standards/) | Detailed language, architecture, security, testing, data, and operational standards |
| [`templates/`](templates/) | Reference project, class, service, endpoint, and test artifacts |
| [`examples/`](examples/) | Example configuration files |

## Required standards

| Standard | Governs |
|---|---|
| [`DOTNET_CODING_STANDARD.md`](standards/DOTNET_CODING_STANDARD.md) | C# structure, APIs, nullability, async behavior, exceptions, and maintainability |
| [`ARCHITECTURE_STANDARD.md`](standards/ARCHITECTURE_STANDARD.md) | Boundaries, dependency direction, configuration, and design decisions |
| [`DOCUMENTATION_STANDARD.md`](standards/DOCUMENTATION_STANDARD.md) | XML documentation, examples, operational documentation, and change notes |
| [`TESTING_STANDARD.md`](standards/TESTING_STANDARD.md) | Unit, integration, functional, and architecture testing |
| [`SECURITY_STANDARD.md`](standards/SECURITY_STANDARD.md) | Authentication, authorization, validation, secrets, cryptography, and secure defaults |
| [`DEPENDENCY_MANAGEMENT_STANDARD.md`](standards/DEPENDENCY_MANAGEMENT_STANDARD.md) | NuGet selection, versions, provenance, lock strategy, and vulnerability review |
| [`ASPNETCORE_STANDARD.md`](standards/ASPNETCORE_STANDARD.md) | HTTP pipelines, APIs, middleware, validation, errors, and hosting |
| [`DATA_ACCESS_STANDARD.md`](standards/DATA_ACCESS_STANDARD.md) | Transactions, migrations, queries, data integrity, and provider boundaries |
| [`OBSERVABILITY_STANDARD.md`](standards/OBSERVABILITY_STANDARD.md) | Structured logs, metrics, traces, health checks, and sensitive-data controls |
| [`COMPLETION_EVIDENCE.md`](standards/COMPLETION_EVIDENCE.md) | Proof required before completion claims |

## Adoption procedure

1. Inventory solutions, projects, target frameworks, package management, tests, analyzers, and deployment targets.
2. Pin the supported SDK in `global.json` or the repository's approved equivalent.
3. Declare target frameworks, supported operating systems, runtime identifiers, and hosting model.
4. Define analyzer severities, formatting, nullability, and warning policies.
5. Define test frameworks, integration dependencies, and coverage expectations.
6. Define database providers, migration ownership, and transaction requirements.
7. Define authentication, authorization, secret storage, and configuration sources.
8. Add applicable framework, platform, virtualization, operating-system, networking, security, database, and project-profile overlays.
9. Record the real validation and packaging commands.
10. Review the composed standard with an accountable .NET maintainer.

## Project tailoring checklist

- [ ] SDK feature band and target frameworks are declared.
- [ ] Supported operating systems, architectures, and deployment targets are documented.
- [ ] Nullable reference types and analyzer policies are defined.
- [ ] Package versioning and central package-management policy are defined.
- [ ] Authentication, authorization, and secret-management requirements are documented.
- [ ] Database providers, migrations, and transaction ownership are documented.
- [ ] Cancellation, retry, timeout, and graceful-shutdown behavior are defined.
- [ ] Logging, metrics, tracing, health, and data-redaction requirements are defined.
- [ ] Test frameworks, integration environments, and evidence requirements are defined.
- [ ] Publishing, deployment, rollback, and compatibility expectations are defined.

## Safety and compatibility expectations

- Preserve public contracts unless change is explicitly authorized.
- Treat serialized data, migrations, configuration keys, API routes, and package APIs as compatibility surfaces.
- Preserve cancellation and graceful-shutdown paths.
- Do not hide blocking I/O behind asynchronous signatures.
- Do not log tokens, connection strings, credentials, or regulated data.
- Validate authorization at the resource and operation boundary, not merely at the UI or controller surface.
- Use strongly typed configuration and fail safely when required values are missing.

## Validation baseline

Use repository-defined commands when available:

```bash
dotnet --info
dotnet restore
dotnet format --verify-no-changes
dotnet build --no-restore
dotnet test --no-build
dotnet package list --vulnerable --include-transitive
```

Additional checks may include publishing, migration validation, architecture tests, API contract tests, container builds, and deployment smoke tests.

## Testing expectations

Tests should cover expected behavior, invalid input, authorization failures, cancellation, timeouts, external dependency failures, serialization contracts, database transactions, migrations, retries, and graceful shutdown.

A test suite that merely repeats implementation details is not meaningful completion evidence.

## Completion evidence

A completion report must include:

- files and projects changed
- behavior and public contracts changed
- security, data, and compatibility impact
- tests and validation commands actually run
- build, package, migration, or publish results
- documentation updated
- checks not run and why
- limitations, untested paths, and remaining risk

## Templates and examples

The package includes reference starting points for build configuration, package management, SDK selection, classes, interfaces, services, controllers, endpoints, and tests. Templates must be reviewed and tailored before production use.

Useful entry points include:

- [`Directory.Build.props`](templates/Directory.Build.props)
- [`Directory.Packages.props`](templates/Directory.Packages.props)
- [`global.json`](templates/global.json)
- [`SERVICE_TEMPLATE.cs`](templates/SERVICE_TEMPLATE.cs)
- [`CONTROLLER_TEMPLATE.cs`](templates/CONTROLLER_TEMPLATE.cs)
- [`UNIT_TEST_TEMPLATE.cs`](templates/UNIT_TEST_TEMPLATE.cs)
- [`INTEGRATION_TEST_TEMPLATE.cs`](templates/INTEGRATION_TEST_TEMPLATE.cs)

## What this package does not decide

The adopting repository must still define production architecture, deployment environments, data ownership, identity providers, database operations, incident response, backup, recovery, and organization-specific compliance.

This package improves agent behavior. It does not guarantee that generated software is secure, correct, compliant, or production ready.

## Authoritative starting points

- [.NET documentation](https://learn.microsoft.com/en-us/dotnet/)
- [Target frameworks in SDK-style projects](https://learn.microsoft.com/en-us/dotnet/standard/frameworks)
- [Configure the .NET SDK](https://learn.microsoft.com/en-us/dotnet/core/tools/global-json)
- [NuGet documentation](https://learn.microsoft.com/en-us/nuget/)
- [.NET support policy](https://dotnet.microsoft.com/en-us/platform/support/policy/dotnet-core)

Revalidate current SDK, target-framework, package, security, and support behavior before relying on version-specific guidance.
