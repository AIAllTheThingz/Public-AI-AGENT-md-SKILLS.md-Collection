---
id: TF-PKG-001
status: baseline
title: Terraform and OpenTofu Package
---

# Terraform and OpenTofu Language Package

This package provides project-agnostic engineering standards for declarative infrastructure code, modules, providers, state, plans, imports, moves, and controlled applies.

It defines how coding agents should inspect, design, implement, test, secure, document, plan, apply, verify, and report infrastructure changes. It does not select a cloud provider, state backend, organization topology, or production approval process for the adopting project.

## Package status

**Status:** `baseline`

The package is structurally complete and suitable for adoption. Projects must tailor engine, provider, backend, account, environment, policy, deployment, and organization-specific requirements before treating it as a final production standard.

## Intended scope

- Terraform or OpenTofu root modules
- reusable infrastructure modules
- provider and backend configuration
- state, imports, moves, and migrations
- plans, policy checks, tests, and controlled applies

## Engine baseline

- Declare one execution engine per workflow: Terraform or OpenTofu.
- Declare the exact supported engine version.
- Do not assume Terraform and OpenTofu are interchangeable without validation.
- Constrain provider and module versions.
- Use remote state, locking, encryption, and recovery appropriate to the environment.
- Require reviewed plans before consequential applies.

## Package structure

| Path | Purpose |
|---|---|
| [`AGENTS.md`](AGENTS.md) | Mandatory Terraform/OpenTofu operating rules |
| [`MANIFEST.md`](MANIFEST.md) | Package inventory and adoption checklist |
| [`standards/`](standards/) | Coding, module, provider, state, security, testing, plan, apply, and evidence standards |
| [`templates/`](templates/) | Adoption templates |
| [`examples/`](examples/) | Example package composition |

## Required standards

| Standard | Governs |
|---|---|
| [`TERRAFORM_OPENTOFU_CODING_STANDARD.md`](standards/TERRAFORM_OPENTOFU_CODING_STANDARD.md) | HCL structure, naming, variables, outputs, expressions, and maintainability |
| [`ARCHITECTURE_STANDARD.md`](standards/ARCHITECTURE_STANDARD.md) | Module boundaries, environments, ownership, composition, and dependencies |
| [`DOCUMENTATION_STANDARD.md`](standards/DOCUMENTATION_STANDARD.md) | Module interfaces, assumptions, examples, operations, and migration notes |
| [`TESTING_STANDARD.md`](standards/TESTING_STANDARD.md) | Formatting, validation, tests, plans, policy, and representative environments |
| [`SECURITY_STANDARD.md`](standards/SECURITY_STANDARD.md) | Secrets, state, credentials, privilege, network exposure, and secure defaults |
| [`DEPENDENCY_MANAGEMENT_STANDARD.md`](standards/DEPENDENCY_MANAGEMENT_STANDARD.md) | Module sources, registries, checksums, provenance, versions, and updates |
| [`OBSERVABILITY_STANDARD.md`](standards/OBSERVABILITY_STANDARD.md) | Plan evidence, apply logs, change records, outputs, and sensitive-data controls |
| [`MODULE_STANDARD.md`](standards/MODULE_STANDARD.md) | Module cohesion, interfaces, composition, versioning, and examples |
| [`STATE_BACKEND_STANDARD.md`](standards/STATE_BACKEND_STANDARD.md) | Backend security, locking, recovery, migration, imports, and state operations |
| [`PROVIDER_DEPENDENCY_STANDARD.md`](standards/PROVIDER_DEPENDENCY_STANDARD.md) | Provider sources, aliases, constraints, authentication, and upgrades |
| [`PLAN_APPLY_STANDARD.md`](standards/PLAN_APPLY_STANDARD.md) | Planning, approval, saved plans, drift, apply controls, and verification |
| [`COMPLETION_EVIDENCE.md`](standards/COMPLETION_EVIDENCE.md) | Proof required before completion claims |

## Adoption procedure

