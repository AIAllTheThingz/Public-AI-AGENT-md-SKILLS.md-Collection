---
id: VIRT-AHV-README-001
title: Nutanix AHV Package
version: 0.1.0
status: baseline
---

# Nutanix AHV Package

## Purpose

Provide project-agnostic standards for safe, testable, reviewable, recoverable, and evidence-based Nutanix AHV engineering and automation.

## Use this package when

- AHV and AOS clusters
- Prism Central
- Prism Element
- hosts
- CVMs
- VMs
- images
- storage containers
- networks and subnets
- categories
- policies
- protection domains
- recovery
- lifecycle
- NCC
- APIs

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

The authoritative boundary is Prism Central or Prism Element scope that owns the AHV cluster and objects.

Record the endpoint class and stable object identifiers without committing production details. If multiple managers can see the same objects, determine which one owns desired state before proceeding.

## Interfaces

Use Prism Central and Element APIs, supported Nutanix SDKs, aCLI, nCLI, lifecycle tooling, and supported automation providers.

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

Verify AOS, AHV, Prism Central, firmware, Foundation, LCM, hardware model, guest tools, backup, replication, API, licensing, and Nutanix interoperability before relying on a feature.

Authoritative starting points: [Nutanix support policies and FAQs](https://www.nutanix.com/support-services/support-policies-and-faqs) and the [Nutanix product documentation portal](https://portal.nutanix.com/page/documents/list?type=software).

The accountable repository source-review date and evidence are maintained in [`../../SOURCE_REVIEWS.json`](../../SOURCE_REVIEWS.json) and [`../../source-reviews/`](../../source-reviews/). Do not duplicate that date here. The adopting project must still revalidate exact supported builds, interoperability, release notes, compatibility, security guidance, licensing, and support before product-specific work.

## Product cautions

- Do not treat CVMs as ordinary guest VMs or alter them outside supported Nutanix procedures.
- Do not run broad aCLI or nCLI mutations without cluster and Prism scope verification.
- Do not claim protection-domain or snapshot configuration proves recoverability without restore or failover evidence.

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
