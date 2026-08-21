from __future__ import annotations

import ast
import json
import unittest
from collections import Counter

import rc_finding_code_contracts_base as literal_base
import test_rc_extended_finding_reachability as extended_reachability
import test_rc_finding_code_contracts as finding_contracts
import test_rc_zz_async_execution_regressions as _async_execution


def _parent_map(tree: ast.AST) -> dict[int, ast.AST]:
    parents: dict[int, ast.AST] = {}
    for parent in ast.walk(tree):
        for child in ast.iter_child_nodes(parent):
            parents[id(child)] = parent
    return parents


def _index_identity(items: list[ast.AST], target: ast.AST) -> int | None:
    for index, item in enumerate(items):
        if item is target:
            return index
    return None


def _emission_sink_contract(
    node: ast.Call,
    parents: dict[int, ast.AST],
) -> list[str]:
    """Describe how a Finding value is delivered beyond its constructor."""

    chain: list[str] = []
    current: ast.AST = node

    while True:
        parent = parents.get(id(current))
        if parent is None:
            chain.append("unknown")
            break

        if isinstance(parent, ast.Expr):
            chain.append(
                "discarded-expression" if parent.value is current else "expression"
            )
            break
        if isinstance(parent, ast.Return):
            chain.append("return")
            break
        if isinstance(parent, ast.Yield):
            chain.append("yield")
            break
        if isinstance(parent, ast.YieldFrom):
            chain.append("yield-from")
            break

        if isinstance(parent, ast.Call):
            position = _index_identity(parent.args, current)
            if position is not None:
                chain.append(
                    f"call-arg:{literal_base.canonical_ast(parent.func)}:{position}"
                )
                break
            keyword_name = next(
                (
                    keyword.arg if keyword.arg is not None else "**"
                    for keyword in parent.keywords
                    if keyword.value is current
                ),
                None,
            )
            if keyword_name is not None:
                chain.append(
                    f"call-keyword:{literal_base.canonical_ast(parent.func)}:{keyword_name}"
                )
                break
            if parent.func is current:
                chain.append("called-as-function")
                break

        if isinstance(parent, ast.Assign) and parent.value is current:
            chain.append(
                "assign:"
                + ",".join(
                    literal_base.canonical_ast(target) for target in parent.targets
                )
            )
            break
        if isinstance(parent, ast.AnnAssign) and parent.value is current:
            chain.append(f"annassign:{literal_base.canonical_ast(parent.target)}")
            break
        if isinstance(parent, ast.NamedExpr) and parent.value is current:
            chain.append(f"namedexpr:{literal_base.canonical_ast(parent.target)}")
            break

        if isinstance(parent, ast.List):
            chain.append("list")
        elif isinstance(parent, ast.Tuple):
            chain.append("tuple")
        elif isinstance(parent, ast.Set):
            chain.append("set")
        elif isinstance(parent, ast.Dict):
            chain.append("dict-key" if current in parent.keys else "dict-value")
        elif isinstance(parent, ast.Starred):
            chain.append("starred")
        elif isinstance(parent, ast.keyword):
            chain.append(f"keyword:{parent.arg or '**'}")
        elif isinstance(parent, ast.Await):
            chain.append("await")
        elif isinstance(parent, ast.IfExp):
            if parent.body is current:
                chain.append("ifexp:true")
            elif parent.orelse is current:
                chain.append("ifexp:false")
            else:
                chain.append("ifexp:test")
        elif isinstance(parent, ast.BoolOp):
            position = _index_identity(parent.values, current)
            chain.append(
                f"boolop:{type(parent.op).__name__}:{position if position is not None else '?'}"
            )
        else:
            chain.append(type(parent).__name__.lower())

        current = parent
        if len(chain) >= 8:
            chain.append("outer-chain-truncated")
            break

    return chain


# Importing the async overlay above installs all earlier generator/decorator/
# coroutine patches. The dedicated sink-aware visitor builds on that composed
# behavior without changing the scanners used by earlier regression modules.
_existing_literal_visit_call = literal_base.FindingSignatureVisitor.visit_Call


