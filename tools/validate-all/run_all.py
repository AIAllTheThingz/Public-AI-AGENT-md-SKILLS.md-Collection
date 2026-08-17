#!/usr/bin/env python3
"""Run the complete repository validation pipeline and aggregate structured results."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

TOOLS_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TOOLS_ROOT / "lib"))

from standards_tools import Finding, ToolResult, add_common_arguments, execute_tool  # noqa: E402

TOOL = "validate-all"
VERSION = "1.3.0"
DEFAULT_ROOT = Path(__file__).resolve().parents[2]
VALIDATORS = {
    "validate-standards": "tools/validate-standards/validate_repository.py",
    "check-links": "tools/check-links/check_links.py",
    "check-freshness": "tools/check-freshness/check_freshness.py",
    "validate-skills": "tools/validate-skills/validate_skills.py",
    "validate-schemas": "tools/validate-schemas/validate_schemas.py",
    "validate-templates": "tools/validate-templates/validate_templates.py",
    "validate-tools": "tools/validate-tools/validate_tools.py",
    "validate-release": "tools/release/validate_release.py",
}

COMPATIBILITY_HISTORY_BUNDLE = Path("releases/compatibility/rc-history.bundle")
COMPATIBILITY_HISTORY_REFS = {
    "83c73f3ab9a049ff2321d463164fcf98fb453a9c": "refs/heads/compat-v010",
    "2f6d39288e5c1a7d416e62cd75651b3d6da48dfe": "refs/heads/compat-csharp",
    "a96d6a92da40257cbe4c6e0fe0c7bbbd397adef3": "refs/heads/compat-helper",
}


def _git(root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(root), *args],
        text=True,
        capture_output=True,
        check=False,
    )


def ensure_compatibility_history(root: Path) -> None:
    """Make authenticated RC baselines available in shallow clones and archives."""
    root = root.resolve()
    missing = [
        commit
        for commit in COMPATIBILITY_HISTORY_REFS
        if _git(root, "cat-file", "-e", f"{commit}^{{commit}}").returncode != 0
    ]
    if not missing:
        return

    bundle = root / COMPATIBILITY_HISTORY_BUNDLE
    if not bundle.is_file():
        raise RuntimeError(
            f"Compatibility history is unavailable and bundled baseline is missing: {bundle}"
        )

    if not (root / ".git").exists():
        initialized = _git(root, "init", "--quiet")
        if initialized.returncode != 0:
            raise RuntimeError(initialized.stderr.strip() or "git init failed")

    refspecs = [f"{ref}:{ref}" for ref in COMPATIBILITY_HISTORY_REFS.values()]
    fetched = _git(root, "fetch", "--quiet", str(bundle), *refspecs)
    if fetched.returncode != 0:
        raise RuntimeError(fetched.stderr.strip() or "git bundle fetch failed")

    unresolved = [
        commit
        for commit in COMPATIBILITY_HISTORY_REFS
        if _git(root, "cat-file", "-e", f"{commit}^{{commit}}").returncode != 0
    ]
    if unresolved:
        raise RuntimeError(
            "Bundled compatibility history did not provide required commits: "
            + ", ".join(unresolved)
        )


def run(args: argparse.Namespace) -> ToolResult:
    root = args.root.resolve()
    if args.include_tests:
        ensure_compatibility_history(root)
    selected = args.tool or list(VALIDATORS)
    unknown = [name for name in selected if name not in VALIDATORS]
    if unknown:
        raise ValueError(f"Unknown validator(s): {', '.join(unknown)}")

    results: list[dict] = []
    findings: list[Finding] = []
    for name in selected:
        script = root / VALIDATORS[name]
        completed = subprocess.run(
            [sys.executable, str(script), "--root", str(root), "--format", "json"],
            cwd=root,
            text=True,
            capture_output=True,
            check=False,
        )
        try:
            payload = json.loads(completed.stdout)
        except json.JSONDecodeError:
            payload = {
                "tool": name,
                "status": "error",
                "summary": {},
                "findings": [{
                    "code": "AGGREGATE_UNPARSEABLE_RESULT",
                    "severity": "error",
                    "message": "Validator did not emit valid JSON.",
                }],
                "metadata": {"stdout": completed.stdout[-4000:], "stderr": completed.stderr[-4000:]},
            }
        payload["exitCode"] = completed.returncode
        results.append(payload)
        if payload.get("status") != "passed":
            findings.append(Finding(
                "VALIDATOR_FAILED",
                f"{name} returned status {payload.get('status')} and exit code {completed.returncode}.",
                path=VALIDATORS[name],
                details={"result": payload},
            ))
            if args.fail_fast:
                break

    tests_result = None
    if args.include_tests and not (args.fail_fast and findings):
        completed = subprocess.run(
            [sys.executable, "-m", "unittest", "discover", "-s", str(root / "tools" / "tests"), "-p", "test_*.py"],
            cwd=root,
            text=True,
            capture_output=True,
            check=False,
        )
        tests_result = {
            "exitCode": completed.returncode,
            "stdout": completed.stdout[-4000:],
            "stderr": completed.stderr[-4000:],
        }
        if completed.returncode != 0:
            findings.append(Finding("UNIT_TESTS_FAILED", "Tool unit tests failed.", path="tools/tests", details=tests_result))

    return ToolResult.from_findings(
        tool=TOOL,
        version=VERSION,
        findings=findings,
        summary={
            "validatorsRequested": len(selected),
            "validatorsCompleted": len(results),
            "testsIncluded": args.include_tests,
            "findings": len(findings),
        },
        metadata={"results": results, "tests": tests_result},
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    add_common_arguments(parser, default_root=DEFAULT_ROOT)
    parser.add_argument("--tool", action="append", choices=tuple(VALIDATORS), help="Run only the named validator. Repeatable.")
    parser.add_argument("--fail-fast", action="store_true")
    parser.add_argument("--include-tests", action="store_true")
    parser.add_argument("--list", action="store_true", dest="list_tools", help="List validator names and exit.")
    parser.add_argument("--debug", action="store_true", help=argparse.SUPPRESS)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    if argv is not None and "--list" in argv:
        print("\n".join(VALIDATORS))
        return 0
    if argv is None and "--list" in sys.argv[1:]:
        print("\n".join(VALIDATORS))
        return 0
    return execute_tool(tool=TOOL, version=VERSION, parser=parser, run=run, argv=argv)


if __name__ == "__main__":
    raise SystemExit(main())
