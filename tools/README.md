---
id: TOOL-INDEX-001
title: Repository Toolchain
version: 1.3.0
status: baseline
---

# Repository Toolchain

## Purpose

The repository toolchain makes standards, schemas, templates, manifests, composition decisions, source-maintenance state, and repository releases executable and reviewable.

It provides:

- repository structure validation
- Markdown link and anchor validation
- authoritative-source review-date freshness checking
- skill entry-point and package-routing validation
- JSON Schema validation
- template package validation
- tool package validation
- release-policy and tag validation
- project manifest generation
- traceable agent-standards composition
- deterministic release artifact generation
- a unified validation runner

The tools are deliberately conservative. They validate implemented contracts and produce traceable plans, files, artifacts, or maintenance state. They do not grant authorization, prove evidence is truthful, certify compliance, verify live vendor content unless explicitly designed to do so, or decide that a system is production-ready. Humans remain annoyingly involved in all the consequential parts.

## Tool catalog

| Tool | Entry point | Mode | Primary responsibility |
|---|---|---|---|
| [Validate Standards](validate-standards/) | `validate_repository.py` | read-only | Validate root files, licensing, ownership, JSON parsing, unique IDs, AGENTS depth, and final-branch hygiene. |
| [Check Links](check-links/) | `check_links.py` | read-only | Validate relative Markdown targets and local heading anchors without network access. |
| [Check Freshness](check-freshness/) | `check_freshness.py` | read-only | Validate authoritative-source review metadata and report recorded review-date state as Passed, Warning, or NotRun without live network access. |
| [Validate Skills](validate-skills/) | `validate_skills.py` | read-only | Validate skill metadata, progressive disclosure, package routing, registration, local links, and optional UI metadata. |
| [Validate Schemas](validate-schemas/) | `validate_schemas.py` | read-only | Validate Draft 2020-12 contracts, examples, versioned equivalence, and repository instances. |
| [Validate Templates](validate-templates/) | `validate_templates.py` | read-only | Validate template packages, placeholders, examples, stable paths, and schema-backed JSON. |
| [Validate Tools](validate-tools/) | `validate_tools.py` | read-only | Validate tool package structure, executable entry points, contracts, documentation, workflows, and tests. |
| [Validate Release](release/) | `validate_release.py` | read-only | Validate VERSION, changelog, release notes, migration notes, release policy, maturity policy, workflow, publication state, and tag matching. |
| [Build Release](release/) | `build_release.py` | writes output | Build deterministic archives, SHA-256 checksums, release notes, migration notes, and a release manifest. |
| [Generate Manifest](generate-manifest/) | `generate_manifest.py` | writes output | Produce a schema-valid project manifest from explicit profile, language, discipline, framework, platform, virtualization, operating-system, and networking selections. |
| [Compose Agents](compose-agents/) | `compose_agents.py` | writes output | Create a traceable standards bundle, including repository-defined governance selections and selected virtualization, operating-system, and networking packages, without flattening or rewriting source standards. |
| [Validate All](validate-all/) | `run_all.py` | read-only | Run and aggregate the complete validation pipeline. |

See [`TOOL_CATALOG.md`](TOOL_CATALOG.md) for inputs, outputs, dependencies, and ownership.

## Quick start

Install the hash-locked validation dependencies:

```bash
python -m pip install --require-hashes -r tools/validate-schemas/requirements.lock
```

Run the complete validation pipeline:

```bash
python tools/validate-all/run_all.py --include-tests
```

Run one validator:

```bash
python tools/check-links/check_links.py
```

Check recorded source-review freshness:

```bash
python tools/check-freshness/check_freshness.py
```

Validate the release program:

```bash
python tools/release/validate_release.py
```

Build release artifacts only for the deliberately prepared current version:

```bash
python tools/release/build_release.py \
  --tag v<VERSION> \
  --output-dir dist
```

Generate a project manifest safely:

```bash
python tools/generate-manifest/generate_manifest.py \
  --name example-service \
  --profile WEB_API \
  --language python \
  --operating-system ubuntu \
  --include-profile-required \
  --risk moderate \
  --dry-run
```

Compose a traceable bundle after reviewing the manifest:

```bash
python tools/compose-agents/compose_agents.py \
  --manifest project-manifest.json \
  --output-dir generated/standards-bundle \
  --dry-run
```

Remove `--dry-run` only after reviewing planned output. Generation tools refuse to overwrite existing output unless `--force` is explicit. The release builder refuses to replace an existing distribution directory without `--force` and respects the machine-readable publication boundary.

## Common command-line contract

Shared validators and generators support:

- `--root PATH`
- `--format text|json`
- `--output PATH`
- `--quiet`
- `--help`

The release builder uses a narrower artifact-generation interface documented in [`release/README.md`](release/README.md).

Tool-specific options are documented in each package README.

See [`TOOL_CONTRACT.md`](TOOL_CONTRACT.md).

## Exit codes

Shared tools use:

- `0`: tool completed with no error-severity findings
- `1`: tool completed and found validation failures
- `2`: invalid input, missing configuration, or dependency problem
- `3`: unexpected internal failure

The release builder uses `0` for success and `2` for invalid release input or build state.

A nonzero exit code must not be converted to success by a wrapper unless the wrapper explicitly records and reports the failure.

## Structured output

JSON output from shared tools conforms to [`contracts/tool-result.schema.json`](contracts/tool-result.schema.json).

A result contains:

- tool name and version
- `passed`, `failed`, or `error` shared status
- summary counters
- structured findings
- tool-specific metadata

