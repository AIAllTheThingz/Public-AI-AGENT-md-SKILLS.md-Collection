#!/usr/bin/env python3
"""Validate repository skill entry points, routing coverage, and optional UI metadata."""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import unquote, urlsplit

TOOLS_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TOOLS_ROOT / "lib"))

from standards_tools import Finding, ToolResult, add_common_arguments, execute_tool, rel  # noqa: E402

TOOL = "validate-skills"
VERSION = "1.0.0"
DEFAULT_ROOT = Path(__file__).resolve().parents[2]
NAME = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
FRONTMATTER_FIELD = re.compile(r"^([A-Za-z][A-Za-z0-9_-]*):\s*(.*)$")
INLINE_LINK = re.compile(r"!?\[[^\]]*\]\(([^)]+)\)")
REFERENCE_LINK = re.compile(r"^[ ]{0,3}\[[^\]]+\]:\s*(\S+)", re.MULTILINE)
FENCE = re.compile(r"```.*?```|~~~.*?~~~", re.DOTALL)
INLINE_CODE = re.compile(r"`[^`\n]*`")
WINDOWS_ABSOLUTE = re.compile(r"^[A-Za-z]:[\\/]")
SAFE_EXTERNAL_SCHEMES = {"http", "https", "mailto", "tel"}
PLACEHOLDER = re.compile(r"\b(?:TODO|TBD|FIXME)\b|<\s*PLACEHOLDER\s*>", re.IGNORECASE)
COMPLETE_PACKAGES_HEADING = re.compile(r"^##\s+Complete(?:\s+[A-Za-z0-9-]+)*\s+packages\s*$", re.IGNORECASE)
REGISTRY_HEADING = re.compile(r"^##\s+Agent skill entry points\s*$", re.IGNORECASE)
BACKTICK_SKILL = re.compile(r"`([^`]*SKILL\.md)`")
BACKTICK_PATH = re.compile(r"`([^`]+)`")
METADATA_FIELD = re.compile(r"^\s+([a-z][a-z0-9_]*):\s*(.*?)\s*$", re.MULTILINE)


@dataclass(frozen=True)
class ParsedSkill:
    path: Path
    name: str | None
    description: str | None
    body: str
    body_start_line: int


def unquote_scalar(value: str) -> str:
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] == '"':
        try:
            decoded = json.loads(value)
        except json.JSONDecodeError:
            return value[1:-1]
        return decoded if isinstance(decoded, str) else value
    if len(value) >= 2 and value[0] == value[-1] == "'":
        return value[1:-1].replace("''", "'")
    return value


def parse_skill(path: Path, root: Path, findings: list[Finding]) -> ParsedSkill:
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    rel_path = rel(path, root)
    if not lines or lines[0].strip() != "---":
        findings.append(Finding(
            "SKILL_FRONTMATTER_MISSING",
            "SKILL.md must begin with YAML frontmatter.",
            path=rel_path,
            line=1,
        ))
        return ParsedSkill(path, None, None, text, 1)

    closing = next((index for index, line in enumerate(lines[1:], start=1) if line.strip() == "---"), None)
    if closing is None:
        findings.append(Finding(
            "SKILL_FRONTMATTER_UNTERMINATED",
            "SKILL.md frontmatter does not have a closing delimiter.",
            path=rel_path,
            line=1,
        ))
        return ParsedSkill(path, None, None, "", len(lines) + 1)

    fields: dict[str, str] = {}
    for index, line in enumerate(lines[1:closing], start=2):
        match = FRONTMATTER_FIELD.match(line)
        if not match:
            findings.append(Finding(
                "SKILL_FRONTMATTER_INVALID",
                "Frontmatter fields must be single-line key/value scalars.",
                path=rel_path,
                line=index,
            ))
            continue
        key, raw_value = match.groups()
        if key not in {"name", "description"}:
            findings.append(Finding(
                "SKILL_FRONTMATTER_KEY_UNSUPPORTED",
                f"Unsupported SKILL.md frontmatter key: {key}",
                path=rel_path,
                line=index,
            ))
            continue
        if key in fields:
            findings.append(Finding(
                "SKILL_FRONTMATTER_FIELD_DUPLICATE",
                f"Frontmatter field appears more than once: {key}",
                path=rel_path,
                line=index,
            ))
            continue
        if raw_value.strip() in {"|", ">", "|-", ">-", "|+", ">+"}:
            findings.append(Finding(
                "SKILL_FRONTMATTER_INVALID",
                f"Frontmatter field must use a single-line scalar: {key}",
                path=rel_path,
                line=index,
            ))
            continue
        fields[key] = unquote_scalar(raw_value)

    for required in ("name", "description"):
        if not fields.get(required, "").strip():
            findings.append(Finding(
                "SKILL_FRONTMATTER_FIELD_MISSING",
                f"Required SKILL.md frontmatter field is missing or empty: {required}",
                path=rel_path,
                line=1,
            ))

    return ParsedSkill(
        path=path,
        name=fields.get("name"),
        description=fields.get("description"),
        body="\n".join(lines[closing + 1:]),
        body_start_line=closing + 2,
    )


