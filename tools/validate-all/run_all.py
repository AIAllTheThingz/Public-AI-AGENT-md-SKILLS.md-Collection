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

COMPATIBILITY_HISTORY_BUNDLE = Path("releases/compatibility/rc-history.bundle")
COMPATIBILITY_HISTORY_REFS = {
    "83c73f3ab9a049ff2321d463164fcf98fb453a9c": "refs/heads/compat-v010",
    "2f6d39288e5c1a7d416e62cd75651b3d6da48dfe": "refs/heads/compat-csharp",
    "a96d6a92da40257cbe4c6e0fe0c7bbbd397adef3": "refs/heads/compat-helper",
}

_HISTORY_REAL_GIT = "PAG_COMPATIBILITY_REAL_GIT"
_HISTORY_SOURCE_ROOT = "PAG_COMPATIBILITY_SOURCE_ROOT"
_HISTORY_GIT_DIR = "PAG_COMPATIBILITY_GIT_DIR"
_HISTORY_SELECTORS = "PAG_COMPATIBILITY_SELECTORS"


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


def _populate_temporary_head(
    git_dir: Path,
    root: Path,
    real_git: str,
) -> None:
    """Create an external ephemeral HEAD representing a no-Git source tree."""
    index_file = git_dir.parent / "validation-index"
    env = os.environ.copy()
    env["GIT_INDEX_FILE"] = str(index_file)

    added = subprocess.run(
        [
            real_git,
            f"--git-dir={git_dir}",
            f"--work-tree={root}",
            "add",
            "-A",
            "--",
            ".",
        ],
        cwd=root,
        text=True,
        capture_output=True,
        check=False,
        env=env,
    )
    if added.returncode != 0:
        raise RuntimeError(added.stderr.strip() or "temporary source-tree staging failed")

    tree = subprocess.run(
        [real_git, f"--git-dir={git_dir}", "write-tree"],
        text=True,
        capture_output=True,
        check=False,
        env=env,
    )
    if tree.returncode != 0:
        raise RuntimeError(tree.stderr.strip() or "temporary source tree creation failed")
    tree_sha = tree.stdout.strip()

    commit_env = env.copy()
    commit_env.update(
        {
            "GIT_AUTHOR_NAME": "Public AI Governance Validation",
            "GIT_AUTHOR_EMAIL": "validation@example.invalid",
            "GIT_COMMITTER_NAME": "Public AI Governance Validation",
            "GIT_COMMITTER_EMAIL": "validation@example.invalid",
            "GIT_AUTHOR_DATE": "2000-01-01T00:00:00+00:00",
            "GIT_COMMITTER_DATE": "2000-01-01T00:00:00+00:00",
        }
    )
    committed = subprocess.run(
        [
            real_git,
            f"--git-dir={git_dir}",
            "commit-tree",
            tree_sha,
            "-m",
            "temporary distributed-source validation tree",
        ],
        text=True,
        capture_output=True,
        check=False,
        env=commit_env,
    )
    if committed.returncode != 0:
        raise RuntimeError(
            committed.stderr.strip() or "temporary source commit creation failed"
        )
    commit_sha = committed.stdout.strip()

    updated = subprocess.run(
        [
            real_git,
            f"--git-dir={git_dir}",
            "update-ref",
            "refs/heads/current-source",
            commit_sha,
        ],
        text=True,
        capture_output=True,
        check=False,
    )
    if updated.returncode != 0:
        raise RuntimeError(
            updated.stderr.strip() or "temporary source HEAD update failed"
        )

    symbolic = subprocess.run(
        [
            real_git,
            f"--git-dir={git_dir}",
            "symbolic-ref",
            "HEAD",
            "refs/heads/current-source",
        ],
        text=True,
        capture_output=True,
        check=False,
    )
    if symbolic.returncode != 0:
        raise RuntimeError(
            symbolic.stderr.strip() or "temporary source HEAD selection failed"
        )


