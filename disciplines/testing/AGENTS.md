---
id: DISC-TEST
title: Testing and Quality Engineering Agent Standard
version: 0.2.0
status: baseline
applies_to:
  - testing
depends_on:
  - GOV-WORK
  - GOV-RISK
  - GOV-EVIDENCE
---

# Testing and Quality Engineering Agent Standard

## Purpose

This file defines mandatory agent behavior for work governed by the **Testing and Quality Engineering** discipline.

Its objective is to produce meaningful evidence that behavior, failure handling, security, compatibility, and operational expectations are satisfied.

> Make the smallest safe, reviewable, testable, and evidence-backed change that satisfies the requirement.

## Scope

This discipline applies to:

- test strategy and risk coverage
- unit and component tests
- integration and contract tests
- end-to-end and acceptance tests
- nonfunctional tests
- test data and environments
- defect regression

## Instruction priority

When instructions conflict, apply them in this order:

1. explicit user requirements
2. the nearest more-specific `AGENTS.md`
3. this discipline `AGENTS.md`
4. the supporting standards in this package
5. repository conventions
6. general agent preferences

Do not resolve a material conflict silently. Follow the higher-priority instruction and report the conflict.

## Required supporting standards

Read every applicable supporting standard before implementation:

- [`standards/TEST_STRATEGY_STANDARD.md`](standards/TEST_STRATEGY_STANDARD.md)
- [`standards/UNIT_COMPONENT_STANDARD.md`](standards/UNIT_COMPONENT_STANDARD.md)
- [`standards/INTEGRATION_CONTRACT_STANDARD.md`](standards/INTEGRATION_CONTRACT_STANDARD.md)
- [`standards/END_TO_END_STANDARD.md`](standards/END_TO_END_STANDARD.md)
- [`standards/NONFUNCTIONAL_TESTING_STANDARD.md`](standards/NONFUNCTIONAL_TESTING_STANDARD.md)
- [`standards/TEST_DATA_ENVIRONMENT_STANDARD.md`](standards/TEST_DATA_ENVIRONMENT_STANDARD.md)
- [`standards/DEFECT_REGRESSION_STANDARD.md`](standards/DEFECT_REGRESSION_STANDARD.md)
- [`standards/COMPLETION_EVIDENCE.md`](standards/COMPLETION_EVIDENCE.md)

The supporting standards extend this file. This `AGENTS.md` takes precedence if wording conflicts.

## Mandatory rules

### TEST-STRATEGY-001

**Requirement:** Define the test levels required by risk: unit, component, integration, contract, end-to-end, security, performance, and recovery.

**Evidence:** Test strategy mapped to risk.

### TEST-NEGATIVE-002

**Requirement:** Test invalid, unauthorized, boundary, timeout, and failure behavior.

**Evidence:** Negative test results.

### TEST-ISOLATION-003

**Requirement:** Keep tests deterministic, independently runnable, and isolated from uncontrolled external state.

**Evidence:** Repeatable test execution.

### TEST-REGRESSION-004

**Requirement:** Add regression tests for fixed defects where practical.

**Evidence:** Fail-before/pass-after evidence.

### TEST-QUALITY-005

**Requirement:** Do not weaken assertions or skip tests to make a pipeline pass.

**Evidence:** Diff and test review.

### TEST-PERFORMANCE-006

**Requirement:** Record performance-test execution state separately from outcome, and report performance or scalability validated only when every applicable test type has a current explicit `Pass` against its authorized acceptance criteria for the exact artifact and representative conditions.

**Evidence:** Per-test matrix records applicability, execution state, outcome, criteria, exact artifact and environment, primary evidence, owner, authorization, safeguards, and stop conditions.

## Non-negotiable behavior

- Inspect existing code, configuration, contracts, tests, documentation, ownership, and operational context before changing anything.
- Do not invent production values, identities, endpoints, schemas, credentials, infrastructure, legal obligations, or compatibility promises.
- Classify risk and identify trust boundaries, sensitive data, state changes, and reversibility.
- Default to safe, narrow, reversible behavior and stop when prerequisites or target identity are ambiguous.
- Do not weaken tests, security, privacy, accessibility, approvals, or evidence requirements to make work appear complete.
- Preserve public behavior unless change is explicitly authorized and migration or compatibility work is included.
- Keep examples fictitious and keep secrets and sensitive data out of source, tests, logs, errors, artifacts, and documentation.
- Record exact commands, results, limitations, assumptions, exceptions, and remaining risk.

## Required working method

1. Determine whether this discipline applies and document the reason.
2. Inspect the current implementation, contracts, evidence, and ownership.
3. Identify risk, trust boundaries, dependencies, failure modes, and affected users or operators.
4. Define acceptance criteria and required evidence before implementation.
5. Make the smallest coherent change.
6. Add or update tests, documentation, runbooks, contracts, diagrams, and evidence as applicable.
7. Run package-specific validation and review the final diff for unrelated or unsafe changes.
8. Report what changed, what was verified, what was not verified, and what risk remains.

## Completion gate

Do not report this discipline complete until:

- applicable mandatory rules are satisfied
- supporting standards were considered
- required evidence is recorded
- checks not run are identified
- limitations, assumptions, exceptions, and remaining risks are stated
