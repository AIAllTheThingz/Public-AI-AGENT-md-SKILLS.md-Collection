---
id: DISC-TPL-TEST-REVIEW
title: Testing and Quality Engineering Review Checklist
version: 0.1.0
status: baseline
---
# Testing and Quality Engineering Review Checklist

## Scope

- [ ] The change states why this discipline applies.
- [ ] The diff is limited to the requested outcome.
- [ ] Affected users, systems, data, contracts, and operators are identified.
- [ ] Hidden assumptions and environment-specific values were not invented.

## Requirements

- [ ] Applicable `AGENTS.md` rules are satisfied.
- [ ] Relevant supporting standards were reviewed.
- [ ] Security, privacy, accessibility, compatibility, reliability, and operational impacts are addressed as applicable.
- [ ] Failure, timeout, retry, rollback, recovery, and partial-success behavior is explicit where relevant.
- [ ] Exceptions are documented and approved.

## Evidence

- [ ] Every performance-test type identifies its execution state; separate `Pass`, `Fail`, `Blocked`, or justified `NotApplicable` outcome; owner; exact artifact; configuration; workload; data; environment; topology; duration; dependencies; explicit execution authorization and safeguards; safe stop conditions; and result window. `Tested` is not treated as `Pass`.
- [ ] Selected throughput, p50/p95/p99, error, CPU, memory, I/O, connection, queue, database, saturation, and cost metrics are relevant; omissions are contextual, not hidden.
- [ ] Scaling, failure-under-load, and recovery-under-load claims are supported where applicable.
- [ ] Raw results and supported operating envelope are retained; unrepresentative evidence is not generalized.
- [ ] Evidence maps to each material claim.
- [ ] Positive, negative, boundary, and failure behavior was verified proportionate to risk.
- [ ] Commands, environments, results, and checks not run are recorded.
- [ ] Examples and documentation match actual behavior.
- [ ] Limitations, assumptions, residual risks, owners, and follow-up work are visible.

## Final review

- [ ] No unrelated refactoring or formatting is included.
- [ ] No secrets or sensitive data appear in source, tests, logs, errors, examples, or artifacts.
- [ ] Completion language does not exceed the available evidence.
