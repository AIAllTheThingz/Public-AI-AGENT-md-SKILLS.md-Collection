from __future__ import annotations

import ast
import importlib
import json
import re
import unittest
from collections import Counter
from pathlib import Path

import test_rc_numbered_rule_semantics as numbered
import test_rc_unnumbered_governance_semantics as unnumbered


# Terminal closure for the current PR #71 review cluster.
#
# Keep this layer narrow: repair static destructuring in the returned-sink
# constructor alias flow, then close the two governance compatibility blind
# spots raised against the same exact head. Earlier overlays remain responsible
# for the already-reviewed execution, sink, and provenance semantics.


def _load_overlay(suffix: str):
    matches = sorted(Path(__file__).parent.glob(f"test_rc_*{suffix}.py"))
    if len(matches) != 1:
        raise RuntimeError(f"expected exactly one RC overlay for {suffix!r}")
    return importlib.import_module(matches[0].stem)


expr = _load_overlay("_returned_sink_alias_expression_closure")
_load_overlay("_returned_sink_alias_provenance_final")

_NO = expr._NO
_previous_assign = expr._assign


# ---------------------------------------------------------------------------
# Returned-sink constructor aliases: evaluate static sequence RHS values once,
# then bind the resulting element states to destructuring targets. This avoids
# losing constructor identity after the later provenance overlay and handles a
# starred middle target without treating the collected list as a callable alias.


def _evaluate_static_shape(
    node: ast.AST,
    env: dict[str, str],
) -> tuple[tuple[str, list[object] | None], dict[str, str]]:
    if isinstance(node, (ast.Tuple, ast.List)):
        children: list[object] = []
        after = dict(env)
        for element in node.elts:
            child, after = _evaluate_static_shape(element, after)
            children.append(child)
        return (_NO, children), after

    state, after = expr._eval_expr(node, env)
    return (state, None), after


def _bind_shape(
    target: ast.AST,
    shape: tuple[str, list[object] | None],
    env: dict[str, str],
) -> dict[str, str]:
    state, children = shape

    if isinstance(target, ast.Name):
        return expr._bind(env, target.id, state)

    if isinstance(target, ast.Starred):
        # A starred assignment target receives a newly constructed list, not
        # the original constructor object, even if one captured element is the
        # constructor. Do not fabricate callable-alias identity for that list.
        return expr._kill_target(env, target)

    if not isinstance(target, (ast.Tuple, ast.List)) or children is None:
        return expr._kill_target(env, target)

    targets = list(target.elts)
    starred = [
        index for index, item in enumerate(targets) if isinstance(item, ast.Starred)
    ]

    if not starred:
        if len(targets) != len(children):
            return expr._kill_target(env, target)
        result = dict(env)
        for target_item, child in zip(targets, children):
            result = _bind_shape(target_item, child, result)
        return result

    if len(starred) != 1:
        return expr._kill_target(env, target)

    star_index = starred[0]
    before = targets[:star_index]
    after_targets = targets[star_index + 1 :]
    if len(children) < len(before) + len(after_targets):
        return expr._kill_target(env, target)

    result = dict(env)
    for target_item, child in zip(before, children[: len(before)]):
        result = _bind_shape(target_item, child, result)

    # Starred capture is always a list value, so clear any previous callable
    # alias on the capture target.
    result = expr._kill_target(result, targets[star_index])

    if after_targets:
        tail = children[-len(after_targets) :]
        for target_item, child in zip(after_targets, tail):
            result = _bind_shape(target_item, child, result)

    return result


def _assign_with_static_destructuring(
    statement: ast.Assign | ast.AnnAssign,
    env: dict[str, str],
) -> dict[str, str]:
    if (
        isinstance(statement, ast.Assign)
        and len(statement.targets) == 1
        and isinstance(statement.targets[0], (ast.Tuple, ast.List))
        and isinstance(statement.value, (ast.Tuple, ast.List))
    ):
        shape, after = _evaluate_static_shape(statement.value, env)
        return _bind_shape(statement.targets[0], shape, after)

    return _previous_assign(statement, env)


expr._assign = _assign_with_static_destructuring


