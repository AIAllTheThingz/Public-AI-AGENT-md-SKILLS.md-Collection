---
id: TEMPLATE-CATALOG-001
title: Template Catalog
version: 0.2.0
status: baseline
---

# Template Catalog

## Purpose

This catalog maps template types to stable files, package guidance, consumers, and related machine-readable contracts.

| Type | Package | Stable template |
|---|---|---|
| `root-agents` | [Root Agent Instructions](root/README.md) | [`AGENTS_TEMPLATE.md`](root/AGENTS_TEMPLATE.md) |
| `nested-agents` | [Nested Agent Instructions](nested/README.md) | [`AGENTS_TEMPLATE.md`](nested/AGENTS_TEMPLATE.md) |
| `architecture-decision` | [Architecture Decision Record](architecture-decision/README.md) | [`ADR_TEMPLATE.md`](architecture-decision/ADR_TEMPLATE.md) |
| `risk-assessment` | [Change Risk Assessment](risk/README.md) | [`RISK_ASSESSMENT_TEMPLATE.md`](risk/RISK_ASSESSMENT_TEMPLATE.md) |
| `threat-model` | [Threat Model](threat-model/README.md) | [`THREAT_MODEL_TEMPLATE.md`](threat-model/THREAT_MODEL_TEMPLATE.md) |
| `exception-record` | [Standards Exception Record](exception/README.md) | [`EXCEPTION_RECORD_TEMPLATE.md`](exception/EXCEPTION_RECORD_TEMPLATE.md) |
| `completion-report` | [Completion Report](completion/README.md) | [`COMPLETION_REPORT_TEMPLATE.md`](completion/COMPLETION_REPORT_TEMPLATE.md) |
| `project-manifest` | [Project Standards Manifest](project-manifest/README.md) | [`PROJECT_MANIFEST_TEMPLATE.json`](project-manifest/PROJECT_MANIFEST_TEMPLATE.json) |
| `test-evidence` | [Test Evidence Record](test-evidence/README.md) | [`TEST_EVIDENCE_TEMPLATE.json`](test-evidence/TEST_EVIDENCE_TEMPLATE.json) |
| `artifact-record` | [Artifact Record](artifact-record/README.md) | [`ARTIFACT_RECORD_TEMPLATE.json`](artifact-record/ARTIFACT_RECORD_TEMPLATE.json) |
| `change-authorization` | [Change Authorization Record](authorization/README.md) | [`CHANGE_AUTHORIZATION_TEMPLATE.md`](authorization/CHANGE_AUTHORIZATION_TEMPLATE.md) |
| `human-review` | [Human Review Record](human-review/README.md) | [`HUMAN_REVIEW_TEMPLATE.md`](human-review/HUMAN_REVIEW_TEMPLATE.md) |
| `production-readiness` | [Production Readiness Review](production-readiness/README.md) | [`PRODUCTION_READINESS_TEMPLATE.md`](production-readiness/PRODUCTION_READINESS_TEMPLATE.md) |
| `release-plan` | [Release Plan](release/README.md) | [`RELEASE_PLAN_TEMPLATE.md`](release/RELEASE_PLAN_TEMPLATE.md) |
| `rollback-recovery` | [Rollback and Recovery Plan](recovery/README.md) | [`ROLLBACK_RECOVERY_TEMPLATE.md`](recovery/ROLLBACK_RECOVERY_TEMPLATE.md) |
| `operational-runbook` | [Operational Runbook](operations/README.md) | [`RUNBOOK_TEMPLATE.md`](operations/RUNBOOK_TEMPLATE.md) |

## Schema-backed templates

| Template | Versioned schema |
|---|---|
| Project standards manifest | [`project-manifest`](../schemas/v1/project-manifest.schema.json) |
| Test evidence | [`test-evidence`](../schemas/v1/test-evidence.schema.json) |
| Artifact record | [`artifact-record`](../schemas/v1/artifact-record.schema.json) |

Human-readable risk, exception, and completion templates may be paired with their corresponding current-major schemas where an adopting repository requires machine-readable evidence. Completion-result consumers use v2 for current records and retain v1 for historical or pinned records.

## Consumer categories

Templates may be consumed by:

- project teams
- coding agents
- CI and release automation
- governance reviewers
- security and privacy reviewers
- change authorities
- operators and incident responders
- auditors and evidence processors

Consumers must pin stable paths or record a template version. Copying from a moving branch without recording the source is a surprisingly efficient way to create undocumented policy drift.

## Ownership

Every adopted record needs:

- record owner
- source template and version
- scope
- required reviewers
- lifecycle or revisit trigger
- evidence retention
- replacement or deprecation path

## Compatibility surface

Compatibility includes:

- stable file path
- placeholder names
- section meaning
- defined decision vocabulary
- schema alignment
- example behavior
- validation rules
- expected consumers

A Markdown template can break automation even when it still looks attractive in a browser. Formatting is not the whole contract.
