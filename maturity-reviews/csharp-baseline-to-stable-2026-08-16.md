---
id: MATURITY-CSHARP-2026-08-16
title: C# Baseline to Stable Maturity Review
version: 1.0.0
status: baseline
---

# C# Baseline to Stable Maturity Review

## Review identity

- Review ID: `MR-CSHARP-2026-08-16`
- Component: `languages/csharp`
- Component version: `0.1.0`
- Repository commit reviewed: `ba4901c72f4c1fccda517280946f1fb1b6d2824c`
- Published package source used by adoption evidence: `83c73f3ab9a049ff2321d463164fcf98fb453a9c` (`v0.10.0`)
- Current maturity at reviewed commit: `baseline`
- Proposed maturity: `stable`
- Owner: `Language standards maintainers`
- Reviewers: `AIAllTheThingz` maintainer evidence review; policy-required independent C# specialist approval must be recorded on the exact promotion PR before merge
- Review date: `2026-08-16`

## Scope and applicability

This review covers the **C# language package** under `languages/csharp/`: its stable paths, front-matter identifiers, language-level normative standards, templates, adoption guidance, examples, and direct C# skill routing.

It does **not** promote the separate `languages/dotnet` package, ASP.NET Core, any project profile, deployment environment, or adopting project. Modern C# projects commonly compose C# with .NET, but the C# stable promise is limited to C# language semantics and the C# package contracts.

The C# package content exercised by the `v0.10.0` adoption tests and downstream pilots is unchanged between published source commit `83c73f3ab9a049ff2321d463164fcf98fb453a9c` and reviewed repository commit `ba4901c72f4c1fccda517280946f1fb1b6d2824c`; post-release work in that range affected release/adoption evidence, PowerShell, and manifest-generation behavior rather than `languages/csharp/`.

## Normative quality

The package has a complete scoped `AGENTS.md`, direct `SKILL.md`, package manifest, C# coding and type/nullability standards, async/concurrency guidance, API compatibility, resource/performance, security, build/dependency, testing, documentation, interop/reflection/generation, scripting/tooling, observability, and completion-evidence requirements.

Requirements identify observable compatibility surfaces, negative behavior, cancellation and concurrency ownership, resource lifetime, security boundaries, compiler/runtime assumptions, and exact evidence expectations. Stable front-matter IDs remain unchanged by this promotion. The maturity PR changes maturity metadata and evidence records only; it does not alter C# normative meaning.

## Adoption evidence

### Package-level adoption test

Issue #47 added the `csharp-modern-dotnet` package-level exercise in `adoption-tests/candidates.json`. It requires the C# package plus the .NET companion for a modern .NET project, verifies real manifest selection and entry-point standards composition, checks accountable source-review evidence, detects incomplete adoption when .NET is omitted, and exercises invalid-selection and overwrite failure behavior. That entry-point exercise remains useful but is not treated as proof that the complete proposed stable C# surface was bound.

PR #70 therefore adds `tools/tests/test_csharp_full_package_adoption.py` as the promotion-specific complete-surface exercise. The test derives the required package surface from `languages/csharp/MANIFEST.md`, binds every manifest-required file into a temporary adopter copy, and verifies SHA-256 identity for the direct skill, agent registration, package entry points, all normative standards, all required templates, and the adoption example. Its error-path cases remove a required security standard and tamper with a unit-test template, and both conditions must be detected rather than accepted.

- original #47 implementation run: `31962412526` — Passed
- original #47 permanent PR validation: `31962475556` — Passed
- full-package-surface remediation run: `31969012948` — Passed
- published source boundary exercised by the downstream/entry-point evidence: `v0.10.0` / `83c73f3ab9a049ff2321d463164fcf98fb453a9c`
- complete package surface exercised against the exact PR #70 remediation tree by the full-surface test

### Representative downstream adoption 1 — TheCertMaster

- repository: `AIAllTheThingz/TheCertMaster`
- pre-adoption revision: `4d93d1193a7a5f2c314726197b8c8198e5f37190`
- composition: C# + .NET + ASP.NET Core + Windows Server + `WEB_APPLICATION`
- final adoption merge: `fb868247047ca5dc8d8b50c0dc356622329fc654`
- final SQL-backed downstream CI: run `31966237083` — Passed

The generic pilot initially failed tests because it omitted the project's required SQL Server test service. The project-native rerun passed. That failure remains durable adoption evidence and was not converted into a passing claim.

### Representative downstream adoption 2 — WindowsScriptRunner

- repository: `AIAllTheThingz/WindowsScriptRunner`
- pre-adoption revision: `8694698829aa33640abc2f798233f47d71a77e39`
- composition: C# + .NET + PowerShell + ASP.NET Core + Windows Server with mixed `INTERNAL_AUTOMATION` / `WEB_APPLICATION` profiles
- adoption merge: `9fe595f678e9de5dc940c19ca33e439ed8b5690a`
- pinned-source binding follow-up: `b026062b0e066e88bccf362b5570073fa8afec43`

