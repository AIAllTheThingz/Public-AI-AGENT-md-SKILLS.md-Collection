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


_previous_eval_expr = expr._eval_expr


def _is_static_value(node: ast.AST) -> bool:
    try:
        ast.literal_eval(node)
    except (ValueError, TypeError, SyntaxError):
        return False
    return True


def _is_resolvable_partial_constructor(node: ast.AST) -> bool:
    return (
        isinstance(node, ast.Call)
        and getattr(node, "_pag_resolvable_partial", False)
        and bool(node.args)
        and not any(isinstance(argument, ast.Starred) for argument in node.args)
        and all(_is_static_value(argument) for argument in node.args[1:])
        and all(
            keyword.arg is not None and _is_static_value(keyword.value)
            for keyword in node.keywords
        )
    )


def _partial_factory(node: ast.AST, modules: set[str], factories: set[str]) -> bool:
    return (
        isinstance(node, ast.Name)
        and node.id in factories
    ) or (
        isinstance(node, ast.Attribute)
        and isinstance(node.value, ast.Name)
        and node.value.id in modules
        and node.attr == "partial"
    )


def _bound_names(statement: ast.Assign | ast.AnnAssign) -> set[str]:
    targets = (
        [statement.target]
        if isinstance(statement, ast.AnnAssign)
        else list(statement.targets)
    )
    return {
        target.id
        for target in targets
        if isinstance(target, ast.Name)
    }


def _mark_partial_calls(
    node: ast.AST,
    modules: set[str],
    factories: set[str],
) -> None:
    for candidate in ast.walk(node):
        if isinstance(candidate, ast.Call) and _partial_factory(
            candidate.func,
            modules,
            factories,
        ):
            candidate._pag_resolvable_partial = True


def _mark_partial_statements(
    statements: list[ast.stmt],
    modules: set[str],
    factories: set[str],
) -> None:
    for statement in statements:
        if isinstance(statement, ast.Import):
            for imported in statement.names:
                name = imported.asname or imported.name.split(".", 1)[0]
                if imported.name == "functools":
                    modules.add(name)
                else:
                    modules.discard(name)
                    factories.discard(name)
            continue

        if isinstance(statement, ast.ImportFrom):
            for imported in statement.names:
                name = imported.asname or imported.name
                if statement.module == "functools" and imported.name == "partial":
                    factories.add(name)
                else:
                    modules.discard(name)
                    factories.discard(name)
            continue

        if isinstance(statement, (ast.Assign, ast.AnnAssign)) and statement.value:
            _mark_partial_calls(statement.value, modules, factories)
            names = _bound_names(statement)
            if _partial_factory(statement.value, modules, factories):
                factories.update(names)
            else:
                factories.difference_update(names)
                modules.difference_update(names)
            continue

        if isinstance(statement, (ast.FunctionDef, ast.AsyncFunctionDef)):
            local_modules = set(modules)
            local_factories = set(factories)
            local_names = {
                argument.arg
                for argument in (
                    *statement.args.posonlyargs,
                    *statement.args.args,
                    *statement.args.kwonlyargs,
                )
            }
            if statement.args.vararg is not None:
                local_names.add(statement.args.vararg.arg)
            if statement.args.kwarg is not None:
                local_names.add(statement.args.kwarg.arg)
            local_modules.difference_update(local_names)
            local_factories.difference_update(local_names)
            _mark_partial_statements(
                statement.body,
                local_modules,
                local_factories,
            )
            modules.discard(statement.name)
            factories.discard(statement.name)
            continue

        _mark_partial_calls(statement, modules, factories)


def _mark_resolvable_partial_calls(
    finding: ast.Call,
    parents: dict[int, ast.AST],
) -> None:
    root: ast.AST = finding
    while id(root) in parents:
        root = parents[id(root)]
    if isinstance(root, ast.Module):
        _mark_partial_statements(root.body, set(), set())


_previous_aliased_return_markers = expr.alias_layer._aliased_return_markers


def _aliased_return_markers_with_partial_wrappers(
    finding: ast.Call,
    receiver: ast.AST,
    parents: dict[int, ast.AST],
) -> list[str]:
    _mark_resolvable_partial_calls(finding, parents)
    return _previous_aliased_return_markers(finding, receiver, parents)


expr.alias_layer._aliased_return_markers = (
    _aliased_return_markers_with_partial_wrappers
)


