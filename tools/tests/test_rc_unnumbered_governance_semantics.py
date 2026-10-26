from __future__ import annotations

import json
import re
import unittest
from collections import Counter, defaultdict

import rc_normative_rule_contracts_base as base
from helpers import require_git_history

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
CHECKPOINT_INVENTORY_PATH = (
    base.REPO_ROOT / "releases" / "compatibility" / "0.10.0-checkpoint.json"
)

# These stable root documents are deliberately forward-moving status/index
# surfaces rather than durable policy authorities. Their current-version,
# readiness, and roadmap prose must advance after publication without turning
# every version bump into a compatibility break. Normative root documents such
# as SECURITY.md, CONTRIBUTING.md, MAINTAINERS.md, MATURITY_POLICY.md,
# RELEASE_POLICY.md, and the PR template remain derived from the authenticated
# stable-root checkpoint and protected semantically.
FORWARD_MOVING_INFORMATIONAL_ROOT_PATHS = frozenset(
    {
        "README.md",
        "CATALOG.md",
        "CHANGELOG.md",
        "ROADMAP.md",
    }
)

# This paragraph is deliberately forward-moving release-state narrative, not a
# stable governance obligation.  The immutable v0.10.0 copy said the next
# intended publication was v0.10.0; after publication the correct forward-only
# text names 1.0.0-rc.1.  Keep the rest of the Pre-1.0 policy protected.
MUTABLE_ROOT_NARRATIVE = {
    (
        "RELEASE_POLICY.md",
        "pre-1.0 policy",
    ): "The repository originally prepared ",
}

# Additive governance is generally allowed. Candidate-only language becomes
# incompatible only when it introduces a permission/exception/override path that
# can weaken the published control surface.
_PERMISSION_EXPANSION_PATTERNS = (
    re.compile(
        r"\b(?:may|can|allowed|permitted)\b.*"
        r"\b(?:without|skip|bypass|override|waiv\w*|omit|ignore|circumvent)\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(?:exception|exceptions|override|waiver|waivers)\b.*"
        r"\b(?:may|can|allowed|permitted|bypass|skip|override|waiv\w*)\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(?:need not|does not require|do not require|not required|"
        r"no longer required|optional)\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\bwithout\b.*"
        r"\b(?:approval|authorization|review|evidence|validation|testing|"
        r"security|authentication)\b",
        re.IGNORECASE,
    ),
)
_RESTRICTIVE_DEONTIC_PATTERNS = (
    re.compile(
        r"\b(?:is|are|was|were|be)(?:\s+not|n't|\s+no\s+longer)\s+optional\b"
    ),
    re.compile(
        r"\b(?:must|shall|may|can|do|does|did)(?:\s+not|n't)\s+"
        r"(?:be\s+)?(?:skipp\w*|omit\w*|waiv\w*)\b"
    ),
    re.compile(
        r"\bno\s+(?:exceptions?|overrides?|waivers?)\b.*"
        r"\b(?:permitted|allowed|available|applicable)\b"
    ),
    re.compile(
        r"\b(?:exceptions?|overrides?|waivers?)\b.*"
        r"\b(?:is|are|be)(?:\s+not|n't)\s+"
        r"(?:permitted|allowed|available|applicable)\b"
    ),
)
_DEOBLIGATION_PATTERNS = (
    re.compile(
        r"\b(?:is|are|was|were|be)(?:\s+not|n't|\s+no\s+longer)\s+"
        r"(?:mandatory|required|compulsory|obligatory|necessary)\b"
    ),
    re.compile(r"\bneed(?:\s+not|n't)\b"),
    re.compile(r"\b(?:do|does|did)(?:\s+not|n't)\s+have\s+to\b"),
    re.compile(
        r"\b(?:may|can)\s+(?:be\s+)?(?:skipp\w*|omit\w*|waiv\w*)\b"
    ),
)

# A blanket `unless` detector would also reject genuinely additive restrictions
# such as `Do not merge unless independent review succeeds`. Instead compare the
# obligation before the escape clause with published obligations in the same
# section. If the new statement restates an existing obligation and then adds
# `unless` / `except when` / `except if`, it is an exception to the published
# control rather than a new restrictive control.
_ESCAPE_CLAUSE = re.compile(
    r"\b(?:unless|except\s+(?:if|when|where))\b",
    re.IGNORECASE,
)
_OBLIGATION_MARKER = re.compile(
    r"\b(?:must|shall|required|require|only|may\s+not|must\s+not|"
    r"shall\s+not|cannot|do\s+not|no\s+)\b",
    re.IGNORECASE,
)
_STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "before",
    "by",
    "for",
    "from",
    "in",
    "is",
    "it",
    "of",
    "on",
    "or",
    "the",
    "to",
    "when",
    "with",
}
_OBLIGATION_RESTATEMENT_TOKENS = {
    "mandatory",
    "must",
    "perform",
    "requir",
    "require",
    "shall",
}


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


def _is_permission_expanding_statement(statement: str) -> bool:
    whitespace_normalized = " ".join(statement.split()).casefold()
    if any(pattern.search(whitespace_normalized) for pattern in _DEOBLIGATION_PATTERNS):
        return True
    if any(pattern.search(whitespace_normalized) for pattern in _RESTRICTIVE_DEONTIC_PATTERNS):
        return False
    normalized = normalize_contract_text(statement)
    return any(pattern.search(normalized) for pattern in _PERMISSION_EXPANSION_PATTERNS)


