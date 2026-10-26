from __future__ import annotations

import json
import re
import subprocess
import unittest
from collections import defaultdict

from helpers import REPO_ROOT, require_git_history, sha256_utf8_text_file

CANDIDATE_INVENTORY = REPO_ROOT / "releases" / "compatibility" / "1.0.0-rc.1.json"
RULE_CHECKPOINT = REPO_ROOT / "releases" / "compatibility" / "0.10.0-rule-contracts.json"
RULE_CHECKPOINT_SHA256 = "5f3b7a7ddd28de5a44b45f96998d7acffb2c287bad4c7699e21561a869e50c95"
CHECKPOINT_COMMIT = "83c73f3ab9a049ff2321d463164fcf98fb453a9c"
CSHARP_PROMOTION_EVIDENCE_COMMIT = "2f6d39288e5c1a7d416e62cd75651b3d6da48dfe"
CSHARP_NORMATIVE_ROOT = "languages/csharp/standards"
HTML_COMMENT_PATTERN = re.compile(r"<!--.*?-->", re.DOTALL)
_FENCE_OPEN_PATTERN = re.compile(r"^[ \t]{0,3}(?P<marker>`{3,}|~{3,})")
_ATX_HEADING_PATTERN = re.compile(r"^#{1,6}(?:[ \t]+|$)")
_LIST_MARKER_PATTERN = re.compile(r"^(?:[-+*]|\d{1,9}[.)])(?:[ \t]+|$)")
_SETEXT_OR_RULE_PATTERN = re.compile(r"^(?:=+|-+|(?:\*\s*){3,}|(?:_\s*){3,})[ \t]*$")
RULE_PATTERN = re.compile(
    r"^### (?P<id>[A-Z][A-Z0-9-]*-\d{3})\s*$\n\n"
    r"\*\*Requirement:\*\* (?P<requirement>[^\n]+)$",
    re.MULTILINE,
)


def git_output(*args: str) -> str:
    completed = subprocess.run(
        ["git", "-C", str(REPO_ROOT), *args],
        text=True,
        encoding="utf-8",
        capture_output=True,
        check=False,
    )
    if completed.returncode != 0:
        raise AssertionError(completed.stderr.strip() or "git command failed")
    return completed.stdout


def git_source_at(revision: str, relative: str) -> str:
    require_git_history(revision)
    return git_output("show", f"{revision}:{relative}")


def git_paths_at(revision: str, suffix: str) -> list[str]:
    paths = git_output("ls-tree", "-r", "--name-only", revision).splitlines()
    return sorted(path for path in paths if path.endswith(suffix))


def git_object_sha_at(revision: str, relative: str) -> str:
    return git_output("rev-parse", f"{revision}:{relative}").strip()


def _indent_columns(text: str) -> int:
    columns = 0
    for character in text:
        if character == " ":
            columns += 1
        elif character == "\t":
            columns += 4 - (columns % 4)
        else:
            break
    return columns


def _line_break(raw_line: str) -> str:
    return "\n" if raw_line.endswith(("\n", "\r")) else ""


def _opens_or_continues_paragraph(candidate: str) -> bool:
    """Return whether a following indented line would interrupt paragraph/list text."""

    stripped = candidate.lstrip(" \t")
    if not stripped:
        return False
    if _ATX_HEADING_PATTERN.match(stripped):
        return False
    if stripped.startswith(">"):
        return False
    if _SETEXT_OR_RULE_PATTERN.match(stripped):
        return False
    # List content owns ambiguous indentation ahead of indented-code parsing.
    if _LIST_MARKER_PATTERN.match(stripped):
        return True
    return True


def rendered_markdown(text: str) -> str:
    """Project Markdown to operative source text for compatibility scanners.

    Compatibility contracts describe operative rendered guidance, not text hidden
    in HTML comments, fenced code, or CommonMark indented code blocks. Every
    Markdown semantic extractor (numbered rules, rule fields, unnumbered
    governance, templates, and skill routers) uses this one projection for both
    the immutable published source and the candidate, so a published obligation
    cannot survive comparison merely by moving into a non-operative region.

    This intentionally is not a full Markdown renderer. Four-column indentation
    begins code when it does not interrupt an active paragraph/list continuation;
    headings and other block boundaries therefore permit indented code without
    requiring an extra blank line.
    """

    without_comments = HTML_COMMENT_PATTERN.sub("", text)
    output: list[str] = []
    fence_character: str | None = None
    fence_length = 0
    in_indented_code = False
    paragraph_or_list_open = False

    for raw_line in without_comments.splitlines(keepends=True):
        candidate = raw_line.rstrip("\r\n")
        blank = candidate.strip(" \t") == ""
        leading_columns = _indent_columns(candidate)
        eligible_fence_indent = leading_columns <= 3
        stripped = candidate.lstrip(" \t") if eligible_fence_indent else candidate

        if fence_character is not None:
            if eligible_fence_indent:
                closing = re.match(
                    rf"^{re.escape(fence_character)}{{{fence_length},}}[ \t]*$",
                    stripped,
                )
                if closing is not None:
                    fence_character = None
                    fence_length = 0
            output.append(_line_break(raw_line))
            paragraph_or_list_open = False
            continue

        if in_indented_code:
            if blank or leading_columns >= 4:
                output.append(_line_break(raw_line))
                paragraph_or_list_open = False
                continue
            in_indented_code = False

        match = _FENCE_OPEN_PATTERN.match(candidate)
        if match is not None:
            marker = match.group("marker")
            fence_character = marker[0]
            fence_length = len(marker)
            output.append(_line_break(raw_line))
            paragraph_or_list_open = False
            continue

        if leading_columns >= 4 and not paragraph_or_list_open and not blank:
            in_indented_code = True
            output.append(_line_break(raw_line))
            paragraph_or_list_open = False
            continue

        output.append(raw_line)
        if blank:
            paragraph_or_list_open = False
        elif leading_columns < 4:
            paragraph_or_list_open = _opens_or_continues_paragraph(candidate)

    return "".join(output)


