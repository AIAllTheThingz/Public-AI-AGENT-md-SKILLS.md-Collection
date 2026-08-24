---
id: DISC-TPL-SRE-ADOPTION
title: Site Reliability Engineering Adoption Checklist
version: 0.1.0
status: baseline
---
# Site Reliability Engineering Adoption Checklist

## Applicability

- [ ] The project or change was reviewed against this discipline's applicability criteria.
- [ ] The reason for adopting or omitting the discipline is recorded.
- [ ] In-scope components, environments, users, data, and operations are identified.

## Ownership and risk

- [ ] Implementation, review, approval, operations, exception, and follow-up owners are identified.
- [ ] Risk classification is recorded.
- [ ] Trust boundaries, dependencies, sensitive data, and state-changing behavior are identified.
- [ ] Compatibility, migration, rollback, recovery, and support constraints are documented.

## Package composition

- [ ] `AGENTS.md`, `README.md`, `MANIFEST.md`, supporting standards, templates, and example were included.
- [ ] Required governance standards were included.
- [ ] Applicable language, framework, platform, virtualization, operating-system, networking, project-profile, and companion-discipline packages were selected.
- [ ] Nested instructions add specificity without weakening parent requirements.

## Tailoring

- [ ] Project-specific tools, environments, commands, and evidence were declared.
- [ ] Inapplicable requirements were removed only with documented justification.
- [ ] Stricter organization or project rules were added where required.
- [ ] No production secrets or sensitive identifiers were inserted.

## Validation and approval

- [ ] Production-readiness per-area results, separate overall result, and decision authority are defined for the exact candidate and operating scope.
- [ ] Applicable data migrations and irreversible changes have rehearsal evidence, backup or recovery planning, irreversible-step handling, explicit go/no-go criteria, and decision authority.
- [ ] Scaling areas are marked `Applicable`, justified `NotApplicable`, `NotRun`, `Blocked`, `Failed`, or `Verified` with authorized criteria and decision evidence; tested failure is recorded as `Failed`, not unresolved.
- [ ] The overall scaling-strategy state and decision authority are recorded, and the strategy is not `Verified` while any applicable area is `Applicable`, `NotRun`, `Blocked`, or `Failed`.
- [ ] Deployment, rollback, backup, restore, recovery, data-migration, observability, capacity, security, privacy, ownership, runbook, incident, cost, limitation, and risk evidence is selected proportionate to applicability.
- [ ] Any `production` lifecycle claim records accountable approval plus current exact-artifact deployment and post-deployment operational evidence for the stated production environment and scope; readiness, approval, and deployment intent are not substituted for actual deployment evidence.
- [ ] Repository validation and link checking pass.
- [ ] Project-specific validation is executable.
- [ ] Evidence storage and completion reporting are defined.
- [ ] Accountable maintainers reviewed the tailored package.
