---
id: GOV-INDEX-001
title: Governance Standards
version: 0.2.0
status: baseline
---

# Governance Standards

## Purpose

The governance layer defines the control plane for agent-assisted engineering. It establishes authority, precedence, risk, review, evidence, exceptions, security, production readiness, and vulnerability handling across every language, framework, platform, virtualization, operating-system, networking, discipline, profile, and example in this repository.

Governance answers questions that implementation standards cannot answer safely:

- Who is authorized to request, review, approve, and operate a change?
- Which obligations take precedence?
- How is risk classified and reassessed?
- What evidence is required before claiming completion?
- Which work requires independent human review?
- How are temporary deviations approved and expired?
- What separates a successful build from production readiness?
- How are AI-generated changes reviewed?
- How are threats and vulnerabilities handled?
- What records must exist when humans and agents disagree?

The governance package improves consistency and traceability. It does not grant authority, replace law or organizational policy, or make a repository production-ready by being copied into it. Paperwork is not magic, despite several centuries of determined experimentation.

## Precedence model

Governance uses both **authority precedence** and **scope specificity**.

Authority precedence:

1. Applicable legal, regulatory, contractual, safety, and security obligations
2. Explicit authorized user or organizational direction within delegated authority
3. Root repository `AGENTS.md`
4. Governance policies
5. Selected project-profile, language, discipline, framework, platform, virtualization, operating-system, and networking standards
6. Repository conventions and general agent preferences

Scope specificity:

- The nearest applicable nested `AGENTS.md` controls local work when it specializes or strengthens the applicable baseline.
- A nested instruction must not silently weaken root instructions, governance policies, or selected standards.
- A weaker, ambiguous, or authority-changing conflict must stop and be resolved by an accountable authority or the documented exception process.

Material conflicts must be recorded. Specificity is not permission to bypass governance.

## Governance policy catalog

| Policy | Primary question |
|---|---|
| [Organization Contract](ORGANIZATION_CONTRACT.md) | What is non-negotiable, and who remains accountable? |
| [Agent Working Method](AGENT_WORKING_METHOD.md) | What sequence must an agent follow from discovery through reporting? |
| [Risk Classification](RISK_CLASSIFICATION.md) | How much review, validation, authorization, and evidence are required? |
| [Completion Evidence](COMPLETION_EVIDENCE.md) | What proof is required before work may be reported complete? |
| [Exception Process](EXCEPTION_PROCESS.md) | How may a temporary deviation be requested, approved, monitored, and closed? |
| [AI-Generated Code Policy](AI_GENERATED_CODE_POLICY.md) | How is AI-assisted work reviewed, verified, and attributed? |
| [Human Review Policy](HUMAN_REVIEW_POLICY.md) | Which decisions require accountable human review and approval? |
| [Production Readiness](PRODUCTION_READINESS.md) | What operational evidence is required before production use? |
| [Secure Development Policy](SECURE_DEVELOPMENT_POLICY.md) | How is security integrated throughout engineering work? |
| [Threat Modeling Policy](THREAT_MODELING_POLICY.md) | When is threat analysis required, and what must it produce? |
| [Vulnerability Response](VULNERABILITY_RESPONSE.md) | How are vulnerabilities received, contained, fixed, verified, and closed? |

See [POLICY_MAP.md](POLICY_MAP.md) for dependencies, records, triggers, and decision relationships.

## Governance operating model

Governance is a lifecycle, not a folder:

```text
request
  -> identify authority and obligations
  -> discover context
  -> classify risk
  -> define acceptance criteria and evidence
  -> authorize consequential work
  -> implement in safe phases
  -> validate
  -> review
  -> approve or reject
  -> release or operate
  -> monitor
  -> learn, remediate, or renew exceptions
```

Detailed roles and decision responsibilities are described in [OPERATING_MODEL.md](OPERATING_MODEL.md).

New products and material capabilities also follow the [Product Inception Lifecycle](PRODUCT_INCEPTION_LIFECYCLE.md), which defines evidence-based Concept, Requirements, Design, and Build gates plus product lifecycle states without replacing component maturity policy.

## Required roles

Projects must identify roles proportionate to risk:

- **Requester:** states the desired outcome and constraints.
- **Accountable owner:** owns the system, change, and residual risk.
- **Implementer or agent:** performs work within authorization.
- **Reviewer:** independently evaluates scope, evidence, and risk.
- **Approver:** authorizes a decision within delegated authority.
- **Operator or service owner:** accepts operational and recovery responsibility.
- **Exception owner:** monitors deviation, controls, expiration, and remediation.
- **Security, privacy, accessibility, data, legal, or platform specialist:** reviews applicable specialist concerns.

