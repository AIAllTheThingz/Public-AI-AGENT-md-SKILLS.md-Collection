from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from helpers import REPO_ROOT, sha256_utf8_text_file

INVENTORY_PATH = REPO_ROOT / "releases" / "compatibility" / "1.0.0-rc.1.json"
PIN_KEYS = (
    "publishedCheckpointInventory",
    "publishedAgentSkillEntryPointCheckpoint",
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
                actual = sha256_utf8_text_file(path)
                self.assertEqual(
                    pin["sha256"],
                    actual,
                    f"{key} digest does not match {pin['path']}",
                )

    def test_text_checkpoint_hash_normalizes_only_crlf_and_rejects_binary_content(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            lf = root / "checkpoint-lf.json"
            crlf = root / "checkpoint-crlf.json"
            bare_cr = root / "checkpoint-bare-cr.json"
            changed = root / "checkpoint-changed.json"
            binary = root / "checkpoint.bin"
            lf.write_bytes(b'{"version":"1"}\n')
            crlf.write_bytes(b'{"version":"1"}\r\n')
            bare_cr.write_bytes(b'{"version":"1"}\r')
            changed.write_bytes(b'{"version":"2"}\n')
            binary.write_bytes(b"\0")

            self.assertEqual(sha256_utf8_text_file(lf), sha256_utf8_text_file(crlf))
            self.assertNotEqual(sha256_utf8_text_file(lf), sha256_utf8_text_file(bare_cr))
            self.assertNotEqual(sha256_utf8_text_file(lf), sha256_utf8_text_file(changed))
            with self.assertRaisesRegex(ValueError, "UTF-8 text"):
                sha256_utf8_text_file(binary)

    def test_agent_skill_checkpoint_is_authoritative_inventory_evidence(self):
        pin = self.inventory["publishedAgentSkillEntryPointCheckpoint"]
        self.assertEqual(
            pin["path"],
            "releases/compatibility/0.10.0-agent-skill-entrypoints.json",
        )
        checkpoint = json.loads((REPO_ROOT / pin["path"]).read_text(encoding="utf-8"))
        self.assertEqual(len(checkpoint["stableAgentSkillEntryPaths"]), 7)
        self.assertIn("languages/SKILL.md", checkpoint["stableAgentSkillEntryPaths"])


if __name__ == "__main__":
    unittest.main()
