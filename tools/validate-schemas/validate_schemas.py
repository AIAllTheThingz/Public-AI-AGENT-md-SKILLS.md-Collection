#!/usr/bin/env python3
"""Validate Draft 2020-12 schemas, examples, and repository instances."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

TOOLS_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TOOLS_ROOT / "lib"))

from standards_tools import Finding, ToolResult, add_common_arguments, execute_tool  # noqa: E402

try:
    import jsonschema
    from jsonschema import Draft202012Validator, FormatChecker
except ImportError as exc:
    raise SystemExit(
        "Missing dependency 'jsonschema'. Install with: "
        "python -m pip install -r tools/validate-schemas/requirements.txt"
    ) from exc

TOOL = "validate-schemas"
VERSION = "1.2.0"
DEFAULT_ROOT = Path(__file__).resolve().parents[2]
SCHEMA_NAMES = [
    "artifact-record",
    "completion-result",
    "exception-record",
    "project-manifest",
    "risk-classification",
    "test-evidence",
]
CURRENT_SCHEMA_MAJORS = {
    "artifact-record": 1,
    "completion-result": 2,
    "exception-record": 1,
    "project-manifest": 1,
    "risk-classification": 1,
    "test-evidence": 1,
}
VERSIONED_SCHEMA_MAJORS = {
    "artifact-record": (1,),
    "completion-result": (1, 2),
    "exception-record": (1,),
    "project-manifest": (1,),
    "risk-classification": (1,),
    "test-evidence": (1,),
}
INSTANCE_RULES = [
    ("project-manifest.json", "project-manifest"),
    ("completion-result", "completion-result"),
    ("test-evidence", "test-evidence"),
    ("artifact-record", "artifact-record"),
    ("exception-record", "exception-record"),
    ("risk-classification", "risk-classification"),
]


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def pointer(parts: list[Any]) -> str:
    if not parts:
        return "/"
    return "/" + "/".join(str(part).replace("~", "~0").replace("/", "~1") for part in parts)


def normalized(schema: dict[str, Any]) -> dict[str, Any]:
    value = json.loads(json.dumps(schema))
    value.pop("$id", None)
    value.pop("x-versionedSchema", None)
    return value


def versioned_schema_path(schema_root: Path, name: str, major: int) -> Path:
    return schema_root / f"v{major}" / f"{name}.schema.json"


def instance_schema_path(instance: Any, schema_root: Path, name: str) -> Path:
    major = 1
    if isinstance(instance, dict) and "schemaVersion" in instance:
        value = instance["schemaVersion"]
        prefix = value.split(".", 1)[0] if isinstance(value, str) else ""
        major = int(prefix) if prefix.isdigit() else -1
    if major not in VERSIONED_SCHEMA_MAJORS[name]:
        major = CURRENT_SCHEMA_MAJORS[name]
    return versioned_schema_path(schema_root, name, major)


def remote_refs(value: Any, location: str="/") -> list[tuple[str, str]]:
    found: list[tuple[str, str]] = []
    if isinstance(value, dict):
        for key, child in value.items():
            child_location = f"{location.rstrip('/')}/{key}"
            if key == "$ref" and isinstance(child, str) and child.startswith(("http://", "https://")):
                found.append((child_location, child))
            found.extend(remote_refs(child, child_location))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            found.extend(remote_refs(child, f"{location.rstrip('/')}/{index}"))
    return found


def instance_findings(instance_path: Path, schema_path: Path, root: Path, expect_valid: bool) -> list[Finding]:
    instance = load_json(instance_path)
    schema = load_json(schema_path)
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    errors = sorted(validator.iter_errors(instance), key=lambda item: list(item.absolute_path))
    rel_instance = instance_path.relative_to(root).as_posix()
    if expect_valid:
        return [
            Finding(
                "SCHEMA_INSTANCE_INVALID",
                error.message,
                path=rel_instance,
                details={
                    "schema": schema_path.relative_to(root).as_posix(),
                    "pointer": pointer(list(error.absolute_path)),
                    "validator": error.validator,
                },
            )
            for error in errors
        ]
    if not errors:
        return [Finding(
            "NEGATIVE_EXAMPLE_PASSED",
            "Intentionally invalid example unexpectedly passed validation.",
            path=rel_instance,
            details={"schema": schema_path.relative_to(root).as_posix()},
        )]
    return []


def discover(path: Path) -> str | None:
    name = path.name.lower()
    for marker, schema_name in INSTANCE_RULES:
        if marker == "project-manifest.json" and name == marker:
            return schema_name
        if marker != "project-manifest.json" and marker in name:
            return schema_name
    return None


def run(args: argparse.Namespace) -> ToolResult:
    root = args.root.resolve()
    schema_root = root / "schemas"
    findings: list[Finding] = []
    schema_ids: dict[str, str] = {}
    positive_count = 0
    negative_count = 0
    instance_count = 0
    unsafe_names: set[str] = set()

    versioned_schema_count = sum(len(majors) for majors in VERSIONED_SCHEMA_MAJORS.values())

    for name in SCHEMA_NAMES:
        rolling = schema_root / f"{name}.schema.json"
        current_versioned = versioned_schema_path(
            schema_root, name, CURRENT_SCHEMA_MAJORS[name]
        )
        versioned_paths = [
            (versioned_schema_path(schema_root, name, major), f"versioned-v{major}")
            for major in VERSIONED_SCHEMA_MAJORS[name]
        ]
        for path, kind in [(rolling, "rolling"), *versioned_paths]:
            if not path.is_file():
                findings.append(Finding("SCHEMA_MISSING", f"Missing {kind} schema.", path=path.relative_to(root).as_posix()))
                continue
            try:
                schema = load_json(path)
                Draft202012Validator.check_schema(schema)
            except (json.JSONDecodeError, jsonschema.SchemaError) as exc:
                findings.append(Finding("SCHEMA_INVALID", str(exc), path=path.relative_to(root).as_posix()))
                continue
            schema_id = schema.get("$id")
            if not isinstance(schema_id, str) or not schema_id:
                findings.append(Finding("SCHEMA_ID_MISSING", "Schema lacks a non-empty $id.", path=path.relative_to(root).as_posix()))
            elif schema_id in schema_ids:
                findings.append(Finding(
                    "SCHEMA_ID_DUPLICATE",
                    f"Schema $id is also used by {schema_ids[schema_id]}: {schema_id}",
                    path=path.relative_to(root).as_posix(),
                ))
            else:
                schema_ids[schema_id] = path.relative_to(root).as_posix()
            refs = remote_refs(schema)
            if refs:
                unsafe_names.add(name)
            for location, ref in refs:
                findings.append(Finding(
                    "SCHEMA_REMOTE_REF",
                    f"Remote $ref is not allowed in offline repository validation: {ref}",
                    path=path.relative_to(root).as_posix(),
                    details={"pointer": location},
                ))

        if rolling.is_file() and current_versioned.is_file():
            if normalized(load_json(rolling)) != normalized(load_json(current_versioned)):
                findings.append(Finding(
                    "SCHEMA_VERSION_MISMATCH",
                    "Rolling and versioned schemas differ beyond identifier metadata.",
                    path=rolling.relative_to(root).as_posix(),
                ))

        if name in unsafe_names:
            continue

        example_root = schema_root / "examples" / name
        valid_example = example_root / "valid.example.json"
        invalid_example = example_root / "invalid.example.json"
        if valid_example.is_file() and current_versioned.is_file():
            positive_count += 1
            findings.extend(instance_findings(valid_example, current_versioned, root, True))
        else:
            findings.append(Finding("SCHEMA_POSITIVE_EXAMPLE_MISSING", "Missing positive example.", path=valid_example.relative_to(root).as_posix()))
        if invalid_example.is_file() and current_versioned.is_file():
            negative_count += 1
            findings.extend(instance_findings(invalid_example, current_versioned, root, False))
        else:
            findings.append(Finding("SCHEMA_NEGATIVE_EXAMPLE_MISSING", "Missing negative example.", path=invalid_example.relative_to(root).as_posix()))

        historical_valid = example_root / "valid-v1.example.json"
        v1_schema = versioned_schema_path(schema_root, name, 1)
        if historical_valid.is_file() and v1_schema.is_file():
            positive_count += 1
            findings.extend(instance_findings(historical_valid, v1_schema, root, True))

    if not args.skip_repository_instances:
        for path in sorted(root.rglob("*.json")):
            if schema_root in path.parents or (root / "tools" / "contracts") in path.parents:
                continue
            schema_name = discover(path)
            if schema_name is None:
                continue
            instance_count += 1
            schema_path = instance_schema_path(load_json(path), schema_root, schema_name)
            if schema_path.is_file():
                findings.extend(instance_findings(path, schema_path, root, True))

    return ToolResult.from_findings(
        tool=TOOL,
        version=VERSION,
        findings=findings,
        summary={
            "rollingSchemas": len(SCHEMA_NAMES),
            "versionedSchemas": versioned_schema_count,
            "positiveExamples": positive_count,
            "negativeExamples": negative_count,
            "repositoryInstances": instance_count,
            "schemaIdentifiers": len(schema_ids),
            "findings": len(findings),
        },
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    add_common_arguments(parser, default_root=DEFAULT_ROOT)
    parser.add_argument("--skip-repository-instances", action="store_true", help="Validate contracts and examples only.")
    parser.add_argument("--debug", action="store_true", help=argparse.SUPPRESS)
    return parser


def main(argv: list[str] | None = None) -> int:
    return execute_tool(tool=TOOL, version=VERSION, parser=build_parser(), run=run, argv=argv)


if __name__ == "__main__":
    raise SystemExit(main())
