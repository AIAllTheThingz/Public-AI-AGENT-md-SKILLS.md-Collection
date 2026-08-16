---
id: CSHARP-MANIFEST-001
title: C# Package Manifest
version: 0.1.0
status: stable
---

# C# Package Manifest

## Required files

- `SKILL.md`
- `agents/openai.yaml`
- `AGENTS.md`
- `README.md`
- `MANIFEST.md`
- `standards/CSHARP_CODING_STANDARD.md`
- `standards/TYPE_SYSTEM_AND_NULLABILITY_STANDARD.md`
- `standards/ASYNC_AND_CONCURRENCY_STANDARD.md`
- `standards/API_DESIGN_AND_COMPATIBILITY_STANDARD.md`
- `standards/RESOURCE_AND_PERFORMANCE_STANDARD.md`
- `standards/SECURITY_STANDARD.md`
- `standards/BUILD_AND_DEPENDENCY_STANDARD.md`
- `standards/TESTING_STANDARD.md`
- `standards/DOCUMENTATION_STANDARD.md`
- `standards/INTEROP_REFLECTION_AND_GENERATION_STANDARD.md`
- `standards/SCRIPTING_AND_TOOLING_STANDARD.md`
- `standards/OBSERVABILITY_STANDARD.md`
- `standards/COMPLETION_EVIDENCE.md`
- `templates/AGENTS_TEMPLATE.md`
- `templates/ADOPTION_CHECKLIST.md`
- `templates/CLASS_TEMPLATE.cs`
- `templates/ASYNC_SERVICE_TEMPLATE.cs`
- `templates/UNIT_TEST_TEMPLATE.cs`
- `examples/ADOPTION_EXAMPLE.md`

## Acceptance checks

- `SKILL.md` is registered and routes C# work without replacing repository governance.
- `AGENTS.md` references every mandatory supporting standard and defines stable evidence-backed rules.
- C# language semantics are separated from .NET SDK/runtime/application responsibilities.
- Compiler, language-version, nullable, analyzer, generated-code, and compatibility boundaries are explicit.
- Async, concurrency, cancellation, resource lifetime, security, interop, scripting, testing, documentation, observability, and completion evidence are covered.
- Templates are compilable starting points after namespace/project adaptation and contain no secrets or production identifiers.
- Examples are fictitious and do not claim live validation.
- Official documentation is linked and current version behavior requires revalidation.
- Links resolve, Markdown IDs are unique, and repository validation passes.