class SinkAwareFindingSignatureVisitor(literal_base.FindingSignatureVisitor):
    def visit_Call(self, node: ast.Call) -> None:
        code = None
        before = 0
        if isinstance(node.func, ast.Name) and node.func.id == "Finding":
            code = literal_base.finding_code(node)
            if code is not None:
                before = len(self.signatures.get(code, []))

        _existing_literal_visit_call(self, node)

        if code is None:
            return
        signatures = self.signatures.get(code, [])
        if len(signatures) <= before:
            return

        sink = _emission_sink_contract(node, self._finding_parent_map)
        for index in range(before, len(signatures)):
            payload = json.loads(signatures[index])
            payload["sink"] = sink
            signatures[index] = json.dumps(payload, sort_keys=True)


def finding_semantic_signatures_with_sink(
    text: str,
    source_path: str = "<memory>",
) -> dict[str, list[str]]:
    tree = literal_base.normalize_bound_names(ast.parse(text))
    visitor = SinkAwareFindingSignatureVisitor(
        literal_base.module_semantic_bindings(tree),
        source_path,
    )
    visitor._finding_parent_map = _parent_map(tree)
    visitor.visit(tree)
    return {
        code: sorted(signatures)
        for code, signatures in visitor.signatures.items()
    }


def _aggregate_sink_signatures(
    sources: list[tuple[str, str]],
) -> dict[str, set[str]]:
    result: dict[str, set[str]] = {}
    for source_path, text in sources:
        for code, signatures in finding_semantic_signatures_with_sink(
            text,
            source_path,
        ).items():
            result.setdefault(code, set()).update(signatures)
    return result


def published_sink_signatures() -> dict[str, set[str]]:
    return _aggregate_sink_signatures(
        [
            (
                relative,
                literal_base.git_source_at(literal_base.CHECKPOINT_COMMIT, relative),
            )
            for relative in literal_base.published_python_paths()
        ]
    )


def candidate_sink_signatures() -> dict[str, set[str]]:
    return _aggregate_sink_signatures(
        [
            (
                path.relative_to(literal_base.REPO_ROOT).as_posix(),
                path.read_text(encoding="utf-8"),
            )
            for path in literal_base.candidate_python_paths()
        ]
    )


_existing_extended_visit_call = (
    extended_reachability.ExtendedReachableFindingVisitor.visit_Call
)


class SinkAwareReachableFindingVisitor(
    extended_reachability.ExtendedReachableFindingVisitor
):
    def __init__(self, source_path: str) -> None:
        super().__init__(source_path)
        self.emission_contracts: Counter[tuple[str, str, str, str]] = Counter()
        self._finding_parent_map: dict[int, ast.AST] = {}

    def visit_Call(self, node: ast.Call) -> None:
        code = None
        if isinstance(node.func, ast.Name) and node.func.id == "Finding":
            code = extended_reachability._base.literal_finding_code(node)

        _existing_extended_visit_call(self, node)

        if code is not None:
            sink = json.dumps(
                _emission_sink_contract(node, self._finding_parent_map),
                sort_keys=True,
            )
            self.emission_contracts[
                (self.source_path, self.function, code, sink)
            ] += 1


def reachable_emission_contracts(
    text: str,
    source_path: str,
) -> Counter[tuple[str, str, str, str]]:
    tree = literal_base.normalize_bound_names(ast.parse(text))
    visitor = SinkAwareReachableFindingVisitor(source_path)
    visitor._finding_parent_map = _parent_map(tree)
    visitor.visit(tree)
    return visitor.emission_contracts


def published_reachable_emission_contracts() -> Counter[
    tuple[str, str, str, str]
]:
    result: Counter[tuple[str, str, str, str]] = Counter()
    for relative in literal_base.published_python_paths():
        result.update(
            reachable_emission_contracts(
                literal_base.git_source_at(literal_base.CHECKPOINT_COMMIT, relative),
                relative,
            )
        )
    return result


def candidate_reachable_emission_contracts() -> Counter[
    tuple[str, str, str, str]
]:
    result: Counter[tuple[str, str, str, str]] = Counter()
    for path in literal_base.candidate_python_paths():
        relative = path.relative_to(literal_base.REPO_ROOT).as_posix()
        result.update(
            reachable_emission_contracts(
                path.read_text(encoding="utf-8"),
                relative,
            )
        )
    return result


