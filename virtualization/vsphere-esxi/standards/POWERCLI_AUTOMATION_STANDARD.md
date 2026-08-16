---
id: VIRT-VSPH-PCLI-STD-001
title: VCF PowerCLI Automation Standard for VMware vSphere and ESXi
version: 0.1.0
status: baseline
---

# VCF PowerCLI Automation Standard for VMware vSphere and ESXi

## Purpose

Define the mandatory product-specific contract for PowerShell automation that uses Broadcom VCF PowerCLI to discover, validate, plan, change, or verify VMware vSphere and ESXi state.

This standard composes with the [PowerShell package](../../../languages/powershell/) and the [vSphere operations and automation standard](OPERATIONS_AND_AUTOMATION_STANDARD.md). The PowerShell package governs language engineering; this standard adds vSphere control-plane requirements. Neither may weaken the other.

## Applicability

Apply this standard to scripts, modules, functions, jobs, runbooks, CI/CD tasks, and operator procedures that load PowerCLI modules or invoke PowerCLI cmdlets against vCenter Server or an explicitly standalone ESXi host.

It applies to read-only automation as well as mutation because connecting to the wrong endpoint, accepting an untrusted certificate, leaking inventory, or querying ambiguous global connection state can still create security or operational risk.

## Distribution and naming boundary

- Treat `VCF.PowerCLI` as the current Broadcom distribution name for new dependency evaluations.
- Treat existing `VMware.PowerCLI` distribution references as a compatibility and migration decision, not as an automatic search-and-replace task.
- Do not infer that an installation is obsolete merely because child modules or namespaces retain `VMware.*` names.
- Record the distribution package, imported child modules, resolved versions, source repository, PowerShell version, operating system, target product version, and validation date.
- Verify the supported installation, migration, and compatibility path against current Broadcom documentation before changing dependencies.

The accountable VCF PowerCLI source-review state is maintained in [`../../../SOURCE_REVIEWS.json`](../../../SOURCE_REVIEWS.json) with durable evidence under [`../../../source-reviews/`](../../../source-reviews/). The 2026-08-15 accountable review found the current Broadcom portal advertising VCF PowerCLI 9.1. This observation is not a version pin or a compatibility certification. Adopters must revalidate the current release and its support boundary.

## Dependency and runtime management

- Use PowerShell 7 unless an explicitly documented, reviewed product requirement mandates another runtime.
- Install modules only from an approved repository and verify publisher, integrity, and provenance controls available to the adopting environment.
- Pin an exact tested version for reproducible automation or define a reviewed bounded constraint with a documented update process.
- Separate dependency installation and upgrade from operational execution. Operational scripts must not silently install or update PowerCLI.
- Fail closed when required modules or cmdlets are missing, outside the approved version constraint, shadowed by an unexpected command, or incompatible with the target.
- Inspect the commands and module versions actually resolved in the execution environment; do not rely only on a package manifest or an operator workstation claim.
- Load only the modules required for the task where practical, and do not alter persistent module paths as an execution shortcut.

## Endpoint, certificate, and identity controls

- Accept the intended vCenter Server or standalone ESXi endpoint as validated configuration, not as an invented default.
- Resolve and record endpoint class, environment, product identity, instance identity where available, version/build, and certificate identity before mutation.
- Validate the certificate chain and expected endpoint identity using the adopting environment's approved trust process before transmitting credentials.
- Do not set certificate handling to ignore invalid certificates. Do not suppress or bypass TLS errors to make a connection succeed.
- Do not connect directly to a vCenter-managed ESXi host as an independent source of truth unless a reviewed recovery procedure explicitly requires it.
- Use least-privilege identities and separate discovery from state-changing roles where practical.
- Do not expose credentials, session tokens, certificate contents, connection objects, or sensitive endpoint and inventory data in logs or returned objects.

## Connection and configuration lifecycle

- Create connections explicitly and retain the exact connection object returned for each endpoint.
- Pass the intended connection through `-Server` or the equivalent supported parameter on discovery, mutation, and verification commands.
- Do not rely on mutable global default-server state. Fail closed when ambient default connections could make target selection ambiguous.
- When compatible with the selected PowerCLI version, avoid adding task-specific connections to ambient default-server state.
- Connect once per validated endpoint for a bounded operation rather than repeatedly reconnecting inside per-object loops.
- Enclose owned connections in `try`/`finally` cleanup and disconnect only connections created by the current execution.
- Do not disconnect or reconfigure unrelated operator or process sessions.
- Avoid persistent PowerCLI configuration changes. If a setting must change, use the narrowest supported nonpersistent scope, capture the prior value, restore it in `finally`, and report the deviation.
- Never change user-wide or all-users certificate, proxy, participation, or default-server settings merely to make one script run.

