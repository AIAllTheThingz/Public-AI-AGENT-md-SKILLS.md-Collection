#!/usr/bin/env python3
"""Validate relative Markdown links and local heading anchors without network access."""

from __future__ import annotations

import argparse
import re
import sys
from collections import defaultdict
from pathlib import Path
from urllib.parse import unquote, urlsplit

TOOLS_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TOOLS_ROOT / "lib"))

from standards_tools import Finding, ToolResult, add_common_arguments, execute_tool  # noqa: E402

TOOL = "check-links"
VERSION = "1.0.0"
DEFAULT_ROOT = Path(__file__).resolve().parents[2]
INLINE_LINK = re.compile(r"!?\[[^\]]*\]\(([^)]+)\)")
REFERENCE_DEFINITION = re.compile(r"^[ ]{0,3}\[[^\]]+\]:\s*(\S+)", re.MULTILINE)
HEADING = re.compile(r"^(#{1,6})\s+(.+?)\s*#*\s*$", re.MULTILINE)
FENCE = re.compile(r"```.*?```|~~~.*?~~~", re.DOTALL)
INLINE_CODE = re.compile(r"`[^`]*`")
SAFE_EXTERNAL_SCHEMES = {"http", "https", "mailto", "tel"}
UNSAFE_SCHEMES = {"javascript", "data", "file"}
WINDOWS_ABSOLUTE = re.compile(r"^[A-Za-z]:[\\/]")


def github_slug(text: str) -> str:
    value = re.sub(r"<[^>]+>", "", text).strip().lower()
    value = re.sub(r"[^\w\- ]", "", value, flags=re.UNICODE)
    value = re.sub(r"\s+", "-", value)
    return value


def anchors_for(path: Path) -> set[str]:
    text = path.read_text(encoding="utf-8")
    seen: dict[str, int] = defaultdict(int)
    anchors: set[str] = set()
    for _, heading in HEADING.findall(text):
        base = github_slug(heading)
        count = seen[base]
        anchor = base if count == 0 else f"{base}-{count}"
        seen[base] += 1
        anchors.add(anchor)
    return anchors


def extract_targets(text: str) -> list[tuple[str, int]]:
    # Keep the newlines of removed code so reported line numbers match the file.
    blank = lambda match: "\n" * match.group().count("\n")  # noqa: E731
    scrubbed = FENCE.sub(blank, text)
    scrubbed = INLINE_CODE.sub(blank, scrubbed)
    targets: list[tuple[str, int]] = []
    for regex in (INLINE_LINK, REFERENCE_DEFINITION):
        for match in regex.finditer(scrubbed):
            raw = match.group(1).strip()
            if raw.startswith("<") and raw.endswith(">"):
                raw = raw[1:-1]
            if " " in raw and not raw.startswith(("http://", "https://")):
                raw = raw.split()[0]
            line = scrubbed.count("\n", 0, match.start()) + 1
            targets.append((raw, line))
    return targets


def run(args: argparse.Namespace) -> ToolResult:
    root = args.root.resolve()
    findings: list[Finding] = []
    documents = sorted(root.rglob("*.md"))
    anchor_cache: dict[Path, set[str]] = {}
    checked = 0

    for document in documents:
        text = document.read_text(encoding="utf-8")
        for raw_target, line in extract_targets(text):
            checked += 1
            parsed = urlsplit(raw_target)
            scheme = parsed.scheme.lower()
            rel_document = document.relative_to(root).as_posix()
            if scheme in SAFE_EXTERNAL_SCHEMES:
                continue
            if scheme in UNSAFE_SCHEMES:
                findings.append(Finding(
                    "LINK_UNSAFE_SCHEME",
                    f"Unsafe or unsupported link scheme: {raw_target}",
                    path=rel_document,
                    line=line,
                ))
                continue
            if scheme and not WINDOWS_ABSOLUTE.match(raw_target):
                continue

            target_path = unquote(parsed.path)
            anchor = unquote(parsed.fragment)
            if WINDOWS_ABSOLUTE.match(target_path) or target_path.startswith("/"):
                findings.append(Finding(
                    "LINK_ABSOLUTE_PATH",
                    f"Repository documentation must not use absolute filesystem links: {raw_target}",
                    path=rel_document,
                    line=line,
                ))
                continue

            destination = document if not target_path else (document.parent / target_path)
            try:
                resolved = destination.resolve()
                resolved.relative_to(root)
            except ValueError:
                findings.append(Finding(
                    "LINK_ESCAPES_ROOT",
                    f"Relative link escapes the repository root: {raw_target}",
                    path=rel_document,
                    line=line,
                ))
                continue

            if not resolved.exists():
                findings.append(Finding(
                    "LINK_MISSING_TARGET",
                    f"Relative link target does not exist: {raw_target}",
                    path=rel_document,
                    line=line,
                ))
                continue

            if args.check_anchors and anchor:
                anchor_document = resolved
                if resolved.is_dir():
                    anchor_document = resolved / "README.md"
                if anchor_document.suffix.lower() == ".md" and anchor_document.is_file():
                    if anchor_document not in anchor_cache:
                        anchor_cache[anchor_document] = anchors_for(anchor_document)
                    normalized = github_slug(anchor)
                    if normalized not in anchor_cache[anchor_document]:
                        findings.append(Finding(
                            "LINK_MISSING_ANCHOR",
                            f"Heading anchor does not exist: {raw_target}",
                            path=rel_document,
                            line=line,
                        ))

    return ToolResult.from_findings(
        tool=TOOL,
        version=VERSION,
        findings=findings,
        summary={
            "markdownDocuments": len(documents),
            "linksChecked": checked,
            "findings": len(findings),
            "anchorChecking": args.check_anchors,
        },
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    add_common_arguments(parser, default_root=DEFAULT_ROOT)
    parser.add_argument(
        "--no-check-anchors",
        dest="check_anchors",
        action="store_false",
        help="Check target existence but skip local Markdown anchor validation.",
    )
    parser.set_defaults(check_anchors=True)
    parser.add_argument("--debug", action="store_true", help=argparse.SUPPRESS)
    return parser


def main(argv: list[str] | None = None) -> int:
    return execute_tool(tool=TOOL, version=VERSION, parser=build_parser(), run=run, argv=argv)


if __name__ == "__main__":
    raise SystemExit(main())
