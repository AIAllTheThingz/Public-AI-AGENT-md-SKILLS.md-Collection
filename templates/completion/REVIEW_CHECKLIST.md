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
- [ ] Validation rows contain exact commands and evidence; each executed pass or failure identifies the exact retry-ledger objective and unique action that performed the check.
- [ ] Not-run checks are explicit.
- [ ] Artifact identifiers are immutable where possible.
- [ ] Limitations and residual risk are honest.
- [ ] Schema-backed JSON uses one `retryLedger` map keyed by objective; each objective's `failedOrIndeterminateOutcomes` array is non-empty exactly when the same ledger contains a Failed or Indeterminate attempt, and no objective is split across maps.
- [ ] Execution discipline records authorization/recovery continuity and any out-of-scope routing.
- [ ] Retry ledger has one row per budget-consuming action, each successful non-consuming discovery, reconciliation, or validation action, and each subsequent successful objective-clearing action at its current retry position, with objective/blocker, sequence, sequence-specific reset evidence, action ID, action, actor, execution context, start/end, reconciliation, result, budget position/count, retry-specific material change and causal rationale, justification, and terminal disposition.
- [ ] Every executed passed or failed validation identifies one exact ledger action using the same objective ID and action ID, and the referenced action result matches the validation result.
- [ ] Every retry records a causally relevant material change and why it may now succeed; every prior retry sequence remains present, and each sequence after the first records the immediately prior `sequenceId`, prior stop/report, separate accountable authorization and `authorizedAt` timestamp, material-change evidence, and causal rationale in `resetAuthorization`.
- [ ] Retry counting distinguishes failed or indeterminate read-only execution from successful evidence-only discovery, reconciliation, or validation; exhaustion and any reset basis are explicit.
- [ ] Every prior and current sequence has an explicit per-sequence delegation handoff; delegated work includes meaningful value, failure evidence from the containing objective's outcomes, blocker, retry count equal to that same sequence's recorded retry depth, unresolved state with that sequence ending `reported-unresolved`, and confirmation that retry/no-progress boundaries remain enforced and were not reset or bypassed. Prior-sequence handoffs remain preserved after an authorized reset.
- [ ] A sequence ending `reported-unresolved` stores earlier successful evidence in `preTerminalNonConsumingActions`, every retained action ends no later than the terminal attempt starts, and the sequence has no `nonConsumingActions`; other sequences leave the pre-terminal array empty, and any action after the stop appears only in a separately authorized reset sequence.
- [ ] Every action other than an objective-completing attempt ends no later than that terminal attempt starts; no activity is recorded after completion.

## Validation

- [ ] Repository validation passed.
- [ ] Relative link validation passed.
- [ ] Template validation passed.
- [ ] Applicable schema and completion semantic validation passed.
- [ ] Checks not run are recorded.

## Decision

- [ ] Approved
- [ ] Approved with conditions
- [ ] Changes required
- [ ] Rejected

Conditions, findings, and limitations:
