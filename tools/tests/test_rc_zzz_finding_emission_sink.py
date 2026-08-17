from __future__ import annotations

import ast
import json
import unittest
from collections import Counter

import rc_finding_code_contracts_base as literal_base
import test_rc_extended_finding_reachability as extended_reachability
import test_rc_finding_reachability as basic_reachability
import test_rc_zz_async_execution_regressions as async_execution


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
    """Describe how a Finding value leaves its constructor expression.

    The compatibility surface cares whether a constructed Finding is actually
    delivered to a reporting sink. Human-readable message text remains outside
    this contract; only the use-chain around the constructor is recorded.
    """

    chain: list[str] = []
    current: ast.AST = node

    while True:
        parent = parents.get(id(current))
        if parent is None:
            chain.append("unknown")
            break

        if isinstance(parent, ast.Expr):
            if parent.value is current:
                chain.append("discarded-expression")
            else:
                chain.append("expression")
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
            if current in parent.keys:
                chain.append("dict-key")
            else:
                chain.append("dict-value")
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


def _is_discarded_constructor(
    node: ast.Call,
    parents: dict[int, ast.AST],
) -> bool:
    parent = parents.get(id(node))
    return isinstance(parent, ast.Expr) and parent.value is node


# Importing the async module above installs the generator, decorator, and async
# execution overlays. Capture that fully composed visit method and add sink
# identity on top of it.
_original_literal_visit_call = literal_base.FindingSignatureVisitor.visit_Call


def _literal_visit_call_with_sink(self, node: ast.Call) -> None:
    code = None
    before = 0
    if isinstance(node.func, ast.Name) and node.func.id == "Finding":
        code = literal_base.finding_code(node)
        if code is not None:
            before = len(self.signatures.get(code, []))

    _original_literal_visit_call(self, node)

    if code is None:
        return

    signatures = self.signatures.get(code, [])
    if len(signatures) <= before:
        return

    sink = _emission_sink_contract(
        node,
        getattr(self, "_finding_parent_map", {}),
    )
    for index in range(before, len(signatures)):
        payload = json.loads(signatures[index])
        payload["sink"] = sink
        signatures[index] = json.dumps(payload, sort_keys=True)


literal_base.FindingSignatureVisitor.visit_Call = _literal_visit_call_with_sink


def _semantic_signatures_with_sink(
    text: str,
    source_path: str = "<memory>",
) -> dict[str, list[str]]:
    tree = literal_base.normalize_bound_names(ast.parse(text))
    visitor = literal_base.FindingSignatureVisitor(
        literal_base.module_semantic_bindings(tree),
        source_path,
    )
    visitor._finding_parent_map = _parent_map(tree)
    visitor.visit(tree)
    return {
        code: sorted(signatures)
        for code, signatures in visitor.signatures.items()
    }


literal_base.finding_semantic_signatures = _semantic_signatures_with_sink


# Reachability means reachable *emission*, not merely reachable construction.
# Preserve every prior control-flow/deferred-execution patch and suppress only a
# directly discarded `Finding(...)` expression.
_original_basic_visit_call = basic_reachability.ReachableFindingVisitor.visit_Call
_original_extended_visit_call = (
    extended_reachability.ExtendedReachableFindingVisitor.visit_Call
)


def _basic_visit_call_with_sink(self, node: ast.Call) -> None:
    if (
        isinstance(node.func, ast.Name)
        and node.func.id == "Finding"
        and _is_discarded_constructor(
            node,
            getattr(self, "_finding_parent_map", {}),
        )
    ):
        self.generic_visit(node)
        return
    _original_basic_visit_call(self, node)


def _extended_visit_call_with_sink(self, node: ast.Call) -> None:
    if (
        isinstance(node.func, ast.Name)
        and node.func.id == "Finding"
        and _is_discarded_constructor(
            node,
            getattr(self, "_finding_parent_map", {}),
        )
    ):
        self.generic_visit(node)
        return
    _original_extended_visit_call(self, node)