def _eval_expr_with_partial_constructor_aliases(
    node: ast.AST,
    env: dict[str, str],
    calls: list[tuple[ast.Call, str]] | None = None,
) -> tuple[str, dict[str, str]]:
    if not _is_resolvable_partial_constructor(node):
        return _previous_eval_expr(node, env, calls)

    _, after = _previous_eval_expr(node.func, env, calls)
    constructor_state, after = _previous_eval_expr(node.args[0], after, calls)
    for keyword in node.keywords:
        _, after = _previous_eval_expr(keyword.value, after, calls)
    return constructor_state, after


expr._eval_expr = _eval_expr_with_partial_constructor_aliases


_previous_bind_shape = terminal._bind_shape


def _bind_shape_preserving_normalized_duplicate_aliases(
    target: ast.AST,
    shape: tuple[str, list[object] | None],
    env: dict[str, str],
) -> dict[str, str]:
    state, children = shape
    if not isinstance(target, (ast.Tuple, ast.List)) or children is None:
        return _previous_bind_shape(target, shape, env)

    targets = list(target.elts)
    if (
        len(targets) != len(children)
        or any(isinstance(item, ast.Starred) for item in targets)
    ):
        return _previous_bind_shape(target, shape, env)

    duplicate_names = {
        item.id
        for item in targets
        if isinstance(item, ast.Name)
        and sum(
            isinstance(candidate, ast.Name) and candidate.id == item.id
            for candidate in targets
        ) > 1
    }
    if not duplicate_names:
        return _previous_bind_shape(target, shape, env)

    joined_states: dict[str, str] = {}
    for item, child in zip(targets, children):
        if not isinstance(item, ast.Name) or item.id not in duplicate_names:
            continue
        child_state, _child_children = child
        previous = joined_states.get(item.id, terminal._NO)
        joined_states[item.id] = expr._join(previous, child_state)

    result = dict(env)
    for item, child in zip(targets, children):
        if isinstance(item, ast.Name) and item.id in joined_states:
            result = expr._bind(result, item.id, joined_states[item.id])
        else:
            result = _previous_bind_shape(item, child, result)
    return result


# Bound-name normalization can collapse distinct destructuring names to one
# canonical identifier. Retain the joined alias state rather than letting a
# later non-alias slot erase an earlier constructor alias.
terminal._bind_shape = _bind_shape_preserving_normalized_duplicate_aliases


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


def _is_permission_expanding_statement(value: str) -> bool:
    normalized = numbered.normalize_contract_text(value).casefold()
    if any(pattern.search(normalized) for pattern in _DEOBLIGATION_PATTERNS):
        return True
    if any(pattern.search(normalized) for pattern in _RESTRICTIVE_DEONTIC_PATTERNS):
        return False
    return _previous_permission_expansion_classifier(value)


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


_previous_unnumbered_extractor = unnumbered.extract_unnumbered_governance_contracts
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


def _extract_unnumbered_contracts_with_permission_bullets(
    text: str,
    path: str,
):
    contracts = _previous_unnumbered_extractor(text, path)
    section = ""
    for line in text.splitlines():
        heading = re.match(r"^\s*#{1,6}\s+(.+?)\s*$", line)
        if heading is not None:
            section = numbered.normalize_contract_text(heading.group(1)).casefold()
            continue

        bullet = re.match(r"^\s*[-*+]\s+(.+?)\s*$", line)
        if bullet is None or not section:
            continue
        statement = bullet.group(1)
        if terminal._is_permission_expanding_statement(statement):
            contracts[(path, section, statement)] += 1

    return contracts


