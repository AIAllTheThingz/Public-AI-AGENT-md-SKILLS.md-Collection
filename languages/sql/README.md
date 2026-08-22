---
id: SQL-PKG-001
status: baseline
title: SQL Package
---

# SQL Language Package

This package provides project-agnostic engineering standards for SQL queries, schema objects, migrations, data-access scripts, and database validation.

It defines how coding agents should inspect, design, implement, test, secure, document, migrate, and report SQL work. It does not select a database engine, migration framework, schema ownership model, or production deployment process for the adopting project.

## Package status

**Status:** `baseline`

The package is structurally complete and suitable for adoption. Projects must tailor database dialect, engine version, migration tooling, data classification, deployment, and organization-specific requirements before treating it as a final production standard.

## Intended scope

- queries, views, procedures, functions, and triggers
- schema definitions, keys, indexes, and constraints
- migration and rollback scripts
- seed and reference data
- performance-sensitive data access
- database tests and deployment validation

## Dialect baseline

- Declare the SQL dialect, database engine, edition, and supported versions.
- Do not claim portability without testing against every supported engine.
- Define transaction, locking, isolation, timeout, and migration behavior.
- Validate SQL against a representative database engine rather than only a generic parser.
- Preserve existing contracts and data compatibility unless migration is explicitly in scope.

## Package structure

| Path | Purpose |
|---|---|
| [`AGENTS.md`](AGENTS.md) | Mandatory SQL-specific operating rules |
| [`MANIFEST.md`](MANIFEST.md) | Package inventory and adoption checklist |
| [`standards/`](standards/) | Coding, dialect, migration, data-integrity, security, testing, and evidence standards |
| [`templates/`](templates/) | Adoption templates |
| [`examples/`](examples/) | Example package composition |

## Required standards

| Standard | Governs |
|---|---|
| [`SQL_CODING_STANDARD.md`](standards/SQL_CODING_STANDARD.md) | Query structure, naming, joins, predicates, transactions, errors, and maintainability |
| [`ARCHITECTURE_STANDARD.md`](standards/ARCHITECTURE_STANDARD.md) | Schema boundaries, ownership, interfaces, data lifecycle, and coupling |
| [`DOCUMENTATION_STANDARD.md`](standards/DOCUMENTATION_STANDARD.md) | Object purpose, data contracts, migrations, operations, and examples |
| [`TESTING_STANDARD.md`](standards/TESTING_STANDARD.md) | Queries, constraints, migrations, rollback, integration, and representative data |
| [`SECURITY_STANDARD.md`](standards/SECURITY_STANDARD.md) | Parameterization, privileges, dynamic SQL, sensitive data, and secure defaults |
| [`DEPENDENCY_MANAGEMENT_STANDARD.md`](standards/DEPENDENCY_MANAGEMENT_STANDARD.md) | Extensions, functions, collations, engine features, and external requirements |
| [`OBSERVABILITY_STANDARD.md`](standards/OBSERVABILITY_STANDARD.md) | Query diagnostics, execution evidence, audits, and sensitive-data controls |
| [`DIALECT_COMPATIBILITY_STANDARD.md`](standards/DIALECT_COMPATIBILITY_STANDARD.md) | Engine syntax, version support, portability, and feature gates |
| [`MIGRATION_STANDARD.md`](standards/MIGRATION_STANDARD.md) | Forward migration, rollback, locks, data transformation, and sequencing |
| [`DATA_INTEGRITY_STANDARD.md`](standards/DATA_INTEGRITY_STANDARD.md) | Constraints, keys, nullability, concurrency, retention, and reconciliation |
| [`COMPLETION_EVIDENCE.md`](standards/COMPLETION_EVIDENCE.md) | Proof required before completion claims |

## Adoption procedure

