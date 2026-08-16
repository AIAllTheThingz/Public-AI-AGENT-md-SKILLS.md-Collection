from __future__ import annotations

import json
import re
import unittest
from pathlib import Path

from helpers import REPO_ROOT


CANONICAL_REPOSITORY = "AIAllTheThingz/Public-AI-Governance"
STALE_REPOSITORY = "AIAllTheThingz/Public-Access-Agents"
CANONICAL_RAW_PREFIX = f"https://raw.githubusercontent.com/{CANONICAL_REPOSITORY}/"
STALE_RAW_PREFIX = f"https://raw.githubusercontent.com/{STALE_REPOSITORY}/"
SEMVER = (
    r"\d+\.\d+\.\d+"
    r"(?:-[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*)?"
    r"(?:\+[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*)?"
)
NEXT_PUBLICATION = re.compile(
    rf"next intended publication(?:\s+is|:)?\s+`(?P<version>{SEMVER})`",
    re.IGNORECASE,
)


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

    def test_durable_release_and_toolchain_docs_follow_release_state(self):
        state = json.loads((REPO_ROOT / "releases" / "release-state.json").read_text(encoding="utf-8"))
        next_version = state["nextIntendedVersion"]
        prepared = set(state["preparedUnpublishedVersions"])

        self.assertEqual(next_version, "0.10.0")
        self.assertIn("0.9.0", prepared)

        roadmap = (REPO_ROOT / "ROADMAP.md").read_text(encoding="utf-8")
        manifest = (REPO_ROOT / "MANIFEST.md").read_text(encoding="utf-8")
        catalog = (REPO_ROOT / "CATALOG.md").read_text(encoding="utf-8")
        release_policy = (REPO_ROOT / "RELEASE_POLICY.md").read_text(encoding="utf-8")

        expected_direction = {
            "ROADMAP.md": (
                f"- The next intended publication is `{next_version}` after source-currency review, "
                "final release preparation, and the independent specialist review required for its breaking changes."
            ),
            "MANIFEST.md": f"Next intended publication: `{next_version}`.",
            "CATALOG.md": f"The next intended publication is `{next_version}`.",
            "RELEASE_POLICY.md": f"The forward-only next intended publication is `{next_version}`, as recorded in",
        }
        durable_docs = {
            "ROADMAP.md": roadmap,
            "MANIFEST.md": manifest,
            "CATALOG.md": catalog,
            "RELEASE_POLICY.md": release_policy,
        }
        for name, text in durable_docs.items():
            with self.subTest(document=name):
                self.assertIn(expected_direction[name], text)
                self.assertNotIn("Publish and independently verify the `v0.9.0` GitHub Release", text)
                declared_versions = NEXT_PUBLICATION.findall(text)
                self.assertEqual(
                    declared_versions,
                    [next_version],
                    f"{name} must contain exactly one next-intended-publication declaration and it must match release-state.json.",
                )

        self.assertIn("prepared, unpublished", manifest.lower())
        self.assertIn("check-freshness", manifest)
        self.assertIn("requirements.lock", manifest)
        self.assertIn("check-freshness", catalog)
        self.assertIn("prepared, unpublished", catalog.lower())

        self.assertIn("originally prepared `0.9.0`", release_policy)
        self.assertIn("never published", release_policy)
        self.assertIn("must not be reconstructed or retroactively tagged", release_policy)
        self.assertIn("releases/release-state.json", release_policy)
        self.assertNotIn("The initial repository release target is `0.9.0`", release_policy)

    def test_roadmap_retains_package_level_adoption_testing_before_stable_promotion(self):
        roadmap = (REPO_ROOT / "ROADMAP.md").read_text(encoding="utf-8")
        adoption_tests = roadmap.index("Add automated package-level adoption tests")
        maturity_reviews = roadmap.index("Complete package maturity reviews")

        self.assertLess(adoption_tests, maturity_reviews)
        self.assertIn("positive, negative, and failure-path exercises", roadmap)
        release_step = roadmap.index("Prepare the first real `v0.10.0` release")
        review_gate = roadmap.index("independent specialist review required for its breaking changes", release_step)
        publish_gate = roadmap.index("publish only after that gate passes", review_gate)
        self.assertLess(review_gate, publish_gate)


if __name__ == "__main__":
    unittest.main()
