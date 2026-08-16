---
id: RELEASE-INDEX-001
title: Repository Releases
version: 1.0.0-rc.1
status: baseline
---

# Repository Releases

## Purpose

This directory contains version-specific release notes and migration guidance for **Public Access Agents**.

The project/library name is **Public Access Agents**. The canonical GitHub repository is **`AIAllTheThingz/Public-AI-Governance`**. Repository URLs and machine-readable source identifiers use the current repository name, while release archives retain the established `Public-Access-Agents-<VERSION>` prefix.

Repository release requirements are defined by [`../RELEASE_POLICY.md`](../RELEASE_POLICY.md). Package maturity requirements are defined by [`../MATURITY_POLICY.md`](../MATURITY_POLICY.md).

## Current release state

| Version | Repository state | Git tag | GitHub Release |
|---|---|---|---|
| `0.9.0` | Prepared compatibility baseline | **Not published** | **Not published** |
| `0.10.0` | Published pre-1.0 adoption and compatibility checkpoint | `v0.10.0` | Published 2026-08-16 |
| `1.0.0-rc.1` | Prepared source candidate; functional compatibility candidate validated; exact record/document tree remains `NotRun` in the source readiness record | **Not published** | **Not published** |

The `0.9.0` materials were prepared on 2026-07-13, but no `v0.9.0` tag and no GitHub Release were created. Current `main` must not be retroactively tagged as `v0.9.0`, because it contains substantial work accumulated after that prepared baseline.

The machine-readable [`release-state.json`](release-state.json) records this publication exception. Release validation rejects a tag for a version listed under `preparedUnpublishedVersions`, and the release builder refuses to construct publication artifacts for it. This prevents the tag-triggered workflow from turning the prepared `0.9.0` documents into an accidental GitHub Release.

The `0.10.0` release is published and verified and remains the published migration checkpoint. For `1.0.0-rc.1`, the functional compatibility candidate has passed the compatibility gate and permanent validation; that immutable functional evidence is recorded in [`rc-readiness/1.0.0-rc.1.md`](rc-readiness/1.0.0-rc.1.md). The readiness record intentionally keeps validation of the exact record/document tree as `NotRun`, because updating the record to embed a later run would create a different tree. PR #71 therefore requires a fresh exact-head permanent CI run after any record or documentation update, with that result carried in PR metadata rather than written back into the source record.

The next intended publication is `1.0.0-rc.1` and is forward-only; independent specialist approval and deliberate tag-driven publication remain required before the prepared source candidate becomes a published release.

## Structure

```text
releases/
├── README.md
├── release-state.json
├── <VERSION>.md
├── compatibility/
│   ├── 0.10.0-checkpoint.json
│   └── 1.0.0-rc.1.json
├── migrations/
│   └── <VERSION>.md
├── rc-readiness/
│   └── <VERSION>.md
└── verification/
    └── <VERSION>.md
```

`release-state.json` records repository-specific publication-state facts that release tooling must enforce. It is not a substitute for GitHub tag/release verification and must remain synchronized with release documentation.

Compatibility inventories record the published checkpoint and candidate compatibility surfaces used by the RC gate. RC readiness records pin source-candidate validation evidence while explicitly separating that evidence from publication and final-release approval.

## Release notes

Every repository version requires `releases/<VERSION>.md` containing:

- breaking changes
- normative changes
- editorial changes
- tooling changes where applicable
- deprecations
- migration notes
- security changes
- known limitations

A section must remain present even when it contains `None`.

Prepared release notes are not proof that a Git tag or GitHub Release exists. Published state must be verified against GitHub, and a version explicitly marked prepared/unpublished must remain blocked by the release tooling until a deliberate future release-state change removes that block.

## Migration notes

Every repository version requires `releases/migrations/<VERSION>.md`.

Migration notes identify affected adopters, required actions, validation, downgrade or rollback considerations, and unresolved limitations.

## Release artifacts

The release workflow attaches:

- deterministic ZIP archive
- deterministic TAR.GZ archive
- SHA-256 checksum file
- release manifest
- release notes
- migration notes

Archive filenames use the project-compatible `Public-Access-Agents-<VERSION>` prefix even though the GitHub repository is named `Public-AI-Governance`.

## Boundary

A GitHub Release identifies a reviewed source and compatibility boundary. A prepared release document or validated source candidate without the corresponding tag and GitHub Release does not establish a published boundary. Repository releases do not certify adopting systems or prove that every baseline package has reached stable maturity.
