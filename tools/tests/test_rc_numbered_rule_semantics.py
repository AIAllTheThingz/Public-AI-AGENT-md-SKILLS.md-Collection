from __future__ import annotations

import re
import unittest
from collections import defaultdict

import rc_normative_rule_contracts_base as base

RULE_HEADING_PATTERN = re.compile(
    r"^### (?P<id>[A-Z][A-Z0-9-]*-\d{3})\s*$",
    re.MULTILINE,
)
FIELD_PATTERN = re.compile(r"^\*\*(?P<label>[^*\n:]+):\*\*\s*(?P<value>.*)$")
HTML_COMMENT_PATTERN = re.compile(r"<!--.*?-->", re.DOTALL)


def normalize_contract_text(text: str) -> str:
    return " ".join(text.split())


def visible_markdown(text: str) -> str:
    return HTML_COMMENT_PATTERN.sub("", text)


def extract_rule_field_contracts(
    text: str, path: str
) -> list[tuple[str, str, dict[str, str]]]:
    """Extract every visible bold-labeled behavioral field in numbered rules."""

    text = visible_markdown(text)
    matches = list(RULE_HEADING_PATTERN.finditer(text))
    contracts: list[tuple[str, str, dict[str, str]]] = []

    for index, match in enumerate(matches):
        block_start = match.end()
        block_end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        block = text[block_start:block_end]

        # A non-rule heading ends the current numbered-rule block. The next numbered
        # rule is already bounded above by `block_end`.
        next_heading = re.search(r"^#{1,3}\s+.+$", block, flags=re.MULTILINE)
        if next_heading is not None:
            block = block[: next_heading.start()]

        fields: dict[str, str] = {}
        current_label: str | None = None
        current_lines: list[str] = []

        def flush_field() -> None:
            nonlocal current_label, current_lines
            if current_label is not None:
                fields[current_label] = normalize_contract_text(" ".join(current_lines))
            current_label = None
            current_lines = []

        for raw_line in block.splitlines():
            stripped = raw_line.strip()
            field_match = FIELD_PATTERN.match(stripped)
            if field_match is not None:
                flush_field()
                current_label = normalize_contract_text(field_match.group("label")).casefold()
                initial = field_match.group("value").strip()
                current_lines = [initial] if initial else []
                continue

            if current_label is not None and stripped:
                current_lines.append(stripped)

        flush_field()
        contracts.append((path, match.group("id"), fields))

    return contracts


def published_rule_field_contracts() -> list[tuple[str, str, dict[str, str]]]:
    contracts: list[tuple[str, str, dict[str, str]]] = []
    for relative in base.git_paths_at(base.CHECKPOINT_COMMIT, ".md"):
        contracts.extend(
            extract_rule_field_contracts(
                base.git_source_at(base.CHECKPOINT_COMMIT, relative), relative
            )
        )
    return contracts


def candidate_rule_field_contracts() -> list[tuple[str, str, dict[str, str]]]:
    contracts: list[tuple[str, str, dict[str, str]]] = []
    for path in sorted(base.REPO_ROOT.rglob("*.md")):
        relative = path.relative_to(base.REPO_ROOT).as_posix()
        contracts.extend(
            extract_rule_field_contracts(path.read_text(encoding="utf-8"), relative)
        )
    return contracts


def contracts_by_key(
    contracts: list[tuple[str, str, dict[str, str]]]
) -> dict[tuple[str, str], list[dict[str, str]]]:
    result: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    for path, rule_id, fields in contracts:
        result[(path, rule_id)].append(fields)
    return dict(result)


