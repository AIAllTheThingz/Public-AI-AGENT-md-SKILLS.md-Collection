---
id: TEMPLATE-EX-COMPLETION-001
title: Completion Report Example
version: 0.3.0
status: baseline
---

# Completion Report Example

- Work ID: `PR-EXAMPLE-0042`
- Completion status: `partially-validated`
- Artifact identifiers: commit `0000000000000000000000000000000000000000`

## Scope

Documentation-only template-library update.

## Change summary

Expanded reusable templates and added validation tooling.

## Files and artifacts changed

Template Markdown, examples, validator, and root catalog documents.

## Risk classification

Low for this fictitious documentation-only example.

## Security and privacy impact

No production systems or sensitive data are affected.

## Compatibility and migration impact

Stable template paths remain present.

## Validation performed

| Command or check | Result | Environment | Evidence | Limitations |
|---|---|---|---|---|
| `python tools/validate-templates/validate_templates.py` | passed | fictitious CI runner | workflow log | No adopting project tested |
| `python tools/check-links/check_links.py` | passed | fictitious CI runner | workflow log | External links not fetched |

## Validation not performed

No copied-template adoption test was run in a real project.

## Execution discipline

Failed or indeterminate outcomes: One objective-directed read-only validation returned `Failed` because the fixture still used the v1 completion contract; observable output was reconciled and the producer fixture was corrected.

Authorization/recovery continuity for consequential mutations: Confirmed authorization and recovery controls remained valid; the correction was limited to the fictitious fixture.

| Objective/blocker | Sequence | Sequence reset evidence | Action | Actor | Execution context | Start | End | Observable-effects reconciliation | Result | Budget position/count | Justification | Terminal disposition |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Completion record migration | Sequence 1 | Initial sequence; no reset | Validate completion fixture | Example maintainer | command sequence `migration-check`; plan `RC-MIGRATION`; workflow `fictitious-ci`; tool `template-validator`; task `PR-EXAMPLE-0042` | 2026-08-16T10:00:00Z | 2026-08-16T10:00:01Z | No target-state mutation; failed output reconciled | Failed | Initial attempt (1 budget-consuming action) | Detected v1 fixture against the current v2 contract | Retry justified after correcting the fixture |
| Completion record migration | Sequence 1 | Initial sequence; no reset | Inspect schema-version routing and fixture metadata | Example maintainer | command sequence `migration-check`; plan `RC-MIGRATION`; workflow `fictitious-ci`; tool `template-validator`; task `PR-EXAMPLE-0042` | 2026-08-16T10:01:00Z | 2026-08-16T10:01:01Z | No target-state mutation; evidence reconciled | Successful | Non-consuming | Gathered evidence identifying the version mismatch | Not terminal |
| Completion record migration | Sequence 1 | Initial sequence; no reset | Validate corrected completion fixture | Example maintainer | command sequence `migration-check`; plan `RC-MIGRATION`; workflow `fictitious-ci`; tool `template-validator`; task `PR-EXAMPLE-0042` | 2026-08-16T10:02:00Z | 2026-08-16T10:02:01Z | Corrected fixture output reconciled; no target-state mutation | Successful | Retry 1 (successful objective-clearing action) | Corrected producer fixture using reviewed facts | Objective complete |

Reset basis: None; no new execution sequence was authorized.

Progress or blocker narrowing: The failed validation identified the v1 fixture as the blocker; the corrected fixture validated the current contract.

Delegation handoff: No delegation; the example maintainer retained the work.

Delegation boundary continuity before handoff completion: Confirmed; retry and no-progress boundaries remained enforced and were not reset or bypassed.

Authorized routing of non-blocking out-of-scope findings: None; no non-blocking out-of-scope finding was identified.

## Deployment and operational impact

None.

## Rollback or recovery

Revert the documentation commit.

## Limitations and remaining risks

Placeholder guidance still requires human review in adopting projects.

## Human review

Reviewer not yet assigned.

## Boundary

This example does not claim production readiness.
