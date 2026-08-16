---
id: MATURITY-REVIEW-INDEX-001
title: Maturity Review Records
version: 0.9.0
status: baseline
---

# Maturity Review Records

## Purpose

This directory stores evidence-backed decisions that promote, defer, reject, demote, or deprecate repository components.

Requirements are defined by [`../MATURITY_POLICY.md`](../MATURITY_POLICY.md).

## Required structure

```text
maturity-reviews/
├── README.md
├── TEMPLATE.md
└── examples/
    └── BASELINE_TO_STABLE_EXAMPLE.md
```

Completed review records should use a stable filename such as:

```text
<component-id>-<from>-to-<to>-<yyyy-mm-dd>.md
```

## Completed decisions

- [`csharp-baseline-to-stable-2026-08-16.md`](csharp-baseline-to-stable-2026-08-16.md) — `approved`, subject to the policy-required independent specialist approval before the promotion PR merges.
- [`powershell-baseline-to-stable-2026-08-16.md`](powershell-baseline-to-stable-2026-08-16.md) — `deferred` pending current-revision runtime and behavioral adoption evidence.
- [`terraform-opentofu-baseline-to-stable-2026-08-16.md`](terraform-opentofu-baseline-to-stable-2026-08-16.md) — `deferred` because the required representative downstream adoptions do not yet exist.

## Decision boundary

A maturity review records repository confidence in a component. It does not certify an adopting project, guarantee future compatibility beyond the release policy, or replace specialist review.
