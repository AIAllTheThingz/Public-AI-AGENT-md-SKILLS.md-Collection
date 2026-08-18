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


class ReleaseCandidateArchiveHeadHistoryTests(unittest.TestCase):
    def test_archive_history_exposes_ephemeral_head_without_source_git_metadata(self) -> None:
        run_all = _load_run_all_module()

        with tempfile.TemporaryDirectory(prefix="rc-archive-head-") as temp:
            root = Path(temp)
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


if __name__ == "__main__":
    unittest.main()
