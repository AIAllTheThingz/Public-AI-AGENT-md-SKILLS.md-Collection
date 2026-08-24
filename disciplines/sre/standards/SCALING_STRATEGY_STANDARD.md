---
id: DISC-SRE-SCALING-STRATEGY-STANDARD
title: Scaling Strategy Standard
version: 0.1.0
status: baseline
---

# Scaling Strategy Standard

## Purpose

Turn demand and capacity evidence into explicit implementation and operating decisions without forcing distributed infrastructure onto simple projects.

This standard composes with [`CAPACITY_PERFORMANCE_STANDARD.md`](CAPACITY_PERFORMANCE_STANDARD.md), which governs demand, saturation, quotas, bottlenecks, headroom, scaling, and cost. It does not duplicate those analyses; it records the resulting strategy choices.

## Applicability model

Evaluate each area as `Applicable`, `NotApplicable` with justification, `NotRun`, `Blocked`, `Failed`, or `Verified`. Use `Failed` when representative validation executes but shows that the strategy is unsafe or misses its authorized criteria; do not collapse tested failure into an unresolved state. `Verified` requires representative evidence that satisfies the authorized criteria for the stated workload and environment. A simple single-instance system may correctly mark many areas `NotApplicable` when its operating envelope and rationale are explicit.

## Required decisions

| Area | Decision to record when applicable |
|---|---|
| Horizontal scaling | Unit of replication, coordination, distribution, health, drain, and safe scale-in behavior. |
| Vertical scaling | Resource ceiling, restart or migration impact, saturation signal, and upgrade boundary. |
| Statelessness | Which request-processing state is absent, externalized, or deliberately local. |
| State and sessions | Ownership, affinity, consistency, expiration, migration, and failure behavior. |
| Connections and pooling | Limits, pool sizing rationale, timeout, backpressure, leak detection, and dependency capacity. |
| Caching | Ownership, keying, freshness, invalidation, consistency, capacity, failure, and sensitive-data handling. |
| Asynchronous processing | Delivery, idempotency, ordering, retry, timeout, backpressure, and completion semantics. |
| Queues and background workers | Capacity, concurrency, visibility, dead-letter/recovery, poison work, and queue-depth signals. |
| Rate limiting | Protected resource, identity or scope, limits, fairness, client feedback, and recovery. |
| Partitioning | Partition key, balance, hotspots, resharding, routing, failure, and migration. |
| Replication | Topology, lag, consistency, quorum or failover, recovery, and data-loss boundary. |
| Read/write distribution | Routing, consistency, read-after-write needs, failover, and hotspot behavior. |
| Storage growth | Retention, compaction/archive, indexes, backup/restore growth, quotas, and exhaustion behavior. |
| Network saturation | Bandwidth, connections, packets, data transfer, cross-zone/region effects, and backpressure. |
| External quotas | Owner, current limit, consumption signal, throttling behavior, escalation, and fallback. |
| Autoscaling | Signals, target, min/max, stabilization, hysteresis, cooldown, scale failure, and manual control. |
| Cold starts | Startup dependencies, warm-up, latency/error impact, readiness, and mitigation. |
| Resource limits | Requests/limits or equivalent, concurrency, memory/CPU/I/O exhaustion, and termination behavior. |
| Cost per workload unit | Defined workload unit, fixed and marginal components, scaling curve, variance, and budget owner. |

## Required behavior

- Define the workload model and operating envelope by reference to current capacity evidence.
- Record decisions, alternatives, constraints, dependency limits, failure behavior, observability, cost, owner, and review trigger for each applicable area.
- Prefer the simplest strategy that satisfies evidenced requirements and supported operating conditions.
- Validate scaling, failure, recovery, and cost claims under representative conditions before using `Verified`.
- Reassess after material changes to workload, architecture, data distribution, dependency quotas, configuration, platform, cost model, or SLOs.

## Required evidence

Applicability matrix, linked capacity evidence, architecture decisions, configuration, load/scaling test results, failure and recovery results, telemetry, cost model, limitations, owners, and checks not run.

## Completion gate

Do not report a scaling strategy verified from diagrams, configuration intent, vendor capability, or a single unrepresentative test. An overall scaling-strategy `Verified` claim requires every applicable area to be `Verified` with current representative evidence that satisfies its authorized criteria and a stated supported envelope. Any area that is `Applicable`, `NotRun`, `Blocked`, or `Failed` prevents the overall strategy from being reported `Verified`; `Failed` must remain distinct from unresolved work, and `NotApplicable` requires recorded justification.