unnumbered.extract_unnumbered_governance_contracts = (
    _extract_unnumbered_contracts_with_permission_bullets
)


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
        if terminal._is_permission_expanding_statement(
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

    def test_functools_partial_constructor_alias_tracks_discarded_findings(self) -> None:
        kept = """
import functools
from standards_tools import Finding, ToolResult

def validate():
    findings = []
    maker = functools.partial(
        ToolResult.from_findings,
        tool="validate",
        version="1",
    )
    findings.append(Finding("PUBLIC_CODE", "visible"))
    return maker(findings=findings)
"""
        discarded = kept.replace(
            "return maker(findings=findings)",
            "return maker(findings=[])",
        )
        self.assertNotEqual(
            expr.literal_base.finding_semantic_signatures(kept, "sample.py"),
            expr.literal_base.finding_semantic_signatures(discarded, "sample.py"),
        )

    def test_imported_partial_constructor_alias_tracks_discarded_findings(self) -> None:
        source = """
from functools import partial
from standards_tools import Finding, ToolResult

def validate():
    findings = []
    maker = partial(ToolResult.from_findings, tool="validate", version="1")
    findings.append(Finding("PUBLIC_CODE", "visible"))
    return maker(findings=[])
"""
        self.assertTrue(self._has_alias_marker(source))

    def test_partial_factory_alias_tracks_static_bound_findings(self) -> None:
        direct = """
from standards_tools import Finding, ToolResult

def validate():
    findings = []
    findings.append(Finding("PUBLIC_CODE", "visible"))
    return ToolResult.from_findings(tool="validate", version="1", findings=findings)
"""
        discarded = """
import functools as wrappers
from standards_tools import Finding, ToolResult

def validate():
    findings = []
    factory = wrappers.partial
    maker = factory(ToolResult.from_findings, "validate", "1", [])
    findings.append(Finding("PUBLIC_CODE", "visible"))
    return maker()
"""
        self.assertNotEqual(
            expr.literal_base.finding_semantic_signatures(direct, "sample.py"),
            expr.literal_base.finding_semantic_signatures(discarded, "sample.py"),
        )
        self.assertTrue(self._has_alias_marker(discarded))

    def test_dynamic_prebound_findings_remains_conservative(self) -> None:
        prebound = """
from functools import partial
from standards_tools import Finding, ToolResult

def validate():
    findings = []
    maker = partial(
        ToolResult.from_findings,
        tool="validate",
        version="1",
        findings=findings,
    )
    findings.append(Finding("PUBLIC_CODE", "visible"))
    return maker()
"""
        self.assertFalse(self._has_alias_marker(prebound))

    def test_functools_partial_of_unrelated_callable_is_not_constructor_alias(self) -> None:
        source = """
import functools
from standards_tools import Finding, ToolResult

def harmless(**kwargs):
    return kwargs

def validate():
    findings = []
    maker = functools.partial(harmless, tool="validate")
    findings.append(Finding("PUBLIC_CODE", "visible"))
    return maker(findings=[])
"""
        self.assertFalse(self._has_alias_marker(source))

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

    def test_neutral_label_not_mandatory_is_permission_expansion(self) -> None:
        published_text = """
### SAMPLE-001

**Requirement:** Authentication is required.
"""
        candidate_text = published_text + """
**Notes:** Authentication is not mandatory.
"""
        published = numbered.extract_rule_field_contracts(published_text, "sample.md")
        candidate = numbered.extract_rule_field_contracts(candidate_text, "sample.md")
        self.assertIn(
            "RULE_BEHAVIORAL_FIELD_ADDED:sample.md:SAMPLE-001:notes",
            numbered.rule_field_contract_findings(published, candidate),
        )

    def test_neutral_label_deobligation_family_is_permission_expansion(self) -> None:
        published_text = """
### SAMPLE-001

**Requirement:** Authentication is required.
"""
        expected = "RULE_BEHAVIORAL_FIELD_ADDED:sample.md:SAMPLE-001:notes"
        for value in (
            "Authentication is not compulsory.",
            "Authentication is no longer obligatory.",
            "Authentication is not necessary.",
            "Authentication need not be performed.",
            "Authentication does not have to be performed.",
            "Authentication may be omitted.",
            "Authentication can be waived.",
        ):
            with self.subTest(value=value):
                candidate = numbered.extract_rule_field_contracts(
                    published_text + f"\n**Notes:** {value}\n",
                    "sample.md",
                )
                published = numbered.extract_rule_field_contracts(
                    published_text,
                    "sample.md",
                )
                self.assertIn(
                    expected,
                    numbered.rule_field_contract_findings(published, candidate),
                )

    def test_neutral_label_restrictive_deontic_text_is_not_permission_expansion(
        self,
    ) -> None:
        published_text = """
### SAMPLE-001

**Requirement:** Authentication is required.
"""
        for value in (
            "Authentication is not optional.",
            "Authentication is no longer optional.",
            "Authentication must not be skipped.",
            "Authentication may not be omitted.",
            "No waiver is permitted.",
            "Exceptions are not allowed.",
        ):
            with self.subTest(value=value):
                candidate = numbered.extract_rule_field_contracts(
                    published_text + f"\n**Notes:** {value}\n",
                    "sample.md",
                )
                published = numbered.extract_rule_field_contracts(
                    published_text,
                    "sample.md",
                )
                self.assertEqual(
                    numbered.rule_field_contract_findings(published, candidate),
                    [],
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
