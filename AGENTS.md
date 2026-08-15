# Repository Agent Instructions

## Purpose

This repository contains public engineering standards for coding agents. Changes must improve safety, clarity, maintainability, testability, portability, or evidence quality without silently weakening existing controls.

## Required reading order

Before modifying this repository:

1. Read `README.md`, `CONTRIBUTING.md`, `SECURITY.md`, `MAINTAINERS.md`, and `CATALOG.md`.
2. Read the applicable governance files.
3. Read `RELEASE_POLICY.md` and `MATURITY_POLICY.md` when a change affects compatibility, versioning, maturity, deprecation, tags, release notes, or release automation.
4. Read every scoped `AGENTS.md` between the repository root and the target file.
5. Inspect referenced standards, schemas, examples, templates, release notes, and migration notes.
6. Classify the change as editorial, normative, compatibility-related, security-related, breaking, or release-related.
7. Identify the applicable CODEOWNER, area owner, and whether specialist or release review is recommended or independently required.

## Mandatory working method

- Define the smallest coherent scope.
- Inspect existing behavior before proposing replacements.
- Preserve stable rule identifiers.
- Keep normative requirements testable.
- Update cross-references, manifests, examples, schemas, templates, changelog entries, and migration notes affected by the change.
- Classify repository version impact according to `RELEASE_POLICY.md`.
- Validate JSON, YAML, Markdown links, repository structure, ownership files, release contracts, and executable tooling.
- Report what was validated and what was not.
- Do not claim completion without evidence.
- Do not treat CODEOWNERS routing as proof of authorization or independent review.
- Do not invent a requirement for external approval when `MAINTAINERS.md` classifies specialist review as recommended rather than mandatory.

## Non-negotiable rules

- Do not weaken security controls merely to simplify generated code.
- Do not remove testing, review, documentation, or evidence requirements without documented rationale.
- Do not add credentials, tokens, private keys, production host names, internal identifiers, or sensitive examples.
- Use fictitious values in examples.
- Do not copy incompatible third-party content.
- Summarize external standards and link to authoritative sources.
- Do not create placeholder `AGENTS.md` files that look authoritative but contain incomplete requirements.
- Mark planned packages as planned rather than pretending they are complete.
- Do not reformat unrelated files.
- Do not modify generated or vendored files unless the task requires it.
- Do not bypass repository validation to make checks pass.
- Do not merge a change that lacks the review class required by `MAINTAINERS.md`.
- Do not represent self-review as independent specialist review.
- Do not create a release tag from an unmerged branch or unreviewed commit.
- Do not move or recreate a published release tag.
- Do not promote a component to `stable` without the evidence and review required by `MATURITY_POLICY.md`.

## Required governance

All changes are subject to:

- `governance/ORGANIZATION_CONTRACT.md`
- `governance/AGENT_WORKING_METHOD.md`
- `governance/RISK_CLASSIFICATION.md`
- `governance/COMPLETION_EVIDENCE.md`
- `governance/EXCEPTION_PROCESS.md`
- `governance/AI_GENERATED_CODE_POLICY.md`
- `governance/SECURE_DEVELOPMENT_POLICY.md`
- `governance/HUMAN_REVIEW_POLICY.md`
- `MAINTAINERS.md`
- `.github/CODEOWNERS`
- `RELEASE_POLICY.md`
- `MATURITY_POLICY.md`

## Completion evidence

The final summary must include:

- files created, modified, or deleted
- normative behavior changed
- repository version and release impact
- security impact
- compatibility impact
- validation performed
- validation not performed
- required owners and reviewers
- remaining limitations and risks
