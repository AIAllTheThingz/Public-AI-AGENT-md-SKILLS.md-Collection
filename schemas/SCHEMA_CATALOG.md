---
id: SCHEMA-CATALOG-001
title: Schema Catalog
version: 0.4.0
status: baseline
---

# Schema Catalog

## Purpose

This catalog maps each machine-readable contract to stable paths, versioned paths, expected instances, owners, and compatibility concerns.

| Contract | Rolling path | Versioned path | Purpose |
|---|---|---|---|
| `artifact-record` | `artifact-record.schema.json` | `v1/artifact-record.schema.json` | Identifies a produced artifact, its source revision, digest, build context, provenance, and signing state. |
| `completion-result` | `completion-result.schema.json` | `v2/completion-result.schema.json` | Records implementation state, validation outcomes, execution-discipline evidence, limitations, risk, compatibility impact, and review without treating a single successful command as proof of full completion. |
| `exception-record` | `exception-record.schema.json` | `v1/exception-record.schema.json` | Records a time-bounded deviation from a specific rule, including ownership, rationale, risk, compensating controls, approval, status, and closure. |
| `project-manifest` | `project-manifest.schema.json` | `v1/project-manifest.schema.json` | Declares the selected project profile; language, discipline, framework, platform, virtualization, operating-system, and networking packages; risk; exceptions; and project-specific composition metadata. |
| `risk-classification` | `risk-classification.schema.json` | `v1/risk-classification.schema.json` | Records a change risk level, rationale, evaluated factors, required reviewers, rollback requirement, ownership, and reassessment triggers. |
| `test-evidence` | `test-evidence.schema.json` | `v1/test-evidence.schema.json` | Records an executed or explicitly not-run validation command, result, environment, timing, evidence, and limitations. |

## Instance discovery

The repository validator maps files by naming convention:

| Instance filename | Schema |
|---|---|
| `project-manifest.json` | project manifest |
| `completion-result*.json` | completion result |
| `test-evidence*.json` | test evidence |
| `artifact-record*.json` | artifact record |
| `exception-record*.json` | exception record |
| `risk-classification*.json` | risk classification |

## Completion-result compatibility

The rolling and current versioned completion-result contracts are major version 2 and require `executionDiscipline` with `schemaVersion: "2.0.0"`. `v1/completion-result.schema.json` remains unchanged for historical records and pinned v1 consumers. The other catalogued contracts remain major version 1.

Files under `schemas/examples/` are handled as explicit positive or negative test cases, including the preserved completion-result v1 compatibility pair.

Completion-result v2 consumers must run both Draft 2020-12 structural validation and the repository's semantic completion checks. The semantic pass correlates each executed validation's `objectiveId` and `actionId` with one exact retry-ledger action and validates action, terminal, sequence-reset, authorization, and RFC 3339 chronology.

## Ownership

The adopting repository must assign:

- contract owner
- consumer owners
- validator owner
- migration owner for breaking changes
- evidence owner for generated records
- release or automation owner where schemas gate delivery

## Consumer responsibilities

Consumers must:

- use a major-version schema for durable automation and pin a repository tag or commit when exact immutability is required
- reject unknown top-level fields unless an extension policy says otherwise
- retain the original instance used for a decision
- record the validator and schema version
- treat validation failure as a contract problem, not an invitation to disable validation
- avoid assuming that structural validity proves semantic truth
