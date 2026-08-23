---
id: PROFILE-DATA-PIPELINE
title: Data Pipeline Project Profile
version: 0.2.0
status: baseline
applies_to:
  - data-pipeline
depends_on:
  - GOV-CONTRACT
  - GOV-WORK
  - GOV-RISK
  - GOV-EVIDENCE
---
# Data Pipeline Project Profile

## Purpose

Define the minimum standards composition for ingesting, transforming, validating, storing, and publishing data across batch, streaming, and analytical workflows.

## Complete package

Use the complete package at [`data-pipeline/`](data-pipeline/). This canonical file remains the stable profile entry point.

## Applicability

This profile applies to:

- batch ETL and ELT
- stream processing
- data ingestion
- analytics pipelines
- data export and publication workflows

It normally does not describe:

- transactional application logic with no pipeline behavior
- ad hoc manual queries
- simple file copies with no governed data transformation

## Typical starting risk

`high`

This is a starting point only. The actual project or change must be classified under governance.

## Required governance

- `governance/ORGANIZATION_CONTRACT.md`
- `governance/AGENT_WORKING_METHOD.md`
- `governance/RISK_CLASSIFICATION.md`
- `governance/COMPLETION_EVIDENCE.md`
- `governance/HUMAN_REVIEW_POLICY.md`
- `governance/PRODUCTION_READINESS.md` when deployed or operated

## Required discipline overlays

- `disciplines/architecture/AGENTS.md`
- `disciplines/testing/AGENTS.md`
- `disciplines/integration/AGENTS.md`
- `disciplines/database/AGENTS.md`
- `disciplines/data-engineering/AGENTS.md`
- `disciplines/privacy/AGENTS.md`
- `disciplines/observability/AGENTS.md`
- `disciplines/sre/AGENTS.md`

## Conditionally required disciplines

- `disciplines/product-management/AGENTS.md`
- `disciplines/user-experience/AGENTS.md`
- `disciplines/application-security/AGENTS.md`
- `disciplines/ci-cd/AGENTS.md`
- `disciplines/supply-chain/AGENTS.md`
- `disciplines/release-engineering/AGENTS.md`
- `disciplines/documentation/AGENTS.md`

Conditional packages become required when their concern is present. Document every omission that would reasonably appear applicable.

Product Management becomes required when the pipeline is governed as a data product or materially changes consumer outcomes, requirements, published scope, or acceptance criteria. User Experience becomes required only when analysts, operators, or other users pursue goals through an owned workflow or interface; a headless pipeline implementing an existing data contract may justify omission.

## Required project decisions

- data contracts and ownership
- lineage and metadata
- replay and backfill behavior
- quality gates
- retention and sensitive-data handling
- schema compatibility
- late, duplicate, and out-of-order data
- recovery, cost, and operational ownership

## Architecture and trust boundaries

- sources and ingestion boundaries
- schema and contract ownership
- transformation stages
- storage layers and publication targets
- orchestration and checkpoints
- lineage, observability, and recovery

## Security and privacy focus

- data classification
- least-privilege access
- secret and key handling
- privacy and minimization
- safe logs and samples
- controlled export and sharing

## Testing and validation

- data-quality rules
- schema compatibility
- replay and idempotency
- late and duplicate data
- failure and restart
- representative volume and performance

## Operations and release

- freshness, completeness, quality, and lag metrics
- backfill and replay runbooks
- retention and deletion
- capacity and cost
- dependency and schema alerts
- incident and recovery ownership

## Suggested nested instruction scopes

- `src/ingest/AGENTS.md`
- `src/transform/AGENTS.md`
- `src/publish/AGENTS.md`
- `tests/AGENTS.md`
- `docs/AGENTS.md`
- `orchestration/AGENTS.md`

## Completion evidence

Record:

- profile selection rationale
- risk classification
- required and conditional package decisions
- architecture and trust boundaries
- project decisions
- validation commands and outcomes
- checks not run
- operational and production-readiness status
- limitations and residual risk
- accountable reviewers and approvers

## Completion gate

The project must satisfy applicable governance, language, discipline, framework, platform, virtualization, operating-system, networking, and profile standards. Document exclusions, exceptions, and unvalidated behavior.

Selecting this profile does not prove the project is secure, tested, accessible, private, reliable, compatible, supportable, or production-ready.
