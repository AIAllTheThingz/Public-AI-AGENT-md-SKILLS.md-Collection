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

- `0.9.0` is a prepared baseline that was never published.
- Current `main` must not be retroactively tagged as `v0.9.0`.
- The next intended publication is `0.10.0` after source-currency review, final release preparation, and the independent specialist review required for its breaking changes.

## Next maturity work

1. Perform accountable authoritative-source reviews and refine freshness coverage for time-sensitive packages.
2. Prepare the first real `v0.10.0` release, obtain the independent specialist review required for its breaking changes, publish only after that gate passes, then independently verify the published tag, artifacts, checksums, and release manifest.
3. Add automated package-level adoption tests for selected high-value packages, including positive, negative, and failure-path exercises required by the maturity policy.
4. Run representative external or independent adoption pilots and convert observed friction into focused fixes.
5. Complete package maturity reviews that promote only qualified baseline packages to stable.
6. Add additional active maintainers and independent specialist reviewers as participation grows.
7. Configure and verify lightweight branch, tag, and private-reporting settings where GitHub administration access permits it.
8. Add current provider-service compatibility matrices and migration guidance where adoption evidence shows they are useful.
9. Add executable validation templates for containers, Kubernetes, infrastructure as code, and cloud platforms where they close demonstrated gaps.
10. Add additional composition examples for data pipelines, internal automation, public libraries, security tools, and AI agent applications where pilots identify missing examples.
11. Add policy-dependency checks where they prevent demonstrated configuration or composition mistakes.
12. Define the intended stable compatibility surface and prepare and review at least one `1.0.0-rc.N` release.
13. Publish `1.0.0` only after the compatibility, adoption, maturity, source-review, and independent-review gates are satisfied.
