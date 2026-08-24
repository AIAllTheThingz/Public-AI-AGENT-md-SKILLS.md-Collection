---
id: DISC-TPL-PROD-EVIDENCE
title: Product Management Evidence Record Template
version: 0.1.0
status: baseline
---

# Product Management Evidence Record

## Context

- Product or capability:
- Date and source revision:
- Owner and reviewers:
- Risk classification:
- Problem and intended outcome:
- Intended users or actors:
- Facts, assumptions, constraints, and unknowns:
- Research state (`Performed`, `NotRun`, `Blocked`, or `NotApplicable`):
- Research evidence or rationale:

## Requirement traceability

Record one row per lifecycle stage so that each stage has an independent evidence state.

| Requirement | Lifecycle stage | State | Evidence | Owner |
|---|---|---|---|---|
| `REQ-___-___` | Idea/source | `Planned` | | |
| `REQ-___-___` | Requirement | `Planned` | | |
| `REQ-___-___` | Architecture decision | `NotRun` | | |
| `REQ-___-___` | Implementation | `NotRun` | | |
| `REQ-___-___` | Test | `NotRun` | | |
| `REQ-___-___` | Release/deployment | `NotRun` | | |
| `REQ-___-___` | Production evidence | `NotRun` | | |

Allowed states: `Planned`, `Implemented`, `Tested`, `Reviewed`, `OperationallyVerified`, `NotRun`, `Blocked`, `NotApplicable`. Explain every `NotApplicable` entry.

## Acceptance validation

Record acceptance separately from execution or evidence state. `Tested` and the presence of output do not imply `Pass`.

| Requirement | Acceptance criterion | Result (`Pass`, `Fail`, `Blocked`, `NotRun`, `NotApplicable`) | Exact artifact and conditions | Validation method | Primary evidence | Owner |
|---|---|---|---|---|---|---|
| `REQ-___-___` | | | | | | |

Every `NotApplicable` result requires reviewed justification. A requirement is accepted only when every applicable criterion has a current explicit `Pass` for the exact reviewed artifact and conditions.

## Decisions and limitations

- MVP inclusions and exclusions:
- Decisions and alternatives:
- Checks not run and reasons:
- Blockers, limitations, unresolved risks, and follow-up owners:
- Review or transition decision:
