---
id: TOOL-PKG-RELEASE-001
title: Repository Release Tool
version: 1.0.0
status: baseline
---

# Repository Release Tool

## Purpose

The release package validates repository release contracts and builds deterministic release artifacts.

The project/library name is **Public Access Agents**. The canonical GitHub repository is **`AIAllTheThingz/Public-AI-Governance`**. Generated source archives intentionally retain the `Public-Access-Agents-<VERSION>` prefix as the stable project artifact name.

It contains two executable entry points:

- [`validate_release.py`](validate_release.py)
- [`build_release.py`](build_release.py)

The release validator is part of the permanent read-only validation pipeline. The release builder writes artifacts only to an explicit output directory.

## Current publication boundary

The prepared `0.9.0` release program was never published. There is no `v0.9.0` tag and no `0.9.0` GitHub Release. Do not use the examples in this document to retroactively tag current `main` as `v0.9.0`.

This boundary is executable, not advisory. [`../../releases/release-state.json`](../../releases/release-state.json) records `0.9.0` under `preparedUnpublishedVersions`. A tag-validation invocation for an explicitly unpublished version returns `RELEASE_PUBLICATION_BLOCKED`, and the release builder refuses to construct publication artifacts for that version. The tag-driven workflow validates before building and publishing, so `v0.9.0` cannot reach `gh release create` from the current repository state.

The next intended publication is `0.10.0` after the repository `VERSION`, changelog entry, release notes, migration notes, and validation evidence have been deliberately prepared for that version. The issue #40 release-candidate source deliberately sets `VERSION` to `0.10.0`; tag creation and GitHub Release publication remain separate authorized actions.

## Stable entry points

```text
tools/release/validate_release.py
tools/release/build_release.py
```

Moving or renaming these files requires migration guidance, tool-catalog updates, workflow updates, and compatibility review.

## Inputs

The tools read:

- `VERSION`
- `CHANGELOG.md`
- `RELEASE_POLICY.md`
- `MATURITY_POLICY.md`
- `releases/release-state.json` when present
- `releases/<VERSION>.md`
- `releases/migrations/<VERSION>.md`
- `.github/workflows/release.yml`
- Git-tracked repository files
- Git commit and tag metadata

`releases/release-state.json` may identify versions that were prepared but deliberately never published. A malformed state file is a validation/build error. The repository regression suite requires the current unpublished-baseline record to remain present.

## Validate a release program

```bash
python tools/release/validate_release.py
```

Validate the proposed tag that matches the deliberately prepared `VERSION`:

```bash
python tools/release/validate_release.py --tag v<VERSION>
```

Require the current commit to carry the matching tag:

```bash
python tools/release/validate_release.py \
  --tag v<VERSION> \
  --require-head-tag
```

Do not substitute a historical prepared version merely because release notes exist for it. Confirm the intended publication version, machine-readable release state, and actual GitHub tag state first.

## Build release artifacts

```bash
python tools/release/build_release.py \
  --tag v<VERSION> \
  --output-dir dist
```

The builder refuses to construct artifacts when the canonical `VERSION` is listed under `preparedUnpublishedVersions`. It also refuses to replace an existing output directory unless `--force` is supplied:

```bash
python tools/release/build_release.py \
  --tag v<VERSION> \
  --output-dir dist \
  --force
```

## Generated files

The output directory contains:

```text
Public-Access-Agents-<VERSION>.zip
Public-Access-Agents-<VERSION>.tar.gz
SHA256SUMS.txt
release-manifest.json
RELEASE_NOTES.md
MIGRATION_NOTES.md
```

The archive prefix is the project artifact identity and is intentionally distinct from the GitHub repository slug.

## Determinism

Archives are generated from Git-tracked files in sorted path order.

The builder normalizes:

- ZIP timestamps
- TAR timestamps
- archive ownership metadata
- archive root names
- file ordering
- checksum ordering

The same source commit and tool version should produce identical archive contents. Compression-library or platform differences must be investigated before claiming byte-for-byte reproducibility across environments.

## Checksums

