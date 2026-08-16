---
id: TOOL-PKG-CHECK-FRESHNESS-001
title: Check Freshness Tool
version: 1.0.0
status: baseline
---

# Check Freshness Tool

## Purpose

`check-freshness` evaluates the repository's recorded authoritative-source review dates without performing live network requests.

It exists to make time-sensitive maintenance visible without turning every pull request into an unreliable internet availability test.

The tool reads [`../../SOURCE_REVIEWS.json`](../../SOURCE_REVIEWS.json), validates its structure, evaluates source-review age, and reports whether source review is current, stale, or not yet recorded.

## Stable entry point

```text
tools/check-freshness/check_freshness.py
```

Moving or renaming this entry point requires migration guidance and release classification under [`../../RELEASE_POLICY.md`](../../RELEASE_POLICY.md).

## Operating model

The checker is intentionally offline.

It does not:

- fetch vendor documentation
- scrape lifecycle pages
- infer current product support from cached repository text
- treat DNS or network availability as evidence
- promote package maturity
- certify vendor compatibility

Live external-source verification is reported as `NotRun` unless a separate accountable review is performed and recorded.

## Source-review registry

The canonical metadata file is:

```text
SOURCE_REVIEWS.json
```

Each record identifies:

- a stable record ID
- repository scope
- optional package maturity
- accountable owner
- review interval in days
- last authoritative-source review date, or `null`
- one or more named authoritative HTTPS sources
- optional notes

A repository modification date is not a substitute for `lastReviewed`.

Do not populate a review date merely because a document was edited, merged, or reformatted.

## Freshness states

The human-facing freshness state is separate from the shared tool execution status.

### Passed

`Passed` means every evaluated record has a recorded source-review date and that date is within its configured review interval.

It does not mean the external sources were fetched during this execution.

### Warning

`Warning` means at least one recorded review date is older than its configured review interval.

By default, stale records produce warning findings and exit code `0` so the scheduled maintenance workflow can surface maintenance work without turning ordinary repository validation red.

Use `--strict` when stale review state must be enforced as a blocking condition.

### NotRun

`NotRun` means at least one record has no accountable source-review date.

This is an explicit state, not success.

The initial registry may legitimately contain `null` review dates until maintainers perform and record source-currency reviews.

### Invalid

`Invalid` means the registry contains structural or semantic errors such as duplicate IDs, invalid dates, missing scopes, invalid maturity values, unsafe paths, or malformed source URLs.

Invalid metadata is a tool failure.

## Shared tool status

The shared result contract still uses:

- `passed`
- `failed`
- `error`

Warning findings do not change shared status from `passed` unless `--strict` is supplied.

Consumers that care about maintenance state should inspect:

```text
summary.freshnessState
```

Do not infer source currency from the shared `status` field alone.

## Network state

Every normal execution reports:

```text
summary.liveSourceVerification = "NotRun"
```

This prevents offline execution from being misrepresented as live verification.

The tool does not silently convert network absence into success because it does not attempt network access at all.

## Default review intervals

The registry defines a default review interval and may override it per record.

Shorter intervals are appropriate for:

- operating-system lifecycle claims
- virtualization compatibility
- network firmware and controller support
- cloud or provider behavior
- security-sensitive current-version statements

Longer intervals may be appropriate for slower-moving foundational standards.

Review cadence must remain consistent with [`../../MATURITY_POLICY.md`](../../MATURITY_POLICY.md).

## Run the checker

```bash
python tools/check-freshness/check_freshness.py
```

JSON output:

```bash
python tools/check-freshness/check_freshness.py --format json
```

Write a JSON report:

```bash
python tools/check-freshness/check_freshness.py \
  --format json \
  --output source-freshness-result.json \
  --quiet
```

## Deterministic evaluation date

For testing or reproducible maintenance review, supply an explicit date:

```bash
python tools/check-freshness/check_freshness.py \
  --as-of 2026-12-31 \
  --format json
```

`--as-of` must use `YYYY-MM-DD`.

## Strict mode

Strict mode converts stale and not-run source-review findings from warnings to errors:

```bash
python tools/check-freshness/check_freshness.py --strict
```

Use strict mode deliberately.

The permanent pull-request pipeline uses the default non-strict mode so missing source review creates visible maintenance state without claiming external facts were verified.

## Registry validation

The checker rejects:

- missing or empty records
- duplicate record IDs
- absolute scopes
- scopes that escape the repository root
- scopes that do not exist
- unsupported maturity values
- invalid review intervals
- malformed review dates
- review dates in the future
- missing authoritative sources
- non-HTTPS authoritative-source URLs

