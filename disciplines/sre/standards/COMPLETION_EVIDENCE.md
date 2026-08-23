---
id: DISC-SRE-COMPLETION-EVIDENCE
title: SRE Completion Evidence
version: 0.1.0
status: baseline
---
# SRE Completion Evidence

## Purpose

This standard defines detailed requirements for one part of the **Site Reliability Engineering** discipline:

> Record objectives, capacity results, resilience tests, runbooks, incident actions, change controls, limitations, and residual risks.

## Required behavior

- Record objectives, capacity results, resilience tests, runbooks, incident actions, change controls, limitations, and residual risks.
- Define scope, ownership, inputs, outputs, assumptions, dependencies, and supported operating conditions.
- Use explicit, reviewable configuration and documented defaults rather than hidden environment assumptions.
- Apply controls proportionate to change risk, data sensitivity, trust boundaries, reversibility, and operational impact.
- Define positive behavior, negative behavior, boundary conditions, partial failure, recovery, and safe stopping conditions.
- Keep implementation, configuration, examples, and evidence free of credentials, internal production identifiers, and sensitive data.
- Preserve existing contracts unless an authorized change includes compatibility, migration, and communication work.
- Record exceptions through the repository exception process instead of weakening the standard silently.

## Required evidence

Evidence should be concrete and reproducible. Depending on scope, include:

- design, configuration, contract, diagram, or decision records
- implementation or review evidence tied to the requirement
- positive, negative, boundary, and failure-path tests
- operational, data-migration, security, privacy, compatibility, or recovery evidence
- commands run, environments used, results, and checks not run
- known limitations, assumptions, unresolved risks, owners, and follow-up work

## Review questions

- Is this standard applicable to the change, and is the chosen scope documented?
- Are ownership and trust boundaries explicit?
- Are unsafe defaults, ambiguity, and hidden coupling avoided?
- Are failure, retry, rollback, recovery, and partial-success behaviors defined where relevant?
- Does the evidence prove the claim rather than merely describe intent?
- Are exceptions approved, time-bounded, and visible?

## Completion gate

Do not report this area complete until the applicable requirements are implemented, evidence is recorded, unsupported claims are removed, and remaining risk is stated plainly.
