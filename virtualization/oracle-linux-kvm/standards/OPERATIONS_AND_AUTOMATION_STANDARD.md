---
id: VIRT-OLKVM-OPS-001
title: Oracle Linux KVM Operations and Automation Standard
version: 0.1.0
status: baseline
---

# Oracle Linux KVM Operations and Automation Standard

## Purpose

Define the detailed operating and automation contract for Oracle Linux KVM work.

## Applicability

This standard applies to Oracle Linux KVM/QEMU/libvirt hosts, domains, storage pools, virtual networks, migration, Oracle VirtIO drivers, and explicitly supported legacy Oracle Linux Virtualization Manager estates.

Current Oracle guidance identifies OLVM availability with Oracle Linux 8. OLVM is therefore a separate legacy managed boundary, not a current management plane for Oracle Linux 9 or 10.

## Authority and identity

- For current KVM work, connect only to the exact Oracle Linux libvirt host.
- For an OLVM-managed estate, treat OLVM as authoritative only after verifying the exact OLVM release, Oracle Linux 8 boundary, entitlement, and support state.
- Record endpoint class, environment, stable object IDs, Oracle Linux/OLVM versions, and acting identity.
- Verify certificate and endpoint identity before credential use.
- Use least privilege and separate read-only discovery from state-changing execution.
- Do not let automation approve its own consequential action.
- Reject ambiguous selection or conflicting direct-libvirt/OLVM ownership.

## Discovery

Collect:

- Oracle Linux, kernel, KVM/QEMU/libvirt, OLVM when present, hardware, firmware, drivers, guest tools, API, SDK, module, and lifecycle/support state
- management, host, VM, network, and storage topology
- for a supported OLVM estate, manager, cluster, storage-domain, network, and VM relationships
- health, alarms, events, active tasks, maintenance state, backup, replication, and monitoring
- owners, dependencies, maintenance windows, recovery objectives, and acceptance tests
- CPU, memory, storage, network, admission-control, and temporary migration capacity
- security, licensing, entitlement, and support constraints

Discovery must not change state.

## Validation

Validate:

- target and identity
- permissions
- lifecycle and support state
- host or supported manager health
- compatibility and support
- capacity and evacuation
- network and storage paths
- independent backup and recovery
- active conflicting tasks
- workload-owner authorization
- monitoring and escalation
- rollback, restore, failback, or rebuild

Stop on an unmet prerequisite.

## Plan and dry-run

The plan must show:

- exact stable object identifiers
- intended before-to-after transitions
- ordered actions
- power and availability impact
- network and storage impact
- destructive or irreversible steps
- concurrency and timeouts
- stop conditions
- expected task identifiers and completion states
- recovery and validation
- evidence captured

## Execution

- Require explicit enablement.
- Use supported interfaces only.
- Bound concurrent operations.
- Apply timeouts and cancellable polling where practical.
- Preserve task, job, and event identifiers.
- Stop on defined terminal failures.
- Do not silently continue past partial failure.
- Avoid unrelated cleanup.
- Preserve recovery options until verification and acceptance.
- Record manual intervention.

## Verification

Verify:

- host or supported manager and inventory state
- host or cluster health where applicable
- VM configuration and power state
- guest OS, tools, devices, time, and application health
- required and denied network paths
- storage accessibility, capacity, performance, and integrity
- HA, replication, backup, and restore coverage where applicable
- monitoring, alerts, events, and audit
- absence of unexpected snapshots, orphaned disks, duplicate identities, or stale state

## Product-specific rules

### VIRT-OLKVM-MODE-001

**Requirement:** Identify standalone libvirt versus an explicitly supported legacy OLVM boundary before mutation and reject conflicting ownership.

**Expected evidence:** Management mode, Oracle Linux/OLVM versions, support state, URI or OLVM scope, stable object IDs, and identity evidence.

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

**Requirement:** Use supported Oracle Linux interfaces or, only within a verified supported legacy estate, OLVM interfaces and verify actual state after tasks.

**Expected evidence:** Interface version, support boundary, task/event records, and post-change state.

## Product-specific cautions

- Do not mix direct libvirt ownership with OLVM-managed objects unless Oracle documents the operation for the exact supported estate.
- Do not assume upstream oVirt or generic KVM procedures are supported unchanged by Oracle.
- Do not deploy or expand OLVM as if it were the current management plane for Oracle Linux 9 or 10.
- Protect OLVM engine backup and recovery before manager, cluster, or storage changes in a supported legacy OLVM estate.
- Treat migration away from OLVM as a lifecycle project with source retention and recovery evidence.

## Automation implementation

Automation must:

- use structured configuration and input validation
- separate discovery, validation, plan, report, execute, and verify code paths
- provide preview semantics when supported
- confirm target identity and support boundary again immediately before mutation
- use stable IDs and expected parent scope
- redact sensitive values
- use structured logs and reports
- preserve correlation with host/manager tasks
- handle stale inventory and disappearing objects
- classify retryable, terminal, and operator-required failures
- use bounded exponential polling rather than unbounded loops
- provide safe rerun or recovery behavior
- avoid self-modifying or dynamically downloaded unverified code
- pin or constrain dependencies where practical
- document supported versions
- include unit tests and mocked interface tests
- include negative and partial-failure tests

## Testing

Test:

- successful read-only discovery
- missing and duplicate targets
- wrong parent scope
- access denied
- disconnected or unhealthy host/manager
- unsupported OLVM or Oracle Linux generation
- compatibility failure
- capacity failure
- active conflicting task
- dry-run with no mutation
- confirmation refusal
- asynchronous task success and failure
- timeout and cancellation
- partial batch failure
- log redaction
- actual-state mismatch
- rollback or manual handoff
- idempotent rerun

Do not use production as the first test environment.

## Observability

Capture:

- start/end timestamps
- tool and dependency versions
- endpoint and object scope in redacted form
- acting identity class
- lifecycle/support boundary
- change or approval reference
- host/manager task, job, or event identifiers
- per-object outcomes
- retries, timeouts, cancellations, and interventions
- before and after state
- validation and workload health
- recovery status
- residual risk

## Recovery

Recovery must be independent from the path being changed where practical. Define what happens if the host, supported manager, network, storage, VM, guest, automation runner, or backup system fails mid-change.

Do not remove the source, disk, snapshot, checkpoint, or recovery copy until the authorized acceptance and retention boundary is satisfied.

## Completion

Completion requires exact evidence, owner acceptance where applicable, operational observation, explicit checks not run, and disclosed residual risk. Tool success alone is insufficient.

## Current source boundary

Oracle publishes current KVM guidance for Oracle Linux 9 and 10. Current Oracle Linux KVM documentation identifies Oracle Linux Virtualization Manager availability with Oracle Linux 8, so OLVM must be treated as a separate legacy managed boundary.

Verify exact Oracle Linux release, UEK/RHCK, KVM/QEMU/libvirt, hardware certification, VirtIO, guest, storage, networking, migration, API, entitlement, and any OLVM support boundary using [Oracle Linux KVM User's Guide](https://docs.oracle.com/en/operating-systems/oracle-linux/kvm-user/) and current official lifecycle, compatibility, security, and release documentation before execution.
