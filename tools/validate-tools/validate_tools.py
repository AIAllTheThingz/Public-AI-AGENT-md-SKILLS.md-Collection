#!/usr/bin/env python3
"""Validate tool package structure, executable entry points, contracts, dependencies, workflows, and tests."""

from __future__ import annotations

import argparse
import json
import py_compile
import re
import subprocess
import sys
from itertools import product
from pathlib import Path
from typing import Any, Iterable

TOOLS_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TOOLS_ROOT / "lib"))

from standards_tools import Finding, ToolResult, add_common_arguments, execute_tool  # noqa: E402

TOOL = "validate-tools"
VERSION = "1.3.2"
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
FULL_SHA = re.compile(r"^[A-Fa-f0-9]{40}$")
OCI_SHA256 = re.compile(r"^sha256:[A-Fa-f0-9]{64}$")
LOCK_SHA256 = re.compile(r"--hash=sha256:([A-Fa-f0-9]{64})(?=\s|\\|$)")
MATRIX_RUNNER_EXPRESSION = re.compile(r"^\$\{\{\s*matrix\.([A-Za-z_][A-Za-z0-9_-]*)\s*\}\}$")
DIRECT_REQUIREMENTS_PATH = "tools/validate-schemas/requirements.txt"


def rel(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix()


def require_yaml() -> Any:
    """Load PyYAML inside the CLI boundary so missing dependencies follow the tool contract."""
    try:
        import yaml
    except ModuleNotFoundError as exc:
        if exc.name != "yaml":
            raise
        raise FileNotFoundError(
            "Required dependency PyYAML is not installed. Install the hash-locked validation dependencies before running validation."
        ) from exc
    return yaml


def strip_requirement_comment(value: str) -> str:
    """Remove a PEP 508 requirements-file inline comment introduced by whitespace."""
    return re.split(r"\s+#", value, maxsplit=1)[0].strip()


def normalize_requirement(value: str) -> str:
    """Normalize one requirement declaration for exact input/lock comparison."""
    cleaned = strip_requirement_comment(value)
    if cleaned.endswith("\\"):
        cleaned = cleaned[:-1].rstrip()
    return re.sub(r"\s+", "", cleaned).casefold()


def locked_direct_requirement_specs(lock_text: str) -> set[str]:
    """Return lock entries annotated by pip-compile as direct requirements."""
    direct_specs: set[str] = set()
    current_spec: str | None = None

    for line in lock_text.splitlines():
        if line and not line[0].isspace():
            stripped = line.strip()
            if not stripped or stripped.startswith(("#", "-")):
                current_spec = None
                continue
            current_spec = normalize_requirement(stripped)
            continue

        stripped = line.strip()
        if (
            current_spec
            and stripped.startswith("#")
            and f"-r {DIRECT_REQUIREMENTS_PATH}" in stripped
        ):
            direct_specs.add(current_spec)

    return direct_specs


def locked_requirement_hashes(lock_text: str) -> list[tuple[str, set[str]]]:
    """Return every resolved lock requirement with its valid SHA-256 hashes."""
    requirements: list[tuple[str, set[str]]] = []
    current_spec: str | None = None
    current_hashes: set[str] = set()

    for line in lock_text.splitlines():
        if line and not line[0].isspace():
            if current_spec is not None:
                requirements.append((current_spec, current_hashes))

            stripped = line.strip()
            if not stripped or stripped.startswith(("#", "-")):
                current_spec = None
                current_hashes = set()
                continue

            current_spec = normalize_requirement(stripped)
            current_hashes = {match.casefold() for match in LOCK_SHA256.findall(line)}
            continue

        if current_spec is not None:
            current_hashes.update(match.casefold() for match in LOCK_SHA256.findall(line))

    if current_spec is not None:
        requirements.append((current_spec, current_hashes))

    return requirements


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

    direct_specs = {
        normalize_requirement(line)
        for line in direct.read_text(encoding="utf-8").splitlines()
        if strip_requirement_comment(line) and not line.lstrip().startswith("#")
    }
    direct_specs.discard("")
    lock_text = lock.read_text(encoding="utf-8")
    locked_direct_specs = locked_direct_requirement_specs(lock_text)

    for spec, hashes in locked_requirement_hashes(lock_text):
        if not hashes:
            findings.append(Finding(
                "DEPENDENCY_LOCK_UNHASHED",
                f"Resolved dependency must include at least one valid SHA-256 hash: {spec}",
                path=rel(lock, root),
            ))

    for spec in sorted(direct_specs - locked_direct_specs):
        findings.append(Finding(
            "DEPENDENCY_LOCK_OUT_OF_SYNC",
            f"Direct dependency is not represented exactly in requirements.lock: {spec}",
            path=rel(lock, root),
        ))

    for spec in sorted(locked_direct_specs - direct_specs):
        findings.append(Finding(
            "DEPENDENCY_LOCK_OUT_OF_SYNC",
            f"requirements.lock still marks a dependency as direct that is absent from requirements.txt: {spec}",
            path=rel(lock, root),
        ))


def iter_scalar_strings(value: Any) -> Iterable[str]:
    """Yield scalar strings from a string/list/mapping value."""
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for child in value.values():
            yield from iter_scalar_strings(child)
    elif isinstance(value, list):
        for child in value:
            yield from iter_scalar_strings(child)


def iter_workflow_action_references(document: Any) -> Iterable[Any]:
    """Yield only semantic GitHub Actions/reusable-workflow uses values."""
    if not isinstance(document, dict):
        return

    jobs = document.get("jobs")
    if not isinstance(jobs, dict):
        return

    for job in jobs.values():
        if not isinstance(job, dict):
            continue

        if "uses" in job:
            yield job["uses"]

        steps = job.get("steps")
        if not isinstance(steps, list):
            continue
        for step in steps:
            if isinstance(step, dict) and "uses" in step:
                yield step["uses"]


def iter_workflow_runner_references(document: Any) -> Iterable[tuple[Any, Any]]:
    """Yield job runs-on values paired with their statically declared matrix."""
    if not isinstance(document, dict):
        return

    jobs = document.get("jobs")
    if not isinstance(jobs, dict):
        return

    for job in jobs.values():
        if not isinstance(job, dict) or "runs-on" not in job:
            continue

        matrix: Any = None
        strategy = job.get("strategy")
        if isinstance(strategy, dict):
            matrix = strategy.get("matrix")

        yield job["runs-on"], matrix


def load_yaml_document(path: Path, root: Path, findings: list[Finding]) -> Any | None:
    """Load repository YAML and report parse failures through the workflow finding contract."""
    yaml = require_yaml()
    try:
        return yaml.safe_load(path.read_text(encoding="utf-8"))
    except (UnicodeDecodeError, yaml.YAMLError) as exc:
        findings.append(Finding(
            "WORKFLOW_YAML_INVALID",
            f"Workflow or local action metadata is not valid YAML: {exc}",
            path=rel(path, root),
        ))
        return None


def validate_local_action_reference(
    value: str,
    root: Path,
    findings: list[Finding],
    visited_local_actions: set[Path],
) -> None:
    """Follow a referenced local composite action and validate nested uses entries."""
    repository_root = root.resolve()
    action_dir = (repository_root / value[2:]).resolve()
    try:
        action_dir.relative_to(repository_root)
    except ValueError:
        return

    metadata: Path | None = None
    for name in ("action.yml", "action.yaml"):
        candidate = action_dir / name
        if candidate.is_file():
            metadata = candidate
            break
    if metadata is None or metadata in visited_local_actions:
        return

    visited_local_actions.add(metadata)
    document = load_yaml_document(metadata, root, findings)
    if not isinstance(document, dict):
        return

    runs = document.get("runs")
    if not isinstance(runs, dict) or runs.get("using") != "composite":
        return

    steps = runs.get("steps")
    if not isinstance(steps, list):
        return

    for step in steps:
        if isinstance(step, dict) and "uses" in step:
            validate_action_reference(
                step["uses"],
                metadata,
                root,
                findings,
                visited_local_actions,
            )


def validate_action_reference(
    raw: Any,
    path: Path,
    root: Path,
    findings: list[Finding],
    visited_local_actions: set[Path] | None = None,
) -> None:
    if not isinstance(raw, str):
        findings.append(Finding(
            "WORKFLOW_ACTION_INVALID",
            "Workflow uses values must be strings.",
            path=rel(path, root),
        ))
        return

    value = raw.strip()
    if value.startswith("./"):
        validate_local_action_reference(
            value,
            root,
            findings,
            visited_local_actions if visited_local_actions is not None else set(),
        )
        return

    if value.startswith("docker://"):
        _, separator, digest = value.rpartition("@")
        if not separator or not OCI_SHA256.fullmatch(digest):
            findings.append(Finding(
                "WORKFLOW_DOCKER_NOT_PINNED",
                f"Docker action must be pinned to an immutable sha256 OCI digest: {value}",
                path=rel(path, root),
            ))
        return

    action, separator, ref = value.rpartition("@")
    if not separator or not action or not FULL_SHA.fullmatch(ref):
        findings.append(Finding(
            "WORKFLOW_ACTION_NOT_PINNED",
            f"Third-party action must be pinned to a full 40-character commit SHA: {value}",
            path=rel(path, root),
        ))


def validate_runner_literal(value: str, path: Path, root: Path, findings: list[Finding]) -> None:
    stripped = value.strip()
    if "${{" in stripped:
        findings.append(Finding(
            "WORKFLOW_RUNNER_UNRESOLVED",
            f"Runner expression could not be statically resolved for pin validation: {stripped}",
            path=rel(path, root),
        ))
    elif stripped.endswith("-latest"):
        findings.append(Finding(
            "WORKFLOW_RUNNER_FLOATING",
            f"Hosted runner must use an explicit image family rather than {stripped}.",
            path=rel(path, root),
        ))


def static_matrix_combinations(matrix: Any) -> list[dict[str, Any]] | None:
    """Expand statically declared matrix axes and apply partial-match exclusions."""
    if not isinstance(matrix, dict):
        return None

    axes = [
        (name, values)
        for name, values in matrix.items()
        if name not in {"include", "exclude"}
    ]
    if any(not isinstance(values, list) or not values for _, values in axes):
        return None

    if axes:
        names = [name for name, _ in axes]
        combinations = [
            dict(zip(names, values, strict=True))
            for values in product(*(values for _, values in axes))
        ]
    else:
        combinations = [{}]

    excluded = matrix.get("exclude", [])
    if excluded is None:
        excluded = []
    if not isinstance(excluded, list) or any(not isinstance(entry, dict) for entry in excluded):
        return None

    for entry in excluded:
        combinations = [
            combination
            for combination in combinations
            if not all(
                name in combination and combination[name] == expected
                for name, expected in entry.items()
            )
        ]

    return combinations


def matrix_values_for_key(matrix: Any, key: str) -> list[str]:
    """Return effective static values for a matrix key after exclude, then include."""
    combinations = static_matrix_combinations(matrix)
    if combinations is None:
        return []

    values: list[str] = []
    for combination in combinations:
        if key in combination:
            values.extend(iter_scalar_strings(combination[key]))

    include = matrix.get("include")
    if isinstance(include, list):
        for entry in include:
            if isinstance(entry, dict) and key in entry:
                values.extend(iter_scalar_strings(entry[key]))

    return list(dict.fromkeys(values))


def validate_runner_reference(
    raw: Any,
    matrix: Any,
    path: Path,
    root: Path,
    findings: list[Finding],
) -> None:
    for value in iter_scalar_strings(raw):
        stripped = value.strip()
        match = MATRIX_RUNNER_EXPRESSION.fullmatch(stripped)
        if match:
            resolved_values = matrix_values_for_key(matrix, match.group(1))
            if not resolved_values:
                findings.append(Finding(
                    "WORKFLOW_RUNNER_UNRESOLVED",
                    f"Runner matrix expression has no statically declared values: {stripped}",
                    path=rel(path, root),
                ))
                continue
            for resolved in resolved_values:
                validate_runner_literal(resolved, path, root, findings)
            continue

        validate_runner_literal(stripped, path, root, findings)


def validate_workflow_pins(root: Path, findings: list[Finding]) -> None:
    workflows = root / ".github" / "workflows"
    if not workflows.is_dir():
        return

    visited_local_actions: set[Path] = set()
    for path in sorted(list(workflows.glob("*.yml")) + list(workflows.glob("*.yaml"))):
        document = load_yaml_document(path, root, findings)
        if document is None:
            continue

        for action in iter_workflow_action_references(document):
            validate_action_reference(action, path, root, findings, visited_local_actions)
        for runner, matrix in iter_workflow_runner_references(document):
            validate_runner_reference(runner, matrix, path, root, findings)


def run(args: argparse.Namespace) -> ToolResult:
    require_yaml()
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