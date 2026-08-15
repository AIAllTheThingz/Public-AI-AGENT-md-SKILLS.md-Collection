# Changelog

All notable repository changes are recorded here.

The repository follows [Semantic Versioning 2.0.0](https://semver.org/) as adapted by [`RELEASE_POLICY.md`](RELEASE_POLICY.md) for normative standards, schemas, templates, executable tools, stable paths, and documentation.

Release notes distinguish:

- **breaking changes** that invalidate a supported contract or require migration
- **normative changes** that add or alter requirements or evidence expectations
- **editorial changes** that do not change normative meaning
- **tooling changes** that alter executable validation, generation, composition, or release behavior
- **security changes** that address or disclose security-relevant behavior

## [Unreleased]

### Breaking changes

- Changed repository-maintenance approval behavior relative to the prepared `0.9.0` governance contract: low- and moderate-risk repository changes may now be maintainer self-reviewed after permanent CI when no independent-review gate applies. Independent review remains mandatory for high/critical risk, any breaking repository change, the final `1.0.0` compatibility approval, and stable-maturity commitments. This change affects repository maintenance governance only; it does not weaken adopter-facing engineering or security standards.

### Normative changes

- Added a complete C# language package and direct `csharp` skill covering compiler/language boundaries, nullable types, API compatibility, async and concurrency, resource ownership, performance, security, reproducible builds and dependencies, testing, documentation, observability, scripting, source generation, reflection, native interop, unsafe code, and completion evidence.
- Separated C# language responsibility from the existing .NET SDK/runtime/application package and updated ASP.NET Core plus representative C# examples to compose both packages.
- Added a VCF PowerCLI automation standard under the VMware vSphere and ESXi package, composed it with the general PowerShell package, and added adoption, review, and completion-evidence requirements for dependency provenance, endpoint and certificate identity, explicit connections, stable inventory targeting, confirmation, asynchronous tasks, cleanup, structured results, and isolated testing.
- Extended the project-manifest version 1 contract with version `1.1.0` and optional `virtualization`, `operatingSystems`, and `networking` package arrays while retaining validation of existing version `1.0.0` manifests.
- Synchronized profile, language, discipline, framework, platform, governance, template, and example composition guidance so adopters must explicitly select or justify omission of virtualization, operating-system, and networking standards.
- Added collection-level language, framework, and platform skills that route agent work to the applicable standards packages and require advanced, version-compatible implementation, layered validation, and explicit completion evidence.
- Added a virtualization engineering skill and complete baseline packages for VMware vSphere/ESXi, XenServer/Citrix Hypervisor, Proxmox VE, XCP-ng, KVM/libvirt, Nutanix AHV, Microsoft Hyper-V, Red Hat Virtualization, and Oracle Linux KVM/OLVM.
- Added shared virtualization requirements for target identity, supported automation interfaces, discovery, validation, dry-run or planning, authorization, bounded execution, actual-state verification, backup, recovery, lifecycle, and migration.
- Added an operating-system engineering skill and complete baseline packages for Windows Server 2016/2019/2022/2025, Windows 10/11 clients, the RHEL family, Ubuntu Server/Desktop, Debian, SUSE Linux Enterprise, Oracle Linux, macOS, and FreeBSD.
- Added shared OS requirements for authoritative target and policy identity, current lifecycle verification, trusted repositories and artifacts, staged/canary rollout, access preservation, bounded automation and restarts, actual-state verification, recovery, upgrades, migrations, destructive actions, and decommissioning.
- Added a network engineering skill and complete baseline packages for HPE Aruba Networking, Cisco, Juniper Networks, and Broadcom Brocade Fabric OS/SANnav, including explicit ownership triage for legacy Brocade Ethernet/IP product lines.
- Added shared networking requirements for authoritative device/controller/fabric identity, configuration ownership, management/control/data-plane separation, transactional changes, topology and redundancy safety, bounded execution, actual-state verification, firmware lifecycle, rollback, recovery, and migration/refresh.

### Editorial changes

- Added a concise pull request template for summary, impact, validation, limitations, and maintainer self-review without introducing heavyweight governance records.

### Tooling changes

- Extended skill-validation regression expectations for the registered C# direct skill and the eleventh language-package route.
- Updated `generate-manifest` and `compose-agents` to version `1.1.0` so they validate, emit, compose, and report selected virtualization, operating-system, and networking packages; added backward-compatibility, positive, and negative tests.
- Added a permanent read-only skill validator for metadata, progressive disclosure, package-routing coverage, root-manifest registration, safe local links, and optional agent UI metadata.
- Integrated skill validation and its positive, boundary, negative, and deterministic tests into the complete validation pipeline.
- Extended the repository skill-collection regression test to cover the virtualization router and its nine package routes.
- Extended the skill-collection regression test to cover the operating-system router and its nine package routes.
- Extended the skill-collection regression test to cover the networking router and its four package routes.

### Security

- Added C# safeguards for trust-boundary validation, secret and diagnostic disclosure, unsafe deserialization, command and path injection, certificate bypass, unbounded concurrency and resource growth, broad analyzer suppression, floating build-time code, unsafe/native lifetime errors, and attacker-selected reflection or runtime code generation.
- Added PowerCLI safeguards against certificate-validation bypass, ambiguous ambient connections, persistent configuration weakening, automatic operational module changes, name-only targeting, leaked authenticated sessions, unbounded tasks, unsafe retries, unrelated session cleanup, and success claims without actual-state verification.
- Made infrastructure-control boundaries explicit in manifests and generated composition indexes so material hypervisor, host operating-system, and network standards are less likely to be silently omitted from review.
- Added virtualization safeguards for privileged control planes, ambiguous object selection, bulk or destructive actions, management-plane exposure, network and storage changes, snapshots and checkpoints, backup and restore, device passthrough, unsupported lifecycle states, and cross-platform migration.
- Added OS safeguards for privileged fleet actions, ambiguous target selection, repository and package trust, security-control bypass, identity and remote-access loss, restart and partial-fleet failure, encryption and recovery material, destructive endpoint actions, unsupported lifecycle states, and user-data privacy.
- Added networking safeguards for high-blast-radius control planes, ambiguous device/controller/fabric scope, conflicting configuration owners, management loss, loops and convergence failure, redundancy sequencing, policy exposure, unsupported firmware/hardware, Fibre Channel zoning and multipath changes, and sensitive topology or support data.

### Deprecations

- None.

### Migration notes

- Repository maintainers following the prepared `0.9.0` maintenance policy should update local review expectations: low- and moderate-risk repository maintenance may be self-reviewed after permanent CI unless an independent-review gate applies. Existing adopter-facing package requirements, security controls, and project human-review requirements are unchanged by this repository-maintenance policy update.
- Existing `languages/dotnet` adopters remain valid. Repositories with C# source should add `languages/csharp` at their next standards update; modern C# projects normally compose `csharp` for language semantics and `dotnet` for SDK, target framework, CLR, MSBuild, NuGet, hosting, and publishing behavior.
- Existing `VMware.PowerCLI` adopters are not required to perform an immediate or blind rename. They should inventory the distribution and child modules, verify the current Broadcom-supported migration and compatibility path, test the selected `VCF.PowerCLI` constraint, and update dependency records separately from operational execution.
- Existing project-manifest version `1.0.0` instances remain valid. Producers using the new package arrays must emit `schemaVersion: "1.1.0"`; consumers that depend on those arrays must use schema and composition tooling version `1.1.0` or later.
- Existing adopters may continue using `AGENTS.md` and package entry points directly. Agents that support skills may additionally use `languages/SKILL.md`, `frameworks/SKILL.md`, `platforms/SKILL.md`, `virtualization/SKILL.md`, `operating-systems/SKILL.md`, and `networking/SKILL.md` without changing existing package paths.

### Known limitations

- The C# package and templates were validated as repository content only because a .NET SDK/compiler was unavailable in the authoring environment. No C# compilation, NuGet restore, analyzer execution, runtime test, benchmark, native-platform validation, or framework integration test was performed.
- The PowerCLI standard was validated as repository content only. No live vCenter or ESXi connection, module installation, product compatibility certification, or integration test was performed.
- Project-manifest package arrays record reviewed selection intent only. Schema validity and generated composition bundles do not prove that every applicable infrastructure boundary was identified, tailored, authorized, or operationally validated.

## [0.9.0] - 2026-07-13

### Breaking changes

- None. This is the first repository-level release contract. Existing public paths are treated as the initial pre-1.0 compatibility baseline.

### Normative changes

- Established the repository governance operating model, risk classification, exception process, completion evidence, secure-development expectations, human review, production readiness, threat modeling, and vulnerability response.
- Completed language, discipline, framework, platform, project-profile, template, schema, example, and toolchain collections.
- Added repository licensing under Apache-2.0.
- Added repository maintainer, ownership, CODEOWNERS, specialist-review, merge-authority, emergency-change, inactivity, and succession rules.
- Added repository-wide semantic versioning, deprecation, migration, maturity-promotion, release-evidence, tag, and GitHub Release requirements.

### Editorial changes

- Expanded root and package README files into adoption and maintenance guides.
- Added catalogs, manifests, selection guides, examples, and explicit non-production boundaries throughout the repository.

### Tooling changes

- Added repository, link, schema, template, tool, and release validation.
- Added deterministic project-manifest generation and traceable standards-bundle composition.
- Added deterministic release ZIP and TAR archives, release manifests, migration-note packaging, and SHA-256 checksums.
- Added a unified validation runner and central unit-test suite.

### Security

- Added offline schema validation and remote-reference rejection.
- Added committed-cache and temporary-artifact checks.
- Added path containment, dry-run, overwrite protection, and atomic staging for writing tools.
- Added restricted release workflow permissions and tag validation.

### Deprecations

- None.

### Migration notes

- See [`releases/migrations/0.9.0.md`](releases/migrations/0.9.0.md).

[Unreleased]: https://github.com/AIAllTheThingz/Public-Access-Agents/compare/v0.9.0...HEAD
[0.9.0]: https://github.com/AIAllTheThingz/Public-Access-Agents/releases/tag/v0.9.0
