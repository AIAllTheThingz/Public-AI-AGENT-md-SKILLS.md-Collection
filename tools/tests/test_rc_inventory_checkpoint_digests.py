from __future__ import annotations

import hashlib
import json
import unittest

from helpers import REPO_ROOT

INVENTORY_PATH = REPO_ROOT / "releases" / "compatibility" / "1.0.0-rc.1.json"
PIN_KEYS = (
    "publishedCheckpointInventory",
    "publishedToolBehaviorContract",
    "publishedFindingCodeContract",
    "publishedRuleContractCheckpoint",
)


class ReleaseCandidateInventoryCheckpointDigestTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.inventory = json.loads(INVENTORY_PATH.read_text(encoding="utf-8"))

    def test_every_machine_readable_checkpoint_digest_matches_referenced_file(self):
        for key in PIN_KEYS:
            with self.subTest(checkpoint=key):
                pin = self.inventory[key]
                path = REPO_ROOT / pin["path"]
                self.assertTrue(path.is_file(), f"{key} references missing file {path}")
                actual = hashlib.sha256(path.read_bytes()).hexdigest()
                self.assertEqual(
                    pin["sha256"],
                    actual,
                    f"{key} digest does not match {pin['path']}",
                )


if __name__ == "__main__":
    unittest.main()
