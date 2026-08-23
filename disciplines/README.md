# Engineering Discipline Standards

## Purpose

Discipline packages define product and engineering behavior that crosses programming languages, frameworks, platforms, and project types. They turn concerns such as product definition, user experience, security, testing, architecture, accessibility, reliability, documentation, and delivery into explicit agent instructions, supporting standards, review checklists, evidence requirements, and completion gates.

A discipline package is selected because its work is relevant, not because a team has a matching job title. A small project can require several disciplines. A large project can still omit a discipline only when the omission is genuinely justified and recorded.

These packages improve consistency and reviewability. They do not replace accountable engineers, specialists, legal obligations, organizational policy, or project-specific decisions.

## Package catalog

| Discipline | Use it when | Common companions |
|---|---|---|
| [Product Management](product-management/) | A product, capability, material outcome, requirement, MVP boundary, or priority is being defined or changed. | [User Experience](user-experience/), [Architecture and System Design](architecture/), [Testing and Quality Engineering](testing/) |
| [User Experience](user-experience/) | A user or operator pursues goals through a journey, task, workflow, or interface. | [Product Management](product-management/), [Accessibility](accessibility/), [Testing and Quality Engineering](testing/) |
| [Application Security](application-security/) | The system accepts untrusted input. | [Architecture and System Design](architecture/), [Testing and Quality Engineering](testing/), [Privacy and Data Governance](privacy/) |
| [Architecture and System Design](architecture/) | A new component, service, data store, or external dependency is introduced. | [Application Security](application-security/), [Testing and Quality Engineering](testing/), [Observability](observability/) |
| [Testing and Quality Engineering](testing/) | Software behavior changes. | [Application Security](application-security/), [Architecture and System Design](architecture/), [CI/CD](ci-cd/) |
| [API Engineering](api-engineering/) | HTTP, RPC, event, or programmatic interfaces are created or changed. | [Application Security](application-security/), [Testing and Quality Engineering](testing/), [Integration Engineering](integration/) |
| [Integration Engineering](integration/) | Two systems exchange data or commands. | [API Engineering](api-engineering/), [Application Security](application-security/), [Data Engineering](data-engineering/) |
| [Database Engineering](database/) | Schemas, indexes, constraints, stored code, or queries change. | [Architecture and System Design](architecture/), [Application Security](application-security/), [Data Engineering](data-engineering/) |
| [Data Engineering](data-engineering/) | Data is ingested, transformed, moved, aggregated, or published. | [Database Engineering](database/), [Privacy and Data Governance](privacy/), [Integration Engineering](integration/) |
| [Accessibility](accessibility/) | Users interact with visual, audio, mobile, desktop, document, or web interfaces. | [Testing and Quality Engineering](testing/), [Documentation](documentation/), [Architecture and System Design](architecture/) |
| [Privacy and Data Governance](privacy/) | Personal, sensitive, confidential, or regulated data is collected or processed. | [Application Security](application-security/), [Data Engineering](data-engineering/), [Database Engineering](database/) |
| [Observability](observability/) | Software runs as a service, job, workflow, integration, or operational process. | [Site Reliability Engineering](sre/), [Application Security](application-security/), [Privacy and Data Governance](privacy/) |
| [Site Reliability Engineering](sre/) | A service or operational workflow has availability or recovery expectations. | [Observability](observability/), [Architecture and System Design](architecture/), [CI/CD](ci-cd/) |
| [Documentation](documentation/) | Software, configuration, behavior, operations, interfaces, deployment, or support processes change. | [Architecture and System Design](architecture/), [Testing and Quality Engineering](testing/), [Site Reliability Engineering](sre/) |
| [CI/CD](ci-cd/) | Automated workflows build, test, scan, package, release, deploy, or modify infrastructure. | [Software Supply Chain](supply-chain/), [Testing and Quality Engineering](testing/), [Release Engineering](release-engineering/) |
| [Software Supply Chain](supply-chain/) | Dependencies, build tools, package registries, containers, actions, plugins, or generated artifacts change. | [CI/CD](ci-cd/), [Application Security](application-security/), [Release Engineering](release-engineering/) |
| [Release Engineering](release-engineering/) | Software or infrastructure is versioned, packaged, promoted, deployed, published, or handed to operations. | [CI/CD](ci-cd/), [Software Supply Chain](supply-chain/), [Site Reliability Engineering](sre/) |

## What a complete discipline package contains

Every complete package includes:

```text
discipline/
├── AGENTS.md
├── README.md
├── MANIFEST.md
├── standards/
├── templates/
│   ├── ADOPTION_CHECKLIST.md
│   ├── REVIEW_CHECKLIST.md
│   └── EVIDENCE_RECORD_TEMPLATE.md
└── examples/
    └── ADOPTION_EXAMPLE.md
```

The files serve different purposes:

- `AGENTS.md` is the normative entry point for coding agents.
- `README.md` explains scope, adoption, tailoring, validation, companion disciplines, evidence, and limitations.
- `MANIFEST.md` defines the package inventory and package acceptance checks.
- `standards/` contains detailed requirements and completion gates.
- `templates/` supports repeatable adoption, review, and evidence capture.
- `examples/` demonstrates composition without pretending one project shape fits everything.

