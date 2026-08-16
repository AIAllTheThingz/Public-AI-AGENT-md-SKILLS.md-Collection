#!/usr/bin/env python3
"""Validate repository versioning, release notes, maturity policy, and tag contracts."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

TOOLS_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TOOLS_ROOT / "lib"))

from standards_tools import Finding, ToolResult, add_common_arguments, execute_tool  # noqa: E402

TOOL = "validate-release"
VERSION = "1.0.0"
DEFAULT_ROOT = Path(__file__).resolve().parents[2]
RELEASE_STATE_PATH = Path("releases/release-state.json")
SEMVER_CORE = r"(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)"
SEMVER_PRERELEASE_ID = r"(?:0|[1-9][0-9]*|[0-9A-Za-z-]*[A-Za-z-][0-9A-Za-z-]*)"
SEMVER_PATTERN = (
    rf"{SEMVER_CORE}"
    rf"(?:-{SEMVER_PRERELEASE_ID}(?:\.{SEMVER_PRERELEASE_ID})*)?"
    r"(?:\+[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*)?"
)
SEMVER = re.compile(rf"^{SEMVER_PATTERN}$")
REQUIRED_ROOT = ("VERSION", "CHANGELOG.md", "RELEASE_POLICY.md", "MATURITY_POLICY.md")
REQUIRED_RELEASE_HEADINGS = (
    "## Breaking changes",
    "## Normative changes",
    "## Editorial changes",
    "## Deprecations",
    "## Migration notes",
    "## Security",
    "## Known limitations",
)
REQUIRED_POLICY_HEADINGS = (
    "## Repository semantic versioning",
    "## Pre-1.0 policy",
    "## Deprecation windows",
    "## Release process",
    "## Git tags",
    "## GitHub releases",
    "## Release artifacts and checksums",
    "## 1.0.0 compatibility gate",
)
REQUIRED_MATURITY_HEADINGS = (
    "## Maturity states",
    "## Promotion requirements",
    "## Baseline to stable review",
    "## Demotion and deprecation",
    "## Review record",
)


def rel(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix()


def read_version(root: Path, findings: list[Finding]) -> str | None:
    path = root / "VERSION"
    if not path.is_file():
        findings.append(Finding("RELEASE_FILE_MISSING", "Missing repository version file.", path="VERSION"))
        return None
    version = path.read_text(encoding="utf-8").strip()
    if not SEMVER.fullmatch(version):
        findings.append(Finding(
            "RELEASE_VERSION_INVALID",
            "VERSION must contain exactly one Semantic Version 2.0.0 value.",
            path="VERSION",
            details={"value": version},
        ))
        return None
    return version


def read_release_state(root: Path, findings: list[Finding]) -> dict[str, Any]:
    """Read optional repository publication-state metadata."""
    path = root / RELEASE_STATE_PATH
    if not path.is_file():
        return {}
    try:
        state = json.loads(path.read_text(encoding="utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        findings.append(Finding(
            "RELEASE_STATE_INVALID",
            f"Release-state metadata is not valid JSON: {exc}",
            path=RELEASE_STATE_PATH.as_posix(),
        ))
        return {}
    if not isinstance(state, dict):
        findings.append(Finding(
            "RELEASE_STATE_INVALID",
            "Release-state metadata must be a JSON object.",
            path=RELEASE_STATE_PATH.as_posix(),
        ))
        return {}
    blocked = state.get("preparedUnpublishedVersions", [])
    if not isinstance(blocked, list) or any(not isinstance(item, str) or not SEMVER.fullmatch(item) for item in blocked):
        findings.append(Finding(
            "RELEASE_STATE_INVALID",
            "preparedUnpublishedVersions must be an array of Semantic Version strings.",
            path=RELEASE_STATE_PATH.as_posix(),
        ))
        return {}
    next_intended = state.get("nextIntendedVersion")
    if not isinstance(next_intended, str) or not SEMVER.fullmatch(next_intended):
        findings.append(Finding(
            "RELEASE_STATE_INVALID",
            "nextIntendedVersion must be a Semantic Version 2.0.0 string.",
            path=RELEASE_STATE_PATH.as_posix(),
            details={"value": next_intended},
        ))
        return {}
    return state


def git_output(root: Path, *args: str) -> str | None:
    completed = subprocess.run(
        ["git", "-C", str(root), *args],
        text=True,
        capture_output=True,
        check=False,
    )
    return completed.stdout.strip() if completed.returncode == 0 else None


def run(args: argparse.Namespace) -> ToolResult:
    root = args.root.resolve()
    findings: list[Finding] = []

    for name in REQUIRED_ROOT:
        if not (root / name).is_file():
            findings.append(Finding("RELEASE_FILE_MISSING", "Missing release-program file.", path=name))

    version = read_version(root, findings)
    release_state = read_release_state(root, findings)
    blocked_versions = set(release_state.get("preparedUnpublishedVersions", []))
    changelog = root / "CHANGELOG.md"
    release_notes = root / "releases" / f"{version}.md" if version else None
    migration = root / "releases" / "migrations" / f"{version}.md" if version else None
    release_policy = root / "RELEASE_POLICY.md"
    maturity_policy = root / "MATURITY_POLICY.md"
    workflow = root / ".github" / "workflows" / "release.yml"

    if version and changelog.is_file():
        text = changelog.read_text(encoding="utf-8")
        entry = re.compile(rf"^## \[{re.escape(version)}\] - \d{{4}}-\d{{2}}-\d{{2}}$", re.MULTILINE)
        if not entry.search(text):
            findings.append(Finding(
                "CHANGELOG_VERSION_MISSING",
                f"CHANGELOG.md lacks a dated [{version}] release entry.",
                path="CHANGELOG.md",
            ))
        if "## [Unreleased]" not in text:
            findings.append(Finding(
                "CHANGELOG_UNRELEASED_MISSING",
                "CHANGELOG.md must retain an Unreleased section.",
                path="CHANGELOG.md",
            ))

    if release_notes:
        if not release_notes.is_file():
            findings.append(Finding(
                "RELEASE_NOTES_MISSING",
                f"Missing release notes for version {version}.",
                path=rel(release_notes, root),
            ))
        else:
            text = release_notes.read_text(encoding="utf-8")
            for heading in REQUIRED_RELEASE_HEADINGS:
                if heading not in text:
                    findings.append(Finding(
                        "RELEASE_NOTES_SECTION_MISSING",
                        f"Release notes lack required section: {heading}",
                        path=rel(release_notes, root),
                    ))
            if f"# Public-Access-Agents {version}" not in text:
                findings.append(Finding(
                    "RELEASE_NOTES_VERSION_MISMATCH",
                    "Release notes title does not match VERSION.",
                    path=rel(release_notes, root),
                ))

    if migration:
        if not migration.is_file():
            findings.append(Finding(
                "MIGRATION_NOTES_MISSING",
                f"Missing migration notes for version {version}.",
                path=rel(migration, root),
            ))
        elif "## Required actions" not in migration.read_text(encoding="utf-8"):
            findings.append(Finding(
                "MIGRATION_NOTES_INCOMPLETE",
                "Migration notes must include a Required actions section.",
                path=rel(migration, root),
            ))

    if release_policy.is_file():
        text = release_policy.read_text(encoding="utf-8")
        for heading in REQUIRED_POLICY_HEADINGS:
            if heading not in text:
                findings.append(Finding(
                    "RELEASE_POLICY_SECTION_MISSING",
                    f"Release policy lacks required section: {heading}",
                    path="RELEASE_POLICY.md",
                ))
        for marker in ("90 calendar days", "180 calendar days", "vMAJOR.MINOR.PATCH"):
            if marker not in text:
                findings.append(Finding(
                    "RELEASE_POLICY_MARKER_MISSING",
                    f"Release policy lacks required compatibility marker: {marker}",
                    path="RELEASE_POLICY.md",
                ))

    if maturity_policy.is_file():
        text = maturity_policy.read_text(encoding="utf-8")
        for heading in REQUIRED_MATURITY_HEADINGS:
            if heading not in text:
                findings.append(Finding(
                    "MATURITY_POLICY_SECTION_MISSING",
                    f"Maturity policy lacks required section: {heading}",
                    path="MATURITY_POLICY.md",
                ))

    if not workflow.is_file():
        findings.append(Finding(
            "RELEASE_WORKFLOW_MISSING",
            "Missing tag-driven GitHub release workflow.",
            path=".github/workflows/release.yml",
        ))
    else:
        workflow_text = workflow.read_text(encoding="utf-8")
        for marker in ("tags:", "v*", "tools/release/build_release.py", "gh release create", "SHA256SUMS.txt"):
            if marker not in workflow_text:
                findings.append(Finding(
                    "RELEASE_WORKFLOW_INCOMPLETE",
                    f"Release workflow lacks required marker: {marker}",
                    path=".github/workflows/release.yml",
                ))

    expected_tag = f"v{version}" if version else None
    if args.tag and expected_tag and args.tag != expected_tag:
        findings.append(Finding(
            "RELEASE_TAG_MISMATCH",
            f"Tag {args.tag!r} does not match VERSION {version!r}; expected {expected_tag!r}.",
            path="VERSION",
        ))

    if version and version in blocked_versions and (args.tag or args.require_head_tag):
        findings.append(Finding(
            "RELEASE_PUBLICATION_BLOCKED",
            f"Version {version} is explicitly recorded as prepared but unpublished and must not be tagged or published from this repository state.",
            path=RELEASE_STATE_PATH.as_posix(),
            details={"version": version, "tag": args.tag or expected_tag},
        ))

    if args.require_head_tag and expected_tag:
        tags = set((git_output(root, "tag", "--points-at", "HEAD") or "").splitlines())
        if expected_tag not in tags:
            findings.append(Finding(
                "RELEASE_HEAD_TAG_MISSING",
                f"HEAD is not tagged with {expected_tag}.",
                path="VERSION",
            ))

    return ToolResult.from_findings(
        tool=TOOL,
        version=VERSION,
        findings=findings,
        summary={
            "repositoryVersion": version or "",
            "expectedTag": expected_tag or "",
            "releaseNotes": bool(release_notes and release_notes.is_file()),
            "migrationNotes": bool(migration and migration.is_file()),
            "publicationBlocked": bool(version and version in blocked_versions),
            "findings": len(findings),
        },
        metadata={
            "branch": git_output(root, "branch", "--show-current"),
            "commit": git_output(root, "rev-parse", "HEAD"),
            "tagChecked": args.tag,
        },
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    add_common_arguments(parser, default_root=DEFAULT_ROOT)
    parser.add_argument("--tag", help="Validate an explicit release tag such as v<VERSION>.")
    parser.add_argument("--require-head-tag", action="store_true")
    parser.add_argument("--debug", action="store_true", help=argparse.SUPPRESS)
    return parser


def main(argv: list[str] | None = None) -> int:
    return execute_tool(tool=TOOL, version=VERSION, parser=build_parser(), run=run, argv=argv)


if __name__ == "__main__":
    raise SystemExit(main())
