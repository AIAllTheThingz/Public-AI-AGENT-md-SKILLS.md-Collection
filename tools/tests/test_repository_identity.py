from __future__ import annotations

import unittest
from pathlib import Path

from helpers import REPO_ROOT


CANONICAL_REPOSITORY = "AIAllTheThingz/Public-AI-Governance"
STALE_REPOSITORY = "AIAllTheThingz/Public-Access-Agents"
CANONICAL_RAW_PREFIX = f"https://raw.githubusercontent.com/{CANONICAL_REPOSITORY}/"
STALE_RAW_PREFIX = f"https://raw.githubusercontent.com/{STALE_REPOSITORY}/"


class RepositoryIdentityTests(unittest.TestCase):
    def test_schema_and_tool_contract_ids_use_canonical_repository(self):
        candidates = sorted((REPO_ROOT / "schemas").rglob("*.schema.json"))
        candidates.append(REPO_ROOT / "tools" / "contracts" / "tool-result.schema.json")

        for path in candidates:
            text = path.read_text(encoding="utf-8")
            with self.subTest(path=path.relative_to(REPO_ROOT).as_posix()):
                self.assertNotIn(STALE_RAW_PREFIX, text)
                if '"$id"' in text:
                    self.assertIn(CANONICAL_RAW_PREFIX, text)

    def test_repository_identity_is_documented_without_rebranding_artifacts(self):
        readme = (REPO_ROOT / "README.md").read_text(encoding="utf-8")
        release_index = (REPO_ROOT / "releases" / "README.md").read_text(encoding="utf-8")
        builder = (REPO_ROOT / "tools" / "release" / "build_release.py").read_text(encoding="utf-8")

        self.assertIn(CANONICAL_REPOSITORY, readme)
        self.assertIn("Public Access Agents", readme)
        self.assertIn("0.9.0 (prepared, unpublished)", readme)
        self.assertIn("0.10.0", release_index)
        self.assertIn('ARCHIVE_PREFIX = "Public-Access-Agents"', builder)

    def test_unpublished_0_9_0_state_and_forward_release_plan_are_explicit(self):
        changelog = (REPO_ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
        old_notes = (REPO_ROOT / "releases" / "0.9.0.md").read_text(encoding="utf-8")
        next_notes = (REPO_ROOT / "releases" / "0.10.0.md").read_text(encoding="utf-8")
        next_migration = (REPO_ROOT / "releases" / "migrations" / "0.10.0.md").read_text(encoding="utf-8")

        self.assertIn("never published", old_notes.lower())
        self.assertIn("must not be retroactively tagged as `v0.9.0`", changelog)
        self.assertIn("Status: **Prepared, not published**", next_notes)
        self.assertIn("## Required actions", next_migration)
        self.assertNotIn(f"https://github.com/{STALE_REPOSITORY}/", changelog)


if __name__ == "__main__":
    unittest.main()
