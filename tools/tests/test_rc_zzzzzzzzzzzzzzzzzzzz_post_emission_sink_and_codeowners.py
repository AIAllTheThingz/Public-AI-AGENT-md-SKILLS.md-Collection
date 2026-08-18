from __future__ import annotations

import ast
import json
import unittest

import rc_finding_code_contracts_base as base
import test_rc_zzzz_sink_rebinding_and_parameterized_multiplicity as sink_state
import test_rc_zzzzzzzzzzzzzzzzzzz_post_emission_completion as _post_completion  # noqa: F401


# ---------------------------------------------------------------------------
# Preserve the finding sink after emission.
# ---------------------------------------------------------------------------

_previous_emission_sink_contract = sink_state.sink_execution._emission_sink_contract


def _normalized_if_requirement(test: ast.AST, branch: bool) -> tuple[str, bool]:
    if isinstance(test, ast.UnaryOp) and isinstance(test.op, ast.Not):
        return base.canonical_ast(test.operand), not branch
    return base.canonical_ast(test), branch


def _if_requirements(
    node: ast.AST,
    function: ast.FunctionDef | ast.AsyncFunctionDef,
    parents: dict[int, ast.AST],
) -> dict[str, bool]:
    requirements: dict[str, bool] = {}
    current = node
    while True:
        parent = parents.get(id(current))
        if parent is None or parent is function:
            break
        if isinstance(parent, ast.If):
            if current in parent.body:
                key, value = _normalized_if_requirement(parent.test, True)
                requirements[key] = value
            elif current in parent.orelse:
                key, value = _normalized_if_requirement(parent.test, False)
                requirements[key] = value
        current = parent
    return requirements


def _can_share_execution_path(
    finding: ast.Call,
    mutation: ast.AST,
    function: ast.FunctionDef | ast.AsyncFunctionDef,
    parents: dict[int, ast.AST],
) -> bool:
    finding_requirements = _if_requirements(finding, function, parents)
    mutation_requirements = _if_requirements(mutation, function, parents)
    return not any(
        key in mutation_requirements and mutation_requirements[key] != value
        for key, value in finding_requirements.items()
    )


def _post_emission_sink_state_history(
    node: ast.Call,
    receiver: ast.AST,
    parents: dict[int, ast.AST],
) -> list[str]:
    function = sink_state._enclosing_function(node, parents)
    if function is None:
        return []

    cutoff = getattr(node, "lineno", 10**9)
    changes: list[tuple[int, int, str]] = []

    def record(item: ast.AST) -> None:
        line = getattr(item, "lineno", 0)
        if line <= cutoff:
            return
        if not _can_share_execution_path(node, item, function, parents):
            return
        changes.append(
            (
                line,
                getattr(item, "col_offset", 0),
                json.dumps(
                    {
                        "context": sink_state._sink_state_context(
                            item, function, parents
                        ),
                        "operation": base.canonical_ast(item),
                    },
                    sort_keys=True,
                ),
            )
        )

    for item in ast.walk(function):
        if not sink_state._belongs_to_function(item, function, parents):
            continue
        line = getattr(item, "lineno", 0)
        if line <= cutoff:
            continue

        # Resolve aliases at the mutation point, including aliases introduced
        # after the finding was appended.
        aliases = sink_state._receiver_aliases_before(
            function, receiver, parents, line + 1
        )

        if isinstance(item, ast.Assign):
            for target in item.targets:
                # Rebinding the local name after an append does not erase the
                # already-mutated caller sink. Subscript/attribute writes can.
                if not isinstance(target, ast.Name) and sink_state._target_touches_receiver(
                    target, receiver, aliases
                ):
                    record(item)
                    break
        elif isinstance(item, ast.AnnAssign):
            if not isinstance(item.target, ast.Name) and sink_state._target_touches_receiver(
                item.target, receiver, aliases
            ):
                record(item)
        elif isinstance(item, ast.AugAssign):
            if sink_state._target_touches_receiver(item.target, receiver, aliases):
                record(item)
        elif isinstance(item, ast.Delete):
            if any(
                sink_state._target_touches_receiver(target, receiver, aliases)
                for target in item.targets
            ):
                record(item)
        elif (
            isinstance(item, ast.Call)
            and isinstance(item.func, ast.Attribute)
            and sink_state._root_name(item.func.value) in aliases
            and item.func.attr in sink_state._DESTRUCTIVE_SINK_METHODS
        ):
            record(item)

    changes.sort()
    return [value for _, _, value in changes]


