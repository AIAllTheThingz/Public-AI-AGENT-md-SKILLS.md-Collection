---
id: VIRT-HV-README-001
title: Microsoft Hyper-V Package
version: 0.1.0
status: baseline
---

# Microsoft Hyper-V Package

## Purpose

Provide project-agnostic standards for safe, testable, reviewable, recoverable, and evidence-based Microsoft Hyper-V engineering and automation.

## Use this package when

- Windows Server Hyper-V hosts and clusters
- Failover Clustering
- Cluster Shared Volumes
- VMs
- checkpoints
- virtual switches
- live and storage migration
- Hyper-V Replica
- shielded VMs
- WAC
- SCVMM
- PowerShell

Do not select this package merely because a dependency shares an underlying hypervisor. Select it when this product's control plane owns or materially controls the target boundary.

## Package contents

| Path | Purpose |
|---|---|
| [AGENTS.md](AGENTS.md) | Mandatory scoped agent behavior and product rules |
| [Operations and automation standard](standards/OPERATIONS_AND_AUTOMATION_STANDARD.md) | Detailed design, safety, testing, execution, and evidence requirements |
| [Adoption checklist](templates/ADOPTION_CHECKLIST.md) | Tailoring and readiness record |
| [Review checklist](templates/REVIEW_CHECKLIST.md) | Human review prompts |
| [Evidence record](templates/EVIDENCE_RECORD_TEMPLATE.md) | Durable completion evidence structure |
| [Adoption example](examples/ADOPTION_EXAMPLE.md) | Fictitious non-production composition |
| [Manifest](MANIFEST.md) | Required files and acceptance checks |

## Authority

The authoritative boundary is Windows Server Failover Cluster, SCVMM fabric, or exact standalone Hyper-V host.

Record the endpoint class and stable object identifiers without committing production details. If multiple managers can see the same objects, determine which one owns desired state before proceeding.

## Interfaces

Use Hyper-V and FailoverClusters PowerShell modules, Windows Admin Center, SCVMM, WMI/CIM, and supported Microsoft APIs.

Verify current product and client compatibility. Prefer read-only queries before changes. Preserve asynchronous task identifiers and poll bounded terminal state.

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

Verify Windows Server version and servicing, cluster functional level, hardware and firmware, guest support, VM configuration version, integration services, backup, storage, network, SCVMM/WAC, PowerShell, and licensing.

Authoritative starting point: [Microsoft Hyper-V documentation](https://learn.microsoft.com/en-us/windows-server/virtualization/hyper-v/overview).

The accountable repository source-review date and evidence are maintained in [`../../SOURCE_REVIEWS.json`](../../SOURCE_REVIEWS.json) and [`../../source-reviews/`](../../source-reviews/). Do not duplicate that date here. The adopting project must still revalidate current release notes, Windows Server lifecycle, compatibility, security guidance, licensing, and support before product-specific work.

## Product cautions

- Do not change a cluster-owned VM through a standalone-host assumption.
- Do not use standard checkpoints as backup or assume production checkpoints are application-consistent recovery copies.
- Do not modify CSV, live-migration, virtual-switch, constrained-delegation, or cluster networking without end-to-end ownership and validation.

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
