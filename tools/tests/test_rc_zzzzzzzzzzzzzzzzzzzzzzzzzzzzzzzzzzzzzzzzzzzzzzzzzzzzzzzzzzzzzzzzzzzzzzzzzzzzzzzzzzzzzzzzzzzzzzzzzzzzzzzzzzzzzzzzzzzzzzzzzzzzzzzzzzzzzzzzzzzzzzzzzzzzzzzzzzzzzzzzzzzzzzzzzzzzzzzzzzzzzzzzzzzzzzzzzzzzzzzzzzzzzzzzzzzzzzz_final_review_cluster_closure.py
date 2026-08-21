from __future__ import annotations

import ast
import re
import unittest
from collections import defaultdict
from pathlib import Path

import test_rc_numbered_rule_semantics as numbered
import test_rc_unnumbered_governance_semantics as unnumbered


def _load_overlay(suffix: str):
    matches = sorted(Path(__file__).parent.glob(f"test_rc_*{suffix}.py"))
    if len(matches) != 1:
        raise RuntimeError(f"expected exactly one RC overlay for {suffix!r}")
    return __import__(matches[0].stem)


expr = _load_overlay("_returned_sink_alias_expression_closure")
terminal = _load_overlay("_pr71_terminal_closure")
# Ensure the reviewed mutable-root projection is active even when this module is
# run directly rather than imported through full unittest discovery.
_load_overlay("_root_governance_projection_reuse")


# ---------------------------------------------------------------------------
# Starred RHS unpacking in static destructuring.
#
# `maker, = (*[ToolResult.from_findings],)` evaluates the starred iterable and
# then splices its elements into the surrounding tuple before assignment. The
# prior shape walker treated ast.Starred as one opaque value, losing constructor
# identity. Flatten statically known tuple/list starred operands in evaluation
# order while leaving dynamic starred iterables conservative.


def _evaluate_static_shape_with_starred_rhs(
    node: ast.AST,
    env: dict[str, str],
) -> tuple[tuple[str, list[object] | None], dict[str, str]]:
    if isinstance(node, (ast.Tuple, ast.List)):
        children: list[object] = []
        after = dict(env)
        for element in node.elts:
            if isinstance(element, ast.Starred) and isinstance(
                element.value,
                (ast.Tuple, ast.List),
            ):
                nested, after = _evaluate_static_shape_with_starred_rhs(
                    element.value,
                    after,
                )
                _state, nested_children = nested
                if nested_children is None:
                    # This should not occur for a literal tuple/list, but keep a
                    # conservative single non-alias element if the shape cannot
                    # be proven rather than fabricating constructor identity.
                    children.append((terminal._NO, None))
                else:
                    children.extend(nested_children)
                continue

            child, after = _evaluate_static_shape_with_starred_rhs(element, after)
            children.append(child)

        return (terminal._NO, children), after

    if isinstance(node, ast.Starred):
        # A nested static starred sequence is flattened by its parent. A direct
        # starred node whose value is not a static sequence remains conservative.
        if isinstance(node.value, (ast.Tuple, ast.List)):
            return _evaluate_static_shape_with_starred_rhs(node.value, env)
        _ignored_state, after = expr._eval_expr(node.value, env)
        return (terminal._NO, None), after

    state, after = expr._eval_expr(node, env)
    return (state, None), after


terminal._evaluate_static_shape = _evaluate_static_shape_with_starred_rhs


# ---------------------------------------------------------------------------
# Candidate-only numbered-rule fields.
#
# Do not rely exclusively on a small label vocabulary. Expand obvious escape-
# hatch spellings such as exemption, and also inspect the candidate-only field
# value so a neutral label like `Notes:` cannot hide `may be skipped` semantics.


_previous_rule_findings = numbered.rule_field_contract_findings
_previous_permission_expansion_classifier = (
    terminal._is_permission_expanding_statement
)

_EXTRA_ESCAPE_LABEL_MARKERS = (
    "exempt",
    "dispensation",
    "carve-out",
    "carveout",
)
_previous_label_classifier = terminal._is_candidate_only_behavioral_field


def _candidate_only_behavioral_label(label: str) -> bool:
    normalized = numbered.normalize_contract_text(label).casefold()
    return _previous_label_classifier(label) or any(
        marker in normalized for marker in _EXTRA_ESCAPE_LABEL_MARKERS
    )