def extract_rule_contracts(text: str, path: str) -> list[tuple[str, str, str]]:
    visible_text = rendered_markdown(text)
    return [
        (match.group("id"), match.group("requirement").strip(), path)
        for match in RULE_PATTERN.finditer(visible_text)
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


def occurrence_paths_by_id(contracts: list[tuple[str, str, str]]) -> dict[str, list[str]]:
    result: dict[str, list[str]] = defaultdict(list)
    for rule_id, _, path in contracts:
        result[rule_id].append(path)
    return dict(result)


def rule_contract_findings(
    published: list[tuple[str, str, str]],
    candidate: list[tuple[str, str, str]],
) -> list[str]:
    findings: list[str] = []
    expected_by_key = occurrences_by_key(published)
    actual_by_key = occurrences_by_key(candidate)
    expected_occurrences = occurrence_paths_by_id(published)
    actual_occurrences = occurrence_paths_by_id(candidate)

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
    # published ID to acquire a new scope, and do not allow a new ID to appear more
    # than once even when every occurrence is in the same file.
    for rule_id, candidate_occurrences in actual_occurrences.items():
        published_occurrences = expected_occurrences.get(rule_id)
        if published_occurrences is not None:
            published_paths = set(published_occurrences)
            for extra_path in sorted(set(candidate_occurrences) - published_paths):
                findings.append(f"REUSED_PUBLISHED_RULE_ID:{extra_path}:{rule_id}")
        elif len(candidate_occurrences) > 1:
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
        self.assertEqual(sha256_utf8_text_file(RULE_CHECKPOINT), RULE_CHECKPOINT_SHA256)
        self.assertEqual(self.checkpoint["releaseVersion"], "0.10.0")
        self.assertEqual(self.checkpoint["tag"], "v0.10.0")
        self.assertEqual(self.checkpoint["sourceCommit"], CHECKPOINT_COMMIT)
        self.assertIn("grandfathered", self.checkpoint["coverageRule"])

    def test_every_published_numbered_rule_occurrence_and_meaning_is_preserved(self):
        require_git_history(CHECKPOINT_COMMIT)
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

        same_file_reuse = compatible_addition + [
            ("RULE-003", "New optional requirement.", "same.md"),
            ("RULE-003", "New optional requirement.", "same.md"),
        ]
        self.assertIn(
            "DUPLICATE_NEW_RULE_ID:RULE-003",
            rule_contract_findings(published, same_file_reuse),
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

    def test_html_comments_do_not_preserve_numbered_rules(self):
        visible = """
### GOV-SAMPLE-001

**Requirement:** Preserve this published requirement.
""".lstrip()
        hidden = """
<!--
### GOV-SAMPLE-001

**Requirement:** Preserve this published requirement.
-->
""".lstrip()
        published = extract_rule_contracts(visible, "sample.md")
        candidate = extract_rule_contracts(hidden, "sample.md")
        self.assertEqual(candidate, [])
        self.assertIn(
            "MISSING_RULE:sample.md:GOV-SAMPLE-001",
            rule_contract_findings(published, candidate),
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
        require_git_history(CSHARP_PROMOTION_EVIDENCE_COMMIT)
        promoted_tree = git_object_sha_at(CSHARP_PROMOTION_EVIDENCE_COMMIT, CSHARP_NORMATIVE_ROOT)
        current_tree = git_object_sha_at("HEAD", CSHARP_NORMATIVE_ROOT)
        self.assertEqual(
            current_tree,
            promoted_tree,
            "stable C# normative standards changed after the independently reviewed promotion evidence candidate",
        )


if __name__ == "__main__":
    unittest.main()
