#!/usr/bin/env python3
"""Create a traceable project standards bundle without flattening or rewriting source standards."""

from __future__ import annotations

import argparse
import json
import shutil
import sys
import tempfile
from pathlib import Path
from typing import Any

TOOLS_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TOOLS_ROOT / "lib"))

from standards_tools import Finding, ToolResult, add_common_arguments, ensure_within_root, execute_tool, sha256_file  # noqa: E402

try:
    from jsonschema import Draft202012Validator, FormatChecker
except ImportError as exc:
    raise SystemExit(
        "Missing dependency 'jsonschema'. Install with: "
        "python -m pip install -r tools/validate-schemas/requirements.txt"
    ) from exc

TOOL = "compose-agents"
VERSION = "1.1.0"
DEFAULT_ROOT = Path(__file__).resolve().parents[2]
GOVERNANCE_SOURCES = [
    "governance/ORGANIZATION_CONTRACT.md",
    "governance/AGENT_WORKING_METHOD.md",
    "governance/RISK_CLASSIFICATION.md",
    "governance/COMPLETION_EVIDENCE.md",
    "governance/EXCEPTION_PROCESS.md",
    "governance/AI_GENERATED_CODE_POLICY.md",
    "governance/HUMAN_REVIEW_POLICY.md",
    "governance/PRODUCTION_READINESS.md",
]
GOVERNANCE_SELECTION_EXTENSION = "AIAllTheThingz.governanceSelections"
GOVERNANCE_SELECTION_DEPENDENCIES = {
    "governance/PRODUCT_INCEPTION_LIFECYCLE.md": (
        "MATURITY_POLICY.md",
        "SOURCE_REVIEWS.json",
        "source-reviews/README.md",
        "disciplines/product-management/README.md",
        "disciplines/product-management/standards/TRACEABILITY_STANDARD.md",
        "disciplines/product-management/templates/EVIDENCE_RECORD_TEMPLATE.md",
        "disciplines/sre/README.md",
        "disciplines/sre/standards/CAPACITY_PERFORMANCE_STANDARD.md",
        "disciplines/sre/standards/PRODUCTION_READINESS_STANDARD.md",
        "disciplines/sre/standards/SCALING_STRATEGY_STANDARD.md",
        "disciplines/sre/templates/EVIDENCE_RECORD_TEMPLATE.md",
        "source-reviews/2026-08-15.md",
        "source-reviews/2026-08-23.md",
    ),
}


def load_manifest(path: Path, root: Path) -> dict[str, Any]:
    manifest = json.loads(path.read_text(encoding="utf-8"))
    schema_path = root / "schemas" / "v1" / "project-manifest.schema.json"
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    errors = sorted(
        Draft202012Validator(schema, format_checker=FormatChecker()).iter_errors(manifest),
        key=lambda item: list(item.absolute_path),
    )
    if errors:
        message = "; ".join(f"/{'/'.join(str(p) for p in error.absolute_path)}: {error.message}" for error in errors)
        raise ValueError(f"Project manifest is invalid: {message}")
    return manifest


def canonical_profile_path(root: Path, profile: str) -> Path:
    candidates = [
        root / "profiles" / f"{profile}.md",
        root / "profiles" / f"{profile.upper().replace('-', '_')}.md",
    ]
    for path in candidates:
        if path.is_file():
            return path
    raise ValueError(f"Cannot resolve canonical profile file for {profile!r}.")


def package_files(root: Path, collection: str, slug: str) -> list[Path]:
    package = root / collection / slug
    if not package.is_dir():
        raise ValueError(f"Selected {collection.rstrip('s')} package does not exist: {slug}")
    selected = []
    for name in ("AGENTS.md", "README.md", "MANIFEST.md"):
        path = package / name
        if path.is_file():
            selected.append(path)
    if not selected:
        raise ValueError(f"Selected package has no standard entry points: {package}")
    return selected


