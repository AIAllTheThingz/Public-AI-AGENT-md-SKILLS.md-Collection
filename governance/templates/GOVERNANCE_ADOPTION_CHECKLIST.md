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
- [ ] Count each budget-consuming attempt as one consequential action ending after observable effects are reconciled with a Failed or Indeterminate result; each subsequent consequential action counts as a retry even within the same command sequence, plan, workflow, tool, agent, or strategy; read-only discovery, reconciliation, and non-state-changing validation do not consume budget, and Successful ends the objective or blocker
- [ ] A new budget requires the prior sequence to stop and report, separate accountable requester or owner authorization, and recorded material blocker or relevant scope or system-state change

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
