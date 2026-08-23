---
id: DISC-TEST-NONFUNCTIONAL-TESTING-STANDARD
title: Nonfunctional Testing Standard
version: 0.1.0
status: baseline
---
# Nonfunctional Testing Standard

## Purpose

This standard defines detailed requirements for one part of the **Testing and Quality Engineering** discipline:

> Define performance, load, resilience, recovery, security, accessibility, and compatibility tests when risk requires them.

## Required behavior

- Define performance, load, resilience, recovery, security, accessibility, and compatibility tests when risk requires them.
- For performance validation, explicitly assess the applicability of baseline, load, stress, spike, soak or endurance, scaling, failure-under-load, and recovery-under-load testing.
- Record each performance-test type as `Applicable`, justified `NotApplicable`, `NotRun`, `Blocked`, or `Tested` using the repository evidence model; do not infer a result from planned scripts or configuration.
- Define workload model, user or workload unit, concurrency or arrival pattern, data shape, duration, warm-up, ramp, environment, topology, dependencies, quotas, resource limits, success criteria, stop conditions, and owner.
- Select representative metrics contextually. Consider throughput, p50, p95, p99, error rate, CPU, memory, I/O, connection counts, queue depth, database utilization, relevant service saturation, and cost; do not require or report irrelevant metrics merely to fill a table.
- Establish a versioned baseline before interpreting regressions where a meaningful comparison exists.
- Exercise expected demand with appropriate headroom and confirm acceptance criteria under sustained load where load testing applies.
- Explore capacity and failure boundaries safely where stress testing applies; define safeguards so testing cannot harm uncontrolled systems.
- Exercise rapid demand change where spike behavior is material and verify throttling, backpressure, degradation, and recovery.
- Exercise long-duration behavior where leaks, fragmentation, queue accumulation, storage growth, cache behavior, rollover, or dependency drift are material.
- Validate scaling signals, limits, timing, cold starts, state/session behavior, connection management, and scale-in safety where scaling applies.
- Exercise dependency failure, timeout, throttling, partial failure, and recovery during representative load where safe and applicable.
- Verify post-load recovery: backlog drains, resources return to an expected range, data remains correct, alerts resolve, and the service resumes its supported operating condition.
- Protect test data, credentials, systems, participants, and third-party dependencies; authorize high-impact or production-like tests explicitly.
- Preserve raw or primary result evidence and tie conclusions to the exact artifact, configuration, data, environment, and test window.

## Required evidence

Evidence should be concrete and reproducible. Depending on scope, include:

- test plan, requirement and acceptance-criteria mappings, exact artifact/configuration identity, and applicability decisions
- workload model, generators, data, duration, environment, topology, dependencies, quotas, warm-up, ramp, and stop conditions
- raw results and summarized throughput, latency percentiles, errors, utilization, saturation, connections, queues, database, and cost metrics selected for the system
- baseline comparison, variability, repeated-run or confidence rationale, observed bottlenecks, and supported operating envelope
- scaling, failure-under-load, and recovery-under-load evidence where applicable
- exact commands, timestamps, tools and versions, result locations, checks not run, limitations, risks, owners, and follow-up

## Review questions

- Is this standard applicable to the change, and is the chosen scope documented?
- Is every performance-test type explicitly assessed rather than silently omitted?
- Does the workload represent the claimed operating condition without exposing uncontrolled systems?
- Are acceptance thresholds authorized and traceable instead of invented for the test?
- Are tail latency, errors, resource saturation, dependency behavior, and cost measured only where relevant?
- Did the test identify behavior during and after scaling or failure, not merely peak throughput?
- Does the evidence prove the supported envelope for the exact candidate and environment rather than describe intent?

## Completion gate

Do not report performance or scalability validated until every applicable test type has current evidence, the workload and environment are representative of the claim, raw results are retained, recovery is evaluated where relevant, and unsupported operating conditions and remaining risk are stated plainly.
