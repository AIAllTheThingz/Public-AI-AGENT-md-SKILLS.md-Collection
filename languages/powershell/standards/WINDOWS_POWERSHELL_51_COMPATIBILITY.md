# Windows PowerShell 5.1 Compatibility Overlay

## Purpose

Provide an explicit legacy-adoption path for repositories that must retain **Windows PowerShell 5.1** while adopting the runtime-neutral safety, testing, security, documentation, and completion-evidence controls from the PowerShell package.

PowerShell 7 remains the package default for new modern work. This overlay is not a recommendation to start new projects on Windows PowerShell 5.1, and it does not extend the support lifecycle of Windows, Windows PowerShell, or any vendor module.

## When this overlay applies

Use this overlay only when the adopting repository explicitly documents a Windows PowerShell 5.1 requirement, such as:

- supported Windows Server estates that still depend on Windows PowerShell-only administrative modules;
- legacy vendor modules that do not support PowerShell 7;
- Windows PowerShell remoting or host behavior that is part of the supported compatibility contract;
- an existing automation estate where runtime migration is outside the approved change scope.

If the repository does not explicitly require Windows PowerShell 5.1, use the normal PowerShell 7 baseline.

## Required adoption declaration

The adopting repository must record:

- Windows PowerShell 5.1 as an explicit supported runtime;
- the supported Windows versions and architectures;
- modules and vendor tooling that require or constrain the legacy runtime;
- whether PowerShell 7 is also supported;
- runtime-specific code paths, encoding assumptions, remoting behavior, and .NET dependencies;
- the validation commands actually executed for each claimed runtime.

Do not infer Windows PowerShell 5.1 support from syntax that happens to parse under PowerShell 7.

## Runtime compatibility rules

For a Windows PowerShell 5.1 compatibility boundary:

- avoid PowerShell 7-only syntax such as ternary expressions, null-coalescing operators, pipeline-chain operators, and `ForEach-Object -Parallel`;
- avoid PowerShell 7-only cmdlets, parameters, .NET APIs, and module versions unless they are behind a separately validated runtime-specific path;
- treat text encoding, JSON behavior, native-process invocation, remoting, TLS defaults, and module-loading behavior as runtime-sensitive until validated;
- keep Windows-only modules and host assumptions explicit;
- preserve `[CmdletBinding(SupportsShouldProcess)]`, `-WhatIf`, `-Confirm`, input validation, least privilege, target identity, rollback/recovery, idempotence, structured results, and truthful failure reporting from the main package wherever applicable;
- do not bypass execution policy, signing, TLS, certificate, authentication, or authorization controls to make legacy automation run.

## Validation evidence

A claim of Windows PowerShell 5.1 compatibility requires validation with **`powershell.exe`** on an applicable Windows environment.

Typical evidence can include:

```powershell
powershell.exe -NoProfile -Command "$PSVersionTable"
powershell.exe -NoProfile -Command "Invoke-ScriptAnalyzer -Path . -Recurse"
powershell.exe -NoProfile -Command "Invoke-Pester -Path ./tests -CI"
```

Use repository-specific commands when they differ.

A `pwsh` parser pass, Pester run under PowerShell 7, or successful execution on Linux/macOS is useful additional evidence but **does not prove Windows PowerShell 5.1 runtime compatibility**.

If Windows PowerShell 5.1 validation cannot run, record it as `NotRun` or `Blocked` and do not claim validated 5.1 compatibility.

## Dual-runtime adoption

A repository that claims both Windows PowerShell 5.1 and PowerShell 7 support must:

- declare both runtimes and their minimum versions;
- validate meaningful behavior under both `powershell.exe` and `pwsh`;
- keep runtime-specific branches narrow and documented;
- test module/import behavior and remoting separately when they differ;
- report failures and checks not run per runtime rather than merging the evidence into one generic “PowerShell passed” statement.

## Source and lifecycle boundary

This overlay does not make Windows PowerShell 5.1 a current greenfield baseline. Windows PowerShell support follows the applicable supported Windows host and Microsoft/vendor module lifecycle. Adopters must verify the exact host, module, and product support boundary before relying on legacy automation.

## Completion boundary

Applying this overlay means only that a documented legacy runtime boundary can compose with the package without pretending to be PowerShell 7. Production readiness still requires project-specific target, authorization, security, runtime, module, integration, recovery, and validation evidence.
