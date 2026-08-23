---
id: PROFILE-INDEX-001
title: Project Profiles
version: 0.2.0
status: baseline
---
# Project Profiles

## Purpose

Project profiles are composition blueprints. They identify the minimum governance, discipline, language, framework, platform, virtualization, operating-system, networking, decision, evidence, and operational concerns normally expected for a project shape.

A profile answers:

- What kind of system is this?
- Which standards normally apply?
- Which decisions must be made before implementation?
- Which evidence must exist before completion?
- Which nested instruction scopes are likely?
- What risk factors commonly escalate review?
- What does this profile not replace?

A profile is not a project plan, architecture, compliance claim, production approval, or magic folder that makes an application safe. It is a starting control surface. Humans remain inconveniently necessary.

## Profile catalog

| Profile | Complete package | Typical starting risk | Purpose |
|---|---|---:|---|
| [Web API](WEB_API.md) | [web-api/](web-api/) | `moderate` | Define the minimum standards composition for HTTP, RPC, event-facing, or other programmatic service interfaces that expose business or operational capabilities. |
| [Web Application](WEB_APPLICATION.md) | [web-application/](web-application/) | `moderate` | Define the minimum standards composition for browser-delivered applications with interactive user experiences, client and server trust boundaries, and accessibility obligations. |
| [Worker Service](WORKER_SERVICE.md) | [worker-service/](worker-service/) | `moderate` | Define the minimum standards composition for long-running or scheduled background processes that consume work, coordinate dependencies, and operate without an interactive user request. |
| [Command-Line Tool](CLI_TOOL.md) | [cli-tool/](cli-tool/) | `low` | Define the minimum standards composition for command-line tools used by humans or automation, including safe input, output, exit codes, configuration, and state-changing behavior. |
| [Desktop Application](DESKTOP_APPLICATION.md) | [desktop-application/](desktop-application/) | `moderate` | Define the minimum standards composition for installed desktop applications that execute on user-managed endpoints and may store data, integrate with the operating system, or update independently. |
| [Mobile Application](MOBILE_APPLICATION.md) | [mobile-application/](mobile-application/) | `moderate` | Define the minimum standards composition for mobile applications distributed through device ecosystems with constrained permissions, intermittent connectivity, local storage, and upgrade behavior. |
| [Serverless Function](SERVERLESS_FUNCTION.md) | [serverless-function/](serverless-function/) | `moderate` | Define the minimum standards composition for event-driven functions whose execution, scaling, retries, identity, and lifecycle are controlled by a managed runtime. |
| [Data Pipeline](DATA_PIPELINE.md) | [data-pipeline/](data-pipeline/) | `high` | Define the minimum standards composition for ingesting, transforming, validating, storing, and publishing data across batch, streaming, and analytical workflows. |
| [Public Library](PUBLIC_LIBRARY.md) | [public-library/](public-library/) | `moderate` | Define the minimum standards composition for libraries, SDKs, packages, and reusable components consumed outside the repository's direct control. |
| [Internal Automation](INTERNAL_AUTOMATION.md) | [internal-automation/](internal-automation/) | `high` | Define the minimum standards composition for automation that inspects or changes internal systems, infrastructure, applications, accounts, or data. |
| [Multi-Tenant SaaS](MULTI_TENANT_SAAS.md) | [multi-tenant-saas/](multi-tenant-saas/) | `high` | Define the minimum standards composition for hosted software serving multiple tenants with isolation, authorization, data lifecycle, quota, billing, and operational obligations. |
| [Security Tool](SECURITY_TOOL.md) | [security-tool/](security-tool/) | `high` | Define the minimum standards composition for tools that inspect security posture, process findings, handle evidence, or perform authorized security-sensitive actions. |
| [AI Agent Application](AI_AGENT_APPLICATION.md) | [ai-agent-application/](ai-agent-application/) | `high` | Define the minimum standards composition for applications that use language models or other AI systems to reason, retrieve content, call tools, generate outputs, or perform actions. |

## Stable entry points

Each profile has two stable entry points:

1. The canonical top-level profile file, such as [`WEB_API.md`](WEB_API.md).
2. The complete package directory, such as [`web-api/`](web-api/).

The canonical file preserves the original public profile ID and provides the normative composition summary. The package directory provides detailed adoption, tailoring, scoped instructions, standards, templates, and examples.

## Complete profile package structure

```text
profiles/
├── WEB_API.md
├── web-api/
│   ├── AGENTS.md
│   ├── README.md
│   ├── MANIFEST.md
│   ├── standards/
│   │   ├── PROJECT_BOUNDARY_STANDARD.md
│   │   ├── ARCHITECTURE_DECISION_STANDARD.md
│   │   ├── SECURITY_PRIVACY_STANDARD.md
│   │   ├── TESTING_VALIDATION_STANDARD.md
│   │   ├── OPERATIONS_RELEASE_STANDARD.md
│   │   └── COMPLETION_EVIDENCE.md
│   ├── templates/
│   │   ├── ADOPTION_CHECKLIST.md
│   │   ├── REVIEW_CHECKLIST.md
│   │   └── EVIDENCE_RECORD_TEMPLATE.md
│   └── examples/
│       └── ADOPTION_EXAMPLE.md
└── ...
```

