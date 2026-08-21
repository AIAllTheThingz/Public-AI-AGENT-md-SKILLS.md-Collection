from __future__ import annotations

import ast
import copy
import string
import unittest

import rc_finding_code_contracts_base as base
import test_rc_zzzzzzzzzzzzzzzzzzzz_post_emission_sink_and_codeowners as _post_sink  # noqa: F401
import test_rc_zzzzzzzzzzzzzzzzzzzzz_positional_git_init as _positional_git_init  # noqa: F401


# Human-readable Finding message wording is intentionally not a compatibility
# contract, but evaluating a non-literal message expression is executable code.
# If that evaluation raises or changes its dependencies, the Finding is never
# constructed/emitted. Preserve the execution contract without freezing prose.

_original_finding_call_shape = base.finding_call_shape
_original_finding_dependency_nodes = base.finding_dependency_nodes


def _message_expression(node: ast.Call) -> ast.AST | None:
    if len(node.args) >= 2:
        return node.args[1]
    for keyword in node.keywords:
        if keyword.arg == "message":
            return keyword.value
    return None


def _is_inert_literal_message(node: ast.AST) -> bool:
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return True
    if isinstance(node, ast.JoinedStr):
        return all(
            isinstance(value, ast.Constant) and isinstance(value.value, str)
            for value in node.values
        )
    return False


def _format_template_contract(value: str) -> str:
    """Discard prose while retaining str.format field execution structure."""
    try:
        fields = [
            (field_name, conversion, format_spec)
            for _literal, field_name, format_spec, conversion in string.Formatter().parse(value)
            if field_name is not None
        ]
    except ValueError:
        # An invalid format string can itself raise during message evaluation.
        return "<invalid-format-template>"
    return repr(fields)


class _MessageExecutionNormalizer(ast.NodeTransformer):
    """Normalize prose fragments but keep executable message structure."""

    def visit_JoinedStr(self, node: ast.JoinedStr) -> ast.AST:
        cloned = copy.deepcopy(node)
        normalized: list[ast.AST] = []
        for value in cloned.values:
            if isinstance(value, ast.Constant) and isinstance(value.value, str):
                normalized.append(ast.Constant(value="<message-text>"))
            else:
                normalized.append(self.visit(value))
        cloned.values = normalized
        return cloned

    def visit_Call(self, node: ast.Call) -> ast.AST:
        cloned = copy.deepcopy(node)
        cloned = self.generic_visit(cloned)
        if (
            isinstance(cloned.func, ast.Attribute)
            and cloned.func.attr == "format"
            and isinstance(cloned.func.value, ast.Constant)
            and isinstance(cloned.func.value.value, str)
        ):
            cloned.func.value.value = (
                "<format-template:"
                + _format_template_contract(cloned.func.value.value)
                + ">"
            )
        return cloned


def _message_execution_shape(node: ast.AST) -> str:
    cloned = copy.deepcopy(node)
    cloned = _MessageExecutionNormalizer().visit(cloned)
    ast.fix_missing_locations(cloned)
    return base.canonical_ast(cloned)


def _finding_call_shape_with_message_execution(node: ast.Call) -> dict[str, object]:
    shape = dict(_original_finding_call_shape(node))
    message = _message_expression(node)
    if message is not None and not _is_inert_literal_message(message):
        shape["messageEvaluation"] = _message_execution_shape(message)
    return shape


def _finding_dependency_nodes_with_message_execution(node: ast.Call) -> list[ast.AST]:
    dependencies = list(_original_finding_dependency_nodes(node))
    message = _message_expression(node)
    if message is not None and not _is_inert_literal_message(message):
        dependencies.append(message)
    return dependencies


# FindingSignatureVisitor resolves these module globals at execution time. The
# composed sink/reachability layers call through the same semantic visitor, so
# this strengthens the permanent contract without replacing prior overlays.
base.finding_call_shape = _finding_call_shape_with_message_execution
base.finding_dependency_nodes = _finding_dependency_nodes_with_message_execution


class ReleaseCandidateExecutableFindingMessageTests(unittest.TestCase):
    def test_literal_message_rewording_remains_compatible(self) -> None:
        original = '''
from standards_tools import Finding

def run(findings):
    findings.append(Finding("PUBLIC_CODE", "old wording"))
'''
        reworded = '''
from standards_tools import Finding

def run(findings):
    findings.append(Finding("PUBLIC_CODE", "clearer wording"))
'''
        self.assertEqual(
            base.finding_semantic_signatures(original, "sample.py"),
            base.finding_semantic_signatures(reworded, "sample.py"),
        )

    def test_executable_message_expression_changes_contract(self) -> None:
        literal = '''
from standards_tools import Finding

def run(findings):
    findings.append(Finding("PUBLIC_CODE", "message"))
'''
        executable = '''
from standards_tools import Finding

def explode():
    raise RuntimeError("message evaluation failed")

def run(findings):
    findings.append(Finding("PUBLIC_CODE", explode()))
'''
        self.assertNotEqual(
            base.finding_semantic_signatures(literal, "sample.py"),
            base.finding_semantic_signatures(executable, "sample.py"),
        )

    def test_message_helper_semantics_are_dependencies(self) -> None:
        safe = '''
from standards_tools import Finding

def render_message():
    return "message"

def run(findings):
    findings.append(Finding("PUBLIC_CODE", render_message()))
'''
        raising = '''
from standards_tools import Finding

def render_message():
    raise RuntimeError("boom")

def run(findings):
    findings.append(Finding("PUBLIC_CODE", render_message()))
'''
        self.assertNotEqual(
            base.finding_semantic_signatures(safe, "sample.py"),
            base.finding_semantic_signatures(raising, "sample.py"),
        )

    def test_fstring_prose_rewording_keeps_dynamic_evaluation_contract(self) -> None:
        original = '''
from standards_tools import Finding

def run(findings, path):
    findings.append(Finding("PUBLIC_CODE", f"Missing {path}"))
'''
        reworded = '''
from standards_tools import Finding

def run(findings, path):
    findings.append(Finding("PUBLIC_CODE", f"Could not find {path}"))
'''
        self.assertEqual(
            base.finding_semantic_signatures(original, "sample.py"),
            base.finding_semantic_signatures(reworded, "sample.py"),
        )

    def test_message_keyword_is_execution_tracked(self) -> None:
        literal = '''
from standards_tools import Finding

def run(findings):
    findings.append(Finding(code="PUBLIC_CODE", message="message"))
'''
        executable = '''
from standards_tools import Finding

def explode():
    raise RuntimeError("boom")

def run(findings):
    findings.append(Finding(code="PUBLIC_CODE", message=explode()))
'''
        self.assertNotEqual(
            base.finding_semantic_signatures(literal, "sample.py"),
            base.finding_semantic_signatures(executable, "sample.py"),
        )


if __name__ == "__main__":
    unittest.main()
