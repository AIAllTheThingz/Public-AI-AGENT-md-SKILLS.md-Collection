# Repository Release Policy

## Purpose

This policy defines repository-wide versioning, compatibility, deprecation, migration, release review, Git tags, GitHub Releases, artifacts, checksums, and release evidence for Public-Access-Agents.

The repository contains normative standards, schemas, templates, examples, and executable tools. A release therefore represents more than a documentation snapshot. It communicates which public contracts are intended to remain compatible and what adopters must review before upgrading.

A version number does not prove quality, security, correctness, adoption, or production readiness. It identifies a reviewed compatibility boundary. Numbers remain unable to perform peer review despite their excellent attendance record.

## Authority

Release ownership and merge authority are defined by [`MAINTAINERS.md`](MAINTAINERS.md).

The Release Manager coordinates a release but may not bypass:

- review gates explicitly required by `MAINTAINERS.md`
- security review appropriate to release risk
- schema or tool compatibility review appropriate to changed contracts
- permanent CI
- migration requirements
- the `1.0.0` compatibility gate

Routine low- and moderate-risk release-tooling or release-automation maintenance may be maintainer self-reviewed after permanent CI when no independent-review gate applies. Breaking changes, high/critical changes, the final `1.0.0` compatibility approval, and other commitments identified by `MAINTAINERS.md` still require independent specialist review.

## Repository semantic versioning

Repository versions use Semantic Versioning 2.0.0:

```text
MAJOR.MINOR.PATCH[-PRERELEASE][+BUILD]
```

The canonical source version is stored in [`VERSION`](VERSION).

The repository version covers the combined public contract of:

- stable repository paths
- normative rule identifiers and meaning
- package selection and composition behavior
- schema contracts and versioned schema paths
- template stable paths and required fields
- executable tool paths, options, output contracts, exit codes, and generated file semantics
- release artifact structure
- licensing, ownership, and governance declarations

Individual documents, schemas, packages, and tools may retain their own versions. Their versions do not override the repository release version.

### Patch release

Increment PATCH for backward-compatible corrections that do not require adopter migration, including:

- editorial corrections that preserve normative meaning
- source-link updates
- example corrections that preserve the contract
- validator false-positive or false-negative fixes that restore documented behavior
- security fixes that preserve supported interfaces
- clarification of evidence expectations without adding a new obligation

A change described as editorial must not alter requirement strength, scope, authority, compatibility, or completion criteria.

### Minor release

Increment MINOR for backward-compatible additions, including:

- new optional standards packages
- new optional rules or evidence fields
- new optional schema properties
- new tool flags or result metadata
- new templates or examples
- new supported platforms, frameworks, or languages
- introduction of a deprecation
- stricter behavior that is opt-in and does not change an existing default

A minor release may require adopters to review new capability, but must not invalidate supported existing use without an approved exception described in the release notes.

### Major release

Increment MAJOR for a breaking compatibility change, including:

- removing or renaming stable paths
- removing or reusing rule identifiers
- changing normative rule meaning in a way that invalidates supported adoption
- making an optional requirement mandatory
- narrowing supported runtimes, platforms, or inputs without a preserved compatibility path
- changing schema required fields, property types, enums, identifiers, or extension behavior incompatibly
- changing executable entry points, exit-code meaning, required options, overwrite behavior, or generated file semantics incompatibly
- changing governance authority, approval, or exception behavior incompatibly
- removing a deprecated contract after its supported window

A breaking change requires migration notes, explicit release-note classification, independent specialist review, and a major version increment after `1.0.0`.

## Pre-1.0 policy

Versions below `1.0.0` communicate that the repository is usable but its long-term compatibility contract is not yet stable.

Pre-1.0 releases still classify changes as patch, minor, or breaking using this policy. A `0.MINOR.0` release may contain a breaking change, but the change must be identified explicitly under **Breaking changes** and accompanied by migration notes.

Pre-1.0 status is not permission to change public contracts silently.

