from __future__ import annotations

import json
import unittest
from pathlib import Path

from helpers import REPO_ROOT


class RepositoryConsistencyTests(unittest.TestCase):
    def test_forward_release_guidance_never_revives_unpublished_090(self):
        release_state = json.loads((REPO_ROOT / "releases" / "release-state.json").read_text(encoding="utf-8"))
        roadmap = (REPO_ROOT / "ROADMAP.md").read_text(encoding="utf-8")

        self.assertIn("0.9.0", release_state["preparedUnpublishedVersions"])
        self.assertEqual(release_state["nextIntendedVersion"], "0.10.0")
        self.assertNotIn("Publish and independently verify the `v0.9.0` GitHub Release", roadmap)
        self.assertIn("forward-only `v0.10.0` GitHub Release", roadmap)

    def test_root_manifest_lists_freshness_contract_and_hash_locked_install(self):
        manifest = (REPO_ROOT / "MANIFEST.md").read_text(encoding="utf-8")

        self.assertIn("`SOURCE_REVIEWS.json`", manifest)
        self.assertIn("offline authoritative-source review freshness validation", manifest)
        self.assertIn("--require-hashes -r tools/validate-schemas/requirements.lock", manifest)
        self.assertNotIn("python -m pip install -r tools/validate-schemas/requirements.txt", manifest)

    def test_catalog_exposes_freshness_validator(self):
        catalog = (REPO_ROOT / "CATALOG.md").read_text(encoding="utf-8")

        self.assertIn("source-review freshness metadata", catalog)
        self.assertIn("[Freshness validator](tools/check-freshness/)", catalog)
        self.assertIn("[Source-review freshness registry](SOURCE_REVIEWS.json)", catalog)


if __name__ == "__main__":
    unittest.main()
