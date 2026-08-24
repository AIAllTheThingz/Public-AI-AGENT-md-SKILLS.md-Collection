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
  - GOV-PROD
  - GOV-EXCEPTION
---

# Product Inception Lifecycle

## Purpose

Define a proportionate, evidence-based path from idea through build while preventing normal production implementation from outrunning product, requirements, UX, architecture, and validation decisions.

## Applicability

Normative control: [`GOV-PRODUCT-INCEPTION-001`](#gov-product-inception-001).

This lifecycle applies only when explicitly selected for a project or change. Adopting this repository, its governance, a project profile, or the Product Management package does not select it. Once selected, it governs the selected scope for a new product, material capability, or material change in intended users, outcomes, requirements, architecture, trust boundaries, or operating model. Existing records that answer a gate count as its evidence. For small changes within the selected scope, record a concise gate decision that references those records.

Selecting this lifecycle does not silently select a discipline package. Before the Build Gate can pass, explicitly select the Product Management package and satisfy its [Requirement Traceability Standard](../disciplines/product-management/standards/TRACEABILITY_STANDARD.md) for every material requirement. A lifecycle state that depends on another discipline contract may be assigned only after that package is explicitly selected and its referenced standard is satisfied. In particular, `production-candidate` requires the Site Reliability Engineering package and its complete [Production Readiness Standard](../disciplines/sre/standards/PRODUCTION_READINESS_STANDARD.md), and `scaled-production` additionally requires its complete [Scaling Strategy Standard](../disciplines/sre/standards/SCALING_STRATEGY_STANDARD.md).

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

**Requirement:** Use only `Planned`, `Implemented`, `Tested`, `Reviewed`, `OperationallyVerified`, `NotRun`, `Blocked`, or justified `NotApplicable` for lifecycle evidence states, record gate decisions separately, and do not treat a passing gate as proof of a later lifecycle state.

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

**Requirement:** Normal production implementation must not start unless the Concept, Requirements, Design, and Build Gate decisions are explicitly `Pass` for the reviewed scope, every applicable package and technology selection or justified `NotApplicable` decision, acceptance criteria, validation strategy, implementation plan, ownership, dependencies, rollback considerations, and evidence locations.

**Expected evidence:** Linked `Pass` decisions for the prerequisite Concept, Requirements, and Design Gates plus a Build decision of `Pass`, `Fail`, or `Blocked` identifying the reviewed scope, selected packages and reviewed omission decisions, plan, owners, validation strategy, rollback considerations, and re-review triggers.

### GOV-PRODUCT-INCEPTION-007

**Requirement:** Start pre-gate prototype or experiment work only under an explicit bounded charter, and do not allow that work to become production implementation, product commitment, architecture of record, production data model, or supported service without the applicable gates and reviews.

**Expected evidence:** Authorized prototype or experiment charter, accurate missing-evidence states, stop and disposition criteria, prohibited-use boundary, and any later transition decision.

### GOV-PRODUCT-INCEPTION-008

**Requirement:** Assign product lifecycle states only from dated evidence for the reviewed artifact and scope, with accountable ownership, limitations, and rollback or reversal considerations. Assign `scaled-production` only while the `production` evidence boundary remains satisfied and after explicitly selecting the Site Reliability Engineering package and satisfying its complete [Scaling Strategy Standard](../disciplines/sre/standards/SCALING_STRATEGY_STANDARD.md): the overall scaling-strategy decision is `Verified`, every applicable scaling area is `Verified` with current representative evidence and a stated supported envelope, any `Applicable`, `NotRun`, or `Blocked` area prevents that state, and every `NotApplicable` area requires justification.

**Expected evidence:** Lifecycle transition record naming the prior and new state, artifact or revision, owner, decision, supporting evidence, limitations, and reversal considerations; a `scaled-production` transition also retains the production approval, records the SRE package selection, and links the complete scaling applicability matrix, overall `Verified` decision, decision authority, supported envelope, and evidence for every applicable area.

### GOV-PRODUCT-INCEPTION-009

**Requirement:** Transition to `production-candidate` only after the Build Gate and its prerequisite Concept, Requirements, and Design Gates are `Pass`; every material requirement is implemented; every applicable functional and nonfunctional acceptance criterion has a current explicit `Pass` for the exact candidate, supported configuration, and representative environment; the Site Reliability Engineering package is explicitly selected; and its complete [Production Readiness Standard](../disciplines/sre/standards/PRODUCTION_READINESS_STANDARD.md) is satisfied for the exact candidate and operating scope. Any acceptance criterion with a `Fail`, `Blocked`, `NotRun`, missing, stale, or different-candidate result prevents the transition. The readiness overall decision must be `Pass`, every applicable readiness area must be `Pass`, every `NotApplicable` result must be justified, and no applicable area may be `Fail`, `Blocked`, or `NotRun`.

**Expected evidence:** Linked prerequisite gate decisions; a complete acceptance matrix or equivalent mapping every material requirement and acceptance criterion to implementation evidence, validation method, exact candidate and environment, current `Pass`, `Fail`, `Blocked`, `NotRun`, or justified `NotApplicable` result, primary evidence, and owner; SRE package selection; the standard's complete per-area `Pass`, `Fail`, `Blocked`, or justified `NotApplicable` matrix for the exact candidate; and a separate overall readiness decision with accountable authority, operating scope, conditions, checks not run, and remaining limitations.

### GOV-PRODUCT-INCEPTION-010

**Requirement:** Before the Build Gate can pass, explicitly select the [Product Management package](../disciplines/product-management/) and satisfy its [Requirement Traceability Standard](../disciplines/product-management/standards/TRACEABILITY_STANDARD.md) for every material requirement. Maintain that end-to-end traceability and re-evaluate affected gates after a material change to users, requirements, scope, evidence, architecture, technology, data, trust, artifact, deployment, operating conditions, ownership, or risk.

**Expected evidence:** Product Management package selection, a complete traceability matrix or equivalent links, and dated gate re-review records for every material change trigger.

### GOV-PRODUCT-INCEPTION-011

**Requirement:** Do not treat implementation artifacts, prototypes, tests, or checklists as product completion or production-readiness proof, and do not use an exception to conceal a failed gate, missing evidence, or missing authority or to assign a lifecycle state whose evidence boundary is not satisfied.

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

Lifecycle evidence records use only `Planned`, `Implemented`, `Tested`, `Reviewed`, `OperationallyVerified`, `NotRun`, `Blocked`, or `NotApplicable`. `NotApplicable` requires rationale. Gate decisions use the outcomes defined by the applicable gate and remain separate from evidence states. A passing gate means required evidence is sufficient for the next bounded phase; it does not prove later lifecycle states.

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

- `Pass` decisions for the Concept, Requirements, and Design Gates for the reviewed scope
- approved implementation scope and explicit exclusions
- selected applicable project profile
- selected every applicable governance, language, discipline, framework, platform, virtualization, operating-system, and networking package, with a justified `NotApplicable` decision for each reviewed omission
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
| `defined` | The Concept and Requirements gates are `Pass` for the reviewed scope. |
| `prototype` | A bounded learning artifact operates under the prototype exception. |
| `MVP` | The Build Gate is `Pass` and the minimum coherent scope is implemented or undergoing bounded validation against explicit criteria. |
| `beta` | The Build Gate is `Pass`; selected users or environments exercise a bounded release with known limitations, monitoring, ownership, and stop or rollback conditions. The label does not authorize production exposure, which separately requires the applicable production-readiness evidence and accountable approval. |
| `production-candidate` | The Build Gate and its prerequisite Concept, Requirements, and Design Gates are `Pass`; every material requirement is implemented; every applicable functional and nonfunctional acceptance criterion has a current explicit `Pass` for the exact candidate, supported configuration, and representative environment; the Site Reliability Engineering package is selected; and its complete Production Readiness Standard has an overall `Pass` for the exact candidate and operating scope, with every applicable area `Pass` and every `NotApplicable` area justified. |
| `production` | The `production-candidate` evidence boundary remains satisfied and an accountable human with delegated authority approves production use within the stated artifact, scope, configuration, environment, and operating conditions. |
| `scaled-production` | The `production` evidence boundary remains satisfied; the Site Reliability Engineering package is selected; and its complete Scaling Strategy Standard is satisfied: the overall scaling-strategy decision is `Verified`, and every applicable scaling area is `Verified` with current representative evidence and a stated supported envelope. Any `Applicable`, `NotRun`, or `Blocked` area prevents this state; every `NotApplicable` area has recorded justification. |
| `deprecated` | New use is discouraged or prohibited and migration, support, and communication boundaries are defined. |
| `retired` | Service and data disposition, access removal, dependencies, records, and residual obligations are closed or explicitly owned. |

Transitions require dated evidence, owner, reviewed artifact or revision, decision, limitations, and rollback or reversal considerations. Skipping a state is permitted only when every evidence boundary and prerequisite for the resulting state is satisfied; labels must not be awarded by schedule, aspiration, or exception.

## Production-candidate gate

Normative control: [`GOV-PRODUCT-INCEPTION-009`](#gov-product-inception-009).

Before transition to `production-candidate`, the Build Gate and its prerequisite Concept, Requirements, and Design Gates must be `Pass`; every material requirement must be implemented; and every applicable functional and nonfunctional acceptance criterion must have a current explicit `Pass` for the exact candidate, supported configuration, and representative environment. Record acceptance as a decision separate from execution or evidence state: `Tested`, `Reviewed`, or the presence of test output does not imply `Pass`. Any `Fail`, `Blocked`, `NotRun`, missing, stale, or different-candidate acceptance result prevents transition, and every `NotApplicable` result requires reviewed justification.

Also explicitly select the [Site Reliability Engineering package](../disciplines/sre/) and satisfy its complete [Production Readiness Standard](../disciplines/sre/standards/PRODUCTION_READINESS_STANDARD.md). The readiness record must assess every area defined by that standard—Deployment; Rollback and recovery; Backup and restore; Data migration; Observability; Capacity; Security; Privacy; Failure behavior; Operations; Cost; and Limitations and risks—rather than a locally chosen subset. Production-readiness results do not replace functional or nonfunctional acceptance decisions.

Each area receives `Pass`, `Fail`, `Blocked`, or justified `NotApplicable`; `NotRun` remains an evidence state and cannot support `Pass` for an applicable area. Transition requires a separate overall `Pass` tied to the exact candidate, supported configuration, representative environment, operating scope, accountable decision authority, conditions, limitations, unresolved risks, and checks not run. This gate does not itself establish production approval or operational verification.

## Traceability and review triggers

Normative control: [`GOV-PRODUCT-INCEPTION-010`](#gov-product-inception-010).

Maintain the applicable chain `Idea -> Requirement -> Architecture Decision -> Implementation -> Test -> Release/Deployment -> Production Evidence` under the [Product Management Traceability Standard](../disciplines/product-management/standards/TRACEABILITY_STANDARD.md). Revisit gates after material changes to users, requirements, scope, evidence, architecture, technology, data, trust, artifact, deployment, operating conditions, ownership, or risk.

## Exceptions and prohibited shortcuts

Normative control: [`GOV-PRODUCT-INCEPTION-011`](#gov-product-inception-011).

- Do not treat code, a prototype, a passing test, or a gate checklist as proof of product completion or production readiness.
- Do not fabricate research, approval, deployment, or operational evidence.
- Do not use an exception to conceal a failed gate or missing authority.
- Do not use an exception to convert `Fail`, `Blocked`, `NotRun`, or missing package evidence into `Pass`, `Verified`, or a later lifecycle state; an authorized bounded activity retains its accurate lower or blocked state.
- Approved exceptions follow [`EXCEPTION_PROCESS.md`](EXCEPTION_PROCESS.md) and retain visible failed or not-run checks.

## Related policies, standards, and templates

- [Organization Contract](ORGANIZATION_CONTRACT.md)
- [Agent Working Method](AGENT_WORKING_METHOD.md)
- [Risk Classification](RISK_CLASSIFICATION.md)
- [Completion Evidence](COMPLETION_EVIDENCE.md)
- [Production Readiness](PRODUCTION_READINESS.md)
- [Exception Process](EXCEPTION_PROCESS.md)
- [Product Management Requirement Traceability Standard](../disciplines/product-management/standards/TRACEABILITY_STANDARD.md)
- [Product Management Evidence Record Template](../disciplines/product-management/templates/EVIDENCE_RECORD_TEMPLATE.md)
- [SRE Production Readiness Standard](../disciplines/sre/standards/PRODUCTION_READINESS_STANDARD.md)
- [SRE Scaling Strategy Standard](../disciplines/sre/standards/SCALING_STRATEGY_STANDARD.md)
- [SRE Evidence Record Template](../disciplines/sre/templates/EVIDENCE_RECORD_TEMPLATE.md)

## Completion boundary

Normative control: [`GOV-PRODUCT-INCEPTION-012`](#gov-product-inception-012).

Adopting this lifecycle does not establish product success, certification, compliance, release approval, or production readiness. Those claims require applicable implementation, validation, accountable review, authorization, and operational evidence.

Accountable authoritative-source review dates and sources are recorded in [`SOURCE_REVIEWS.json`](../SOURCE_REVIEWS.json), with durable findings under [`source-reviews/`](../source-reviews/).
