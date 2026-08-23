---
id: EX-FULL-README-001
title: Full-Stack Web Application Composition Example
version: 0.2.0
status: baseline
---
# Full-Stack Web Application Composition Example

## Purpose

A high-risk React and ASP.NET Core web application demonstrating a broad multi-language standards composition.

This directory demonstrates a complete standards composition, including selection rationale, project tailoring, scoped agent instructions, architecture, risk, tests, operations, and schema-shaped evidence. It contains no production application code.

## Fictitious project summary

- **Profile:** [WEB_APPLICATION](../../profiles/WEB_APPLICATION.md)
- **Risk classification:** `high`
- **Implementation status:** documentation-only example
- **Production readiness:** not assessed and not claimed
- **Data:** The fictitious application models user profiles and transaction-like records. All values are synthetic; the example intentionally contains no production data or secrets.

## Learning goals

Use this example to understand how to:

- select standards based on project shape and risk
- document why each package applies
- convert shared standards into project-specific instructions
- use nested `AGENTS.md` files to narrow scope
- describe architecture and trust boundaries without inventing environment facts
- define validation before implementation
- record limitations, checks not run, and residual risk
- use repository schemas for machine-readable evidence

## Example structure

```text
full-stack/
├── AGENTS.md
├── README.md
├── MANIFEST.md
├── project-manifest.json
├── composition/
│   ├── STANDARDS_SELECTION.md
│   └── TAILORING_DECISIONS.md
├── docs/
│   ├── AGENTS.md
│   ├── ARCHITECTURE.md
│   ├── RISK_ASSESSMENT.md
│   ├── TEST_STRATEGY.md
│   ├── OPERATIONS.md
│   └── COMPLETION_EVIDENCE.md
├── evidence/
│   ├── completion-result.example.json
│   ├── test-evidence.example.json
│   └── artifact-record.example.json
└── scoped directories containing nested AGENTS.md files
```

## Selected profile

[WEB_APPLICATION](../../profiles/WEB_APPLICATION.md) provides the project-type overlay. It supplements rather than replaces governance, language, discipline, framework, platform, virtualization, operating-system, and networking standards.

## Selected languages

