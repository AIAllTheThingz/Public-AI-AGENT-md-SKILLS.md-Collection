# Repository Manifest

## Stable entry points

- `AGENTS.md`
- `README.md`
- `CATALOG.md`
- `SOURCES.md`
- `SOURCE_REVIEWS.json`
- `CONTRIBUTING.md`
- `SECURITY.md`
- `MAINTAINERS.md`
- `.github/CODEOWNERS`
- `.github/pull_request_template.md`
- `VERSION`
- `CHANGELOG.md`
- `RELEASE_POLICY.md`
- `MATURITY_POLICY.md`
- `ROADMAP.md`
- `LICENSE`
- `NOTICE`
- `LICENSING.md`

## Agent skill entry points

- `languages/SKILL.md`
- `languages/csharp/SKILL.md`
- `frameworks/SKILL.md`
- `platforms/SKILL.md`
- `virtualization/SKILL.md`
- `operating-systems/SKILL.md`
- `networking/SKILL.md`

These progressive-disclosure routers and direct language skills select and compose existing standards packages. They do not replace root governance or scoped `AGENTS.md` instructions.

## Repository licensing

- Apache License, Version 2.0 (`Apache-2.0`)
- Copyright 2026 Metello Zuccolini
- complete license text in `LICENSE`
- attribution and project notice in `NOTICE`
- repository licensing scope and third-party-content guidance in `LICENSING.md`

## Repository maintenance and ownership

- current maintainer roster in `MAINTAINERS.md`
- review routing in `.github/CODEOWNERS`
- area ownership for governance, security, schemas, tools, standards packages, licensing, releases, and repository documentation
- editorial, normative, specialist, and legal review classes
- merge and author self-merge authority
- emergency-change and seven-day post-merge review requirements
- active, unavailable, inactive, and emeritus maintainer states
- appointment, reactivation, removal, and succession rules
- branch-protection and review-enforcement expectations
- explicit disclosure of the current single-maintainer limitation

## Repository versioning and releases

- canonical repository version in `VERSION`
- repository changelog in `CHANGELOG.md`
- Semantic Versioning and compatibility rules in `RELEASE_POLICY.md`
- maturity states and promotion reviews in `MATURITY_POLICY.md`
- machine-readable release state in `releases/release-state.json`
- versioned release notes under `releases/`
- versioned migration notes under `releases/migrations/`
- published-checkpoint and release-candidate compatibility inventories under `releases/compatibility/`
- release-candidate readiness records under `releases/rc-readiness/`
- maturity review records and template under `maturity-reviews/`
- downstream adoption pilot records under `adoption-pilots/`
- repeatable package-level adoption-test definitions and fixtures under `adoption-tests/`
- release validation and deterministic artifact generation under `tools/release/`
- tag-driven GitHub Release publication in `.github/workflows/release.yml`
- ZIP and TAR.GZ source archives
- SHA-256 checksum file
- machine-readable release manifest
- explicit `1.0.0` compatibility gate

Current repository version: `1.0.0-rc.1` **prepared and permanently validated; not yet published**.

The published migration checkpoint remains `0.10.0`, published as `v0.10.0` on 2026-08-16 from commit `83c73f3ab9a049ff2321d463164fcf98fb453a9c`. The validated RC functional candidate is `89a0470a3be4902f0c70eb31d396655dde4c8d7c`, recorded in `releases/rc-readiness/1.0.0-rc.1.md`.

The `0.9.0` baseline remains **prepared, unpublished** and must not be reconstructed or retroactively tagged.

Next intended publication: `1.0.0-rc.1`.

Current `main` must not be retroactively tagged as `v0.9.0`.

## Source-currency maintenance

- authoritative-source catalog in `SOURCES.md`
- accountable source-review registry in `SOURCE_REVIEWS.json`
- offline source-review age validation in `tools/check-freshness/check_freshness.py`
- scheduled/manual freshness workflow in `.github/workflows/source-freshness.yml`
- live vendor/source content verification remains separate from offline freshness validation and must be recorded honestly when performed

## Complete governance system

- `governance/AGENTS.md`
- `governance/README.md`
- `governance/MANIFEST.md`
- `governance/POLICY_MAP.md`
- `governance/ADOPTION_GUIDE.md`
- `governance/OPERATING_MODEL.md`
- `governance/POLICY_LIFECYCLE.md`
- `governance/CONTROL_EVIDENCE_MODEL.md`
- `governance/GOVERNANCE_DECISION_MATRIX.md`
- eleven governance policies
- governance adoption, authorization, review, risk, exception, readiness, threat, vulnerability, AI-review, evidence, and policy-change templates
- governance workflow and decision examples
- schema-shaped risk, exception, and completion evidence examples

## Complete language packages

- `languages/powershell`
- `languages/csharp`
- `languages/dotnet`
- `languages/javascript-typescript`
- `languages/python`
- `languages/java`
- `languages/go`
- `languages/rust`
- `languages/bash`
- `languages/sql`
- `languages/terraform-opentofu`

## Complete discipline packages

- `disciplines/application-security`
- `disciplines/architecture`
- `disciplines/testing`
- `disciplines/api-engineering`
- `disciplines/integration`
- `disciplines/database`
- `disciplines/data-engineering`
- `disciplines/accessibility`
- `disciplines/privacy`
- `disciplines/observability`
- `disciplines/sre`
- `disciplines/documentation`
- `disciplines/ci-cd`
- `disciplines/supply-chain`
- `disciplines/release-engineering`

## Complete framework packages

