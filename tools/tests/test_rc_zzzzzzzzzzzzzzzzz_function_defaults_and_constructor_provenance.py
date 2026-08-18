from __future__ import annotations

import ast
import unittest

import rc_finding_code_contracts_base as literal_base
import test_rc_zzzzzzzzzzzzzzz_finding_producer_invocation as _producer_invocation  # noqa: F401
import test_rc_zzzzzzzzzzzzzzzz_stable_legal_contracts as _stable_legal_contracts  # noqa: F401


# Final composition layer for PR #71. Preserve all prior execution/sink/call-graph
# patches while adding two pieces of semantic identity that Python applies before
# the finding-producing body executes: function defaults and constructor binding.


# ---------------------------------------------------------------------------
# Bind imported/assigned Finding constructor provenance into dependency snapshots.
# ---------------------------------------------------------------------------

_previous_module_semantic_bindings = literal_base.module_semantic_bindings
_previous_finding_dependency_nodes = literal_base.finding_dependency_nodes


def _module_execution_statements(statements: list[ast.stmt]):
    """Yield statements executed in module scope without descending into definitions."""
    for statement in statements:
        yield statement
        if isinstance(statement, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            continue
        if isinstance(statement, ast.If):
            yield from _module_execution_statements(statement.body)
            yield from _module_execution_statements(statement.orelse)
        elif isinstance(statement, (ast.For, ast.AsyncFor, ast.While)):
            yield from _module_execution_statements(statement.body)
            yield from _module_execution_statements(statement.orelse)
        elif isinstance(statement, (ast.With, ast.AsyncWith)):
            yield from _module_execution_statements(statement.body)
        elif isinstance(statement, ast.Try) or (
            hasattr(ast, "TryStar") and isinstance(statement, ast.TryStar)
        ):
            yield from _module_execution_statements(statement.body)
            for handler in statement.handlers:
                yield from _module_execution_statements(handler.body)
            yield from _module_execution_statements(statement.orelse)
            yield from _module_execution_statements(statement.finalbody)
        elif isinstance(statement, ast.Match):
            for case in statement.cases:
                yield from _module_execution_statements(case.body)


def _module_semantic_bindings(tree: ast.Module) -> dict[str, ast.AST]:
    definitions = _previous_module_semantic_bindings(tree)

    # Import provenance is part of a public constructor's identity even when the
    # import is intentionally wrapped in module-level execution control such as
    # validate-all's bytecode-containment try/finally. Do not descend into
    # function/class definitions, where Python binding rules are different.
    for statement in _module_execution_statements(tree.body):
        if isinstance(statement, ast.ImportFrom):
            module = statement.module or ""
            for alias in statement.names:
                if alias.name == "*":
                    continue
                bound_name = alias.asname or alias.name
                definitions[bound_name] = ast.Constant(
                    value=f"import-from:{module}:{alias.name}"
                )
        elif isinstance(statement, ast.Import):
            for alias in statement.names:
                bound_name = alias.asname or alias.name.split(".", 1)[0]
                definitions[bound_name] = ast.Constant(
                    value=f"import:{alias.name}"
                )

    return definitions


def _finding_dependency_nodes(node: ast.Call) -> list[ast.AST]:
    dependencies = list(_previous_finding_dependency_nodes(node))
    # The public Finding constructor is itself a dependency. If it is imported,
    # rebound, or assigned differently, module_semantic_bindings now gives that
    # name a provenance node that becomes part of the semantic signature.
    if isinstance(node.func, ast.Name) and node.func.id == "Finding":
        dependencies.append(node.func)
    return dependencies


literal_base.module_semantic_bindings = _module_semantic_bindings
literal_base.finding_dependency_nodes = _finding_dependency_nodes


# ---------------------------------------------------------------------------
# Include body-relevant function defaults in finding semantic context.
# ---------------------------------------------------------------------------

_previous_visit_function_def = literal_base.FindingSignatureVisitor.visit_FunctionDef
_previous_visit_async_function_def = literal_base.FindingSignatureVisitor.visit_AsyncFunctionDef


def _body_loaded_names(node: ast.FunctionDef | ast.AsyncFunctionDef) -> set[str]:
    names: set[str] = set()
    for statement in node.body:
        names.update(
            item.id
            for item in ast.walk(statement)
            if isinstance(item, ast.Name) and isinstance(item.ctx, ast.Load)
        )
    return names


def _relevant_default_entries(
    node: ast.FunctionDef | ast.AsyncFunctionDef,
) -> list[tuple[str, ast.AST]]:
    loaded = _body_loaded_names(node)
    result: list[tuple[str, ast.AST]] = []

    positional = [*node.args.posonlyargs, *node.args.args]
    if node.args.defaults:
        for argument, default in zip(
            positional[-len(node.args.defaults) :],
            node.args.defaults,
        ):
            if argument.arg in loaded:
                result.append((argument.arg, default))

    for argument, default in zip(node.args.kwonlyargs, node.args.kw_defaults):
        if default is not None and argument.arg in loaded:
            result.append((argument.arg, default))

    return result


def _visit_function_with_defaults(self, node, previous) -> None:
    entries = _relevant_default_entries(node)
    markers = [
        f"function-default:{name}={literal_base.normalized_semantic_ast(default)}"
        for name, default in entries
    ]
    defaults = [default for _, default in entries]

    self.context.extend(markers)
    self.context_nodes.extend(defaults)
    try:
        previous(self, node)
    finally:
        if defaults:
            del self.context_nodes[-len(defaults) :]
        if markers:
            del self.context[-len(markers) :]


def _visit_function_def(self, node: ast.FunctionDef) -> None:
    _visit_function_with_defaults(self, node, _previous_visit_function_def)


def _visit_async_function_def(self, node: ast.AsyncFunctionDef) -> None:
    _visit_function_with_defaults(self, node, _previous_visit_async_function_def)


literal_base.FindingSignatureVisitor.visit_FunctionDef = _visit_function_def
literal_base.FindingSignatureVisitor.visit_AsyncFunctionDef = _visit_async_function_def


# ---------------------------------------------------------------------------
# Permanent regressions.
# ---------------------------------------------------------------------------


class ReleaseCandidateFunctionDefaultsAndConstructorProvenanceTests(unittest.TestCase):
    def test_body_relevant_default_changes_finding_semantics(self) -> None:
        enabled = '''
from standards_tools import Finding

def run(enabled=True):
    if enabled:
        Finding("PUBLIC_CODE", "message")
'''
        disabled = enabled.replace("enabled=True", "enabled=False")

        expected = literal_base.finding_semantic_signatures(enabled)
        actual = literal_base.finding_semantic_signatures(disabled)
        self.assertNotEqual(expected, actual)
        self.assertTrue(
            any(
                "function-default" in signature
                for signature in expected["PUBLIC_CODE"]
            )
        )

    def test_unrelated_default_does_not_freeze_finding_contract(self) -> None:
        first = '''
from standards_tools import Finding

def run(enabled=True, label="first"):
    if enabled:
        Finding("PUBLIC_CODE", "message")
'''
        second = first.replace('label="first"', 'label="second"')
        self.assertEqual(
            literal_base.finding_semantic_signatures(first),
            literal_base.finding_semantic_signatures(second),
        )

    def test_kw_only_default_changes_finding_semantics(self) -> None:
        enabled = '''
from standards_tools import Finding

def run(*, enabled=True):
    if enabled:
        Finding("PUBLIC_CODE", "message")
'''
        disabled = enabled.replace("enabled=True", "enabled=False")
        self.assertNotEqual(
            literal_base.finding_semantic_signatures(enabled),
            literal_base.finding_semantic_signatures(disabled),
        )

    def test_finding_constructor_import_provenance_is_preserved(self) -> None:
        published = '''
from standards_tools import Finding

def run():
    Finding("PUBLIC_CODE", "message")
'''
        replaced = published.replace(
            "from standards_tools import Finding",
            "from alternate_tools import Finding",
        )

        expected = literal_base.finding_semantic_signatures(published)
        actual = literal_base.finding_semantic_signatures(replaced)
        self.assertNotEqual(expected, actual)
        self.assertTrue(
            any(
                "import-from:standards_tools:Finding" in signature
                for signature in expected["PUBLIC_CODE"]
            )
        )

    def test_finding_constructor_alias_provenance_is_preserved(self) -> None:
        published = '''
from standards_tools import Finding as Finding

def run():
    Finding("PUBLIC_CODE", "message")
'''
        replaced = published.replace(
            "from standards_tools import Finding as Finding",
            "from alternate_tools import Finding as Finding",
        )
        self.assertNotEqual(
            literal_base.finding_semantic_signatures(published),
            literal_base.finding_semantic_signatures(replaced),
        )

    def test_finding_constructor_import_inside_module_try_is_preserved(self) -> None:
        direct = '''
from standards_tools import Finding

def run():
    Finding("PUBLIC_CODE", "message")
'''
        wrapped = '''
try:
    from standards_tools import Finding
finally:
    cleanup = True

def run():
    Finding("PUBLIC_CODE", "message")
'''
        alternate = wrapped.replace(
            "from standards_tools import Finding",
            "from alternate_tools import Finding",
        )

        direct_signature = literal_base.finding_semantic_signatures(direct)
        wrapped_signature = literal_base.finding_semantic_signatures(wrapped)
        alternate_signature = literal_base.finding_semantic_signatures(alternate)
        self.assertEqual(
            direct_signature["PUBLIC_CODE"][0],
            wrapped_signature["PUBLIC_CODE"][0],
        )
        self.assertNotEqual(wrapped_signature, alternate_signature)


if __name__ == "__main__":
    unittest.main()
