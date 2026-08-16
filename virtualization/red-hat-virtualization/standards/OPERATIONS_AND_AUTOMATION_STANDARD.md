---
id: VIRT-RHV-OPS-001
title: Red Hat Virtualization Operations and Automation Standard
version: 0.1.0
status: baseline
---

# Red Hat Virtualization Operations and Automation Standard

## Purpose

Define the detailed operating and automation contract for Red Hat Virtualization work.

## Applicability

This standard applies to RHV 4.4 Manager, self-hosted engine, data centers, clusters, hosts, VMs, templates, storage domains, logical networks, HA, backup, disaster recovery, APIs, and migration.

## Authority and identity

- Connect only to Red Hat Virtualization Manager and its data center, cluster, host, storage-domain, and VM inventory.
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

### VIRT-RHV-LIFE-001

**Requirement:** Record lifecycle, entitlement, support status, exposure, and migration owner before work.

**Expected evidence:** Current Red Hat source, entitlement status, risk acceptance, and migration record.

### VIRT-RHV-ENGINE-002

**Requirement:** Protect and test RHV Manager or self-hosted-engine backup and recovery before manager, host, or storage work.

**Expected evidence:** Engine backup, restore procedure, and recovery evidence.

### VIRT-RHV-DOMAIN-003

**Requirement:** Validate data center, cluster, storage-domain, network, and VM relationships before mutation.

**Expected evidence:** Manager inventory and dependency map.

### VIRT-RHV-MIGRATE-004

**Requirement:** Prefer supported migration or replacement planning; preserve rollback and source retention until destination acceptance.

**Expected evidence:** Migration plan, destination compatibility, validation, and hold period.

### VIRT-RHV-API-005

**Requirement:** Use supported RHV APIs, Ansible, or SDKs and preserve job/event evidence.

**Expected evidence:** Interface version, task results, and actual-state verification.

## Product-specific cautions

- Prioritize inventory, containment, backup, and migration planning over feature expansion.
- Do not perform a greenfield RHV deployment based only on historical documentation.
- Do not change self-hosted engine, storage domains, or manager state without tested engine recovery.
- Do not interpret Extended Life Phase as normal maintenance coverage or continued security-fix delivery.

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

Red Hat Virtualization is in Extended Life Phase. Current Red Hat lifecycle policy describes limited support and does not include new bug fixes, security fixes, hardware enablement, or root-cause analysis. Treat this package as legacy-operation and migration guidance, verify the exact installed release and entitlement before work, and do not select RHV for a new deployment without an explicit supported exception.

Red Hat identifies OpenShift Virtualization as the continuity roadmap. Verify current behavior with [Red Hat Virtualization lifecycle policy](https://access.redhat.com/support/policy/updates/rhev), [Red Hat Virtualization 4.4 documentation](https://docs.redhat.com/en/documentation/red_hat_virtualization/4.4), and current official migration, compatibility, and security guidance before execution.
