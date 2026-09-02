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

| Command or check | Result | Environment | Evidence | Limitations |
|---|---|---|---|---|
{{VALIDATION_ROWS}}

## Validation not performed

{{VALIDATION_NOT_PERFORMED}}

## Execution discipline

- Failed or indeterminate outcomes:
{{FAILED_OR_INDETERMINATE_OUTCOMES}}
- Authorization/recovery continuity for consequential mutations:
{{AUTHORIZATION_RECOVERY_CONTINUITY}}
- Retry ledger, one row per budget-consuming action (execution context is the command sequence, plan, workflow, tool, agent, strategy, task, or session as applicable):

| Objective/blocker | Action | Actor | Execution context | Start | End | Observable-effects reconciliation | Result | Budget position/count | Justification | Terminal disposition |
|---|---|---|---|---|---|---|---|---|---|---|
{{RETRY_LEDGER_ROWS}}

- Reset basis, if any:
{{RESET_BASIS}}
- Progress or blocker narrowing:
{{PROGRESS_OR_BLOCKER_NARROWING}}
- Delegation handoff:
{{DELEGATION_HANDOFF}}
- Delegation boundary continuity before handoff completion:
{{DELEGATION_BOUNDARY_CONTINUITY}}
- Authorized routing of non-blocking out-of-scope findings:
{{OUT_OF_SCOPE_ROUTING}}

The retry budget allows the initial attempt plus at most two justified retries. A budget-consuming attempt is any execution action directed at achieving the objective or clearing the blocker whose observable effects are reconciled and whose result is Failed or Indeterminate, whether mutating or read-only; every subsequent execution action after that result for the objective or blocker is a retry even within the same command sequence, plan, workflow, tool, agent, or strategy. Successful read-only discovery, reconciliation, or validation that only gathers evidence is non-consuming, a Failed or Indeterminate read-only execution directed at the objective or blocker consumes budget, and a subsequent Successful objective-clearing action is recorded at its current retry position and ends the objective or blocker.

## Deployment and operational impact

{{OPERATIONAL_IMPACT}}

## Rollback or recovery

{{ROLLBACK_RECOVERY}}

## Limitations and remaining risks

{{LIMITATIONS}}

## Human review

{{HUMAN_REVIEW}}

The report must not claim a stronger state than the evidence supports.