## Inventory resolution and target safety

- Resolve targets by stable vSphere identifiers plus the expected endpoint and parent inventory scope.
- Treat display names as human-readable evidence, not unique authority.
- Reject missing, duplicate, stale, disconnected, inaccessible, or wrong-parent objects before mutation.
- Re-resolve or refresh critical objects immediately before a consequential action; do not mutate from an indefinitely cached discovery result.
- Prefer managed object references or view-based access when it materially reduces ambiguity or round trips, but isolate low-level property use behind tested functions and document version assumptions.
- Minimize broad inventory enumeration and request only required properties where supported.
- Recheck that each target is still owned by the validated vCenter Server and still satisfies the approved scope before change execution.

## Discovery, planning, and confirmation

- Keep discovery and validation non-mutating and callable independently from execution.
- Produce a plan containing stable object IDs, current state, intended state, exact endpoint, ordered operations, impact, expected tasks, timeouts, stop conditions, recovery, and verification.
- State-changing wrappers must use `[CmdletBinding(SupportsShouldProcess)]` and call `$PSCmdlet.ShouldProcess()` immediately around the mutation boundary.
- Do not assume an underlying PowerCLI cmdlet honors `-WhatIf`. The wrapper must prevent invocation when `ShouldProcess` declines.
- Use an additional explicit execution mode or switch for bulk, destructive, privilege, network, storage, power, host, cluster, migration, or recovery-impacting actions.
- Confirmation and dry-run output must identify the exact endpoint and stable target scope without leaking sensitive inventory.
- Do not allow the automation to approve its own consequential action.

## Task, timeout, and partial-failure handling

- Capture the returned object and any vCenter task, event, or correlation identifiers for every state-changing call.
- When asynchronous execution is used, poll with bounded intervals, a documented deadline, and explicit success and failure terminal states.
- Do not use unbounded `Wait-Task` calls or polling loops for unattended automation.
- Treat timeout as an unknown or incomplete outcome, not proof that the server-side task stopped.
- Before retrying, query the original task and actual object state. Retry only failures classified as transient and safe for the operation.
- Do not claim cancellation unless the server confirms it. Record when a task may continue after the client exits.
- Bound concurrency according to vCenter, host, storage, network, and workload capacity; do not launch an unbounded pipeline of asynchronous tasks.
- Stop or isolate the remaining batch according to the reviewed failure policy, and report every succeeded, failed, skipped, timed-out, and unknown target.
- Verify actual inventory and workload state after task completion; a successful cmdlet return or task state alone is insufficient.

## Errors, cleanup, and safe rerun

- Use terminating error behavior at the product boundary so failures reach the owning error handler.
- Preserve useful PowerCLI and vCenter error context while redacting secrets and sensitive inventory.
- Classify failures as validation, authorization, compatibility, transient, terminal, partial, unknown, or operator-required.
- Clean up only resources created by the current execution.
- Design operations to be idempotent where the platform permits. Otherwise, record a checkpoint and explicit manual or automated recovery path.
- Re-discover actual state before a rerun; do not replay a stale mutation list.
- Never use broad catch-and-continue behavior that converts failed vSphere operations into reported success.

## Structured output, logging, and evidence

Reusable code must return structured objects that distinguish planned, skipped, changed, unchanged, failed, timed-out, and unknown outcomes.

Record at minimum:

- UTC start and end timestamps
- script, PowerShell, PowerCLI distribution, child-module, and cmdlet versions
- approved module source and version constraint
- redacted endpoint identity and vSphere version/build
- certificate-validation result without certificate secrets
- connection and configuration scope, including owned-session cleanup
- acting identity class and authorization reference
- stable target IDs and parent scope in an appropriately protected evidence store
- intended operation and `ShouldProcess` outcome
- task, event, and correlation IDs
- per-object result, retries, timeout, and intervention
- actual-state and workload verification
- checks not run, limitations, residual risk, and owner

Separate pipeline objects from operator presentation. Do not use formatted strings as the only completion evidence.

## Credential and sensitive-data requirements

- Obtain credentials through an approved secret-management or credential-broker mechanism.
- Do not hardcode credentials, place them in command-line arguments, persist them in scripts or configuration, export connection objects, or serialize authenticated sessions.
- Avoid converting secrets to plaintext. If an unavoidable supported integration requires plaintext at its boundary, minimize lifetime and scope and document the reviewed exception.
- Redact user names when they are sensitive, and redact session identifiers, tokens, certificate material, console output, support bundles, annotations, custom attributes, paths, and inventory details according to classification.
- Ensure debug, verbose, transcript, exception, and CI artifact output cannot disclose secrets.

