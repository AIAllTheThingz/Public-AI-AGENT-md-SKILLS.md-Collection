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
- [ ] Schema-backed JSON uses one `retryLedger` map keyed by objective; each objective's `failedOrIndeterminateOutcomes` array is non-empty exactly when the same ledger contains a Failed or Indeterminate attempt, and no objective is split across maps.
- [ ] Execution discipline records authorization/recovery continuity and any out-of-scope routing.
- [ ] Retry ledger has one row per budget-consuming action, each successful non-consuming discovery, reconciliation, or validation action, and each subsequent successful objective-clearing action at its current retry position, with objective/blocker, sequence, sequence-specific reset evidence, action, actor, execution context, start/end, reconciliation, result, budget position/count, retry-specific material change and causal rationale, justification, and terminal disposition.
- [ ] Every retry records a causally relevant material change and why it may now succeed; every prior retry sequence remains present, and each sequence after the first records the prior stop/report, separate accountable authorization, material-change evidence, and causal rationale.
- [ ] Retry counting distinguishes failed or indeterminate read-only execution from successful evidence-only discovery, reconciliation, or validation; exhaustion and any reset basis are explicit.
- [ ] Delegation handoff explicitly records whether work was delegated; delegated work includes meaningful value, failure evidence, blocker, retry count, unresolved state, and confirmation that retry/no-progress boundaries remain enforced and were not reset or bypassed.

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
