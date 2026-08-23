---
id: PROFILE-AI-AGENT-PKG-001
title: AI Agent Application Project Profile Package
version: 0.2.0
status: baseline
---
# AI Agent Application Project Profile Package

## Purpose

Define the minimum standards composition for applications that use language models or other AI systems to reason, retrieve content, call tools, generate outputs, or perform actions.

This package is a project-shape overlay. It composes governance, language, discipline, framework, platform, virtualization, operating-system, networking, and project-specific standards into a coherent starting point.

Status: **baseline**

## Canonical profile

The stable profile entry point is [`../AI_AGENT_APPLICATION.md`](../AI_AGENT_APPLICATION.md).

The canonical file provides the normative summary. This package supplies the detailed adoption model, standards, templates, and example.

## When to adopt

Adopt this profile when:

- tool-using AI agents
- retrieval-augmented applications
- workflow assistants
- autonomous or semi-autonomous task systems
- AI systems that generate or modify code, configuration, or operational actions

Do not use it as the primary profile for:

- static machine-learning inference with no agentic tool use unless other AI controls apply
- simple search without generated decisions
- non-AI automation

## Typical starting risk

`high`

Reclassify using actual project facts. Escalate for public exposure, privilege, destructive capability, sensitive data, tenant boundaries, weak rollback, availability, safety, or incomplete evidence.

## What this package does not replace

This package does not replace:

- governance authority and risk classification
- architecture and threat modeling
- language or framework standards
- platform ownership
- discipline packages
- organization policy or legal obligations
- project-specific tests and evidence
- production-readiness approval

## Package structure

```text
profiles/ai-agent-application/
├── AGENTS.md
├── README.md
├── MANIFEST.md
├── standards/
│   ├── PROJECT_BOUNDARY_STANDARD.md
│   ├── ARCHITECTURE_DECISION_STANDARD.md
│   ├── SECURITY_PRIVACY_STANDARD.md
│   ├── TESTING_VALIDATION_STANDARD.md
│   ├── OPERATIONS_RELEASE_STANDARD.md
│   └── COMPLETION_EVIDENCE.md
├── templates/
│   ├── ADOPTION_CHECKLIST.md
│   ├── REVIEW_CHECKLIST.md
│   └── EVIDENCE_RECORD_TEMPLATE.md
└── examples/
    └── ADOPTION_EXAMPLE.md
```

## Normative entry points

- [`AGENTS.md`](AGENTS.md)
- [`../AI_AGENT_APPLICATION.md`](../AI_AGENT_APPLICATION.md)
- [`MANIFEST.md`](MANIFEST.md)

## Required disciplines

- [Application Security](../../disciplines/application-security/)
- [Architecture and System Design](../../disciplines/architecture/)
- [Testing and Quality Engineering](../../disciplines/testing/)
- [API Engineering](../../disciplines/api-engineering/)
- [Privacy and Data Governance](../../disciplines/privacy/)
- [Observability](../../disciplines/observability/)
- [Software Supply Chain](../../disciplines/supply-chain/)

## Conditional disciplines

- [Product Management](../../disciplines/product-management/)
- [User Experience](../../disciplines/user-experience/)
- [Integration Engineering](../../disciplines/integration/)
- [Documentation](../../disciplines/documentation/)
- [Site Reliability Engineering](../../disciplines/sre/)
- [Data Engineering](../../disciplines/data-engineering/)
- [CI/CD](../../disciplines/ci-cd/)
- [Release Engineering](../../disciplines/release-engineering/)

A conditional discipline becomes required when its concern exists. “Another team handles that” is a responsibility statement only when the boundary and evidence are explicit.

Product Management becomes required when the agent scope defines or materially changes a product capability, intended outcome, requirement set, bounded MVP behavior, acceptance criteria, or product decision. User Experience becomes required when people set goals, provide context, review outputs, grant approval, recover from errors, or otherwise interact with materially changed agent behavior. Headless agent components may justify UX omission when their human workflow is governed by another scoped profile. Profile selection alone does not make either discipline mandatory.

## Language, framework, and platform selection

This profile intentionally does not choose a language, framework, or platform.

The adopting project must declare:

- implementation languages
- frameworks
- execution and deployment platforms
- supported versions
- package and dependency management
- build and release tooling
- compatibility commitments
- operational ownership

## Required project decisions

- tool authorization and allowlists
- prompt and retrieved-content trust boundaries
- human approval for consequential actions
- identity and credential delegation
- traceable model decisions, outputs, and tool calls
- evaluation for unsafe, incorrect, or deceptive behavior
- data retention and training boundaries
- fallback, stop, and incident behavior

