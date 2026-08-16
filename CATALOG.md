# Standards Catalog

This catalog lists the standards available for composition into a project.

## Agent skills

- [Language engineering skill](languages/SKILL.md)
- [C# engineering skill](languages/csharp/SKILL.md)
- [Framework engineering skill](frameworks/SKILL.md)
- [Platform engineering skill](platforms/SKILL.md)
- [Virtualization engineering skill](virtualization/SKILL.md)
- [Operating-system engineering skill](operating-systems/SKILL.md)
- [Network engineering skill](networking/SKILL.md)

These collection-level and direct language skills select and compose the detailed packages below. They supplement rather than replace repository governance and scoped `AGENTS.md` instructions.

## Governance

The governance system defines authority, precedence, risk, evidence, review, exceptions, secure development, production readiness, threat modeling, vulnerability response, and policy lifecycle across every package in this repository.

| Standard | Purpose |
|---|---|
| [Governance index](governance/README.md) | Selection, precedence, operating model, adoption, evidence states, and maintenance |
| [Organization Contract](governance/ORGANIZATION_CONTRACT.md) | Defines precedence, non-negotiable controls, authority, and accountability |
| [Agent Working Method](governance/AGENT_WORKING_METHOD.md) | Defines discovery, planning, implementation, validation, and reporting |
| [Risk Classification](governance/RISK_CLASSIFICATION.md) | Scales review, testing, authorization, rollback, and evidence |
| [Completion Evidence](governance/COMPLETION_EVIDENCE.md) | Defines proof required before claiming completion |
| [Exception Process](governance/EXCEPTION_PROCESS.md) | Provides a time-bounded, reviewed path for deviations |
| [AI-Generated Code Policy](governance/AI_GENERATED_CODE_POLICY.md) | Defines responsibility, verification, provenance, and review for AI-assisted work |
| [Human Review Policy](governance/HUMAN_REVIEW_POLICY.md) | Defines work requiring accountable human review and approval |
| [Production Readiness](governance/PRODUCTION_READINESS.md) | Defines operational, recovery, support, and go-live gates |
| [Secure Development Policy](governance/SECURE_DEVELOPMENT_POLICY.md) | Integrates security into design, implementation, testing, delivery, and maintenance |
| [Threat Modeling Policy](governance/THREAT_MODELING_POLICY.md) | Defines threat-model triggers, contents, mitigations, and residual risk |
| [Vulnerability Response](governance/VULNERABILITY_RESPONSE.md) | Defines confidential intake, triage, containment, remediation, verification, and closure |

See the [governance policy map](governance/POLICY_MAP.md), [adoption guide](governance/ADOPTION_GUIDE.md), [operating model](governance/OPERATING_MODEL.md), and [decision matrix](governance/GOVERNANCE_DECISION_MATRIX.md).

## Engineering disciplines

- [Application Security](disciplines/application-security/)
- [Architecture and System Design](disciplines/architecture/)
- [Testing and Quality Engineering](disciplines/testing/)
- [API Engineering](disciplines/api-engineering/)
- [Integration Engineering](disciplines/integration/)
- [Database Engineering](disciplines/database/)
- [Data Engineering](disciplines/data-engineering/)
- [Accessibility](disciplines/accessibility/)
- [Privacy and Data Governance](disciplines/privacy/)
- [Observability](disciplines/observability/)
- [Site Reliability Engineering](disciplines/sre/)
- [Documentation](disciplines/documentation/)
- [CI/CD](disciplines/ci-cd/)
- [Software Supply Chain](disciplines/supply-chain/)
- [Release Engineering](disciplines/release-engineering/)

## Languages

- [PowerShell 7.x](languages/powershell/)
- [C#](languages/csharp/)
- [.NET 10 LTS](languages/dotnet/)
- [JavaScript and TypeScript](languages/javascript-typescript/)
- [Python](languages/python/)
- [Java](languages/java/)
- [Go](languages/go/)
- [Rust](languages/rust/)
- [Bash](languages/bash/)
- [SQL](languages/sql/)
- [Terraform and OpenTofu](languages/terraform-opentofu/)

C# is the first language package promoted from `baseline` to `stable` through the evidence-backed maturity process. Other language-package maturity remains as declared in the package metadata, language index, source-review registry, and maturity-review records.

## Platforms

Platform packages are complete, independently adoptable overlays for execution, deployment, identity, network, data, state, policy, observability, resilience, recovery, cost, capacity, quota, and operational ownership.

- [Containers](platforms/containers/)
- [Kubernetes](platforms/kubernetes/)
- [Terraform and OpenTofu](platforms/terraform/)
- [Microsoft Azure](platforms/azure/)
- [Amazon Web Services](platforms/aws/)
- [Google Cloud Platform](platforms/gcp/)

See the [platforms index](platforms/README.md) for selection, shared responsibility, change lifecycle, decision scaling, adoption, validation, and maintenance guidance.

## Virtualization

Virtualization packages are complete, independently adoptable overlays for hypervisor managers, clusters and pools, hosts, virtual machines, virtual networking and storage, backup and recovery, automation, lifecycle, and migration.

- [VMware vSphere and ESXi](virtualization/vsphere-esxi/)
- [XenServer and Citrix Hypervisor](virtualization/xenserver-citrix-hypervisor/)
- [Proxmox VE](virtualization/proxmox-ve/)
- [XCP-ng](virtualization/xcp-ng/)
- [KVM and libvirt](virtualization/kvm-libvirt/)
- [Nutanix AHV](virtualization/nutanix-ahv/)
- [Microsoft Hyper-V](virtualization/microsoft-hyper-v/)
- [Red Hat Virtualization](virtualization/red-hat-virtualization/)
- [Oracle Linux KVM](virtualization/oracle-linux-kvm/)

See the [virtualization index](virtualization/README.md) for selection, shared responsibility, safe change phases, automation, lifecycle, recovery, and migration guidance.

## Operating systems

Operating-system packages are complete, independently adoptable overlays for provisioning, configuration, package and update management, identity, services, networking, storage, host security, observability, backup, recovery, lifecycle, upgrade, migration, and fleet automation.

- [Windows Server 2016, 2019, 2022, and 2025](operating-systems/windows-server/)
- [Windows 10 and Windows 11 clients](operating-systems/windows-client/)
- [Red Hat Enterprise Linux family](operating-systems/rhel-family/)
- [Ubuntu Server and Desktop](operating-systems/ubuntu/)
- [Debian](operating-systems/debian/)
- [SUSE Linux Enterprise](operating-systems/suse-linux-enterprise/)
- [Oracle Linux](operating-systems/oracle-linux/)
- [macOS](operating-systems/macos/)
- [FreeBSD](operating-systems/freebsd/)

See the [operating-systems index](operating-systems/README.md) for current-release semantics, selection, shared responsibility, safe change phases, automation, security, recovery, upgrade, and migration guidance.

## Networking

Networking packages are complete, independently adoptable overlays for device and controller ownership, management/control/data planes, routing, switching, topology, high availability, policy, telemetry, lifecycle, software/firmware, recovery, migration, and automation.

- [HPE Aruba Networking](networking/hpe-aruba-networking/)
- [Cisco networking](networking/cisco-networking/)
- [Juniper Networks](networking/juniper-networks/)
- [Brocade networking and Fibre Channel fabrics](networking/brocade-networking/)

See the [networking index](networking/README.md) for vendor and ownership selection, shared responsibility, safe change phases, topology controls, automation, security, recovery, firmware, and migration guidance.

## Frameworks

Framework packages are complete, independently adoptable overlays with framework-specific agent instructions, standards, templates, manifests, examples, adoption guidance, and completion evidence.

- [ASP.NET Core](frameworks/aspnet-core/)
- [React](frameworks/react/)
- [Angular](frameworks/angular/)
- [Spring Boot](frameworks/spring-boot/)
- [FastAPI](frameworks/fastapi/)

See the [frameworks index](frameworks/README.md) for selection, composition, tailoring, validation, maturity, and maintenance guidance.

## Project profiles

Project profiles are complete composition packages that select and organize governance, language, discipline, framework, platform, virtualization, operating-system, networking, project-decision, evidence, and operational expectations for a project shape. Canonical uppercase files remain stable compatibility entry points; lowercase directories contain the complete packages.

- [Web API](profiles/WEB_API.md) ([complete package](profiles/web-api/))
- [Web application](profiles/WEB_APPLICATION.md) ([complete package](profiles/web-application/))
- [Worker service](profiles/WORKER_SERVICE.md) ([complete package](profiles/worker-service/))
- [Command-line tool](profiles/CLI_TOOL.md) ([complete package](profiles/cli-tool/))
- [Desktop application](profiles/DESKTOP_APPLICATION.md) ([complete package](profiles/desktop-application/))
- [Mobile application](profiles/MOBILE_APPLICATION.md) ([complete package](profiles/mobile-application/))
- [Serverless function](profiles/SERVERLESS_FUNCTION.md) ([complete package](profiles/serverless-function/))
- [Data pipeline](profiles/DATA_PIPELINE.md) ([complete package](profiles/data-pipeline/))
- [Public library](profiles/PUBLIC_LIBRARY.md) ([complete package](profiles/public-library/))
- [Internal automation](profiles/INTERNAL_AUTOMATION.md) ([complete package](profiles/internal-automation/))
- [Multi-tenant SaaS](profiles/MULTI_TENANT_SAAS.md) ([complete package](profiles/multi-tenant-saas/))
- [Security tool](profiles/SECURITY_TOOL.md) ([complete package](profiles/security-tool/))
- [AI agent application](profiles/AI_AGENT_APPLICATION.md) ([complete package](profiles/ai-agent-application/))

See the [profiles index](profiles/README.md) for selection, primary and secondary composition, risk scaling, adoption, evidence, lifecycle, and maintenance guidance.

## Machine-readable schemas

The schema system defines versioned Draft 2020-12 contracts for project manifests, risk classifications, standards exceptions, test evidence, artifact records, and completion results.

- [Schema index](schemas/README.md)
- [Schema catalog](schemas/SCHEMA_CATALOG.md)
- [Versioning policy](schemas/VERSIONING_POLICY.md)
- [Compatibility policy](schemas/COMPATIBILITY_POLICY.md)
- [Validation guide](schemas/VALIDATION_GUIDE.md)
- [Executable examples](schemas/examples/)

Long-lived consumers should use `schemas/v1/` major-version contracts and also pin a repository tag or commit when exact immutability is required. Rolling top-level paths remain convenience entry points.

## Reusable templates

The template library provides governed, validated starting structures for agent instructions, architecture decisions, risk assessments, threat models, exceptions, completion evidence, machine-readable records, authorization, human review, production readiness, releases, recovery, and operations.

- [Template library index](templates/README.md)
- [Template catalog](templates/TEMPLATE_CATALOG.md)
- [Selection guide](templates/TEMPLATE_SELECTION_GUIDE.md)
- [Placeholder conventions](templates/PLACEHOLDER_CONVENTIONS.md)
- [Customization policy](templates/CUSTOMIZATION_POLICY.md)
- [Validation guide](templates/VALIDATION_GUIDE.md)

The seven original template paths remain stable. Every template package now includes detailed adoption guidance, a review checklist, and a completed fictitious example.

## Repository versioning, releases, and maturity

The repository has a pre-1.0 versioned compatibility baseline and an evidence-based release program.

- [Repository version](VERSION)
- [Changelog](CHANGELOG.md)
- [Release policy](RELEASE_POLICY.md)
- [Maturity policy](MATURITY_POLICY.md)
- [Versioned release notes](releases/README.md)
- [Machine-readable release state](releases/release-state.json)
- [Maturity review records](maturity-reviews/README.md)
- [Package-level adoption tests](adoption-tests/README.md)
- [Release validation and artifact tooling](tools/release/)

The current `0.10.0` release is **published as `v0.10.0`**. The `0.9.0` baseline remains **prepared, unpublished** and must not be retroactively tagged. The next intended publication is `1.0.0-rc.1`.

The release program defines Semantic Versioning for standards, schemas, templates, tools, governance, and stable paths; 90-day and 180-day deprecation windows; migration notes; tag and GitHub Release rules; deterministic archives; SHA-256 checksums; and the `1.0.0` compatibility gate.

A repository release does not automatically promote every package to `stable`.

## Repository toolchain

The executable toolchain validates repository structure, links, source-review freshness, skill entry points and package routing, schemas, templates, tool packages, and the release program; generates project manifests; composes traceable standards bundles; builds deterministic release artifacts; and provides a unified validation runner.

- [Toolchain index](tools/README.md)
- [Tool catalog](tools/TOOL_CATALOG.md)
- [Source freshness validator](tools/check-freshness/)
- [Command and result contract](tools/TOOL_CONTRACT.md)
- [Development guide](tools/DEVELOPMENT_GUIDE.md)
- [Testing guide](tools/TESTING_GUIDE.md)
- [Security boundaries](tools/SECURITY_BOUNDARIES.md)
- [Release tool](tools/release/README.md)

Stable entry points are preserved. Permanent CI invokes the unified validation runner, including source-freshness and release validation.

## Composition examples

The examples demonstrate how standards are selected, tailored, scoped, and supported by architecture, risk, testing, operations, and evidence documents.

- [Minimal CLI composition](examples/minimal/)
- [Web API composition](examples/web-api/)
- [Worker service composition](examples/worker-service/)
- [Full-stack web application composition](examples/full-stack/)

See the [examples index](examples/README.md) for selection guidance, boundaries, evidence shapes, and adaptation instructions.

## Status terminology

- `baseline`: usable minimum standard
- `stable`: mature and broadly reviewed under the maturity policy
- `draft`: usable for review but expected to change
- `planned`: catalog entry only; not an enforceable standard
- `deprecated`: retained for migration only
