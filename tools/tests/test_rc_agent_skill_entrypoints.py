from __future__ import annotations

import hashlib
import json
import re
import subprocess
import unittest

from helpers import REPO_ROOT

CHECKPOINT_COMMIT = "83c73f3ab9a049ff2321d463164fcf98fb453a9c"
CHECKPOINT_PATH = REPO_ROOT / "releases" / "compatibility" / "0.10.0-agent-skill-entrypoints.json"
CHECKPOINT_SHA256 = "635e34c53f967d1b0bff9602037f7c716650cbf815f7aae3efc6f15c936921fb"


def git_source_at(commit: str, relative: str) -> str:
    completed = subprocess.run(
        ["git", "-C", str(REPO_ROOT), "show", f"{commit}:{relative}"],
        text=True,
        capture_output=True,
        check=False,
    )
    if completed.returncode != 0:
        raise AssertionError(completed.stderr.strip() or f"cannot resolve {commit}:{relative}")
    return completed.stdout


def git_object_sha(commit: str, relative: str) -> str:
    completed = subprocess.run(
        ["git", "-C", str(REPO_ROOT), "rev-parse", f"{commit}:{relative}"],
        text=True,
        capture_output=True,
        check=False,
    )
    if completed.returncode != 0:
        raise AssertionError(completed.stderr.strip() or f"cannot resolve {commit}:{relative}")
    return completed.stdout.strip()


def agent_skill_entry_paths(manifest_text: str) -> set[str]:
    section = manifest_text.split("## Agent skill entry points", 1)[1].split(
        "## Repository licensing", 1
    )[0]
    return set(re.findall(r"^- `([^`]+)`\s*$", section, flags=re.MULTILINE))


def missing_skill_entries(expected: set[str], observed: set[str]) -> list[str]:
    return sorted(expected - observed)


class ReleaseCandidateAgentSkillEntryPointTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.checkpoint_bytes = CHECKPOINT_PATH.read_bytes()
        cls.checkpoint = json.loads(cls.checkpoint_bytes.decode("utf-8"))

    def test_checkpoint_is_immutable_and_derived_from_published_manifest(self):
        self.assertEqual(hashlib.sha256(self.checkpoint_bytes).hexdigest(), CHECKPOINT_SHA256)
        self.assertEqual(self.checkpoint["releaseVersion"], "0.10.0")
        self.assertEqual(self.checkpoint["tag"], "v0.10.0")
        self.assertEqual(self.checkpoint["sourceCommit"], CHECKPOINT_COMMIT)

        source_manifest = self.checkpoint["sourceManifest"]
        self.assertEqual(source_manifest["path"], "MANIFEST.md")
        self.assertEqual(
            git_object_sha(CHECKPOINT_COMMIT, source_manifest["path"]),
            source_manifest["blobSha"],
        )

        published = agent_skill_entry_paths(
            git_source_at(CHECKPOINT_COMMIT, source_manifest["path"])
        )
        self.assertEqual(
            set(self.checkpoint["stableAgentSkillEntryPaths"]),
            published,
        )

    def test_candidate_preserves_every_published_agent_skill_entry_path(self):
        expected = set(self.checkpoint["stableAgentSkillEntryPaths"])
        current_manifest = (REPO_ROOT / "MANIFEST.md").read_text(encoding="utf-8")
        observed = agent_skill_entry_paths(current_manifest)
        self.assertEqual(missing_skill_entries(expected, observed), [])

        for relative in expected:
            with self.subTest(path=relative):
                self.assertTrue((REPO_ROOT / relative).is_file(), relative)

    def test_candidate_comparison_detects_removed_language_skill_entry(self):
        expected = set(self.checkpoint["stableAgentSkillEntryPaths"])
        observed = set(expected)
        observed.remove("languages/SKILL.md")
        self.assertEqual(
            missing_skill_entries(expected, observed),
            ["languages/SKILL.md"],
        )


if __name__ == "__main__":
    unittest.main()
