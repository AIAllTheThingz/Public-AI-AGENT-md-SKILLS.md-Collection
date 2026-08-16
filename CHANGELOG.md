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

Post-release maintenance after `0.10.0` publication:

- Recorded durable `0.10.0` publication verification and reconciled repository documentation with the published Git tag and GitHub Release.
- Advanced the forward-only next intended publication to `1.0.0-rc.1` for the evidence-backed compatibility-gate program.
- Added an explicit legacy Windows PowerShell 5.1 adoption overlay from downstream pilot evidence while preserving PowerShell 7 as the default for new work; `pwsh` validation is not accepted as proof of Windows PowerShell 5.1 runtime compatibility.
- Corrected `generate-manifest --include-profile-required` so selected secondary profiles contribute their discipline links as well as the primary profile; the change is additive and preserves the published `0.10.0` primary-profile expansion behavior.
- Added shared package-level adoption tests for the initial C#, PowerShell, and Terraform/OpenTofu maturity candidates, covering positive composition, accountable source evidence, incomplete adoption, invalid selection, and overwrite failure behavior.
- Completed three representative real downstream `v0.10.0` adoption pilots across application/service, internal automation, and mixed-system repositories; recorded exact command outcomes and limitations, fixed the Windows PowerShell 5.1 and secondary-profile adoption defects found by the pilots, and added durable downstream evidence under `adoption-pilots/`.
- Completed the first evidence-backed maturity review cohort: proposed C# `baseline` → `stable` based on package tests, two real downstream adoptions, current source review, compatibility inventory, and independent specialist merge gating; deferred PowerShell and Terraform/OpenTofu without changing their `baseline` maturity because their evidence sets remain incomplete.

## [0.10.0] - 2026-08-16

The `0.10.0` release is the first forward-only publication candidate after the prepared-but-unpublished `0.9.0` baseline. Current `main` must not be retroactively tagged as `v0.9.0`.

### Breaking changes

- Changed repository-maintenance approval behavior relative to the prepared `0.9.0` governance contract: low- and moderate-risk repository changes may now be maintainer self-reviewed after permanent CI when no independent-review gate applies. Independent review remains mandatory for high/critical risk, any breaking repository change, the final `1.0.0` compatibility approval, and stable-maturity commitments. This change affects repository maintenance governance only; it does not weaken adopter-facing engineering or security standards.
- Changed canonical schema and tool-result `$id` identifiers from raw GitHub URLs under `AIAllTheThingz/Public-Access-Agents` to `AIAllTheThingz/Public-AI-Governance`. Schema validation structure is unchanged, but consumers that persist or compare exact `$id` strings must migrate those identifiers. This is an explicit pre-1.0 breaking machine-readable contract change.
- Narrowed the supported Oracle Linux Virtualization Manager (OLVM) boundary: OLVM is treated as a legacy managed boundary tied to supported Oracle Linux 8 estates and must not be inferred as the management plane for Oracle Linux 9/10. Adopters that previously applied the prepared 0.9 guidance to OLVM-managed Oracle Linux 9/10 environments must migrate or re-scope that adoption.

### Normative changes

