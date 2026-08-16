---
id: VIRT-OLKVM-AGENT-001
title: Oracle Linux KVM Agent Standard
version: 0.1.0
status: baseline
applies_to:
  - oracle-linux-kvm
depends_on:
  - VIRT-AGENT-001
  - GOV-RISK
  - GOV-SECDEV
---

# Oracle Linux KVM Agent Standard

## Purpose

Define mandatory behavior for agents designing, scripting, administering, reviewing, troubleshooting, recovering, or migrating Oracle Linux KVM environments.

This package supplements root governance, the virtualization collection, language packages, engineering disciplines, project profiles, and adopting-project instructions.

## Authoritative boundary

For current Oracle Linux KVM, the management authority is the exact Oracle Linux libvirt host. For an existing Oracle Linux Virtualization Manager estate, OLVM is authoritative only after verifying that the exact deployment remains inside Oracle's supported OLVM and Oracle Linux 8 boundary.

Do not mutate objects until that authority, environment, stable object scope, acting identity, product generation, and support state are verified.

## Scope

- Oracle Linux KVM/QEMU/libvirt hosts
- domains
- storage pools
- virtual networks
- migration
- Oracle VirtIO drivers
- legacy OLVM data centers, clusters, hosts, storage domains, networks, and VMs only when the installed OLVM estate remains explicitly supported

## Required reading

- [Package README](README.md)
- [Package manifest](MANIFEST.md)
- [Operations and automation standard](standards/OPERATIONS_AND_AUTOMATION_STANDARD.md)
- [Collection selection guide](../VIRTUALIZATION_SELECTION_GUIDE.md)
- [Collection change lifecycle](../VIRTUALIZATION_CHANGE_LIFECYCLE.md)
- [Collection migration matrix](../MIGRATION_DECISION_MATRIX.md)
- applicable governance, language, discipline, platform, virtualization, operating-system, networking, framework, and profile packages

## Supported interfaces

For current KVM work, prefer Oracle Linux KVM/libvirt tooling, `virsh`, Cockpit where supported, supported SDKs, and Ansible.

For an existing OLVM estate, use OLVM REST APIs, supported SDKs, Ansible, and engine backup procedures only after verifying the exact OLVM release, Oracle Linux 8 boundary, entitlement, and support state. Do not treat OLVM as a current management plane for Oracle Linux 9 or 10.

Pin or constrain automation dependencies when practical. Verify interface, server, and API compatibility against current official documentation. Do not use screen scraping, direct manager-database edits, undocumented endpoints, or manual edits to manager-owned state.

## Lifecycle and compatibility

Oracle publishes current KVM guidance for Oracle Linux 9 and 10. Verify Oracle Linux release, UEK or RHCK kernel boundary, KVM/QEMU/libvirt, hardware certification, Oracle VirtIO drivers, guest support, storage, networking, migration, API, and support entitlement.

Current Oracle Linux KVM documentation identifies Oracle Linux Virtualization Manager availability with Oracle Linux 8. Treat OLVM as a separate legacy managed boundary. Do not infer OLVM support for Oracle Linux 9 or 10 from generic KVM support.

Record exact versions, authoritative source URLs, lifecycle/support state, and source-review date. Do not rely on remembered compatibility, feature, licensing, or support claims.

## Non-negotiable behavior

- Discover inventory, versions, health, alarms, events, tasks, capacity, backup, and dependencies before mutation.
- Resolve stable IDs and parent scope; reject ambiguous name-only matches.
- Separate discovery, validation, preview, reporting, execution, verification, and recovery.
- Require explicit authorization for power, deletion, disk, snapshot, checkpoint, network, storage, host, cluster, failover, replication, or migration changes.
- Verify independent backup or export and recovery readiness before destructive or high-blast-radius work.
- Treat snapshots and checkpoints as short-lived operational mechanisms, not backups by default.
- Bound concurrency, polling, retries, and timeouts.
- Preserve task, event, audit, and correlation identifiers.
- Redact credentials, tokens, certificates, console data, support bundles, and sensitive inventory.
- Verify actual platform and workload state after task completion.
- Record checks not run, limitations, operator interventions, and residual risk.
- Do not claim zero downtime, recoverability, compatibility, supportability, or production readiness without evidence.

