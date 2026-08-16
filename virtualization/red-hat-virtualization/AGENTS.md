---
id: VIRT-RHV-AGENT-001
title: Red Hat Virtualization Agent Standard
version: 0.1.0
status: baseline
applies_to:
  - red-hat-virtualization
depends_on:
  - VIRT-AGENT-001
  - GOV-RISK
  - GOV-SECDEV
---

# Red Hat Virtualization Agent Standard

## Purpose

Define mandatory behavior for agents designing, scripting, administering, reviewing, troubleshooting, recovering, or migrating Red Hat Virtualization environments.

This package supplements root governance, the virtualization collection, language packages, engineering disciplines, project profiles, and adopting-project instructions.

## Authoritative boundary

The management authority is Red Hat Virtualization Manager and its data center, cluster, host, storage-domain, and VM inventory.

Do not mutate objects until that authority, environment, stable object scope, and acting identity are verified.

## Scope

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

## Required reading

- [Package README](README.md)
- [Package manifest](MANIFEST.md)
- [Operations and automation standard](standards/OPERATIONS_AND_AUTOMATION_STANDARD.md)
- [Collection selection guide](../VIRTUALIZATION_SELECTION_GUIDE.md)
- [Collection change lifecycle](../VIRTUALIZATION_CHANGE_LIFECYCLE.md)
- [Collection migration matrix](../MIGRATION_DECISION_MATRIX.md)
- applicable governance, language, discipline, platform, virtualization, operating-system, networking, framework, and profile packages

## Supported interfaces

Prefer RHV Manager UI, REST API, supported Ansible collections, SDKs, host tools, and engine backup/restore procedures.

Pin or constrain automation dependencies when practical. Verify interface, server, and API compatibility against current official documentation. Do not use screen scraping, direct manager-database edits, undocumented endpoints, or manual edits to manager-owned state.

## Lifecycle and compatibility

Red Hat Virtualization is in Extended Life Phase and must be treated as legacy-operation and migration scope. Current Red Hat lifecycle policy describes limited support and does not include new bug fixes, security fixes, hardware enablement, or root-cause analysis. Red Hat identifies OpenShift Virtualization as the continuity roadmap.

Verify the exact installed RHV release, entitlement, available support, migration guidance, and recovery posture before work. Do not select RHV for a new deployment without an explicit supported exception.

Record the exact versions, authoritative lifecycle sources, and source-review date. Do not rely on remembered compatibility, feature, licensing, or support claims.

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

- Prioritize inventory, containment, backup, and migration planning over feature expansion.
- Do not perform a greenfield RHV deployment based only on historical documentation.
- Do not change self-hosted engine, storage domains, or manager state without tested engine recovery.
- Do not interpret Extended Life Phase as normal maintenance coverage or continued security-fix delivery.

## Product rules

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

## Required working method

1. Identify authority, target, versions, owners, and current state without mutation.
2. Validate health, privileges, compatibility, capacity, backup, recovery, and maintenance window.
3. Produce an exact plan or dry-run with selected object IDs and ordered actions.
4. Review power, deletion, privilege, network, storage, availability, licensing, and support effects.
5. Obtain accountable authorization for the exact plan and target.
6. Execute through supported interfaces with bounded concurrency and stop conditions.
7. Verify manager, host, VM, guest, network, storage, backup, and monitoring state.
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

Stop when target identity, authority, health, compatibility, capacity, backup, recovery, support, or authorization is unresolved.

## Completion evidence

Record:

- selected package and exact product boundary
- endpoint and object scope without sensitive identifiers
- acting identity class and authorization
- versions, edition, lifecycle, and sources checked
- before, intended, and actual state
- task and event identifiers
- power, network, storage, availability, licensing, and recovery impact
- exact validation and results
- actual-state and workload verification
- rollback, restore, failback, or rebuild readiness
- checks not run, limitations, owners, reviewers, and residual risk
