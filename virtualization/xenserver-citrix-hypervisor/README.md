---
id: VIRT-XENS-README-001
title: XenServer and Citrix Hypervisor Package
version: 0.1.0
status: baseline
---

# XenServer and Citrix Hypervisor Package

## Purpose

Provide project-agnostic standards for safe, testable, reviewable, recoverable, and evidence-based XenServer and Citrix Hypervisor engineering and automation.

## Use this package when

- XenServer/Citrix Hypervisor hosts
- pools
- pool coordination
- VMs
- templates
- networks
- physical interfaces
- bonds
- storage repositories
- HA
- updates
- XenCenter
- xe
- XAPI

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

The authoritative boundary is XenServer resource pool and its pool coordinator, or the exact standalone host.

Record the endpoint class and stable object identifiers without committing production details. If multiple managers can see the same objects, determine which one owns desired state before proceeding.

## Interfaces

Use XenCenter, the supported xe CLI, XAPI, and supported XenServer SDKs.

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

XenServer 9 is the current GA family. Treat Citrix Hypervisor and XenServer 8 or older references as installed-estate, compatibility, or migration boundaries rather than the default greenfield target.

Verify the exact XenServer update channel, update age, upgrade path, pool compatibility, hardware compatibility, guest support, tools, licensing, and support status before work. Current XenServer 9 support guidance requires supported installations to remain within the vendor's published update window; do not infer support from the major version alone.

Authoritative starting point: [XenServer 9 documentation](https://docs.xenserver.com/en-us/xenserver/9/).

The repository source-review record is maintained in [`../../SOURCE_REVIEWS.json`](../../SOURCE_REVIEWS.json) with durable evidence under [`../../source-reviews/`](../../source-reviews/). The adopting project must still revalidate current release notes, compatibility, security guidance, licensing, and support before product-specific work.

## Product cautions

- Do not assume the current pool coordinator remains fixed during failure or maintenance.
- Do not perform unsupported package changes in the control domain.
- Do not remove or forget a storage repository until VM and disk ownership is proven.

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
