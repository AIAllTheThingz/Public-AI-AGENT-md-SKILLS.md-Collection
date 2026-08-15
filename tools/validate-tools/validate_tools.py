#!/usr/bin/env python3
"""Validate tool package structure, executable entry points, contracts, dependencies, workflows, and tests."""

from __future__ import annotations

import argparse
import json
import py_compile
import re
import subprocess
import sys
from pathlib import Path

TOOLS_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TOOLS_ROOT / "lib"))

from standards_tools import Finding, ToolResult, add_common_arguments, execute_tool  # noqa: E402

TOOL = "validate-tools"
VERSION = "1.3.1"
DEFAULT_ROOT = Path(__file__).resolve().parents[2]
TOOL_PACKAGES = {
    "validate-standards": "validate_repository.py",
    "check-links": "check_links.py",
    "validate-skills": "validate_skills.py",
    "validate-schemas": "validate_schemas.py",
    "validate-templates": "validate_templates.py",
    "validate-tools": "validate_tools.py",
    "generate-manifest": "generate_manifest.py",
    "compose-agents": "compose_agents.py",
    "validate-all": "run_all.py",
    "release": "validate_release.py",
}
REQUIRED_COLLECTION = [
    "AGENTS.md", "README.md", "MANIFEST.md", "TOOL_CATALOG.md", "TOOL_CONTRACT.md",
    "DEVELOPMENT_GUIDE.md", "TESTING_GUIDE.md", "SECURITY_BOUNDARIES.md",
    "RELEASE_AND_COMPATIBILITY.md", "TROUBLESHOOTING.md",
]
FRONTMATTER_ID = re.compile(r"^id:\s*(\S+)\s*$", re.MULTILINE)
WORKFLOW_USE = re.compile(r"^\s*-?\s*uses:\s*(.+?)\s*$")
WORKFLOW_RUNNER = re.compile(r"^\s*runs-on:\s*(.+?)\s*$")
FULL_SHA = re.compile(r"^[A-Fa-f0-9]{40}$")