Copying only a README does not adopt a discipline. It merely creates the appearance of documentation, a hobby software teams have practiced for decades.

## How to select disciplines

Start with the project profile, architecture, data flows, trust boundaries, users, deployment model, support obligations, and change risk.

Ask:

1. Is a product problem, intended user, outcome, requirement, scope, or priority being defined or changed?
2. Does a user or operator pursue goals through a journey, workflow, or interface?
3. Does the project accept untrusted input or protect sensitive operations?
4. Does it expose an API or integrate with another system?
5. Does it store, transform, publish, or retain data?
6. Does it have a user interface or user-facing content?
7. Does it run as a service, scheduled job, workflow, or operational process?
8. Does it build, package, publish, deploy, or promote artifacts?
9. Does it have availability, scaling, recovery, incident, or on-call expectations?
10. Will non-authors need to use, operate, maintain, audit, or recover it?
11. Are compatibility, migration, versioning, or coordinated rollout concerns present?
12. What evidence would be required before an accountable reviewer accepts the change?

The answer normally produces several applicable discipline packages.

## Common project compositions

These are starting points, not exemptions.

### Web application

Usually includes product management, user experience, application security, architecture, testing, API engineering when applicable, accessibility, privacy, documentation, CI/CD, software supply chain, observability, release engineering, and SRE when production reliability is material.

### Worker service or scheduled automation

Usually includes architecture, testing, application security, integration when external systems are involved, database or data engineering when data is stored or transformed, observability, documentation, CI/CD, supply chain, release engineering, and SRE when recovery or on-call support exists.

### Data pipeline

Usually includes data engineering, database engineering, integration, privacy, application security, testing, observability, SRE, documentation, CI/CD, supply chain, and release engineering.

### Public library or SDK

Usually includes architecture, testing, API engineering for public programmatic contracts, application security, documentation, CI/CD, supply chain, and release engineering.

### Internal automation

Usually includes application security, architecture, testing, integration when systems are orchestrated, documentation, observability, CI/CD, supply chain, and release engineering.

Internal use does not make unsafe automation harmless. It merely reduces the number of witnesses.

## Adoption model

Discipline standards are layered with governance, language, framework, platform, virtualization, operating-system, networking, and project-profile standards:

```text
project/
├── AGENTS.md
├── standards/
│   ├── governance/
│   ├── languages/
│   ├── disciplines/
│   ├── platforms/
│   ├── frameworks/
│   └── profiles/
├── src/
│   └── AGENTS.md
├── tests/
│   └── AGENTS.md
└── docs/
    └── AGENTS.md
```

The nearest scoped `AGENTS.md` may add stricter requirements for its directory. It must not silently weaken applicable parent or shared requirements.

## Adoption procedure

1. Read the repository root `AGENTS.md` and governance standards.
2. Select the applicable project profile.
3. Select applicable language, framework, platform, virtualization, operating-system, and networking packages.
4. Select every relevant discipline package.
5. Copy or compose each complete package.
6. Preserve stable identifiers and package manifests.
7. Tailor scope, ownership, environments, tools, validation, evidence, and exceptions.
8. Add stricter project instructions where needed.
9. Run repository validation and link checking.
10. Obtain accountable review before normal use.

## Tailoring rules

Tailoring may add stricter controls, identify owners, declare supported environments and tools, add project-specific evidence, mark a requirement inapplicable with justification, and add nested instructions.

Tailoring must not delete inconvenient controls without justification, weaken safeguards silently, invent production values, claim support without evidence, or replace professional judgment.

## Evidence model

Each discipline package distinguishes among:

- **planned**: a control or test is intended
- **implemented**: the change exists
- **tested**: behavior was exercised in a stated environment
- **reviewed**: an accountable reviewer assessed the evidence
- **operationally verified**: behavior was confirmed in an appropriate runtime or operational context

A completion report must not collapse these states into a single cheerful checkbox.

Typical evidence includes contracts, diagrams, ADRs, inventories, schemas, plans, runbooks, exact commands, tests, review records, scans, telemetry, artifact metadata, checks not run, exceptions, limitations, residual risks, owners, and follow-up actions.

## Validation

Run from the repository root:

```bash
python tools/validate-standards/validate_repository.py
python tools/check-links/check_links.py
```

The adopting project must also define executable project-specific validation. This repository cannot know the project's runtime, infrastructure, data, credentials, deployment environments, or organizational obligations, and it should not pretend otherwise.

## Package maturity

- `baseline`: usable minimum package that should receive further review and refinement
- `stable`: mature, broadly reviewed, and supported for general adoption
- `draft`: usable for review but expected to change materially
- `planned`: catalog entry only, not an enforceable package
- `deprecated`: retained for migration and compatibility guidance

All discipline packages are currently baseline packages.

## Maintaining a package

A package change must preserve stable identifiers unless a breaking change is approved, update all maintained entry points together, keep requirements specific and evidence-based, validate links and identifiers, document migration impact, and disclose checks not run.

## Contribution boundaries

Do not add organization-specific production values, credentials, internal identifiers, copied proprietary standards, vague “best practices,” or unsupported compliance claims.
