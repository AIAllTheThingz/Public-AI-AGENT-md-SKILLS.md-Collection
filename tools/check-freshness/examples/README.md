---
id: TOOL-PKG-CHECK-FRESHNESS-001-EXAMPLES
title: Check Freshness Examples
version: 1.0.0
status: baseline
---

# Check Freshness Examples

## Purpose

These examples show how to interpret source-review freshness without implying live external verification.

## Normal repository check

```bash
python tools/check-freshness/check_freshness.py --format json
```

If all recorded review dates are current, the result includes:

```json
{
  "status": "passed",
  "summary": {
    "freshnessState": "Passed",
    "liveSourceVerification": "NotRun"
  }
}
```

`Passed` refers only to recorded review dates and registry structure.

## Not-run review state

A record with:

```json
{
  "lastReviewed": null
}
```

produces a `SOURCE_REVIEW_NOT_RUN` warning and contributes to:

```text
freshnessState: NotRun
```

The shared tool status remains `passed` in non-strict mode because the record is a visible maintenance condition rather than a structural validation error.

## Stale review state

For a record reviewed on `2026-01-01` with a 90-day interval, evaluating on `2026-07-01` produces:

```text
freshnessState: Warning
```

and a `SOURCE_REVIEW_STALE` finding.

Use a deterministic evaluation date when reproducing maintenance results:

```bash
python tools/check-freshness/check_freshness.py \
  --as-of 2026-07-01 \
  --format json
```

## Strict maintenance gate

```bash
python tools/check-freshness/check_freshness.py \
  --strict \
  --as-of 2026-07-01
```

Strict mode returns a nonzero validation result when any source review is stale or not recorded.

## Updating metadata

After an accountable source review, update only the record that was actually reviewed:

```json
{
  "id": "networking",
  "lastReviewed": "2026-08-15",
  "reviewIntervalDays": 90
}
```

Do not copy that date into unrelated records.

## Network boundary

The checker does not fetch any URL in `authoritativeSources`.

A recent review date means a maintainer recorded a completed review. It does not mean this invocation repeated that review.

`liveSourceVerification` therefore remains `NotRun`.