The repository originally prepared `0.9.0` as its initial release target, but that release was never published and must not be reconstructed or retroactively tagged. The first real repository release, `0.10.0`, was published on 2026-08-16. The forward-only next intended publication is `1.0.0-rc.1`, as recorded in [`releases/release-state.json`](releases/release-state.json). `0.10.0` remains the pre-1.0 adoption and compatibility checkpoint used to gather evidence for that release candidate, not the final compatibility commitment.

## Compatibility inventory

Before every release, the Release Manager must review changes to:

- root stable files
- repository catalogs and manifests
- `AGENTS.md` precedence and scope behavior
- governance policies
- rule identifiers
- package paths and manifests
- schemas and versioned schema copies
- templates and placeholders
- tool commands and generated output
- licensing and ownership terms
- release artifacts and workflow behavior

Compatibility impact must be stated as one of:

- compatible
- conditionally compatible
- breaking
- not applicable

“Probably compatible” is not a supported classification, though it remains a popular source of post-release exercise.

## Change classification in release notes

Every release note must contain these sections, even when the value is `None`:

- Breaking changes
- Normative changes
- Editorial changes
- Deprecations
- Migration notes
- Security
- Known limitations

Tooling changes may be recorded in a separate section when applicable.

Each normative item should identify affected packages, rules, schemas, templates, or tools.

## Deprecation windows

### Ordinary deprecations

A supported rule, option, path, template field, or behavior must normally remain available for at least:

- one subsequent minor release, and
- 90 calendar days after the release that announces deprecation

Removal must occur in a release whose notes identify the removed contract and link to migration guidance.

### Stable paths and machine-readable contracts

Stable executable paths, schema major versions, required schema fields, documented JSON result fields, and stable template paths must normally remain supported for at least:

- two subsequent minor releases, and
- 180 calendar days after deprecation is announced

A replacement and migration procedure must be available throughout the overlap period.

### Security exception

A dangerous interface or instruction may be removed sooner when continued support creates material security or safety risk.

Accelerated removal requires:

- explicit security rationale
- affected-consumer analysis
- the safest available migration or containment path
- Security Maintainer approval
- specialist review where feasible and independent review when required by `MAINTAINERS.md`
- release-note disclosure appropriate to the vulnerability context

Confidential vulnerability details must not be exposed merely to make the changelog feel complete.

## Migration notes

Every repository version must have a migration file under:

```text
releases/migrations/<VERSION>.md
```

Migration notes must identify:

- who is affected
- required actions
- optional improvements
- removed or deprecated contracts
- compatibility assumptions
- validation commands
- rollback or downgrade considerations
- unresolved limitations

A release with no adopter action must say so explicitly.

## Release process

### 1. Prepare the release change

The release pull request must:

1. update `VERSION`
2. move completed entries from `Unreleased` into a dated changelog section
3. add `releases/<VERSION>.md`
4. add `releases/migrations/<VERSION>.md`
5. update affected manifests, policies, schemas, templates, examples, and tools
6. classify compatibility and risk
7. identify recommended and required reviewers
8. run the permanent validation pipeline
9. build release artifacts locally or in CI
10. verify checksums and the release manifest

### 2. Review

The final release commit must receive the review class required by `MAINTAINERS.md`.

Any breaking change covered by the release and the final `1.0.0` compatibility approval require independent specialist review. Material release-workflow, release-tool, schema-contract, and security-sensitive release changes should receive specialist review when practical and require independence when `MAINTAINERS.md` classifies the change into an independent-review gate.

### 3. Merge

The release pull request must merge to `main` before tagging.

The tag must reference the exact reviewed commit on `main`. Tags must not be created from an unmerged branch, working tree, or reconstructed local state.

### 4. Tag

Create an annotated, signed tag where signing capability is available:

```bash
git tag -s vMAJOR.MINOR.PATCH -m "Public-Access-Agents MAJOR.MINOR.PATCH"
git push origin vMAJOR.MINOR.PATCH
```

When signed tags are not available, create an annotated tag and record that limitation:

```bash
git tag -a vMAJOR.MINOR.PATCH -m "Public-Access-Agents MAJOR.MINOR.PATCH"
```

