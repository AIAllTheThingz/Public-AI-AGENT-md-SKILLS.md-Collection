---
id: CSHARP-SCRIPT-001
title: C# Scripting and Tooling Standard
version: 0.1.0
status: stable
---

# C# Scripting and Tooling Standard

## Purpose

Define reproducible and safe behavior for `.csx`, file-based C# applications, compiler scripting hosts, local tools, administrative automation, and build helpers.

## Host and dependency boundary

- Declare the exact scripting/file-app host, SDK/compiler, language version, operating systems, and invocation command.
- Pin tools through the repository's approved mechanism.
- Pin or constrain script dependencies and use approved sources.
- Do not use floating directives or automatic remote dependency acquisition during operational execution.
- Do not assume an IDE scripting host, `csi`, `dotnet-script`, notebook kernel, or file-based app support is available merely because C# is installed.
- Keep script execution policy and trust separate from ordinary compiled application deployment.

## Safe automation phases

State-changing automation must separate:

1. discovery
2. validation
3. preview or dry-run
4. impact and authorization
5. execution
6. actual-state verification
7. structured reporting and cleanup

Default to non-mutating behavior where practical. Consequential execution requires explicit enablement and accountable authorization.

## Input and command safety

- Use typed options or a documented parser rather than ad hoc argument indexing for reusable tools.
- Validate paths, URLs, identifiers, file formats, sizes, counts, encodings, and environment variables before use.
- Pass native process arguments as discrete values and avoid a shell unless shell semantics are the explicit requirement.
- Bound subprocess time, output, environment, working directory, and privileges.
- Never download and immediately execute code.
- Do not accept arbitrary C# expressions, script fragments, assemblies, or type names from untrusted input.

## Results and failure behavior

- Return structured results from reusable logic and keep presentation at the entry point.
- Define stable exit codes for success, validation failure, authorization refusal, partial failure, execution failure, and unknown outcome where relevant.
- Write diagnostics to the correct channel and keep machine-readable output parseable.
- Treat partial success and timeout accurately; do not flatten them into success.
- Preserve correlation identifiers and per-target outcomes for batch operations.

## Credentials and state

- Use approved credential and secret providers.
- Do not persist secrets, authenticated sessions, or sensitive inventory in source, script history, arguments, logs, or temporary files.
- Use least privilege and narrow target scope.
- Clean up only state and resources created by the current execution.
- Make rerun behavior idempotent or provide a checkpoint and recovery procedure.

## Testing

Move reusable logic into testable compiled units where practical. Test parsing, validation, dry-run with zero mutation, authorization refusal, process failure, timeout, partial results, redaction, cleanup, exit codes, and rerun behavior.

Do not use production as the first integration environment.

## Evidence

Record the host/tool versions, dependency resolution, exact invocation, selected target scope, preview evidence, authorization state, per-target results, exit code, cleanup, verification, tests, checks not run, and residual risk.
