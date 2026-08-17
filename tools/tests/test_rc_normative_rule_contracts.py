from __future__ import annotations

import hashlib
import json
import re
import subprocess
import unittest
from collections import defaultdict

from helpers import REPO_ROOT

CANDIDATE_INVENTORY = REPO_ROOT / "releases" / "compatibility" / "1.0.0-rc.1.json"
RULE_CHECKPOINT = REPO_ROOT / "releases" / "compatibility" / "0.10.0-rule-contracts.json"
RULE_CHECKPOINT_SHA256 = "5f3b7a7ddd28de5a44b45f96998d7acffb2c287bad4c7699e21561a869e50c95"
CHECKPOINT_COMMIT = "83c73f3ab9a049ff2321d463164fcf98fb453a9c"
CSHARP_PROMOTION_EVIDENCE_COMMIT = "2f6d39288e5c1a7d416e62cd75651b3d6da48dfe"
CSHARP_NORMATIVE_ROOT = "languages/csharp/standards"
RULE_PATTERN = re.compile(
    r"^### (?P<id>[A-Z][A-Z0-9-]*-\d{3})\s*$\n\n"
    r"\*\*Requirement:\*\* (?P<requirement>[^\n]+)$",
    re.MULTILINE,
)


def git_output(*args: str) -> str:
    completed = subprocess.run(
        ["git", "-C", str(REPO_ROOT), *args],
        text=True,
        capture_output=True,
        check=False,
    )
    if completed.returncode != 0:
        raise AssertionError(completed.stderr.strip() or "git command failed")
    return completed.stdout


def git_source_at(revision: str, relative: str) -> str:
    return git_output("show", f"{revision}:{relative}")


def git_paths_at(revision: str, suffix: str) -> list[str]:
    paths = git_output("ls-tree", "-r", "--name-only", revision).splitlines()
    return sorted(path for path in paths if path.endswith(suffix))


def git_object_sha_at(revision: str, relative: str) -> str:
    return git_output("rev-parse", f"{revision}:{relative}").strip()


def extract_rule_contracts(text: str, path: str) -> list[tuple[str, str, str]]:
    return [
        (match.group("id"), match.group("requirement").strip(), path)
        for match in RULE_PATTERN.finditer(text)
    ]


def published_rule_contracts() -> list[tuple[str, str, str]]:
    contracts: list[tuple[str, str, str]] = []
    for relative in git_paths_at(CHECKPOINT_COMMIT, ".md"):
        contracts.extend(extract_rule_contracts(git_source_at(CHECKPOINT_COMMIT, relative), relative))
    return contracts


def candidate_rule_contracts() -> list[tuple[str, str, str]]:
    contracts: list[tuple[str, str, str]] = []
    for path in sorted(REPO_ROOT.rglob("*.md")):
        relative = path.relative_to(REPO_ROOT).as_posix()
        contracts.extend(extract_rule_contracts(path.read_text(encoding="utf-8"), relative))
    return contracts


def occurrences_by_key(
    contracts: list[tuple[str, str, str]]
) -> dict[tuple[str, str], list[str]]:
    result: dict[tuple[str, str], list[str]] = defaultdict(list)
    for rule_id, requirement, path in contracts:
        result[(path, rule_id)].append(requirement)
    return dict(result)


def paths_by_id(contracts: list[tuple[str, str, str]]) -> dict[str, set[str]]:
    result: dict[str, set[str]] = defaultdict(set)
    for rule_id, _, path in contracts:
        result[rule_id].add(path)
    return dict(result)


def rule_contract_findings(
    published: list[tuple[str, str, str]],
    candidate: list[tuple[str, str, str]],
) -> list[str]:
    findings: list[str] = []
    expected_by_key = occurrences_by_key(published)
    actual_by_key = occurrences_by_key(candidate)
    expected_paths = paths_by_id(published)
    actual_paths = paths_by_id(candidate)

    for (path, rule_id), published_requirements in expected_by_key.items():
        if len(published_requirements) != 1:
            findings.append(f"PUBLISHED_DUPLICATE_IN_SCOPE:{path}:{rule_id}")
            continue

        candidate_requirements = actual_by_key.get((path, rule_id), [])
        if not candidate_requirements:
            findings.append(f"MISSING_RULE:{path}:{rule_id}")
            continue
        if len(candidate_requirements) != 1:
            findings.append(f"DUPLICATE_RULE_IN_SCOPE:{path}:{rule_id}")
            continue
        if candidate_requirements[0] != published_requirements[0]:
            findings.append(f"CHANGED_RULE_MEANING:{path}:{rule_id}")

    # Published duplicate IDs in distinct scopes are grandfathered. Do not allow a
    # published ID to acquire a new scope, and do not allow a new ID to be reused.
    for rule_id, candidate_paths in actual_paths.items():
        published_paths = expected_paths.get(rule_id)
        if published_paths is not None:
            for extra_path in sorted(candidate_paths - published_paths):
                findings.append(f"REUSED_PUBLISHED_RULE_ID:{extra_path}:{rule_id}")
        elif len(candidate_paths) > 1:
            findings.append(f"DUPLICATE_NEW_RULE_ID:{rule_id}")

    return sorted(findings)


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
        self.assertEqual(self.checkpoint["sourceCommit"], CHECKPOINT_COMMIT)
        self.assertIn("grandfathered", self.checkpoint["coverageRule"])

    def test_every_published_numbered_rule_occurrence_and_meaning_is_preserved(self):
        published = published_rule_contracts()
        candidate = candidate_rule_contracts()
        self.assertGreater(len(published), 100)
        published_ids = {rule_id for rule_id, _, _ in published}
        self.assertIn("SEC-INPUT-001", published_ids)
        self.assertIn("CSHARP-LANG-001", published_ids)
        self.assertEqual(rule_contract_findings(published, candidate), [])

    def test_published_scoped_duplicates_are_grandfathered(self):
        published = [
            ("SHARED-001", "Same published meaning.", "a.md"),
            ("SHARED-001", "Same published meaning.", "b.md"),
        ]
        self.assertEqual(rule_contract_findings(published, list(published)), [])

        reused_in_new_scope = published + [
            ("SHARED-001", "Same published meaning.", "c.md")
        ]
        self.assertIn(
            "REUSED_PUBLISHED_RULE_ID:c.md:SHARED-001",
            rule_contract_findings(published, reused_in_new_scope),
        )

    def test_new_unique_rules_are_allowed_but_new_reuse_is_rejected(self):
        published = [("RULE-001", "Published requirement.", "a.md")]
        compatible_addition = published + [
            ("RULE-002", "New optional requirement.", "b.md")
        ]
        self.assertEqual(rule_contract_findings(published, compatible_addition), [])

        reused = compatible_addition + [
            ("RULE-002", "Same new rule reused.", "c.md")
        ]
        self.assertIn(
            "DUPLICATE_NEW_RULE_ID:RULE-002",
            rule_contract_findings(published, reused),
        )

    def test_rule_contract_checker_detects_removal_and_meaning_change(self):
        published = [
            ("RULE-001", "First requirement.", "a.md"),
            ("RULE-002", "Second requirement.", "b.md"),
        ]
        removed = [("RULE-001", "First requirement.", "a.md")]
        self.assertIn(
            "MISSING_RULE:b.md:RULE-002",
            rule_contract_findings(published, removed),
        )

        changed = [
            ("RULE-001", "Changed meaning.", "a.md"),
            ("RULE-002", "Second requirement.", "b.md"),
        ]
        self.assertIn(
            "CHANGED_RULE_MEANING:a.md:RULE-001",
            rule_contract_findings(published, changed),
        )

    def test_csharp_product_rule_ids_and_meaning_are_preserved(self):
        source = self.checkpoint["csharpProductRules"]
        text = (REPO_ROOT / source["sourcePath"]).read_text(encoding="utf-8")
        actual = {
            rule_id: requirement
            for rule_id, requirement, _ in extract_rule_contracts(text, source["sourcePath"])
        }
        self.assertEqual(actual, source["rules"])
        self.assertEqual(len(actual), 10)

    def test_full_csharp_normative_standards_match_promotion_evidence_candidate(self):
        promoted_tree = git_object_sha_at(CSHARP_PROMOTION_EVIDENCE_COMMIT, CSHARP_NORMATIVE_ROOT)
        current_tree = git_object_sha_at("HEAD", CSHARP_NORMATIVE_ROOT)
        self.assertEqual(
            current_tree,
            promoted_tree,
            "stable C# normative standards changed after the independently reviewed promotion evidence candidate",
        )


if __name__ == "__main__":
    unittest.main()
