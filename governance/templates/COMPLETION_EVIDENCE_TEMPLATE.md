---
id: GOV-TPL-EVID-001
title: Completion Evidence Template
version: 0.3.0
status: baseline
---

# Completion Evidence

## Status

- [ ] Implemented
- [ ] Validated
- [ ] Partially validated
- [ ] Not completed

## Scope

- Summary:
- Changed files:
- Commit or artifact:
- Risk:

## Validation

| Objective ID | Action ID | Check | Command or source | Result | Evidence | Limitations |
|---|---|---|---|---|---|---|

## Execution discipline

- Failed or indeterminate outcomes from the same retry-ledger entry keyed by objective; actual-state reconciliation; and confirmation that authorization and recovery controls remain valid for consequential mutations:
- Retry ledger, grouped into repeatable sequences for each objective or blocker, with one row per action and retry-specific material-change and causal-rationale evidence (execution context is the command sequence, plan, workflow, tool, agent, strategy, task, or session as applicable):

| Objective/blocker | Sequence | Sequence reset evidence | Action ID | Action | Actor | Execution context | Start | End | Observable-effects reconciliation | Result | Budget position/count | Retry material change | Retry causal rationale | Justification | Terminal disposition |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| | | | | | | | | | | | | | | | |

For schema-backed JSON, use one `retryLedger` map keyed by objective. Each executed `passed` or `failed` validation records an `objectiveId` that exactly matches the ledger key and an `actionId` that uniquely identifies the ledger action performing that check; the referenced action carries the same `actionId`. Each objective ledger contains its own `failedOrIndeterminateOutcomes` array, and every prior or current sequence contains its own `delegationHandoff`. The outcome array is non-empty exactly when that ledger contains a Failed or Indeterminate attempt and supplies a delegated handoff's authoritative failure evidence. A delegated handoff requires its containing sequence to end `reported-unresolved`, and its `retryCount` equals that same sequence's recorded retry depth. Preserve prior-sequence handoffs after an authorized reset. No second objective map exists, so an objective and its failure evidence cannot be split across ledgers. The rendered outcome, handoff, and evidence table describe those same per-objective, per-sequence records.

The budget allows the initial attempt plus at most two justified retries per sequence. A budget-consuming attempt is any execution action directed at achieving the objective or clearing the blocker whose observable effects are reconciled and whose result is Failed or Indeterminate, whether mutating or read-only; every subsequent execution action after that result for the objective or blocker is a retry even within the same command sequence, plan, workflow, tool, agent, or strategy. Every retry records a causally relevant material change and why that change creates a concrete reason it may succeed; generic justification is insufficient. Successful read-only discovery, reconciliation, or validation that only gathers evidence is non-consuming, a Failed or Indeterminate read-only execution directed at the objective or blocker consumes budget, and a subsequent Successful objective-clearing action is recorded at its current retry position and ends the objective or blocker. Every other action ends no later than that objective-completing attempt starts. A sequence ending `reported-unresolved` stores earlier successful evidence in `preTerminalNonConsumingActions` and leaves `nonConsumingActions` empty; each retained action ends no later than the terminal attempt starts, and further action requires a separately authorized reset sequence, while other sequences leave the pre-terminal array empty. Preserve every stopped sequence and its handoff; each sequence after the first records `resetAuthorization.priorSequenceId` for the immediately preceding unresolved sequence, a separate accountable authorization timestamp in `authorizedAt` after that stop and before the new sequence starts, material-change evidence, and causal rationale. Full v2 conformance requires both JSON Schema validation and the completion semantic validator invoked by `tools/validate-schemas/validate_schemas.py`.
- Reset basis, if any (immediately prior sequence ID and stop/report, accountable requester or owner authorization and timestamp, material blocker or relevant scope or system-state change, and causal rationale):
- Progress or blocker narrowing:
- Per-sequence delegation handoffs (`delegated`; sequence; summary; meaningful value; failure evidence from the containing objective's outcome array; blocker; retry count equal to that sequence's retry depth; unresolved state; boundaries preserved):
- [ ] Before handoff completion, active retry and no-progress boundaries remain enforced and were not reset or bypassed:
- Authorized routing of non-blocking out-of-scope findings:

## Review and authorization

- Reviewer:
- Approval:
- Authorization:
- Exceptions:
- Residual risk:

## Limitations

- Checks not run:
- Unverified behavior:
- Environment differences:
- Follow-up:
