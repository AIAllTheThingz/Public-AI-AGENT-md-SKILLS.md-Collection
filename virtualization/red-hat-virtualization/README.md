---
id: VIRT-RHV-README-001
title: Red Hat Virtualization Package
version: 0.1.0
status: baseline
---

# Red Hat Virtualization Package

## Purpose

Provide project-agnostic standards for safe, testable, reviewable, recoverable, and evidence-based Red Hat Virtualization engineering and automation.

## Use this package when

- RHV 4.4 Manager
- self-hosted engine
- data centers
- clusters
- hosts
- VMs
- templates
- storage domains
- logical networks
- HA
- backup
- disaster recovery
- APIs
- migration

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

The authoritative boundary is Red Hat Virtualization Manager and its data center, cluster, host, storage-domain, and VM inventory.

Record the endpoint class and stable object identifiers without committing production details. If multiple managers can see the same objects, determine which one owns desired state before proceeding.

## Interfaces

Use RHV Manager UI, REST API, supported Ansible collections, SDKs, host tools, and engine backup/restore procedures.

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

Red Hat Virtualization is in Extended Life Phase and must be treated as legacy-operation and migration scope, not as the default platform for a new deployment. Current Red Hat lifecycle policy states that Extended Life Phase provides limited support and does not include new bug fixes, security fixes, hardware enablement, or root-cause analysis.

Red Hat identifies OpenShift Virtualization as the continuity and roadmap platform. Inventory current RHV estates, verify entitlement and available support for the exact installed release, protect engine and workload recovery, and prioritize a supported migration path where continued operation carries unacceptable lifecycle risk.

Authoritative lifecycle source: [Red Hat Virtualization Life Cycle](https://access.redhat.com/support/policy/updates/rhev).

The repository source-review record is maintained in [`../../SOURCE_REVIEWS.json`](../../SOURCE_REVIEWS.json) with durable evidence under [`../../source-reviews/`](../../source-reviews/). The adopting project must revalidate current support entitlement, compatibility, migration guidance, and security implications before product-specific work.

## Product cautions

- Prioritize inventory, containment, backup, and migration planning over feature expansion.
- Do not perform a greenfield RHV deployment based only on historical documentation.
- Do not change self-hosted engine, storage domains, or manager state without tested engine recovery.
- Do not interpret Extended Life Phase as normal maintenance coverage or continued security-fix delivery.

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
- unavailable security or bug fixes because the product is in Extended Life Phase

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

Review this package when Red Hat changes lifecycle, support, migration, security, or OpenShift Virtualization guidance, or when the adopting estate's entitlement or migration plan changes.
