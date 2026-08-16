---
id: MATURITY-TERRAFORM-OPENTOFU-2026-08-16
title: Terraform and OpenTofu Baseline to Stable Maturity Review
version: 1.0.0
status: baseline
---

# Terraform and OpenTofu Baseline to Stable Maturity Review

## Review identity

- Review ID: `MR-TERRAFORM-OPENTOFU-2026-08-16`
- Component: `languages/terraform-opentofu`
- Component version: `unversioned package at repository VERSION 0.10.0`
- Repository commit reviewed: `ba4901c72f4c1fccda517280946f1fb1b6d2824c`
- Current maturity: `baseline`
- Proposed maturity: `stable`
- Owner: `Language standards maintainers`
- Reviewers: `AIAllTheThingz` maintainer evidence review
- Review date: `2026-08-16`

## Scope and applicability

This review covers the Terraform/OpenTofu language package governing HCL, modules, providers, backends/state, plans, controlled applies, tests, security, and completion evidence.

## Normative quality

The package is structurally complete and explicit about choosing one execution engine, pinning versions/providers/modules, state security/recovery, plan review, controlled apply, imports/moves/replacements, and environment-specific authorization.

## Adoption evidence

- Package-level #47 `terraform-opentofu-infrastructure` adoption exercise: Passed, including rejection of ambiguous `engine: both` evidence.
- Real downstream #41 pilots: **none of the three representative downstream repositories used Terraform/OpenTofu**.

Repository-controlled fixtures are not substitutes for the two representative real adoptions required by `MATURITY_POLICY.md`.

## Compatibility inventory

The package exposes Terraform/OpenTofu engine selection, module/provider/state/plan/apply standards, templates, examples, and evidence behavior. Provider/backend/runtime compatibility is inherently environment-specific and must be pinned by adopters.

## Validation evidence

The package-level adoption harness provides positive, negative, invalid-selection, evidence, and overwrite-failure coverage. No live provider/backend or representative downstream repository was exercised by #41, and no infrastructure apply was performed.

## Source currency

- Authoritative sources reviewed: HashiCorp Terraform CLI documentation; OpenTofu 1.12 release material
- Last source review date: `2026-08-15`
- Current source-review registry maturity: `baseline`
- Known concern: exact engine, provider, backend, and module compatibility remains adopter-specific

## Security and operational review

The package has strong state, credential, plan, apply, drift, rollback/recovery, and destructive-action boundaries. The promotion blocker is adoption evidence, not lack of security language.

## Open findings and conditions

- Fewer than two representative downstream adoptions exist; the current count from #41 is zero.
- No real provider/backend/state workflow was exercised.
- No production apply is required for maturity, but realistic downstream plan/state/provider evidence is required before claiming broad stable adoption confidence.

## Decision

`deferred`

## Rationale

The package meets structure, source-review, and package-test expectations but fails the explicit two-representative-adoptions requirement. It remains `baseline`.

## Conditions and owners

- Complete at least two representative downstream adoptions or independently reviewed composition exercises that actually use Terraform or OpenTofu.
- Record engine/provider/backend/state boundaries and validation outcomes for those adoptions.
- Owner: `Language standards maintainers` with infrastructure adopters for downstream evidence.

## Next review

- Next review date or trigger: `after two representative Terraform/OpenTofu downstream adoption records exist`
- Responsible owner: `Language standards maintainers`

## Release linkage

- Target repository release: `Not scheduled while deferred`
- Release-note entry: `No stable promotion; deferral recorded under issue #42`