- [C#](../../languages/csharp/)
- [.NET](../../languages/dotnet/)
- [JavaScript and TypeScript](../../languages/javascript-typescript/)

Language packages define runtime, coding, dependency, testing, security, documentation, and completion expectations for implementation work.

## Selected disciplines

- [Product Management](../../disciplines/product-management/)
- [User Experience](../../disciplines/user-experience/)
- [Application Security](../../disciplines/application-security/)
- [Architecture and System Design](../../disciplines/architecture/)
- [Testing and Quality Engineering](../../disciplines/testing/)
- [API Engineering](../../disciplines/api-engineering/)
- [Database Engineering](../../disciplines/database/)
- [Accessibility](../../disciplines/accessibility/)
- [Privacy and Data Governance](../../disciplines/privacy/)
- [Observability](../../disciplines/observability/)
- [Site Reliability Engineering](../../disciplines/sre/)
- [Documentation](../../disciplines/documentation/)
- [CI/CD](../../disciplines/ci-cd/)
- [Software Supply Chain](../../disciplines/supply-chain/)
- [Release Engineering](../../disciplines/release-engineering/)
- [Integration Engineering](../../disciplines/integration/)

The selection rationale is documented in [`composition/STANDARDS_SELECTION.md`](composition/STANDARDS_SELECTION.md). Omitting a discipline requires a reason; absence from a job title is not a reason.

## Selected platforms

- [Containers](../../platforms/containers/)
- [Kubernetes](../../platforms/kubernetes/)

## Selected frameworks

- [ASP.NET Core](../../frameworks/aspnet-core/)
- [React](../../frameworks/react/)

## Selected virtualization

- None selected; the example does not administer the infrastructure beneath its Kubernetes boundary.

## Selected operating systems

- None selected; node and endpoint operating-system management is outside the fictitious application scope.

## Selected networking

- None selected; application and Kubernetes networking are modeled, but external network-device and fabric control planes are not.

## Architecture summary

- **React web client:** Presents accessible user workflows and calls the API.
- **ASP.NET Core API:** Enforces authentication, authorization, validation, and business rules.
- **Relational database:** Stores fictitious application records with explicit constraints.
- **Background processing:** Handles bounded asynchronous work.
- **Deployment stack:** Packages immutable artifacts for Kubernetes promotion.

See [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) for responsibilities, dependencies, trust boundaries, state, and failure behavior.

## Trust boundaries

- Public browser clients
- Identity provider
- API and database boundaries
- Background job infrastructure
- Container registry and Kubernetes cluster

Every real adoption must replace these fictitious boundaries with reviewed project facts.

## Root instructions

[`AGENTS.md`](AGENTS.md) defines:

- instruction precedence
- allowed and prohibited scope
- project facts
- mandatory working method
- safety and evidence requirements
- change-classification and completion gates
- links to the selected standards packages

## Nested instructions

- `src/backend/AGENTS.md`: Backend implementation scope
- `src/frontend/AGENTS.md`: Frontend implementation scope
- `tests/AGENTS.md`: Cross-system test scope
- `deploy/AGENTS.md`: Deployment scope
- `docs/AGENTS.md`: Documentation scope

Nested instructions add local constraints. They do not weaken root or shared standards.

## Composition and tailoring

- [`STANDARDS_SELECTION.md`](composition/STANDARDS_SELECTION.md) explains why packages were selected.
- [`TAILORING_DECISIONS.md`](composition/TAILORING_DECISIONS.md) records project facts, owners, assumptions, inapplicable controls, and unresolved decisions.
- [`project-manifest.json`](project-manifest.json) provides the machine-readable package selection.

A real project must review all three together. Contradictory narrative and manifest files are not “flexibility”; they are drift.

## Common documentation

- [`ARCHITECTURE.md`](docs/ARCHITECTURE.md)
- [`RISK_ASSESSMENT.md`](docs/RISK_ASSESSMENT.md)
- [`TEST_STRATEGY.md`](docs/TEST_STRATEGY.md)
- [`OPERATIONS.md`](docs/OPERATIONS.md)
- [`COMPLETION_EVIDENCE.md`](docs/COMPLETION_EVIDENCE.md)

Additional example-specific documents:

- [`THREAT_MODEL.md`](docs/THREAT_MODEL.md)
- [`DATA_HANDLING.md`](docs/DATA_HANDLING.md)
- [`RELEASE_PLAN.md`](docs/RELEASE_PLAN.md)
- [`ACCESSIBILITY_PLAN.md`](docs/ACCESSIBILITY_PLAN.md)

## Validation baseline

The example proposes the following project validations:

- .NET restore, format, build, unit, integration, and contract tests
- Frontend frozen install, formatting, linting, type checking, tests, and build
- Accessibility keyboard, semantics, focus, contrast, and automated checks
- Database migration and rollback rehearsal
- Container, Kubernetes, security, and release-evidence checks

The commands and outcomes in this example are illustrative. An adopting project must use actual repository commands and record whether each check passed, failed, or was not run.

## Evidence files

- [`completion-result.example.json`](evidence/completion-result.example.json) follows the [completion-result schema](../../schemas/completion-result.schema.json).
- [`test-evidence.example.json`](evidence/test-evidence.example.json) follows the [test-evidence schema](../../schemas/test-evidence.schema.json).
- [`artifact-record.example.json`](evidence/artifact-record.example.json) follows the [artifact-record schema](../../schemas/artifact-record.schema.json).

Example digests, commits, runs, timestamps, and reviewers are fictitious or explicitly marked as not verified.

## How to adapt this example

1. Replace the fictitious project name and summary.
2. Reclassify risk using actual impact and reversibility.
3. Re-select the profile, languages, disciplines, frameworks, platforms, virtualization systems, operating systems, and networking systems.
4. Replace architecture and trust-boundary assumptions with reviewed facts.
5. Define actual owners and approval paths.
6. Replace example commands with repository commands.
7. Define real environments and test data.
8. Add or remove nested scopes based on the real directory structure.
9. Replace example evidence with actual results.
10. Record exceptions, limitations, and checks not run.
11. Validate the repository.
12. Obtain accountable review.

## What not to copy

Do not copy:

- fictitious names or identifiers as though they were approved
- example risk classifications without reassessment
- placeholder ownership or reviewer values
- example evidence as proof
- framework, platform, virtualization, operating-system, or networking selections that do not apply
- operational claims that were not tested
- any statement implying certification, compliance, or production approval

## Known limitations

- No production identity, database, registry, cluster, or observability backend is configured.
- High risk requires accountable architecture, security, privacy, accessibility, operations, and release review.
- The example is a standards composition, not a deployable application.

## Review checklist

Before using the composition:

- [ ] The manifest matches the actual project.
- [ ] Every selected standard is applicable.
- [ ] Every omitted standard has a defensible reason.
- [ ] Root and nested instructions do not conflict.
- [ ] Architecture and trust boundaries are accurate.
- [ ] Risk and evidence requirements are proportionate.
- [ ] Validation commands are executable.
- [ ] Example evidence has been replaced.
- [ ] No secrets or sensitive production values are present.
- [ ] Limitations and residual risks are explicit.
- [ ] Accountable reviewers are identified.

## Validation of this standards repository

From the repository root:

```bash
python tools/validate-standards/validate_repository.py
python tools/check-links/check_links.py
```

## Non-production warning

This example is educational. It does not implement full-stack web application composition example, prove the selected controls, validate a deployment, or replace accountable engineering review.