def rule_field_contract_findings(
    published: list[tuple[str, str, dict[str, str]]],
    candidate: list[tuple[str, str, dict[str, str]]],
) -> list[str]:
    findings: list[str] = []
    expected = contracts_by_key(published)
    actual = contracts_by_key(candidate)

    for (path, rule_id), expected_occurrences in expected.items():
        if len(expected_occurrences) != 1:
            # Duplicate handling is already enforced by the base numbered-rule gate.
            continue
        actual_occurrences = actual.get((path, rule_id), [])
        if len(actual_occurrences) != 1:
            continue

        expected_fields = expected_occurrences[0]
        actual_fields = actual_occurrences[0]
        for label, expected_value in sorted(expected_fields.items()):
            if label not in actual_fields:
                findings.append(f"RULE_FIELD_MISSING:{path}:{rule_id}:{label}")
            elif actual_fields[label] != expected_value:
                findings.append(f"RULE_FIELD_CHANGED:{path}:{rule_id}:{label}")

    return sorted(findings)


class ReleaseCandidateNumberedRuleSemanticTests(unittest.TestCase):
    def test_every_published_numbered_rule_field_semantic_is_preserved(self):
        published = published_rule_field_contracts()
        candidate = candidate_rule_field_contracts()
        self.assertGreater(len(published), 100)
        sec_input = [
            fields
            for path, rule_id, fields in published
            if path == "disciplines/application-security/AGENTS.md"
            and rule_id == "SEC-INPUT-001"
        ]
        self.assertEqual(len(sec_input), 1)
        self.assertIn("requirement", sec_input[0])
        self.assertIn("evidence", sec_input[0])
        self.assertEqual(rule_field_contract_findings(published, candidate), [])

    def test_scope_exception_and_evidence_changes_are_detected(self):
        published_text = """
### SAMPLE-001

**Requirement:** Preserve the published behavior.

**Applicability:** Applies to trusted and untrusted callers.

**Exceptions:** Only an explicitly approved exception is allowed.

**Expected evidence:** Record positive and negative tests.
"""
        compatible_text = published_text.replace(
            "\n\n**Expected evidence:**",
            "\n\n\n**Expected evidence:**",
        )
        changed_applicability = compatible_text.replace(
            "Applies to trusted and untrusted callers.",
            "Applies only to trusted callers.",
        )
        broadened_exception = compatible_text.replace(
            "Only an explicitly approved exception is allowed.",
            "Any documented exception is allowed.",
        )
        removed_evidence = compatible_text.replace(
            "\n\n**Expected evidence:** Record positive and negative tests.",
            "",
        )

        published = extract_rule_field_contracts(published_text, "sample.md")
        self.assertEqual(
            rule_field_contract_findings(
                published,
                extract_rule_field_contracts(compatible_text, "sample.md"),
            ),
            [],
        )
        self.assertIn(
            "RULE_FIELD_CHANGED:sample.md:SAMPLE-001:applicability",
            rule_field_contract_findings(
                published,
                extract_rule_field_contracts(changed_applicability, "sample.md"),
            ),
        )
        self.assertIn(
            "RULE_FIELD_CHANGED:sample.md:SAMPLE-001:exceptions",
            rule_field_contract_findings(
                published,
                extract_rule_field_contracts(broadened_exception, "sample.md"),
            ),
        )
        self.assertIn(
            "RULE_FIELD_MISSING:sample.md:SAMPLE-001:expected evidence",
            rule_field_contract_findings(
                published,
                extract_rule_field_contracts(removed_evidence, "sample.md"),
            ),
        )

    def test_html_comments_cannot_preserve_hidden_rule_fields(self):
        published_text = """
### SAMPLE-001

**Requirement:** Preserve the published behavior.

**Expected evidence:** Record positive and negative tests.
"""
        candidate_text = """
### SAMPLE-001

**Requirement:** Preserve the published behavior.

<!--
**Expected evidence:** Record positive and negative tests.
-->
"""
        published = extract_rule_field_contracts(published_text, "sample.md")
        candidate = extract_rule_field_contracts(candidate_text, "sample.md")
        self.assertIn(
            "RULE_FIELD_MISSING:sample.md:SAMPLE-001:expected evidence",
            rule_field_contract_findings(published, candidate),
        )
        self.assertNotIn("expected evidence", candidate[0][2])


if __name__ == "__main__":
    unittest.main()
