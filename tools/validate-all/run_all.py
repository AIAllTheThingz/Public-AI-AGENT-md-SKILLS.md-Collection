#!/usr/bin/env python3
"""Run the complete repository validation pipeline and aggregate structured results."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
from contextlib import contextmanager
from pathlib import Path

TOOLS_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TOOLS_ROOT / "lib"))

_previous_dont_write_bytecode = sys.dont_write_bytecode
sys.dont_write_bytecode = True
try:
    from standards_tools import Finding, ToolResult, add_common_arguments, execute_tool  # noqa: E402
finally:
    sys.dont_write_bytecode = _previous_dont_write_bytecode

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


@contextmanager
def python_bytecode_disabled():
    """Keep validation bytecode out of the declared source tree."""
    previous_environment = {
        "PYTHONDONTWRITEBYTECODE": os.environ.get("PYTHONDONTWRITEBYTECODE"),
        "PYTHONPYCACHEPREFIX": os.environ.get("PYTHONPYCACHEPREFIX"),
    }
    previous_runtime = sys.dont_write_bytecode
    previous_pycache_prefix = sys.pycache_prefix

    # PYTHONDONTWRITEBYTECODE prevents ordinary imports from caching bytecode.
    # The external cache prefix is a second containment boundary for code that
    # deliberately re-enables bytecode writes (for example an import probe in a
    # test).  Both the current interpreter and child interpreters are covered,
    # while the caller's settings are restored on exit.
    with tempfile.TemporaryDirectory(prefix="public-ai-governance-pycache-") as pycache:
        os.environ["PYTHONDONTWRITEBYTECODE"] = "1"
        os.environ["PYTHONPYCACHEPREFIX"] = pycache
        sys.dont_write_bytecode = True
        sys.pycache_prefix = pycache
        try:
            yield
        finally:
            sys.dont_write_bytecode = previous_runtime
            sys.pycache_prefix = previous_pycache_prefix
            for name, value in previous_environment.items():
                if value is None:
                    os.environ.pop(name, None)
                else:
                    os.environ[name] = value


def run(args: argparse.Namespace) -> ToolResult:
    root = args.root.resolve()
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
    if parser.parse_known_args(argv)[0].list_tools:
        print("\n".join(VALIDATORS))
        return 0
    with python_bytecode_disabled():
        return execute_tool(tool=TOOL, version=VERSION, parser=parser, run=run, argv=argv)


if __name__ == "__main__":
    raise SystemExit(main())