1. Inventory root modules, child modules, providers, backends, workspaces, state, policies, tests, and deployment automation.
2. Declare Terraform or OpenTofu, exact engine version, and supported execution environments.
3. Define provider, module, registry, mirror, checksum, and lockfile policies.
4. Define backend, encryption, locking, access, backup, recovery, and state-migration procedures.
5. Define account, subscription, project, tenant, region, environment, and workspace boundaries.
6. Define plan creation, review, approval, saved-plan, apply authorization, and post-apply verification.
7. Define imports, moves, replacements, taints, drift, and exceptional state operations.
8. Add applicable discipline, platform, virtualization, operating-system, networking, and project-profile overlays.
9. Run repository and package validation.
10. Review the composed standard with accountable infrastructure and platform maintainers.

## Project tailoring checklist

- [ ] Terraform or OpenTofu engine and exact version are declared.
- [ ] Provider, module, registry, mirror, and checksum policies are defined.
- [ ] Backend, state locking, encryption, access, backup, and recovery are defined.
- [ ] Environment, account, subscription, project, tenant, region, and workspace boundaries are documented.
- [ ] Plan review, approval, apply authorization, drift, and rollback procedures are defined.
- [ ] Import, move, replace, taint, and state-migration procedures are defined.
- [ ] Policy, security scanning, tests, representative plans, and post-deployment verification are defined.
- [ ] Secret-management, sensitive outputs, logging, and artifact retention are defined.
- [ ] Module interfaces, ownership, versioning, and release expectations are defined.

## Infrastructure-specific safety expectations

- Never expose secrets through variables, outputs, plans, state, logs, or examples.
- Do not run an apply merely because validation or planning succeeded.
- Review create, update, replace, destroy, and data-source actions in the plan.
- State operations, imports, moves, replacements, and backend migrations require explicit review and recovery planning.
- Use least-privileged credentials scoped to the intended environment.
- Verify critical resulting infrastructure and service behavior after apply.
- Do not claim rollback exists unless it has a documented and realistic recovery path.

## Validation baseline

Use the engine declared by the repository:

```text
terraform fmt -check -recursive OR tofu fmt -check -recursive
terraform init -backend=false OR tofu init -backend=false
terraform validate OR tofu validate
run repository-configured tests, policy checks, and security scans
produce and review a plan using the declared engine
```

Do not run both engines merely to satisfy a checklist. Validate the actual execution path used by the project.

## Testing expectations

Tests should cover formatting, validation, module interfaces, variable validation, representative plans, policy rules, security controls, expected replacements, failure paths, provider behavior, and post-deployment checks where practical.

## Completion evidence

A completion report must include modules and resources changed, create/update/replace/destroy impact, provider and state impact, plan evidence, approvals, tests and policy checks, apply and verification evidence if executed, checks not run, limitations, and remaining risk.

## Templates and examples

- [`AGENTS_TEMPLATE.md`](templates/AGENTS_TEMPLATE.md)
- [`ADOPTION_CHECKLIST.md`](templates/ADOPTION_CHECKLIST.md)
- [`ADOPTION_EXAMPLE.md`](examples/ADOPTION_EXAMPLE.md)

## What this package does not decide

The adopting repository must still define cloud architecture, account ownership, networking, identity, policy enforcement, production approvals, incident response, business continuity, backup, recovery, and organization-specific compliance.

This package improves agent behavior. It does not guarantee that generated infrastructure code is secure, correct, compliant, or safe to apply.

## Authoritative starting points

- [Terraform CLI documentation](https://developer.hashicorp.com/terraform/cli)
- [Terraform language documentation](https://developer.hashicorp.com/terraform/language)
- [Terraform v1.x compatibility promises](https://developer.hashicorp.com/terraform/language/v1-compatibility-promises)
- [OpenTofu documentation](https://opentofu.org/docs/)
- [OpenTofu language documentation](https://opentofu.org/docs/language/)

Revalidate the selected Terraform or OpenTofu engine, exact version, providers, security, and support behavior before relying on version-specific guidance.
