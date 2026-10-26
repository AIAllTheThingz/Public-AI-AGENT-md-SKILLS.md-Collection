#!/usr/bin/env python3
"""Validate repository structure, licensing, ownership, JSON, identifiers, and final-branch hygiene."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

TOOLS_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TOOLS_ROOT / "lib"))

from standards_tools import Finding, ToolResult, add_common_arguments, execute_tool, rel  # noqa: E402

TOOL = "validate-standards"
VERSION = "1.2.0"
DEFAULT_ROOT = Path(__file__).resolve().parents[2]
REQUIRED_ROOT = {
    "AGENTS.md",
    "README.md",
    "CATALOG.md",
    "CONTRIBUTING.md",
    "LICENSE",
    "LICENSING.md",
    "MAINTAINERS.md",
    "MANIFEST.md",
    "NOTICE",
    "ROADMAP.md",
    "SECURITY.md",
    "SOURCES.md",
}
FRONTMATTER_ID = re.compile(r"^id:\s*(\S+)\s*$", re.MULTILINE)
TEMPORARY_NAMES = {
    "profile-build-failure.log",
    "profile-repair-failure.log",
}
APACHE_LICENSE_MARKERS = (
    "Apache License\nVersion 2.0, January 2004",
    "TERMS AND CONDITIONS FOR USE, REPRODUCTION, AND DISTRIBUTION",
    "END OF TERMS AND CONDITIONS",
    "APPENDIX: How to apply the Apache License to your work.",
)
EXPECTED_COPYRIGHT = "Copyright 2026 Metello Zuccolini"
SPDX_IDENTIFIER = "Apache-2.0"
STALE_LICENSE_TEXT = "A repository license has not yet been selected"
EXPECTED_MAINTAINER_NAME = "Metello Zuccolini"
EXPECTED_MAINTAINER = "@AIAllTheThingz"
MAINTAINER_MARKERS = (
    "# Maintainers and Repository Ownership",
    "## Current maintainer roster",
    "### Current coverage limitation",
    "## Area ownership",
    "### Independent specialist review",
    "## Merge authority",
    "## Author self-merge",
    "## Emergency changes",
    "## Inactivity",
    "## Appointment and succession",
    "## Branch protection and enforcement",
    "## Review cadence",
)
REQUIRED_CODEOWNER_ROUTES = {
    "*": EXPECTED_MAINTAINER,
    "/MAINTAINERS.md": EXPECTED_MAINTAINER,
    "/.github/CODEOWNERS": EXPECTED_MAINTAINER,
    "/governance/": EXPECTED_MAINTAINER,
    "/SECURITY.md": EXPECTED_MAINTAINER,
    "/schemas/": EXPECTED_MAINTAINER,
    "/tools/": EXPECTED_MAINTAINER,
    "/.github/workflows/": EXPECTED_MAINTAINER,
}
STALE_OWNERSHIP_ROADMAP = "Add maintainers and code ownership"


def read_text(path: Path, findings: list[Finding], code: str) -> str | None:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError as exc:
        findings.append(Finding(code, str(exc), path=rel(path, path.parent)))
        return None


def validate_licensing(root: Path, findings: list[Finding]) -> None:
    license_path = root / "LICENSE"
    if license_path.is_file():
        license_text = read_text(license_path, findings, "LICENSE_ENCODING")
        if license_text is not None:
            for marker in APACHE_LICENSE_MARKERS:
                if marker not in license_text:
                    findings.append(Finding(
                        "LICENSE_INVALID",
                        f"Apache-2.0 license text is missing required marker: {marker}",
                        path="LICENSE",
                    ))

    notice_path = root / "NOTICE"
    if notice_path.is_file():
        notice_text = read_text(notice_path, findings, "NOTICE_ENCODING")
        if notice_text is not None:
            if EXPECTED_COPYRIGHT not in notice_text:
                findings.append(Finding(
                    "NOTICE_INVALID",
                    f"NOTICE must contain the expected copyright statement: {EXPECTED_COPYRIGHT}",
                    path="NOTICE",
                ))
            if "Apache License, Version 2.0" not in notice_text:
                findings.append(Finding(
                    "NOTICE_INVALID",
                    "NOTICE must identify the Apache License, Version 2.0.",
                    path="NOTICE",
                ))

    licensing_path = root / "LICENSING.md"
    if licensing_path.is_file():
        licensing_text = read_text(licensing_path, findings, "LICENSING_ENCODING")
        if licensing_text is not None:
            if SPDX_IDENTIFIER not in licensing_text:
                findings.append(Finding(
                    "LICENSING_POLICY_INVALID",
                    f"LICENSING.md must contain the SPDX identifier {SPDX_IDENTIFIER}.",
                    path="LICENSING.md",
                ))
            if EXPECTED_COPYRIGHT not in licensing_text:
                findings.append(Finding(
                    "LICENSING_POLICY_INVALID",
                    f"LICENSING.md must contain the expected copyright statement: {EXPECTED_COPYRIGHT}",
                    path="LICENSING.md",
                ))
            for required_link in ("[`LICENSE`](LICENSE)", "[`NOTICE`](NOTICE)"):
                if required_link not in licensing_text:
                    findings.append(Finding(
                        "LICENSING_POLICY_INVALID",
                        f"LICENSING.md must link to {required_link}.",
                        path="LICENSING.md",
                    ))

    for name in ("README.md", "CONTRIBUTING.md"):
        path = root / name
        if not path.is_file():
            continue
        text = read_text(path, findings, "LICENSE_DECLARATION_ENCODING")
        if text is None:
            continue
        if STALE_LICENSE_TEXT in text:
            findings.append(Finding(
                "LICENSE_SELECTION_STALE",
                "Repository documentation still states that no license has been selected.",
                path=name,
            ))
        if SPDX_IDENTIFIER not in text:
            findings.append(Finding(
                "LICENSE_DECLARATION_MISSING",
                f"Repository documentation must identify the license with SPDX identifier {SPDX_IDENTIFIER}.",
                path=name,
            ))


def parse_codeowners(text: str, findings: list[Finding]) -> dict[str, list[str]]:
    routes: dict[str, list[str]] = {}
    for line_number, line in enumerate(text.splitlines(), start=1):
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        parts = stripped.split()
        if len(parts) < 2:
            findings.append(Finding(
                "CODEOWNERS_INVALID",
                "CODEOWNERS route must contain a path pattern and at least one owner.",
                path=".github/CODEOWNERS",
                line=line_number,
            ))
            continue
        routes[parts[0]] = parts[1:]
    return routes


def validate_ownership(root: Path, findings: list[Finding]) -> None:
    maintainers_path = root / "MAINTAINERS.md"
    if maintainers_path.is_file():
        maintainers_text = read_text(maintainers_path, findings, "MAINTAINERS_ENCODING")
        if maintainers_text is not None:
            for marker in MAINTAINER_MARKERS:
                if marker not in maintainers_text:
                    findings.append(Finding(
                        "MAINTAINERS_POLICY_INCOMPLETE",
                        f"MAINTAINERS.md is missing required section marker: {marker}",
                        path="MAINTAINERS.md",
                    ))
            for identity in (EXPECTED_MAINTAINER_NAME, EXPECTED_MAINTAINER):
                if identity not in maintainers_text:
                    findings.append(Finding(
                        "MAINTAINER_ROSTER_INVALID",
                        f"MAINTAINERS.md must identify the current maintainer: {identity}",
                        path="MAINTAINERS.md",
                    ))
            if "one active maintainer" not in maintainers_text:
                findings.append(Finding(
                    "MAINTAINER_LIMITATION_MISSING",
                    "MAINTAINERS.md must disclose the current single-maintainer limitation.",
                    path="MAINTAINERS.md",
                ))
            if "must not be the author" not in maintainers_text:
                findings.append(Finding(
                    "SPECIALIST_INDEPENDENCE_MISSING",
                    "MAINTAINERS.md must require independent specialist review where applicable.",
                    path="MAINTAINERS.md",
                ))

    codeowners_path = root / ".github" / "CODEOWNERS"
    if not codeowners_path.is_file():
        findings.append(Finding(
            "CODEOWNERS_MISSING",
            "Repository review routing file is missing.",
            path=".github/CODEOWNERS",
        ))
    else:
        codeowners_text = read_text(codeowners_path, findings, "CODEOWNERS_ENCODING")
        if codeowners_text is not None:
            routes = parse_codeowners(codeowners_text, findings)
            for pattern, required_owner in REQUIRED_CODEOWNER_ROUTES.items():
                owners = routes.get(pattern)
                if owners is None:
                    findings.append(Finding(
                        "CODEOWNERS_ROUTE_MISSING",
                        f"CODEOWNERS is missing required route: {pattern}",
                        path=".github/CODEOWNERS",
                    ))
                elif required_owner not in owners:
                    findings.append(Finding(
                        "CODEOWNERS_OWNER_MISSING",
                        f"CODEOWNERS route {pattern} must include {required_owner}.",
                        path=".github/CODEOWNERS",
                    ))

    required_links = {
        "README.md": ("[`MAINTAINERS.md`](MAINTAINERS.md)", "[`.github/CODEOWNERS`](.github/CODEOWNERS)"),
        "CONTRIBUTING.md": ("[`MAINTAINERS.md`](MAINTAINERS.md)", "[`.github/CODEOWNERS`](.github/CODEOWNERS)"),
        "AGENTS.md": ("`MAINTAINERS.md`", "`.github/CODEOWNERS`"),
    }
    for name, markers in required_links.items():
        path = root / name
        if not path.is_file():
            continue
        text = read_text(path, findings, "OWNERSHIP_DECLARATION_ENCODING")
        if text is None:
            continue
        for marker in markers:
            if marker not in text:
                findings.append(Finding(
                    "OWNERSHIP_DECLARATION_MISSING",
                    f"{name} must reference ownership contract {marker}.",
                    path=name,
                ))

    roadmap = root / "ROADMAP.md"
    if roadmap.is_file():
        roadmap_text = read_text(roadmap, findings, "ROADMAP_ENCODING")
        if roadmap_text is not None and STALE_OWNERSHIP_ROADMAP in roadmap_text:
            findings.append(Finding(
                "OWNERSHIP_ROADMAP_STALE",
                "ROADMAP.md still lists maintainers and code ownership as unfinished.",
                path="ROADMAP.md",
            ))


def run(args: argparse.Namespace) -> ToolResult:
    root = args.root.resolve()
    findings: list[Finding] = []
    if not root.is_dir():
        raise ValueError(f"Repository root does not exist or is not a directory: {root}")

    for name in sorted(REQUIRED_ROOT):
        if not (root / name).is_file():
            findings.append(Finding("ROOT_FILE_MISSING", f"Missing required root file: {name}", path=name))

    validate_licensing(root, findings)
    validate_ownership(root, findings)

    bootstrap = root / "bootstrap"
    if bootstrap.exists():
        findings.append(Finding(
            "BOOTSTRAP_PRESENT",
            "Temporary bootstrap content remains in the final repository tree.",
            path="bootstrap",
        ))

    for name in sorted(TEMPORARY_NAMES):
        path = root / name
        if path.exists():
            findings.append(Finding("TEMPORARY_ARTIFACT", "Temporary diagnostic artifact remains.", path=name))

    generated_artifacts: set[str] = set()
    tracked = subprocess.run(
        ["git", "-C", str(root), "ls-files", "-z"],
        check=False,
        capture_output=True,
        text=False,
    )
    if tracked.returncode == 0:
        candidates = [
            root / item.decode("utf-8", errors="surrogateescape")
            for item in tracked.stdout.split(b"\0")
            if item
        ]
    else:
        candidates = list(root.rglob("*"))

    for path in candidates:
        if "__pycache__" in path.parts or path.suffix in {".pyc", ".pyo"}:
            generated_artifacts.add(rel(path, root))
    for artifact in sorted(generated_artifacts):
        findings.append(Finding(
            "PYTHON_CACHE_PRESENT",
            "Generated Python cache or bytecode must not be committed.",
            path=artifact,
        ))

    json_count = 0
    for path in sorted(root.rglob("*.json")):
        json_count += 1
        try:
            json.loads(path.read_text(encoding="utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            findings.append(Finding(
                "JSON_INVALID",
                str(exc),
                path=rel(path, root),
                line=getattr(exc, "lineno", None),
            ))

    ids: dict[str, Path] = {}
    markdown_count = 0
    for path in sorted(root.rglob("*.md")):
        markdown_count += 1
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError as exc:
            findings.append(Finding("MARKDOWN_ENCODING", str(exc), path=rel(path, root)))
            continue
        match = FRONTMATTER_ID.search(text)
        if match:
            document_id = match.group(1)
            if document_id in ids:
                findings.append(Finding(
                    "DUPLICATE_ID",
                    f"Duplicate front-matter ID also used by {rel(ids[document_id], root)}: {document_id}",
                    path=rel(path, root),
                ))
            else:
                ids[document_id] = path

    agents_count = 0
    for path in sorted(root.rglob("AGENTS.md")):
        agents_count += 1
        try:
            text = path.read_text(encoding="utf-8").strip()
        except UnicodeDecodeError:
            continue  # already reported as MARKDOWN_ENCODING above
        if len(text) < args.minimum_agents_length:
            findings.append(Finding(
                "AGENTS_INCOMPLETE",
                f"AGENTS.md contains {len(text)} characters; minimum is {args.minimum_agents_length}.",
                path=rel(path, root),
            ))

    summary = {
        "rootFilesRequired": len(REQUIRED_ROOT),
        "licensingFilesRequired": 3,
        "ownershipFilesRequired": 2,
        "codeownerRoutesRequired": len(REQUIRED_CODEOWNER_ROUTES),
        "jsonFiles": json_count,
        "markdownFiles": markdown_count,
        "identifiedDocuments": len(ids),
        "agentInstructionFiles": agents_count,
        "findings": len(findings),
    }
    return ToolResult.from_findings(tool=TOOL, version=VERSION, findings=findings, summary=summary)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    add_common_arguments(parser, default_root=DEFAULT_ROOT)
    parser.add_argument(
        "--minimum-agents-length",
        type=int,
        default=300,
        help="Minimum non-whitespace character count for AGENTS.md files.",
    )
    parser.add_argument("--debug", action="store_true", help=argparse.SUPPRESS)
    return parser


def main(argv: list[str] | None = None) -> int:
    return execute_tool(tool=TOOL, version=VERSION, parser=build_parser(), run=run, argv=argv)


if __name__ == "__main__":
    raise SystemExit(main())
