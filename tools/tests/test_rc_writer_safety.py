from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path

from helpers import REPO_ROOT, run_tool

CHECKPOINT_COMMIT = "83c73f3ab9a049ff2321d463164fcf98fb453a9c"
EXPECTED_WRITERS = {
    "tools/generate-manifest/generate_manifest.py",
    "tools/compose-agents/compose_agents.py",
}


def git_output(*args: str) -> str:
    completed = subprocess.run(
        ["git", "-C", str(REPO_ROOT), *args],
        text=True,
        capture_output=True,
        check=False,
    )
    if completed.returncode != 0:
        raise AssertionError(completed.stderr.strip() or "git command failed")
    return completed.stdout


def published_stable_writers() -> set[str]:
    paths = git_output(
        "ls-tree", "-r", "--name-only", CHECKPOINT_COMMIT, "tools"
    ).splitlines()
    writers: set[str] = set()
    for path in paths:
        if not path.endswith(".py") or path.startswith("tools/tests/") or "/tests/" in path:
            continue
        source = git_output("show", f"{CHECKPOINT_COMMIT}:{path}")
        if '"--force"' in source and '"--dry-run"' in source:
            writers.add(path)
    return writers


class ReleaseCandidateWriterSafetyTests(unittest.TestCase):
    def test_published_writer_set_is_complete(self):
        self.assertEqual(published_stable_writers(), EXPECTED_WRITERS)

    def test_generate_manifest_refuses_dry_runs_and_forces_safely(self):
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / "project-manifest.json"
            sentinel = "do-not-overwrite\n"
            output.write_text(sentinel, encoding="utf-8")
            args = (
                "--format",
                "json",
                "--name",
                "writer-safety",
                "--profile",
                "CLI_TOOL",
                "--language",
                "csharp",
                "--manifest-output",
                str(output),
            )

            blocked = run_tool("tools/generate-manifest/generate_manifest.py", *args)
            self.assertEqual(blocked.returncode, 2, blocked.stdout + blocked.stderr)
            self.assertEqual(output.read_text(encoding="utf-8"), sentinel)

            dry_run = run_tool(
                "tools/generate-manifest/generate_manifest.py", *args, "--dry-run"
            )
            self.assertEqual(dry_run.returncode, 0, dry_run.stdout + dry_run.stderr)
            self.assertEqual(output.read_text(encoding="utf-8"), sentinel)

            forced = run_tool(
                "tools/generate-manifest/generate_manifest.py", *args, "--force"
            )
            self.assertEqual(forced.returncode, 0, forced.stdout + forced.stderr)
            self.assertNotEqual(output.read_text(encoding="utf-8"), sentinel)
            payload = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(payload["name"], "writer-safety")

    def test_compose_agents_refuses_dry_runs_and_forces_safely(self):
        with tempfile.TemporaryDirectory() as temp:
            temp_root = Path(temp)
            manifest = temp_root / "manifest.json"
            manifest.write_text(
                json.dumps(
                    {
                        "name": "writer-safety",
                        "profile": "CLI_TOOL",
                        "languages": ["csharp"],
                        "disciplines": [],
                    }
                ),
                encoding="utf-8",
            )
            output = temp_root / "bundle"
            output.mkdir()
            sentinel = output / "sentinel.txt"
            sentinel.write_text("do-not-overwrite\n", encoding="utf-8")
            args = (
                "--root",
                str(REPO_ROOT),
                "--format",
                "json",
                "--manifest",
                str(manifest),
                "--output-dir",
                str(output),
                "--no-copy-sources",
            )

            blocked = run_tool("tools/compose-agents/compose_agents.py", *args)
            self.assertEqual(blocked.returncode, 2, blocked.stdout + blocked.stderr)
            self.assertTrue(sentinel.is_file())

            dry_run = run_tool(
                "tools/compose-agents/compose_agents.py", *args, "--dry-run"
            )
            self.assertEqual(dry_run.returncode, 0, dry_run.stdout + dry_run.stderr)
            self.assertTrue(sentinel.is_file())
            self.assertEqual(sentinel.read_text(encoding="utf-8"), "do-not-overwrite\n")

            forced = run_tool(
                "tools/compose-agents/compose_agents.py", *args, "--force"
            )
            self.assertEqual(forced.returncode, 0, forced.stdout + forced.stderr)
            self.assertFalse(sentinel.exists())
            self.assertTrue((output / "AGENTS.md").is_file())
            self.assertTrue((output / "COMPOSITION_MANIFEST.json").is_file())
            payload = json.loads(
                (output / "COMPOSITION_MANIFEST.json").read_text(encoding="utf-8")
            )
            self.assertEqual(payload["project"], "writer-safety")
            self.assertFalse(payload["copiedSources"])


if __name__ == "__main__":
    unittest.main()
