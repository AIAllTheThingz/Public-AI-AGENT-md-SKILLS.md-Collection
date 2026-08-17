from __future__ import annotations

import ast
import copy
import json
import unittest

import rc_finding_code_contracts_base as literal_base
import test_rc_alias_and_generator_execution as generator_expression_execution
import test_rc_extended_finding_reachability as extended_reachability
import test_rc_finding_reachability as basic_reachability
import test_rc_parameterized_finding_codes as parameterized_active
import test_rc_parameterized_finding_reachability as parameterized_reachability


GENERATOR_FUNCTION_SUFFIX = "<generator>"


def _function_is_generator(node: ast.FunctionDef | ast.AsyncFunctionDef) -> bool:
    """Return true when this function's own scope contains yield/yield from.

    Generator classification is syntactic in Python, so a yield under `if False`
    still makes the function body deferred until iteration. Nested function,
    lambda, and class scopes do not change the enclosing function's status.
    """

    class Finder(ast.NodeVisitor):
        def __init__(self) -> None:
            self.found = False

        def visit_Yield(self, item: ast.Yield) -> None:
            self.found = True

        def visit_YieldFrom(self, item: ast.YieldFrom) -> None:
            self.found = True

        def visit_FunctionDef(self, item: ast.FunctionDef) -> None:
            return

        def visit_AsyncFunctionDef(self, item: ast.AsyncFunctionDef) -> None:
            return

        def visit_Lambda(self, item: ast.Lambda) -> None:
            return

        def visit_ClassDef(self, item: ast.ClassDef) -> None:
            return

    finder = Finder()
    for statement in node.body:
        finder.visit(statement)
        if finder.found:
            return True
    return False


def _with_generator_function_name(
    node: ast.FunctionDef | ast.AsyncFunctionDef,
) -> ast.FunctionDef | ast.AsyncFunctionDef:
    if not _function_is_generator(node):
        return node
    cloned = copy.copy(node)
    cloned.name = f"{node.name}{GENERATOR_FUNCTION_SUFFIX}"
    return cloned


# Literal finding semantic signatures. Preserve all existing lambda and
# generator-expression handling, but give generator functions a distinct
# execution identity so adding even an unreachable yield cannot masquerade as
# unchanged eager behavior.
_original_literal_visit_function = literal_base.FindingSignatureVisitor.visit_FunctionDef
_original_literal_visit_async_function = (
    literal_base.FindingSignatureVisitor.visit_AsyncFunctionDef
)


def _literal_visit_function(self, node: ast.FunctionDef) -> None:
    _original_literal_visit_function(self, _with_generator_function_name(node))


def _literal_visit_async_function(self, node: ast.AsyncFunctionDef) -> None:
    _original_literal_visit_async_function(self, _with_generator_function_name(node))


literal_base.FindingSignatureVisitor.visit_FunctionDef = _literal_visit_function
literal_base.FindingSignatureVisitor.visit_AsyncFunctionDef = _literal_visit_async_function


# Literal reachability inventories use `(source, function, code)` identities.
# Reuse their full existing control-flow implementation and change only the
# function identity when execution is deferred by generator semantics.
def _patch_reachability_generator_functions(visitor_type) -> None:
    original_visit_function = visitor_type._visit_function

    def patched_visit_function(self, node):
        return original_visit_function(self, _with_generator_function_name(node))

    visitor_type._visit_function = patched_visit_function


_patch_reachability_generator_functions(basic_reachability.ReachableFindingVisitor)
_patch_reachability_generator_functions(extended_reachability.ExtendedReachableFindingVisitor)


# Caller-supplied finding call sites already encode the caller name. Give a
# generator caller a distinct execution identity, and additionally bind whether
# the parameterized emitting helper itself became a generator. The latter
# catches a helper such as read_text() silently changing from eager emission to
# returning an unconsumed generator object.
_original_parameterized_visit_function = (
    parameterized_active.BranchAwareParameterizedCallSiteVisitor._visit_function
)
_original_parameterized_visit_call = (
    parameterized_active.BranchAwareParameterizedCallSiteVisitor.visit_Call
)


def _parameterized_visit_function(self, node) -> None:
    _original_parameterized_visit_function(self, _with_generator_function_name(node))


def _parameterized_visit_call(self, node: ast.Call) -> None:
    before = set(self.contracts)
    _original_parameterized_visit_call(self, node)

    if not (
        isinstance(node.func, ast.Name)
        and node.func.id in self.parameterized_helpers
        and node.func.id in self.definitions
        and _function_is_generator(self.definitions[node.func.id])
    ):
        return

    added = self.contracts - before
    if not added:
        return

    self.contracts.difference_update(added)
    for raw in added:
        payload = json.loads(raw)
        if payload.get("helper") == node.func.id:
            payload["helperExecution"] = "generator:iteration-required"
        self.contracts.add(json.dumps(payload, sort_keys=True))