def _emission_sink_contract_with_post_state(
    node: ast.Call,
    parents: dict[int, ast.AST],
) -> list[str]:
    contract = list(_previous_emission_sink_contract(node, parents))
    receiver = sink_state._finding_sink_receiver(node, parents)
    if receiver is None:
        return contract

    post_state = _post_emission_sink_state_history(node, receiver, parents)
    if post_state:
        contract.append("post-receiver-state:" + json.dumps(post_state, sort_keys=True))
    return contract


sink_state.sink_execution._emission_sink_contract = _emission_sink_contract_with_post_state


# ---------------------------------------------------------------------------
# Preserve the stable CODEOWNERS routing contract.
# ---------------------------------------------------------------------------

CODEOWNERS_PATH = ".github/CODEOWNERS"


def _codeowners_routes(text: str) -> tuple[tuple[str, tuple[str, ...]], ...]:
    routes: list[tuple[str, tuple[str, ...]]] = []
    for raw in text.splitlines():
        stripped = raw.strip()
        if not stripped or stripped.startswith("#"):
            continue
        parts = stripped.split()
        if len(parts) < 2:
            continue
        routes.append((parts[0], tuple(parts[1:])))
    return tuple(routes)


class ReleaseCandidatePostEmissionSinkAndCodeownersTests(unittest.TestCase):
    def test_destructive_sink_mutation_after_emission_changes_contract(self) -> None:
        emitted = '''
def validate(findings):
    findings.append(Finding("PUBLIC_CODE", "visible"))
'''
        cleared = '''
def validate(findings):
    findings.append(Finding("PUBLIC_CODE", "visible"))
    findings.clear()
'''
        alias_cleared = '''
def validate(findings):
    findings.append(Finding("PUBLIC_CODE", "visible"))
    alias = findings
    alias.clear()
'''

        expected = base.finding_semantic_signatures(emitted)
        cleared_contract = base.finding_semantic_signatures(cleared)
        alias_contract = base.finding_semantic_signatures(alias_cleared)

        self.assertNotEqual(expected, cleared_contract)
        self.assertNotEqual(expected, alias_contract)
        sink = json.loads(cleared_contract["PUBLIC_CODE"][0])["sink"]
        self.assertTrue(
            any(item.startswith("post-receiver-state:") for item in sink),
            sink,
        )

    def test_mutually_exclusive_post_clear_does_not_freeze_contract(self) -> None:
        original = '''
def validate(findings, enabled):
    if enabled:
        findings.append(Finding("PUBLIC_CODE", "visible"))
'''
        exclusive = '''
def validate(findings, enabled):
    if enabled:
        findings.append(Finding("PUBLIC_CODE", "visible"))
    if not enabled:
        findings.clear()
'''
        self.assertEqual(
            base.finding_semantic_signatures(original),
            base.finding_semantic_signatures(exclusive),
        )

    def test_additive_append_after_emission_is_not_destructive(self) -> None:
        original = '''
def validate(findings):
    findings.append(Finding("PUBLIC_CODE", "visible"))
'''
        additive = '''
def validate(findings):
    findings.append(Finding("PUBLIC_CODE", "visible"))
    findings.append(Finding("NEW_CODE", "new"))
'''
        expected_sink = json.loads(
            base.finding_semantic_signatures(original)["PUBLIC_CODE"][0]
        )["sink"]
        actual_sink = json.loads(
            base.finding_semantic_signatures(additive)["PUBLIC_CODE"][0]
        )["sink"]
        self.assertEqual(expected_sink, actual_sink)

    def test_all_published_codeowners_routes_are_preserved_semantically(self) -> None:
        checkpoint = json.loads(
            (base.REPO_ROOT / "releases/compatibility/0.10.0-checkpoint.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertIn(CODEOWNERS_PATH, checkpoint["stablePathGroups"]["root"])

        published = _codeowners_routes(
            base.git_source_at(base.CHECKPOINT_COMMIT, CODEOWNERS_PATH)
        )
        candidate = _codeowners_routes(
            (base.REPO_ROOT / CODEOWNERS_PATH).read_text(encoding="utf-8")
        )
        self.assertGreater(len(published), 20)
        self.assertEqual(
            candidate,
            published,
            "stable CODEOWNERS patterns, owners, or precedence changed",
        )

    def test_codeowners_owner_change_is_detected_but_comments_are_editable(self) -> None:
        published_text = base.git_source_at(base.CHECKPOINT_COMMIT, CODEOWNERS_PATH)
        published = _codeowners_routes(published_text)

        changed = published_text.replace(
            "/languages/ @AIAllTheThingz",
            "/languages/ @different-owner",
            1,
        )
        self.assertNotEqual(_codeowners_routes(changed), published)

        comment_only = "# editorial comment\n" + published_text
        self.assertEqual(_codeowners_routes(comment_only), published)


if __name__ == "__main__":
    unittest.main()
