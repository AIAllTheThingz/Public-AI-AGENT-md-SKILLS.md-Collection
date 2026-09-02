---
id: SCHEMA-VERSION-001
title: Schema Versioning Policy
version: 0.4.0
status: baseline
---

# Schema Versioning Policy

## Version model

Schema contracts use semantic versioning principles:

- **Patch:** descriptions, examples, annotations, and validator fixes that do not change accepted instances.
- **Minor:** backward-compatible additions, such as optional properties or broader accepted values.
- **Major:** required-field changes, removed properties, narrowed enums, stricter formats, changed meanings, or any change that invalidates previously valid instances.

## Paths

- Rolling paths may advance within the compatibility policy.
- Versioned major paths preserve backward compatibility within that major. They may receive compatible patch or minor additions, but must not receive a breaking change.
- A new major version receives a new directory such as `v2/`.
- Completion-result rolling/current is major v2; `v1/completion-result.schema.json` remains unchanged for historical and pinned v1 consumers. Other contracts remain major v1.

Consumers that require byte-for-byte immutability must pin a repository tag or commit in addition to the major schema path and record the instance `schemaVersion`.

## Instance version

Instances may include:

```json
"schemaVersion": "2.0.0"
```

Current completion-result instances use `schemaVersion: "2.0.0"` and the required `executionDiscipline` record. Version 1 completion-result instances may omit the property for backward compatibility and are interpreted as `1.0.0` under the preserved v1 contract. Other version 1 contracts use `1.0.0`, except project manifests using standard virtualization, operating-system, or networking selections, which require `1.1.0`.

## Release requirements

A schema release must identify:

- changed contracts
- compatibility class
- affected consumers
- migration steps
- positive and negative tests
- validator version
- unresolved limitations
- approval for breaking changes
- handling of retained historical records when a new major is introduced

## Deprecation

Deprecated fields or versions require:

- replacement guidance
- supported overlap period
- removal target
- consumer inventory
- migration evidence
- explicit status

Silently changing a field's meaning while preserving its name is not compatibility. It is an ambush with excellent syntax.