## Testing and validation

- Parse PowerShell and run PSScriptAnalyzer on changed code.
- Use Pester to mock the PowerCLI boundary in unit tests. Unit tests must not connect to production or require real credentials.
- Assert that mutation cmdlets are not called during discovery, validation failure, `-WhatIf`, confirmation refusal, ambiguous selection, wrong endpoint, invalid certificate, or unsupported dependency conditions.
- Test explicit `-Server` propagation and failure when ambient connection state is ambiguous.
- Test missing and duplicate inventory, stale objects, authorization failure, asynchronous success/failure/timeout, partial batch results, retry classification, unknown outcomes, cleanup ownership, redaction, idempotent rerun, and post-state mismatch.
- Use a dedicated non-production vCenter or simulator for integration tests when product fidelity is required, with isolated inventory, least privilege, bounded scope, and cleanup evidence.
- Record exact PowerShell, PowerCLI, target, and test-environment versions. Mocked tests do not prove live product compatibility.

## Product rules

### VIRT-VSPH-PCLI-MODULE-101

**Requirement:** Resolve PowerCLI from an approved source and tested version constraint, and separate dependency changes from operational execution.

**Expected evidence:** Distribution, child-module, source, resolved version, PowerShell runtime, compatibility review, and dependency update record.

### VIRT-VSPH-PCLI-SESSION-102

**Requirement:** Bind every operation to an explicitly validated connection and reject ambiguous ambient default-server state.

**Expected evidence:** Redacted endpoint identity, owned connection object, explicit server propagation, and cleanup result.

### VIRT-VSPH-PCLI-CERT-103

**Requirement:** Validate endpoint certificate trust and identity before credential use; certificate-error bypass is prohibited.

**Expected evidence:** Approved trust method, validation result, and source-review date without private or complete certificate material.

### VIRT-VSPH-PCLI-TARGET-104

**Requirement:** Select vSphere objects by stable ID, expected parent scope, and validated endpoint, then recheck immediately before consequential mutation.

**Expected evidence:** Stable identifiers, parent scope, endpoint binding, uniqueness result, and pre-mutation revalidation.

### VIRT-VSPH-PCLI-PREVIEW-105

**Requirement:** State-changing wrappers must implement `ShouldProcess` and must not call the PowerCLI mutation when preview or confirmation declines.

**Expected evidence:** Plan output and tests proving zero mutation calls for `-WhatIf` and refusal paths.

### VIRT-VSPH-PCLI-CONFIG-106

**Requirement:** Do not persistently weaken or alter PowerCLI configuration for task execution; any approved temporary change must be narrowly scoped and restored.

**Expected evidence:** Prior value, narrow scope, justification, restored value, and cleanup outcome.

### VIRT-VSPH-PCLI-TASK-107

**Requirement:** Bound asynchronous work, preserve task identifiers, distinguish unknown outcomes, and verify actual state before success.

**Expected evidence:** Task IDs, deadlines, terminal states, per-object outcomes, retry decisions, and post-state verification.

### VIRT-VSPH-PCLI-OUTPUT-108

**Requirement:** Return structured, redacted per-object results and retain sufficient execution and verification evidence for independent review.

**Expected evidence:** Machine-readable result schema or sample plus redaction and retention checks.

### VIRT-VSPH-PCLI-TEST-109

**Requirement:** Isolate unit tests from live infrastructure and cover endpoint, selection, preview, task, partial-failure, cleanup, redaction, and actual-state mismatch paths.

**Expected evidence:** Pester, syntax, static-analysis, and appropriately scoped integration-test results with exact version boundaries.

### VIRT-VSPH-PCLI-CLEANUP-110

**Requirement:** Clean up only connections and temporary configuration created by the current execution, including on failure.

**Expected evidence:** Ownership tracking and tests for successful, failed, interrupted, and pre-existing-session cases.

## Completion gate

PowerCLI work is incomplete until the selected dependency and target boundary are documented, security controls are preserved, preview and failure paths are tested, task outcomes are reconciled with actual state, owned resources are cleaned up, and all unperformed checks and unsupported compatibility claims are disclosed.

## Authoritative starting points

- [Broadcom VCF PowerCLI portal](https://developer.broadcom.com/powercli)
- [Broadcom `Connect-VIServer` command reference](https://developer.broadcom.com/powercli/latest/vmware.vimautomation.core/commands/connect-viserver)
- [Broadcom `Set-PowerCLIConfiguration` command reference](https://developer.broadcom.com/powercli/latest/vmware.vimautomation.core/commands/set-powercliconfiguration)

These links are starting points, not a substitute for the current release notes, compatibility matrix, security guidance, module-specific command reference, or the adopting environment's support requirements.