def extract_unnumbered_governance_contracts(
    text: str,
    path: str,
) -> Counter[tuple[str, str, str]]:
    source = text
    text = base.rendered_markdown(text)
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

    # Also record permission-expanding bullets under any heading of the source
    # text so a candidate-only escape hatch reaches the findings gate.
    section = ""
    for line in source.splitlines():
        heading = re.match(r"^\s*#{1,6}\s+(.+?)\s*$", line)
        if heading is not None:
            section = " ".join(heading.group(1).split()).casefold()
            continue

        bullet = re.match(r"^\s*[-*+]\s+(.+?)\s*$", line)
        if bullet is None or not section:
            continue
        statement = bullet.group(1)
        if _is_permission_expanding_statement(statement):
            contracts[(path, section, statement)] += 1

    return contracts


def _stable_root_contracts(text: str, path: str) -> Counter[tuple[str, str, str]]:
    contracts = extract_unnumbered_governance_contracts(text, path)
    for (contract_path, section, statement), count in list(contracts.items()):
        prefix = MUTABLE_ROOT_NARRATIVE.get((contract_path, section))
        if prefix is not None and statement.startswith(prefix):
            del contracts[(contract_path, section, statement)]
    return contracts


def _published_normative_stable_root_paths() -> tuple[str, ...]:
    """Derive durable normative Markdown roots from the authenticated stable-root inventory."""
    checkpoint = json.loads(CHECKPOINT_INVENTORY_PATH.read_text(encoding="utf-8"))
    stable_roots = checkpoint["stablePathGroups"]["root"]
    normative: list[str] = []
    for relative in stable_roots:
        if not relative.endswith(".md"):
            continue
        if relative in FORWARD_MOVING_INFORMATIONAL_ROOT_PATHS:
            continue
        published_text = base.git_source_at(base.CHECKPOINT_COMMIT, relative)
        if _stable_root_contracts(published_text, relative):
            normative.append(relative)
    return tuple(normative)


def _root_governance_contracts_at_checkpoint() -> Counter[tuple[str, str, str]]:
    contracts: Counter[tuple[str, str, str]] = Counter()
    for relative in _published_normative_stable_root_paths():
        contracts.update(
            _stable_root_contracts(
                base.git_source_at(base.CHECKPOINT_COMMIT, relative),
                relative,
            )
        )
    return contracts


def _candidate_root_governance_contracts() -> Counter[tuple[str, str, str]]:
    contracts: Counter[tuple[str, str, str]] = Counter()
    for relative in _published_normative_stable_root_paths():
        contracts.update(
            _stable_root_contracts(
                (base.REPO_ROOT / relative).read_text(encoding="utf-8"),
                relative,
            )
        )
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
    # Stable root policies are protected through the reviewed root projection.
    contracts.update(_root_governance_contracts_at_checkpoint())
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
    contracts.update(_candidate_root_governance_contracts())
    return contracts


def _stem_token(token: str) -> str:
    for suffix in ("ing", "ed", "es", "s"):
        if len(token) > len(suffix) + 3 and token.endswith(suffix):
            return token[: -len(suffix)]
    return token


def _semantic_tokens(text: str) -> set[str]:
    return {
        _stem_token(token)
        for token in re.findall(r"[a-z0-9]+", text.casefold())
        if token not in _STOPWORDS and len(token) > 2
    }


def _obligation_subject_action_tokens(text: str) -> set[str]:
    return _semantic_tokens(text) - _OBLIGATION_RESTATEMENT_TOKENS


def _conditional_escape_weakens_published(
    statement: str,
    published_peers: list[str],
) -> bool:
    match = _ESCAPE_CLAUSE.search(statement)
    if match is None:
        return False

    prefix = statement[: match.start()].strip(" ,;:-")
    if not prefix or _OBLIGATION_MARKER.search(prefix) is None:
        return False

    prefix_tokens = _obligation_subject_action_tokens(prefix)
    if len(prefix_tokens) < 2:
        return False

    for peer in published_peers:
        if _OBLIGATION_MARKER.search(peer) is None:
            continue
        peer_tokens = _obligation_subject_action_tokens(peer)
        if not peer_tokens:
            continue
        overlap = len(prefix_tokens & peer_tokens) / len(prefix_tokens)
        if overlap >= 0.6:
            return True

    return False


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

    peers: dict[tuple[str, str], list[str]] = defaultdict(list)
    for path, section, statement in published:
        peers[(path, section)].append(statement)

    for (path, section, statement), count in (candidate - published).items():
        if count <= 0:
            continue
        if _is_permission_expanding_statement(
            statement
        ) or _conditional_escape_weakens_published(
            statement,
            peers.get((path, section), []),
        ):
            findings.append(
                "UNNUMBERED_GOVERNANCE_WEAKENING_ADDED:"
                f"{path}:{section}:{statement}"
            )

    return sorted(set(findings))


class ReleaseCandidateUnnumberedGovernanceSemanticTests(unittest.TestCase):
    def test_published_unnumbered_governance_controls_are_preserved(self):
        require_git_history(base.CHECKPOINT_COMMIT)
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

    def test_html_comments_cannot_preserve_hidden_governance_controls(self):
        published_text = """
## Decision gates

- Stop when authorization is absent for state-changing work.
"""
        candidate_text = """
## Decision gates

<!--
- Stop when authorization is absent for state-changing work.
-->
"""
        published = extract_unnumbered_governance_contracts(
            published_text, "governance/sample.md"
        )
        candidate = extract_unnumbered_governance_contracts(
            candidate_text, "governance/sample.md"
        )
        self.assertTrue(unnumbered_contract_findings(published, candidate))
        self.assertEqual(candidate, Counter())


if __name__ == "__main__":
    unittest.main()
