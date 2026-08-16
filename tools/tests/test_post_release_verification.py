from __future__ import annotations

import json
import unittest

from helpers import REPO_ROOT


class PostReleaseVerificationTests(unittest.TestCase):
    def test_published_release_state_is_durable(self):
        state = json.loads((REPO_ROOT / "releases" / "release-state.json").read_text(encoding="utf-8"))
        self.assertIn("0.10.0", state["publishedVersions"])
        self.assertEqual(state["nextIntendedVersion"], "1.0.0-rc.1")
        self.assertNotIn("0.10.0", state["preparedUnpublishedVersions"])

    def test_release_notes_and_index_record_publication(self):
        notes = (REPO_ROOT / "releases" / "0.10.0.md").read_text(encoding="utf-8")
        index = (REPO_ROOT / "releases" / "README.md").read_text(encoding="utf-8")
        self.assertIn("Status: **Published and verified**", notes)
        self.assertIn("`v0.10.0`", notes)
        self.assertIn("Published 2026-08-16", index)

    def test_verification_record_pins_release_evidence(self):
        evidence = (REPO_ROOT / "releases" / "verification" / "0.10.0.md").read_text(encoding="utf-8")
        self.assertIn("83c73f3ab9a049ff2321d463164fcf98fb453a9c", evidence)
        self.assertIn("31961226369", evidence)
        self.assertIn("82399ab998c4bc28a195d191bf2595c9b1ccb9666a8cbe08e43ccd274579a778", evidence)
        self.assertIn("543905518c3d7bbff3055bd30adce934bd1ca8d2a3022dbd9f5997a232d0341d", evidence)
        self.assertIn("NotRun / unsigned annotated tag", evidence)


if __name__ == "__main__":
    unittest.main()
