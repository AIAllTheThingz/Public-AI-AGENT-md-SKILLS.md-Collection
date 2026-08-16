---
id: RELEASE-INDEX-001
title: Repository Releases
version: 0.10.0
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
| `0.10.0` | Prepared release candidate; publication pending final independent review and tag workflow | Not created | Not created |

The `0.9.0` materials were prepared on 2026-07-13, but no `v0.9.0` tag and no GitHub Release were created. Current `main` must not be retroactively tagged as `v0.9.0`, because it contains substantial work accumulated after that prepared baseline.

The machine-readable [`release-state.json`](release-state.json) records this publication exception. Release validation rejects a tag for a version listed under `preparedUnpublishedVersions`, and the release builder refuses to construct publication artifacts for it. This prevents the tag-triggered workflow from turning the prepared `0.9.0` documents into an accidental GitHub Release.

The next intended publication is `0.10.0` and is forward-only. The release-candidate source now sets `VERSION` to `0.10.0`; before the tag is created, changelog, release notes, migration guidance, release artifacts, independent review, and validation evidence must all describe the same exact candidate consistently.

## Structure

```text
releases/
├── README.md
├── release-state.json
├── <VERSION>.md
└── migrations/
    └── <VERSION>.md
```

`release-state.json` records repository-specific publication-state facts that release tooling must enforce. It is not a substitute for GitHub tag/release verification and must remain synchronized with release documentation.

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

A GitHub Release identifies a reviewed source and compatibility boundary. A prepared release document without the corresponding tag and GitHub Release does not establish a published boundary. Repository releases do not certify adopting systems or prove that every baseline package has reached stable maturity.
