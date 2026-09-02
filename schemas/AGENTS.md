---
id: SCHEMA-AGENT-001
title: Schema Agent Instructions
version: 0.3.0
status: baseline
---

# Schema Agent Instructions

## Purpose

These instructions govern changes to schema contracts, examples, validation tooling, and schema documentation.

Schema changes can alter public machine-readable contracts. Treat them as API changes rather than tidy JSON edits.

## Scope

These instructions apply to:

- `schemas/*.schema.json`
- `schemas/v*/*.schema.json`
- schema examples
- schema versioning and compatibility documents
- schema validation tooling
- repository instances governed by these schemas

## Instruction precedence

1. Applicable legal, contractual, safety, and security obligations
2. Explicit authorized requirements
3. Root repository `AGENTS.md`
4. Governance standards
5. These schema instructions
6. More-specific local instructions
7. Repository conventions

Local instructions may strengthen controls. They may not silently weaken compatibility, evidence integrity, or governance.

## Required behavior

- Preserve the six existing rolling filenames.
- Do not remove or rename a required field without a versioned breaking change.
- Keep each rolling schema synchronized with its current-major versioned copy; preserve prior-major contracts unchanged except for separately approved backward-compatible maintenance. For completion-result, rolling aligns with v2 and v1 completion is excluded from current-major synchronization.
- Keep schemas closed by default.
- Put custom data under the `extensions` object.
- Do not reuse a standard property name for a different meaning.
- Validate schema documents against Draft 2020-12.
- Validate positive examples and require negative examples to fail.
- Identify affected repository instances and downstream consumers.
- Enable format checking when evaluating `date` and `date-time`.
- Do not claim semantic truth from structural validation.
- Do not add production secrets, identities, endpoints, or internal evidence to examples.
- State compatibility and migration impact.
- Preserve deterministic, readable JSON formatting.

## Required working method

1. Inspect the current schema, versioned copy, examples, consumers, and validation tooling.
2. Define the intended contract change.
3. Classify compatibility.
4. Update the smallest coherent set of files.
5. Add positive and negative cases.
6. Run schema meta-validation.
7. Run repository instance validation.
8. Review the diff for accidental required fields, enum narrowing, closed-object changes, and stale examples.
9. Document migration and checks not run.
10. Obtain accountable review.

## Completion gate

Schema work is incomplete until:

- rolling and versioned contracts agree
- schema documents pass meta-validation
- positive examples pass
- negative examples fail
- repository instances pass
- compatibility is classified
- migration guidance is updated when needed
- no unresolved placeholder or sensitive value remains
- evidence and limitations are recorded
