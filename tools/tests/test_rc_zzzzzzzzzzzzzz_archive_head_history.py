from __future__ import annotations

import importlib.util
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
RUN_ALL_PATH = REPO_ROOT / "tools/validate-all/run_all.py"
CSHARP_PROMOTION_COMMIT = "2f6d39288e5c1a7d416e62cd75651b3d6da48dfe"


def _load_run_all_module():
    spec = importlib.util.spec_from_file_location(
        "rc_validate_all_archive_history",
        RUN_ALL_PATH,
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("could not load validate-all module")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _prepare_archive_root(root: Path, run_all) -> None:
    bundle_target = root / run_all.COMPATIBILITY_HISTORY_BUNDLE
    bundle_target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(
        REPO_ROOT / run_all.COMPATIBILITY_HISTORY_BUNDLE,
        bundle_target,
    )

    standards = root / "languages/csharp/standards"
    standards.mkdir(parents=True)
    (standards / "ARCHIVE_MARKER.md").write_text(
        "archive current tree\n",
        encoding="utf-8",
    )


class ReleaseCandidateArchiveHeadHistoryTests(unittest.TestCase):
    def test_archive_history_exposes_ephemeral_head_without_source_git_metadata(self) -> None:
        run_all = _load_run_all_module()

        with tempfile.TemporaryDirectory(prefix="rc-archive-head-") as temp:
            root = Path(temp)
            _prepare_archive_root(root, run_all)

            self.assertFalse((root / ".git").exists())
            with run_all.compatibility_history(root):
                head = subprocess.run(
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
                self.assertEqual(head.returncode, 0, head.stderr)
                self.assertRegex(head.stdout.strip(), r"^[0-9a-f]{40}$")

                pinned = subprocess.run(
                    [
                        "git",
                        "-C",
                        str(root),
                        "rev-parse",
                        f"{CSHARP_PROMOTION_COMMIT}:languages/csharp/standards",
                    ],
                    text=True,
                    capture_output=True,
                    check=False,
                )
                self.assertEqual(pinned.returncode, 0, pinned.stderr)
                self.assertRegex(pinned.stdout.strip(), r"^[0-9a-f]{40}$")
                self.assertFalse((root / ".git").exists())

            self.assertFalse((root / ".git").exists())

    def test_archive_history_allows_nested_repository_initialization(self) -> None:
        run_all = _load_run_all_module()

        with tempfile.TemporaryDirectory(prefix="rc-archive-nested-git-") as temp:
            root = Path(temp)
            _prepare_archive_root(root, run_all)
            fixture = root / "fixture"
            fixture.mkdir()

            self.assertFalse((root / ".git").exists())
            self.assertFalse((fixture / ".git").exists())

            with run_all.compatibility_history(root):
                initialized = subprocess.run(
                    ["git", "-C", str(fixture), "init", "--quiet"],
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

                subprocess.run(
                    ["git", "-C", str(fixture), "config", "user.name", "RC fixture"],
                    check=True,
                    text=True,
                    capture_output=True,
                )
                subprocess.run(
                    [
                        "git",
                        "-C",
                        str(fixture),
                        "config",
                        "user.email",
                        "fixture@example.invalid",
                    ],
                    check=True,
                    text=True,
                    capture_output=True,
                )
                (fixture / "marker.txt").write_text("fixture repository\n", encoding="utf-8")
                subprocess.run(
                    ["git", "-C", str(fixture), "add", "marker.txt"],
                    check=True,
                    text=True,
                    capture_output=True,
                )
                subprocess.run(
                    ["git", "-C", str(fixture), "commit", "--quiet", "-m", "fixture"],
                    check=True,
                    text=True,
                    capture_output=True,
                )
                committed = subprocess.run(
                    ["git", "-C", str(fixture), "rev-parse", "HEAD"],
                    text=True,
                    capture_output=True,
                    check=False,
                )
                self.assertEqual(committed.returncode, 0, committed.stderr)
                self.assertRegex(committed.stdout.strip(), r"^[0-9a-f]{40}$")

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


if __name__ == "__main__":
    unittest.main()
