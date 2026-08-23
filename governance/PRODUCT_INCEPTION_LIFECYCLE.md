---
id: GOV-PRODUCT-INCEPTION
title: Product Inception Lifecycle
version: 0.1.0
status: baseline
applies_to:
  - product-inception
depends_on:
  - GOV-CONTRACT
  - GOV-WORK
  - GOV-RISK
  - GOV-EVIDENCE
---

# Product Inception Lifecycle

## Purpose

Define a proportionate, evidence-based path from idea through build while preventing normal production implementation from outrunning product, requirements, UX, architecture, and validation decisions.

## Applicability

Normative control: [`GOV-PRODUCT-INCEPTION-001`](#gov-product-inception-001).

This lifecycle applies only when explicitly selected for a project or change. Adopting this repository, its governance, a project profile, or the Product Management package does not select it. Once selected, it governs the selected scope for a new product, material capability, or material change in intended users, outcomes, requirements, architecture, trust boundaries, or operating model. Existing records that answer a gate count as its evidence. For small changes within the selected scope, record a concise gate decision that references those records.

## Roles

- **Product owner:** owns problem, outcome, scope, requirements, and product decisions.
- **Design or UX owner:** owns applicable journey, interaction, research, and UX-validation evidence.
- **Engineering owner:** owns architecture, technology, implementation planning, and build evidence.
- **Security, privacy, accessibility, data, reliability, or operational owner:** owns applicable specialist decisions.
- **Reviewer or approver:** evaluates gate evidence within delegated authority; an agent may recommend but not impersonate approval.

## Normative rules

### GOV-PRODUCT-INCEPTION-001

**Requirement:** Apply this lifecycle only to an explicitly selected project or change scope, and retain that selection, scope, and applicability decision as evidence.

**Expected evidence:** Selection record naming the governed scope, accountable owner, applicable change, and any referenced existing gate evidence.

### GOV-PRODUCT-INCEPTION-002

**Requirement:** Record gate evidence and decisions with accurate repository-supported states, and do not treat a passing gate as proof of a later lifecycle state.

**Expected evidence:** Dated gate record identifying the evidence state, decision, reviewer or approver, limitations, and next bounded phase.

### GOV-PRODUCT-INCEPTION-003

**Requirement:** Pass the Concept Gate only when the problem, intended users or actors, desired outcome, evidence basis, constraints, unknowns, boundaries, owners, and review are sufficient to authorize requirements work.

**Expected evidence:** Concept decision of `Pass`, `Fail`, or `Blocked` linked to reviewed concept evidence and owners for material unknowns.

### GOV-PRODUCT-INCEPTION-004

**Requirement:** Pass the Requirements Gate only when uniquely identified functional and applicable nonfunctional requirements, measurable acceptance criteria, dependencies, unknowns, exclusions, ownership, sources, and change history are reviewable and testable.

**Expected evidence:** Requirements decision of `Pass`, `Fail`, or `Blocked` linked to the reviewed requirement set and acceptance criteria.

### GOV-PRODUCT-INCEPTION-005

**Requirement:** Pass the Design Gate only when every applicable UX, architecture, trust, data, integration, technology, and accessibility design area has reviewed evidence and every omitted area has a justified `NotApplicable` decision.

**Expected evidence:** Design decision of `Pass`, `Fail`, or `Blocked` linked to reviewed design records, applicability decisions, and material architecture or technology decisions.

### GOV-PRODUCT-INCEPTION-006

**Requirement:** Normal production implementation must not start unless the Build Gate decision is explicitly `Pass` for the reviewed scope, package and technology selections, acceptance criteria, validation strategy, implementation plan, ownership, dependencies, rollback considerations, and evidence locations.

**Expected evidence:** Build decision of `Pass`, `Fail`, or `Blocked` identifying the reviewed scope, selections, plan, owners, validation strategy, rollback considerations, and re-review triggers.

### GOV-PRODUCT-INCEPTION-007

**Requirement:** Start pre-gate prototype or experiment work only under an explicit bounded charter, and do not allow that work to become production implementation, product commitment, architecture of record, production data model, or supported service without the applicable gates and reviews.

**Expected evidence:** Authorized prototype or experiment charter, accurate missing-evidence states, stop and disposition criteria, prohibited-use boundary, and any later transition decision.

### GOV-PRODUCT-INCEPTION-008

**Requirement:** Assign product lifecycle states only from dated evidence for the reviewed artifact and scope, with accountable ownership, limitations, and rollback or reversal considerations. Assign `scaled-production` only when every applicable scaling area is `Verified` with current representative evidence and a stated supported envelope; any `Applicable`, `NotRun`, or `Blocked` area prevents that state, and every `NotApplicable` area requires justification, whether or not the SRE package is otherwise selected.

**Expected evidence:** Lifecycle transition record naming the prior and new state, artifact or revision, owner, decision, supporting evidence, limitations, and reversal considerations; a `scaled-production` transition also links the complete scaling applicability matrix and evidence for every applicable area.

### GOV-PRODUCT-INCEPTION-009

**Requirement:** Transition to `production-candidate` only when the exact candidate has a passing or justified not-applicable result for every applicable readiness area and no applicable required area remains `NotRun`.

**Expected evidence:** Per-area `Pass`, `Fail`, `Blocked`, or justified `NotApplicable` results for the exact candidate plus the candidate-level gate decision and remaining limitations.

### GOV-PRODUCT-INCEPTION-010

**Requirement:** Maintain end-to-end product traceability and re-evaluate affected gates after a material change to users, requirements, scope, evidence, architecture, technology, data, trust, artifact, deployment, operating conditions, ownership, or risk.

**Expected evidence:** Traceability links and dated gate re-review records for every material change trigger.

### GOV-PRODUCT-INCEPTION-011

**Requirement:** Do not treat implementation artifacts, prototypes, tests, or checklists as product completion or production-readiness proof, and do not use an exception to conceal a failed gate, missing evidence, or missing authority.

**Expected evidence:** Honest failed and not-run states, exact-rule exception records where applicable, and separate completion and production-readiness decisions.

### GOV-PRODUCT-INCEPTION-012

**Requirement:** Do not claim product success, certification, compliance, release approval, or production readiness from lifecycle adoption alone.

**Expected evidence:** Completion reporting distinguishes lifecycle adoption from implementation, validation, accountable review, authorization, release, and operational evidence.

## Lifecycle

```text
Idea
  -> Problem Definition
  -> Users / Actors
  -> Desired Outcomes
  -> Constraints
  -> Requirements
  -> MVP Scope
  -> UX Flows
  -> Nonfunctional Requirements
  -> Architecture
  -> Technology Selection
  -> Implementation Planning
  -> Build
```

The sequence is a decision flow, not a command to create one artifact per line. Activities may iterate, but later decisions must not conceal unmet earlier evidence.

## Evidence states

Normative control: [`GOV-PRODUCT-INCEPTION-002`](#gov-product-inception-002).

Gate records must distinguish the available evidence using repository-supported states such as `Planned`, `Implemented`, `Tested`, `Reviewed`, `OperationallyVerified`, `NotRun`, `Blocked`, and `NotApplicable`. `NotApplicable` requires rationale. A passing gate means required evidence is sufficient for the next bounded phase; it does not prove later lifecycle states.

## Inception gates

### Concept Gate

Normative control: [`GOV-PRODUCT-INCEPTION-003`](#gov-product-inception-003).

The gate requires sufficient definition of:

- the problem and evidence basis
- intended users or actors
- desired outcome and measurement approach
- facts, assumptions, constraints, and material unknowns
- product boundaries and explicit exclusions

**Decision:** `Pass`, `Fail`, or `Blocked`. A pass requires an accountable owner, reviewed evidence, and owners for material unknowns. It authorizes requirements work, not production implementation.

### Requirements Gate

Normative control: [`GOV-PRODUCT-INCEPTION-004`](#gov-product-inception-004).

The gate requires:

- uniquely identified functional requirements
- applicable nonfunctional requirements, including security, privacy, accessibility, performance, reliability, recovery, operations, and compatibility where relevant
- measurable acceptance criteria mapped to requirements
- known dependencies and integration assumptions
- material unknowns, exclusions, and unresolved conflicts
- requirement ownership, sources, and change history

**Decision:** `Pass`, `Fail`, or `Blocked`. A pass requires reviewable and testable requirements; it does not assert implementation or validation.

### Design Gate

Normative control: [`GOV-PRODUCT-INCEPTION-005`](#gov-product-inception-005).

The gate requires, where applicable:

- UX journeys and flows with success, failure, and recovery states
- architecture context and component boundaries
- trust boundaries, identities, privileges, and sensitive data
- data flows, storage, retention, and ownership
- integration boundaries, dependencies, contracts, quotas, and failure behavior
- architecture decision records for material decisions
- major technology decisions with alternatives, constraints, lifecycle, and reversal implications
- separate accessibility applicability and validation planning

Each omitted area must be `NotApplicable` with justification.

**Decision:** `Pass`, `Fail`, or `Blocked`. A pass requires reviewed design evidence for every applicable area; it does not convert a prototype into architecture of record.

### Build Gate

Normative control: [`GOV-PRODUCT-INCEPTION-006`](#gov-product-inception-006).

The gate requires:

- approved implementation scope and explicit exclusions
- selected applicable project profile
- identified applicable governance, language, discipline, framework, platform, virtualization, operating-system, and networking packages
- selected languages, frameworks, and platforms with version or support boundaries where material
- measurable acceptance criteria
- validation strategy covering applicable positive, negative, security, accessibility, performance, resilience, recovery, compatibility, and operational behavior
- phased implementation plan, owners, dependencies, rollback considerations, and evidence locations

**Decision:** `Pass`, `Fail`, or `Blocked`. Normal production implementation must not start unless the Build Gate decision is explicitly `Pass`. Passing authorizes only the reviewed scope and must be revisited after material change.

## Prototype and experiment exception

Normative control: [`GOV-PRODUCT-INCEPTION-007`](#gov-product-inception-007).

An explicitly authorized prototype or experiment may begin before all normal inception evidence exists when its charter records:

- the question or hypothesis, scope, owner, time boundary, and stop criteria
- permitted users, data, environments, integrations, and risk controls
- missing gate evidence and accurate state
- prohibited production use and limitations
- disposition criteria for discard, further discovery, or deliberate transition

Prototype work must not silently become normal production implementation, product commitment, architecture of record, production data model, or supported operational service. Reuse requires the applicable inception gates, architecture and security review, production-quality implementation and validation, and an explicit decision record.

## Product lifecycle states

Normative control: [`GOV-PRODUCT-INCEPTION-008`](#gov-product-inception-008).

Product lifecycle state is distinct from component maturity governed by [`MATURITY_POLICY.md`](../MATURITY_POLICY.md). A package may remain `baseline` while an adopting product advances, and a `stable` package does not make a product production-ready.

| State | Evidence boundary |
|---|---|
| `idea` | A proposed opportunity exists; problem evidence may be incomplete. |
| `discovery` | Problem, users, outcomes, assumptions, and unknowns are being investigated. |
| `defined` | Concept and requirements evidence is sufficient for reviewed design and planning. |
| `prototype` | A bounded learning artifact operates under the prototype exception. |
| `MVP` | The minimum coherent scope is implemented or being validated against explicit criteria. |
| `beta` | Selected users or environments exercise a bounded release with known limitations and monitoring. |
| `production-candidate` | The candidate artifact and operating plan have passed the production-candidate gate below. |
| `production` | Accountable approval authorizes production use within stated scope and operating conditions. |
| `scaled-production` | Every applicable scaling area is `Verified` with current representative evidence and a stated supported envelope. Any `Applicable`, `NotRun`, or `Blocked` area prevents this state; every `NotApplicable` area has recorded justification. This boundary applies even when the SRE package is not otherwise selected. |
| `deprecated` | New use is discouraged or prohibited and migration, support, and communication boundaries are defined. |
| `retired` | Service and data disposition, access removal, dependencies, records, and residual obligations are closed or explicitly owned. |

Transitions require dated evidence, owner, reviewed artifact or revision, decision, limitations, and rollback or reversal considerations. Skipping a state is permitted only when the resulting gate evidence is still satisfied; labels must not be awarded by schedule or aspiration.

## Production-candidate gate

Normative control: [`GOV-PRODUCT-INCEPTION-009`](#gov-product-inception-009).

Before transition to `production-candidate`, the exact candidate must have applicable evidence for:

- reviewed requirements and acceptance criteria
- testing against the supported configuration and risk
- security and privacy readiness
- deployment and rollback
- observability, logging, monitoring, alerting, and SLOs or operating expectations
- backup, restore, recovery, and dependency-failure behavior
- production readiness, operational ownership, runbooks, and incident response
- known limitations, unresolved risks, owners, and approval conditions

Each area receives `Pass`, `Fail`, `Blocked`, or justified `NotApplicable` using existing readiness conventions. `NotRun` cannot support a pass for an applicable required area. The gate does not establish production approval or operational verification.

## Traceability and review triggers

Normative control: [`GOV-PRODUCT-INCEPTION-010`](#gov-product-inception-010).

Maintain the applicable chain `Idea -> Requirement -> Architecture Decision -> Implementation -> Test -> Release/Deployment -> Production Evidence` under the [Product Management Traceability Standard](../disciplines/product-management/standards/TRACEABILITY_STANDARD.md). Revisit gates after material changes to users, requirements, scope, evidence, architecture, technology, data, trust, artifact, deployment, operating conditions, ownership, or risk.

## Exceptions and prohibited shortcuts

Normative control: [`GOV-PRODUCT-INCEPTION-011`](#gov-product-inception-011).

- Do not treat code, a prototype, a passing test, or a gate checklist as proof of product completion or production readiness.
- Do not fabricate research, approval, deployment, or operational evidence.
- Do not use an exception to conceal a failed gate or missing authority.
- Approved exceptions follow [`EXCEPTION_PROCESS.md`](EXCEPTION_PROCESS.md) and retain visible failed or not-run checks.

## Completion boundary

Normative control: [`GOV-PRODUCT-INCEPTION-012`](#gov-product-inception-012).

Adopting this lifecycle does not establish product success, certification, compliance, release approval, or production readiness. Those claims require applicable implementation, validation, accountable review, authorization, and operational evidence.

Accountable authoritative-source review dates and sources are recorded in [`SOURCE_REVIEWS.json`](../SOURCE_REVIEWS.json), with durable findings under [`source-reviews/`](../source-reviews/).
