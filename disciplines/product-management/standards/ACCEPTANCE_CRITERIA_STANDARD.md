---
id: DISC-PROD-ACCEPTANCE-CRITERIA-STANDARD
title: Acceptance Criteria Standard
version: 0.1.0
status: baseline
---

# Acceptance Criteria Standard

## Purpose

Define observable evidence for accepting or rejecting a requirement.

## Required behavior

- Map criteria to stable requirement identifiers and state expected behavior, conditions, boundaries, and failure behavior.
- Make criteria measurable and technology-neutral unless a reviewed constraint requires a technology.
- Include applicable nonfunctional, security, privacy, accessibility, performance, reliability, and recovery outcomes.
- Identify validation method, environment, evidence owner, and acceptable limitations without inventing thresholds.
- Record a separate acceptance result of `Pass`, `Fail`, `Blocked`, `NotRun`, or justified `NotApplicable` for every criterion; an execution or evidence state such as `Tested` or `Reviewed` is not an acceptance result.
- Use `Pass` only when current primary evidence for the exact reviewed artifact and conditions satisfies the criterion; stale, different-artifact, failing, missing, blocked, or not-run evidence cannot support acceptance.

## Required evidence

Requirement-to-criteria mapping, review record, validation strategy, exact artifact and conditions, per-criterion acceptance result, primary test or operational evidence, limitations, and owner.

## Completion gate

Do not accept a requirement from implementation presence, author assertion, or execution state. Every applicable criterion must have a current explicit `Pass` for the exact reviewed artifact and conditions; any `Fail`, `Blocked`, `NotRun`, or missing result prevents acceptance, and `NotApplicable` requires reviewed justification.
