from __future__ import annotations

import re
import unittest
from collections import Counter

import rc_normative_rule_contracts_base as base

NUMBERED_RULE_HEADING = re.compile(
    r"^### [A-Z][A-Z0-9-]*-\d{3}\s*$",
    re.MULTILINE,
)
H2_HEADING = re.compile(r"^## (?P<title>[^\n]+)\s*$", re.MULTILINE)
H3_OR_HIGHER_HEADING = re.compile(r"^#{1,3}\s+.+$", re.MULTILINE)
BEHAVIOR_SECTION_MARKERS = (
    "decision",
    "exception",
    "completion",
    "required",
    "prohibited",
    "authorization",
    "approval",
    "boundary",
    "trigger",
    "scope",
    "precedence",
    "safety",
)
NORMATIVE_PATTERN = re.compile(
    r"\b(?:must(?:\s+not)?|shall(?:\s+not)?|may\s+not|cannot|can't|"
    r"do\s+not|does\s+not|is\s+not|are\s+not|required|requires?|"
    r"prohibited|only|needs?\s+to)\b",
    re.IGNORECASE,
)
IMPERATIVE_PREFIXES = (
    "stop ", "preserve ", "record ", "retain ", "ensure ", "verify ",
    "validate ", "review ", "classify ", "reassess ", "re-review ",
    "use ", "apply ", "include ", "identify ", "document ", "obtain ",
    "provide ", "protect ", "treat ", "report ", "update ", "keep ",
)
TABLE_SEPARATOR_CELL = re.compile(r"^:?-{3,}:?$")


def normalize_contract_text(text: str) -> str:
    text = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", text)
    text = re.sub(r"[`*_]+", "", text)
    return " ".join(text.split()).strip()


def _without_numbered_rule_blocks(text: str) -> str:
    matches = list(NUMBERED_RULE_HEADING.finditer(text))
    if not matches:
        return text
    pieces: list[str] = []
    cursor = 0
    for match in matches:
        pieces.append(text[cursor : match.start()])
        tail = text[match.end() :]
        next_heading = H3_OR_HIGHER_HEADING.search(tail)
        cursor = len(text) if next_heading is None else match.end() + next_heading.start()
    pieces.append(text[cursor:])
    return "".join(pieces)


def _section_is_behavior_defining(title: str) -> bool:
    normalized = normalize_contract_text(title).casefold()
    return any(marker in normalized for marker in BEHAVIOR_SECTION_MARKERS)


def _normalize_table_row(line: str) -> str | None:
    cells = [normalize_contract_text(cell) for cell in line.strip().strip("|").split("|")]
    if not cells or all(not cell for cell in cells):
        return None
    if all(TABLE_SEPARATOR_CELL.fullmatch(cell.replace(" ", "")) for cell in cells):
        return None
    return "table:" + " | ".join(cells)


def _section_statements(block: str) -> list[str]:
    statements: list[str] = []
    paragraph: list[str] = []

    def flush_paragraph() -> None:
        if paragraph:
            statements.append(normalize_contract_text(" ".join(paragraph)))
            paragraph.clear()

    for raw_line in block.splitlines():
        stripped = raw_line.strip()
        if not stripped:
            flush_paragraph()
            continue
        if stripped.startswith("```"):
            flush_paragraph()
            continue
        if stripped.startswith("|"):
            flush_paragraph()
            table_row = _normalize_table_row(stripped)
            if table_row is not None:
                statements.append(table_row)
            continue
        if stripped.startswith(("- ", "* ")):
            flush_paragraph()
            statements.append(normalize_contract_text(stripped[2:]))
            continue
        if re.match(r"^\d+[.)]\s+", stripped):
            flush_paragraph()
            statements.append(
                "ordered:" + normalize_contract_text(re.sub(r"^\d+[.)]\s+", "", stripped))
            )
            continue
        if stripped.startswith("#"):
            flush_paragraph()
            continue
        paragraph.append(stripped)

    flush_paragraph()
    return [statement for statement in statements if statement]


def _statement_is_behavior_defining(statement: str) -> bool:
    if statement.startswith(("table:", "ordered:")):
        return True
    normalized = normalize_contract_text(statement).casefold()
    return (
        normalized.startswith("no ")
        or normalized.startswith(IMPERATIVE_PREFIXES)
        or NORMATIVE_PATTERN.search(normalized) is not None
    )


def extract_unnumbered_governance_contracts(
    text: str,
    path: str,
) -> Counter[tuple[str, str, str]]:
    text = _without_numbered_rule_blocks(text)
    matches = list(H2_HEADING.finditer(text))
    contracts: Counter[tuple[str, str, str]] = Counter()

    for index, match in enumerate(matches):
        title = normalize_contract_text(match.group("title"))
        block_start = match.end()
        block_end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        block = text[block_start:block_end]
        section_is_behavior_defining = _section_is_behavior_defining(title)
        for statement in _section_statements(block):
            if section_is_behavior_defining or _statement_is_behavior_defining(statement):
                contracts[(path, title.casefold(), statement)] += 1

    return contracts


