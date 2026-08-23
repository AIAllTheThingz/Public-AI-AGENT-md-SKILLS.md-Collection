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

The skills are progressive-disclosure routers. They load only the packages relevant to the repository and request; they do not replace root governance, scoped `AGENTS.md` files, or accountable human review.

## Repository structure

| Area | Purpose |
|---|---|
| [`governance/`](governance/README.md) | Organization-wide agent behavior, product inception, risk, exceptions, evidence, and review |
| [`disciplines/`](disciplines/README.md) | Product management, UX, security, architecture, testing, APIs, data, accessibility, operations, and delivery |
| [`languages/`](languages/README.md) | Copyable language-specific standards packages |
| [`platforms/`](platforms/README.md) | Containers, Kubernetes, infrastructure as code, and cloud platforms |
| [`virtualization/`](virtualization/README.md) | Hypervisors, virtualization managers, clusters, hosts, guests, virtual networking and storage, recovery, and migration |
| [`operating-systems/`](operating-systems/README.md) | Windows, Enterprise Linux, Ubuntu, Debian, SUSE, Oracle Linux, macOS, and FreeBSD lifecycle, administration, security, recovery, and automation |
| [`networking/`](networking/README.md) | HPE Aruba, Cisco, Juniper, and Brocade network control planes, routing, switching, policy, fabrics, lifecycle, recovery, and automation |
| [`frameworks/`](frameworks/README.md) | Framework-specific scoped agent instructions |
| [`profiles/`](profiles/README.md) | Project-type overlays such as web API, worker service, and AI agent application |
| [`templates/`](templates/README.md) | Root and nested agent files, completion evidence, threat models, ADRs, and exceptions |
| [`schemas/`](schemas/README.md) | Machine-readable evidence and manifest schemas |
| [`examples/`](examples/README.md) | Example compositions showing how standards fit together |
| [`tools/`](tools/README.md) | Repository validation, composition, and release utilities |
| [`releases/`](releases/README.md) | Versioned release notes and migration guidance |
| [`maturity-reviews/`](maturity-reviews/README.md) | Evidence-backed maturity promotion and demotion records |

## Current language packages

- PowerShell 7.x
- C# 14 language engineering for the current .NET 10 boundary, with existing compiler boundaries preserved
- .NET 10 LTS
- JavaScript and TypeScript
- Python
- Java
- Go
- Rust
- Bash
- SQL
- Terraform and OpenTofu

Each language directory is independently adoptable and includes mandatory agent instructions, supporting standards, templates, examples, and a package manifest.

## Current virtualization packages

- VMware vSphere and ESXi
- XenServer and Citrix Hypervisor
- Proxmox VE
- XCP-ng
- KVM and libvirt
- Nutanix AHV
- Microsoft Hyper-V
- Red Hat Virtualization
- Oracle Linux KVM and Oracle Linux Virtualization Manager

Each virtualization directory is independently adoptable and includes mandatory agent instructions, an operations-and-automation standard, adoption and review templates, an evidence record, a fictitious example, and a package manifest.

## Current operating-system packages

- Windows Server 2016, 2019, 2022, and 2025
- Windows client: Windows 10 and Windows 11
- Red Hat Enterprise Linux family
- Ubuntu Server and Desktop
- Debian
- SUSE Linux Enterprise
- Oracle Linux
- macOS
- FreeBSD

Each operating-system directory is independently adoptable and includes mandatory agent instructions, an operations-and-automation standard, adoption and review templates, an evidence record, a fictitious example, and a package manifest. “Current” release claims require revalidation against authoritative lifecycle and security-update sources.

## Current networking packages

- HPE Aruba Networking
- Cisco networking
- Juniper Networks
- Broadcom Brocade Fabric OS and SANnav, with legacy Brocade Ethernet ownership triage

Each networking directory is independently adoptable and includes mandatory agent instructions, an operations-and-automation standard, adoption and review templates, an evidence record, a fictitious example, and a package manifest. Product, release, controller, lifecycle, firmware, feature, and interoperability claims require revalidation against current authoritative sources.

## Adoption model

Standards are layered rather than copied blindly:

```text
project/
├── AGENTS.md
├── standards/
├── src/
│   └── AGENTS.md
├── tests/
│   └── AGENTS.md
└── docs/
    └── AGENTS.md
```

The nearest scoped `AGENTS.md` may add stricter rules for its directory. It must not silently weaken applicable parent rules.

Adopters should record the repository version, tag, or source commit used so future upgrades can be reviewed against an explicit compatibility boundary.

## Rule format

Normative rules should include a stable identifier, a concrete requirement, expected evidence, and an exception path where applicable.

## Releases and maturity

Repository releases use Semantic Versioning as adapted by [`RELEASE_POLICY.md`](RELEASE_POLICY.md).

Release notes identify breaking, normative, editorial, tooling, security, deprecation, migration, and known-limitation changes.

Component maturity is governed by [`MATURITY_POLICY.md`](MATURITY_POLICY.md). A repository release does not automatically promote every package from `baseline` to `stable`.

`1.0.0` is reserved for a reviewed compatibility commitment that satisfies the release, ownership, adoption-testing, specialist-review, migration, and maturity gates.

## Maintainers and ownership

Repository ownership, area review, specialist-review requirements, merge authority, emergency changes, inactivity, and succession are defined in [`MAINTAINERS.md`](MAINTAINERS.md).

Review routing is defined in [`.github/CODEOWNERS`](.github/CODEOWNERS). CODEOWNERS requests review; it does not grant merge authority or create an independent-approval requirement by itself.

The repository currently has one active maintainer: **Metello Zuccolini** ([@AIAllTheThingz](https://github.com/AIAllTheThingz)). Routine low- and moderate-risk maintenance may be self-reviewed after permanent CI when no independent-review gate applies. Specialist review is encouraged for material technical changes; when independent specialist review is required by the maintainer or maturity policy, it must come from a qualified reviewer who is not the author.

## Contributing

Read [`CONTRIBUTING.md`](CONTRIBUTING.md), [`SECURITY.md`](SECURITY.md), [`MAINTAINERS.md`](MAINTAINERS.md), [`RELEASE_POLICY.md`](RELEASE_POLICY.md), and the affected scoped `AGENTS.md` files before making changes.

## Sources

Public source frameworks and standards used as references are cataloged in [`SOURCES.md`](SOURCES.md).

## License

This repository is licensed under the Apache License, Version 2.0 (`Apache-2.0`).

Copyright 2026 Metello Zuccolini.

See [`LICENSE`](LICENSE), [`NOTICE`](NOTICE), and [`LICENSING.md`](LICENSING.md).