## Architecture and trust boundaries

Document:

- model and provider boundary
- prompt and policy layer
- retrieval and content sources
- tool broker and authorization
- memory and data stores
- human approval and audit control plane

Use [`standards/PROJECT_BOUNDARY_STANDARD.md`](standards/PROJECT_BOUNDARY_STANDARD.md) and [`standards/ARCHITECTURE_DECISION_STANDARD.md`](standards/ARCHITECTURE_DECISION_STANDARD.md).

## Security and privacy expectations

- prompt injection and content trust
- tool parameter validation
- least-privilege delegated identity
- secret isolation from prompts and outputs
- data exfiltration controls
- human approval for consequential actions

Use [`standards/SECURITY_PRIVACY_STANDARD.md`](standards/SECURITY_PRIVACY_STANDARD.md).

## Testing and validation expectations

- task success and failure evaluations
- prompt-injection and adversarial tests
- tool authorization and parameter tests
- hallucination and unsupported-claim checks
- privacy and data leakage tests
- fallback, stop, timeout, and provider-failure behavior

Use [`standards/TESTING_VALIDATION_STANDARD.md`](standards/TESTING_VALIDATION_STANDARD.md).

## Operations and release expectations

- model and prompt version traceability
- tool-call audit logs
- quality and safety monitoring
- cost and rate limits
- incident shutdown and revocation
- evaluation and release ownership

Use [`standards/OPERATIONS_RELEASE_STANDARD.md`](standards/OPERATIONS_RELEASE_STANDARD.md).

## Suggested nested instructions

Consider scoped `AGENTS.md` files under:

- src/agent
- src/tools
- src/retrieval
- src/policy
- tests
- evals
- docs

Nested instructions specialize local work. They may be stricter but may not silently weaken governance or the selected packages.

## Common failure modes

- letting model output authorize actions
- trusting retrieved content as instructions
- broad tool credentials
- untraceable prompts or model versions
- fabricated evidence or citations
- no stop path for unsafe behavior

Other recurring failures include copying example facts, treating a profile as architecture approval, omitting conditional packages without justification, and claiming completion from partial evidence.

## Adoption workflow

1. Read root governance and the [profile collection guide](../README.md).
2. Confirm this is the primary or a scoped secondary profile.
3. Record profile-selection rationale.
4. Classify risk.
5. Select applicable language, discipline, framework, platform, virtualization, operating-system, and networking packages.
6. Complete the adoption checklist.
7. Document architecture, security, tests, operations, and release decisions.
8. Add nested instructions for distinct scopes.
9. Define exact validation commands and evidence.
10. Review exclusions and exceptions.
11. Validate links, IDs, manifests, and project behavior.
12. Obtain accountable review.

## Tailoring checklist

Before adoption, define:

- project purpose and non-goals
- users and operators
- interfaces and trust boundaries
- data and privacy
- identities and privileges
- state and storage
- dependencies and integrations
- deployment and environments
- supported versions
- validation and test environments
- observability and support
- recovery and migration
- release and compatibility
- evidence retention
- reviewers and approvers

## Evidence

Use [`templates/EVIDENCE_RECORD_TEMPLATE.md`](templates/EVIDENCE_RECORD_TEMPLATE.md) and [`standards/COMPLETION_EVIDENCE.md`](standards/COMPLETION_EVIDENCE.md).

Evidence should include:

- profile rationale
- selected and omitted packages
- risk
- changed scope
- decisions
- validation commands and results
- representative environments
- checks not run
- limitations and residual risk
- review and approval
- production-readiness status

## Common validation

From the standards repository root:

```bash
python tools/validate-standards/validate_repository.py
python tools/check-links/check_links.py
```

The adopting project must define executable checks for its real implementation.

## Templates and example

- [`ADOPTION_CHECKLIST.md`](templates/ADOPTION_CHECKLIST.md)
- [`REVIEW_CHECKLIST.md`](templates/REVIEW_CHECKLIST.md)
- [`EVIDENCE_RECORD_TEMPLATE.md`](templates/EVIDENCE_RECORD_TEMPLATE.md)
- [`ADOPTION_EXAMPLE.md`](examples/ADOPTION_EXAMPLE.md)

Examples are fictitious. Replace them with reviewed facts and actual evidence.

## Maintenance

Package changes must preserve stable IDs, update canonical and package files together, state migration impact, validate links, and disclose checks not run.

## Completion boundary

Adopting this package does not prove that the project is complete or production-ready. Completion requires implementation, validation, evidence, and accountable review.
