from __future__ import annotations

import ast
import copy
import hashlib
import json
import unittest
from collections import Counter

import rc_finding_code_contracts_base as literal_base
import test_rc_extended_finding_reachability as extended_reachability
import test_rc_finding_reachability as basic_reachability
import test_rc_parameterized_finding_codes as parameterized_active
import test_rc_parameterized_finding_reachability as parameterized_reachability
import test_rc_zzzzzzzzzzz_context_manager_entry_execution as context_manager_execution
import test_rc_zzzzzzzzzzzz_execution_prerequisites as execution_prerequisites
import test_rc_zzzzzzzzzzzzzzzzzzz_post_emission_completion as post_completion
import test_rc_zzzzzzzzzzzzzzzzzzzzzz_executable_message_evaluation as _message_evaluation  # noqa: F401


# Python evaluates class decorators, base expressions, and keyword values such as
# metaclass= before it executes the class body. A failure in those prerequisite
# expressions prevents every Finding or parameterized finding producer in the
# body from running. Generic AST traversal loses that execution boundary.

_CLASS_FAILS = False
_CLASS_SUCCEEDS = True
_CLASS_UNKNOWN = None


def _class_prerequisites(node: ast.ClassDef) -> list[tuple[str, ast.AST]]:
    items: list[tuple[str, ast.AST]] = []
    for index, decorator in enumerate(node.decorator_list):
        items.append((f"decorator:{index}", decorator))
    for index, base in enumerate(node.bases):
        items.append((f"base:{index}", base))
    for index, keyword in enumerate(node.keywords):
        label = keyword.arg if keyword.arg is not None else "**"
        items.append((f"keyword:{index}:{label}", keyword.value))
    return items


def _direct_call_outcome(
    expression: ast.AST,
    definitions: dict[str, ast.AST],
) -> bool | None:
    if execution_prerequisites._expression_statically_raises(expression, {}):
        return _CLASS_FAILS

    if isinstance(expression, ast.Constant):
        return _CLASS_SUCCEEDS

    if not isinstance(expression, ast.Call) or not isinstance(expression.func, ast.Name):
        return _CLASS_UNKNOWN

    definition = definitions.get(expression.func.id)
    if isinstance(definition, (ast.FunctionDef, ast.AsyncFunctionDef)):
        outcome = context_manager_execution._callable_direct_outcome(definition)
        if outcome is context_manager_execution._ENTRY_FAILS:
            return _CLASS_FAILS
        if outcome is context_manager_execution._ENTRY_SUCCEEDS:
            return _CLASS_SUCCEEDS
    return _CLASS_UNKNOWN


def _prerequisite_dependency(
    prerequisites: list[tuple[str, ast.AST]],
) -> ast.AST:
    values: list[ast.AST] = []
    for label, expression in prerequisites:
        values.append(ast.Constant(value=label))
        values.append(copy.deepcopy(expression))
    if not values:
        return ast.Constant(value="class:no-prerequisites")
    dependency = ast.Tuple(elts=values, ctx=ast.Load())
    ast.fix_missing_locations(dependency)
    return dependency


def _prerequisite_digest(prerequisites: list[tuple[str, ast.AST]]) -> str:
    material = "\n".join(
        f"{label}:{literal_base.normalized_semantic_ast(expression)}"
        for label, expression in prerequisites
    )
    return hashlib.sha256(material.encode("utf-8")).hexdigest()[:16]


def _class_marker(phase: str, prerequisites: list[tuple[str, ast.AST]]) -> str:
    return f"class:{phase}:requires-construction:{_prerequisite_digest(prerequisites)}"


def _literal_expression_with_context(
    visitor,
    marker: str,
    dependency: ast.AST,
    expression: ast.AST,
) -> None:
    visitor.context.append(marker)
    visitor.context_nodes.append(dependency)
    try:
        visitor.visit(expression)
    finally:
        visitor.context_nodes.pop()
        visitor.context.pop()


def _literal_visit_class(self, node: ast.ClassDef) -> None:
    definitions = getattr(self, "_context_manager_definitions", {})
    completed: list[tuple[str, ast.AST]] = []

    for index, (label, expression) in enumerate(_class_prerequisites(node)):
        if completed:
            _literal_expression_with_context(
                self,
                _class_marker(f"prerequisite:{index}", completed),
                _prerequisite_dependency(completed),
                expression,
            )
        else:
            self.visit(expression)
        completed.append((label, expression))
        if _direct_call_outcome(expression, definitions) is _CLASS_FAILS:
            return

    if completed:
        self._with_context(
            _class_marker("body", completed),
            _prerequisite_dependency(completed),
            node.body,
        )
    else:
        self._visit_block(node.body)


literal_base.FindingSignatureVisitor.visit_ClassDef = _literal_visit_class


# Literal reachability visitors need the same execution boundary. Their module
# hooks already carry the runtime definition map from the context-manager layer.
def _patch_literal_reachability(visitor_type) -> None:
    def visit_class(self, node: ast.ClassDef) -> None:
        definitions = getattr(self, "_context_manager_definitions", {})
        for _label, expression in _class_prerequisites(node):
            self.visit(expression)
            if _direct_call_outcome(expression, definitions) is _CLASS_FAILS:
                return
        self._visit_block(node.body)

    visitor_type.visit_ClassDef = visit_class


_patch_literal_reachability(basic_reachability.ReachableFindingVisitor)
_patch_literal_reachability(extended_reachability.ExtendedReachableFindingVisitor)


