---
id: SOURCE-REVIEWS-INDEX-001
title: Source Review Records
version: 1.0.0
status: baseline
---

# Source Review Records

This directory contains durable records for authoritative-source reviews referenced by [`../SOURCE_REVIEWS.json`](../SOURCE_REVIEWS.json).

A source review establishes only what public authoritative material was inspected on the recorded date and which repository claims required correction. It does not establish vendor certification, support entitlement, environment compatibility, successful deployment, or live integration testing.

## Current records

- [`2026-08-15.md`](2026-08-15.md) — first package-level source-currency review supporting the `0.10.0` release program

## Recording rules

- Record only sources actually reviewed.
- Use `NotRun` or `Blocked` when a required source could not be reviewed.
- Do not substitute commit dates, file modification dates, or successful URL resolution for semantic source review.
- Identify material lifecycle, release, naming, support, security, compatibility, or migration findings.
- Correct repository content in a focused change when current authoritative sources contradict it.
- Keep entitlement-only, portal-only, and environment-specific compatibility limitations explicit.
- Link reviewed records from `SOURCE_REVIEWS.json` using `reviewEvidence`.
- Re-run the offline freshness checker and complete repository validation after metadata changes.

## Validation

```bash
python tools/check-freshness/check_freshness.py
python tools/validate-all/run_all.py --include-tests
```
