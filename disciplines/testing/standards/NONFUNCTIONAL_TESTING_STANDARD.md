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
- Define scope, ownership, inputs, outputs, assumptions, dependencies, and supported operating conditions.
- Use explicit, reviewable configuration and documented defaults rather than hidden environment assumptions.
- Apply controls proportionate to change risk, data sensitivity, trust boundaries, reversibility, and operational impact.
- Define positive behavior, negative behavior, boundary conditions, partial failure, recovery, and safe stopping conditions.
- Keep implementation, configuration, examples, and evidence free of credentials, internal production identifiers, and sensitive data.
- Preserve existing contracts unless an authorized change includes compatibility, migration, and communication work.
- Record exceptions through the repository exception process instead of weakening the standard silently.
- For performance validation, explicitly assess the applicability of baseline, load, stress, spike, soak or endurance, scaling, failure-under-load, and recovery-under-load testing.
- Record each performance-test type as `Applicable`, justified `NotApplicable`, `NotRun`, `Blocked`, or `Tested` using the repository evidence model; do not infer a result from planned scripts or configuration.
- Record a separate outcome of `Pass`, `Fail`, `Blocked`, or justified `NotApplicable` for every performance-test type. `Tested` records execution evidence and does not imply `Pass`; use `Pass` only when current primary evidence for the exact artifact and representative conditions satisfies the authorized acceptance criteria.
- For an applicable test whose state is `Applicable`, `NotRun`, or `Blocked`, record outcome `Blocked`; for a tested applicable type, record `Pass`, `Fail`, or `Blocked` from the evidence; align `NotApplicable` state and outcome and retain the justification.
- For each performance-test type, record its accountable owner, explicit execution authorization and safeguards, and safe stop conditions independently; record why any field is unresolved when the state is `NotRun` or `Blocked`.
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

- design, configuration, contract, diagram, or decision records
- implementation or review evidence tied to the requirement
- positive, negative, boundary, and failure-path tests
- operational, security, privacy, compatibility, or recovery evidence
- commands run, environments used, results, and checks not run
- known limitations, assumptions, unresolved risks, owners, and follow-up work
- test plan, requirement and acceptance-criteria mappings, exact artifact/configuration identity, and applicability decisions
- workload model, generators, data, duration, environment, topology, dependencies, quotas, warm-up, ramp, and stop conditions
- per-test-type owner, execution authorization, safeguards, and stop conditions for baseline, load, stress, spike, soak or endurance, scaling, failure-under-load, and recovery-under-load tests
- per-test-type execution state and separate `Pass`, `Fail`, `Blocked`, or justified `NotApplicable` outcome mapped to authorized acceptance criteria
- raw results and summarized throughput, latency percentiles, errors, utilization, saturation, connections, queues, database, and cost metrics selected for the system
- baseline comparison, variability, repeated-run or confidence rationale, observed bottlenecks, and supported operating envelope
- scaling, failure-under-load, and recovery-under-load evidence where applicable
- exact commands, timestamps, tools and versions, result locations, checks not run, limitations, risks, owners, and follow-up

## Review questions

- Is this standard applicable to the change, and is the chosen scope documented?
- Are ownership and trust boundaries explicit?
- Are unsafe defaults, ambiguity, and hidden coupling avoided?
- Are failure, retry, rollback, recovery, and partial-success behaviors defined where relevant?
- Does the evidence prove the claim rather than merely describe intent?
- Are exceptions approved, time-bounded, and visible?
- Is every performance-test type explicitly assessed rather than silently omitted?
- Does every performance-test type identify its owner, execution authorization and safeguards, and safe stop conditions rather than relying on record-level assumptions?
- Does the workload represent the claimed operating condition without exposing uncontrolled systems?
- Are acceptance thresholds authorized and traceable instead of invented for the test?
- Is execution state recorded separately from outcome, with every `Pass` supported by current primary evidence that meets the authorized criteria for the exact artifact and representative conditions?
- Are tail latency, errors, resource saturation, dependency behavior, and cost measured only where relevant?
- Did the test identify behavior during and after scaling or failure, not merely peak throughput?
- Does the evidence prove the supported envelope for the exact candidate and environment rather than describe intent?

## Completion gate

Do not report this area complete until the applicable requirements are implemented, evidence is recorded, unsupported claims are removed, and remaining risk is stated plainly.

Do not report performance or scalability validated until every applicable test type has state `Tested` and a separate current explicit outcome of `Pass` against its authorized acceptance criteria for the exact artifact and representative conditions, raw results are retained, recovery is evaluated where relevant, and unsupported operating conditions and remaining risk are stated plainly. Any applicable `Fail`, `Blocked`, `NotRun`, missing, stale, or different-artifact result prevents the validated claim.
