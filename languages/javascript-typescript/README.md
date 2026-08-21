# JavaScript and TypeScript Agent Standard Package

This package provides project-agnostic engineering standards for Node.js services, browser applications, reusable packages, command-line tools, build tooling, and TypeScript codebases.

It defines how coding agents should inspect, design, implement, test, secure, document, and report JavaScript and TypeScript work. It does not select a framework, hosting platform, browser support matrix, or production architecture for the adopting project.

## Intended scope

- Node.js applications and services
- browser applications and shared frontend code
- JavaScript and TypeScript libraries
- command-line tools and build tooling
- package metadata and workspaces
- tests, linting, formatting, type checking, and bundling configuration

## Runtime and tooling baseline

For new work this package currently uses the following reference baseline:

- Node.js 24 LTS
- TypeScript 6.0 where TypeScript is used
- ES2025
- ECMAScript modules
- pnpm 11
- ESLint flat configuration
- Prettier
- Vitest reference configuration

Projects may use different supported tooling, but must declare it explicitly and keep the package manager and lockfile consistent.

## Package structure

| Path | Purpose |
|---|---|
| [`AGENTS.md`](AGENTS.md) | Mandatory JavaScript and TypeScript operating rules |
| [`MANIFEST.md`](MANIFEST.md) | Package inventory and adoption validation |
| [`standards/`](standards/) | Language, runtime, frontend, architecture, security, testing, and operational standards |
| [`templates/`](templates/) | Reference package, compiler, lint, formatting, source, and test files |
| [`examples/`](examples/) | Example environment and package metadata |

## Required standards

| Standard | Governs |
|---|---|
| [`JAVASCRIPT_TYPESCRIPT_CODING_STANDARD.md`](standards/JAVASCRIPT_TYPESCRIPT_CODING_STANDARD.md) | Modules, language structure, errors, async behavior, and maintainability |
| [`TYPESCRIPT_STANDARD.md`](standards/TYPESCRIPT_STANDARD.md) | Strict typing, public types, narrowing, generics, and compiler settings |
| [`NODEJS_STANDARD.md`](standards/NODEJS_STANDARD.md) | Runtime behavior, process lifecycle, files, networking, and services |
| [`WEB_FRONTEND_STANDARD.md`](standards/WEB_FRONTEND_STANDARD.md) | Browser security, accessibility, rendering, state, and client boundaries |
| [`ARCHITECTURE_STANDARD.md`](standards/ARCHITECTURE_STANDARD.md) | Module boundaries, dependency direction, configuration, and design decisions |
| [`DOCUMENTATION_STANDARD.md`](standards/DOCUMENTATION_STANDARD.md) | Package, API, operational, and example documentation |
| [`TESTING_STANDARD.md`](standards/TESTING_STANDARD.md) | Unit, integration, browser, and negative-path tests |
| [`SECURITY_STANDARD.md`](standards/SECURITY_STANDARD.md) | Trust boundaries, secrets, browser and server security, and secure defaults |
| [`DEPENDENCY_MANAGEMENT_STANDARD.md`](standards/DEPENDENCY_MANAGEMENT_STANDARD.md) | Packages, lockfiles, scripts, provenance, audits, and updates |
| [`OBSERVABILITY_STANDARD.md`](standards/OBSERVABILITY_STANDARD.md) | Logs, metrics, traces, error reporting, and data minimization |
| [`COMPLETION_EVIDENCE.md`](standards/COMPLETION_EVIDENCE.md) | Proof required before completion claims |

## Adoption procedure

1. Inventory runtimes, browsers, package manager, workspaces, frameworks, bundlers, and deployment targets.
2. Pin Node.js and package-manager versions using repository-standard files.
3. Declare module format, TypeScript policy, browser matrix, and package output.
4. Define lint, formatting, type-check, test, and build scripts.
5. Define dependency provenance, lifecycle-script, audit, and lockfile policies.
6. Define browser and server trust boundaries, authentication, authorization, and secret storage.
7. Add applicable framework, discipline, platform, virtualization, operating-system, networking, and project-profile overlays.
8. Review templates before copying them into the application.
9. Record the real validation and release commands.
10. Review the composed standard with an accountable maintainer.

## Project tailoring checklist

- [ ] Node.js, browser, and ECMAScript support are declared.
- [ ] Package manager, lockfile, registry, and workspace policies are defined.
- [ ] Module format and package export strategy are defined.
- [ ] TypeScript strictness and compiler output are defined.
- [ ] Framework, bundler, server, and deployment requirements are documented.
- [ ] Content security, authentication, authorization, and secret handling are defined.
- [ ] Accessibility and supported interaction requirements are defined for browser work.
- [ ] Test environments, browser coverage, and integration dependencies are defined.
- [ ] Logging, metrics, tracing, error reporting, and redaction are defined.
- [ ] Release, versioning, rollback, and compatibility expectations are defined.

## Security and supply-chain expectations

- Treat network data, browser input, storage, messages, files, environment variables, and package metadata as untrusted.
- Do not use dynamic evaluation or unsafe HTML injection to bypass design problems.
- Treat package lifecycle scripts and transitive dependencies as executable supply-chain risk.
- Keep browser-only and server-only code paths explicit.
- Do not expose server secrets in client bundles, source maps, logs, errors, or examples.
- Use context-appropriate output encoding and approved sanitization at rendering boundaries.

## Validation baseline

Use repository-defined scripts when they exist:

```bash
node --version
pnpm --version
pnpm install --frozen-lockfile
pnpm format:check
pnpm lint
pnpm typecheck
pnpm test
pnpm build
pnpm audit
```

Framework-specific validation may add browser tests, accessibility checks, server integration tests, package publishing checks, or deployment smoke tests.

## Testing expectations

Tests should cover expected behavior, invalid input, asynchronous failures, timeouts, cancellation, network and storage failures, browser compatibility, accessibility, authorization, package boundaries, and build output.

Do not rely solely on snapshots or shallow component tests when behavior crosses meaningful trust or integration boundaries.

## Completion evidence

A completion report must include:

- files and packages changed
- behavior and public contracts changed
- browser, runtime, security, and compatibility impact
- validation commands and results
- dependency or lockfile impact
- build and package output tested
- documentation updated
- checks not run and why
- limitations and remaining risk

## Templates and examples

The package includes reference configuration for Node.js versions, pnpm workspaces, package metadata, TypeScript, ESLint, Prettier, Vitest, source modules, services, HTTP clients, and tests.

Templates are starting points, not a command to replace an existing toolchain. Review package names, paths, scripts, target environments, and dependencies before adoption.

## What this package does not decide

The adopting repository must still define framework architecture, browser support, deployment environments, API ownership, data classification, incident response, package publishing, backup, recovery, and organization-specific compliance.

This package improves agent behavior. It does not guarantee that generated software is secure, correct, compliant, or production ready.

## Authoritative starting points

- [ECMAScript Language Specification](https://tc39.es/ecma262/)
- [TypeScript Handbook](https://www.typescriptlang.org/docs/handbook/intro.html)
- [TypeScript TSConfig Reference](https://www.typescriptlang.org/tsconfig/)
- [Node.js 24 LTS API documentation](https://nodejs.org/docs/latest-v24.x/api/index.html)
- [DOM Standard](https://dom.spec.whatwg.org/)

Revalidate current ECMAScript, TypeScript, Node.js, browser, security, and support behavior before relying on version-specific guidance.