- `frameworks/aspnet-core`
- `frameworks/react`
- `frameworks/angular`
- `frameworks/spring-boot`
- `frameworks/fastapi`

Each complete framework package includes scoped agent instructions, a useful README, a manifest, framework-specific standards, adoption and review templates, an evidence template, and an adoption example.

## Complete platform packages

- `platforms/containers`
- `platforms/kubernetes`
- `platforms/terraform`
- `platforms/azure`
- `platforms/aws`
- `platforms/gcp`

Each complete platform package includes scoped agent instructions, a useful README, a manifest, platform-specific standards, adoption and review templates, an evidence template, and an adoption example.

The platform collection also includes selection, shared-responsibility, change-lifecycle, and decision-matrix guidance.

## Complete virtualization packages

- `virtualization/vsphere-esxi`
- `virtualization/xenserver-citrix-hypervisor`
- `virtualization/proxmox-ve`
- `virtualization/xcp-ng`
- `virtualization/kvm-libvirt`
- `virtualization/nutanix-ahv`
- `virtualization/microsoft-hyper-v`
- `virtualization/red-hat-virtualization`
- `virtualization/oracle-linux-kvm`

Each complete virtualization package includes scoped agent instructions, an operations-and-automation standard, adoption and review templates, an evidence template, a fictitious adoption example, and a manifest.

The virtualization collection also includes selection, shared-responsibility, change-lifecycle, and cross-platform migration guidance.

## Complete operating-system packages

- `operating-systems/windows-server`
- `operating-systems/windows-client`
- `operating-systems/rhel-family`
- `operating-systems/ubuntu`
- `operating-systems/debian`
- `operating-systems/suse-linux-enterprise`
- `operating-systems/oracle-linux`
- `operating-systems/macos`
- `operating-systems/freebsd`

Each complete operating-system package includes scoped agent instructions, an operations-and-automation standard, adoption and review templates, an evidence template, a fictitious adoption example, and a manifest.

The operating-system collection also includes selection, shared-responsibility, change-lifecycle, current-release, and upgrade/migration guidance.

## Complete networking packages

- `networking/hpe-aruba-networking`
- `networking/cisco-networking`
- `networking/juniper-networks`
- `networking/brocade-networking`

Each complete networking package includes scoped agent instructions, an operations-and-automation standard, adoption and review templates, an evidence template, a fictitious adoption example, and a manifest.

The networking collection also includes vendor/ownership selection, shared-responsibility, change-lifecycle, topology, firmware, recovery, and migration/refresh guidance.

## Complete project profile packages

- `profiles/web-api`
- `profiles/web-application`
- `profiles/worker-service`
- `profiles/cli-tool`
- `profiles/desktop-application`
- `profiles/mobile-application`
- `profiles/serverless-function`
- `profiles/data-pipeline`
- `profiles/public-library`
- `profiles/internal-automation`
- `profiles/multi-tenant-saas`
- `profiles/security-tool`
- `profiles/ai-agent-application`

Each complete profile package includes scoped agent instructions, a useful README, a manifest, six profile-specific standards, adoption and review templates, an evidence template, and an adoption example. The uppercase canonical profile files remain stable compatibility entry points.

## Complete schema system

- six rolling Draft 2020-12 schemas under `schemas/`
- six backward-compatible major-version schemas under `schemas/v1/`
- schema agent instructions and manifest
- schema catalog
- versioning, compatibility, extension, migration, validation, and design guidance
- positive and negative examples for every contract
- executable schema validation tooling under `tools/validate-schemas/`

The six stable rolling filenames remain present. Long-lived consumers should pin the versioned paths.

## Complete template library

- root and nested agent-instruction templates
- architecture decision records
- risk assessments
- threat models
- standards exception records
- completion reports
- project manifest, test evidence, and artifact record JSON templates
- change authorization and human review records
- production-readiness reviews
- release plans
- rollback and recovery plans
- operational runbooks
- template selection, authoring, customization, placeholder, lifecycle, validation, and completion guidance
- package review checklists and completed fictitious examples
- executable template validation under `tools/validate-templates/`

The seven original template paths remain stable.

## Complete composition examples

- `examples/minimal`
- `examples/web-api`
- `examples/worker-service`
- `examples/full-stack`

Each complete example includes root and nested agent instructions, a project manifest, composition rationale, tailoring decisions, architecture, risk, testing, operations, completion evidence, and schema-shaped JSON evidence.

## Complete repository toolchain

- repository structure validation
- relative Markdown link and anchor validation
- source-review freshness validation through `tools/check-freshness/check_freshness.py`
- skill metadata, package-routing, registration, and local-link validation
- Draft 2020-12 schema and instance validation
- reusable template package validation
- tool package and executable-entry validation
- repository release validation
- published-checkpoint-to-RC compatibility regression with deliberate-removal failure coverage
- deterministic release artifact generation
- deterministic project-manifest generation
- traceable agent-standards composition
- unified validation aggregation
- shared result library and JSON result contract
- central unit tests and fixtures
- tool selection, development, testing, security, troubleshooting, release, and compatibility guidance

The stable validator entry paths remain present. Shared executable tools support text and JSON results, common exit-code semantics, and offline operation. Writing tools preserve safe overwrite behavior. Release artifacts are checksum-backed and tied to the source commit.

## Validation

For CI-equivalent dependency installation and full validation:

```bash
python -m pip install --require-hashes -r tools/validate-schemas/requirements.lock
python tools/validate-all/run_all.py --include-tests
python tools/release/validate_release.py
```
