---
id: VIRT-XENS-OPS-001
title: XenServer and Citrix Hypervisor Operations and Automation Standard
version: 0.1.0
status: baseline
---

# XenServer and Citrix Hypervisor Operations and Automation Standard

## Purpose

Define the detailed operating and automation contract for XenServer and Citrix Hypervisor work.

## Applicability

This standard applies to XenServer/Citrix Hypervisor hosts, pools, pool coordination, VMs, templates, networks, physical interfaces, bonds, storage repositories, HA, updates, XenCenter, xe, and XAPI.

## Authority and identity

- Connect only to XenServer resource pool and its pool coordinator, or the exact standalone host.
- Record endpoint class, environment, stable object IDs, and acting identity.
- Verify certificate and endpoint identity before credential use.
- Use least privilege and separate read-only discovery from state-changing execution.
- Do not let automation approve its own consequential action.
- Reject ambiguous selection.

## Discovery

Collect:

- product, edition, version, build, hardware, firmware, drivers, guest tools, API, SDK, module, and lifecycle
- management, cluster or pool, host, VM, network, and storage topology
- health, alarms, events, active tasks, maintenance state, backup, replication, and monitoring
- owners, dependencies, maintenance windows, recovery objectives, and acceptance tests
- CPU, memory, storage, network, admission-control, and temporary migration capacity
- security, licensing, entitlement, and support constraints

Discovery must not change state.

## Validation

Validate:

- target and identity
- permissions
- manager and cluster health
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

- manager and inventory state
- cluster or pool and host health
- VM configuration and power state
- guest OS, tools, devices, time, and application health
- required and denied network paths
- storage accessibility, capacity, performance, and integrity
- HA, replication, backup, and restore coverage
- monitoring, alerts, events, and audit
- absence of unexpected snapshots, orphaned disks, duplicate identities, or stale state

## Product-specific rules

### VIRT-XENS-POOL-001

**Requirement:** Resolve pool UUID, coordinator, member health, versions, and active tasks before pool or host mutation.

**Expected evidence:** Pool inventory, UUIDs, coordinator, health, and task evidence.

### VIRT-XENS-UPDATE-002

**Requirement:** Use supported update and upgrade sequencing with mixed-version and pool restrictions reviewed.

**Expected evidence:** Vendor-supported sequence, compatibility review, and rollback limits.

### VIRT-XENS-SR-003

**Requirement:** Validate storage-repository type, shared state, paths, capacity, PBD attachments, and VDI ownership before mutation.

**Expected evidence:** SR/PBD/VDI inventory and recovery evidence.

### VIRT-XENS-NET-004

**Requirement:** Map networks, PIFs, bonds, VLANs, management access, and VM interfaces before network changes.

**Expected evidence:** Topology and connectivity validation including recovery access.

### VIRT-XENS-XAPI-005

**Requirement:** Use supported XAPI, SDK, or xe operations and preserve task/event identifiers.

**Expected evidence:** Interface version, task records, and actual-state verification.

## Product-specific cautions

- Do not assume the current pool coordinator remains fixed during failure or maintenance.
- Do not perform unsupported package changes in the control domain.
- Do not remove or forget a storage repository until VM and disk ownership is proven.

## Automation implementation

Automation must:

- use structured configuration and input validation
- separate discovery, validation, plan, report, execute, and verify code paths
- provide preview semantics when supported
- confirm target identity again immediately before mutation
- use stable IDs and expected parent scope
- redact sensitive values
- use structured logs and reports
- preserve correlation with manager tasks
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
- disconnected or unhealthy manager/host
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
- change or approval reference
- manager task/job/event identifiers
- per-object outcomes
- retries, timeouts, cancellations, and interventions
- before and after state
- validation and workload health
- recovery status
- residual risk

## Recovery

Recovery must be independent from the path being changed where practical. Define what happens if the manager, host, network, storage, VM, guest, automation runner, or backup system fails mid-change.

Do not remove the source, disk, snapshot, checkpoint, or recovery copy until the authorized acceptance and retention boundary is satisfied.

## Completion

Completion requires exact evidence, owner acceptance where applicable, operational observation, explicit checks not run, and disclosed residual risk. Tool success alone is insufficient.

## Current source boundary

XenServer 9 is the current GA family. Treat Citrix Hypervisor and XenServer 8 or older references as installed-estate, compatibility, or migration boundaries rather than the default greenfield target.

Verify exact update age, update channel, upgrade path, pool compatibility, hardware compatibility, guest support, tools, licensing, and support lifecycle using [XenServer 9 product documentation](https://docs.xenserver.com/en-us/xenserver/9/) and current official compatibility, security, lifecycle, and release guidance before execution.
