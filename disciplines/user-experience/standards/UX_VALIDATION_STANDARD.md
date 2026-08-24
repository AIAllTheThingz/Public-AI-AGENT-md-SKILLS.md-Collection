---
id: DISC-UX-UX-VALIDATION-STANDARD
title: User Experience Validation Standard
version: 0.1.0
status: baseline
---

# User Experience Validation Standard

## Purpose

Match UX claims to proportionate, representative, attributable evidence.

## Required behavior

- Map validation questions to user outcomes, requirements, journeys, risk, and the interface version tested.
- Select representative methods such as research, usability evaluation, controlled analytics, expert review, or experiment; state what each method cannot prove.
- Record state as `Tested`, `Reviewed`, `OperationallyVerified`, `NotRun`, `Blocked`, or justified `NotApplicable` only when supported by the repository evidence model.
- Record an independent `Pass`, `Fail`, `Blocked`, or justified `NotApplicable` outcome for every validation method and claim, plus a separate overall outcome. Execution or evidence state does not imply `Pass`.
- Use an overall `Pass` only when current primary evidence for the exact interface version, representative users or source, tasks, environment, and conditions satisfies the authorized criteria for every applicable method and claim. Any applicable `Fail`, `Blocked`, `NotRun`, missing, stale, or different-version result prevents the overall pass.
- Preserve negative, conflicting, inconclusive, and excluded-population findings.
- Revalidate when material users, tasks, journeys, content, interactions, architecture, or operating context changes.

## Required evidence

Plan, method, authorized criteria, exact version, environment, participants or evidence source, per-method state and outcome, primary results, limitations, finding disposition, separate overall outcome, authority, and traceability to requirements and decisions.

## Completion gate

Do not claim UX validated when only a design review, prototype, synthetic simulation, automated accessibility check, or implementation exists, or when the separate overall validation outcome is not `Pass`. Any applicable failed, blocked, not-run, missing, stale, or different-version result prevents that claim; `NotApplicable` requires reviewed justification.
