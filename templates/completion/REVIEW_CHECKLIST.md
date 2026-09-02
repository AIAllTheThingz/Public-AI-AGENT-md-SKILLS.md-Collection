---
id: TEMPLATE-REVIEW-COMPLETION-001
title: Completion Report Review Checklist
version: 0.3.0
status: baseline
---

# Completion Report Review Checklist

## Identity

- Template type: `completion-report`
- Stable template: [`COMPLETION_REPORT_TEMPLATE.md`](COMPLETION_REPORT_TEMPLATE.md)
- Record reviewed:
- Reviewer:
- Review date:

## Template completion

- [ ] The correct template type was selected.
- [ ] Every allowed placeholder was replaced.
- [ ] No unknown project fact was invented.
- [ ] Required sections were preserved.
- [ ] Optional omissions are justified.
- [ ] Ownership and scope are explicit.
- [ ] Related evidence and decisions resolve.
- [ ] Review and approval roles are distinguished.
- [ ] No secret or sensitive production value is embedded.

## Content-specific review

- [ ] Scope matches authorization.
- [ ] Validation rows contain exact commands and evidence.
- [ ] Not-run checks are explicit.
- [ ] Artifact identifiers are immutable where possible.
- [ ] Limitations and residual risk are honest.
- [ ] Execution discipline records failed or indeterminate outcomes, authorization/recovery continuity, and any out-of-scope routing.
- [ ] Retry ledger has one row per budget-consuming action and each subsequent successful objective-clearing action at its current retry position, with objective/blocker, action, actor, execution context, start/end, reconciliation, result, budget position/count, justification, and terminal disposition.
- [ ] Retry counting distinguishes failed or indeterminate read-only execution from successful evidence-only discovery, reconciliation, or validation; exhaustion and any reset basis are explicit.
- [ ] Delegation handoff records value and state, and confirms retry/no-progress boundaries remain enforced and were not reset or bypassed.

## Validation

- [ ] Repository validation passed.
- [ ] Relative link validation passed.
- [ ] Template validation passed.
- [ ] Applicable schema validation passed.
- [ ] Checks not run are recorded.

## Decision

- [ ] Approved
- [ ] Approved with conditions
- [ ] Changes required
- [ ] Rejected

Conditions, findings, and limitations:
