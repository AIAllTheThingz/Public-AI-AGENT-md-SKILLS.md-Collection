## Summary

Describe the focused change and why it is needed.

## Change classification and risk

- Classification (select all that apply): Editorial / Normative / Compatibility / Tooling / Security / Release / Breaking
- Risk: Low / Moderate / High / Critical
- Risk rationale: Briefly explain why the selected level is appropriate, considering data sensitivity, privilege, blast radius, reversibility, external exposure, availability, and safety as applicable.
- Release impact: None / Patch / Minor / Major / Prerelease

A change classified as **Breaking** requires independent specialist review under `MAINTAINERS.md`, including during the pre-1.0 period.

For **High** or **Critical** risk changes, complete these additional control-evidence fields:

- Threat analysis: Link or concise summary / Not applicable for Low or Moderate
- Rollback plan: Link or concise summary / Not applicable for Low or Moderate
- Explicit approval: Reviewer/approver and link to approval record / Pending

## Ownership and review routing

- Applicable CODEOWNER:
- Area owner:
- Specialist review: Not needed / Recommended / Independently required

## Impact

- Compatibility:
- Security:
- Affected packages, schemas, tools, or stable paths:
- Changelog impact: None / Unreleased updated / Target release updated
- Release-note impact: None / Required / Updated
- Deprecation impact: None / Required / Updated
- Migration impact: None / Required / Updated

## Validation performed

List the exact validation commands or hosted checks that actually ran and their outcomes.

## Validation not performed

List relevant checks that were not run and why. Use `NotRun` or `Blocked` rather than implying success.

## Limitations and follow-up

Record remaining assumptions, limitations, or follow-up work. Use `None` when there are no known items.

## Maintainer review

For low- or moderate-risk changes that do not require independent specialist review, the active maintainer may record a self-review here after permanent CI passes.
