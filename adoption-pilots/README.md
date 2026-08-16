# Downstream Adoption Pilots

## Purpose

This directory records real downstream adoption exercises for published Public Access Agents releases.

These records complement package-level adoption tests under `adoption-tests/`. Repository-controlled fixtures prove repeatable selection and composition behavior; downstream pilots test whether independent project repositories can apply the standards to real project facts, validation environments, instruction hierarchies, and maintenance boundaries.

A downstream pilot is evidence, not certification. It must preserve failures, `NotRun`, and `Blocked` outcomes exactly as observed.

## Requirements

Each pilot record must identify:

- downstream repository and source revision before adoption;
- exact Public Access Agents release/tag and source commit;
- selected profile/package composition;
- generated or authored project manifest;
- standards composition method;
- the downstream `AGENTS.md` scope used to make the selected standards actionable;
- validation commands and real outcomes;
- adopter-specific tailoring versus repository defects;
- actionable follow-up issues or pull requests;
- limitations and checks not run.

When a downstream repository uses `compose-agents --no-copy-sources`, the traceable composition bundle is an index and hash record, not automatically active parent instructions. The downstream `AGENTS.md` hierarchy must explicitly bind agents to the exact pinned upstream source paths and applicable supporting standards, or the adoption must not be presented as active.

## Records

- [`2026-08-16.md`](2026-08-16.md) — first three representative `v0.10.0` pilots: application/service, internal automation, and mixed application/infrastructure.

## Completion boundary

Successful downstream adoption shows that a project could select, compose, tailor, and validate the standards at the identified revision. It does not prove production readiness, security, compliance, compatibility outside the exercised boundary, or stable package maturity by itself.