def section_lines(text: str, heading: re.Pattern[str]) -> list[tuple[int, str]]:
    lines = text.splitlines()
    start = next((index for index, line in enumerate(lines) if heading.match(line.strip())), None)
    if start is None:
        return []
    selected: list[tuple[int, str]] = []
    for index, line in enumerate(lines[start + 1:], start=start + 2):
        if line.startswith("## "):
            break
        selected.append((index, line))
    return selected


def extract_links(text: str) -> list[tuple[str, int]]:
    scrubbed = FENCE.sub("", text)
    scrubbed = INLINE_CODE.sub("", scrubbed)
    targets: list[tuple[str, int]] = []
    for pattern in (INLINE_LINK, REFERENCE_LINK):
        for match in pattern.finditer(scrubbed):
            target = match.group(1).strip()
            if target.startswith("<") and target.endswith(">"):
                target = target[1:-1]
            if " " in target and not target.startswith(("http://", "https://")):
                target = target.split()[0]
            targets.append((target, scrubbed.count("\n", 0, match.start()) + 1))
    return targets


def resolve_local_target(
    *, raw_target: str, source: Path, root: Path, path: str, line: int, findings: list[Finding]
) -> Path | None:
    parsed = urlsplit(raw_target)
    scheme = parsed.scheme.lower()
    if WINDOWS_ABSOLUTE.match(raw_target):
        findings.append(Finding(
            "SKILL_LINK_ABSOLUTE",
            f"Skill instructions must not use absolute filesystem links: {raw_target}",
            path=path,
            line=line,
        ))
        return None
    if scheme in SAFE_EXTERNAL_SCHEMES:
        return None
    if scheme:
        findings.append(Finding(
            "SKILL_LINK_UNSAFE_SCHEME",
            f"Skill link uses an unsafe or unsupported scheme: {raw_target}",
            path=path,
            line=line,
        ))
        return None
    if raw_target.startswith("#"):
        return None
    target_path = unquote(parsed.path)
    if WINDOWS_ABSOLUTE.match(target_path) or target_path.startswith("/"):
        findings.append(Finding(
            "SKILL_LINK_ABSOLUTE",
            f"Skill instructions must not use absolute filesystem links: {raw_target}",
            path=path,
            line=line,
        ))
        return None
    destination = source if not target_path else source.parent / target_path
    resolved = destination.resolve()
    try:
        resolved.relative_to(root)
    except ValueError:
        findings.append(Finding(
            "SKILL_LINK_ESCAPE",
            f"Skill link escapes the repository root: {raw_target}",
            path=path,
            line=line,
        ))
        return None
    if not resolved.exists():
        findings.append(Finding(
            "SKILL_LINK_MISSING",
            f"Skill link target does not exist: {raw_target}",
            path=path,
            line=line,
        ))
        return None
    return resolved


def declared_packages(skill: ParsedSkill, root: Path, findings: list[Finding]) -> set[Path]:
    manifest = skill.path.parent / "MANIFEST.md"
    if not manifest.is_file():
        return set()
    text = manifest.read_text(encoding="utf-8")
    packages: set[Path] = set()
    for line_number, line in section_lines(text, COMPLETE_PACKAGES_HEADING):
        for raw_path in BACKTICK_PATH.findall(line):
            candidate = root / raw_path if "/" in raw_path else skill.path.parent / raw_path
            resolved = candidate.resolve()
            try:
                resolved.relative_to(root)
            except ValueError:
                findings.append(Finding(
                    "SKILL_PACKAGE_DECLARATION_ESCAPE",
                    f"Declared package escapes the repository root: {raw_path}",
                    path=rel(manifest, root),
                    line=line_number,
                ))
                continue
            if not resolved.is_dir():
                findings.append(Finding(
                    "SKILL_PACKAGE_DECLARATION_MISSING",
                    f"Declared skill package does not exist: {raw_path}",
                    path=rel(manifest, root),
                    line=line_number,
                ))
                continue
            packages.add(resolved)
    return packages


