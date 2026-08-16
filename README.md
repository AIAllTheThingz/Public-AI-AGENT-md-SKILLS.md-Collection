# Public Access Agents

Public, reusable `AGENTS.md` standards for secure, maintainable, testable, and evidence-based AI-assisted engineering.

## Why this repository exists

AI coding agents can generate useful software quickly. They can also generate fragile code, unsafe defaults, vague documentation, weak tests, and confident completion claims unsupported by evidence. This repository provides composable standards that turn engineering discipline into explicit agent instructions.

These standards improve behavior. They do not guarantee security, correctness, compliance, or production readiness.

## Repository identity

**Public Access Agents** is the project and library name. The canonical GitHub repository is **`AIAllTheThingz/Public-AI-Governance`**.

Repository URLs, raw-content URLs, and machine-readable schema identifiers use the current GitHub repository name. Release archive names retain the established `Public-Access-Agents-<VERSION>` prefix so the project identity and artifact naming remain stable without pretending the GitHub repository was never renamed.

The `0.9.0 (prepared, unpublished)` baseline was never published and must not be retroactively tagged. The first real repository release, `v0.10.0`, was published on 2026-08-16 from the reviewed `main` commit `83c73f3ab9a049ff2321d463164fcf98fb453a9c`.

## Current repository version

The current source candidate is defined in [`VERSION`](VERSION).

Current source candidate: **1.0.0-rc.1** (prepared, with its recorded functional compatibility candidate permanently validated; exact record/document-tree validation is tracked separately, and the RC is not yet published). See the [RC readiness record](releases/rc-readiness/1.0.0-rc.1.md) and PR validation metadata for the exact-head result.

Current published release: **0.10.0** (`v0.10.0`, published 2026-08-16). It remains the published migration checkpoint for the RC compatibility gate.

Next intended publication: `1.0.0-rc.1`.

The prepared RC defines the proposed first stable compatibility surface but does not itself establish a published release. Final `1.0.0` remains a separate gate requiring a published RC, independently verified artifacts/checksums, exact-final-commit independent compatibility approval, and no unresolved high/critical release blocker.

See:

- [`CHANGELOG.md`](CHANGELOG.md)
- [`RELEASE_POLICY.md`](RELEASE_POLICY.md)
- [`MATURITY_POLICY.md`](MATURITY_POLICY.md)
- [`releases/`](releases/README.md)

## Start here

1. Read the root [`AGENTS.md`](AGENTS.md).
2. Select one or more standards from the [`CATALOG.md`](CATALOG.md).
3. Select a project profile from [`profiles/`](profiles/README.md).
4. Copy the relevant language package from [`languages/`](languages/README.md).
5. Add scoped standards for applicable disciplines, platforms, virtualization systems, operating systems, networking systems, and frameworks.
6. Tailor the result without weakening security, validation, testing, or completion-evidence requirements.
7. Record the repository version or tag used by the adopting project.
8. Validate the repository with the tools under [`tools/`](tools/README.md).

## Agent skill entry points

Use the collection-level skills and registered direct language skills when an agent must select and apply the repository's standards while performing engineering work:

- [`languages/SKILL.md`](languages/SKILL.md) routes advanced coding and scripting work to the applicable language packages.
- [`languages/csharp/SKILL.md`](languages/csharp/SKILL.md) directly applies advanced C# language, scripting, compiler, API, async, performance, interop, security, testing, and migration standards.
- [`frameworks/SKILL.md`](frameworks/SKILL.md) composes framework and underlying language packages for application work.
- [`platforms/SKILL.md`](platforms/SKILL.md) composes platform packages for infrastructure and deployment work while preserving authorization boundaries.
- [`virtualization/SKILL.md`](virtualization/SKILL.md) composes hypervisor and virtualization-management packages for safe automation, operations, recovery, and migration work.
- [`operating-systems/SKILL.md`](operating-systems/SKILL.md) composes OS packages for safe provisioning, administration, hardening, patching, recovery, upgrade, and fleet automation.
- [`networking/SKILL.md`](networking/SKILL.md) composes vendor networking packages for safe control-plane automation, operations, upgrades, migration, recovery, routing, switching, policy, and Fibre Channel fabric work.

## Repository contents

- [`governance/`](governance/) — organization-level and repository-level governance rules
- [`profiles/`](profiles/) — project-type composition blueprints
- [`languages/`](languages/) — language-specific coding, testing, security, and migration standards
- [`disciplines/`](disciplines/) — cross-cutting engineering disciplines
- [`frameworks/`](frameworks/) — framework-specific standards and composition guidance
- [`platforms/`](platforms/) — platform and cloud engineering standards
- [`virtualization/`](virtualization/) — hypervisor and virtualization-management standards
- [`operating-systems/`](operating-systems/) — operating-system administration and automation standards
- [`networking/`](networking/) — vendor networking and fabric-management standards
- [`schemas/`](schemas/) — machine-readable evidence and manifest contracts
- [`templates/`](templates/) — reusable project, evidence, authorization, and review templates
- [`tools/`](tools/) — repository validators, composition utilities, and release tooling
- [`releases/`](releases/) — release notes, migration guidance, compatibility inventories, and readiness evidence

## License

Licensed under the [Apache License 2.0](LICENSE). See [`NOTICE`](NOTICE) and [`LICENSING.md`](LICENSING.md) for repository licensing details.