# Parameterized semantic and reachable call-site visitors already expose the same
# branch-context primitive used by the with-entry execution layer.
def _parameterized_visit_class(self, node: ast.ClassDef) -> None:
    definitions = getattr(self, "_context_manager_definitions", {})
    completed: list[tuple[str, ast.AST]] = []

    for index, (label, expression) in enumerate(_class_prerequisites(node)):
        if completed:
            self._with_context(
                _class_marker(f"prerequisite:{index}", completed),
                _prerequisite_dependency(completed),
                [ast.Expr(value=expression)],
            )
        else:
            self.visit(expression)
        completed.append((label, expression))
        if _direct_call_outcome(expression, definitions) is _CLASS_FAILS:
            return

    if completed:
        self._with_context(
            _class_marker("body", completed),
            _prerequisite_dependency(completed),
            node.body,
        )
    else:
        for statement in node.body:
            self.visit(statement)


parameterized_active.BranchAwareParameterizedCallSiteVisitor.visit_ClassDef = (
    _parameterized_visit_class
)
parameterized_active.base.ParameterizedCallSiteVisitor = (
    parameterized_active.BranchAwareParameterizedCallSiteVisitor
)
parameterized_reachability.ReachableParameterizedCallSiteVisitor.visit_ClassDef = (
    _parameterized_visit_class
)


class ReleaseCandidateClassConstructionExecutionTests(unittest.TestCase):
    def test_raising_base_expression_hides_literal_finding(self) -> None:
        source = '''
def explode():
    raise RuntimeError("base evaluation failed")

def validate(findings):
    class Broken(explode()):
        findings.append(Finding("PUBLIC_CODE", "hidden"))
'''
        self.assertNotIn(
            "PUBLIC_CODE",
            literal_base.finding_semantic_signatures(source, "sample.py"),
        )
        self.assertEqual(
            basic_reachability.reachable_literal_finding_contracts(
                source, "sample.py"
            ),
            Counter(),
        )
        self.assertEqual(
            extended_reachability.reachable_contracts(source, "sample.py"),
            Counter(),
        )
        normal, _abnormal = post_completion._completion_counts(source, "sample.py")
        self.assertEqual(normal, Counter())

    def test_unknown_base_adds_class_construction_identity(self) -> None:
        direct = '''
def validate(findings):
    findings.append(Finding("PUBLIC_CODE", "visible"))
'''
        wrapped = '''
def validate(findings):
    class Wrapped(dynamic_base()):
        findings.append(Finding("PUBLIC_CODE", "visible"))
'''
        expected = literal_base.finding_semantic_signatures(direct, "sample.py")
        actual = literal_base.finding_semantic_signatures(wrapped, "sample.py")
        self.assertNotEqual(expected, actual)
        payload = json.loads(actual["PUBLIC_CODE"][0])
        self.assertTrue(
            any(marker.startswith("class:body:requires-construction") for marker in payload["context"]),
            payload["context"],
        )

    def test_base_helper_semantics_are_dependencies(self) -> None:
        safe = '''
def choose_base():
    return object

def validate(findings):
    class Wrapped(choose_base()):
        findings.append(Finding("PUBLIC_CODE", "visible"))
'''
        raising = '''
def choose_base():
    raise RuntimeError("stop")

def validate(findings):
    class Wrapped(choose_base()):
        findings.append(Finding("PUBLIC_CODE", "visible"))
'''
        self.assertIn(
            "PUBLIC_CODE",
            literal_base.finding_semantic_signatures(safe, "sample.py"),
        )
        self.assertNotIn(
            "PUBLIC_CODE",
            literal_base.finding_semantic_signatures(raising, "sample.py"),
        )

    def test_raising_metaclass_keyword_hides_literal_finding(self) -> None:
        source = '''
def explode():
    raise RuntimeError("metaclass evaluation failed")

def validate(findings):
    class Broken(metaclass=explode()):
        findings.append(Finding("PUBLIC_CODE", "hidden"))
'''
        self.assertNotIn(
            "PUBLIC_CODE",
            literal_base.finding_semantic_signatures(source, "sample.py"),
        )
        self.assertEqual(
            extended_reachability.reachable_contracts(source, "sample.py"),
            Counter(),
        )

    def test_raising_decorator_expression_hides_class_body(self) -> None:
        source = '''
def explode():
    raise RuntimeError("decorator evaluation failed")

def validate(findings):
    @explode()
    class Broken:
        findings.append(Finding("PUBLIC_CODE", "hidden"))
'''
        self.assertNotIn(
            "PUBLIC_CODE",
            literal_base.finding_semantic_signatures(source, "sample.py"),
        )

    def test_raising_base_hides_parameterized_call(self) -> None:
        source = '''
def explode():
    raise RuntimeError("base evaluation failed")

def read_text(path, findings, code):
    Finding(code, "decode failed", path="sample")

def validate(path, findings):
    class Broken(explode()):
        read_text(path, findings, "PUBLIC_CODE")
'''
        self.assertEqual(
            parameterized_active.parameterized_finding_contracts(
                source, "sample.py"
            ),
            set(),
        )
        self.assertEqual(
            parameterized_reachability.reachable_parameterized_contracts(
                source, "sample.py"
            ),
            set(),
        )

    def test_later_base_expression_requires_prior_base_success(self) -> None:
        source = '''
def validate(findings):
    class Wrapped(unknown_base(), findings.append(Finding("PUBLIC_CODE", "base"))):
        pass
'''
        payload = json.loads(
            literal_base.finding_semantic_signatures(source, "sample.py")[
                "PUBLIC_CODE"
            ][0]
        )
        self.assertTrue(
            any(marker.startswith("class:prerequisite:1:requires-construction") for marker in payload["context"]),
            payload["context"],
        )


if __name__ == "__main__":
    unittest.main()