One person may hold multiple roles for low-risk work. High and critical work requires enough separation to challenge assumptions and prevent self-approval.

## Governance records

A mature adoption normally maintains:

- risk classification
- authorization record
- scope and acceptance criteria
- threat model when required
- validation and completion evidence
- human review and approval record
- exception record where applicable
- production-readiness decision
- vulnerability triage and closure records
- policy change and migration records
- residual-risk acceptance
- follow-up actions and expiration dates

Templates are under [`templates/`](templates/).

## Evidence states

Governance records must distinguish:

- **proposed:** requested but not authorized
- **authorized:** approved to proceed within defined scope
- **implemented:** change exists
- **validated:** relevant checks passed
- **partially validated:** some required checks are absent or inconclusive
- **reviewed:** accountable reviewer evaluated the evidence
- **approved:** authorized authority accepted the decision and limitations
- **operationally verified:** behavior was confirmed in an appropriate runtime context
- **closed:** required follow-up, expiration, or remediation is complete

These states must not be collapsed into one cheerful “done” field.

## Risk scaling

- **Low:** limited, reversible, narrow, and non-sensitive.
- **Moderate:** meaningful behavior, integration, data, deployment, or operational impact.
- **High:** privileged, destructive, public, security-sensitive, privacy-sensitive, hard-to-reverse, or broad blast radius.
- **Critical:** potential severe safety, legal, systemic, security, availability, or irreversible impact.

See [RISK_CLASSIFICATION.md](RISK_CLASSIFICATION.md) and [GOVERNANCE_DECISION_MATRIX.md](GOVERNANCE_DECISION_MATRIX.md).

## Adoption procedure

1. Read root repository instructions.
2. Review this README and [AGENTS.md](AGENTS.md).
3. Identify applicable external obligations.
4. Adopt all governance policies as the default baseline.
5. Assign owners, reviewers, approvers, and operators.
6. Define risk thresholds and delegated authority.
7. Select record storage and retention.
8. Tailor templates without weakening policy.
9. Define how governance integrates with pull requests, CI, releases, change management, and incident response.
10. Validate identifiers and links.
11. Obtain accountable approval for the adoption.
12. Review governance periodically and after material incidents or policy changes.

Use [ADOPTION_GUIDE.md](ADOPTION_GUIDE.md) and [`templates/GOVERNANCE_ADOPTION_CHECKLIST.md`](templates/GOVERNANCE_ADOPTION_CHECKLIST.md).

## Per-change workflow

For each material change:

1. Identify scope and target.
2. Confirm authority.
3. Classify risk.
4. Identify applicable policies and standards.
5. For new products or material capabilities, evaluate the applicable Product Inception gates.
6. Define acceptance criteria and evidence.
7. Determine whether threat modeling, specialist review, rollback, or exception handling is required.
8. Authorize consequential execution.
9. Implement the smallest coherent change.
10. Validate exact behavior.
11. Review evidence and limitations.
12. Approve, reject, or request changes.
13. Record production or operational decision when applicable.
14. Track follow-up, exception expiry, and residual risk.

## Exceptions

Exceptions are temporary, explicit, owned, reviewed, and expiring. They are not private agreements to ignore failed controls.

An exception must identify:

- exact rule
- reason
- risk
- affected scope
- compensating controls
- control owner
- approver
- expiration
- remediation or closure plan
- review schedule

See [EXCEPTION_PROCESS.md](EXCEPTION_PROCESS.md).

## Policy lifecycle

Governance policies require versioning, review, migration, deprecation, and traceability. A policy change can alter review or production expectations across every downstream package, so “just wording” deserves more scrutiny than the phrase suggests.

See [POLICY_LIFECYCLE.md](POLICY_LIFECYCLE.md).

## Control and evidence model

Normative rules should define:

- stable rule ID
- requirement
- applicability
- accountable role
- expected evidence
- decision gate
- exception boundary
- review trigger

See [CONTROL_EVIDENCE_MODEL.md](CONTROL_EVIDENCE_MODEL.md).

## Validation

From the repository root:

```bash
python tools/validate-standards/validate_repository.py
python tools/check-links/check_links.py
```

An adopting organization must also validate governance integration, authority, record retention, approval workflows, and operational use. A Markdown link checker is useful, but it has never stopped an unqualified approver from clicking a green button.

## Maturity

Status: **baseline**

This governance system is suitable for adoption and review but must be tailored to real authority, obligations, risk appetite, and operating context. It does not claim legal compliance, certification, production approval, or universal completeness.
