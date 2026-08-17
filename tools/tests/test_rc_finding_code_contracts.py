from __future__ import annotations

import ast
import hashlib

import rc_finding_code_contracts_base as base


class _DistinctBindingNormalizer(base._FunctionScopeNameNormalizer):
    """Keep alpha-renames compatible without merging distinct same-shaped locals."""

    def _mapping(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> dict[str, str]:
        parameters = self._parameter_names(node)
        parameter_positions = {name: index for index, name in enumerate(parameters)}
        local_names = self._local_store_names(node) - set(parameters)
        binding_shapes = self._binding_shapes(node, parameter_positions, local_names)

        mapping = {name: f"_p{index}" for name, index in parameter_positions.items()}
        first_shapes = {
            name: (binding_shapes.get(name) or ["store"])[0]
            for name in local_names
        }
        shape_ordinals: dict[str, int] = {}
        first_binding_order: list[str] = []

        class FirstBindingCollector(ast.NodeVisitor):
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
                    and item.id in local_names
                    and item.id not in first_binding_order
                ):
                    first_binding_order.append(item.id)

            def visit_ExceptHandler(self, item: ast.ExceptHandler) -> None:
                if (
                    item.name
                    and item.name in local_names
                    and item.name not in first_binding_order
                ):
                    first_binding_order.append(item.name)
                self.generic_visit(item)

        FirstBindingCollector().visit(node)
        for name in sorted(local_names - set(first_binding_order)):
            first_binding_order.append(name)

        for name in first_binding_order:
            structural_binding = first_shapes[name]
            ordinal = shape_ordinals.get(structural_binding, 0)
            shape_ordinals[structural_binding] = ordinal + 1
            digest = hashlib.sha256(structural_binding.encode("utf-8")).hexdigest()[:12]
            mapping[name] = f"_v_{digest}_{ordinal}"
        return mapping


base._FunctionScopeNameNormalizer = _DistinctBindingNormalizer

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


if __name__ == "__main__":
    import unittest

    unittest.main()
