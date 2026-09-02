---
id: GOV-TPL-ADOPT-001
title: Governance Adoption Checklist
version: 0.3.0
status: baseline
---

# Governance Adoption Checklist

## Authority and scope

- [ ] Governance owner identified
- [ ] Systems and repositories in scope identified
- [ ] Applicable external obligations identified
- [ ] Request, review, approval, and operation roles defined
- [ ] Delegated authority and escalation defined
- [ ] Separation of duties defined for high and critical work

## Risk and decisions

- [ ] Risk classes tailored
- [ ] Review and approval requirements mapped to risk
- [ ] Threat-model triggers defined
- [ ] Rollback and recovery expectations defined
- [ ] Production-readiness gate defined
- [ ] Residual-risk acceptance authority defined

## Records and evidence

- [ ] Record locations selected
- [ ] Retention and access defined
- [ ] Completion evidence format selected
- [ ] Authorization record available
- [ ] Review and approval record available
- [ ] Exception record available
- [ ] Vulnerability triage and closure records available
- [ ] GOV-WORK-011..014 records selected for failed or indeterminate outcomes, reconciliation, authorization/recovery-control continuity for consequential mutations, retry ledger/budget, terminal disposition/reset basis, progress/blocker narrowing, delegation handoff, and authorized out-of-scope routing
- [ ] Retry ledger spans the objective or blocker across the active task or change and all tools, tasks, sessions, agents, and strategies; exhaustion stops further attempts and records unresolved
- [ ] Count a budget-consuming attempt as any execution action directed at the objective or blocker whose observable effects are reconciled with a Failed or Indeterminate result, whether mutating or read-only; count every subsequent execution action after that result as a retry even within the same command sequence, plan, workflow, tool, agent, or strategy; successful read-only discovery, reconciliation, or validation that only gathers evidence is non-consuming, Failed or Indeterminate read-only execution directed at the objective or blocker consumes budget, and a subsequent Successful objective-clearing action is recorded at its current retry position and ends the objective or blocker
- [ ] Preserve every retry sequence for the objective or blocker; each sequence after the first requires the prior sequence to stop and report, separate accountable requester or owner authorization, and recorded material blocker or relevant scope or system-state change

## Integration

- [ ] Pull-request process integrated
- [ ] CI and release gates integrated
- [ ] Deployment or change-management integration defined
- [ ] Incident and vulnerability workflows integrated
- [ ] Exception expiry tracking implemented
- [ ] Policy review schedule defined

## Validation and approval

- [ ] Pilot completed
- [ ] Known gaps recorded
- [ ] Migration plan approved
- [ ] Governance package reviewed
- [ ] Effective date recorded
- [ ] Accountable approval recorded