- Added a complete C# language package and direct `csharp` skill covering compiler/language boundaries, nullable types, API compatibility, async and concurrency, resource ownership, performance, security, reproducible builds and dependencies, testing, documentation, observability, scripting, source generation, reflection, native interop, unsafe code, and completion evidence.
- Separated C# language responsibility from the existing .NET SDK/runtime/application package and updated ASP.NET Core plus representative C# examples to compose both packages.
- Added a VCF PowerCLI automation standard under the VMware vSphere and ESXi package, composed it with the general PowerShell package, and added adoption, review, and completion-evidence requirements for dependency provenance, endpoint and certificate identity, explicit connections, stable inventory targeting, confirmation, asynchronous tasks, cleanup, structured results, and isolated testing.
- Extended the project-manifest version 1 contract with version `1.1.0` and optional `virtualization`, `operatingSystems`, and `networking` package arrays while retaining validation of existing version `1.0.0` manifests.
- Synchronized profile, language, discipline, framework, platform, governance, template, and example composition guidance so adopters must explicitly select or justify omission of virtualization, operating-system, and networking standards.
- Added collection-level language, framework, and platform skills that route agent work to the applicable language packages and require advanced, version-compatible implementation, layered validation, and explicit completion evidence.
- Added a virtualization engineering skill and complete baseline packages for VMware vSphere/ESXi, XenServer/Citrix Hypervisor, Proxmox VE, XCP-ng, KVM/libvirt, Nutanix AHV, Microsoft Hyper-V, Red Hat Virtualization, and Oracle Linux KVM/OLVM.
- Added shared virtualization requirements for target identity, supported automation interfaces, discovery, validation, dry-run or planning, authorization, bounded execution, actual-state verification, backup, recovery, lifecycle, and migration.
- Updated XenServer lifecycle guidance across package and operations standards so XenServer 9 is the current GA family while XenServer 8/Citrix Hypervisor references are treated as installed-estate, compatibility, or migration boundaries rather than greenfield defaults.
- Updated Red Hat Virtualization guidance across README, agent, and operations standards to the current Extended Life Phase boundary: limited support, no new bug/security fixes or hardware enablement, and OpenShift Virtualization as the continuity roadmap. Removed the unsupported repository claim that attached an exact August 31, 2026 software-fix date.
- Updated Oracle Linux KVM guidance across README, agent, and operations standards so current Oracle Linux 9/10 KVM is separated from OLVM, which current Oracle guidance ties to an Oracle Linux 8 legacy managed boundary. OLVM must not be inferred as the current Oracle Linux 9/10 management plane.
- Added an operating-system engineering skill and complete baseline packages for Windows Server 2016/2019/2022/2025, Windows 10/11 clients, the RHEL family, Ubuntu Server/Desktop, Debian, SUSE Linux Enterprise, Oracle Linux, macOS, and FreeBSD.
- Added shared OS requirements for authoritative target and policy identity, current lifecycle verification, trusted repositories and artifacts, staged/canary rollout, access preservation, bounded automation and restarts, actual-state verification, recovery, upgrades, migrations, destructive actions, and decommissioning.
- Added a network engineering skill and complete baseline packages for HPE Aruba Networking, Cisco, Juniper Networks, and Broadcom Brocade Fabric OS/SANnav, including explicit ownership triage for legacy Brocade Ethernet/IP product lines.
- Added shared networking requirements for authoritative device/controller/fabric identity, configuration ownership, management/control/data-plane separation, transactional changes, topology and redundancy safety, bounded execution, actual-state verification, firmware lifecycle, rollback, recovery, and migration/refresh.

### Editorial changes

- Added a concise pull request template for summary, impact, validation, limitations, and maintainer self-review without introducing heavyweight governance records.
- Reconciled the project/library identity (`Public Access Agents`) with the canonical GitHub repository (`AIAllTheThingz/Public-AI-Governance`) and documented the prepared-but-unpublished `0.9.0` state plus the forward-only `0.10.0` release plan.
- Documented a lightweight authoritative-source maintenance model that separates accountable source-review dates from ordinary repository modification dates and treats missing review evidence as explicit `NotRun` rather than inferred success.
- Replaced coarse collection-level source-review entries with package/scoped records and made `SOURCE_REVIEWS.json` plus durable `source-reviews/` evidence the accountable source-review date authority, removing duplicated hard-coded dates from affected package READMEs.

### Tooling changes

