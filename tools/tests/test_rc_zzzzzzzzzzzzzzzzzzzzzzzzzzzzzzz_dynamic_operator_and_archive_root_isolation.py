from __future__ import annotations

import ast
import importlib.util
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from helpers import REPO_ROOT
import rc_finding_code_contracts_base as literal_base
import test_rc_zzz_finding_emission_sink as sink_execution
import test_rc_zzzzzzzzzzzzzzzzzzzzzzzzzzz_left_to_right_expression_execution as left_to_right


# Dynamic unary/binary operators may invoke type-specific or user-defined code
# and can fail before a later expression is evaluated. The static evaluator has
# first chance to prove an operation safe (or definitely raising); only an
# unresolved operator is changed from structurally-safe to an execution
# prerequisite here. This preserves harmless literal arithmetic such as 1 + 1.
_PREVIOUS_STRUCTURALLY_SAFE = left_to_right._structurally_safe


def _structurally_safe(node: ast.AST) -> bool:
    if isinstance(node, (ast.UnaryOp, ast.BinOp)):
        return False
    return _PREVIOUS_STRUCTURALLY_SAFE(node)


left_to_right._structurally_safe = _structurally_safe


RUN_ALL_PATH = REPO_ROOT / "tools" / "validate-all" / "run_all.py"


def _load_run_all_module():
    spec = importlib.util.spec_from_file_location(
        "rc_validate_all_parent_root_isolation",
        RUN_ALL_PATH,
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("could not load validate-all module")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _run(real_git: str, cwd: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [real_git, *args],
        cwd=cwd,
        text=True,
        encoding="utf-8",
        capture_output=True,
        check=False,
    )


class ReleaseCandidateDynamicOperatorExecutionTests(unittest.TestCase):
    def test_unknown_binary_operator_is_an_execution_prerequisite(self) -> None:
        direct = '''
def validate(value, findings):
    findings.append(Finding("PUBLIC_CODE", "visible"))
'''
        guarded = '''
def validate(value, findings):
    (value + 1, findings.append(Finding("PUBLIC_CODE", "visible")))
'''
        self.assertNotEqual(
            literal_base.finding_semantic_signatures(direct),
            literal_base.finding_semantic_signatures(guarded),
        )
        self.assertNotEqual(
            sink_execution.finding_semantic_signatures_with_sink(direct),
            sink_execution.finding_semantic_signatures_with_sink(guarded),
        )

    def test_unknown_unary_operator_is_an_execution_prerequisite(self) -> None:
        direct = '''
def validate(value, findings):
    findings.append(Finding("PUBLIC_CODE", "visible"))
'''
        guarded = '''
def validate(value, findings):
    (-value, findings.append(Finding("PUBLIC_CODE", "visible")))
'''
        self.assertNotEqual(
            literal_base.finding_semantic_signatures(direct),
            literal_base.finding_semantic_signatures(guarded),
        )

    def test_statically_safe_literal_operator_does_not_add_noise(self) -> None:
        direct = '''
def validate(findings):
    findings.append(Finding("PUBLIC_CODE", "visible"))
'''
        guarded = '''
def validate(findings):
    (1 + 1, findings.append(Finding("PUBLIC_CODE", "visible")))
'''
        self.assertEqual(
            literal_base.finding_semantic_signatures(direct),
            literal_base.finding_semantic_signatures(guarded),
        )

    def test_statically_raising_operator_hides_later_finding(self) -> None:
        source = '''
def validate(findings):
    (None + 1, findings.append(Finding("PUBLIC_CODE", "hidden")))
'''
        self.assertNotIn(
            "PUBLIC_CODE",
            literal_base.finding_semantic_signatures(source),
        )


class ReleaseCandidateArchiveParentRepositoryIsolationTests(unittest.TestCase):
    def test_archive_root_does_not_inherit_parent_git_repository(self) -> None:
        run_all = _load_run_all_module()
        real_git = os.environ.get(run_all._HISTORY_REAL_GIT) or shutil.which("git")
        self.assertIsNotNone(real_git)
        assert real_git is not None

        with tempfile.TemporaryDirectory(prefix="rc-parent-git-") as temp:
            parent = Path(temp)
            initialized = _run(real_git, parent, "init", "--quiet")
            self.assertEqual(initialized.returncode, 0, initialized.stderr)

            bundle = REPO_ROOT / run_all.COMPATIBILITY_HISTORY_BUNDLE
            for ref in run_all.COMPATIBILITY_HISTORY_REFS.values():
                fetched = _run(
                    real_git,
                    parent,
                    "fetch",
                    "--quiet",
                    str(bundle),
                    f"{ref}:{ref}",
                )
                self.assertEqual(fetched.returncode, 0, fetched.stderr)

            archive = parent / "extracted-source"
            archive.mkdir()
            archive_bundle = archive / run_all.COMPATIBILITY_HISTORY_BUNDLE
            archive_bundle.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(bundle, archive_bundle)
            marker = archive / "ARCHIVE_MARKER.txt"
            marker.write_text("declared archive root\n", encoding="utf-8")

            inherited = _run(real_git, archive, "rev-parse", "--show-toplevel")
            self.assertEqual(inherited.returncode, 0, inherited.stderr)
            self.assertEqual(Path(inherited.stdout.strip()).resolve(), parent.resolve())
            self.assertFalse((archive / ".git").exists())

            with run_all.compatibility_history(archive):
                isolated = subprocess.run(
                    ["git", "-C", str(archive), "rev-parse", "--show-toplevel"],
                    text=True,
                    encoding="utf-8",
                    capture_output=True,
                    check=False,
                )
                self.assertEqual(isolated.returncode, 0, isolated.stderr)
                self.assertEqual(Path(isolated.stdout.strip()).resolve(), archive.resolve())

                head_marker = subprocess.run(
                    [
                        "git",
                        "-C",
                        str(archive),
                        "show",
                        "HEAD:ARCHIVE_MARKER.txt",
                    ],
                    text=True,
                    encoding="utf-8",
                    capture_output=True,
                    check=False,
                )
                self.assertEqual(head_marker.returncode, 0, head_marker.stderr)
                self.assertEqual(head_marker.stdout, "declared archive root\n")
                self.assertFalse((archive / ".git").exists())

            self.assertFalse((archive / ".git").exists())
            parent_top = _run(real_git, parent, "rev-parse", "--show-toplevel")
            self.assertEqual(parent_top.returncode, 0, parent_top.stderr)
            self.assertEqual(Path(parent_top.stdout.strip()).resolve(), parent.resolve())


if __name__ == "__main__":
    unittest.main()
