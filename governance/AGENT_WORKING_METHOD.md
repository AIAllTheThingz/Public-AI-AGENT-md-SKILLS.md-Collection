---
id: GOV-WORK
title: Agent Working Method
version: 0.3.0
status: baseline
applies_to:
  - all-projects
depends_on:
  - GOV-CONTRACT
---

# Agent Working Method

## Purpose

Defines the required sequence for discovery, planning, implementation, validation, and reporting.

## Applicability

This policy applies to:

- all engineering changes, reviews, investigations, documentation changes, and automation work
- both code-producing and non-code-producing agents

## Roles

- **Requester:** states the desired outcome and explicit constraints.
- **Implementer or agent:** discovers context, controls scope, validates work, and reports evidence.
- **Reviewer:** checks assumptions, risk, scope, validation, and completion claims.

## Policy requirements

### GOV-WORK-001

**Requirement:** Inspect repository instructions, architecture, tests, dependencies, and affected code before editing.

**Expected evidence:** Discovery record lists instructions and relevant files inspected.

### GOV-WORK-002

**Requirement:** State assumptions and resolve material uncertainty before high-risk implementation.

**Expected evidence:** Assumptions and unresolved questions are recorded before execution.

### GOV-WORK-003

**Requirement:** Make the smallest coherent change and avoid unrelated refactoring.

**Expected evidence:** Diff review confirms scope and identifies intentionally related changes.

### GOV-WORK-004

**Requirement:** Implement in safe phases: discovery, validation, simulation where applicable, reporting, then execution.

**Expected evidence:** Work record shows which phases were performed and why any phase was inapplicable.

### GOV-WORK-005

**Requirement:** Run relevant validation and report failures honestly.

**Expected evidence:** Exact commands, environments, results, and failure details are recorded.

### GOV-WORK-006

**Requirement:** Do not claim completion until required evidence exists.

**Expected evidence:** Completion result is linked to validation and review evidence.

### GOV-WORK-007

**Requirement:** Classify change type, risk, affected contracts, and required reviewers before implementation.

**Expected evidence:** Change plan identifies risk and acceptance criteria.

### GOV-WORK-008

**Requirement:** Define rollback, roll-forward, or recovery expectations before consequential mutation.

**Expected evidence:** Recovery plan is reviewed before execution.

### GOV-WORK-009

**Requirement:** Stop when prerequisites, target identity, authorization, or safe validation are missing.

**Expected evidence:** Stop condition is recorded rather than bypassed.

### GOV-WORK-010

**Requirement:** Review the final diff for unrelated changes, secrets, unsafe defaults, compatibility regressions, and false completion claims.

**Expected evidence:** Final diff review appears in completion evidence.

### GOV-WORK-011

**Requirement:** Do not repeat a failed or indeterminate action unless a causally relevant material change—new evidence, changed input/configuration/state, corrected assumption, or materially different implementation or validation method—creates a concrete reason it may succeed; consequential mutations require actual-state reconciliation and confirmation that authorization and recovery controls remain valid; rewording, rerunning, changing tools or agents, or delegating the same approach is not material change.

**Expected evidence:** Failure or indeterminate result, material change and causal rationale, and any required state reconciliation and authorization/recovery confirmation are recorded.

### GOV-WORK-012

**Requirement:** For the same objective or underlying blocker across the whole active task or change and across all tools, tasks, sessions, agents, and strategies, allow the initial attempt plus at most two justified retries; once exhausted, stop all further execution attempts for that objective or blocker and report unresolved; a new tool, strategy, hypothesis, agent, or delegation does not reset the budget; a new budget exists only after the prior sequence stopped and reported, an accountable requester or owner separately authorizes a new execution sequence, and recorded evidence shows that the underlying blocker or relevant scope or system state materially changed.

**Expected evidence:** A retry ledger carries the objective or blocker, active task or change, all attempts and actors across tools, tasks, sessions, agents, and strategies, each retry's justification, and terminal unresolved disposition; any reset records the prior stop and report, accountable requester or owner authorization, and material blocker or relevant scope or system-state change.

### GOV-WORK-013

**Requirement:** Within any remaining GOV-WORK-012 budget, stop/report or adopt a new evidence-based hypothesis when successive actions across approaches or agents make no relevant, nonduplicative progress toward acceptance criteria or narrowing the blocker; after that budget is exhausted, stop all further execution attempts and report unresolved; changing commands, tools, agents, or strategies, producing different but irrelevant output, unrelated scope expansion, or speculative implementation is not progress; route non-blocking out-of-scope findings through the applicable authorized channel under GOV-WORK-003 rather than adding them to active scope.

**Expected evidence:** A progress record maps successive actions to acceptance criteria or blocker narrowing within any remaining GOV-WORK-012 budget, records the stop or new hypothesis or exhausted unresolved disposition, and records authorized routing of non-blocking out-of-scope findings.

### GOV-WORK-014

**Requirement:** Delegate only when it adds meaningful value through different specialization, independent review, alternative implementation or validation strategy, security or testing focus, or a different evidence source; handoff carries failure evidence, blocker, retry count, and unresolved state; delegation cannot repeat a failed approach or bypass or reset retry or no-progress boundaries.

**Expected evidence:** Delegation record states the meaningful value, carries failure evidence, blocker, retry count, and unresolved state, and confirms retry and no-progress boundaries remain in force.

## Decision gates

- Discovery complete before planning.
- Risk and acceptance criteria defined before implementation.
- Validation complete before completion reporting.
- Authorization and rollback readiness confirmed before consequential execution.
- Failed or indeterminate actions are not repeated without a recorded causal material change and required state reconciliation.
- GOV-WORK-012 retry budget is confirmed before another attempt; when exhausted, all further attempts for the objective or blocker stop until the prior sequence is stopped and reported, an accountable requester or owner separately authorizes a new sequence, and recorded evidence shows a material blocker or relevant scope or system-state change.
- GOV-WORK-013 progress is assessed within the remaining GOV-WORK-012 budget; no relevant progress requires stop/report or a new evidence-based hypothesis, while an exhausted budget requires stopping all attempts and reporting unresolved.
- Delegation value, handoff state, and retry/no-progress boundaries are confirmed before handoff.

## Required records and evidence

- Scope statement
- Files and instructions inspected
- Risk and acceptance criteria
- Implementation plan
- Validation commands and results
- Final diff review
- Limitations and remaining risks
- Failure or indeterminate results, material-change rationale, state reconciliation, retry budget, progress/blocker disposition, and delegation/handoff evidence are recorded.

## Exceptions and prohibited shortcuts

Urgency may shorten ceremony but does not permit fabricated evidence, missing authorization, or concealed risk.

An approved exception must follow [EXCEPTION_PROCESS.md](EXCEPTION_PROCESS.md). Failed or unavailable validation must remain visible.

## Review triggers

Re-review this policy decision when scope, risk, architecture, data, privilege, environment, evidence, owner, approver, artifact, or assumptions change materially.

## Related governance

- [Organization Contract](ORGANIZATION_CONTRACT.md)
- [Agent Working Method](AGENT_WORKING_METHOD.md)
- [Risk Classification](RISK_CLASSIFICATION.md)
- [Completion Evidence](COMPLETION_EVIDENCE.md)
- [Human Review Policy](HUMAN_REVIEW_POLICY.md)
- [Exception Process](EXCEPTION_PROCESS.md)

## Completion boundary

Compliance with this policy is not established by the presence of this file. The adopting repository must implement, validate, review, and record the applicable controls.
