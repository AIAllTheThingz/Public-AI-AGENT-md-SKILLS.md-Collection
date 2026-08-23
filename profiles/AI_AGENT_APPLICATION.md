---
id: PROFILE-AI-AGENT
title: AI Agent Application Project Profile
version: 0.2.0
status: baseline
applies_to:
  - ai-agent-application
depends_on:
  - GOV-CONTRACT
  - GOV-WORK
  - GOV-RISK
  - GOV-EVIDENCE
---
# AI Agent Application Project Profile

## Purpose

Define the minimum standards composition for applications that use language models or other AI systems to reason, retrieve content, call tools, generate outputs, or perform actions.

## Complete package

Use the complete package at [`ai-agent-application/`](ai-agent-application/). This canonical file remains the stable profile entry point.

## Applicability

This profile applies to:

- tool-using AI agents
- retrieval-augmented applications
- workflow assistants
- autonomous or semi-autonomous task systems
- AI systems that generate or modify code, configuration, or operational actions

It normally does not describe:

- static machine-learning inference with no agentic tool use unless other AI controls apply
- simple search without generated decisions
- non-AI automation

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

- `disciplines/application-security/AGENTS.md`
- `disciplines/architecture/AGENTS.md`
- `disciplines/testing/AGENTS.md`
- `disciplines/api-engineering/AGENTS.md`
- `disciplines/privacy/AGENTS.md`
- `disciplines/observability/AGENTS.md`
- `disciplines/supply-chain/AGENTS.md`

## Conditionally required disciplines

- [Product Management](../disciplines/product-management/)
- [User Experience](../disciplines/user-experience/)
- `disciplines/integration/AGENTS.md`
- `disciplines/documentation/AGENTS.md`
- `disciplines/sre/AGENTS.md`
- `disciplines/data-engineering/AGENTS.md`
- `disciplines/ci-cd/AGENTS.md`
- `disciplines/release-engineering/AGENTS.md`

Conditional packages become required when their concern is present. Document every omission that would reasonably appear applicable.

Product Management becomes required when the agent scope defines or materially changes a product capability, intended outcome, requirement set, bounded MVP behavior, acceptance criteria, or product decision. User Experience becomes required when people set goals, provide context, review outputs, grant approval, recover from errors, or otherwise interact with materially changed agent behavior. Headless agent components may justify UX omission when their human workflow is governed by another scoped profile. Profile selection alone does not make either discipline mandatory.

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

- model and provider boundary
- prompt and policy layer
- retrieval and content sources
- tool broker and authorization
- memory and data stores
- human approval and audit control plane

## Security and privacy focus

- prompt injection and content trust
- tool parameter validation
- least-privilege delegated identity
- secret isolation from prompts and outputs
- data exfiltration controls
- human approval for consequential actions

## Testing and validation

- task success and failure evaluations
- prompt-injection and adversarial tests
- tool authorization and parameter tests
- hallucination and unsupported-claim checks
- privacy and data leakage tests
- fallback, stop, timeout, and provider-failure behavior

## Operations and release

- model and prompt version traceability
- tool-call audit logs
- quality and safety monitoring
- cost and rate limits
- incident shutdown and revocation
- evaluation and release ownership

## Suggested nested instruction scopes

- `src/agent/AGENTS.md`
- `src/tools/AGENTS.md`
- `src/retrieval/AGENTS.md`
- `src/policy/AGENTS.md`
- `tests/AGENTS.md`
- `evals/AGENTS.md`
- `docs/AGENTS.md`

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
