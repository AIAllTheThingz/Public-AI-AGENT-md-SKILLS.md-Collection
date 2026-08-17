#!/usr/bin/env python3
"""Run the complete repository validation pipeline and aggregate structured results."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
from contextlib import contextmanager, nullcontext
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

_HISTORY_REAL_GIT = "PAG_COMPATIBILITY_REAL_GIT"
_HISTORY_ARCHIVE_ROOT = "PAG_COMPATIBILITY_ARCHIVE_ROOT"
_HISTORY_GIT_DIR = "PAG_COMPATIBILITY_GIT_DIR"


def _git(
    root: Path,
    *args: str,
    env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(root), *args],
        text=True,
        capture_output=True,
        check=False,
        env=env,
    )


def _required_history_missing(
    root: Path,
    *,
    env: dict[str, str] | None = None,
) -> list[str]:
    return [
        commit
        for commit in COMPATIBILITY_HISTORY_REFS
        if _git(root, "cat-file", "-e", f"{commit}^{{commit}}", env=env).returncode != 0
    ]


def _fetch_compatibility_history(
    root: Path,
    bundle: Path,
    *,
    env: dict[str, str] | None = None,
) -> None:
    refspecs = [f"{ref}:{ref}" for ref in COMPATIBILITY_HISTORY_REFS.values()]
    fetched = _git(root, "fetch", "--quiet", str(bundle), *refspecs, env=env)
    if fetched.returncode != 0:
        raise RuntimeError(fetched.stderr.strip() or "git bundle fetch failed")

    unresolved = _required_history_missing(root, env=env)
    if unresolved:
        raise RuntimeError(
            "Bundled compatibility history did not provide required commits: "
            + ", ".join(unresolved)
        )


def _populate_temporary_history(
    git_dir: Path,
    bundle: Path,
    real_git: str,
) -> None:
    refspecs = [f"{ref}:{ref}" for ref in COMPATIBILITY_HISTORY_REFS.values()]
    fetched = subprocess.run(
        [real_git, f"--git-dir={git_dir}", "fetch", "--quiet", str(bundle), *refspecs],
        text=True,
        capture_output=True,
        check=False,
    )
    if fetched.returncode != 0:
        raise RuntimeError(fetched.stderr.strip() or "git bundle fetch failed")

    unresolved = []
    for commit in COMPATIBILITY_HISTORY_REFS:
        completed = subprocess.run(
            [real_git, f"--git-dir={git_dir}", "cat-file", "-e", f"{commit}^{{commit}}"],
            text=True,
            capture_output=True,
            check=False,
        )
        if completed.returncode != 0:
            unresolved.append(commit)
    if unresolved:
        raise RuntimeError(
            "Bundled compatibility history did not provide required commits: "
            + ", ".join(unresolved)
        )


def _write_history_git_wrapper(path: Path) -> None:
    """Write a Git shim that redirects only archive-root Git discovery."""
    path.write_text(
        '''#!/usr/bin/env python3
from __future__ import annotations

import os
import sys
from pathlib import Path

real_git = os.environ["PAG_COMPATIBILITY_REAL_GIT"]
archive_root = Path(os.environ["PAG_COMPATIBILITY_ARCHIVE_ROOT"]).resolve()
history_git_dir = Path(os.environ["PAG_COMPATIBILITY_GIT_DIR"]).resolve()
args = sys.argv[1:]


def inside_archive(path: Path) -> bool:
    try:
        path.resolve().relative_to(archive_root)
        return True
    except ValueError:
        return False


def has_local_git_metadata(path: Path) -> bool:
    current = path.resolve()
    while inside_archive(current):
        if (current / ".git").exists():
            return True
        if current == archive_root:
            break
        current = current.parent
    return False


def should_redirect() -> bool:
    if args and args[0] in {"init", "clone"}:
        return False
    if "-C" in args:
        index = args.index("-C")
        if index + 1 >= len(args):
            return False
        target = Path(args[index + 1]).resolve()
        return inside_archive(target) and not has_local_git_metadata(target)
    current = Path.cwd().resolve()
    return inside_archive(current) and not has_local_git_metadata(current)


if should_redirect():
    args = [f"--git-dir={history_git_dir}", f"--work-tree={archive_root}", *args]

os.execv(real_git, [real_git, *args])
''',
        encoding="utf-8",
    )
    path.chmod(0o755)


@contextmanager
def compatibility_history(root: Path):
    """Expose authenticated RC baselines without mutating extracted source trees."""
    root = root.resolve()
    missing = _required_history_missing(root)
    if not missing:
        yield
        return

    bundle = root / COMPATIBILITY_HISTORY_BUNDLE
    if not bundle.is_file():
        raise RuntimeError(
            f"Compatibility history is unavailable and bundled baseline is missing: {bundle}"
        )

    if (root / ".git").exists():
        _fetch_compatibility_history(root, bundle)
        yield
        return

    # Distributed source archives intentionally contain no Git metadata. Build a
    # temporary object store outside the declared repository root. A scoped Git
    # shim redirects only commands aimed at this archive root to that store; Git
    # commands for temporary fixture repositories continue to use normal discovery.
    with tempfile.TemporaryDirectory(prefix="public-ai-governance-history-") as temp:
        temp_root = Path(temp)
        git_dir = temp_root / "repository.git"
        real_git = os.environ.get(_HISTORY_REAL_GIT) or shutil.which("git")
        if not real_git:
            raise RuntimeError("git executable is required for compatibility validation")

        initialized = subprocess.run(
            [real_git, "init", "--bare", "--quiet", str(git_dir)],
            text=True,
            capture_output=True,
            check=False,
        )
        if initialized.returncode != 0:
            raise RuntimeError(initialized.stderr.strip() or "temporary git init failed")
        _populate_temporary_history(git_dir, bundle, real_git)

        wrapper_dir = temp_root / "bin"
        wrapper_dir.mkdir()
        _write_history_git_wrapper(wrapper_dir / "git")

        managed = (
            "PATH",
            _HISTORY_REAL_GIT,
            _HISTORY_ARCHIVE_ROOT,
            _HISTORY_GIT_DIR,
        )
        previous = {name: os.environ.get(name) for name in managed}
        os.environ[_HISTORY_REAL_GIT] = real_git
        os.environ[_HISTORY_ARCHIVE_ROOT] = str(root)
        os.environ[_HISTORY_GIT_DIR] = str(git_dir)
        os.environ["PATH"] = str(wrapper_dir) + os.pathsep + (previous["PATH"] or "")
        try:
            yield
        finally:
            for name, value in previous.items():
                if value is None:
                    os.environ.pop(name, None)
                else:
                    os.environ[name] = value


def run(args: argparse.Namespace) -> ToolResult:
    root = args.root.resolve()
    history = compatibility_history(root) if args.include_tests else nullcontext()

    with history:
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