# ---------------------------------------------------------------------------
# Numbered rules: published behavioral fields must remain, and a candidate may
# not silently weaken an existing published rule by adding a new exception,
# applicability restriction, override, waiver, or authorization/approval escape
# hatch that had no published counterpart.


_previous_rule_field_findings = numbered.rule_field_contract_findings

_ADDED_BEHAVIORAL_FIELD_MARKERS = (
    "exception",
    "applicability",
    "override",
    "waiver",
    "authorization",
    "approval",
    "scope",
    "precedence",
)


def _is_candidate_only_behavioral_field(label: str) -> bool:
    normalized = numbered.normalize_contract_text(label).casefold()
    return any(marker in normalized for marker in _ADDED_BEHAVIORAL_FIELD_MARKERS)


def _rule_field_contract_findings_closed(
    published: list[tuple[str, str, dict[str, str]]],
    candidate: list[tuple[str, str, dict[str, str]]],
) -> list[str]:
    findings = list(_previous_rule_field_findings(published, candidate))
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
            if _is_candidate_only_behavioral_field(label):
                findings.append(
                    f"RULE_BEHAVIORAL_FIELD_ADDED:{path}:{rule_id}:{label}"
                )

    return sorted(set(findings))


numbered.rule_field_contract_findings = _rule_field_contract_findings_closed


# ---------------------------------------------------------------------------
# Unnumbered governance: extend the checkpoint from governance/*.md into the
# policy-like Markdown documents that are already declared stable at the root.
# Derive membership from the published stable-root inventory rather than a
# second hand-maintained path list.


_previous_published_contracts = unnumbered.published_contracts
_previous_candidate_contracts = unnumbered.candidate_contracts
_previous_unnumbered_findings = unnumbered.unnumbered_contract_findings

_CHECKPOINT_PATH = (
    unnumbered.base.REPO_ROOT
    / "releases"
    / "compatibility"
    / "0.10.0-checkpoint.json"
)


def _is_root_policy_path(relative: str) -> bool:
    if not relative.endswith(".md"):
        return False
    name = Path(relative).name.casefold()
    return (
        name in {
            "agents.md",
            "maintainers.md",
            "security.md",
            "contributing.md",
            "pull_request_template.md",
        }
        or "policy" in name
    )


def _stable_root_policy_paths() -> tuple[str, ...]:
    checkpoint = json.loads(_CHECKPOINT_PATH.read_text(encoding="utf-8"))
    roots = checkpoint["stablePathGroups"]["root"]
    return tuple(sorted(path for path in roots if _is_root_policy_path(path)))


def _published_contracts_with_stable_root_policies() -> Counter[tuple[str, str, str]]:
    contracts = Counter(_previous_published_contracts())
    for relative in _stable_root_policy_paths():
        contracts.update(
            unnumbered.extract_unnumbered_governance_contracts(
                unnumbered.base.git_source_at(
                    unnumbered.base.CHECKPOINT_COMMIT,
                    relative,
                ),
                relative,
            )
        )
    return contracts


def _candidate_contracts_with_stable_root_policies() -> Counter[tuple[str, str, str]]:
    contracts = Counter(_previous_candidate_contracts())
    for relative in _stable_root_policy_paths():
        path = unnumbered.base.REPO_ROOT / relative
        if not path.is_file():
            # Stable-path existence is enforced by the path gate; absence here
            # naturally leaves all published semantic controls missing.
            continue
        contracts.update(
            unnumbered.extract_unnumbered_governance_contracts(
                path.read_text(encoding="utf-8"),
                relative,
            )
        )
    return contracts


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


def _is_permission_expanding_statement(statement: str) -> bool:
    normalized = unnumbered.normalize_contract_text(statement)
    return any(pattern.search(normalized) for pattern in _PERMISSION_EXPANSION_PATTERNS)


def _unnumbered_contract_findings_closed(
    published: Counter[tuple[str, str, str]],
    candidate: Counter[tuple[str, str, str]],
) -> list[str]:
    findings = list(_previous_unnumbered_findings(published, candidate))

    # Additive governance is generally allowed. Candidate-only language becomes
    # incompatible only when it introduces a permission/exception/override path
    # that can weaken the published control surface.
    additions = candidate - published
    for (path, section, statement), count in additions.items():
        if count <= 0 or not _is_permission_expanding_statement(statement):
            continue
        findings.append(
            "UNNUMBERED_GOVERNANCE_WEAKENING_ADDED:"
            f"{path}:{section}:{statement}"
        )

    return sorted(set(findings))