1. Inventory database engines, versions, schemas, migrations, objects, data-access callers, and deployment tooling.
2. Declare the SQL dialect, engine, edition, version, and supported compatibility levels.
3. Define schema ownership, naming, object boundaries, and public data contracts.
4. Define migration tooling, deployment order, transaction scope, lock tolerance, and recovery procedures.
5. Define parameterization, least privilege, dynamic SQL, secret handling, and audit requirements.
6. Define formatting, linting, parse or compile checks, database tests, migration tests, and representative-data tests.
7. Define data classification, retention, backup, restore, reconciliation, and destructive-change approvals.
8. Add applicable discipline, framework, platform, virtualization, operating-system, networking, and project-profile overlays.
9. Run repository and package validation.
10. Review the composed standard with an accountable database maintainer.

## Project tailoring checklist

- [ ] Engine, edition, version, dialect, and compatibility level are declared.
- [ ] Schema ownership, naming, object boundaries, and data contracts are documented.
- [ ] Migration framework, sequencing, locking, rollback, and recovery are defined.
- [ ] Transaction, isolation, timeout, retry, and concurrency behavior are defined.
- [ ] Parameterization, least privilege, dynamic SQL, and credential handling are defined.
- [ ] Data classification, encryption, retention, audit, backup, restore, and deletion are defined.
- [ ] Test data, representative scale, query-plan review, and performance criteria are defined.
- [ ] Deployment, smoke testing, rollback, and post-change verification are defined.

## SQL-specific safety expectations

- Parameterize untrusted values through the calling API or an approved database mechanism.
- Do not concatenate untrusted input into executable SQL.
- Treat schema changes as data and operational changes, not merely syntax changes.
- Analyze locking, blocking, transaction duration, replication, and deployment order.
- Use constraints to enforce durable integrity where appropriate.
- Avoid destructive operations without explicit authorization, verified scope, backup or recovery evidence, and post-change validation.
- Redact sensitive values from logs, plans, diagnostics, and examples.

## Validation baseline

Use repository-defined tools. Typical validation includes:

```text
run the configured SQL formatter or linter
parse or compile SQL against the declared dialect
apply migrations to an isolated representative database
validate rollback or recovery when supported
run integration and data-integrity tests
review relevant query plans and locking behavior
```

A query returning expected rows on a tiny fixture is not sufficient evidence for a consequential production change.

## Testing expectations

Tests should cover expected results, empty and null values, duplicate and conflicting data, constraints, transaction rollback, concurrency, locking, migration from representative prior states, rollback or recovery, permissions, and performance-sensitive plans.

## Completion evidence

A completion report must include objects and scripts changed, data and compatibility impact, migration and rollback behavior, privilege and security impact, tests and database validation performed, performance or locking evidence, checks not run, limitations, and remaining risk.

## Templates and examples

- [`AGENTS_TEMPLATE.md`](templates/AGENTS_TEMPLATE.md)
- [`ADOPTION_CHECKLIST.md`](templates/ADOPTION_CHECKLIST.md)
- [`ADOPTION_EXAMPLE.md`](examples/ADOPTION_EXAMPLE.md)

## What this package does not decide

The adopting repository must still define business data requirements, production ownership, database operations, maintenance windows, data classification, incident response, backup, recovery, retention, and organization-specific compliance.

This package improves agent behavior. It does not guarantee that generated SQL is correct, portable, secure, performant, or safe to deploy.

## Authoritative starting points

ISO/IEC 9075 is the general normative foundation. The selected database engine's official documentation is authoritative for dialect-specific syntax and behavior.

- [ISO/IEC 9075-1:2023 SQL/Framework](https://www.iso.org/standard/76583.html)
- [PostgreSQL documentation](https://www.postgresql.org/docs/)
- [Microsoft SQL Server documentation](https://learn.microsoft.com/en-us/sql/sql-server/)
- [MySQL Reference Manual](https://dev.mysql.com/doc/refman/8.4/en/)
- [SQLite documentation](https://www.sqlite.org/docs.html)

Revalidate the declared engine, edition, version, dialect, security, and support behavior; do not infer portability from another engine's documentation.