def validate_metadata(
    skill: ParsedSkill, root: Path, findings: list[Finding], require_metadata: bool
) -> int:
    metadata = skill.path.parent / "agents" / "openai.yaml"
    rel_skill = rel(skill.path, root)
    if not metadata.is_file():
        if require_metadata:
            findings.append(Finding(
                "SKILL_METADATA_MISSING",
                "Recommended agents/openai.yaml metadata is required by this run.",
                path=rel_skill,
            ))
        return 0

    try:
        metadata.resolve().relative_to(skill.path.parent.resolve())
    except ValueError:
        findings.append(Finding(
            "SKILL_METADATA_ESCAPE",
            "agents/openai.yaml resolves outside the skill directory.",
            path=rel(metadata, root),
        ))
        return 1

    text = metadata.read_text(encoding="utf-8")
    rel_metadata = rel(metadata, root)
    if not re.search(r"^interface:\s*$", text, re.MULTILINE):
        findings.append(Finding(
            "SKILL_METADATA_INTERFACE_MISSING",
            "agents/openai.yaml must contain an interface mapping.",
            path=rel_metadata,
        ))
        return 1

    fields = {key: unquote_scalar(value) for key, value in METADATA_FIELD.findall(text)}
    for required in ("display_name", "short_description", "default_prompt"):
        if not fields.get(required, "").strip():
            findings.append(Finding(
                "SKILL_METADATA_FIELD_MISSING",
                f"Required interface field is missing or empty: {required}",
                path=rel_metadata,
            ))
    short_description = fields.get("short_description", "")
    if short_description and not 25 <= len(short_description) <= 64:
        findings.append(Finding(
            "SKILL_METADATA_SHORT_DESCRIPTION_LENGTH",
            "short_description must contain between 25 and 64 characters.",
            path=rel_metadata,
        ))
    if skill.name and fields.get("default_prompt") and f"${skill.name}" not in fields["default_prompt"]:
        findings.append(Finding(
            "SKILL_METADATA_PROMPT_REFERENCE",
            f"default_prompt must reference ${skill.name}.",
            path=rel_metadata,
        ))

    for icon_key in ("icon_small", "icon_large"):
        if not fields.get(icon_key):
            continue
        icon = (skill.path.parent / fields[icon_key]).resolve()
        try:
            icon.relative_to(skill.path.parent.resolve())
        except ValueError:
            findings.append(Finding(
                "SKILL_METADATA_ICON_ESCAPE",
                f"{icon_key} escapes the skill directory.",
                path=rel_metadata,
            ))
            continue
        if not icon.is_file():
            findings.append(Finding(
                "SKILL_METADATA_ICON_MISSING",
                f"{icon_key} does not reference an existing file: {fields[icon_key]}",
                path=rel_metadata,
            ))
    return 1


def registry_entries(root: Path, findings: list[Finding]) -> Counter[str]:
    manifest = root / "MANIFEST.md"
    if not manifest.is_file():
        findings.append(Finding(
            "SKILL_REGISTRY_MISSING",
            "Repository MANIFEST.md is required to register skill entry points.",
            path="MANIFEST.md",
        ))
        return Counter()
    selected = section_lines(manifest.read_text(encoding="utf-8"), REGISTRY_HEADING)
    if not selected:
        findings.append(Finding(
            "SKILL_REGISTRY_MISSING",
            "MANIFEST.md must contain an 'Agent skill entry points' section.",
            path="MANIFEST.md",
        ))
        return Counter()
    entries: Counter[str] = Counter()
    for line_number, line in selected:
        for raw_path in BACKTICK_SKILL.findall(line):
            candidate = (root / raw_path).resolve()
            try:
                normalized = rel(candidate, root)
            except ValueError:
                findings.append(Finding(
                    "SKILL_REGISTRY_ESCAPE",
                    f"Registered skill path escapes the repository root: {raw_path}",
                    path="MANIFEST.md",
                    line=line_number,
                ))
                continue
            entries[normalized] += 1
            if not candidate.is_file():
                findings.append(Finding(
                    "SKILL_REGISTRY_TARGET_MISSING",
                    f"Registered skill does not exist: {raw_path}",
                    path="MANIFEST.md",
                    line=line_number,
                ))
    for registered, count in sorted(entries.items()):
        if count > 1:
            findings.append(Finding(
                "SKILL_REGISTRY_DUPLICATE",
                f"Skill is registered {count} times: {registered}",
                path="MANIFEST.md",
            ))
    return entries


