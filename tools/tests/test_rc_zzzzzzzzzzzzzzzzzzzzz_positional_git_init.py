from __future__ import annotations

import subprocess
import tempfile
import unittest
from pathlib import Path

from test_rc_zzzzzzzzzzzzzz_archive_head_history import (
    _load_run_all_module,
    _prepare_archive_root,
)
import test_rc_zzzzzzzzzzzzzzzzzzzz_post_emission_sink_and_codeowners as _latest_contracts  # noqa: F401


class ReleaseCandidatePositionalGitInitTests(unittest.TestCase):
    def test_archive_history_allows_positional_nested_repository_initialization(self) -> None:
        run_all = _load_run_all_module()

        with tempfile.TemporaryDirectory(prefix="rc-archive-positional-git-") as temp:
            root = Path(temp)
            _prepare_archive_root(root, run_all)
            fixture = root / "fixture"

            self.assertFalse((root / ".git").exists())
            self.assertFalse((fixture / ".git").exists())

            with run_all.compatibility_history(root):
                initialized = subprocess.run(
                    ["git", "init", "--quiet", str(fixture)],
                    cwd=root,
                    text=True,
                    capture_output=True,
                    check=False,
                )
                self.assertEqual(initialized.returncode, 0, initialized.stderr)
                self.assertTrue((fixture / ".git").exists())
                self.assertFalse((root / ".git").exists())

                top_level = subprocess.run(
                    ["git", "-C", str(fixture), "rev-parse", "--show-toplevel"],
                    text=True,
                    capture_output=True,
                    check=False,
                )
                self.assertEqual(top_level.returncode, 0, top_level.stderr)
                self.assertEqual(Path(top_level.stdout.strip()).resolve(), fixture.resolve())

                # The archive's temporary compatibility HEAD must remain usable
                # and isolated after the nested repository is initialized.
                archive_head = subprocess.run(
                    [
                        "git",
                        "-C",
                        str(root),
                        "rev-parse",
                        "HEAD:languages/csharp/standards",
                    ],
                    text=True,
                    capture_output=True,
                    check=False,
                )
                self.assertEqual(archive_head.returncode, 0, archive_head.stderr)
                self.assertRegex(archive_head.stdout.strip(), r"^[0-9a-f]{40}$")
                self.assertFalse((root / ".git").exists())

            self.assertTrue((fixture / ".git").exists())
            self.assertFalse((root / ".git").exists())

    def test_archive_root_init_without_target_still_uses_temporary_history(self) -> None:
        run_all = _load_run_all_module()

        with tempfile.TemporaryDirectory(prefix="rc-archive-root-git-") as temp:
            root = Path(temp)
            _prepare_archive_root(root, run_all)

            with run_all.compatibility_history(root):
                initialized = subprocess.run(
                    ["git", "init", "--quiet"],
                    cwd=root,
                    text=True,
                    capture_output=True,
                    check=False,
                )
                self.assertEqual(initialized.returncode, 0, initialized.stderr)
                self.assertFalse(
                    (root / ".git").exists(),
                    "validation must not create Git metadata in the archive root",
                )


if __name__ == "__main__":
    unittest.main()
