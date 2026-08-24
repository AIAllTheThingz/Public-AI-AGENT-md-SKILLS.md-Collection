---
id: DISC-TPL-SRE-EVIDENCE
title: Site Reliability Engineering Evidence Record Template
version: 0.1.0
status: baseline
---
# Site Reliability Engineering Evidence Record

## Change

- Repository:
- Branch or pull request:
- Commit:
- Date:
- Author:
- Reviewers:
- Risk classification:

## Scope and applicability

- Reason this discipline applies:
- In-scope components, data, environments, users, and operations:
- Out-of-scope items:
- Trust boundaries and dependencies:
- Assumptions:

## Requirements addressed

| Requirement or standard | Implementation | Evidence | Result |
|---|---|---|---|
| | | | |

## Validation

| Command, review, or test | Environment | Result | Evidence location |
|---|---|---|---|
| | | | |

## Production readiness

| Area | Applicability | Result (`Pass`, `Fail`, `Blocked`, `NotApplicable`) | Evidence or justification | Owner |
|---|---|---|---|---|
| Deployment | | | | |
| Rollback and recovery | | | | |
| Backup and restore | | | | |
| Data migration | | | | |
| Observability | | | | |
| Capacity | | | | |
| Security | | | | |
| Privacy | | | | |
| Failure behavior | | | | |
| Operations | | | | |
| Cost | | | | |
| Limitations and risks | | | | |

- Data migration rehearsal and recovery evidence:
- Irreversible-change handling and accepted risk:
- Data migration go/no-go criteria and decision authority:
- Overall readiness result (`Pass`, `Fail`, `Blocked`, `NotApplicable`):
- Decision authority:
- Decision date:
- Approved candidate, operating scope, and conditions:

## Scaling strategy

| Area | State (`Applicable`, `NotApplicable`, `NotRun`, `Blocked`, `Failed`, `Verified`) | Authorized criteria and decision evidence | Supported envelope | Owner |
|---|---|---|---|---|
| Horizontal scaling | | | | |
| Vertical scaling | | | | |
| Statelessness | | | | |
| State and sessions | | | | |
| Connections and pooling | | | | |
| Caching | | | | |
| Asynchronous processing | | | | |
| Queues and background workers | | | | |
| Rate limiting | | | | |
| Partitioning | | | | |
| Replication | | | | |
| Read/write distribution | | | | |
| Storage growth | | | | |
| Network saturation | | | | |
| External quotas | | | | |
| Autoscaling | | | | |
| Cold starts | | | | |
| Resource limits | | | | |
| Cost per workload unit | | | | |

- Overall scaling-strategy state (`Verified`, `Failed`, `NotRun`, `Blocked`, `NotApplicable`):
- Decision authority:
- Supported workload and operating envelope:
- `NotApplicable` rationale, unresolved areas, or verification limitations:

Use `Failed` when representative validation executes but misses authorized criteria; do not record tested failure as merely `Applicable`, `NotRun`, or `Blocked`. Any `Applicable`, `NotRun`, `Blocked`, or `Failed` area prevents an overall `Verified` state.

## Checks not run

| Check | Reason | Risk | Follow-up owner |
|---|---|---|---|
| | | | |

## Exceptions and limitations

- Approved exceptions:
- Expiration or review dates:
- Known limitations:
- Residual risks:
- Compensating controls:

## Completion assessment

- [ ] Implemented
- [ ] Tested
- [ ] Reviewed
- [ ] Operationally verified where applicable
- [ ] Documentation updated
- [ ] Remaining risk accepted by an accountable owner

Completion statement:
