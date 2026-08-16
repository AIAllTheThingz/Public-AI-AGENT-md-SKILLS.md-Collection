from __future__ import annotations

import hashlib
import json
import re
import subprocess
import unittest
from pathlib import Path

from helpers import REPO_ROOT

CANDIDATE_INVENTORY = REPO_ROOT / "releases" / "compatibility" / "1.0.0-rc.1.json"
RULE_CHECKPOINT = REPO_ROOT / "releases" / "compatibility" / "0.10.0-rule-contracts.json"
RULE_CHECKPOINT_SHA256 = "eba5b25f4036bbd62c3265579ec450c6c44f36da7a69c2a62559ae017de2efa4"
CSHARP_PROMOTION_EVIDENCE_COMMIT = "2f6d39288e5c1a7d416e62cd75651b3d6da48dfe"
CSHARP_NORMATIVE_ROOT = "languages/csharp/standards"
RULE_PATTERN = re.compile(
    r"^### (?P<id>[A-Z][A-Z0-9-]*-\d{3})\s*$\n\n"
    r"\*\*Requirement:\*\* (?P<requirement>[^\n]+)$",
    re.MULTILINE,
)
RULE_HEADING_PATTERN = re.compile(r"(?m)^### ([A-Z][A-Z0-9-]*-\d{3})\s*$")


def git_object_sha_at(revision: str, relative: str) -> str:
    completed = subprocess.run(
        ["git", "-C", str(REPO_ROOT), "rev-parse", f"{revision}:{relative}"],
        text=True,
        capture_output=True,
        check=False,
    )
    if completed.returncode != 0:
        raise AssertionError(
            completed.stderr.strip()
            or f"cannot resolve {revision}:{relative}; full Git history is required"
        )
    return completed.stdout.strip()


def git_object_sha(relative: str) -> str:
    return git_object_sha_at("HEAD", relative)


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

    def test_every_published_numbered_rule_surface_is_anchored(self):
        protected = {}
        protected.update(self.checkpoint["publishedUnchangedRuleTrees"])
        protected.update(self.checkpoint["publishedUnchangedLanguagePackageTrees"])

        for relative, expected_tree in protected.items():
            with self.subTest(tree=relative):
                self.assertEqual(git_object_sha(relative), expected_tree)

        csharp_source = self.checkpoint["csharpProductRules"]["sourcePath"]
        power_shell_root = "languages/powershell"
        rule_paths: dict[str, list[str]] = {}
        for path in sorted(REPO_ROOT.rglob("*.md")):
            relative = path.relative_to(REPO_ROOT).as_posix()
            ids = RULE_HEADING_PATTERN.findall(path.read_text(encoding="utf-8"))
            if ids:
                rule_paths[relative] = ids

        def covered(relative: str) -> bool:
            if relative == csharp_source:
                return True
            if relative == power_shell_root or relative.startswith(power_shell_root + "/"):
                return True
            return any(
                relative == root or relative.startswith(root + "/")
                for root in protected
            )

        uncovered = {path: ids for path, ids in rule_paths.items() if not covered(path)}
        self.assertEqual(uncovered, {})
        self.assertIn("disciplines/application-security/AGENTS.md", rule_paths)
        self.assertIn("SEC-INPUT-001", rule_paths["disciplines/application-security/AGENTS.md"])

    def test_csharp_product_rule_ids_and_meaning_are_preserved(self):
        source = self.checkpoint["csharpProductRules"]
        text = (REPO_ROOT / source["sourcePath"]).read_text(encoding="utf-8")
        actual = extract_rule_contracts(text)
        expected = source["rules"]
        self.assertEqual(rule_contract_findings(expected, actual), [])
        self.assertEqual(len(expected), 10)
        self.assertIn("CSHARP-LANG-001", expected)
        self.assertIn("CSHARP-EVIDENCE-010", expected)

    def test_full_csharp_normative_standards_match_promotion_evidence_candidate(self):
        promoted_tree = git_object_sha_at(CSHARP_PROMOTION_EVIDENCE_COMMIT, CSHARP_NORMATIVE_ROOT)
        current_tree = git_object_sha_at("HEAD", CSHARP_NORMATIVE_ROOT)
        self.assertEqual(
            current_tree,
            promoted_tree,
            "stable C# normative standards changed after the independently reviewed promotion evidence candidate",
        )

        security_standard = f"{CSHARP_NORMATIVE_ROOT}/SECURITY_STANDARD.md"
        self.assertEqual(
            git_object_sha_at("HEAD", security_standard),
            git_object_sha_at(CSHARP_PROMOTION_EVIDENCE_COMMIT, security_standard),
        )

    def test_powershell_published_source_had_no_numbered_rule_contract(self):
        source = self.checkpoint["changedPublishedRuleSources"]["languages/powershell"]
        self.assertEqual(source["publishedTreeSha"], "7f1b68ff66b18108454b22b98e3528736d42e615")
        self.assertIn("no numbered normative rule headings", source["ruleContract"])

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