Restore, Release build, format verification, and PowerShell parsing passed. The Ubuntu `dotnet test` run failed in Windows-native trust/junction tests requiring Windows and `kernel32.dll`; the pilot records that as environment-specific failed evidence rather than proof of Windows failure or a pass.

Neither downstream pilot identified a C# language-package defect. The pilots did identify unrelated adoption/tooling issues, and those were corrected or tracked separately.

## Compatibility inventory

The stable C# compatibility surface includes:

- package entry paths: `languages/csharp/SKILL.md`, `AGENTS.md`, `README.md`, `MANIFEST.md`;
- agent registration path `languages/csharp/agents/openai.yaml`, including the `interface.display_name`, `interface.short_description`, and `interface.default_prompt` fields; the registration must continue to identify the C# package and route its default prompt through `$csharp`, while compatible descriptive wording may evolve;
- existing files under `languages/csharp/standards/`, `templates/`, and `examples/`;
- stable front-matter IDs beginning with the existing C# package identifiers;
- documented compiler/language-version, nullable, public API, serialization, exception, concurrency, resource, interop, generated-code, and scripting behavior where adopters depend on those contracts;
- direct skill name `csharp` and its routing behavior.

The stable promise does not include a specific .NET SDK/runtime package version, ASP.NET Core, database engine, cloud platform, test framework, production environment, or adopting project's architecture. Those remain separately composed contracts.

No schema contract or executable C# tool CLI is exposed by this package.

## Validation evidence

Repository evidence used for this review:

```text
python -m unittest discover -s tools/tests -p "test_package_adoption.py" -v
python -m unittest discover -s tools/tests -p "test_downstream_adoption_evidence.py" -v
python -m unittest discover -s tools/tests -v
python tools/validate-all/run_all.py --include-tests
```

The #41 evidence build run `31966752975` passed the focused downstream-evidence regression, complete unit suite, complete validation pipeline, and diff check before commit. PR #69 permanent exact-head run `31966823124` passed. Post-merge `main` validation run `31966922410` passed at `ba4901c72f4c1fccda517280946f1fb1b6d2824c`.

Project/runtime validation remains downstream-specific; repository validation does not compile arbitrary C# adopter projects or certify them.

## Source currency

- Authoritative sources reviewed: Microsoft C# documentation; Microsoft C# language version history
- Last accountable source review date: `2026-08-15`
- Source-review record: `SOURCE_REVIEWS.json` / `languages-csharp`
- Durable source-review evidence: `source-reviews/2026-08-15.md`
- Current reviewed language boundary: C# 14 associated with .NET 10
- Known lifecycle concern: compiler/language guidance must be rechecked when Microsoft changes the released C#/.NET language boundary; preview language behavior remains outside the normal stable baseline

The source-review cadence remains 180 days. Stable maturity does not turn a dated source review into permanent truth.

## Security and operational review

The package explicitly covers untrusted input, process execution, paths, deserialization, cryptography, secret handling, unsafe/native code, reflection, source generation, logging, resource ownership, concurrency, cancellation, and dependency/build behavior.

The package is documentation/agent guidance and performs no network or privileged operation by itself. Risk appears when adopters implement C# code, so project-specific threat, authorization, runtime, platform, and operational evidence remains mandatory.

## Open findings and conditions

- **Blocking merge gate:** independent C# specialist review is required by `MAINTAINERS.md` before the promotion PR may merge. The independent reviewer must approve the exact final PR head; absent that review, this promotion remains unmerged and ineffective.
- The separate .NET package remains `baseline`; C# stable maturity must not be represented as .NET stable maturity.
- No current high or critical C# package defect is open in the repository issue tracker.
- No production Unity, Godot, native-interop, or legacy .NET Framework pilot was part of this review. Those are non-blocking because the stable promise is the documented C# language package boundary, not universal host certification.

## Decision

`approved`

## Rationale

The maintainer evidence review concludes that the C# package meets the repository's baseline-to-stable evidence bar: complete package structure, accountable current source review, entry-point composition plus complete manifest-surface binding with SHA-256 verification and missing/tamper failure tests, two representative real downstream adoptions, explicit compatibility inventory, security and operational boundaries, stable ownership/cadence, and no unresolved high/critical C# defect.

This decision becomes effective only after the policy-required independent specialist approval is recorded on the exact promotion PR and that PR merges. The approval does not promote `.NET`, ASP.NET Core, or any downstream project.

## Conditions and owners

- No non-blocking promotion conditions remain.
- Owner: `Language standards maintainers`.
- The independent specialist review is a pre-merge policy gate, not a deferred post-promotion condition.

## Next review

- Next review date or trigger: `2027-02-11 or earlier on a material C# compiler/language/source change, high-severity defect, or incompatible adoption finding`
- Responsible owner: `Language standards maintainers`

## Release linkage

- Target repository release: `1.0.0-rc.1`
- Release-note entry: `CHANGELOG.md` `[Unreleased]` maturity-promotion entry; issue #43 must carry this promotion into the `1.0.0-rc.1` release notes before publication

This maturity decision applies only to the reviewed C# package version and repository revision. It does not certify adopting projects.
