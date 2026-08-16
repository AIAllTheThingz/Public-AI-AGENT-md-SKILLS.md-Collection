from __future__ import annotations

import hashlib
import json
import re
import unittest
from pathlib import Path

from helpers import REPO_ROOT

CANDIDATE_INVENTORY = REPO_ROOT / "releases" / "compatibility" / "1.0.0-rc.1.json"
RULE_CHECKPOINT = REPO_ROOT / "releases" / "compatibility" / "0.10.0-rule-contracts.json"
RULE_CHECKPOINT_SHA256 = "ce7708ab32b8bf6a7fbaf0bd12020388f2069470aaf2fc2e890a3778e003029c"
RULE_PATTERN = re.compile(
    r"^### (?P<id>[A-Z][A-Z0-9-]*-\d{3})\s*$\n\n"
    r"\*\*Requirement:\*\* (?P<requirement>[^\n]+)$",
    re.MULTILINE,
)


def git_blob_sha(data: bytes) -> str:
    header = f"blob {len(data)}\0".encode("ascii")
    return hashlib.sha1(header + data).hexdigest()


def extract_rule_contracts(text: str) -> list[tuple[str, str]]:
    return [
        (match.group("id"), match.group("requirement").strip())
        for match in RULE_PATTERN.finditer(text)
    ]


def rule_contract_findings(
    expected: dict[str, str], actual: list[tuple[str, str]]
) -> list[str]:
    findings: list[str] = []
    seen: dict[str, str] = {}
    for rule_id, requirement in actual:
        if rule_id in seen:
            findings.append(f"DUPLICATE_RULE_ID:{rule_id}")
            continue
        seen[rule_id] = requirement

    for rule_id, expected_requirement in expected.items():
        if rule_id not in seen:
            findings.append(f"MISSING_RULE:{rule_id}")
        elif seen[rule_id] != expected_requirement:
            findings.append(f"CHANGED_RULE_MEANING:{rule_id}")

    for rule_id in sorted(set(seen) - set(expected)):
        findings.append(f"UNEXPECTED_RULE:{rule_id}")
    return findings


class ReleaseCandidateNormativeRuleContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.inventory = json.loads(CANDIDATE_INVENTORY.read_text(encoding="utf-8"))
        cls.checkpoint_bytes = RULE_CHECKPOINT.read_bytes()
        cls.checkpoint = json.loads(cls.checkpoint_bytes.decode("utf-8"))

    def test_candidate_pins_published_rule_contract_checkpoint(self):
        pin = self.inventory["publishedRuleContractCheckpoint"]
        self.assertEqual(pin["path"], "releases/compatibility/0.10.0-rule-contracts.json")
        self.assertEqual(pin["sha256"], RULE_CHECKPOINT_SHA256)
        self.assertEqual(hashlib.sha256(self.checkpoint_bytes).hexdigest(), RULE_CHECKPOINT_SHA256)
        self.assertEqual(self.checkpoint["releaseVersion"], "0.10.0")
        self.assertEqual(self.checkpoint["tag"], "v0.10.0")
        self.assertEqual(
            self.checkpoint["sourceCommit"],
            "83c73f3ab9a049ff2321d463164fcf98fb453a9c",
        )
        rule_source = self.inventory["stableIdentifierContracts"]["publishedNormativeRules"]
        self.assertEqual(
            rule_source["source"],
            "releases/compatibility/0.10.0-rule-contracts.json",
        )

    def test_published_governance_rule_ids_and_meaning_are_preserved(self):
        total_rules = 0
        for record in self.checkpoint["governancePolicyRules"]:
            path = REPO_ROOT / record["path"]
            data = path.read_bytes()
            contracts = extract_rule_contracts(data.decode("utf-8"))
            actual_ids = [rule_id for rule_id, _ in contracts]
            expected_ids = [
                f"{record['rulePrefix']}-{number:03d}"
                for number in range(record["first"], record["last"] + 1)
            ]
            with self.subTest(path=record["path"]):
                self.assertEqual(git_blob_sha(data), record["blobSha"])
                self.assertEqual(actual_ids, expected_ids)
                self.assertEqual(len(actual_ids), len(set(actual_ids)))
                self.assertTrue(all(requirement for _, requirement in contracts))
            total_rules += len(expected_ids)
        self.assertEqual(total_rules, 97)

    def test_csharp_product_rule_ids_and_meaning_are_preserved(self):
        source = self.checkpoint["csharpProductRules"]
        text = (REPO_ROOT / source["sourcePath"]).read_text(encoding="utf-8")
        actual = extract_rule_contracts(text)
        expected = source["rules"]
        self.assertEqual(rule_contract_findings(expected, actual), [])
        self.assertEqual(len(expected), 10)
        self.assertIn("CSHARP-LANG-001", expected)
        self.assertIn("CSHARP-EVIDENCE-010", expected)

    def test_rule_contract_checker_detects_removal_meaning_change_and_reuse(self):
        expected = {
            "RULE-001": "First requirement.",
            "RULE-002": "Second requirement.",
        }

        removed = [("RULE-001", "First requirement.")]
        self.assertIn("MISSING_RULE:RULE-002", rule_contract_findings(expected, removed))

        changed = [
            ("RULE-001", "Changed meaning."),
            ("RULE-002", "Second requirement."),
        ]
        self.assertIn(
            "CHANGED_RULE_MEANING:RULE-001",
            rule_contract_findings(expected, changed),
        )

        reused = [
            ("RULE-001", "First requirement."),
            ("RULE-001", "Different reused meaning."),
            ("RULE-002", "Second requirement."),
        ]
        self.assertIn("DUPLICATE_RULE_ID:RULE-001", rule_contract_findings(expected, reused))


if __name__ == "__main__":
    unittest.main()
