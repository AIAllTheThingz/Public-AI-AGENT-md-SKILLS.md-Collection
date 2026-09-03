---
id: TEMPLATE-COMPLETION-001
title: Completion Report Template
version: 0.3.0
status: baseline
template_type: completion-report
---

# Completion Report Template

- Work ID: `{{WORK_ID}}`
- Completion status: `{{COMPLETION_STATUS}}`
- Artifact identifiers: {{ARTIFACT_IDENTIFIERS}}

An `implemented` status requires a non-empty retry ledger containing a `Successful` action whose terminal disposition is `objective-completed`.

## Scope

{{SCOPE}}

## Change summary

{{CHANGE_SUMMARY}}

## Files and artifacts changed

{{FILES_CHANGED}}

## Risk classification

{{RISK_CLASSIFICATION}}

## Security and privacy impact

{{SECURITY_IMPACT}}

## Compatibility and migration impact

{{COMPATIBILITY_IMPACT}}

## Validation performed

| Objective ID | Action ID | Command or check | Result | Environment | Evidence | Limitations |
|---|---|---|---|---|---|---|
{{VALIDATION_ROWS}}

## Validation not performed

{{VALIDATION_NOT_PERFORMED}}

## Execution discipline

- Failed or indeterminate outcomes, recorded inside the same retry-ledger entry keyed by objective:
{{FAILED_OR_INDETERMINATE_OUTCOMES}}
- Authorization/recovery continuity for consequential mutations:
{{AUTHORIZATION_RECOVERY_CONTINUITY}}
- Retry ledger, grouped into repeatable sequences for each objective or blocker, with one row per budget-consuming action and each subsequent Successful objective-clearing action recorded at its current retry position; every retry records its causally relevant material change and why that change creates a concrete reason to succeed; also record each Successful non-consuming discovery, reconciliation, or validation action (execution context is the command sequence, plan, workflow, tool, agent, strategy, task, or session as applicable):

| Objective/blocker | Sequence | Sequence reset evidence | Action ID | Action | Actor | Execution context | Start | End | Observable-effects reconciliation | Result | Budget position/count | Retry material change | Retry causal rationale | Justification | Terminal disposition |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
{{RETRY_LEDGER_ROWS}}

For schema-backed JSON, use one `retryLedger` map keyed by objective. Each executed `passed` or `failed` validation records an `objectiveId` that exactly matches the ledger key and an `actionId` that uniquely identifies the ledger action performing that check; the referenced action carries the same `actionId`. Each objective ledger contains its own `failedOrIndeterminateOutcomes` array, and every prior or current sequence contains its own `delegationHandoff`. The outcome array is non-empty exactly when that same ledger contains a Failed or Indeterminate attempt and supplies authoritative failure evidence for a delegated handoff. A delegated handoff requires its containing sequence to end `reported-unresolved`, and its `retryCount` must equal that same sequence's recorded retry depth. Preserve the handoff on a prior sequence when an authorized reset creates a new current sequence. No second objective map exists, so an objective and its failure evidence cannot be split across ledgers. The rendered summaries and table above describe the same per-objective, per-sequence records.

- Reset basis, if any:
{{RESET_BASIS}}
- Progress or blocker narrowing:
{{PROGRESS_OR_BLOCKER_NARROWING}}
- Per-sequence delegation handoffs (`delegated`; sequence; summary; meaningful value; failure evidence from the containing objective's outcome array; blocker; retry count equal to that sequence's recorded retries; unresolved state; boundaries preserved):
{{DELEGATION_HANDOFF}}
- Delegation boundary continuity before handoff completion:
{{DELEGATION_BOUNDARY_CONTINUITY}}
- Authorized routing of non-blocking out-of-scope findings:
{{OUT_OF_SCOPE_ROUTING}}

The retry budget allows the initial attempt plus at most two justified retries per sequence. A budget-consuming attempt is any execution action directed at achieving the objective or clearing the blocker whose observable effects are reconciled and whose result is Failed or Indeterminate, whether mutating or read-only; every subsequent execution action after that result for the objective or blocker is a retry even within the same command sequence, plan, workflow, tool, agent, or strategy. Successful read-only discovery, reconciliation, or validation that only gathers evidence is non-consuming and is recorded as a non-consuming ledger row; a Failed or Indeterminate read-only execution directed at the objective or blocker consumes budget, and a subsequent Successful objective-clearing action is recorded at its current retry position and ends the objective or blocker. Every other action ends no later than that objective-completing attempt starts. A sequence ending `reported-unresolved` records successful evidence gathered before the terminal attempt in `preTerminalNonConsumingActions` and leaves `nonConsumingActions` empty; every such action ends no later than the terminal attempt starts, and further action requires a separately authorized reset sequence. Other sequences leave the pre-terminal array empty. Preserve every stopped sequence and its handoff; each sequence after the first requires the prior sequence stop/report, separate accountable authorization, material-change evidence, and causal rationale explaining why that change creates a concrete reason the new sequence may succeed. Its `resetAuthorization.priorSequenceId` identifies the immediately preceding unresolved sequence, and `authorizedAt` falls after that sequence's terminal attempt ends and before the new sequence starts.

## Deployment and operational impact

{{OPERATIONAL_IMPACT}}

## Rollback or recovery

{{ROLLBACK_RECOVERY}}

## Limitations and remaining risks

{{LIMITATIONS}}

## Human review

{{HUMAN_REVIEW}}

The report must not claim a stronger state than the evidence supports.
