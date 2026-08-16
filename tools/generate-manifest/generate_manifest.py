#!/usr/bin/env python3
"""Generate a deterministic project-manifest.json from explicit selections."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

TOOLS_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TOOLS_ROOT / "lib"))

from standards_tools import Finding, ToolResult, add_common_arguments, execute_tool  # noqa: E402

try:
    from jsonschema import Draft202012Validator, FormatChecker
except ImportError as exc:
    raise SystemExit(
        "Missing dependency 'jsonschema'. Install with: "
        "python -m pip install -r tools/validate-schemas/requirements.txt"
    ) from exc

TOOL = "generate-manifest"
VERSION = "1.1.0"
DEFAULT_ROOT = Path(__file__).resolve().parents[2]
DISCIPLINE_LINK = re.compile(r"disciplines/([^/]+)/AGENTS\.md")
FRONTMATTER_ID = re.compile(r"^id:\s*(\S+)\s*$", re.MULTILINE)


def unique(values: list[str]) -> list[str]:
    return list(dict.fromkeys(value for value in values if value))


def profile_catalog(root: Path) -> dict[str, tuple[str, Path]]:
    result: dict[str, tuple[str, Path]] = {}
    profiles = root / "profiles"
    for path in sorted(profiles.glob("*.md")):
        if path.name in {"README.md", "MANIFEST.md"} or path.name.startswith("PROFILE_"):
            continue
        text = path.read_text(encoding="utf-8")
        match = FRONTMATTER_ID.search(text)
        if not match:
            continue
        profile_id = match.group(1)
        stem = path.stem
        slug = stem.lower().replace("_", "-")
        for key in {profile_id, stem, slug, stem.lower()}:
            result[key.lower()] = (stem, path)
    return result


def resolve_profile(value: str, root: Path) -> tuple[str, Path]:
    catalog = profile_catalog(root)
    key = value.lower()
    if key not in catalog:
        available = sorted({item[0] for item in catalog.values()})
        raise ValueError(f"Unknown profile {value!r}. Available canonical profiles: {', '.join(available)}")
    return catalog[key]


def ensure_selection(root: Path, collection: str, values: list[str]) -> list[str]:
    normalized = unique(values)
    for value in normalized:
        path = root / collection / value
        if not path.is_dir():
            raise ValueError(f"Unknown {collection.rstrip('s')} selection {value!r}: {path}")
    return normalized


def merge_config(args: argparse.Namespace) -> dict[str, Any]:
    config: dict[str, Any] = {}
    if args.config:
        config = json.loads(args.config.read_text(encoding="utf-8"))
        if not isinstance(config, dict):
            raise ValueError("Manifest input config must contain a JSON object.")
    return config


def select(cli_values: list[str], config: dict[str, Any], key: str) -> list[str]:
    values = list(config.get(key, [])) if isinstance(config.get(key, []), list) else []
    values.extend(cli_values)
    return unique([str(value) for value in values])


def run(args: argparse.Namespace) -> ToolResult:
    root = args.root.resolve()
    config = merge_config(args)
    name = args.name or config.get("name")
    profile_input = args.profile or config.get("profile")
    if not name:
        raise ValueError("Project name is required through --name or --config.")
    if not profile_input:
        raise ValueError("Project profile is required through --profile or --config.")

    profile, profile_path = resolve_profile(str(profile_input), root)
    secondary_inputs = select(args.secondary_profile, config, "secondaryProfiles")
    secondary_resolved = [resolve_profile(value, root) for value in secondary_inputs]
    secondary_profiles = [item[0] for item in secondary_resolved]
    secondary_profile_paths = [item[1] for item in secondary_resolved]

    languages = ensure_selection(root, "languages", select(args.language, config, "languages"))
    if not languages:
        raise ValueError("At least one language selection is required.")
    disciplines = select(args.discipline, config, "disciplines")
    if args.include_profile_required:
        for selected_profile_path in (profile_path, *secondary_profile_paths):
            disciplines.extend(DISCIPLINE_LINK.findall(selected_profile_path.read_text(encoding="utf-8")))
    disciplines = ensure_selection(root, "disciplines", unique(disciplines))
    platforms = ensure_selection(root, "platforms", select(args.platform, config, "platforms"))
    frameworks = ensure_selection(root, "frameworks", select(args.framework, config, "frameworks"))
    virtualization = ensure_selection(
        root, "virtualization", select(args.virtualization, config, "virtualization")
    )
    operating_systems = ensure_selection(
        root, "operating-systems", select(args.operating_system, config, "operatingSystems")
    )
    networking = ensure_selection(root, "networking", select(args.networking, config, "networking"))

    infrastructure_selections = virtualization or operating_systems or networking
    manifest: dict[str, Any] = {
        "schemaVersion": "1.1.0" if infrastructure_selections else "1.0.0",
        "name": str(name),
        "profile": profile,
        "languages": languages,
        "disciplines": disciplines,
    }
    optional_arrays = {
        "secondaryProfiles": secondary_profiles,
        "platforms": platforms,
        "frameworks": frameworks,
        "virtualization": virtualization,
        "operatingSystems": operating_systems,
        "networking": networking,
        "exceptions": select(args.exception, config, "exceptions"),
        "owners": select(args.owner, config, "owners"),
    }
    for key, values in optional_arrays.items():
        if values:
            manifest[key] = unique(values)
    risk = args.risk or config.get("risk")
    if risk:
        manifest["risk"] = risk
    evidence_location = args.evidence_location or config.get("evidenceLocation")
    if evidence_location:
        manifest["evidenceLocation"] = str(evidence_location)

    schema_path = root / "schemas" / "v1" / "project-manifest.schema.json"
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    errors = sorted(
        Draft202012Validator(schema, format_checker=FormatChecker()).iter_errors(manifest),
        key=lambda error: list(error.absolute_path),
    )
    if errors:
        message = "; ".join(f"/{'/'.join(str(p) for p in error.absolute_path)}: {error.message}" for error in errors)
        raise ValueError(f"Generated manifest failed schema validation: {message}")

    output = args.manifest_output
    rendered = json.dumps(manifest, indent=2, sort_keys=False) + "\n"
    if not args.dry_run:
        output = output if output.is_absolute() else root / output
        if output.exists() and not args.force:
            raise ValueError(f"Output already exists; use --force to replace it: {output}")
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(rendered, encoding="utf-8")

    findings: list[Finding] = []
    if not disciplines:
        findings.append(Finding(
            "MANIFEST_NO_DISCIPLINES",
            "No disciplines were selected. This is schema-valid but usually incomplete.",
            severity="warning",
        ))

    return ToolResult.from_findings(
        tool=TOOL,
        version=VERSION,
        findings=findings,
        summary={
            "profile": profile,
            "languages": len(languages),
            "disciplines": len(disciplines),
            "platforms": len(platforms),
            "frameworks": len(frameworks),
            "virtualization": len(virtualization),
            "operatingSystems": len(operating_systems),
            "networking": len(networking),
            "dryRun": args.dry_run,
            "written": not args.dry_run,
        },
        metadata={
            "manifest": manifest,
            "output": str(args.manifest_output),
            "schema": schema_path.relative_to(root).as_posix(),
        },
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    add_common_arguments(parser, default_root=DEFAULT_ROOT)
    parser.add_argument("--config", type=Path, help="Optional JSON object containing manifest inputs.")
    parser.add_argument("--name")
    parser.add_argument("--profile")
    parser.add_argument("--secondary-profile", action="append", default=[])
    parser.add_argument("--language", action="append", default=[])
    parser.add_argument("--discipline", action="append", default=[])
    parser.add_argument("--platform", action="append", default=[])
    parser.add_argument("--framework", action="append", default=[])
    parser.add_argument("--virtualization", action="append", default=[])
    parser.add_argument("--operating-system", action="append", default=[])
    parser.add_argument("--networking", action="append", default=[])
    parser.add_argument("--risk", choices=("low", "moderate", "high", "critical"))
    parser.add_argument("--exception", action="append", default=[])
    parser.add_argument("--owner", action="append", default=[])
    parser.add_argument("--evidence-location")
    parser.add_argument("--include-profile-required", action="store_true")
    parser.add_argument("--manifest-output", type=Path, default=Path("project-manifest.json"))
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--debug", action="store_true", help=argparse.SUPPRESS)
    return parser


def main(argv: list[str] | None = None) -> int:
    return execute_tool(tool=TOOL, version=VERSION, parser=build_parser(), run=run, argv=argv)


if __name__ == "__main__":
    raise SystemExit(main())
