# Language Standards

Use [`SKILL.md`](SKILL.md) when an agent must select and apply these packages during advanced coding, scripting, review, refactoring, debugging, testing, packaging, or migration work.

The `languages/` directory contains copyable, project-agnostic standards packages for repositories that use AI coding agents.

Each complete package defines how engineering work should be performed for a language. It does not define the adopting project's business requirements, production architecture, or organization-specific approval process.

## Available packages

| Package | Primary scope | Maturity |
|---|---|---|
| [PowerShell 7.x](powershell/) | Administrative automation, modules, scripts, remoting, and operational tooling | Complete |
| [C#](csharp/) | C# language semantics, scripting, nullability, async/concurrency, API design, performance, interop, generators, and unsafe code | Stable |
| [.NET](dotnet/) | .NET SDK/runtime, target frameworks, MSBuild, NuGet, ASP.NET Core, worker services, libraries, and data access | Complete |
| [JavaScript and TypeScript](javascript-typescript/) | Node.js, browser applications, libraries, tooling, and TypeScript | Complete |
| [Python](python/) | Packages, services, CLI tools, automation, and data processing | Baseline |
| [Java](java/) | JVM applications, services, libraries, build tooling, and deployment artifacts | Baseline |
| [Go](go/) | Services, CLI tools, libraries, modules, and concurrent systems | Baseline |
| [Rust](rust/) | Crates, services, CLI tools, libraries, systems code, and FFI | Baseline |
| [Bash](bash/) | Shell automation, installation tooling, CI helpers, and operational scripts | Baseline |
| [SQL](sql/) | Queries, schema objects, migrations, database scripts, and data integrity | Baseline |
| [Terraform and OpenTofu](terraform-opentofu/) | Declarative infrastructure, modules, providers, state, plans, and applies | Baseline |

## What a package contains

A language package should contain:

- an enforceable `AGENTS.md`
- a registered `SKILL.md` when the package provides direct specialized invocation
- a package `README.md`
- supporting standards under `standards/`
- reusable templates under `templates/`
- adoption examples under `examples/` where applicable
- a package `MANIFEST.md` where available
- language-specific completion-evidence requirements
- validation commands or procedures

A directory that only contains a title or roadmap marker must not be represented as complete.

### C# and .NET composition

Select `csharp` for C# source and compiler/language behavior. Select `dotnet` for the .NET SDK, target frameworks, CLR, MSBuild, NuGet, application models, hosting, publishing, or deployment. Most modern C# projects should compose both packages. Non-C# .NET projects select `dotnet` plus their actual language guidance.

## How packages are used

### Single-language repositories

Adopt the applicable language package at the repository root or compose its rules into the root `AGENTS.md`. Preserve the links to the supporting standards.

### Multi-language repositories

Keep organization-wide requirements in the root `AGENTS.md`, then use nested language-scoped instructions:

```text
repository/
├── AGENTS.md
├── services/
│   ├── api-dotnet/
│   │   └── AGENTS.md
│   ├── worker-python/
│   │   └── AGENTS.md
│   └── web-typescript/
│       └── AGENTS.md
└── database/
    └── AGENTS.md
```

The nearest scoped `AGENTS.md` may add stricter requirements. It must not silently weaken applicable parent requirements.

## Adoption sequence

1. Read the repository-root `AGENTS.md` and governance standards.
2. Select the applicable language package.
3. Read the package `README.md`, `AGENTS.md`, and supporting standards.
4. Declare exact runtime, platform, dependency, and compatibility requirements.
5. Add applicable discipline, framework, platform, virtualization, operating-system, networking, database, and project-profile overlays.
6. Tailor templates and examples without introducing secrets or production identifiers.
7. Define the project's real formatting, static-analysis, test, build, package, and security commands.
8. Run repository validation and relative-link checking.
9. Review the composed standard with an accountable maintainer.

## Tailoring rules

Projects may:

- add stricter requirements
- narrow supported versions or platforms
- replace reference tooling with repository-standard tooling
- add framework-specific rules
- add organization-specific approval, compliance, and evidence controls

Projects must not silently:

- remove security or validation controls
- reduce testing or completion evidence
- invent compatibility claims
- embed production secrets or internal identifiers
- claim a package is adopted when referenced standards are missing

Material deviations should use the repository exception process.

## Maturity terminology

- **Complete:** structurally complete and independently adoptable.
- **Baseline:** usable for adoption but expected to receive deeper ecosystem review and more examples.
- **Stable:** mature, broadly reviewed, versioned, and supported for predictable adoption.
- **Draft:** available for review but not recommended as an organizational default.
- **Deprecated:** retained only for migration.

Package completeness and maturity are different. A package may be structurally complete while still carrying baseline maturity.

## Repository validation

From the repository root:

```bash
python tools/validate-standards/validate_repository.py
python tools/check-links/check_links.py
```

Each package README documents additional language-specific validation.

## Maintenance expectations

When changing a language package:

- keep `README.md`, `AGENTS.md`, standards, templates, examples, and manifests synchronized
- preserve stable front-matter identifiers
- update compatibility and toolchain guidance deliberately
- cite public authoritative sources when a rule depends on an external standard
- avoid copying large sections of third-party documentation
- report validation performed, checks not run, limitations, and remaining risk