## Findings

Stable finding codes include:

- `SOURCE_REVIEW_NOT_RUN`
- `SOURCE_REVIEW_STALE`
- `SOURCE_REVIEW_DATE_INVALID`
- `SOURCE_REVIEW_DATE_FUTURE`
- `SOURCE_REVIEW_SCOPE_INVALID`
- `SOURCE_REVIEW_SCOPE_ESCAPES_ROOT`
- `SOURCE_REVIEW_SCOPE_MISSING`
- `SOURCE_REVIEW_ID_INVALID`
- `SOURCE_REVIEW_ID_DUPLICATE`
- `SOURCE_REVIEW_INTERVAL_INVALID`
- `SOURCE_REVIEW_MATURITY_INVALID`
- `SOURCE_REVIEW_AUTHORITATIVE_SOURCE_MISSING`
- `SOURCE_REVIEW_AUTHORITATIVE_SOURCE_INVALID`
- `SOURCE_REVIEW_RECORD_INVALID`
- `SOURCE_REVIEW_RECORDS_MISSING`

Finding wording may improve while codes retain their meaning.

## Scheduled workflow

The repository workflow under:

```text
.github/workflows/source-freshness.yml
```

runs on a schedule and through manual dispatch.

The workflow:

1. checks out the repository with immutable action pins
2. sets up the pinned Python boundary
3. runs the offline freshness checker
4. writes a GitHub Actions step summary
5. emits warning annotations for stale or not-run records
6. preserves a blocking failure when strict mode is manually requested

The scheduled workflow does not fetch external vendor content.

## Why the scheduled job can remain green with warnings

A stale review date is maintenance work, not proof that repository content is wrong.

The maturity policy explicitly says a passed review date creates a visible maintenance item and blocks unsupported claims of current review; it does not automatically invalidate the component.

The warning state reflects that distinction.

## Updating a review record

Before changing `lastReviewed`:

1. inspect the declared authoritative sources
2. verify the repository claims affected by those sources
3. record material changes separately if repository content must change
4. update `lastReviewed` only after the review actually occurred
5. keep the source list current
6. preserve limitations when verification was incomplete
7. run the freshness checker
8. run the complete repository validation pipeline

Do not backdate reviews or infer them from commit timestamps.

## Adding a source-review scope

Add a registry record when a repository area contains material time-sensitive claims.

Prefer a collection-level scope when one accountable review can reasonably cover the collection.

Split records when different owners, source sets, or review cadences are needed.

Avoid creating one record per URL merely to generate paperwork.

## Issue reporting

Use the repository's source-freshness issue form for:

- stale vendor references
- lifecycle corrections
- compatibility changes
- moved authoritative documentation
- unsupported current-version claims
- missing source-review metadata

Do not include credentials, private support data, or sensitive customer evidence.

## Exit codes

Normal shared tool behavior applies:

- `0`: completed with no error-severity findings
- `1`: completed with error-severity findings, including strict stale/not-run findings
- `2`: invalid input or missing registry
- `3`: unexpected internal failure

## Tests

Focused tests live in:

```text
tools/tests/test_check_freshness.py
```

Run them with:

```bash
python -m unittest discover -s tools/tests -p "test_check_freshness.py"
```

Run the complete pipeline with:

```bash
python tools/validate-all/run_all.py --include-tests
```

## Compatibility

The initial `1.0.0` tool contract is additive repository tooling.

Backward-compatible changes may add optional registry fields, summary metadata, or finding details.

Breaking changes include:

- changing the stable entry path
- changing the meaning of `Passed`, `Warning`, or `NotRun`
- changing shared exit-code meaning
- silently treating missing review dates as success
- silently adding live network access to default execution
- removing recorded authoritative-source metadata

## Security and privacy

The registry must contain public source metadata only.

Do not store:

- credentials
- support portal tokens
- customer identifiers
- private vulnerability reports
- non-public vendor documents
- internal infrastructure details

## Limitations

- review-date freshness does not prove source content is still unchanged
- an HTTPS URL does not prove the source is authoritative
- the tool does not fetch or compare external content
- a recent review date can still be wrong if the review was incomplete
- warning-free output does not certify package maturity or compatibility
- the scheduled job cannot replace accountable technical review

## Maintenance

Update the executable, README, manifest, examples, catalog, aggregate validator, tests, workflow, and source metadata together when behavior changes.

## Completion boundary

A successful execution proves only that the recorded metadata was structurally valid and evaluated against the configured review intervals.

It does not prove external source currency, vendor support, security posture, interoperability, or production readiness.