def _write_history_git_wrapper(path: Path) -> None:
    """Write POSIX and Windows Git shims for immutable compatibility lookups."""
    path.write_text(
        r'''#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

real_git = os.environ["PAG_COMPATIBILITY_REAL_GIT"]
source_root = Path(os.environ["PAG_COMPATIBILITY_SOURCE_ROOT"]).resolve()
history_git_dir = Path(os.environ["PAG_COMPATIBILITY_GIT_DIR"]).resolve()
selectors = tuple(json.loads(os.environ["PAG_COMPATIBILITY_SELECTORS"]))
args = sys.argv[1:]


def inside_source(path: Path) -> bool:
    try:
        path.resolve().relative_to(source_root)
        return True
    except ValueError:
        return False


def command_directory() -> Path:
    current = Path.cwd().resolve()
    index = 0
    while index < len(args):
        if args[index] == "-C" and index + 1 < len(args):
            candidate = Path(args[index + 1])
            current = (
                candidate.resolve()
                if candidate.is_absolute()
                else (current / candidate).resolve()
            )
            index += 2
            continue
        index += 1
    return current


def command_name() -> str | None:
    index = 0
    while index < len(args):
        argument = args[index]
        if argument == "-C" and index + 1 < len(args):
            index += 2
            continue
        if argument == "-c" and index + 1 < len(args):
            index += 2
            continue
        if argument.startswith("-"):
            index += 1
            continue
        return argument
    return None


def has_nested_git_metadata(path: Path) -> bool:
    current = path.resolve()
    while inside_source(current) and current != source_root:
        if (current / ".git").exists():
            return True
        current = current.parent
    return False


def uses_compatibility_history() -> bool:
    return any(selector in argument for argument in args for selector in selectors)


target = command_directory()
source_has_git_metadata = (source_root / ".git").exists()
nested_repository_creation = (
    target != source_root
    and command_name() == "init"
)
if (
    inside_source(target)
    and not nested_repository_creation
    and not has_nested_git_metadata(target)
    and (uses_compatibility_history() or not source_has_git_metadata)
):
    args = [
        f"--git-dir={history_git_dir}",
        f"--work-tree={source_root}",
        *args,
    ]

os.execv(real_git, [real_git, *args])
''',
        encoding="utf-8",
    )
    path.chmod(0o755)

    # Windows command lookup does not execute an extensionless script from PATH.
    # Keep the Python shim as the single implementation and add a .cmd launcher
    # so subprocess calls to `git` resolve through PATHEXT before reaching git.exe.
    path.with_suffix(".cmd").write_text(
        f'@echo off\r\n"{sys.executable}" "%~dp0{path.name}" %*\r\n',
        encoding="utf-8",
    )


@contextmanager
def compatibility_history(root: Path):
    """Expose authenticated RC baselines without mutating the declared source root."""
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

    # History-deficient inputs include both extracted archives and shallow Git
    # checkouts. Always keep bootstrap objects/refs in a temporary external store;
    # never fetch them into the user's existing repository. In a source archive,
    # the same external store also receives an ephemeral HEAD representing the
    # extracted tree so ordinary HEAD:<path> compatibility checks remain usable.
    # Nested fixture repositories continue to use their own Git metadata.
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
        if not (root / ".git").exists():
            _populate_temporary_head(git_dir, root, real_git)

        wrapper_dir = temp_root / "bin"
        wrapper_dir.mkdir()
        _write_history_git_wrapper(wrapper_dir / "git")

        managed = (
            "PATH",
            _HISTORY_REAL_GIT,
            _HISTORY_SOURCE_ROOT,
            _HISTORY_GIT_DIR,
            _HISTORY_SELECTORS,
        )
        previous = {name: os.environ.get(name) for name in managed}
        os.environ[_HISTORY_REAL_GIT] = real_git
        os.environ[_HISTORY_SOURCE_ROOT] = str(root)
        os.environ[_HISTORY_GIT_DIR] = str(git_dir)
        os.environ[_HISTORY_SELECTORS] = json.dumps(
            [*COMPATIBILITY_HISTORY_REFS.keys(), *COMPATIBILITY_HISTORY_REFS.values()]
        )
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
    with python_bytecode_disabled():
        return execute_tool(tool=TOOL, version=VERSION, parser=parser, run=run, argv=argv)


if __name__ == "__main__":
    raise SystemExit(main())