terminal._is_candidate_only_behavioral_field = _candidate_only_behavioral_label


def _is_permission_expanding_statement(value: str) -> bool:
    normalized = numbered.normalize_contract_text(value).casefold()
    return _previous_permission_expansion_classifier(value) or bool(
        re.search(r"\bno\s+longer\s+mandatory\b", normalized)
    )


terminal._is_permission_expanding_statement = _is_permission_expanding_statement


def _candidate_only_rule_field_findings(
    published: list[tuple[str, str, dict[str, str]]],
    candidate: list[tuple[str, str, dict[str, str]]],
) -> list[str]:
    findings = list(_previous_rule_findings(published, candidate))
    expected = numbered.contracts_by_key(published)
    actual = numbered.contracts_by_key(candidate)

    for (path, rule_id), expected_occurrences in expected.items():
        if len(expected_occurrences) != 1:
            continue
        actual_occurrences = actual.get((path, rule_id), [])
        if len(actual_occurrences) != 1:
            continue

        expected_fields = expected_occurrences[0]
        actual_fields = actual_occurrences[0]
        for label in sorted(set(actual_fields) - set(expected_fields)):
            value = actual_fields[label]
            if (
                terminal._is_candidate_only_behavioral_field(label)
                or terminal._is_permission_expanding_statement(value)
            ):
                findings.append(
                    f"RULE_BEHAVIORAL_FIELD_ADDED:{path}:{rule_id}:{label}"
                )

    return sorted(set(findings))


numbered.rule_field_contract_findings = _candidate_only_rule_field_findings


# ---------------------------------------------------------------------------
# Candidate-only unnumbered governance conditional exceptions.
#
# A blanket `unless` detector would also reject genuinely additive restrictions
# such as `Do not merge unless independent review succeeds`. Instead compare the
# obligation before the escape clause with published obligations in the same
# section. If the new statement restates an existing obligation and then adds
# `unless` / `except when` / `except if`, it is an exception to the published
# control rather than a new restrictive control.


_previous_unnumbered_findings = unnumbered.unnumbered_contract_findings
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


def _unnumbered_findings_with_conditional_escapes(
    published,
    candidate,
) -> list[str]:
    findings = list(_previous_unnumbered_findings(published, candidate))
    peers: dict[tuple[str, str], list[str]] = defaultdict(list)
    for path, section, statement in published:
        peers[(path, section)].append(statement)

    for (path, section, statement), count in (candidate - published).items():
        if count <= 0:
            continue
        if _conditional_escape_weakens_published(
            statement,
            peers.get((path, section), []),
        ):
            findings.append(
                "UNNUMBERED_GOVERNANCE_WEAKENING_ADDED:"
                f"{path}:{section}:{statement}"
            )

    return sorted(set(findings))


unnumbered.unnumbered_contract_findings = _unnumbered_findings_with_conditional_escapes


