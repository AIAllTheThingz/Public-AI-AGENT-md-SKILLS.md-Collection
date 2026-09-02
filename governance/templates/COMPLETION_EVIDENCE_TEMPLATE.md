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

| Check | Command or source | Result | Evidence | Limitations |
|---|---|---|---|---|

## Execution discipline

- Failed or indeterminate outcomes, actual-state reconciliation, and confirmation that authorization and recovery controls remain valid for consequential mutations:
- Retry ledger, grouped into repeatable sequences for each objective or blocker, with one row per action (execution context is the command sequence, plan, workflow, tool, agent, strategy, task, or session as applicable):

| Objective/blocker | Sequence | Sequence reset evidence | Action | Actor | Execution context | Start | End | Observable-effects reconciliation | Result | Budget position/count | Justification | Terminal disposition |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| | | | | | | | | | | | | |

The budget allows the initial attempt plus at most two justified retries per sequence. A budget-consuming attempt is any execution action directed at achieving the objective or clearing the blocker whose observable effects are reconciled and whose result is Failed or Indeterminate, whether mutating or read-only; every subsequent execution action after that result for the objective or blocker is a retry even within the same command sequence, plan, workflow, tool, agent, or strategy; successful read-only discovery, reconciliation, or validation that only gathers evidence is non-consuming, a Failed or Indeterminate read-only execution directed at the objective or blocker consumes budget, and a subsequent Successful objective-clearing action is recorded at its current retry position and ends the objective or blocker. Preserve every stopped sequence; each sequence after the first records the prior stop/report, separate accountable authorization, and material-change evidence.
- Reset basis, if any (prior sequence stopped and reported, accountable requester or owner authorization, material blocker or relevant scope or system-state change):
- Progress or blocker narrowing:
- Delegation handoff (value, failure evidence, blocker, retry count, unresolved state):
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
