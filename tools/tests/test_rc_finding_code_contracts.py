from __future__ import annotations

import ast
import copy
import hashlib

import rc_finding_code_contracts_base as base


class _UsageShapeNameNormalizer(ast.NodeTransformer):
    def __init__(
        self,
        target: str,
        parameter_positions: dict[str, int],
        local_names: set[str],
    ) -> None:
        self.target = target
        self.parameter_positions = parameter_positions
        self.local_names = local_names

    def visit_Name(self, node: ast.Name) -> ast.AST:
        if node.id == self.target:
            node.id = "_self"
        elif node.id in self.parameter_positions:
            node.id = f"_p{self.parameter_positions[node.id]}"
        elif node.id in self.local_names:
            node.id = "_local"
        return node


class _DistinctBindingNormalizer(base._FunctionScopeNameNormalizer):
    """Keep alpha-renames stable without collapsing distinct same-shaped locals."""

    @staticmethod
    def _usage_shapes(
        node: ast.FunctionDef | ast.AsyncFunctionDef,
        parameter_positions: dict[str, int],
        local_names: set[str],
    ) -> dict[str, list[str]]:
        shapes: dict[str, list[str]] = {name: [] for name in local_names}
        parents: dict[ast.AST, ast.AST] = {}
        for parent in ast.walk(node):
            for child in ast.iter_child_nodes(parent):
                parents[child] = parent

        def belongs_to_function(item: ast.AST) -> bool:
            current = item
            while current in parents:
                current = parents[current]
                if isinstance(current, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    return current is node
                if isinstance(current, (ast.Lambda, ast.ClassDef)):
                    return False
            return False

        def enclosing_statement(item: ast.AST) -> ast.stmt | None:
            current = item
            while current in parents:
                current = parents[current]
                if isinstance(current, ast.stmt):
                    return current
            return None

        for item in ast.walk(node):
            if not (
                isinstance(item, ast.Name)
                and isinstance(item.ctx, ast.Load)
                and item.id in local_names
                and belongs_to_function(item)
            ):
                continue
            statement = enclosing_statement(item)
            if statement is None:
                continue
            cloned = copy.deepcopy(statement)
            cloned = _UsageShapeNameNormalizer(
                item.id,
                parameter_positions,
                local_names,
            ).visit(cloned)
            cloned = base.FindingMessageNormalizer().visit(cloned)
            ast.fix_missing_locations(cloned)
            shapes[item.id].append(base.canonical_ast(cloned))

        for values in shapes.values():
            values.sort()
        return shapes

    def _mapping(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> dict[str, str]:
        parameters = self._parameter_names(node)
        parameter_positions = {name: index for index, name in enumerate(parameters)}
        local_names = self._local_store_names(node) - set(parameters)
        binding_shapes = self._binding_shapes(node, parameter_positions, local_names)
        usage_shapes = self._usage_shapes(node, parameter_positions, local_names)

        mapping = {name: f"_p{index}" for name, index in parameter_positions.items()}
        for name in local_names:
            structural_binding = (binding_shapes.get(name) or ["store"])[0]
            semantic_usage = "\n".join(usage_shapes.get(name) or ["<unused>"])
            identity = f"{structural_binding}\n{semantic_usage}"
            digest = hashlib.sha256(identity.encode("utf-8")).hexdigest()[:16]
            mapping[name] = f"_v_{digest}"
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

    def test_unrelated_same_shaped_local_does_not_change_existing_identity(self):
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
            "an unrelated same-shaped local must not alter an existing identity",
        )


if __name__ == "__main__":
    import unittest

    unittest.main()
