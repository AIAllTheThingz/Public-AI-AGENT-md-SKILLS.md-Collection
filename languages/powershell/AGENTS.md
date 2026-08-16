# PowerShell Agent Standard

## Purpose

This file defines the mandatory operating rules for coding agents that create, modify, review, test, or document PowerShell code within this repository.

The standard is project-agnostic. It governs how PowerShell work is performed, not the business purpose of any individual script or module.

The primary objective is:

> Make the smallest safe, maintainable, testable, and well-documented change that satisfies the stated requirement.

## Scope

These instructions apply to:

- PowerShell scripts
- PowerShell modules
- Module manifests
- Pester tests
- PowerShell configuration examples
- Build and validation scripts
- Documentation describing PowerShell behavior
- Generated examples and templates
- Reviews and refactoring of existing PowerShell code

## Instruction Priority

When instructions conflict, apply them in this order:

1. Explicit user requirements
2. More specific nested `AGENTS.md` instructions
3. This root `AGENTS.md`
4. Repository documentation and established conventions
5. General coding-agent preferences

Do not silently resolve a material conflict. Follow the higher-priority instruction and report the conflict in the completion summary.

## Required Supporting Standards

Before creating or modifying PowerShell code, read and follow these files:

- `standards/POWERSHELL_CODING_STANDARD.md`
- `standards/DOCUMENTATION_STANDARD.md`
- `standards/TESTING_STANDARD.md`
- `standards/SECURITY_STANDARD.md`
- `standards/COMPLETION_EVIDENCE.md`
- `standards/WINDOWS_POWERSHELL_51_COMPATIBILITY.md` when the adopting repository explicitly requires Windows PowerShell 5.1 or claims dual-runtime compatibility

These files are mandatory extensions of this `AGENTS.md`.

If a supporting standard conflicts with this file, this file takes precedence.

### Product-specific module overlays

When PowerCLI is used for vSphere or ESXi automation, also read the [`virtualization/vsphere-esxi` package](../../virtualization/vsphere-esxi/) and its [VCF PowerCLI automation standard](../../virtualization/vsphere-esxi/standards/POWERCLI_AUTOMATION_STANDARD.md).

This package remains authoritative for PowerShell language behavior. The vSphere standard adds product-specific connection, certificate, inventory, task, evidence, and test requirements; it may strengthen but not weaken these rules.

## PowerShell Runtime

PowerShell 7.x executed with `pwsh` is the default runtime for new work.

An adopting repository may retain an explicitly documented Windows PowerShell 5.1 compatibility boundary only when that runtime is a real project requirement. In that case, the Windows PowerShell compatibility overlay is mandatory and 5.1 evidence must be collected under `powershell.exe`; validation under `pwsh` must not be presented as proof of 5.1 runtime behavior.

Requirements:

- Use PowerShell Core for the default PowerShell 7 path.
- Do not assume `powershell.exe` is the intended runtime unless the repository explicitly declares a Windows PowerShell 5.1 boundary.
- Do not add Windows PowerShell 5.1 compatibility speculatively.
- Declare the minimum supported version for every runtime the repository claims.
- Do not introduce syntax, modules, or .NET APIs that require a newer runtime than the repository supports.
- Do not claim cross-platform compatibility without evidence.
- Identify Windows-only, Linux-only, or macOS-only behavior explicitly.

## Non-Negotiable Rules

### Safe behavior

- Default to the safest practical behavior.
- Perform discovery and validation before modification.
- Stop when prerequisites are missing, validation fails, or the target is ambiguous.
- Do not weaken security controls to make code succeed.
- Do not perform destructive or state-changing actions without explicit authorization.
- Use the narrowest operation that satisfies the requirement.

### Scope control

- Make the smallest coherent change.
- Do not modify unrelated files, behavior, formatting, or dependencies.
- Do not perform broad refactoring unless explicitly requested or required for safety or correctness.
- Preserve existing public behavior unless the requirement explicitly changes it.
- Stop when the requested outcome has been achieved and validated.

### No invented environment details

Do not invent or hardcode:

- Server names
- Domain names
- User names
- Production paths
- API endpoints
- Tenant identifiers
- Database names
- Credentials
- Secret locations
- Operational assumptions

Use documented placeholders or configuration inputs for unknown values.

### Secrets and sensitive data

Never place credentials or sensitive values in:

- Source code
- Tests
- Documentation examples
- Logs
- Reports
- Error messages
- Committed configuration files

Use approved credential and secret-management mechanisms. Do not convert credentials to plaintext unless a required integration leaves no secure alternative and the exception is documented.

### Input validation

Treat all external input as untrusted, including:

- Parameters
- Pipeline input
- CSV, JSON, XML, and PSD1 files
- Environment variables
- API responses
- Database values
- File names and paths
- Remote-system output
- User-supplied native-command arguments

Validate data type, allowed values, format, range, existence, and operational safety before use.

### State-changing functions

Functions or scripts that modify state must:

- Use `[CmdletBinding(SupportsShouldProcess)]`
- Call `$PSCmdlet.ShouldProcess()` around the actual modification
- Respect `-WhatIf`
- Respect `-Confirm`
- Validate current state before modification
- Verify resulting state after modification
- Report whether a change occurred
- Avoid reporting success when `-WhatIf` prevented execution

High-risk or bulk operations should also require an explicit execution mode or switch. Native `ShouldProcess` support remains mandatory.

