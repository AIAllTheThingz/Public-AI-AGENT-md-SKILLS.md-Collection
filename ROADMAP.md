# Roadmap

## Completed foundation

- Public repository and contribution model
- Apache License 2.0 repository licensing and contribution terms
- Repository maintainer and ownership model:
  - current maintainer roster
  - CODEOWNERS review routing
  - review ownership by repository area
  - independent specialist-review requirements
  - merge and self-merge authority
  - emergency-change and post-merge review rules
  - inactivity, appointment, removal, and succession rules
  - branch-protection and enforcement expectations
- Repository-wide versioning and release program:
  - canonical repository `VERSION`
  - changelog and change classification
  - Semantic Versioning rules for standards, schemas, templates, tools, and stable paths
  - pre-1.0 and `1.0.0` compatibility gates
  - 90-day and 180-day deprecation windows
  - versioned release and migration notes
  - machine-readable release state
  - package maturity policy and review records
  - deterministic ZIP and TAR.GZ release artifacts
  - SHA-256 checksums and release manifest
  - tag validation and tag-driven GitHub Release workflow
  - release validation in permanent CI
- Lightweight source-currency maintenance:
  - accountable source-review registry in `SOURCE_REVIEWS.json`
  - offline `check-freshness` validation with `Passed`, `Warning`, `NotRun`, and `Invalid` maintenance states
  - scheduled and manually dispatchable freshness workflow
  - stale-source and standards-correction issue intake
- Root agent instructions
- Complete governance operating system
- Complete engineering discipline packages
- Complete language packages
- Complete framework packages
- Complete platform packages for:
  - Containers
  - Kubernetes
  - Terraform and OpenTofu
  - Microsoft Azure
  - Amazon Web Services
  - Google Cloud Platform
- Platform selection, shared-responsibility, change-lifecycle, and decision-matrix guidance
- Complete virtualization packages for:
  - VMware vSphere and ESXi
  - XenServer and Citrix Hypervisor
  - Proxmox VE
  - XCP-ng
  - KVM and libvirt
  - Nutanix AHV
  - Microsoft Hyper-V
  - Red Hat Virtualization
  - Oracle Linux KVM and Oracle Linux Virtualization Manager
- Virtualization selection, shared-responsibility, change-lifecycle, automation, recovery, and migration guidance
- Complete operating-system packages for:
  - Windows Server 2016, 2019, 2022, and 2025
  - Windows 10 and Windows 11 clients
  - Red Hat Enterprise Linux family
  - Ubuntu Server and Desktop
  - Debian
  - SUSE Linux Enterprise
  - Oracle Linux
  - macOS
  - FreeBSD
- Operating-system selection, current-release, shared-responsibility, change-lifecycle, security, recovery, upgrade, migration, and decommission guidance
- Complete networking packages for:
  - HPE Aruba Networking
  - Cisco networking
  - Juniper Networks
  - Broadcom Brocade Fabric OS and SANnav, with legacy Brocade Ethernet ownership triage
- Network vendor/ownership selection, shared-responsibility, change-lifecycle, control-plane safety, topology, firmware, recovery, and migration/refresh guidance
- Complete project profile packages for:
  - Web API
  - Web application
  - Worker service
  - Command-line tool
  - Desktop application
  - Mobile application
  - Serverless function
  - Data pipeline
  - Public library
  - Internal automation
  - Multi-tenant SaaS
  - Security tool
  - AI agent application
- Profile selection, composition, risk-and-evidence, lifecycle, and decision-matrix guidance
- Complete schema system:
  - six rolling Draft 2020-12 contracts
  - six backward-compatible major-version 1 contract paths
  - versioning and compatibility policy
  - extension and migration guidance
  - positive and negative contract examples
  - executable schema and repository-instance validation
- Complete template library:
  - root and nested agent instructions
  - architecture, risk, threat, exception, and completion records
  - project manifest, test evidence, and artifact record templates
  - authorization, human review, and production-readiness records
  - release, rollback, recovery, and operational runbook templates
  - selection, authoring, customization, placeholder, lifecycle, validation, and completion guidance
  - completed examples and executable template validation
- Complete repository toolchain:
  - repository structure, link, freshness, skill, schema, template, tool, and release validation
  - deterministic project-manifest generation
  - traceable standards-bundle composition across profile, language, discipline, framework, platform, virtualization, operating-system, and networking packages
  - deterministic release artifact generation
  - shared JSON result and exit-code contract
  - unified validation runner
  - central unit-test suite
  - permanent CI integration
  - tool development, security, troubleshooting, release, and compatibility guidance
- Complete standards-composition examples
- Schema-shaped completion, test, artifact, risk, and exception evidence
- Root and nested `AGENTS.md` composition examples

## Current release direction

- `0.9.0` remains a prepared baseline that was never published and must not be retroactively tagged.
- `0.10.0` was published as `v0.10.0` on 2026-08-16 from source commit `83c73f3ab9a049ff2321d463164fcf98fb453a9c`.
- The next intended publication is `1.0.0-rc.1` after package-level adoption tests, representative downstream pilots, initial maturity decisions, and the compatibility gate are complete.
- The `1.0.0-rc.1` source candidate is now prepared and permanently validated. Its functional candidate is `89a0470a3be4902f0c70eb31d396655dde4c8d7c`, with readiness evidence in `releases/rc-readiness/1.0.0-rc.1.md`. Independent specialist approval and deliberate publication remain outstanding.

## Next maturity work

1. **Completed:** Add automated package-level adoption tests for selected high-value packages, including positive, negative, boundary, and failure-path exercises required by the maturity policy.
2. **Completed:** Run representative downstream adoption pilots and convert observed friction into focused corrections.
3. **Completed for the initial release-candidate cohort:** Complete package maturity reviews that promote only qualified baseline components to stable; C# is stable while PowerShell and Terraform/OpenTofu remain baseline under recorded decisions.
4. Add additional active maintainers and independent specialist reviewers as participation grows.
5. Configure and verify the GitHub-host controls recorded as Blocked under issue #52 when an authorized administration surface becomes available.
6. **In progress:** Define the intended stable compatibility surface and prepare and review `1.0.0-rc.1`; the source candidate and compatibility evidence are complete, while independent specialist approval and publication remain.
7. Publish final `1.0.0` only after at least one RC is published and available for review and the compatibility, adoption, maturity, source-review, security, artifact-verification, and independent-review gates are satisfied.