def run(args: argparse.Namespace) -> ToolResult:
    root = args.root.resolve()
    if args.max_body_lines < 1:
        raise ValueError("--max-body-lines must be at least 1")
    if args.minimum_description_characters < 1:
        raise ValueError("--minimum-description-characters must be at least 1")
    if args.maximum_description_characters < args.minimum_description_characters:
        raise ValueError("--maximum-description-characters must not be smaller than the minimum")

    findings: list[Finding] = []
    discovered_skill_paths = sorted(
        path for path in root.rglob("SKILL.md")
        if ".git" not in path.parts and path.is_file()
    )
    skill_paths: list[Path] = []
    for path in discovered_skill_paths:
        try:
            path.resolve().relative_to(root)
        except ValueError:
            findings.append(Finding(
                "SKILL_FILE_ESCAPE",
                "SKILL.md resolves outside the repository root.",
                path=rel(path, root),
            ))
        else:
            skill_paths.append(path)
    if not skill_paths:
        findings.append(Finding(
            "SKILL_NONE_FOUND",
            "Repository does not contain a SKILL.md entry point.",
            path=".",
        ))

    registry = registry_entries(root, findings)
    parsed_skills = [parse_skill(path, root, findings) for path in skill_paths]
    names: defaultdict[str, list[ParsedSkill]] = defaultdict(list)
    package_routes = 0
    metadata_files = 0

    for skill in parsed_skills:
        rel_path = rel(skill.path, root)
        if registry[rel_path] == 0:
            findings.append(Finding(
                "SKILL_NOT_REGISTERED",
                "SKILL.md is not registered in MANIFEST.md.",
                path=rel_path,
            ))

        if skill.name:
            names[skill.name].append(skill)
            if len(skill.name) > 64:
                findings.append(Finding(
                    "SKILL_NAME_TOO_LONG",
                    "Skill name must not exceed 64 characters.",
                    path=rel_path,
                    line=2,
                ))
            if not NAME.fullmatch(skill.name):
                findings.append(Finding(
                    "SKILL_NAME_INVALID",
                    "Skill name must use lowercase letters, digits, and single hyphens.",
                    path=rel_path,
                    line=2,
                ))
            if skill.name != skill.path.parent.name:
                findings.append(Finding(
                    "SKILL_NAME_DIRECTORY_MISMATCH",
                    f"Skill name '{skill.name}' must match directory '{skill.path.parent.name}'.",
                    path=rel_path,
                    line=2,
                ))

        if skill.description:
            description = skill.description.strip()
            if len(description) < args.minimum_description_characters:
                findings.append(Finding(
                    "SKILL_DESCRIPTION_TOO_SHORT",
                    f"Skill description must contain at least {args.minimum_description_characters} characters.",
                    path=rel_path,
                    line=3,
                ))
            if len(description) > args.maximum_description_characters:
                findings.append(Finding(
                    "SKILL_DESCRIPTION_TOO_LONG",
                    f"Skill description must not exceed {args.maximum_description_characters} characters.",
                    path=rel_path,
                    line=3,
                ))
            if not re.search(r"\buse\s+when\b", description, re.IGNORECASE):
                findings.append(Finding(
                    "SKILL_DESCRIPTION_TRIGGER_MISSING",
                    "Skill description must state when to use it with a 'Use when' trigger clause.",
                    path=rel_path,
                    line=3,
                ))
            if len(description.split()) > 100:
                findings.append(Finding(
                    "SKILL_DESCRIPTION_WORDY",
                    "Skill description exceeds 100 words; shorten it to preserve context.",
                    severity="warning",
                    path=rel_path,
                    line=3,
                ))

        body_lines = skill.body.splitlines()
        if not skill.body.strip():
            findings.append(Finding(
                "SKILL_BODY_MISSING",
                "SKILL.md must contain instructions after its frontmatter.",
                path=rel_path,
                line=skill.body_start_line,
            ))
        else:
            if not re.search(r"^#\s+\S", skill.body, re.MULTILINE):
                findings.append(Finding(
                    "SKILL_BODY_TITLE_MISSING",
                    "Skill instructions must contain an H1 title.",
                    path=rel_path,
                    line=skill.body_start_line,
                ))
            if len(body_lines) > args.max_body_lines:
                findings.append(Finding(
                    "SKILL_BODY_TOO_LONG",
                    f"Skill body exceeds the {args.max_body_lines}-line progressive-disclosure limit.",
                    path=rel_path,
                ))
            for index, line in enumerate(body_lines, start=skill.body_start_line):
                if re.match(r"^#{1,6}\s+When to (?:use|apply|invoke)\b", line, re.IGNORECASE):
                    findings.append(Finding(
                        "SKILL_BODY_TRIGGER_HEADING",
                        "Trigger guidance belongs in the description, not a 'When to use' body section.",
                        path=rel_path,
                        line=index,
                    ))
                if PLACEHOLDER.search(line):
                    findings.append(Finding(
                        "SKILL_PLACEHOLDER",
                        "Skill instructions contain an unresolved placeholder marker.",
                        path=rel_path,
                        line=index,
                    ))

        link_targets: Counter[Path] = Counter()
        for raw_target, body_line in extract_links(skill.body):
            resolved = resolve_local_target(
                raw_target=raw_target,
                source=skill.path,
                root=root,
                path=rel_path,
                line=skill.body_start_line + body_line - 1,
                findings=findings,
            )
            if resolved is not None:
                link_targets[resolved] += 1

        discovered: set[Path] = set()
        for directory in skill.path.parent.iterdir():
            if not (
                directory.is_dir()
                and (directory / "AGENTS.md").is_file()
                and ((directory / "MANIFEST.md").is_file() or (directory / "README.md").is_file())
            ):
                continue
            resolved_directory = directory.resolve()
            try:
                resolved_directory.relative_to(root)
            except ValueError:
                findings.append(Finding(
                    "SKILL_PACKAGE_DISCOVERY_ESCAPE",
                    f"Discovered package resolves outside the repository root: {directory.name}",
                    path=rel_path,
                ))
                continue
            discovered.add(resolved_directory)
        packages = discovered | declared_packages(skill, root, findings)
        for package in sorted(packages):
            count = link_targets[package]
            if count == 0:
                findings.append(Finding(
                    "SKILL_PACKAGE_ROUTE_MISSING",
                    f"Skill does not route to package: {rel(package, root)}",
                    path=rel_path,
                ))
            elif count > 1:
                findings.append(Finding(
                    "SKILL_PACKAGE_ROUTE_DUPLICATE",
                    f"Skill routes to package {count} times: {rel(package, root)}",
                    path=rel_path,
                ))
            else:
                package_routes += 1

        metadata_files += validate_metadata(skill, root, findings, args.require_agent_metadata)

    for name, skills in sorted(names.items()):
        if len(skills) > 1:
            locations = [rel(skill.path, root) for skill in skills]
            for skill in skills:
                findings.append(Finding(
                    "SKILL_NAME_DUPLICATE",
                    f"Skill name '{name}' is also used by: {', '.join(path for path in locations if path != rel(skill.path, root))}",
                    path=rel(skill.path, root),
                    line=2,
                ))

    findings.sort(key=lambda item: (item.path or "", item.line or 0, item.code, item.message))
    return ToolResult.from_findings(
        tool=TOOL,
        version=VERSION,
        findings=findings,
        summary={
            "skillFiles": len(skill_paths),
            "registeredSkills": sum(1 for path in skill_paths if registry[rel(path, root)] == 1),
            "packageRoutes": package_routes,
            "metadataFiles": metadata_files,
            "findings": len(findings),
        },
        metadata={
            "limits": {
                "maxBodyLines": args.max_body_lines,
                "minimumDescriptionCharacters": args.minimum_description_characters,
                "maximumDescriptionCharacters": args.maximum_description_characters,
            },
            "agentMetadataRequired": args.require_agent_metadata,
        },
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    add_common_arguments(parser, default_root=DEFAULT_ROOT)
    parser.add_argument("--max-body-lines", type=int, default=500)
    parser.add_argument("--minimum-description-characters", type=int, default=40)
    parser.add_argument("--maximum-description-characters", type=int, default=1024)
    parser.add_argument(
        "--require-agent-metadata",
        action="store_true",
        help="Require every skill to provide agents/openai.yaml UI metadata.",
    )
    parser.add_argument("--debug", action="store_true", help=argparse.SUPPRESS)
    return parser


def main(argv: list[str] | None = None) -> int:
    return execute_tool(tool=TOOL, version=VERSION, parser=build_parser(), run=run, argv=argv)


if __name__ == "__main__":
    raise SystemExit(main())
