from __future__ import annotations

import ast
import unittest

import rc_finding_code_contracts_base as base


_ORIGINAL_MODULE_BINDINGS = base.module_semantic_bindings
_ORIGINAL_DEPENDENCY_SNAPSHOT = base.FindingSignatureVisitor._dependency_snapshot
_ORIGINAL_VISIT_FUNCTION = base.FindingSignatureVisitor.visit_FunctionDef
_ORIGINAL_VISIT_ASYNC_FUNCTION = base.FindingSignatureVisitor.visit_AsyncFunctionDef


def _function_defaults(
    node: ast.FunctionDef | ast.AsyncFunctionDef,
) -> dict[str, ast.AST]:
    defaults: dict[str, ast.AST] = {}
    positional = [*node.args.posonlyargs, *node.args.args]
    if node.args.defaults:
        for argument, value in zip(
            positional[-len(node.args.defaults) :],
            node.args.defaults,
        ):
            defaults[argument.arg] = value
    for argument, value in zip(node.args.kwonlyargs, node.args.kw_defaults):
        if value is not None:
            defaults[argument.arg] = value
    return defaults


def _with_default_scope(original):
    def wrapped(self, node):
        stack = getattr(self, "_finding_default_stack", None)
        if stack is None:
            stack = []
            self._finding_default_stack = stack
        stack.append(_function_defaults(node))
        try:
            return original(self, node)
        finally:
            stack.pop()

    return wrapped


def _module_semantic_bindings_with_finding_provenance(
    tree: ast.Module,
) -> dict[str, ast.AST]:
    definitions = _ORIGINAL_MODULE_BINDINGS(tree)
    provenance: ast.AST | None = None

    # Track the effective module-level binding in source order.  The compatibility
    # scanner recognizes the bare Finding constructor, so its provenance must be
    # part of every Finding semantic signature just as helper/data dependencies are.
    for statement in tree.body:
        if isinstance(statement, ast.ImportFrom):
            for alias in statement.names:
                bound = alias.asname or alias.name
                if bound == "Finding":
                    provenance = ast.Constant(
                        value=f"from:{statement.module or ''}:{alias.name}"
                    )
        elif isinstance(statement, ast.Assign):
            if any(isinstance(target, ast.Name) and target.id == "Finding" for target in statement.targets):
                provenance = statement.value
        elif isinstance(statement, ast.AnnAssign):
            if (
                isinstance(statement.target, ast.Name)
                and statement.target.id == "Finding"
                and statement.value is not None
            ):
                provenance = statement.value
        elif isinstance(statement, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if statement.name == "Finding":
                provenance = statement

    if provenance is not None:
        definitions["__finding_constructor_provenance__"] = provenance
    return definitions


def _dependency_snapshot_with_defaults_and_constructor(
    self: base.FindingSignatureVisitor,
    nodes: list[ast.AST],
) -> dict[str, str]:
    snapshot = dict(_ORIGINAL_DEPENDENCY_SNAPSHOT(self, nodes))
    pending: set[str] = set()
    for node in nodes:
        pending.update(base.dependency_names(node))

    stack = getattr(self, "_finding_default_stack", [])
    if stack:
        for name, value in stack[-1].items():
            if name in pending:
                snapshot[f"default:{name}"] = base.normalized_semantic_ast(value)

    provenance = self.module_definitions.get("__finding_constructor_provenance__")
    if provenance is not None:
        snapshot["Finding"] = base.normalized_semantic_ast(provenance)

    return dict(sorted(snapshot.items()))


base.module_semantic_bindings = _module_semantic_bindings_with_finding_provenance
base.FindingSignatureVisitor._dependency_snapshot = (
    _dependency_snapshot_with_defaults_and_constructor
)
base.FindingSignatureVisitor.visit_FunctionDef = _with_default_scope(
    _ORIGINAL_VISIT_FUNCTION
)
base.FindingSignatureVisitor.visit_AsyncFunctionDef = _with_default_scope(
    _ORIGINAL_VISIT_ASYNC_FUNCTION
)


class FunctionDefaultAndFindingProvenanceTests(unittest.TestCase):
    def test_finding_dependency_tracks_parameter_default(self):
        enabled = '''
from standards_tools import Finding

def run(enabled=True):
    if enabled:
        Finding("PUBLIC_CODE", "message")
'''
        disabled = enabled.replace("enabled=True", "enabled=False")
        self.assertNotEqual(
            base.finding_semantic_signatures(enabled, "sample.py"),
            base.finding_semantic_signatures(disabled, "sample.py"),
        )

    def test_unrelated_parameter_default_remains_compatible(self):
        original = '''
from standards_tools import Finding

def run(unused=True):
    Finding("PUBLIC_CODE", "message")
'''
        changed = original.replace("unused=True", "unused=False")
        self.assertEqual(
            base.finding_semantic_signatures(original, "sample.py"),
            base.finding_semantic_signatures(changed, "sample.py"),
        )

    def test_kwonly_default_is_tracked_when_finding_depends_on_it(self):
        enabled = '''
from standards_tools import Finding

def run(*, enabled=True):
    if enabled:
        Finding("PUBLIC_CODE", "message")
'''
        disabled = enabled.replace("enabled=True", "enabled=False")
        self.assertNotEqual(
            base.finding_semantic_signatures(enabled, "sample.py"),
            base.finding_semantic_signatures(disabled, "sample.py"),
        )

    def test_finding_import_provenance_is_part_of_signature(self):
        published = '''
from standards_tools import Finding

def run():
    Finding("PUBLIC_CODE", "message")
'''
        replaced = published.replace(
            "from standards_tools import Finding",
            "from alternate_tools import Finding",
        )
        self.assertNotEqual(
            base.finding_semantic_signatures(published, "sample.py"),
            base.finding_semantic_signatures(replaced, "sample.py"),
        )

    def test_same_finding_import_provenance_remains_stable(self):
        left = '''
from standards_tools import Finding

def run():
    Finding("PUBLIC_CODE", "first wording")
'''
        right = left.replace("first wording", "improved wording")
        self.assertEqual(
            base.finding_semantic_signatures(left, "sample.py"),
            base.finding_semantic_signatures(right, "sample.py"),
        )


if __name__ == "__main__":
    unittest.main()