unnumbered.published_contracts = _published_contracts_with_stable_root_policies
unnumbered.candidate_contracts = _candidate_contracts_with_stable_root_policies
unnumbered.unnumbered_contract_findings = _unnumbered_contract_findings_closed


class ReleaseCandidatePR71TerminalClosureTests(unittest.TestCase):
    def _has_alias_marker(self, source: str) -> bool:
        helper = expr.ReleaseCandidateReturnedSinkAliasExpressionClosureTests()
        return helper._has_alias_marker(source)

    def test_plain_destructuring_preserves_constructor_alias(self) -> None:
        source = """
from standards_tools import Finding, ToolResult

def harmless(**kwargs):
    return kwargs

def validate():
    findings = []
    maker, other = ToolResult.from_findings, harmless
    findings.append(Finding("PUBLIC_CODE", "visible"))
    return maker(tool="validate", version="1", findings=[])
"""
        self.assertTrue(self._has_alias_marker(source))

    def test_starred_destructuring_preserves_tail_constructor_alias(self) -> None:
        source = """
from standards_tools import Finding, ToolResult

def harmless(**kwargs):
    return kwargs

def validate():
    first, *rest, maker = (harmless, harmless, ToolResult.from_findings)
    findings = []
    findings.append(Finding("PUBLIC_CODE", "visible"))
    return maker(tool="validate", version="1", findings=[])
"""
        self.assertTrue(self._has_alias_marker(source))

    def test_candidate_only_exception_field_is_incompatible(self) -> None:
        published_text = """
### SAMPLE-001

**Requirement:** Authentication is required.
"""
        weakened_text = published_text + """
**Exceptions:** Authentication may be skipped when documented.
"""
        editorial_text = published_text + """
**Rationale:** Authentication protects the service boundary.
"""

        published = numbered.extract_rule_field_contracts(
            published_text,
            "sample.md",
        )
        weakened = numbered.extract_rule_field_contracts(
            weakened_text,
            "sample.md",
        )
        editorial = numbered.extract_rule_field_contracts(
            editorial_text,
            "sample.md",
        )

        self.assertIn(
            "RULE_BEHAVIORAL_FIELD_ADDED:sample.md:SAMPLE-001:exceptions",
            numbered.rule_field_contract_findings(published, weakened),
        )
        self.assertEqual(
            numbered.rule_field_contract_findings(published, editorial),
            [],
        )

    def test_stable_root_policy_paths_come_from_published_checkpoint(self) -> None:
        paths = set(_stable_root_policy_paths())
        self.assertTrue(
            {
                "AGENTS.md",
                "MAINTAINERS.md",
                "RELEASE_POLICY.md",
                "MATURITY_POLICY.md",
                "SECURITY.md",
            }.issubset(paths)
        )

    def test_candidate_only_governance_permission_expansion_is_rejected(self) -> None:
        published_text = """
## Independent review

Independent review is required before high-risk work is merged.
"""
        candidate_text = published_text + """
- An author may merge without independent review when the change is urgent.
"""
        compatible_text = published_text + """
- Record additional independent-review evidence when available.
"""

        published = unnumbered.extract_unnumbered_governance_contracts(
            published_text,
            "AGENTS.md",
        )
        weakened = unnumbered.extract_unnumbered_governance_contracts(
            candidate_text,
            "AGENTS.md",
        )
        compatible = unnumbered.extract_unnumbered_governance_contracts(
            compatible_text,
            "AGENTS.md",
        )

        self.assertTrue(
            any(
                item.startswith("UNNUMBERED_GOVERNANCE_WEAKENING_ADDED:")
                for item in unnumbered.unnumbered_contract_findings(
                    published,
                    weakened,
                )
            )
        )
        self.assertEqual(
            unnumbered.unnumbered_contract_findings(published, compatible),
            [],
        )


if __name__ == "__main__":
    unittest.main()
