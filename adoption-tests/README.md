# Package-Level Adoption Tests

## Purpose

This directory defines the first repeatable package-level adoption exercises required by `MATURITY_POLICY.md` before selected baseline components can be considered for stable promotion.

These tests do not promote any package by themselves. They provide one evidence input for issue #42 and do not replace the representative downstream pilots required by issue #41.

## Initial candidate cohort

The initial cohort is deliberately small and based on high-value packages on the published `v0.10.0` surface that also have accountable source-review evidence:

- `languages/csharp`, exercised as a modern C# + .NET composition
- `languages/powershell`, exercised as internal automation
- `languages/terraform-opentofu`, exercised as infrastructure automation

The published source boundary is `v0.10.0` at commit `83c73f3ab9a049ff2321d463164fcf98fb453a9c`. The adoption tests themselves run against their exact repository test commit so later maintenance remains reviewable.

## What is exercised

For every candidate, the shared test harness exercises:

1. **Selection**: `generate-manifest` accepts the intended profile and package selections and expands profile-required disciplines.
2. **Composition**: `compose-agents` creates a traceable bundle and records SHA-256 hashes for the candidate entry points.
3. **Expected evidence**: a project-agnostic fixture records the candidate-specific runtime/tool boundary and executable validation commands expected before an adoption can be treated as complete.
4. **Incomplete adoption**: removing any required evidence field produces an explicit incomplete-adoption finding in the shared harness. The modern C# candidate also verifies that omitting the companion `.NET` package is incomplete for that candidate shape.
5. **Invalid selection**: an unknown package slug is rejected by the real manifest generator.
6. **Failure behavior**: composing into an existing output directory without `--force` is rejected for every candidate.
7. **Source currency**: every candidate's accountable `SOURCE_REVIEWS.json` record must have an actual review date and durable evidence.

## Fixtures

Fixtures under `fixtures/` are intentionally fictitious. They contain no credentials, production identifiers, endpoints, account IDs, secrets, or claims that live infrastructure was exercised.

The evidence fields are examples of the facts an adopter must make authoritative before using the selected standards:

- C#: compiler/SDK boundary, runtime boundary, validation commands
- PowerShell: runtime boundary, target scope, validation commands
- Terraform/OpenTofu: selected engine, exact engine constraint, backend/state boundary, validation commands

## Commands

Focused package-level adoption suite:

```bash
python -m unittest discover -s tools/tests -p "test_package_adoption.py" -v
```

Complete repository validation:

```bash
python tools/validate-all/run_all.py --include-tests
```

## Expected outcomes

- positive selection/composition cases pass with traceable source hashes
- missing candidate evidence is reported as incomplete rather than silently accepted
- the modern C# candidate is incomplete without its `.NET` companion selection
- invalid package slugs fail with a nonzero input-error exit
- accidental bundle overwrite fails without `--force`
- unreviewed source records cannot satisfy the candidate source-currency check

## Limitations

- These are repository-controlled package-level exercises, not independent downstream adoption evidence.
- They do not compile C#, connect to infrastructure, execute PowerShell against live targets, or run Terraform/OpenTofu against a backend or provider.
- Fixture values prove harness behavior only; they do not prove a real project has established the corresponding facts.
- A package still needs the remaining `MATURITY_POLICY.md` evidence, including at least two representative adoptions/pilots, compatibility inventory, failure-mode review, maintenance ownership, and independent specialist review before stable promotion.