- Hardened permanent validation and release workflows with immutable GitHub Action commit pins, Ubuntu 24.04 hosted-runner boundaries, an explicit Python 3.13 runtime, and SHA-256 hash-locked validation dependencies.
- Split release validation/artifact construction from GitHub Release publication so write permission is held only by the publication job; transferred built artifacts between jobs and re-verified `SHA256SUMS.txt` before publication.
- Hardened historical prepared/unpublished release blocking so a forbidden requested tag remains explicitly blocked after the canonical repository `VERSION` advances to a later release candidate.
- Added Dependabot maintenance for GitHub Actions and the direct Python validation dependencies.
- Updated `validate-tools` to version `1.3.2` so it structurally parses workflow YAML, validates full Git commit pins and immutable Docker OCI digests, rejects floating hosted runner images, and verifies exact direct-dependency/hash-lock synchronization while accepting ordinary inline requirement comments.
- Added regression coverage for dependency-lock drift, inline requirement comments, quoted YAML scalars, legal YAML key-spacing variants, immutable Docker digests, floating action refs, and floating hosted runners.
- Extended skill-validation regression expectations for the registered C# direct skill and the eleventh language-package route.
- Updated `generate-manifest` and `compose-agents` to version `1.1.0` so they validate, emit, compose, and report selected virtualization, operating-system, and networking packages; added backward-compatibility, positive, and negative tests.
- Added a permanent read-only skill validator for metadata, progressive disclosure, package-routing coverage, root-manifest registration, safe local links, and optional agent UI metadata.
- Integrated skill validation and its positive, boundary, negative, and deterministic tests into the complete validation pipeline.
- Extended the repository skill-collection regression test to cover the virtualization router and its nine package routes.
- Extended the repository skill-collection regression test to cover the operating-system router and its nine package routes.
- Extended the repository skill-collection regression test to cover the networking router and its four package routes.
- Reconciled canonical repository URLs used by release documentation and machine-readable identifiers with `AIAllTheThingz/Public-AI-Governance`; artifact filenames retain the stable `Public-Access-Agents-<VERSION>` project prefix.
- Added `SOURCE_REVIEWS.json` and the offline `check-freshness` tool to track authoritative-source review intervals and report recorded review-date state as `Passed`, `Warning`, or `NotRun` while explicitly reporting live external-source verification as `NotRun`.
- Added `check-freshness` to the permanent aggregate validation pipeline without converting warning-only maintenance state into ordinary CI failure; strict mode remains available for deliberate blocking checks.
- Added a weekly and manually dispatchable source-freshness workflow with immutable action pins, an explicit Ubuntu 24.04/Python 3.13 boundary, GitHub Actions summaries, warning annotations, and no live vendor-source fetches.
- Added a standards-correction/stale-source issue form and positive, warning, `NotRun`, strict, invalid-date, path-containment, registry, and workflow regression coverage for the freshness model.
- Updated `validate-tools` to version `1.3.3`, `validate-all` to version `1.3.0`, and the toolchain manifests/catalog to include the new freshness package and workflow.
- Added source-review evidence regressions that require package/scoped records, preserve explicit `NotRun` coverage for unreviewed packages, pin reviewed evidence to an immutable repository revision, retain current lifecycle corrections in normative files, and prevent duplicated package review-date drift.

### Security

- Reduced workflow supply-chain mutability by pinning third-party actions to immutable references and installing CI/release Python dependencies exclusively from a SHA-256-hashed lock.
- Reduced release-token exposure by keeping `contents: write` out of the validation/build job and granting it only to the publication job.
- Added workflow validation that detects floating repository-action refs, floating `*-latest` hosted runners, mutable Docker action references, invalid workflow YAML, and validation dependency-lock drift.
- Added C# safeguards for trust-boundary validation, secret and diagnostic disclosure, unsafe deserialization, command and path injection, certificate bypass, unbounded concurrency and resource growth, broad analyzer suppression, floating build-time code, unsafe/native lifetime errors, and attacker-selected reflection or runtime code generation.
- Added PowerCLI safeguards against certificate-validation bypass, ambiguous ambient connections, persistent configuration weakening, automatic operational module changes, name-only targeting, leaked authenticated sessions, unbounded tasks, unsafe retries, unrelated session cleanup, and success claims without actual-state verification.
- Made infrastructure-control boundaries explicit in manifests and generated composition indexes so material hypervisor, host operating-system, and network standards are less likely to be silently omitted from review.
- Added virtualization safeguards for privileged control planes, ambiguous object selection, bulk or destructive actions, management-plane exposure, network and storage changes, snapshots and checkpoints, backup and restore, device passthrough, unsupported lifecycle states, and cross-platform migration.
- Added OS safeguards for privileged fleet actions, ambiguous target selection, repository and package trust, security-control bypass, identity and remote-access loss, restart and partial-fleet failure, encryption and recovery material, destructive endpoint actions, unsupported lifecycle states, and user-data privacy.
- Added networking safeguards for high-blast-radius control planes, ambiguous device/controller/fabric scope, conflicting configuration owners, management loss, loops and convergence failure, redundancy sequencing, policy exposure, unsupported firmware/hardware, Fibre Channel zoning and multipath changes, and sensitive topology or support data.
- Restricted source-freshness metadata to public HTTPS source references and repository-contained scopes; the default checker performs no network access and does not accept commit timestamps as source-review evidence.

### Deprecations

- None.

### Migration notes