### 5. Publish

Pushing a valid `v*` tag starts the release workflow. The workflow validates the tag and repository, builds deterministic artifacts, computes checksums, and creates the GitHub Release.

### 6. Verify

After publication, the Release Manager must verify:

- the tag references the intended commit
- the GitHub Release is visible
- release notes match the repository version
- both archives are attached
- `SHA256SUMS.txt` is attached
- `release-manifest.json` is attached
- checksums verify after downloading
- migration notes are attached
- no draft or prerelease flag is incorrect

## Git tags

Stable tags use:

```text
vMAJOR.MINOR.PATCH
```

Prerelease tags use valid Semantic Versioning suffixes, for example:

```text
v1.0.0-rc.1
v1.1.0-beta.2
```

Tags are immutable public release identifiers. A published tag must not be moved or recreated.

If an incorrect tag is published, create a corrective release and document the error. Do not silently retarget the tag and ask history to cooperate.

## GitHub releases

Each GitHub Release must:

- use the matching Git tag
- use the title `Public-Access-Agents <VERSION>`
- use `releases/<VERSION>.md` as the release-note source
- mark prerelease versions as prereleases
- include release and migration notes
- attach release archives, checksums, and the release manifest
- state known limitations

A release may be drafted for review, but it must not be published until the corresponding tag and artifacts pass validation.

## Release artifacts and checksums

The release workflow produces:

- `Public-Access-Agents-<VERSION>.zip`
- `Public-Access-Agents-<VERSION>.tar.gz`
- `SHA256SUMS.txt`
- `release-manifest.json`
- `RELEASE_NOTES.md`
- `MIGRATION_NOTES.md`

Archives are built from Git-tracked files with deterministic ordering and normalized metadata.

`SHA256SUMS.txt` contains SHA-256 digests for the ZIP and TAR archives.

The release manifest records:

- release version
- tag
- source commit
- archive root
- tracked-file count
- artifact names
- artifact sizes
- artifact SHA-256 digests
- release-note and migration-note filenames

Release artifacts are evidence of the published source snapshot. They do not prove that every normative rule is correct or every adopting project is safe.

## Prereleases and release candidates

Prereleases are recommended when:

- a major release is approaching
- schema or CLI compatibility is changing
- release automation changed materially
- broad adoption testing is required
- a stable package is being promoted

A release candidate must use a SemVer prerelease identifier such as `-rc.1` and must not be presented as a stable release.

## 1.0.0 compatibility gate

`1.0.0` may be published only when all of the following are true:

- the repository versioning and ownership policies are active
- stable public paths and contracts are inventoried
- representative package-adoption tests pass
- schemas, templates, and executable tools have compatibility reviews
- governance, security, schemas, tools, and release automation receive independent specialist review
- all packages included in the stable promise are either `stable` or explicitly documented as `baseline` and outside the compatibility promise
- migration guidance exists from the latest `0.x` release
- at least one `1.0.0-rc.N` release has been available for review
- release artifacts and checksums have been independently verified
- no unresolved critical or high release blocker remains
- known limitations are published
- the final release commit passes permanent CI

The `1.0.0` release is a compatibility commitment, not a declaration that the repository has achieved perfection. Perfection would be suspicious and, more importantly, incompatible with maintenance.

## Failed or partial release

If artifact creation or GitHub Release publication fails:

- do not move the tag
- preserve workflow logs and generated evidence
- determine whether any artifact became public
- correct the release machinery through a reviewed pull request
- publish a new patch or prerelease tag when necessary
- document consumer impact

## Release evidence

The release record should retain:

- release pull request
- required reviews
- final validation run
- tag and commit
- release URL
- release manifest
- checksum verification
- migration notes
- known limitations
- any incident or corrective release

## Policy maintenance

Changes to this policy, `VERSION`, release tooling, or release workflow are release-governance or executable-tool changes. They require Release Manager review, compatibility analysis, and permanent CI. Tooling or CI specialist review should be requested for material changes and becomes independently required when `MAINTAINERS.md` places the change behind an independent-review gate.
