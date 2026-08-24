---
id: GOV-MANIFEST-001
title: Governance Package Manifest
version: 0.2.0
status: baseline
---

# Governance Package Manifest

## Required entry points

- `AGENTS.md`
- `README.md`
- `MANIFEST.md`
- `POLICY_MAP.md`
- `ADOPTION_GUIDE.md`
- `OPERATING_MODEL.md`
- `POLICY_LIFECYCLE.md`
- `CONTROL_EVIDENCE_MODEL.md`
- `GOVERNANCE_DECISION_MATRIX.md`
- `PRODUCT_INCEPTION_LIFECYCLE.md`

## Policies

- `ORGANIZATION_CONTRACT.md`
- `AGENT_WORKING_METHOD.md`
- `RISK_CLASSIFICATION.md`
- `COMPLETION_EVIDENCE.md`
- `EXCEPTION_PROCESS.md`
- `AI_GENERATED_CODE_POLICY.md`
- `HUMAN_REVIEW_POLICY.md`
- `PRODUCTION_READINESS.md`
- `SECURE_DEVELOPMENT_POLICY.md`
- `THREAT_MODELING_POLICY.md`
- `VULNERABILITY_RESPONSE.md`

## Templates

- `templates/AI_GENERATED_CODE_REVIEW_TEMPLATE.md`
- `templates/AUTHORIZATION_RECORD_TEMPLATE.md`
- `templates/COMPLETION_EVIDENCE_TEMPLATE.md`
- `templates/EXCEPTION_RECORD_TEMPLATE.md`
- `templates/GOVERNANCE_ADOPTION_CHECKLIST.md`
- `templates/GOVERNANCE_REVIEW_CHECKLIST.md`
- `templates/HUMAN_REVIEW_RECORD_TEMPLATE.md`
- `templates/POLICY_CHANGE_RECORD_TEMPLATE.md`
- `templates/PRODUCTION_READINESS_REVIEW_TEMPLATE.md`
- `templates/RISK_ACCEPTANCE_TEMPLATE.md`
- `templates/RISK_ASSESSMENT_TEMPLATE.md`
- `templates/THREAT_MODEL_REVIEW_TEMPLATE.md`
- `templates/VULNERABILITY_TRIAGE_TEMPLATE.md`

## Examples and evidence

- `examples/AI_CODE_REVIEW_EXAMPLE.md`
- `examples/EXCEPTION_WORKFLOW_EXAMPLE.md`
- `examples/GOVERNANCE_ADOPTION_EXAMPLE.md`
- `examples/HIGH_RISK_CHANGE_EXAMPLE.md`
- `examples/LOW_RISK_CHANGE_EXAMPLE.md`
- `examples/MODERATE_RISK_CHANGE_EXAMPLE.md`
- `examples/PRODUCTION_READINESS_EXAMPLE.md`
- `examples/VULNERABILITY_RESPONSE_EXAMPLE.md`
- `examples/evidence/completion-result.example.json`
- `examples/evidence/exception-record.example.json`
- `examples/evidence/risk-classification.example.json`

## Acceptance checks

- Every Markdown file has a unique front-matter ID.
- Existing governance document and rule identifiers remain present.
- Policies define applicability, roles, evidence, gates, exceptions, and review triggers.
- README, policy map, manifest, templates, and examples agree.
- JSON evidence parses and matches the referenced schema shape.
- Relative links resolve.
- No unresolved placeholders, production values, credentials, or real vulnerability details exist.
- Root catalog, manifest, and roadmap are synchronized.