class ReleaseCandidateFindingEmissionSinkRegressionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.contract = json.loads(
            literal_base.CHECKPOINT_PATH.read_text(encoding="utf-8")
        )

    def test_every_published_finding_sink_semantic_is_preserved(self):
        published = published_sink_signatures()
        current = candidate_sink_signatures()
        approved = self.contract["approvedAdditivePublishedCodeContexts"]

        self.assertGreater(len(published), 20)
        for code, expected_signatures in published.items():
            with self.subTest(code=code):
                # This finding's post-v0.10 local dataflow is intentionally
                # behavior-bound by dedicated runtime tests. Sink reachability is
                # still protected by the separate reachability contract below.
                if code in finding_contracts._BEHAVIOR_BOUND_FINDING_CONTEXTS:
                    continue

                current_signatures = current.get(code, set())
                expected_projected = {
                    literal_base.project_approved_helper_changes(
                        signature,
                        code,
                        self.contract,
                    )
                    for signature in expected_signatures
                }
                current_projected = {
                    literal_base.project_approved_helper_changes(
                        signature,
                        code,
                        self.contract,
                    )
                    for signature in current_signatures
                }
                self.assertEqual(
                    expected_projected - current_projected,
                    set(),
                    f"published emission sink changed/disappeared for {code}",
                )
                additional = current_projected - expected_projected
                if code in approved:
                    self.assertEqual(len(additional), approved[code]["count"])
                else:
                    self.assertEqual(additional, set())

    def test_every_published_reachable_emission_sink_remains(self):
        published = published_reachable_emission_contracts()
        current = candidate_reachable_emission_contracts()
        self.assertGreater(sum(published.values()), 20)

        missing = {
            contract: count - current.get(contract, 0)
            for contract, count in published.items()
            if current.get(contract, 0) < count
        }
        self.assertEqual(
            missing,
            {},
            "published reachable Finding changed or lost its emission sink",
        )

    def test_append_to_bare_constructor_changes_sink_semantics(self):
        emitted = """
def validate(findings):
    findings.append(Finding("PUBLIC_CODE", "visible", path="sample"))
"""
        discarded = """
def validate(findings):
    Finding("PUBLIC_CODE", "visible", path="sample")
"""
        emitted_payload = json.loads(
            finding_semantic_signatures_with_sink(emitted)["PUBLIC_CODE"][0]
        )
        discarded_payload = json.loads(
            finding_semantic_signatures_with_sink(discarded)["PUBLIC_CODE"][0]
        )

        self.assertNotEqual(emitted_payload["sink"], discarded_payload["sink"])
        self.assertTrue(
            any(item.startswith("call-arg:") for item in emitted_payload["sink"])
        )
        self.assertEqual(
            discarded_payload["sink"],
            ["discarded-expression"],
        )

    def test_reachability_identity_includes_emission_sink(self):
        emitted = """
def validate(findings):
    findings.append(Finding("PUBLIC_CODE", "visible"))
"""
        discarded = """
def validate(findings):
    Finding("PUBLIC_CODE", "visible")
"""
        emitted_contracts = reachable_emission_contracts(emitted, "sample.py")
        discarded_contracts = reachable_emission_contracts(discarded, "sample.py")

        self.assertNotEqual(emitted_contracts, discarded_contracts)
        self.assertEqual(sum(emitted_contracts.values()), 1)
        self.assertEqual(sum(discarded_contracts.values()), 1)
        self.assertTrue(
            any("call-arg:" in contract[3] for contract in emitted_contracts)
        )
        self.assertTrue(
            any("discarded-expression" in contract[3] for contract in discarded_contracts)
        )

    def test_return_and_container_call_sinks_are_distinct(self):
        returned = """
def validate():
    return Finding("PUBLIC_CODE", "visible")
"""
        extended = """
def validate(findings):
    findings.extend([Finding("PUBLIC_CODE", "visible")])
"""
        returned_payload = json.loads(
            finding_semantic_signatures_with_sink(returned)["PUBLIC_CODE"][0]
        )
        extended_payload = json.loads(
            finding_semantic_signatures_with_sink(extended)["PUBLIC_CODE"][0]
        )

        self.assertEqual(returned_payload["sink"], ["return"])
        self.assertEqual(extended_payload["sink"][0], "list")
        self.assertTrue(extended_payload["sink"][1].startswith("call-arg:"))


if __name__ == "__main__":
    unittest.main()