def selected_governance_files(root: Path, manifest: dict[str, Any]) -> list[Path]:
    extensions = manifest.get("extensions", {})
    raw_selections = extensions.get(GOVERNANCE_SELECTION_EXTENSION, [])
    if not isinstance(raw_selections, list):
        raise ValueError(
            f"Manifest extension {GOVERNANCE_SELECTION_EXTENSION!r} must be an array."
        )

    governance_root = (root / "governance").resolve()
    selected: list[Path] = []
    for value in raw_selections:
        if not isinstance(value, str) or not value.strip():
            raise ValueError(
                f"Manifest extension {GOVERNANCE_SELECTION_EXTENSION!r} must contain "
                "nonempty repository-relative paths."
            )
        if "\\" in value:
            raise ValueError(
                f"Selected governance source must use repository-relative POSIX paths: {value!r}"
            )

        relative = Path(value)
        if relative.is_absolute():
            raise ValueError(
                f"Selected governance source must be repository-relative: {value!r}"
            )
        path = ensure_within_root(root / relative, root)
        try:
            path.relative_to(governance_root)
        except ValueError as exc:
            raise ValueError(
                f"Selected governance source must be under governance/: {value!r}"
            ) from exc
        if path.suffix.casefold() != ".md" or not path.is_file():
            raise ValueError(f"Selected governance source does not exist: {value}")
        selected.append(path)

        canonical_selection = path.relative_to(root).as_posix()
        for dependency in GOVERNANCE_SELECTION_DEPENDENCIES.get(
            canonical_selection, ()
        ):
            dependency_path = ensure_within_root(root / dependency, root)
            if not dependency_path.is_file():
                raise ValueError(
                    f"Required dependency for selected governance source {value!r} "
                    f"is missing: {dependency}"
                )
            selected.append(dependency_path)
    return selected


def build_source_list(root: Path, manifest: dict[str, Any]) -> list[Path]:
    sources: list[Path] = []
    for relative in GOVERNANCE_SOURCES:
        path = root / relative
        if not path.is_file():
            raise ValueError(f"Required governance source is missing: {relative}")
        sources.append(path)
    sources.extend(selected_governance_files(root, manifest))

    profile_path = canonical_profile_path(root, str(manifest["profile"]))
    sources.append(profile_path)
    profile_slug = profile_path.stem.lower().replace("_", "-")
    profile_package = root / "profiles" / profile_slug
    if profile_package.is_dir():
        for name in ("AGENTS.md", "README.md", "MANIFEST.md"):
            path = profile_package / name
            if path.is_file():
                sources.append(path)

    for collection, key in (
        ("languages", "languages"),
        ("disciplines", "disciplines"),
        ("frameworks", "frameworks"),
        ("platforms", "platforms"),
        ("virtualization", "virtualization"),
        ("operating-systems", "operatingSystems"),
        ("networking", "networking"),
    ):
        for slug in manifest.get(key, []):
            sources.extend(package_files(root, collection, str(slug)))

    unique: dict[str, Path] = {}
    for source in sources:
        resolved = ensure_within_root(source, root)
        unique[resolved.relative_to(root).as_posix()] = resolved
    return [unique[key] for key in sorted(unique)]


def generated_agents(manifest: dict[str, Any], source_records: list[dict[str, str]]) -> str:
    governance_selections = manifest.get("extensions", {}).get(
        GOVERNANCE_SELECTION_EXTENSION, []
    )
    lines = [
        "# Project Standards Composition Index",
        "",
        f"Project: **{manifest['name']}**",
        "",
        "This file was generated as a traceable standards composition index. It does not invent project facts, grant authorization, or replace project-specific root and nested instructions.",
        "",
        "## Selected composition",
        "",
        f"- Governance selections: {', '.join(f'`{item}`' for item in governance_selections) or 'none beyond the required baseline'}",
        f"- Primary profile: `{manifest['profile']}`",
        f"- Languages: {', '.join(f'`{item}`' for item in manifest.get('languages', [])) or 'none declared'}",
        f"- Disciplines: {', '.join(f'`{item}`' for item in manifest.get('disciplines', [])) or 'none declared'}",
        f"- Frameworks: {', '.join(f'`{item}`' for item in manifest.get('frameworks', [])) or 'none declared'}",
        f"- Platforms: {', '.join(f'`{item}`' for item in manifest.get('platforms', [])) or 'none declared'}",
        f"- Virtualization: {', '.join(f'`{item}`' for item in manifest.get('virtualization', [])) or 'none declared'}",
        f"- Operating systems: {', '.join(f'`{item}`' for item in manifest.get('operatingSystems', [])) or 'none declared'}",
        f"- Networking: {', '.join(f'`{item}`' for item in manifest.get('networking', [])) or 'none declared'}",
        "",
        "## Source standards",
        "",
    ]
    for record in source_records:
        lines.append(f"- `{record['path']}` (`sha256:{record['sha256']}`)")
    lines.extend([
        "",
        "## Required project tailoring",
        "",
        "Before using this bundle as project instructions, define and review:",
        "",
        "- project purpose and non-goals",
        "- authoritative owners and reviewers",
        "- supported runtimes and versions",
        "- deployment environments and target boundaries",
        "- sensitive data and privileged operations",
        "- exact validation commands",
        "- evidence location and retention",
        "- authorization, rollback, recovery, and escalation",
        "- compatibility and migration commitments",
        "- nested instruction scopes",
        "",
        "Unknown facts must remain unknown. Do not convert missing information into plausible prose.",
        "",
        "## Precedence",
        "",
        "Applicable law, contracts, explicit authorization, repository governance, and parent instructions remain authoritative. More-specific nested instructions may strengthen but may not silently weaken shared controls.",
        "",
        "## Completion boundary",
        "",
        "The bundle proves only which source files were selected and copied. It does not prove that the project is secure, compliant, validated, reviewed, authorized, deployable, or production-ready.",
        "",
    ])
    return "\n".join(lines)


