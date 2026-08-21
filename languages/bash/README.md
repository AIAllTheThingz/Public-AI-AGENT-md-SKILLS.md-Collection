---
id: BASH-PKG-001
status: baseline
title: Bash Package
---

# Bash Language Package

This package provides project-agnostic engineering standards for Bash scripts, sourced libraries, installers, CI helpers, and operational automation.

It defines how coding agents should inspect, design, implement, test, secure, document, and report shell work. It does not define the adopting project's production targets, privilege model, deployment environment, or approved external utilities.

## Package status

**Status:** `baseline`

The package is structurally complete and suitable for adoption. Projects must tailor interpreter, platform, portability, dependency, privilege, and organization-specific requirements before treating it as a final production standard.

## Intended scope

- Bash scripts and sourced libraries
- installation and bootstrap tooling
- CI and build helpers
- administrative and operational automation
- tests, static analysis, and portability documentation

## Runtime baseline

- Declare the minimum supported Bash version.
- Use a Bash shebang for Bash syntax.
- Do not advertise `/bin/sh` or POSIX compatibility while using Bash-only features.
- Declare supported operating systems, shells, utility implementations, locales, and filesystems.
- Validate external command availability before mutation.

## Package structure

| Path | Purpose |
|---|---|
| [`AGENTS.md`](AGENTS.md) | Mandatory Bash-specific operating rules |
| [`MANIFEST.md`](MANIFEST.md) | Package inventory and adoption checklist |
| [`standards/`](standards/) | Coding, portability, safety, security, testing, dependency, and evidence standards |
| [`templates/`](templates/) | Adoption templates |
| [`examples/`](examples/) | Example package composition |

## Required standards

| Standard | Governs |
|---|---|
| [`BASH_CODING_STANDARD.md`](standards/BASH_CODING_STANDARD.md) | Quoting, arrays, functions, exit status, cleanup, and maintainability |
| [`ARCHITECTURE_STANDARD.md`](standards/ARCHITECTURE_STANDARD.md) | Script boundaries, configuration, sourced libraries, side effects, and decomposition |
| [`DOCUMENTATION_STANDARD.md`](standards/DOCUMENTATION_STANDARD.md) | Usage, parameters, environment variables, examples, and operator guidance |
| [`TESTING_STANDARD.md`](standards/TESTING_STANDARD.md) | Syntax, unit, integration, negative-path, and environment testing |
| [`SECURITY_STANDARD.md`](standards/SECURITY_STANDARD.md) | Injection, temporary files, permissions, secrets, downloads, and secure defaults |
| [`DEPENDENCY_MANAGEMENT_STANDARD.md`](standards/DEPENDENCY_MANAGEMENT_STANDARD.md) | External commands, version assumptions, provenance, and availability checks |
| [`OBSERVABILITY_STANDARD.md`](standards/OBSERVABILITY_STANDARD.md) | Diagnostic output, timestamps, exit codes, redaction, and logging |
| [`PORTABILITY_STANDARD.md`](standards/PORTABILITY_STANDARD.md) | Bash versus POSIX behavior, utilities, platforms, locales, and compatibility |
| [`SAFE_AUTOMATION_STANDARD.md`](standards/SAFE_AUTOMATION_STANDARD.md) | Discovery, dry run, confirmation, idempotence, destructive actions, and rollback |
| [`COMPLETION_EVIDENCE.md`](standards/COMPLETION_EVIDENCE.md) | Proof required before completion claims |

## Adoption procedure

1. Inventory scripts, callers, sourced files, environment variables, external commands, tests, and deployment mechanisms.
2. Declare the interpreter, minimum version, supported operating systems, and portability claims.
3. Document every required external command and the behavior relied upon.
4. Define parameter, environment, file, path, archive, and command-output trust boundaries.
5. Define privilege, elevation, remote execution, and credential handling.
6. Define dry-run, confirmation, idempotence, lock, retry, rollback, and cleanup behavior.
7. Define syntax, ShellCheck, formatting, Bats, integration, and platform validation.
8. Add applicable discipline, framework, platform, virtualization, operating-system, networking, and project-profile overlays.
9. Review templates and examples before adoption.
10. Review the composed standard with an accountable shell maintainer.

## Project tailoring checklist

- [ ] Minimum Bash version and portability target are declared.
- [ ] Supported operating systems, shells, locales, and utility implementations are documented.
- [ ] Required external commands and minimum behavior are documented.
- [ ] Privilege, elevation, remote execution, and credential requirements are defined.
- [ ] Input, path, glob, option, archive, and command-injection controls are defined.
- [ ] Dry-run, confirmation, idempotence, rollback, retry, lock, and cleanup behavior are defined.
- [ ] Logging, output streams, exit codes, redaction, and retention are defined.
- [ ] Syntax, ShellCheck, formatting, Bats, integration, and platform tests are defined.
- [ ] Distribution, signing, download verification, and update requirements are defined.

## Bash-specific safety expectations

- Quote expansions unless deliberate splitting or globbing is documented.
- Use arrays for command arguments rather than constructing command strings.
- Do not use `eval` to avoid proper argument handling.
- Do not download and execute remote content directly.
- Use secure temporary directories and restrictive permissions.
- Use traps for cleanup, but do not let cleanup hide the original failure.
- Use `--` before untrusted positional arguments where supported.
- Validate targets and current state before destructive or bulk actions.

## Validation baseline

Use repository-defined commands when available:

```text
bash --version
bash -n <script>
shellcheck <script-or-directory>
shfmt -d <script-or-directory>
bats <test-directory>
```

Only run tools that are part of the declared project toolchain. Test supported platforms when portability is claimed.

## Testing expectations

Tests should cover parsing, branching, invalid input, paths with spaces and special characters, failed external commands, cleanup, retries, dry-run behavior, idempotence, privilege failures, and supported platform differences.

Tests must use controlled fixtures and must not target production systems.

## Completion evidence

A completion report must identify scripts and files changed, supported shells and platforms, external dependencies, privilege and state-change impact, syntax and test commands, dry-run evidence, checks not run, limitations, assumptions, and remaining risk.

## Templates and examples

- [`AGENTS_TEMPLATE.md`](templates/AGENTS_TEMPLATE.md)
- [`ADOPTION_CHECKLIST.md`](templates/ADOPTION_CHECKLIST.md)
- [`ADOPTION_EXAMPLE.md`](examples/ADOPTION_EXAMPLE.md)

## What this package does not decide

The adopting repository must still define production targets, scheduling, change approval, credentials, remote execution, data classification, incident response, backup, recovery, and organization-specific compliance.

This package improves agent behavior. It does not guarantee that generated shell automation is secure, correct, portable, compliant, or safe to run in production.

## Authoritative starting points

- [GNU Bash Reference Manual (Bash)](https://www.gnu.org/software/bash/manual/bash.html)
- [POSIX Shell Command Language (POSIX `sh`)](https://pubs.opengroup.org/onlinepubs/9799919799/utilities/V3_chap02.html)
- [POSIX Utilities (external command behavior)](https://pubs.opengroup.org/onlinepubs/9799919799/utilities/contents.html)

Revalidate the selected Bash version, declared POSIX target, external utilities, security, and support behavior before relying on version-specific guidance.