### Unsafe execution

The following are prohibited by default:

- `Invoke-Expression`
- Executing dynamically constructed PowerShell text
- Downloading and immediately executing remote code
- Disabling certificate validation
- Ignoring TLS errors
- Bypassing execution policy
- Disabling firewalls, antivirus, or endpoint protection
- Executing arbitrary user-supplied script blocks
- Loading untrusted assemblies or modules

Any exception requires an explicit requirement, documented risk, validated input boundaries, and an explanation of why safer alternatives are insufficient.

### Structured output

Reusable functions must return structured objects.

Do not use formatting commands inside reusable functions:

- `Format-Table`
- `Format-List`
- `Format-Wide`
- `Out-String`

Do not use `Write-Host` as a substitute for pipeline output.

### Error handling

- Do not use empty `catch` blocks.
- Do not silently discard failures.
- Do not report failed operations as successful.
- Use terminating errors when execution cannot safely continue.
- Preserve useful exception context.
- Clean up sessions, files, and resources.
- Report partial success accurately.
- Do not expose secrets in errors.

### Least privilege

- Do not require elevation unless the operation requires it.
- Document required privileges.
- Do not bypass access controls.
- Separate privileged and non-privileged operations where practical.
- Use the narrowest permissions necessary.

### Documentation

- Public scripts and functions require complete comment-based help.
- Non-trivial logic requires administrator-friendly inline comments.
- Comments must explain intent, safety controls, assumptions, external dependencies, and expected failure behavior.
- Keep comments synchronized with code.
- Remove obsolete commented-out code.
- Do not add comments that merely restate obvious syntax.

### Testing and validation

- Run PowerShell syntax validation.
- Run PSScriptAnalyzer against changed PowerShell files.
- Add or update Pester tests for meaningful behavior changes.
- Add regression tests for bug fixes where practical.
- Do not weaken tests to obtain a passing result.
- Do not connect unit tests to production systems.
- Report validation that was not run and explain why.

### Honest reporting

Do not claim:

- Fully tested
- Production ready
- Secure
- Cross-platform
- Compatible with all PowerShell 7 versions
- Issue resolved

unless available evidence supports the claim.

## Required Agent Workflow

Follow this sequence for non-trivial work:

1. Read all applicable instruction and repository files.
2. Inspect the repository structure and relevant implementation.
3. Identify runtime, operating-system, module, and dependency requirements.
4. Define the requested scope and expected deliverables.
5. Assess operational and security risk.
6. Inspect existing callers, tests, output schemas, and documentation.
7. Choose the smallest coherent implementation.
8. Implement discovery and validation before modification.
9. Add safety controls before state-changing behavior.
10. Add or update tests alongside the change.
11. Run syntax checks, static analysis, and applicable tests.
12. Review the full diff for unrelated changes, secrets, placeholders, and artifacts.
13. Update documentation affected by the change.
14. Report completion evidence and limitations.

## Required Coding Practices

At minimum:

- Use approved PowerShell verbs.
- Use `Verb-Noun` function names.
- Use advanced functions for public commands.
- Use typed and validated parameters.
- Prefer named parameters over positional binding.
- Do not use aliases in committed code.
- Avoid global variables.
- Use `$PSScriptRoot` for script-relative paths.
- Use `-LiteralPath` when wildcard behavior is not intended.
- Prefer structured output over formatted text.
- Use UTC and ISO 8601 for machine-consumed timestamps.
- Check `$LASTEXITCODE` for native commands when applicable.
- Pass native-command arguments as discrete values.
- Avoid modifying global PowerShell configuration.
- Do not execute substantial work during module import.
- Keep public interfaces stable unless a breaking change is required and documented.
- Use UTF-8 source encoding.
- Preserve repository line-ending and formatting conventions.

## Standard Validation Commands

Use repository-provided commands when available. Otherwise, use appropriate equivalents such as:

```powershell
# Parse all PowerShell files.
$ParseErrors = @()

Get-ChildItem -Path . -Recurse -File -Include '*.ps1', '*.psm1', '*.psd1' |
    ForEach-Object {
        $Tokens = $null
        $Errors = $null

        [System.Management.Automation.Language.Parser]::ParseFile(
            $_.FullName,
            [ref] $Tokens,
            [ref] $Errors
        ) | Out-Null

        $ParseErrors += $Errors
    }

if ($ParseErrors.Count -gt 0) {
    $ParseErrors | Format-List
    throw "PowerShell parsing failed with $($ParseErrors.Count) error(s)."
}
```

```powershell
# Static analysis.
Invoke-ScriptAnalyzer -Path . -Recurse -Severity Warning, Error
```

```powershell
# Pester tests.
Invoke-Pester -Path ./tests -Output Detailed
```

```powershell
# Module manifest validation, when applicable.
Test-ModuleManifest -Path ./src/ModuleName/ModuleName.psd1
```

Do not pretend a command ran if the required tool or dependency was unavailable.

## Definition of Done

Work is complete only when:

- The requested behavior is implemented.
- Unrelated behavior remains unchanged.
- Safety controls are present where required.
- Documentation is updated.
- Tests are added or updated where applicable.
- Syntax validation passes.
- PSScriptAnalyzer results are reviewed.
- Applicable Pester tests pass.
- The final diff is reviewed.
- Remaining limitations and risks are documented.

The completion response must follow `standards/COMPLETION_EVIDENCE.md`.
