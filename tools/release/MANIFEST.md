---
id: TOOL-PKG-RELEASE-001-MANIFEST
title: Repository Release Tool Manifest
version: 1.0.0
status: baseline
---

# Repository Release Tool Manifest

## Required files

- `validate_release.py`
- `build_release.py`
- `README.md`
- `MANIFEST.md`
- `examples/README.md`

## Shared contracts

- `../TOOL_CONTRACT.md`
- `../contracts/tool-result.schema.json`
- `../tests/test_release.py`
- `../tests/test_release_publication_boundary.py`
- `../../RELEASE_POLICY.md`
- `../../MATURITY_POLICY.md`

## Required repository inputs

- `VERSION`
- `CHANGELOG.md`
- `releases/release-state.json` for repository publication-state exceptions
- `releases/<VERSION>.md`
- `releases/migrations/<VERSION>.md`
- `.github/workflows/release.yml`

## Acceptance checks

- both entry points compile
- validator supports the shared command-line contract
- repository version is valid Semantic Versioning
- changelog contains a dated matching version
- release and migration notes exist
- required release-note sections exist
- tag matches `v<VERSION>`
- versions listed as prepared/unpublished are rejected by tag validation before artifact build or publication
- the builder refuses publication artifacts for prepared/unpublished versions
- deterministic archives build for publishable versions
- checksums verify
- release manifest records source commit and artifacts
- existing output is protected unless `--force` is supplied
- release workflow validates before build and publication
- release workflow uses the permanent validation pipeline
- positive and negative tests pass
- documentation matches behavior
