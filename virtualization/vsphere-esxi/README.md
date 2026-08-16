---
id: VIRT-VSPH-README-001
title: VMware vSphere and ESXi Package
version: 0.2.0
status: baseline
---

# VMware vSphere and ESXi Package

## Purpose

Provide project-agnostic standards for safe, testable, reviewable, recoverable, and evidence-based VMware vSphere and ESXi engineering and automation.

## Use this package when

- vCenter
- ESXi
- datacenters
- clusters
- resource pools
- hosts
- VMs
- datastores
- standard and distributed switching
- HA
- DRS
- vMotion
- Lifecycle Manager
- content libraries

Do not select this package merely because a dependency shares an underlying hypervisor. Select it when this product's control plane owns or materially controls the target boundary.

## Package contents

| Path | Purpose |
|---|---|
| [AGENTS.md](AGENTS.md) | Mandatory scoped agent behavior and product rules |
| [Operations and automation standard](standards/OPERATIONS_AND_AUTOMATION_STANDARD.md) | Detailed design, safety, testing, execution, and evidence requirements |
| [VCF PowerCLI automation standard](standards/POWERCLI_AUTOMATION_STANDARD.md) | Product-specific PowerShell module, connection, certificate, targeting, task, test, and evidence requirements |
| [Adoption checklist](templates/ADOPTION_CHECKLIST.md) | Tailoring and readiness record |
| [Review checklist](templates/REVIEW_CHECKLIST.md) | Human review prompts |
| [Evidence record](templates/EVIDENCE_RECORD_TEMPLATE.md) | Durable completion evidence structure |
| [Adoption example](examples/ADOPTION_EXAMPLE.md) | Fictitious non-production composition |
| [Manifest](MANIFEST.md) | Required files and acceptance checks |

## Authority

The authoritative boundary is vCenter Server inventory when managed, or the exact standalone ESXi host when explicitly unmanaged.

Record the endpoint class and stable object identifiers without committing production details. If multiple managers can see the same objects, determine which one owns desired state before proceeding.

## Interfaces

Use VCF PowerCLI (formerly distributed as VMware PowerCLI), supported vSphere APIs and SDKs, ESXCLI, and Lifecycle Manager.

Verify current product and client compatibility. Prefer read-only queries before changes. Preserve asynchronous task identifiers and poll bounded terminal state.

### PowerCLI automation

Apply both the [VCF PowerCLI automation standard](standards/POWERCLI_AUTOMATION_STANDARD.md) and the [PowerShell package](../../languages/powershell/). Use the vSphere standard for product boundaries and the PowerShell package for language engineering.

For new dependency evaluations, use the current Broadcom `VCF.PowerCLI` distribution name. Treat an existing `VMware.PowerCLI` reference as a reviewed compatibility and migration decision; do not blindly rename child modules that retain `VMware.*` namespaces.

Bind commands to an explicitly validated VIServer connection, reject ambiguous default connections, preserve certificate validation, select inventory by stable ID and parent scope, bound asynchronous tasks, and verify actual state after completion.

## Required safe phases

1. Discovery
2. Validation
3. Plan or dry-run
4. Risk and recovery review
5. Authorization
6. Bounded execution
7. Actual-state verification
8. Observation
9. Evidence and closure

## Adoption questions

- Which product, edition, version, and support lifecycle apply?
- Which manager or host is authoritative?
- Which sites, clusters or pools, hosts, guests, networks, and storage are in scope?
- Which stable identifiers prevent ambiguous selection?
- Which identity plans and executes?
- Which operations require separate approval?
- Which backup is independent and demonstrably restorable?
- Which capacity supports maintenance, migration, failover, and rollback?
- Which hardware, firmware, guest, tools, API, SDK, module, storage, and network compatibility sources were checked?
- Which monitoring and owner will observe the result?
- Which recovery path is tested?

## Lifecycle and compatibility