parameterized_active.BranchAwareParameterizedCallSiteVisitor._visit_function = (
    _parameterized_visit_function
)
parameterized_active.BranchAwareParameterizedCallSiteVisitor.visit_Call = (
    _parameterized_visit_call
)
parameterized_active.base.ParameterizedCallSiteVisitor = (
    parameterized_active.BranchAwareParameterizedCallSiteVisitor
)


class ReleaseCandidateGeneratorFunctionExecutionTests(unittest.TestCase):
    def test_unreachable_yield_changes_literal_finding_semantics(self):
        eager = '''
def validate():
    Finding("PUBLIC_CODE", "visible", path="sample")
'''
        deferred = '''
def validate():
    if False:
        yield None
    Finding("PUBLIC_CODE", "deferred", path="sample")
'''
        eager_signatures = literal_base.finding_semantic_signatures(eager)
        deferred_signatures = literal_base.finding_semantic_signatures(deferred)
        self.assertIn("PUBLIC_CODE", eager_signatures)
        self.assertIn("PUBLIC_CODE", deferred_signatures)
        self.assertNotEqual(eager_signatures, deferred_signatures)
        payload = json.loads(deferred_signatures["PUBLIC_CODE"][0])
        self.assertEqual(
            payload["function"], f"validate{GENERATOR_FUNCTION_SUFFIX}"
        )

    def test_unreachable_yield_changes_literal_reachability_identity(self):
        eager = '''
def validate():
    Finding("PUBLIC_CODE", "visible")
'''
        deferred = '''
def validate():
    if False:
        yield None
    Finding("PUBLIC_CODE", "deferred")
'''
        eager_contracts = extended_reachability.reachable_contracts(
            eager, "sample.py"
        )
        deferred_contracts = extended_reachability.reachable_contracts(
            deferred, "sample.py"
        )
        self.assertEqual(eager_contracts[("sample.py", "validate", "PUBLIC_CODE")], 1)
        self.assertEqual(
            deferred_contracts[
                (
                    "sample.py",
                    f"validate{GENERATOR_FUNCTION_SUFFIX}",
                    "PUBLIC_CODE",
                )
            ],
            1,
        )
        self.assertNotEqual(eager_contracts, deferred_contracts)

    def test_generator_caller_changes_parameterized_call_site_contract(self):
        eager = '''
def read_text(path, findings, code):
    Finding(code, "decode failed", path="sample")
def validate(root, findings):
    read_text(root / "LICENSE", findings, "LICENSE_ENCODING")
'''
        deferred = eager.replace(
            "def validate(root, findings):\n",
            "def validate(root, findings):\n    if False:\n        yield None\n",
        )
        eager_contract = next(
            iter(
                parameterized_reachability.reachable_parameterized_contracts(
                    eager, "sample.py"
                )
            )
        )
        deferred_contract = next(
            iter(
                parameterized_reachability.reachable_parameterized_contracts(
                    deferred, "sample.py"
                )
            )
        )
        self.assertEqual(json.loads(eager_contract)["caller"], "validate")
        self.assertEqual(
            json.loads(deferred_contract)["caller"],
            f"validate{GENERATOR_FUNCTION_SUFFIX}",
        )
        self.assertNotEqual(eager_contract, deferred_contract)

    def test_generator_emitter_changes_parameterized_helper_contract(self):
        eager = '''
def read_text(path, findings, code):
    Finding(code, "decode failed", path="sample")
def validate(root, findings):
    read_text(root / "LICENSE", findings, "LICENSE_ENCODING")
'''
        deferred = eager.replace(
            "def read_text(path, findings, code):\n",
            "def read_text(path, findings, code):\n    if False:\n        yield None\n",
        )
        eager_contract = next(
            iter(
                parameterized_reachability.reachable_parameterized_contracts(
                    eager, "sample.py"
                )
            )
        )
        deferred_contract = next(
            iter(
                parameterized_reachability.reachable_parameterized_contracts(
                    deferred, "sample.py"
                )
            )
        )
        self.assertNotIn("helperExecution", json.loads(eager_contract))
        self.assertEqual(
            json.loads(deferred_contract)["helperExecution"],
            "generator:iteration-required",
        )
        self.assertNotEqual(eager_contract, deferred_contract)

    def test_nested_generator_does_not_defer_outer_function(self):
        tree = ast.parse(
            '''
def validate():
    def nested():
        yield None
    Finding("PUBLIC_CODE", "visible")
'''
        )
        function = tree.body[0]
        self.assertIsInstance(function, ast.FunctionDef)
        self.assertFalse(_function_is_generator(function))


if __name__ == "__main__":
    unittest.main()
