---
id: TEMPLATE-INDEX-001
title: Template Library
version: 0.2.0
status: baseline
---

# Template Library

## Purpose

The template library converts reusable standards into reviewable project records.

Templates provide structure for:

- root and nested agent instructions
- architecture decisions
- risk assessments
- threat models
- standards exceptions
- completion evidence
- project manifests
- test and artifact evidence
- change authorization
- human review
- production readiness
- releases
- rollback and recovery
- operational runbooks

A template is a starting structure, not a completed control. Copying a file does not create authority, evidence, ownership, or correctness. Paperwork remains unable to perform magic despite decades of institutional experimentation.

## Template catalog

| Template package | Stable template | Type | Purpose |
|---|---|---|---|
| [Root Agent Instructions](root/) | [`AGENTS_TEMPLATE.md`](root/AGENTS_TEMPLATE.md) | `root-agents` | Define repository-wide facts, selected standards, authority boundaries, working methods, validation, evidence, and prohibited behavior for coding agents. |
| [Nested Agent Instructions](nested/) | [`AGENTS_TEMPLATE.md`](nested/AGENTS_TEMPLATE.md) | `nested-agents` | Define stricter, scope-specific instructions for a directory whose responsibilities, risks, tooling, or validation differ from the repository root. |
| [Architecture Decision Record](architecture-decision/) | [`ADR_TEMPLATE.md`](architecture-decision/ADR_TEMPLATE.md) | `architecture-decision` | Record a consequential architecture decision, its context, considered alternatives, impacts, evidence, ownership, and revisit triggers. |
| [Change Risk Assessment](risk/) | [`RISK_ASSESSMENT_TEMPLATE.md`](risk/RISK_ASSESSMENT_TEMPLATE.md) | `risk-assessment` | Classify change risk using explicit factors, required controls, residual risk, ownership, and reassessment triggers. |
| [Threat Model](threat-model/) | [`THREAT_MODEL_TEMPLATE.md`](threat-model/THREAT_MODEL_TEMPLATE.md) | `threat-model` | Document assets, actors, entry points, trust boundaries, abuse cases, mitigations, evidence, and residual risk for a defined system or change. |
| [Standards Exception Record](exception/) | [`EXCEPTION_RECORD_TEMPLATE.md`](exception/EXCEPTION_RECORD_TEMPLATE.md) | `exception-record` | Request, review, approve, monitor, expire, and close a time-bounded deviation from a specific standards rule. |
| [Completion Report](completion/) | [`COMPLETION_REPORT_TEMPLATE.md`](completion/COMPLETION_REPORT_TEMPLATE.md) | `completion-report` | Report implemented scope, changed files, risk, validation, execution-discipline evidence, limitations, operational impact, recovery, and accountable review. |
| [Project Standards Manifest](project-manifest/) | [`PROJECT_MANIFEST_TEMPLATE.json`](project-manifest/PROJECT_MANIFEST_TEMPLATE.json) | `project-manifest` | Declare the project's selected profile, languages, disciplines, frameworks, platforms, virtualization systems, operating systems, networking systems, risk, exceptions, ownership, and evidence location in machine-readable form. |
| [Test Evidence Record](test-evidence/) | [`TEST_EVIDENCE_TEMPLATE.json`](test-evidence/TEST_EVIDENCE_TEMPLATE.json) | `test-evidence` | Record an exact validation command, outcome, environment, timing, artifact, evidence, exit code, and limitations in schema-compatible JSON. |
| [Artifact Record](artifact-record/) | [`ARTIFACT_RECORD_TEMPLATE.json`](artifact-record/ARTIFACT_RECORD_TEMPLATE.json) | `artifact-record` | Identify an artifact, immutable digest, source revision, build run, provenance, signing state, creation time, and limitations in schema-compatible JSON. |
| [Change Authorization Record](authorization/) | [`CHANGE_AUTHORIZATION_TEMPLATE.md`](authorization/CHANGE_AUTHORIZATION_TEMPLATE.md) | `change-authorization` | Record who may perform a consequential change, against which targets, during what window, with which controls, stop criteria, validation, and recovery expectations. |
| [Human Review Record](human-review/) | [`HUMAN_REVIEW_TEMPLATE.md`](human-review/HUMAN_REVIEW_TEMPLATE.md) | `human-review` | Record accountable human review scope, evidence examined, findings, required changes, decision, authority, and limitations. |
| [Production Readiness Review](production-readiness/) | [`PRODUCTION_READINESS_TEMPLATE.md`](production-readiness/PRODUCTION_READINESS_TEMPLATE.md) | `production-readiness` | Evaluate whether a system or change is operationally ready for production, including ownership, security, data, reliability, observability, recovery, capacity, support, and approval. |
| [Release Plan](release/) | [`RELEASE_PLAN_TEMPLATE.md`](release/RELEASE_PLAN_TEMPLATE.md) | `release-plan` | Define artifact identity, scope, prerequisites, migration order, rollout stages, validation, stop criteria, communication, rollback, and post-release monitoring. |
| [Rollback and Recovery Plan](recovery/) | [`ROLLBACK_RECOVERY_TEMPLATE.md`](recovery/ROLLBACK_RECOVERY_TEMPLATE.md) | `rollback-recovery` | Define failure scenarios, recovery objectives, rollback or restore methods, prerequisites, authority, validation, stop conditions, and evidence. |
| [Operational Runbook](operations/) | [`RUNBOOK_TEMPLATE.md`](operations/RUNBOOK_TEMPLATE.md) | `operational-runbook` | Provide an operator-safe procedure for observing, diagnosing, changing, recovering, and escalating a supported system. |