## Profile selection

Use [`PROFILE_SELECTION_GUIDE.md`](PROFILE_SELECTION_GUIDE.md).

Select the profile that best describes the system's primary operating shape. A project may need more than one profile when it genuinely combines distinct shapes, such as:

- a web application with worker services
- a SaaS product with public APIs
- a data pipeline with internal automation
- a security tool with a CLI and worker
- an AI agent application with a web API

Do not stack profiles merely because they sound impressive. Each selected profile adds decisions, evidence, and review obligations.

## Composition model

Use [`PROFILE_COMPOSITION_MODEL.md`](PROFILE_COMPOSITION_MODEL.md).

A project composition normally includes:

```text
governance
+ one primary profile
+ optional secondary profiles
+ language packages
+ discipline packages
+ framework packages
+ platform packages
+ virtualization packages
+ operating-system packages
+ networking packages
+ root project instructions
+ nested scoped instructions
+ project-specific evidence
```

Profiles select and organize other packages. They do not override governance and do not silently weaken package requirements.

## Risk and evidence

Use [`PROFILE_RISK_EVIDENCE_MATRIX.md`](PROFILE_RISK_EVIDENCE_MATRIX.md).

Typical risk levels in this repository are starting points only. Actual risk depends on:

- data sensitivity
- privilege
- public exposure
- tenant boundaries
- destructive capability
- reversibility
- availability
- safety
- legal or contractual obligations
- blast radius
- operational ownership
- evidence quality

A “small” script can be high risk if it modifies production. A large documentation site can be low risk. File count remains a poor substitute for thinking.

## Adoption procedure

1. Read root governance and [`profiles/AGENTS.md`](AGENTS.md).
2. Identify the project's primary operating shape.
3. Select a primary profile.
4. Select secondary profiles only for distinct additional shapes.
5. Read the canonical profile file and complete package README.
6. Decide whether to explicitly select the optional [Product Inception Lifecycle](../governance/PRODUCT_INCEPTION_LIFECYCLE.md). Profile selection alone does not activate it. A selected lifecycle requires Product Management traceability before the Build Gate can pass and does not itself supply the Site Reliability Engineering readiness and scaling contracts required for `production-candidate` and `scaled-production`.
7. Select applicable language, discipline, framework, platform, virtualization, operating-system, and networking packages.
8. Record required and conditional package decisions. Product Management and User Experience remain conditional profile overlays and are promoted only when the scoped product or human-experience concern applies.
9. Tailor scope, owners, environments, versions, commands, evidence, and exceptions.
10. Add nested `AGENTS.md` files where responsibility or risk changes.
11. Complete the profile adoption and review checklists.
12. Validate repository links, IDs, manifests, and project-specific behavior.
13. Obtain accountable review.

## Profile tailoring

Tailoring may:

- add stricter project requirements
- add or promote conditional disciplines
- declare supported runtimes, platforms, and environments
- define actual validation commands
- identify owners and approvers
- define evidence retention
- add nested instruction scopes
- document genuinely inapplicable controls

Tailoring must not:

- remove governance
- treat a typical risk level as an approved risk classification
- invent project facts
- omit required packages without justification
- reuse example evidence
- claim production readiness
- let nested instructions silently weaken shared controls
- treat profile selection as architecture approval

## Lifecycle

Use [`PROFILE_LIFECYCLE.md`](PROFILE_LIFECYCLE.md).

Profiles should be reviewed when:

- project shape changes
- a new interface or user type appears
- deployment, platform, virtualization, operating-system, or networking changes
- data sensitivity changes
- tenant or trust boundaries change
- automation becomes state-changing
- a library becomes public
- AI tool use becomes consequential
- evidence or operational ownership changes
- an incident invalidates assumptions

## Evidence model

Profile evidence should identify:

- selected primary and secondary profiles
- rationale
- required and conditional packages
- omitted packages and justification
- architecture and trust boundaries
- risk classification
- project decisions
- root and nested instructions
- validation commands and results
- checks not run
- production-readiness status
- limitations and residual risk
- accountable reviewers

Evidence must distinguish proposed, authorized, implemented, validated, reviewed, approved, operationally verified, and closed states.

## Validation

From the repository root:

```bash
python tools/validate-standards/validate_repository.py
python tools/check-links/check_links.py
```

An adopting repository must add executable project validation for its languages, frameworks, platforms, virtualization systems, operating systems, networking systems, tests, security, data, accessibility, release, and operations.

## Maturity

All profile packages are currently `baseline`.

A baseline profile is suitable for adoption and review but should evolve through real project feedback, incident learning, compatibility review, and specialist scrutiny.

## Non-production boundary

These profiles do not select real accounts, systems, identities, credentials, data stores, dependencies, environments, or production approvals. They define reusable composition guidance. The adopting organization must provide actual facts, authority, evidence, and judgment.
