# PowerShell Agent Standard Package

This package provides project-agnostic engineering standards for PowerShell 7 scripts, modules, administrative tooling, remoting, and operational automation. Repositories with an explicit legacy Windows PowerShell 5.1 contract may compose the dedicated compatibility overlay without changing the package's PowerShell 7 default for new work.

It defines how coding agents should inspect, design, implement, test, secure, document, and report PowerShell work. It does not define the adopting project's production targets, credentials, business workflow, or change-approval process.

## Intended scope

- PowerShell scripts and advanced functions
- PowerShell modules and module manifests
- administrative and infrastructure automation
- remote execution and integration code
- Pester tests and static analysis
- signing, release, and operator documentation

## Runtime baseline

- Target PowerShell 7.x and execute with `pwsh`.
- Do not assume Windows PowerShell 5.1 compatibility unless explicitly required. When it is required, apply [`WINDOWS_POWERSHELL_51_COMPATIBILITY.md`](standards/WINDOWS_POWERSHELL_51_COMPATIBILITY.md) and validate with `powershell.exe`.
- Declare the minimum supported PowerShell version for every claimed runtime.
- Identify Windows-only, Linux-only, and macOS-only behavior.
- Do not claim cross-platform support without evidence.

## Package structure

| Path | Purpose |
|---|---|
| [`AGENTS.md`](AGENTS.md) | Mandatory PowerShell-specific operating rules |
| [`standards/`](standards/) | Detailed coding, documentation, testing, security, and evidence requirements |
| [`templates/`](templates/) | Reference script, module, and function starting points |

## Required standards

Agents must read the applicable standards before implementation:

| Standard | Governs |
|---|---|
| [`POWERSHELL_CODING_STANDARD.md`](standards/POWERSHELL_CODING_STANDARD.md) | Syntax, functions, parameters, structured output, errors, and maintainability |
| [`DOCUMENTATION_STANDARD.md`](standards/DOCUMENTATION_STANDARD.md) | Comment-based help, examples, headers, assumptions, and operator guidance |
| [`TESTING_STANDARD.md`](standards/TESTING_STANDARD.md) | Pester coverage, mocks, isolation, negative paths, and evidence |
| [`SECURITY_STANDARD.md`](standards/SECURITY_STANDARD.md) | Credentials, remoting, native commands, validation, least privilege, and signing |
| [`COMPLETION_EVIDENCE.md`](standards/COMPLETION_EVIDENCE.md) | Proof required before claiming completion |
| [`WINDOWS_POWERSHELL_51_COMPATIBILITY.md`](standards/WINDOWS_POWERSHELL_51_COMPATIBILITY.md) | Explicit legacy Windows PowerShell 5.1 adoption and dual-runtime evidence boundary |

Opening only `AGENTS.md` and ignoring its referenced standards is not compliant adoption.

## Product modules and overlays

Product-specific PowerShell modules require both this language package and the owning product package. For vSphere and ESXi automation, apply the [`virtualization/vsphere-esxi` package](../../virtualization/vsphere-esxi/) and its [VCF PowerCLI automation standard](../../virtualization/vsphere-esxi/standards/POWERCLI_AUTOMATION_STANDARD.md).

For new dependency evaluations, `VCF.PowerCLI` is the current Broadcom distribution name. Existing `VMware.PowerCLI` references require a reviewed compatibility or migration decision; child modules may retain `VMware.*` names and must not be blindly renamed.

## Core safety expectations

- Perform discovery and validation before mutation.
- Stop when prerequisites are missing or the target is ambiguous.
- Use `[CmdletBinding(SupportsShouldProcess)]` for state-changing scripts and functions where applicable.
- Call `$PSCmdlet.ShouldProcess()` around the actual change.
- Respect `-WhatIf` and `-Confirm`.
- Validate current state before changing it and verify resulting state afterward.
- Return structured objects from reusable functions.
- Do not use formatting commands inside reusable functions.
- Do not use `Write-Host` as a substitute for pipeline output.
- Do not use `Invoke-Expression`, downloaded code execution, disabled TLS validation, or execution-policy bypasses as shortcuts.

## Adoption procedure

