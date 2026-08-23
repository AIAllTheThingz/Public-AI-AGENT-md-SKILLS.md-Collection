---
id: DISC-TPL-SRE-REVIEW
title: Site Reliability Engineering Review Checklist
version: 0.1.0
status: baseline
---
# Site Reliability Engineering Review Checklist

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

- [ ] The separate overall production-readiness decision uses `Pass`, `Fail`, `Blocked`, or justified `NotApplicable`, records decision authority, and is tied to the exact candidate and operating scope.
- [ ] Data migration has its own readiness result and evidence or justified `NotApplicable` rationale; applicable migrations and irreversible changes include rehearsal, backup or recovery planning, irreversible-step handling, and explicit go/no-go criteria and authority rather than being inferred from backup, restore, or deployment evidence.
- [ ] Privacy has its own readiness result and evidence or justified `NotApplicable` rationale rather than being inferred from Security.
- [ ] An applicable `NotRun` readiness area did not support a pass.
- [ ] Scaling strategy addresses each listed area contextually and does not force unjustified complexity.
- [ ] Every `Verified` scaling claim identifies workload, environment, operating envelope, result, and cost evidence where material.
- [ ] Evidence maps to each material claim.
- [ ] Positive, negative, boundary, and failure behavior was verified proportionate to risk.
- [ ] Commands, environments, results, and checks not run are recorded.
- [ ] Examples and documentation match actual behavior.
- [ ] Limitations, assumptions, residual risks, owners, and follow-up work are visible.

## Final review

- [ ] No unrelated refactoring or formatting is included.
- [ ] No secrets or sensitive data appear in source, tests, logs, errors, examples, or artifacts.
- [ ] Completion language does not exceed the available evidence.
