---
id: TOOL-CATALOG-001
title: Tool Catalog
version: 1.4.0
status: baseline
---

# Tool Catalog

## Catalog

| Tool | Reads | Writes | External dependency | Primary owner |
|---|---|---|---|---|
| Validate Standards | Repository tree | None | None | Repository maintainers |
| Check Links | Markdown files | None | None | Documentation maintainers |
| Check Freshness | `SOURCE_REVIEWS.json` and referenced repository scopes | Optional result file | None | Standards and source-maintenance owners |
| Validate Skills | Skill files, package routes, manifests, local links, and optional UI metadata | Optional result file | None | Tooling and standards maintainers |
| Validate Schemas | Schemas and JSON instances | None | `jsonschema[format]` | Schema maintainers |
| Validate Templates | Templates, examples, schemas | None | `jsonschema[format]` | Template maintainers |
| Validate Tools | Tool packages, tests, validation dependency input/lock, GitHub Actions workflow YAML, and referenced local composite actions | Optional result file | `PyYAML` | Tool maintainers |
| Validate Release | Version, changelog, release notes, migration notes, release and maturity policies, tag state | Optional result file | None | Release Manager and Tooling Maintainer |
| Build Release | Git-tracked repository files and versioned notes | Release distribution directory | None | Release Manager and Tooling Maintainer |
| Generate Manifest | Profiles; language, discipline, framework, platform, virtualization, operating-system, and networking package directories; schema | Manifest file | `jsonschema[format]` | Project adopter |
| Compose Agents | Project manifest and selected governance, profile, language, discipline, framework, platform, virtualization, operating-system, and networking standards | Bundle directory | `jsonschema[format]` | Project adopter |
| Validate All | Validator entry points and tests | Optional result file | Validator dependencies | Repository maintainers |

`Check Freshness` is offline by default. It validates source-review metadata and review-date age, reports human-facing `Passed`, `Warning`, or `NotRun` freshness state, and separately records live source verification as `NotRun`. It does not fetch vendor documentation or infer source currency from network availability.

`Validate Tools` structurally parses workflow and referenced local composite-action YAML, recursively checks immutable third-party action references (full Git commit SHAs or OCI `sha256` digests for `docker://` actions), rejects floating hosted runner images, verifies exact direct-dependency/lock synchronization, and requires at least one valid SHA-256 hash on every resolved lock entry.

## Stable entry points

Stable Python entry paths include:

- `tools/validate-standards/validate_repository.py`
- `tools/check-links/check_links.py`
- `tools/check-freshness/check_freshness.py`
- `tools/validate-skills/validate_skills.py`
- `tools/validate-schemas/validate_schemas.py`
- `tools/validate-templates/validate_templates.py`
- `tools/validate-tools/validate_tools.py`
- `tools/release/validate_release.py`
- `tools/release/build_release.py`
- `tools/generate-manifest/generate_manifest.py`
- `tools/compose-agents/compose_agents.py`
- `tools/validate-all/run_all.py`

Moving or renaming a stable entry point requires migration guidance and the release classification defined by `RELEASE_POLICY.md`.

## Selection

Use a specific validator during focused development. Use `validate-all` before review or merge.

Use `check-freshness` when reviewing source currency, lifecycle references, compatibility claims, or source-review cadence. Default execution is warning-oriented; use `--strict` only when stale or not-run review state should block the caller.

Use `validate-release` when changing VERSION, changelog, maturity, deprecation, migration, release notes, tags, release tooling, or release workflows.

Use `build-release` only after the versioned release files have been reviewed and validation passes.

Use `generate-manifest` when beginning a project composition. Use `compose-agents` only after the generated manifest is reviewed and accepted as a correct selection record.

## Ownership

Every tool change must identify:

- implementation owner
- contract owner
- CI owner
- affected consumers
- documentation owner
- migration owner for breaking changes
- release owner when the change affects packaging, tags, checksums, or publication

Release-tool and release-workflow changes require the review class defined in `MAINTAINERS.md`.

## Evidence

A tool execution record should capture:

- tool path and version
- repository revision
- exact command
- environment
- exit code
- JSON result where practical
- checks not run
- limitations

A source-freshness record should additionally identify:

- repository scope
- authoritative sources
- accountable owner
- configured review interval
- actual source-review date, or explicit `NotRun`
- whether live external verification was performed

A release-tool execution should additionally capture:

- repository VERSION
- tag
- source commit
- artifact names and sizes
- SHA-256 digests
- release manifest
- checksum verification result
- GitHub Release URL after publication