1. Inventory the existing scripts, modules, tests, configuration, and deployment process.
2. Declare the minimum PowerShell version and supported operating systems.
3. Document required modules and approved versions.
4. Define credential sources, remoting transport, and authentication requirements.
5. Define whether code signing is required and how signatures are validated.
6. Define reporting, logging, scheduling, and unattended-execution behavior.
7. Select applicable discipline, framework, platform, virtualization, operating-system, networking, and project-profile overlays.
8. Add project-specific rules without weakening this package.
9. Record the real validation commands in project documentation.
10. Review the composed standard with an accountable PowerShell maintainer.

## Project tailoring checklist

- [ ] Runtime and minimum supported version are declared. PowerShell 7 remains the default; an explicit Windows PowerShell 5.1 boundary uses the compatibility overlay.
- [ ] Supported operating systems and editions are documented.
- [ ] Required modules and version constraints are documented.
- [ ] Credential and secret-management mechanisms are defined.
- [ ] WinRM, SSH, API, database, or local execution boundaries are documented.
- [ ] Privilege and elevation requirements are explicit.
- [ ] Dry-run, confirmation, idempotence, rollback, and retry behavior are defined.
- [ ] Logging, reporting, redaction, and retention requirements are defined.
- [ ] Code-signing and execution-policy requirements are defined where applicable.
- [ ] Test, static-analysis, and release evidence requirements are defined.

## Validation baseline

Use repository-defined commands when available. Typical checks include:

```powershell
pwsh --version
Invoke-ScriptAnalyzer -Path . -Recurse
Invoke-Pester -Path ./tests -CI
Get-AuthenticodeSignature -FilePath <script-or-module>
```

Do not claim a check passed unless it was actually run successfully against the relevant revision. A repository claiming Windows PowerShell 5.1 support must also run applicable checks under `powershell.exe`; a `pwsh` result is not 5.1 runtime proof.

## Testing expectations

Tests should cover:

- normal behavior
- invalid and boundary input
- remote and external dependency failures
- privilege and authorization failures
- `-WhatIf` and confirmation paths
- idempotent reruns
- cleanup and partial-success behavior
- platform-specific behavior

Mocks should be applied at controlled integration boundaries rather than used to duplicate the implementation.

## Documentation expectations

Public scripts and functions require complete comment-based help. Documentation should explain:

- purpose and scope
- parameters and pipeline behavior
- examples using fictitious values
- required modules and privileges
- credentials and secret handling
- state changes and safety controls
- logging and report outputs
- expected errors and recovery behavior
- platform and runtime limitations

## Completion evidence

A completion report must identify:

- files created, modified, or deleted
- behavior and state changes
- security and compatibility impact
- tests and validation commands actually run
- results or CI evidence
- documentation updated
- checks not run and why
- limitations, assumptions, and remaining risk

## Templates

| Template | Use |
|---|---|
| [`SCRIPT_TEMPLATE.ps1`](templates/SCRIPT_TEMPLATE.ps1) | Script entry point |
| [`MODULE_TEMPLATE.psm1`](templates/MODULE_TEMPLATE.psm1) | Module starting point |
| [`FUNCTION_TEMPLATE.ps1`](templates/FUNCTION_TEMPLATE.ps1) | Advanced function starting point |

Templates are references, not production-ready artifacts. Replace placeholders and review safety, error handling, dependencies, and compatibility before use.

## What this package does not decide

The adopting repository must still define production targets, scheduling, deployment, credential sources, change approval, data classification, backup, recovery, and organization-specific compliance.

This package improves agent behavior. It does not guarantee that generated automation is secure, correct, compliant, or safe to run in production.

## Authoritative starting points

- [PowerShell documentation](https://learn.microsoft.com/en-us/powershell/)
- [PowerShell scripting overview](https://learn.microsoft.com/en-us/powershell/scripting/overview?view=powershell-7.6)
- [about language keywords](https://learn.microsoft.com/en-us/powershell/module/microsoft.powershell.core/about/about_language_keywords?view=powershell-7.6)
- [PSScriptAnalyzer](https://github.com/PowerShell/PSScriptAnalyzer)
- [Pester documentation](https://pester.dev/docs/quick-start)

Revalidate current PowerShell, module, analyzer, security, and platform-support behavior before relying on version-specific guidance.
