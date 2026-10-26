#!/usr/bin/env python3
"""Validate reusable template packages, placeholders, examples, and stable paths."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

TOOLS_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TOOLS_ROOT / "lib"))

from standards_tools import Finding, ToolResult, add_common_arguments, execute_tool, load_json, rel, require_date_time_format  # noqa: E402

try:
    from jsonschema import Draft202012Validator, FormatChecker
except ImportError as exc:
    raise SystemExit(
        "Missing dependency 'jsonschema'. Install with: "
        "python -m pip install -r tools/validate-schemas/requirements.txt"
    ) from exc
require_date_time_format(FormatChecker())

TOOL = "validate-templates"
VERSION = "1.0.0"
DEFAULT_ROOT = Path(__file__).resolve().parents[2]
PACKAGES = {
    "root": ("AGENTS_TEMPLATE.md", "EXAMPLE.md", None),
    "nested": ("AGENTS_TEMPLATE.md", "EXAMPLE.md", None),
    "architecture-decision": ("ADR_TEMPLATE.md", "EXAMPLE.md", None),
    "risk": ("RISK_ASSESSMENT_TEMPLATE.md", "EXAMPLE.md", None),
    "threat-model": ("THREAT_MODEL_TEMPLATE.md", "EXAMPLE.md", None),
    "exception": ("EXCEPTION_RECORD_TEMPLATE.md", "EXAMPLE.md", None),
    "completion": ("COMPLETION_REPORT_TEMPLATE.md", "EXAMPLE.md", None),
    "project-manifest": ("PROJECT_MANIFEST_TEMPLATE.json", "EXAMPLE.json", "project-manifest.schema.json"),
    "test-evidence": ("TEST_EVIDENCE_TEMPLATE.json", "EXAMPLE.json", "test-evidence.schema.json"),
    "artifact-record": ("ARTIFACT_RECORD_TEMPLATE.json", "EXAMPLE.json", "artifact-record.schema.json"),
    "authorization": ("CHANGE_AUTHORIZATION_TEMPLATE.md", "EXAMPLE.md", None),
    "human-review": ("HUMAN_REVIEW_TEMPLATE.md", "EXAMPLE.md", None),
    "production-readiness": ("PRODUCTION_READINESS_TEMPLATE.md", "EXAMPLE.md", None),
    "release": ("RELEASE_PLAN_TEMPLATE.md", "EXAMPLE.md", None),
    "recovery": ("ROLLBACK_RECOVERY_TEMPLATE.md", "EXAMPLE.md", None),
    "operations": ("RUNBOOK_TEMPLATE.md", "EXAMPLE.md", None),
}
REQUIRED_COLLECTION = [
    "AGENTS.md", "README.md", "MANIFEST.md", "TEMPLATE_CATALOG.md",
    "TEMPLATE_SELECTION_GUIDE.md", "AUTHORING_GUIDE.md", "CUSTOMIZATION_POLICY.md",
    "PLACEHOLDER_CONVENTIONS.md", "TEMPLATE_LIFECYCLE.md", "VALIDATION_GUIDE.md",
    "COMPLETION_CRITERIA.md",
]
STABLE_PATHS = [
    "root/AGENTS_TEMPLATE.md", "nested/AGENTS_TEMPLATE.md",
    "architecture-decision/ADR_TEMPLATE.md", "completion/COMPLETION_REPORT_TEMPLATE.md",
    "exception/EXCEPTION_RECORD_TEMPLATE.md", "risk/RISK_ASSESSMENT_TEMPLATE.md",
    "threat-model/THREAT_MODEL_TEMPLATE.md",
]
FRONTMATTER_ID = re.compile(r"^id:\s*(\S+)\s*$", re.MULTILINE)
PLACEHOLDER = re.compile(r"\{\{([^{}]+)\}\}")
VALID_PLACEHOLDER = re.compile(r"^[A-Z][A-Z0-9_]*$")
SECRET_PATTERNS = [
    re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    re.compile(r"\bgh[pousr]_[A-Za-z0-9]{20,}\b"),
    re.compile(r"\bsk-[A-Za-z0-9]{20,}\b"),
]


def run(args: argparse.Namespace) -> ToolResult:
    root = args.root.resolve()
    template_root = root / "templates"
    schema_root = root / "schemas" / "v1"
    findings: list[Finding] = []
    ids: dict[str, Path] = {}

    for name in REQUIRED_COLLECTION:
        path = template_root / name
        if not path.is_file():
            findings.append(Finding("TEMPLATE_COLLECTION_FILE_MISSING", "Missing collection file.", path=rel(path, root)))

    for stable in STABLE_PATHS:
        path = template_root / stable
        if not path.is_file():
            findings.append(Finding("TEMPLATE_STABLE_PATH_MISSING", "Missing stable template path.", path=rel(path, root)))

    for path in sorted(template_root.rglob("*.md")):
        text = path.read_text(encoding="utf-8")
        match = FRONTMATTER_ID.search(text)
        if not match:
            findings.append(Finding("TEMPLATE_ID_MISSING", "Markdown document lacks front-matter ID.", path=rel(path, root)))
            continue
        document_id = match.group(1)
        if document_id in ids:
            findings.append(Finding(
                "TEMPLATE_ID_DUPLICATE",
                f"ID also used by {rel(ids[document_id], root)}: {document_id}",
                path=rel(path, root),
            ))
        else:
            ids[document_id] = path

    for slug, (template_name, example_name, schema_name) in PACKAGES.items():
        package = template_root / slug
        required = [package / template_name, package / "README.md", package / "REVIEW_CHECKLIST.md", package / "examples" / example_name]
        if schema_name:
            required.append(package / "examples" / "README.md")
        for path in required:
            if not path.is_file():
                findings.append(Finding("TEMPLATE_PACKAGE_FILE_MISSING", "Missing package file.", path=rel(path, root)))

        readme = package / "README.md"
        readme_text = readme.read_text(encoding="utf-8") if readme.is_file() else ""
        if readme.is_file() and len(readme_text.splitlines()) < args.minimum_readme_lines:
            findings.append(Finding(
                "TEMPLATE_README_THIN",
                f"README has fewer than {args.minimum_readme_lines} lines.",
                path=rel(readme, root),
            ))

        template = package / template_name
        if template.is_file():
            template_text = template.read_text(encoding="utf-8")
            placeholders = PLACEHOLDER.findall(template_text)
            if not placeholders:
                findings.append(Finding("TEMPLATE_NO_PLACEHOLDERS", "Template contains no documented placeholders.", path=rel(template, root)))
            for placeholder in placeholders:
                token = "{{" + placeholder + "}}"
                if not VALID_PLACEHOLDER.fullmatch(placeholder):
                    findings.append(Finding("TEMPLATE_PLACEHOLDER_INVALID", f"Invalid placeholder: {token}", path=rel(template, root)))
                elif token not in readme_text:
                    findings.append(Finding("TEMPLATE_PLACEHOLDER_UNDOCUMENTED", f"Placeholder is absent from package README: {token}", path=rel(template, root)))
            if template.suffix == ".json":
                try:
                    load_json(template)
                except (json.JSONDecodeError, UnicodeDecodeError) as exc:
                    findings.append(Finding("TEMPLATE_JSON_INVALID", str(exc), path=rel(template, root)))

        example = package / "examples" / example_name
        if example.is_file():
            example_text = example.read_text(encoding="utf-8")
            if PLACEHOLDER.search(example_text):
                findings.append(Finding("TEMPLATE_EXAMPLE_PLACEHOLDER", "Completed example contains unresolved placeholder.", path=rel(example, root)))
            if re.search(r"\bTBD\b|<TODO>", example_text, re.IGNORECASE):
                findings.append(Finding("TEMPLATE_EXAMPLE_UNFINISHED", "Completed example contains unfinished marker.", path=rel(example, root)))
            for pattern in SECRET_PATTERNS:
                if pattern.search(example_text):
                    findings.append(Finding("TEMPLATE_EXAMPLE_SECRET", "Example contains a secret-like value.", path=rel(example, root)))
            if example.suffix == ".json" and schema_name:
                try:
                    instance = load_json(example)
                    schema_path = schema_root / schema_name
                    schema = load_json(schema_path)
                    validator = Draft202012Validator(schema, format_checker=FormatChecker())
                    for error in sorted(validator.iter_errors(instance), key=lambda item: list(item.absolute_path)):
                        findings.append(Finding(
                            "TEMPLATE_EXAMPLE_SCHEMA",
                            error.message,
                            path=rel(example, root),
                            details={"schema": rel(schema_path, root), "pointer": "/" + "/".join(str(part) for part in error.absolute_path)},
                        ))
                except (FileNotFoundError, json.JSONDecodeError) as exc:
                    findings.append(Finding("TEMPLATE_EXAMPLE_JSON", str(exc), path=rel(example, root)))

        checklist = package / "REVIEW_CHECKLIST.md"
        if checklist.is_file() and "## Decision" not in checklist.read_text(encoding="utf-8"):
            findings.append(Finding("TEMPLATE_CHECKLIST_DECISION", "Review checklist lacks a Decision section.", path=rel(checklist, root)))

    return ToolResult.from_findings(
        tool=TOOL,
        version=VERSION,
        findings=findings,
        summary={
            "packages": len(PACKAGES),
            "identifiedDocuments": len(ids),
            "stablePaths": len(STABLE_PATHS),
            "findings": len(findings),
        },
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    add_common_arguments(parser, default_root=DEFAULT_ROOT)
    parser.add_argument("--minimum-readme-lines", type=int, default=100)
    parser.add_argument("--debug", action="store_true", help=argparse.SUPPRESS)
    return parser


def main(argv: list[str] | None = None) -> int:
    return execute_tool(tool=TOOL, version=VERSION, parser=build_parser(), run=run, argv=argv)


if __name__ == "__main__":
    raise SystemExit(main())