def rel(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix()


def normalize_requirement(value: str) -> str:
    """Normalize one requirement declaration for exact input/lock comparison."""
    cleaned = value.strip()
    if cleaned.endswith("\\"):
        cleaned = cleaned[:-1].rstrip()
    return re.sub(r"\s+", "", cleaned).casefold()


def locked_requirement_specs(lock_text: str) -> set[str]:
    """Return top-level resolved requirement declarations from a pip-compile lock."""
    specs: set[str] = set()
    for line in lock_text.splitlines():
        if not line or line[0].isspace():
            continue
        stripped = line.strip()
        if not stripped or stripped.startswith(("#", "-")):
            continue
        specs.add(normalize_requirement(stripped))
    return specs


def yaml_scalar_value(raw: str) -> str:
    """Extract a simple YAML scalar while accepting ordinary single/double quoting."""
    value = raw.strip()
    if not value:
        return value
    if value[0] in {"'", '"'}:
        quote = value[0]
        end = value.find(quote, 1)
        if end == -1:
            return value
        return value[1:end].strip()
    return value.split(" #", 1)[0].strip()


def validate_dependency_lock(root: Path, findings: list[Finding]) -> None:
    direct = root / "tools" / "validate-schemas" / "requirements.txt"
    lock = root / "tools" / "validate-schemas" / "requirements.lock"

    if not direct.is_file():
        findings.append(Finding(
            "DEPENDENCY_INPUT_MISSING",
            "Direct validation dependency file is missing.",
            path=rel(direct, root),
        ))
        return
    if not lock.is_file():
        findings.append(Finding(
            "DEPENDENCY_LOCK_MISSING",
            "Hash-locked validation dependency file is missing.",
            path=rel(lock, root),
        ))
        return

    direct_specs = [
        line.strip()
        for line in direct.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.lstrip().startswith(("#", "-"))
    ]
    lock_text = lock.read_text(encoding="utf-8")
    resolved_specs = locked_requirement_specs(lock_text)

    if "--hash=sha256:" not in lock_text:
        findings.append(Finding(
            "DEPENDENCY_LOCK_UNHASHED",
            "requirements.lock must contain SHA-256 hashes for resolved dependencies.",
            path=rel(lock, root),
        ))

    for spec in direct_specs:
        if normalize_requirement(spec) not in resolved_specs:
            findings.append(Finding(
                "DEPENDENCY_LOCK_OUT_OF_SYNC",
                f"Direct dependency is not represented exactly in requirements.lock: {spec}",
                path=rel(lock, root),
            ))


def validate_workflow_pins(root: Path, findings: list[Finding]) -> None:
    workflows = root / ".github" / "workflows"
    if not workflows.is_dir():
        return

    for path in sorted(list(workflows.glob("*.yml")) + list(workflows.glob("*.yaml"))):
        for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
            use = WORKFLOW_USE.match(line)
            if use:
                value = yaml_scalar_value(use.group(1))
                if "@" not in value:
                    findings.append(Finding(
                        "WORKFLOW_ACTION_NOT_PINNED",
                        f"Third-party action reference is missing an immutable commit SHA: {value}",
                        path=rel(path, root),
                        line=line_number,
                    ))
                else:
                    action, ref = value.rsplit("@", 1)
                    if action.startswith("./"):
                        continue
                    if not FULL_SHA.fullmatch(ref):
                        findings.append(Finding(
                            "WORKFLOW_ACTION_NOT_PINNED",
                            f"Third-party action must be pinned to a full 40-character commit SHA: {action}@{ref}",
                            path=rel(path, root),
                            line=line_number,
                        ))

            runner = WORKFLOW_RUNNER.match(line)
            if runner:
                value = yaml_scalar_value(runner.group(1))
                if "${{" not in value and value.endswith("-latest"):
                    findings.append(Finding(
                        "WORKFLOW_RUNNER_FLOATING",
                        f"Hosted runner must use an explicit image family rather than {value}.",
                        path=rel(path, root),
                        line=line_number,
                    ))


def run(args: argparse.Namespace) -> ToolResult:
    root = args.root.resolve()
    tools = root / "tools"
    findings: list[Finding] = []
    ids: dict[str, Path] = {}

    for name in REQUIRED_COLLECTION:
        path = tools / name
        if not path.is_file():
            findings.append(Finding("TOOL_COLLECTION_FILE_MISSING", "Missing tools collection file.", path=rel(path, root)))

    for path in sorted(tools.rglob("*.md")):
        text = path.read_text(encoding="utf-8")
        match = FRONTMATTER_ID.search(text)
        if not match:
            findings.append(Finding("TOOL_DOC_ID_MISSING", "Tool Markdown document lacks front-matter ID.", path=rel(path, root)))
            continue
        document_id = match.group(1)
        if document_id in ids:
            findings.append(Finding(
                "TOOL_DOC_ID_DUPLICATE",
                f"ID also used by {rel(ids[document_id], root)}: {document_id}",
                path=rel(path, root),
            ))
        else:
            ids[document_id] = path

    for slug, script_name in TOOL_PACKAGES.items():
        package = tools / slug
        script = package / script_name
        for path in (package / "README.md", package / "MANIFEST.md", package / "examples" / "README.md", script):
            if not path.is_file():
                findings.append(Finding("TOOL_PACKAGE_FILE_MISSING", "Missing tool package file.", path=rel(path, root)))
        if (package / "README.md").is_file():
            readme_text = (package / "README.md").read_text(encoding="utf-8")
            if len(readme_text.splitlines()) < args.minimum_readme_lines:
                findings.append(Finding("TOOL_README_THIN", f"README has fewer than {args.minimum_readme_lines} lines.", path=rel(package / "README.md", root)))
            if "planned tool" in readme_text.lower():
                findings.append(Finding("TOOL_STILL_PLANNED", "Tool README still describes the package as planned.", path=rel(package / "README.md", root)))
        if script.is_file():
            text = script.read_text(encoding="utf-8")
            if not text.startswith("#!/usr/bin/env python3"):
                findings.append(Finding("TOOL_SHEBANG", "Python entry point lacks the standard shebang.", path=rel(script, root)))

        for python_file in sorted(package.glob("*.py")):
            try:
                py_compile.compile(str(python_file), doraise=True)
            except py_compile.PyCompileError as exc:
                findings.append(Finding("TOOL_COMPILE", str(exc), path=rel(python_file, root)))

    validate_dependency_lock(root, findings)
    validate_workflow_pins(root, findings)

    tests = sorted((tools / "tests").glob("test_*.py"))
    if len(tests) < len(TOOL_PACKAGES):
        findings.append(Finding(
            "TOOL_TEST_COVERAGE",
            f"Expected at least {len(TOOL_PACKAGES)} test modules; found {len(tests)}.",
            path="tools/tests",
        ))

    contract = tools / "contracts" / "tool-result.schema.json"
    try:
        json.loads(contract.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError) as exc:
        findings.append(Finding("TOOL_CONTRACT_INVALID", str(exc), path=rel(contract, root)))

    if args.run_unit_tests:
        completed = subprocess.run(
            [sys.executable, "-m", "unittest", "discover", "-s", str(tools / "tests"), "-p", "test_*.py"],
            cwd=root,
            text=True,
            capture_output=True,
            check=False,
        )
        if completed.returncode != 0:
            findings.append(Finding(
                "TOOL_TESTS_FAILED",
                "Tool unit tests failed.",
                path="tools/tests",
                details={"stdout": completed.stdout[-4000:], "stderr": completed.stderr[-4000:]},
            ))

    return ToolResult.from_findings(
        tool=TOOL,
        version=VERSION,
        findings=findings,
        summary={
            "toolPackages": len(TOOL_PACKAGES),
            "identifiedDocuments": len(ids),
            "testModules": len(tests),
            "unitTestsRun": args.run_unit_tests,
            "dependencyLockPresent": (root / "tools" / "validate-schemas" / "requirements.lock").is_file(),
            "workflowPinningChecked": True,
            "findings": len(findings),
        },
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    add_common_arguments(parser, default_root=DEFAULT_ROOT)
    parser.add_argument("--minimum-readme-lines", type=int, default=100)
    parser.add_argument("--run-unit-tests", action="store_true")
    parser.add_argument("--debug", action="store_true", help=argparse.SUPPRESS)
    return parser


def main(argv: list[str] | None = None) -> int:
    return execute_tool(tool=TOOL, version=VERSION, parser=build_parser(), run=run, argv=argv)


if __name__ == "__main__":
    raise SystemExit(main())