- Repository maintainers following the prepared `0.9.0` maintenance policy should update local review expectations: low- and moderate-risk repository maintenance may be self-reviewed after permanent CI only when no independent-review gate applies; any breaking repository change still requires independent specialist review. Existing adopter-facing package requirements, security controls, and project human-review requirements are unchanged by this repository-maintenance policy update.
- `0.9.0` was prepared but never published. Adopters must record the actual source commit they consumed and must not claim a `v0.9.0` source tag. Current `main` must not be retroactively tagged as `v0.9.0`; the intended next publication is `0.10.0`.
- Consumers that persist exact schema or tool-result `$id` values from the former raw `Public-Access-Agents` GitHub path must migrate them to the corresponding `Public-AI-Governance` identifiers and re-run integration/schema tests.
- Maintainers changing validation dependencies must update `tools/validate-schemas/requirements.txt`, regenerate `requirements.lock` with the documented Python 3.13 boundary, and commit the resulting SHA-256 hashes; CI intentionally rejects direct-dependency/lock drift.
- Existing `languages/dotnet` adopters remain valid. Repositories with C# source should add `languages/csharp` at their next standards update; modern C# projects normally compose `csharp` for language semantics and `dotnet` for SDK, target framework, CLR, MSBuild, NuGet, hosting, and publishing behavior.
- Existing `VMware.PowerCLI` adopters are not required to perform an immediate or blind rename. They should inventory the distribution and child modules, verify the current Broadcom-supported migration and compatibility path, test the selected `VCF.PowerCLI` constraint, and update dependency records separately from operational execution.
- Existing project-manifest version `1.0.0` instances remain valid. Producers using the new package arrays must emit `schemaVersion: "1.1.0"`; consumers that depend on those arrays must use schema and composition tooling version `1.1.0` or later.
- Existing adopters may continue using `AGENTS.md` and package entry points directly. Agents that support skills may additionally use `languages/SKILL.md`, `frameworks/SKILL.md`, `platforms/SKILL.md`, `virtualization/SKILL.md`, `operating-systems/SKILL.md`, and `networking/SKILL.md` without changing existing package paths.
- XenServer adopters should treat XenServer 9 as the current GA family and explicitly classify older XenServer/Citrix Hypervisor estates as compatibility/migration boundaries before lifecycle work.
- RHV adopters should treat the platform as Extended Life legacy scope, verify exact entitlement/support, protect recovery, and prioritize a supported migration path rather than assuming normal bug/security-fix delivery continues.
- Oracle Linux KVM adopters should distinguish current Oracle Linux KVM from OLVM. Existing OLVM estates must verify the exact OLVM/Oracle Linux 8 support boundary and should not infer OLVM support for Oracle Linux 9 or 10.
- Source-review metadata is additive. Maintainers should populate a date only after actually reviewing the listed authoritative sources; unreviewed package records remain `lastReviewed: null` and must not be inferred current.

### Known limitations

- No repository release has been published yet. The prepared `0.9.0` tag/release does not exist, and the next intended publication is `0.10.0` after final release-state preparation.
- The release publication job is tag-triggered and was not exercised by pull-request validation; publication remains `NotRun` until a reconciled release tag is deliberately created.
- Immutable action and dependency references reduce mutation risk but do not by themselves establish third-party provenance or vulnerability-free dependencies.
- The source-freshness checker evaluates recorded review dates and metadata only; it does not fetch or compare external vendor content. The 2026-08-15 accountable source review covered the records dated that day, while JavaScript/TypeScript, Python, Java, Go, Rust, Bash, SQL, and the vSphere product boundary remain explicitly `NotRun`. Manual `source-freshness` workflow dispatch is `Blocked` through the connected GitHub tool surface.
- The C# package and templates were validated as repository content only because a .NET SDK/compiler was unavailable in the authoring environment. No C# compilation, NuGet restore, analyzer execution, runtime test, benchmark, native-platform validation, or framework integration test was performed.
- The PowerCLI standard was validated as repository content only. No live vCenter or ESXi connection, module installation, product compatibility certification, or integration test was performed.
- Project-manifest package arrays record reviewed selection intent only. Schema validity and generated composition bundles do not prove that every applicable infrastructure boundary was identified, tailored, authorized, or operationally validated.

## [0.9.0] - 2026-07-13

**Prepared baseline only.** No `v0.9.0` Git tag and no `0.9.0` GitHub Release were ever published. This entry records the repository release program that was prepared on 2026-07-13; it does not identify a published immutable source boundary.

### Breaking changes

- None. This was prepared as the first repository-level release contract. Existing public paths are treated as the initial pre-1.0 compatibility baseline.

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

[Unreleased]: https://github.com/AIAllTheThingz/Public-AI-Governance/commits/main
[0.9.0]: releases/0.9.0.md
