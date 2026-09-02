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
- Retry ledger, one row per action (execution context is the command sequence, plan, workflow, tool, agent, strategy, task, or session as applicable):

| Objective/blocker | Action | Actor | Execution context | Start | End | Observable-effects reconciliation | Result | Budget position/count | Justification | Terminal disposition |
|---|---|---|---|---|---|---|---|---|---|---|
| | | | | | | | | | | |

Each budget-consuming action is one consequential execution action directed at achieving the objective or clearing the blocker; each consequential action after Failed or Indeterminate counts as a retry even within the same command sequence, plan, workflow, tool, agent, or strategy; read-only discovery, actual-state reconciliation, and validation that do not themselves try to change target state are non-consuming; Successful ends the objective or blocker rather than consuming a retry.
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
