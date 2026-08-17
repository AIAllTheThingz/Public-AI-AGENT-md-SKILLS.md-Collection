from __future__ import annotations

import ast
import hashlib

import rc_finding_code_contracts_base as base


class _CollisionSafeBindingNormalizer(base._FunctionScopeNameNormalizer):
    """Disambiguate real local-binding collisions without churning unique identities."""

    @staticmethod
    def _loaded_local_names(
        node: ast.FunctionDef | ast.AsyncFunctionDef,
        local_names: set[str],
    ) -> set[str]:
        loaded: set[str] = set()

        class Collector(ast.NodeVisitor):
            def visit_FunctionDef(self, item: ast.FunctionDef) -> None:
                if item is node:
                    for statement in item.body:
                        self.visit(statement)

            def visit_AsyncFunctionDef(self, item: ast.AsyncFunctionDef) -> None:
                if item is node:
                    for statement in item.body:
                        self.visit(statement)

            def visit_Lambda(self, item: ast.Lambda) -> None:
                return

            def visit_ClassDef(self, item: ast.ClassDef) -> None:
                return

            def visit_Name(self, item: ast.Name) -> None:
                if isinstance(item.ctx, ast.Load) and item.id in local_names:
                    loaded.add(item.id)

        Collector().visit(node)
        return loaded

    @staticmethod
    def _first_binding_order(
        node: ast.FunctionDef | ast.AsyncFunctionDef,
        names: set[str],
    ) -> list[str]:
        order: list[str] = []

        class Collector(ast.NodeVisitor):
            def visit_FunctionDef(self, item: ast.FunctionDef) -> None:
                if item is node:
                    for statement in item.body:
                        self.visit(statement)

            def visit_AsyncFunctionDef(self, item: ast.AsyncFunctionDef) -> None:
                if item is node:
                    for statement in item.body:
                        self.visit(statement)

            def visit_Lambda(self, item: ast.Lambda) -> None:
                return

            def visit_ClassDef(self, item: ast.ClassDef) -> None:
                return

            def visit_Name(self, item: ast.Name) -> None:
                if (
                    isinstance(item.ctx, (ast.Store, ast.Del))
                    and item.id in names
                    and item.id not in order
                ):
                    order.append(item.id)

            def visit_ExceptHandler(self, item: ast.ExceptHandler) -> None:
                if item.name and item.name in names and item.name not in order:
                    order.append(item.name)
                self.generic_visit(item)

        Collector().visit(node)
        order.extend(sorted(names - set(order)))
        return order

    def _mapping(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> dict[str, str]:
        parameters = self._parameter_names(node)
        parameter_positions = {name: index for index, name in enumerate(parameters)}
        local_names = self._local_store_names(node) - set(parameters)
        binding_shapes = self._binding_shapes(node, parameter_positions, local_names)
        loaded_names = self._loaded_local_names(node, local_names)

        mapping = {name: f"_p{index}" for name, index in parameter_positions.items()}
        shape_by_name: dict[str, str] = {}
        for name in local_names:
            structural_binding = (binding_shapes.get(name) or ["store"])[0]
            shape_by_name[name] = structural_binding
            digest = hashlib.sha256(structural_binding.encode("utf-8")).hexdigest()[:12]
            mapping[name] = f"_v_{digest}"

        groups: dict[str, set[str]] = {}
        for name in loaded_names:
            groups.setdefault(shape_by_name[name], set()).add(name)

        for structural_binding, names in groups.items():
            if len(names) < 2:
                continue
            digest = hashlib.sha256(structural_binding.encode("utf-8")).hexdigest()[:12]
            for ordinal, name in enumerate(self._first_binding_order(node, names)):
                mapping[name] = f"_v_{digest}_{ordinal}"

        return mapping


base._FunctionScopeNameNormalizer = _CollisionSafeBindingNormalizer

CHECKPOINT_COMMIT = base.CHECKPOINT_COMMIT
normalized_semantic_ast = base.normalized_semantic_ast
finding_semantic_signatures = base.finding_semantic_signatures
published_signatures = base.published_signatures


class ReleaseCandidateFindingCodeContractTests(
    base.ReleaseCandidateFindingCodeContractTests
):
    def test_same_shaped_locals_keep_distinct_semantic_identities(self):
        original = '''
def run(flag):
    passed = []
    failed = []
    if flag:
        passed.append("ok")
    else:
        failed.append("bad")
    if passed:
        Finding("PUBLIC_CODE", "result", path="sample")
'''
        swapped_condition = original.replace(
            "if passed:\n        Finding", "if failed:\n        Finding"
        )
        renamed = original.replace("passed", "accepted").replace("failed", "rejected")
        self.assertNotEqual(
            finding_semantic_signatures(original),
            finding_semantic_signatures(swapped_condition),
            "distinct same-shaped locals must not collapse to one normalized identity",
        )
        self.assertEqual(
            finding_semantic_signatures(original),
            finding_semantic_signatures(renamed),
            "rename-only changes must remain alpha-equivalent",
        )

    def test_unrelated_unused_same_shaped_local_does_not_renumber_existing_identity(self):
        original = '''
def run(flag):
    passed = []
    if flag:
        passed.append("ok")
    if passed:
        Finding("PUBLIC_CODE", "result", path="sample")
'''
        with_scratch = original.replace(
            "    passed = []\n", "    scratch = []\n    passed = []\n"
        )
        self.assertEqual(
            finding_semantic_signatures(original),
            finding_semantic_signatures(with_scratch),
            "an unrelated unused same-shaped local must not renumber an existing binding",
        )


if __name__ == "__main__":
    import unittest

    unittest.main()
