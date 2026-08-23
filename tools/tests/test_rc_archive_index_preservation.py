from __future__ import annotations

import importlib.util
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from helpers import REPO_ROOT


RUN_ALL_PATH = REPO_ROOT / "tools" / "validate-all" / "run_all.py"


def _load_run_all_module():
    spec = importlib.util.spec_from_file_location("rc_validate_all_archive_index", RUN_ALL_PATH)
    if spec is None or spec.loader is None:
        raise AssertionError("unable to load validate-all module")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class ReleaseCandidateArchiveIndexPreservationTests(unittest.TestCase):
    def test_temporary_head_keeps_default_index_for_routed_git_commands(self) -> None:
        real_git = shutil.which("git")
        if real_git is None:
            self.skipTest("git executable is required")

        run_all = _load_run_all_module()

        with tempfile.TemporaryDirectory(prefix="rc-archive-index-") as temp:
            root = Path(temp) / "source"
            git_dir = Path(temp) / "history.git"
            root.mkdir()
            # The archive can contain a file that is ignored by the current
            # source rules because git archive exports tracked files regardless
            # of whether the same path pattern is ignored today. Reconstructing
            # tracked state must therefore force-stage the distributed bytes.
            (root / ".gitignore").write_text("*.pyc\n", encoding="utf-8")
            (root / "committed.pyc").write_bytes(b"published-bytecode-fixture")
            (root / "ordinary.txt").write_text("tracked\n", encoding="utf-8")
            long_name = "z" * 252 + ".py"
            (root / long_name).write_text("long tracked path\n", encoding="utf-8")

            initialized = subprocess.run(
                [real_git, "init", "--bare", "--quiet", str(git_dir)],
                text=True,
                encoding="utf-8",
                capture_output=True,
                check=False,
            )
            self.assertEqual(initialized.returncode, 0, initialized.stderr)

            run_all._populate_temporary_head(git_dir, root, real_git)

            listed = subprocess.run(
                [
                    real_git,
                    f"--git-dir={git_dir}",
                    f"--work-tree={root}",
                    "ls-files",
                ],
                cwd=root,
                text=True,
                encoding="utf-8",
                capture_output=True,
                check=False,
            )
            self.assertEqual(listed.returncode, 0, listed.stderr)
            tracked = listed.stdout.splitlines()
            self.assertIn(".gitignore", tracked)
            self.assertIn("committed.pyc", tracked)
            self.assertIn("ordinary.txt", tracked)
            self.assertIn(long_name, tracked)

            status = subprocess.run(
                [
                    real_git,
                    f"--git-dir={git_dir}",
                    f"--work-tree={root}",
                    "status",
                    "--porcelain",
                ],
                cwd=root,
                text=True,
                encoding="utf-8",
                capture_output=True,
                check=False,
            )
            self.assertEqual(status.returncode, 0, status.stderr)
            self.assertEqual(status.stdout, "")


if __name__ == "__main__":
    unittest.main()
