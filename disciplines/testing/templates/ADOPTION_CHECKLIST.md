---
id: DISC-TPL-TEST-ADOPTION
title: Testing and Quality Engineering Adoption Checklist
version: 0.1.0
status: baseline
---
# Testing and Quality Engineering Adoption Checklist

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

- [ ] Baseline, load, stress, spike, soak/endurance, scaling, failure-under-load, and recovery-under-load applicability is recorded.
- [ ] Each performance-test type records its owner, workload, environment, metrics, thresholds, explicit execution authorization and safeguards, safe stop conditions, and evidence retention proportionate to risk.
- [ ] Repository validation and link checking pass.
- [ ] Project-specific validation is executable.
- [ ] Evidence storage and completion reporting are defined.
- [ ] Accountable maintainers reviewed the tailored package.
