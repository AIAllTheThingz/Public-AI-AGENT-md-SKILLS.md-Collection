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
    "tools/release/build_release.py",
}


def git_output(*args: str) -> str:
    completed = subprocess.run(
        ["git", "-C", str(REPO_ROOT), *args],
        text=True,
        encoding="utf-8",
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
    output_options = ('"--output"', '"--output-dir"', '"--manifest-output"')
    for path in paths:
        if not path.endswith(".py") or path.startswith("tools/tests/") or "/tests/" in path:
            continue
        source = git_output("show", f"{CHECKPOINT_COMMIT}:{path}")
        if '"--force"' in source and any(option in source for option in output_options):
            writers.add(path)
    return writers


def init_release_builder_repo(root: Path) -> None:
    (root / "releases" / "migrations").mkdir(parents=True)
    (root / "VERSION").write_text("0.10.1\n", encoding="utf-8")
    (root / "README.md").write_text("# Release builder fixture\n", encoding="utf-8")
    (root / "releases" / "0.10.1.md").write_text(
        "# Release 0.10.1\n\nCompatibility fixture.\n", encoding="utf-8"
    )
    (root / "releases" / "migrations" / "0.10.1.md").write_text(
        "# Migration 0.10.1\n\nNo breaking migration.\n", encoding="utf-8"
    )
    (root / "releases" / "release-state.json").write_text(
        json.dumps(
            {
                "formatVersion": "1.1.0",
                "project": "Public Access Agents",
                "canonicalRepository": "AIAllTheThingz/Public-AI-Governance",
                "artifactPrefix": "Public-Access-Agents",
                "preparedUnpublishedVersions": [],
                "nextIntendedVersion": "0.10.1",
                "publishedVersions": ["0.10.0"],
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    for args in (
        ("init",),
        ("config", "user.email", "compat@example.invalid"),
        ("config", "user.name", "Compatibility Test"),
        ("add", "."),
        ("commit", "-m", "fixture"),
    ):
        completed = subprocess.run(
            ["git", "-C", str(root), *args],
            text=True,
            encoding="utf-8",
            capture_output=True,
            check=False,
        )
        if completed.returncode != 0:
            raise AssertionError(completed.stdout + completed.stderr)


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

    def test_release_builder_refuses_existing_output_without_force_and_replaces_with_force(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "release-root"
            root.mkdir()
            init_release_builder_repo(root)
            output = root / "dist"
            output.mkdir()
            sentinel = output / "sentinel.txt"
            sentinel.write_text("do-not-overwrite\n", encoding="utf-8")
            args = (
                "--root",
                str(root),
                "--output-dir",
                str(output),
            )

            blocked = run_tool("tools/release/build_release.py", *args)
            self.assertEqual(blocked.returncode, 2, blocked.stdout + blocked.stderr)
            self.assertTrue(sentinel.is_file())
            self.assertEqual(sentinel.read_text(encoding="utf-8"), "do-not-overwrite\n")

            forced = run_tool("tools/release/build_release.py", *args, "--force")
            self.assertEqual(forced.returncode, 0, forced.stdout + forced.stderr)
            self.assertFalse(sentinel.exists())
            self.assertTrue((output / "release-manifest.json").is_file())
            self.assertTrue((output / "SHA256SUMS.txt").is_file())
            self.assertTrue((output / "Public-Access-Agents-0.10.1.zip").is_file())
            self.assertTrue((output / "Public-Access-Agents-0.10.1.tar.gz").is_file())


if __name__ == "__main__":
    unittest.main()
