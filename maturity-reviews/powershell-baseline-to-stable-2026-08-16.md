---
id: MATURITY-POWERSHELL-2026-08-16
title: PowerShell Baseline to Stable Maturity Review
version: 1.0.0
status: baseline
---

# PowerShell Baseline to Stable Maturity Review

## Review identity

- Review ID: `MR-POWERSHELL-2026-08-16`
- Component: `languages/powershell`
- Component version: `unversioned package at repository VERSION 0.10.0 plus post-release compatibility correction`
- Repository commit reviewed: `ba4901c72f4c1fccda517280946f1fb1b6d2824c`
- Current maturity: `baseline`
- Proposed maturity: `stable`
- Owner: `Language standards maintainers`
- Reviewers: `AIAllTheThingz` maintainer evidence review
- Review date: `2026-08-16`

## Scope and applicability

This review considers the PowerShell language package, including the post-pilot Windows PowerShell 5.1 compatibility overlay added by #65 / PR #67.

## Normative quality

The package is broad and structurally complete, with runtime, module, remoting, testing, security, dependency, operational, and completion-evidence guidance. The new legacy overlay appropriately preserves PowerShell 7 as the default while requiring `powershell.exe` evidence for Windows PowerShell 5.1 claims.

## Adoption evidence

- Package-level #47 PowerShell adoption exercise: Passed against published `v0.10.0`.
- Enterprise-PS-Scripts real pilot: manifest/composition, `pwsh` parsing, and module-manifest validation passed; Pester **Failed** because no `*.Tests.ps1` files exist. Downstream issue `AIAllTheThingz/Enterprise-PS-Scripts#1` remains open.
- WindowsScriptRunner real pilot: PowerShell 7-oriented parser evidence passed as part of the mixed-system pilot.

The Windows PowerShell 5.1 overlay did not exist in published `v0.10.0`; it was created *because* of the Enterprise pilot and therefore has not yet received a real downstream `powershell.exe` adoption exercise at the current package revision.

## Compatibility inventory

The package exposes PowerShell 7-first guidance, Windows PowerShell 5.1 compatibility guidance, remoting/module/script standards, templates, operational safety behavior, and completion evidence. Runtime and module behavior differs substantially between `pwsh` and `powershell.exe`, so a stable promise must be explicit per runtime.

## Validation evidence

Repository validation and the #65 focused/full regression suites passed. The missing evidence is not repository CI; it is representative **current-revision runtime adoption evidence** for the newly added Windows PowerShell 5.1 overlay and downstream behavioral tests in Enterprise-PS-Scripts.

## Source currency

- Authoritative sources reviewed: Microsoft PowerShell support lifecycle
- Last source review date: `2026-08-15`
- Current source-review registry maturity: `baseline`
- Known concern: Windows PowerShell compatibility follows the applicable Windows and vendor-module lifecycle and cannot be inferred from PowerShell 7 validation

## Security and operational review

The package has strong operational safety boundaries. The reason for deferral is evidence completeness, not an identified security-policy weakness.

## Open findings and conditions

- Enterprise-PS-Scripts has no Pester tests; downstream issue `AIAllTheThingz/Enterprise-PS-Scripts#1` remains open.
- No real downstream `powershell.exe` exercise has validated the post-#67 Windows PowerShell 5.1 overlay.
- The current package revision differs materially from the `v0.10.0` package-level test because the legacy compatibility overlay was added after the pilots.

## Decision

`deferred`

## Rationale

PowerShell has useful adoption evidence, but promoting now would let the stable label outrun the current package revision. The package remains `baseline` until the newly added legacy-runtime path receives representative runtime evidence and the downstream testing gap is addressed or otherwise evaluated with sufficient independent evidence.

## Conditions and owners

- Exercise the current Windows PowerShell 5.1 overlay under `powershell.exe` in a representative Windows downstream project.
- Add or independently substitute meaningful behavior-level PowerShell test evidence for the Enterprise pilot gap.
- Owner: `Language standards maintainers` with downstream project owners for their own test suites.

## Next review

- Next review date or trigger: `after current-revision Windows PowerShell 5.1 downstream evidence and representative PowerShell behavioral tests exist`
- Responsible owner: `Language standards maintainers`

## Release linkage

- Target repository release: `Not scheduled while deferred`
- Release-note entry: `No stable promotion; deferral recorded under issue #42`