class ReleaseCandidateFinalReviewClusterClosureTests(unittest.TestCase):
    def _has_alias_marker(self, source: str) -> bool:
        helper = expr.ReleaseCandidateReturnedSinkAliasExpressionClosureTests()
        return helper._has_alias_marker(source)

    def test_starred_literal_rhs_preserves_constructor_alias(self) -> None:
        source = """
from standards_tools import Finding, ToolResult

def validate():
    maker, = (*[ToolResult.from_findings],)
    findings = []
    findings.append(Finding("PUBLIC_CODE", "visible"))
    return maker(tool="validate", version="1", findings=[])
"""
        self.assertTrue(self._has_alias_marker(source))

    def test_exemption_label_is_behavioral(self) -> None:
        published_text = """
### SAMPLE-001

**Requirement:** Authentication is required.
"""
        candidate_text = published_text + """
**Exemptions:** Authentication may be skipped when documented.
"""
        published = numbered.extract_rule_field_contracts(published_text, "sample.md")
        candidate = numbered.extract_rule_field_contracts(candidate_text, "sample.md")
        self.assertIn(
            "RULE_BEHAVIORAL_FIELD_ADDED:sample.md:SAMPLE-001:exemptions",
            numbered.rule_field_contract_findings(published, candidate),
        )

    def test_neutral_label_cannot_hide_permission_expansion(self) -> None:
        published_text = """
### SAMPLE-001

**Requirement:** Authentication is required.
"""
        candidate_text = published_text + """
**Notes:** Authentication may be skipped when documented.
"""
        published = numbered.extract_rule_field_contracts(published_text, "sample.md")
        candidate = numbered.extract_rule_field_contracts(candidate_text, "sample.md")
        self.assertIn(
            "RULE_BEHAVIORAL_FIELD_ADDED:sample.md:SAMPLE-001:notes",
            numbered.rule_field_contract_findings(published, candidate),
        )

    def test_neutral_label_no_longer_mandatory_is_permission_expansion(self) -> None:
        published_text = """
### SAMPLE-001

**Requirement:** Authentication is required.
"""
        candidate_text = published_text + """
**Notes:** Authentication is no longer mandatory.
"""
        published = numbered.extract_rule_field_contracts(published_text, "sample.md")
        candidate = numbered.extract_rule_field_contracts(candidate_text, "sample.md")
        self.assertIn(
            "RULE_BEHAVIORAL_FIELD_ADDED:sample.md:SAMPLE-001:notes",
            numbered.rule_field_contract_findings(published, candidate),
        )

    def test_neutral_editorial_label_is_not_permission_expansion(self) -> None:
        published_text = """
### SAMPLE-001

**Requirement:** Authentication is required.
"""
        candidate_text = published_text + """
**Notes:** Authentication terminology is used consistently in this section.
"""
        published = numbered.extract_rule_field_contracts(published_text, "sample.md")
        candidate = numbered.extract_rule_field_contracts(candidate_text, "sample.md")
        self.assertEqual(
            numbered.rule_field_contract_findings(published, candidate),
            [],
        )

    def test_unless_exception_to_published_obligation_is_rejected(self) -> None:
        published_text = """
## Independent review

Independent review is required before high-risk work is merged.
"""
        candidate_text = published_text + """
Independent review is required unless the author marks the change urgent.
"""
        published = unnumbered.extract_unnumbered_governance_contracts(
            published_text,
            "AGENTS.md",
        )
        candidate = unnumbered.extract_unnumbered_governance_contracts(
            candidate_text,
            "AGENTS.md",
        )
        self.assertTrue(
            any(
                item.startswith("UNNUMBERED_GOVERNANCE_WEAKENING_ADDED:")
                for item in unnumbered.unnumbered_contract_findings(
                    published,
                    candidate,
                )
            )
        )

    def test_modal_restatement_unless_exception_is_rejected(self) -> None:
        published_text = """
## Independent review

Independent review is required before high-risk work is merged.
"""
        candidate_text = published_text + """
Independent review must be performed unless the author marks the change urgent.
"""
        published = unnumbered.extract_unnumbered_governance_contracts(
            published_text,
            "AGENTS.md",
        )
        candidate = unnumbered.extract_unnumbered_governance_contracts(
            candidate_text,
            "AGENTS.md",
        )
        self.assertTrue(
            any(
                item.startswith("UNNUMBERED_GOVERNANCE_WEAKENING_ADDED:")
                for item in unnumbered.unnumbered_contract_findings(
                    published,
                    candidate,
                )
            )
        )

    def test_except_when_exception_to_published_obligation_is_rejected(self) -> None:
        published_text = """
## Independent review

Independent review is required before high-risk work is merged.
"""
        candidate_text = published_text + """
Independent review is required except when the author marks the change urgent.
"""
        published = unnumbered.extract_unnumbered_governance_contracts(
            published_text,
            "AGENTS.md",
        )
        candidate = unnumbered.extract_unnumbered_governance_contracts(
            candidate_text,
            "AGENTS.md",
        )
        self.assertTrue(
            unnumbered.unnumbered_contract_findings(published, candidate)
        )

    def test_additive_restrictive_unless_rule_is_not_misclassified(self) -> None:
        published_text = """
## Independent review

Independent review is required before high-risk work is merged.
"""
        candidate_text = published_text + """
Do not merge unless independent review succeeds.
"""
        published = unnumbered.extract_unnumbered_governance_contracts(
            published_text,
            "AGENTS.md",
        )
        candidate = unnumbered.extract_unnumbered_governance_contracts(
            candidate_text,
            "AGENTS.md",
        )
        self.assertEqual(
            unnumbered.unnumbered_contract_findings(published, candidate),
            [],
        )


if __name__ == "__main__":
    unittest.main()