## Product-specific cautions

- Do not mix direct libvirt ownership with OLVM-managed objects unless Oracle documents the operation for the exact supported estate.
- Do not assume upstream oVirt or generic KVM procedures are supported unchanged by Oracle.
- Do not deploy or expand OLVM as if it were the current management plane for Oracle Linux 9 or 10.
- Protect OLVM engine backup and recovery before manager, cluster, or storage changes in a supported legacy OLVM estate.
- Treat manager migration away from OLVM as a lifecycle project with workload, network, storage, identity, and recovery evidence.

## Product rules

### VIRT-OLKVM-MODE-001

**Requirement:** Identify standalone libvirt versus an explicitly supported legacy OLVM management boundary before mutation and reject conflicting ownership.

**Expected evidence:** Manager mode, Oracle Linux/OLVM versions, support state, URI or OLVM scope, stable object IDs, and identity evidence.

### VIRT-OLKVM-KERNEL-002

**Requirement:** Verify Oracle Linux, kernel, KVM, QEMU, libvirt, firmware, and hardware certification compatibility.

**Expected evidence:** Installed versions and current Oracle compatibility sources.

### VIRT-OLKVM-ENGINE-003

**Requirement:** For a supported legacy OLVM estate, protect and test OLVM engine backup and recovery before managed-environment lifecycle work.

**Expected evidence:** Verified OLVM support boundary, engine backup, restore procedure, and recovery evidence.

### VIRT-OLKVM-STOR-004

**Requirement:** Validate storage pool or domain ownership, paths, capacity, multipathing, and backup before mutation.

**Expected evidence:** Storage mapping, health, capacity, and recovery evidence.

### VIRT-OLKVM-API-005

**Requirement:** Use supported Oracle Linux interfaces or, only within a verified supported legacy estate, OLVM interfaces; verify actual state after tasks.

**Expected evidence:** Interface version, support boundary, task/event records, and post-change state.

## Required working method

1. Identify authority, target, versions, owners, and current state without mutation.
2. Validate health, privileges, compatibility, capacity, backup, recovery, lifecycle/support, and maintenance window.
3. Produce an exact plan or dry-run with selected object IDs and ordered actions.
4. Review power, deletion, privilege, network, storage, availability, licensing, lifecycle, and support effects.
5. Obtain accountable authorization for the exact plan and target.
6. Execute through supported interfaces with bounded concurrency and stop conditions.
7. Verify manager or host, VM, guest, network, storage, backup, and monitoring state.
8. Observe outcomes for a risk-proportionate interval.
9. Preserve evidence and disclose deviations and residual risk.

## Automation requirements

Custom automation must:

- default to non-mutating discovery
- provide validation and dry-run or plan behavior
- require explicit execution enablement
- support confirmation semantics when the language and interface permit
- use structured configuration, input, logging, and reports
- handle missing, duplicate, stale, disconnected, unauthorized, unhealthy, and disappearing objects
- classify retryable and terminal failures
- be safe to rerun or clearly document manual recovery
- test positive, negative, partial-failure, and recovery paths
- document exact supported product and interface versions

## Decision gates

Stop when target identity, authority, lifecycle/support state, health, compatibility, capacity, backup, recovery, or authorization is unresolved.

## Completion evidence

Record:

- selected package and exact product boundary
- endpoint and object scope without sensitive identifiers
- acting identity class and authorization
- versions, edition, lifecycle, support state, and sources checked
- before, intended, and actual state
- task and event identifiers
- power, network, storage, availability, licensing, and recovery impact
- exact validation and results
- actual-state and workload verification
- rollback, restore, failback, or rebuild readiness
- checks not run, limitations, owners, reviewers, and residual risk