`SHA256SUMS.txt` contains SHA-256 digests for the ZIP and TAR.GZ archives.

Verify locally:

```bash
cd dist
sha256sum -c SHA256SUMS.txt
```

Checksums establish artifact integrity relative to the published digest. They do not establish that the repository content is correct or safe.

## Release manifest

`release-manifest.json` records:

- format version
- repository version
- tag
- source commit
- archive root
- tracked-file count
- artifact names
- artifact sizes
- artifact SHA-256 digests
- release-note filename
- migration-note filename
- checksum filename

## Exit behavior

`validate_release.py` follows the shared tool contract:

- `0`: validation passed
- `1`: validation completed with findings, including `RELEASE_PUBLICATION_BLOCKED`
- `2`: invalid input or missing dependency
- `3`: unexpected internal failure

`build_release.py` returns:

- `0`: artifacts built successfully
- `2`: invalid version, blocked publication version, tag, source, output, or Git state

## Safety boundaries

- The validator is read-only except for an optional report file supplied through the shared tool contract.
- The builder writes only beneath the selected output directory.
- Explicitly unpublished prepared versions are rejected before publication artifacts are built.
- Existing output is not replaced without `--force`.
- Release archives contain Git-tracked files only.
- The tool performs no network access.
- The tool does not create or push tags.
- The tool does not publish GitHub Releases.
- The tool does not grant release authority.

## Tag boundary

The canonical tag is:

```text
v<VERSION>
```

A supplied tag that does not match `VERSION` is rejected. A matching tag is also rejected when the version is explicitly listed as prepared/unpublished in `releases/release-state.json`.

The release workflow uses `--require-head-tag`; executable publication-state validation occurs before artifact construction and therefore before the publication job can run.

## GitHub Release workflow

The workflow under `.github/workflows/release.yml`:

1. checks out the tagged commit
2. installs pinned validation dependencies
3. validates the full repository and unit tests
4. validates the tag against `VERSION` and the publication-state boundary
5. builds artifacts only for a publishable version
6. verifies checksums
7. creates the GitHub Release using the release-note file
8. attaches archives, checksums, release manifest, and migration notes

Prerelease tags are marked as GitHub prereleases.

## Tests

Focused tests live in:

```text
tools/tests/test_release.py
tools/tests/test_release_publication_boundary.py
```

Run:

```bash
python -m unittest discover -s tools/tests -p "test_release*.py"
```

Run the complete pipeline:

```bash
python tools/validate-all/run_all.py --include-tests
```

The publication-boundary regression executes the validator against forbidden `v0.9.0`, executes the builder against the blocked repository version, verifies that no output is produced, and confirms validation precedes build/publication in the workflow.

## Failure handling

If validation fails, correct the repository through a reviewed pull request before tagging.

If artifact generation fails after a tag exists:

- do not move the tag
- preserve logs
- correct the release machinery through review
- publish a corrective version or prerelease when required

If a GitHub Release is partially created, determine what became public before retrying.

## Compatibility

Backward-compatible changes may add optional result metadata or additional artifacts.

Breaking changes include:

- renaming entry points
- changing tag interpretation
- changing checksum format
- changing archive root or public artifact names
- removing manifest fields
- changing overwrite behavior
- changing which tracked files are included

## Review requirements

Changes to release validation, artifact generation, publication-state controls, or the GitHub Release workflow require:

- Release Manager review
- Tooling or CI specialist review
- compatibility analysis
- security analysis
- permanent CI
- independent specialist review when required by `MAINTAINERS.md`

## Limitations

- Artifact checksums do not certify normative correctness.
- GitHub repository settings and token restrictions require separate administrative review.
- Signed tags depend on maintainer signing capability.
- The repository currently has one active maintainer.
- Pre-1.0 releases do not establish the final stable compatibility promise.
- Prepared release documents are not evidence of a published tag or GitHub Release; publication state must be verified against GitHub and the executable publication-state boundary.

## Completion boundary

A successful release build proves that the reviewed source snapshot was packaged according to the implemented process. It does not prove that a release was published, that all packages are stable, that all guidance is correct, or that any adopting system is production-ready.