def published_contracts() -> Counter[tuple[str, str, str]]:
    contracts: Counter[tuple[str, str, str]] = Counter()
    for relative in base.git_paths_at(base.CHECKPOINT_COMMIT, ".md"):
        if not relative.startswith("governance/") or relative.count("/") != 1:
            continue
        contracts.update(
            extract_unnumbered_governance_contracts(
                base.git_source_at(base.CHECKPOINT_COMMIT, relative), relative
            )
        )
    return contracts


def candidate_contracts() -> Counter[tuple[str, str, str]]:
    contracts: Counter[tuple[str, str, str]] = Counter()
    for path in sorted((base.REPO_ROOT / "governance").glob("*.md")):
        relative = path.relative_to(base.REPO_ROOT).as_posix()
        contracts.update(
            extract_unnumbered_governance_contracts(
                path.read_text(encoding="utf-8"), relative
            )
        )
    return contracts


def unnumbered_contract_findings(
    published: Counter[tuple[str, str, str]],
    candidate: Counter[tuple[str, str, str]],
) -> list[str]:
    findings: list[str] = []
    for (path, section, statement), expected_count in published.items():
        actual_count = candidate.get((path, section, statement), 0)
        if actual_count < expected_count:
            findings.append(
                f"UNNUMBERED_GOVERNANCE_CONTROL_CHANGED:{path}:{section}:{statement}"
            )
    return sorted(findings)


class ReleaseCandidateUnnumberedGovernanceSemanticTests(unittest.TestCase):
    def test_published_unnumbered_governance_controls_are_preserved(self):
        published = published_contracts()
        candidate = candidate_contracts()
        self.assertGreater(sum(published.values()), 10)

        organization_decision_gates = [
            statement for path, section, statement in published
            if path == "governance/ORGANIZATION_CONTRACT.md" and section == "decision gates"
        ]
        self.assertGreaterEqual(len(organization_decision_gates), 3)
        self.assertTrue(
            any("authorization is absent" in statement.casefold() for statement in organization_decision_gates)
        )

        exception_decision_gates = [
            statement for path, section, statement in published
            if path == "governance/EXCEPTION_PROCESS.md" and section == "decision gates"
        ]
        self.assertEqual(len(exception_decision_gates), 3)
        self.assertTrue(
            any(statement.casefold().startswith("no closure until the deviation is removed") for statement in exception_decision_gates)
        )

        decision_matrix_rows = [
            statement for path, section, statement in published
            if path == "governance/GOVERNANCE_DECISION_MATRIX.md"
            and section == "purpose" and statement.startswith("table:")
        ]
        self.assertTrue(
            any("independent review" in statement.casefold() and "required" in statement.casefold() for statement in decision_matrix_rows),
            "risk-based independent-review requirements in the Purpose decision matrix must be immutable",
        )
        self.assertEqual(unnumbered_contract_findings(published, candidate), [])

    def test_normative_content_outside_heading_markers_is_detected(self):
        published_text = """
## Separation of duties

The agent is not the human approver.

## Purpose

| Risk | Independent review |
|---|---|
| High | required |
| Critical | multiple accountable reviewers |
"""
        published = extract_unnumbered_governance_contracts(
            published_text, "governance/sample.md"
        )
        self.assertIn(
            (
                "governance/sample.md",
                "separation of duties",
                "The agent is not the human approver.",
            ),
            published,
        )
        self.assertIn(
            ("governance/sample.md", "purpose", "table:High | required"),
            published,
        )

        removed_separation = published_text.replace(
            "The agent is not the human approver.\n", ""
        )
        removed_high_review = published_text.replace("| High | required |\n", "")
        for candidate_text in (removed_separation, removed_high_review):
            with self.subTest(candidate=candidate_text):
                self.assertTrue(
                    unnumbered_contract_findings(
                        published,
                        extract_unnumbered_governance_contracts(
                            candidate_text, "governance/sample.md"
                        ),
                    )
                )

    def test_decision_exception_and_completion_regressions_are_detected(self):
        published_text = """
## Decision gates

- No closure until the deviation is removed or replaced by an approved permanent policy change.
- Stop when authorization is absent for state-changing work.

## Exceptions and prohibited shortcuts

No exception may override genuine authorization and accountable human approval.

## Completion boundary

The adopting repository must implement, validate, review, and record the applicable controls.
"""
        removed_negative_gate = published_text.replace(
            "- No closure until the deviation is removed or replaced by an approved permanent policy change.\n", ""
        )
        removed_decision = published_text.replace(
            "- Stop when authorization is absent for state-changing work.\n", ""
        )
        weakened_exception = published_text.replace(
            "No exception may override genuine authorization and accountable human approval.",
            "Exceptions may override authorization when documented.",
        )
        removed_completion = published_text.replace(
            "The adopting repository must implement, validate, review, and record the applicable controls.",
            "The adopting repository can consider the applicable controls.",
        )

        published = extract_unnumbered_governance_contracts(
            published_text, "governance/sample.md"
        )
        for candidate_text in (
            removed_negative_gate,
            removed_decision,
            weakened_exception,
            removed_completion,
        ):
            with self.subTest(candidate=candidate_text):
                findings = unnumbered_contract_findings(
                    published,
                    extract_unnumbered_governance_contracts(
                        candidate_text, "governance/sample.md"
                    ),
                )
                self.assertTrue(findings)


if __name__ == "__main__":
    unittest.main()