basic_reachability.ReachableFindingVisitor.visit_Call = _basic_visit_call_with_sink
extended_reachability.ExtendedReachableFindingVisitor.visit_Call = (
    _extended_visit_call_with_sink
)


def _basic_reachable_with_parents(
    text: str,
    source_path: str,
) -> Counter[tuple[str, str, str]]:
    tree = ast.parse(text)
    visitor = basic_reachability.ReachableFindingVisitor(source_path)
    visitor._finding_parent_map = _parent_map(tree)
    visitor.visit(tree)
    return visitor.contracts


def _extended_reachable_with_parents(
    text: str,
    source_path: str,
) -> Counter[tuple[str, str, str]]:
    tree = ast.parse(text)
    visitor = extended_reachability.ExtendedReachableFindingVisitor(source_path)
    visitor._finding_parent_map = _parent_map(tree)
    visitor.visit(tree)
    return visitor.contracts


basic_reachability.reachable_literal_finding_contracts = _basic_reachable_with_parents
extended_reachability.reachable_contracts = _extended_reachable_with_parents


class ReleaseCandidateFindingEmissionSinkRegressionTests(unittest.TestCase):
    def test_append_to_bare_constructor_changes_literal_semantics(self):
        emitted = """
def validate(findings):
    findings.append(Finding("PUBLIC_CODE", "visible", path="sample"))
"""
        discarded = """
def validate(findings):
    Finding("PUBLIC_CODE", "visible", path="sample")
"""
        emitted_signatures = literal_base.finding_semantic_signatures(emitted)
        discarded_signatures = literal_base.finding_semantic_signatures(discarded)

        self.assertNotEqual(emitted_signatures, discarded_signatures)
        emitted_payload = json.loads(emitted_signatures["PUBLIC_CODE"][0])
        discarded_payload = json.loads(discarded_signatures["PUBLIC_CODE"][0])
        self.assertTrue(
            any(item.startswith("call-arg:") for item in emitted_payload["sink"])
        )
        self.assertEqual(
            discarded_payload["sink"],
            ["discarded-expression"],
        )

    def test_discarded_constructor_is_not_a_reachable_emission(self):
        emitted = """
def validate(findings):
    findings.append(Finding("PUBLIC_CODE", "visible"))
"""
        discarded = """
def validate(findings):
    Finding("PUBLIC_CODE", "visible")
"""
        expected_key = ("sample.py", "validate", "PUBLIC_CODE")

        for scanner in (
            basic_reachability.reachable_literal_finding_contracts,
            extended_reachability.reachable_contracts,
        ):
            with self.subTest(scanner=scanner.__name__):
                self.assertEqual(scanner(emitted, "sample.py")[expected_key], 1)
                self.assertEqual(scanner(discarded, "sample.py"), Counter())

    def test_returned_finding_remains_an_emission_with_distinct_sink(self):
        returned = """
def validate():
    return Finding("PUBLIC_CODE", "visible")
"""
        payload = json.loads(
            literal_base.finding_semantic_signatures(returned)["PUBLIC_CODE"][0]
        )
        self.assertEqual(payload["sink"], ["return"])
        self.assertEqual(
            extended_reachability.reachable_contracts(
                returned,
                "sample.py",
            )[("sample.py", "validate", "PUBLIC_CODE")],
            1,
        )

    def test_container_then_call_sink_is_preserved(self):
        extended = """
def validate(findings):
    findings.extend([Finding("PUBLIC_CODE", "visible")])
"""
        payload = json.loads(
            literal_base.finding_semantic_signatures(extended)["PUBLIC_CODE"][0]
        )
        self.assertEqual(payload["sink"][0], "list")
        self.assertTrue(payload["sink"][1].startswith("call-arg:"))


if __name__ == "__main__":
    unittest.main()