def run(args: argparse.Namespace) -> ToolResult:
    root = args.root.resolve()
    manifest_path = args.manifest if args.manifest.is_absolute() else root / args.manifest
    manifest = load_manifest(manifest_path, root)
    sources = build_source_list(root, manifest)
    source_records = [
        {"path": path.relative_to(root).as_posix(), "sha256": sha256_file(path)}
        for path in sources
    ]
    output_dir = args.output_dir if args.output_dir.is_absolute() else root / args.output_dir
    if output_dir.exists() and not args.force and not args.dry_run:
        raise ValueError(f"Output directory already exists; use --force to replace it: {output_dir}")

    composition = {
        "formatVersion": "1.0.0",
        "project": manifest["name"],
        "projectManifest": manifest,
        "sources": source_records,
        "copiedSources": args.copy_sources,
        "limitations": [
            "The bundle is a traceable source selection, not an authorization or compliance record.",
            "Project-specific facts and nested instructions still require accountable review.",
        ],
    }

    if not args.dry_run:
        output_dir.parent.mkdir(parents=True, exist_ok=True)
        staging_parent = output_dir.parent
        with tempfile.TemporaryDirectory(prefix="compose-agents-", dir=staging_parent) as temp:
            staging = Path(temp) / "bundle"
            staging.mkdir()
            (staging / "AGENTS.md").write_text(generated_agents(manifest, source_records), encoding="utf-8")
            (staging / "COMPOSITION_MANIFEST.json").write_text(json.dumps(composition, indent=2) + "\n", encoding="utf-8")
            (staging / "README.md").write_text(
                "# Standards Bundle\n\n"
                "This directory contains a traceable composition index and optional copies of selected source standards. "
                "Review `AGENTS.md` and `COMPOSITION_MANIFEST.json` before adoption.\n",
                encoding="utf-8",
            )
            (staging / "TAILORING_CHECKLIST.md").write_text(
                "# Tailoring Checklist\n\n"
                "- [ ] Project facts are authoritative.\n"
                "- [ ] Risk is classified.\n"
                "- [ ] Validation commands are executable.\n"
                "- [ ] Authorization and recovery are defined.\n"
                "- [ ] Nested instruction scopes are identified.\n"
                "- [ ] Limitations and checks not run are recorded.\n",
                encoding="utf-8",
            )
            if args.copy_sources:
                for source in sources:
                    destination = staging / "sources" / source.relative_to(root)
                    destination.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(source, destination)
            if output_dir.exists():
                shutil.rmtree(output_dir)
            shutil.move(str(staging), output_dir)

    findings: list[Finding] = []
    if not manifest.get("disciplines"):
        findings.append(Finding(
            "COMPOSITION_NO_DISCIPLINES",
            "Manifest selects no disciplines. The bundle is structurally valid but likely incomplete.",
            severity="warning",
        ))

    return ToolResult.from_findings(
        tool=TOOL,
        version=VERSION,
        findings=findings,
        summary={
            "sources": len(source_records),
            "copiedSources": args.copy_sources,
            "dryRun": args.dry_run,
            "written": not args.dry_run,
        },
        metadata={
            "outputDirectory": str(args.output_dir),
            "composition": composition,
        },
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    add_common_arguments(parser, default_root=DEFAULT_ROOT)
    parser.add_argument("--manifest", type=Path, default=Path("project-manifest.json"))
    parser.add_argument("--output-dir", type=Path, default=Path("generated/standards-bundle"))
    parser.add_argument("--copy-sources", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--debug", action="store_true", help=argparse.SUPPRESS)
    return parser


def main(argv: list[str] | None = None) -> int:
    return execute_tool(tool=TOOL, version=VERSION, parser=build_parser(), run=run, argv=argv)


if __name__ == "__main__":
    raise SystemExit(main())