Verify vCenter/ESXi interoperability, hardware compatibility, firmware, drivers, add-ons, image profiles, guest OS support, VMware Tools, virtual hardware, backup integrations, licensing, and Broadcom support entitlements.

Authoritative starting points: [Broadcom VMware vSphere documentation](https://techdocs.broadcom.com/us/en/vmware-cis/vsphere.html) and the [Broadcom VCF PowerCLI portal](https://developer.broadcom.com/powercli).

The accountable vSphere product source-review state is maintained in [`../../SOURCE_REVIEWS.json`](../../SOURCE_REVIEWS.json) with durable evidence under [`../../source-reviews/`](../../source-reviews/). The 2026-08-15 review records the vSphere **product** boundary as `NotRun/Blocked` because the Broadcom vSphere techdocs endpoint could not be retrieved. VCF PowerCLI was reviewed separately through Broadcom Developer documentation. Do not substitute the PowerCLI review for a current vSphere product compatibility review.

The adopting project must revalidate current vSphere release notes, interoperability, compatibility guides, security guidance, licensing, support entitlement, and exact hardware/software combinations before product-specific work.

## Product cautions

- Do not manage a vCenter-owned ESXi host as an independent source of truth.
- Do not enter maintenance mode until evacuation feasibility, pinned workloads, passthrough devices, admission control, and capacity are reviewed.
- Treat snapshots as short-lived operational state; validate consolidation risk and independent backup before removal.

## Automation guidance

- Select by stable ID plus expected parent scope.
- Reject missing or multiple matches.
- Use least privilege and short-lived credentials where supported.
- Keep credentials and sensitive inventory out of configuration, logs, reports, and command history.
- Separate read-only and state-changing functions.
- Support `-WhatIf`, dry-run, plan, or equivalent preview where possible.
- Require explicit execution enablement.
- Use timeouts, cancellation, bounded polling, and bounded concurrency.
- Preserve tasks, jobs, events, and before/after state.
- Treat partial success as incomplete.
- Verify application health, not only VM state.
- Provide structured machine-readable output plus an operator-readable summary.
- Test denied, disconnected, stale, capacity, task-failure, and recovery paths.

## Security

Review:

- management-plane exposure
- privileged and emergency access
- RBAC and inherited permissions
- certificates and API authentication
- host hardening and secure boot
- virtual-network segmentation
- guest isolation and device passthrough
- storage encryption and data remanence
- backup immutability and restore access
- logging, alerting, support bundles, and console data
- automation dependency and credential supply chain

Do not disable a security control merely to make an operation succeed.

## Recovery

Define the applicable rollback, roll-forward, restore, failover, failback, or rebuild path. Validate that the path remains available after the change.

Snapshot presence is not restore evidence.

## Suggested validation

Run repository validation and the exact product-supported read-only health, configuration, cluster, storage, network, backup, and workload checks applicable to the environment.

Record exact commands, target scope, timestamps, results, and checks not run. Redact sensitive data.

## Failure modes

Plan for:

- wrong manager or environment
- duplicate names or stale inventory
- insufficient privilege
- disconnected or maintenance-state hosts
- manager or API unavailability
- failed or stuck asynchronous tasks
- capacity exhaustion
- cluster or quorum loss
- storage path or latency failure
- network reachability loss
- guest-tool or driver incompatibility
- backup or restore failure
- partial migration
- automation interruption and safe rerun
- licensing or support mismatch

## Composition

Common companion packages include:

- the virtualization collection guidance
- PowerShell, Python, Bash, or Terraform/OpenTofu language standards
- architecture
- application security
- testing
- integration
- observability
- SRE
- CI/CD
- supply-chain
- documentation
- internal automation or other project profile

## Limitations

This package does not know the adopting environment's topology, workload dependencies, support contract, compatibility, maintenance window, or recovery capability. It does not grant authority, replace vendor documentation, or guarantee security, supportability, zero downtime, recoverability, or production readiness.

## Maintenance

Review this package when the product's management model, lifecycle, security guidance, compatibility, licensing, API behavior, or support policy changes.