See [`TEMPLATE_CATALOG.md`](TEMPLATE_CATALOG.md) for selection, schema alignment, and expected consumers.

## Collection structure

```text
templates/
├── AGENTS.md
├── README.md
├── MANIFEST.md
├── TEMPLATE_CATALOG.md
├── TEMPLATE_SELECTION_GUIDE.md
├── AUTHORING_GUIDE.md
├── CUSTOMIZATION_POLICY.md
├── PLACEHOLDER_CONVENTIONS.md
├── TEMPLATE_LIFECYCLE.md
├── VALIDATION_GUIDE.md
├── COMPLETION_CRITERIA.md
└── <template-package>/
    ├── <STABLE_TEMPLATE>
    ├── README.md
    ├── REVIEW_CHECKLIST.md
    └── examples/
```

Each package README explains when to use the template, required inputs, placeholders, adoption, review, validation, failure modes, and limitations.

## Template classes

### Instruction templates

- Root `AGENTS.md`
- Nested `AGENTS.md`

These define agent behavior and scope. They do not authorize actions.

### Decision and governance templates

- Architecture decision
- Risk assessment
- Threat model
- Exception record
- Change authorization
- Human review
- Production readiness

These capture decisions and accountability. They must distinguish requester, implementer, reviewer, approver, operator, and risk owner.

### Evidence templates

- Completion report
- Project manifest
- Test evidence
- Artifact record

Machine-readable evidence templates align with their current-major schemas where applicable; historical major paths remain available for retained records.

### Delivery and operations templates

- Release plan
- Rollback and recovery plan
- Operational runbook

These define execution, observation, recovery, and ownership. They do not grant access or production authority.

## Selection model

Use [`TEMPLATE_SELECTION_GUIDE.md`](TEMPLATE_SELECTION_GUIDE.md).

Select templates based on the record or decision required, not because every project deserves a ceremonial binder.

A single change may need several linked records. For example, a high-risk production release may require:

```text
risk assessment
+ architecture decision
+ threat model
+ change authorization
+ release plan
+ rollback and recovery plan
+ production readiness review
+ test evidence
+ artifact record
+ completion report
```

Do not merge distinct decisions into one vague document merely to reduce file count.

## Placeholder model

Use [`PLACEHOLDER_CONVENTIONS.md`](PLACEHOLDER_CONVENTIONS.md).

Template placeholders use:

```text
{UPPER_SNAKE_CASE}
```

Rules:

- placeholder names are stable interfaces
- every placeholder is documented in its package README
- examples contain no unresolved placeholders
- copied records must contain no unresolved placeholders
- unknown facts must not be invented
- optional fields must be removed or explicitly marked according to the template instructions
- JSON value types must be corrected after replacement

## Adoption workflow

1. Read root governance and this collection `AGENTS.md`.
2. Identify the decision, record, evidence, or instruction needed.
3. Select the smallest complete set of templates.
4. Read the package README and stable template.
5. Copy the template into the adopting repository.
6. Replace placeholders using authoritative facts.
7. Link related decisions, evidence, schemas, owners, and approvals.
8. Remove instructional notes that should not remain.
9. Run template, link, repository, and schema validation.
10. Use the package review checklist.
11. Obtain accountable human review.
12. Record lifecycle ownership and revisit triggers.

## Customization

Use [`CUSTOMIZATION_POLICY.md`](CUSTOMIZATION_POLICY.md).

Customization may:

- add project-specific sections
- add stricter review or evidence requirements
- remove genuinely inapplicable optional sections
- add namespaced schema extensions
- define organization-specific decision vocabularies where compatible
- add local examples

Customization must not:

- remove governance-required fields
- conflate review with authorization
- hide failed or not-run validation
- remove expiry from exceptions
- remove rollback or recovery from consequential work
- weaken parent `AGENTS.md`
- insert secrets or confidential evidence
- preserve placeholders in adopted records
- claim production readiness from implementation completion

## Authoring templates

Use [`AUTHORING_GUIDE.md`](AUTHORING_GUIDE.md).

A new template package must include:

- a stable template path
- package README
- review checklist
- completed fictitious example
- unique document identifiers
- documented placeholders
- completion criteria
- related governance or schema references
- compatibility and lifecycle expectations
- automated template validation

## Validation

Use [`VALIDATION_GUIDE.md`](VALIDATION_GUIDE.md).

Run:

```bash
python -m pip install -r tools/validate-schemas/requirements.txt
python tools/validate-standards/validate_repository.py
python tools/check-links/check_links.py
python tools/validate-schemas/validate_schemas.py
python tools/validate-templates/validate_templates.py
```

The template validator checks:

- required collection files
- required package files
- stable template paths
- placeholder syntax
- placeholder documentation
- placeholder absence from examples
- front-matter identifiers
- review checklists
- JSON template parsing
- schema-compatible JSON examples
- accidental secret-like content
- minimum README depth

## Lifecycle

Use [`TEMPLATE_LIFECYCLE.md`](TEMPLATE_LIFECYCLE.md).

Review templates when:

- governance changes
- schemas change
- a recurring review defect appears
- an incident exposes missing evidence or ownership
- consumer feedback identifies ambiguity
- a placeholder changes meaning
- a stable path must move
- tools or validation behavior changes

## Completion criteria

Use [`COMPLETION_CRITERIA.md`](COMPLETION_CRITERIA.md).

A template package is complete only when the template, README, checklist, example, validation, lifecycle, and compatibility story agree.

## Non-production boundary

The templates contain no real credentials, internal endpoints, production targets, personal data, or approved decisions.

Adopting organizations must supply real facts, authority, owners, validation, evidence, and judgment.
