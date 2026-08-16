---
id: VIRT-OLKVM-README-001
title: Oracle Linux KVM Package
version: 0.1.0
status: baseline
---

# Oracle Linux KVM Package

## Purpose

Provide project-agnostic standards for safe, testable, reviewable, recoverable, and evidence-based Oracle Linux KVM engineering and automation.

## Use this package when

- Oracle Linux KVM/QEMU/libvirt hosts
- domains
- storage pools
- virtual networks
- migration
- Oracle VirtIO drivers
- legacy Oracle Linux Virtualization Manager estates that are explicitly within their supported Oracle Linux 8 boundary

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

The authoritative boundary is the exact Oracle Linux libvirt host for standalone KVM. For an existing OLVM-managed estate, the OLVM Manager is authoritative only when that deployment is within the exact Oracle-supported OLVM and Oracle Linux 8 boundary.

Record the endpoint class and stable object identifiers without committing production details. If multiple managers can see the same objects, determine which one owns desired state before proceeding.

## Interfaces

For current Oracle Linux KVM use Oracle Linux KVM/libvirt tooling, `virsh`, Cockpit where supported, supported SDKs, Ansible, and documented migration interfaces.

For an existing OLVM estate, use OLVM APIs and engine backup/recovery procedures only after verifying that the exact OLVM release and Oracle Linux 8 environment remain supported. Do not assume OLVM is a current management plane for Oracle Linux 9 or 10.

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

- Which Oracle Linux generation, kernel family, KVM/QEMU/libvirt release, and support lifecycle apply?
- Is the environment standalone KVM or an explicitly supported legacy OLVM estate?
- Which manager or host is authoritative?
- Which sites, clusters, hosts, guests, networks, and storage are in scope?
- Which stable identifiers prevent ambiguous selection?
- Which identity plans and executes?
- Which operations require separate approval?
- Which backup is independent and demonstrably restorable?
- Which capacity supports maintenance, migration, failover, and rollback?
- Which hardware, firmware, guest, VirtIO, API, SDK, module, storage, and network compatibility sources were checked?
- Which monitoring and owner will observe the result?
- Which recovery path is tested?

## Lifecycle and compatibility

Oracle publishes current KVM guidance for Oracle Linux 10 and Oracle Linux 9. Verify the exact Oracle Linux release, UEK or RHCK kernel boundary, KVM/QEMU/libvirt versions, hardware certification, Oracle VirtIO drivers, guest support, storage, networking, migration, API, and support entitlement.

Current Oracle Linux 10 KVM documentation identifies Oracle Linux Virtualization Manager availability with Oracle Linux 8. Treat OLVM as a separate legacy managed boundary rather than implying that OLVM is a current Oracle Linux 10 or Oracle Linux 9 control plane.

Authoritative starting point: [Oracle Linux KVM User's Guide](https://docs.oracle.com/en/operating-systems/oracle-linux/kvm-user/).

The repository source-review record is maintained in [`../../SOURCE_REVIEWS.json`](../../SOURCE_REVIEWS.json) with durable evidence under [`../../source-reviews/`](../../source-reviews/). The adopting project must revalidate current release notes, compatibility, security guidance, licensing, entitlement, and support before product-specific work.

## Product cautions

- Do not mix direct libvirt ownership with OLVM-managed objects unless Oracle documents the operation for the exact supported estate.
- Do not assume upstream oVirt or generic KVM procedures are supported unchanged by Oracle.
- Do not deploy or expand OLVM as if it were the current management plane for Oracle Linux 9 or 10.
- Protect OLVM engine backup and recovery before changes to a supported legacy OLVM estate.
- Treat manager migration away from OLVM as a lifecycle project with workload, network, storage, identity, and recovery evidence.

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
- an OLVM workflow being applied outside its supported Oracle Linux 8 boundary

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

Review this package when Oracle Linux, KVM, UEK/RHCK, VirtIO, OLVM support, migration, security, or lifecycle guidance changes.