`passed` means only that the tool's implemented error-severity checks passed against the supplied input.

Some maintenance tools expose a more specific human-facing state in summary fields. For `check-freshness`, inspect `summary.freshnessState` rather than assuming shared `status: passed` means every source review is current.

The release builder emits a release manifest describing the source commit and artifact digests.

## Source freshness model

Time-sensitive source-review metadata lives in [`../SOURCE_REVIEWS.json`](../SOURCE_REVIEWS.json).

The freshness checker evaluates recorded review dates without network access. It distinguishes:

- `Passed`: recorded reviews are inside their configured interval
- `Warning`: one or more recorded reviews are stale
- `NotRun`: one or more source reviews have no recorded date
- invalid metadata: shared tool failure

Live source verification remains `NotRun` for the offline checker. A recent repository edit or merge is not accepted as a source-review date.

The scheduled/manual workflow under `.github/workflows/source-freshness.yml` surfaces maintenance warnings. Manual strict mode can turn stale or not-run review state into a blocking failure.

## Safety model

Read-only validators:

- do not modify repository content
- do not require network access unless a tool explicitly documents otherwise
- report all identified failures unless fail-fast behavior is explicitly selected

Writing tools:

- require explicit output paths
- support dry-run where planning is meaningful
- refuse overwrite without `--force`
- validate inputs before writing
- write deterministically
- use atomic staging where multiple files are produced
- stay within the declared repository root unless an explicit absolute output is supplied

Release tooling additionally:

- packages Git-tracked files only
- validates the tag against `VERSION`
- honors machine-readable blocked publication states
- normalizes archive metadata
- emits SHA-256 checksums
- does not create or push tags
- does not publish releases outside the tag-triggered GitHub workflow

See [`SECURITY_BOUNDARIES.md`](SECURITY_BOUNDARIES.md).

## Development workflow

1. Read `tools/AGENTS.md` and the package README.
2. Identify callers and stable paths.
3. Define compatibility and release impact.
4. Implement the smallest coherent change.
5. Add positive, negative, warning, not-run, and error-path tests as applicable.
6. Run the affected tool directly.
7. Run all unit tests.
8. Run `validate-all`.
9. Review text and JSON output.
10. Update documentation, examples, changelog, release notes, migration notes, source metadata, and workflows as applicable.

See [`DEVELOPMENT_GUIDE.md`](DEVELOPMENT_GUIDE.md) and [`TESTING_GUIDE.md`](TESTING_GUIDE.md).

## Validation pipeline

Permanent CI runs:

```bash
python tools/validate-all/run_all.py --include-tests
```

The runner executes validators in this order:

1. repository structure
2. Markdown links and anchors
3. source-review freshness metadata
4. skill entry points and package routes
5. schemas and instances
6. templates
7. tools and workflow hygiene
8. release program
9. unit tests

Order matters because later validators rely on contracts established by earlier ones.

The freshness validator remains offline and warning-oriented by default. Its inclusion in permanent CI makes missing or stale source-review state visible without converting ordinary maintenance due dates into fabricated validation failures.

## Scheduled maintenance pipeline

`.github/workflows/source-freshness.yml` runs the source freshness checker weekly and through manual dispatch.

The workflow uses immutable action references, an explicit Ubuntu 24.04 runner, and Python 3.13.

It writes a GitHub Actions step summary and warning annotations. It does not fetch vendor pages, create issues automatically, or claim live source verification.

A maintainer may manually request strict mode when a blocking source-review gate is appropriate.

## Release pipeline

Pushing an allowed `v*` tag starts `.github/workflows/release.yml`.

The workflow:

1. verifies the tagged commit is on `main`
2. runs the complete validation pipeline
3. verifies the tag matches `VERSION` and is publishable
4. builds deterministic ZIP and TAR.GZ archives
5. verifies SHA-256 checksums
6. creates the GitHub Release
7. attaches archives, checksums, release manifest, and migration notes

Tag creation and release publication remain subject to `MAINTAINERS.md`, `RELEASE_POLICY.md`, and machine-readable release-state controls.

## Compatibility

Stable executable paths are public repository interfaces.

Breaking changes include:

- moving or renaming an entry point
- changing exit-code meaning
- removing JSON fields
- changing a writing tool's overwrite behavior
- narrowing accepted input without migration
- changing generated file semantics
- changing release artifact names, archive roots, checksum format, or tag interpretation
- silently treating `NotRun` source review as current review
- silently adding live network access to an offline validator

See [`RELEASE_AND_COMPATIBILITY.md`](RELEASE_AND_COMPATIBILITY.md) and [`../RELEASE_POLICY.md`](../RELEASE_POLICY.md).

## Troubleshooting

Common failures and maintenance states include:

- missing `jsonschema` dependency
- running from an incomplete checkout
- stale placeholders in completed examples
- broken relative links or anchors
- stale source-review dates
- source reviews explicitly marked `NotRun`
- malformed source-review metadata
- unknown profile or package selections
- output already existing without `--force`
- a bundle source missing from the selected package
- a tag that does not match `VERSION`
- a version blocked from publication
- missing release or migration notes
- a tagged commit that is not on `main`
- checksum verification failure

See [`TROUBLESHOOTING.md`](TROUBLESHOOTING.md).

## Completion boundary

A green toolchain proves that the repository satisfied the implemented automated error-severity checks at that revision. It does not prove every standard is correct, every authoritative source is current, every package is stable, every approval is authoritative, every release note is complete, or every production risk is controlled.
