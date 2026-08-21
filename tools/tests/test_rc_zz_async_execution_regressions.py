from __future__ import annotations

import ast
import copy
import json
import unittest

import rc_finding_code_contracts_base as literal_base
import test_rc_extended_finding_reachability as extended_reachability
import test_rc_finding_reachability as basic_reachability
import test_rc_generator_function_execution as generator_execution
import test_rc_parameterized_finding_codes as parameterized_active
import test_rc_parameterized_finding_reachability as parameterized_reachability
import test_rc_z_decorator_and_numbered_evidence_regressions as decorator_execution


COROUTINE_SUFFIX = "<coroutine>"
ASYNC_GENERATOR_SUFFIX = "<async-generator>"


def _with_async_execution_name(
    node: ast.FunctionDef | ast.AsyncFunctionDef,
) -> ast.FunctionDef | ast.AsyncFunctionDef:
    if not isinstance(node, ast.AsyncFunctionDef):
        return node
    cloned = copy.copy(node)
    suffix = (
        ASYNC_GENERATOR_SUFFIX
        if generator_execution._function_is_generator(node)
        else COROUTINE_SUFFIX
    )
    cloned.name = f"{node.name}{suffix}"
    return cloned


# Python's async execution boundary is part of whether a finding-producing body
# runs at a call site. A plain `def` executes immediately; an `async def` returns
# a coroutine object and requires awaiting. Async generators require iteration.
# Preserve the decorator and generator-function overlays installed by the
# imported modules above, and add this execution identity on top.
_original_literal_visit_async_function = (
    literal_base.FindingSignatureVisitor.visit_AsyncFunctionDef
)


def _literal_visit_async_function(self, node: ast.AsyncFunctionDef) -> None:
    _original_literal_visit_async_function(self, _with_async_execution_name(node))


literal_base.FindingSignatureVisitor.visit_AsyncFunctionDef = (
    _literal_visit_async_function
)


def _patch_reachability_async_functions(visitor_type) -> None:
    original_visit_function = visitor_type._visit_function

    def patched_visit_function(self, node):
        return original_visit_function(self, _with_async_execution_name(node))

    visitor_type._visit_function = patched_visit_function


_patch_reachability_async_functions(basic_reachability.ReachableFindingVisitor)
_patch_reachability_async_functions(extended_reachability.ExtendedReachableFindingVisitor)


# Caller-supplied finding contracts already encode caller identity. Make an
# async caller distinct from a synchronous caller, and bind the execution
# boundary of an async emitting helper so a synchronous call cannot silently
# become an unawaited coroutine or uniterated async generator.
_original_parameterized_visit_function = (
    parameterized_active.BranchAwareParameterizedCallSiteVisitor._visit_function
)
_original_parameterized_visit_call = (
    parameterized_active.BranchAwareParameterizedCallSiteVisitor.visit_Call
)


def _parameterized_visit_async_function(self, node) -> None:
    _original_parameterized_visit_function(self, _with_async_execution_name(node))


def _parameterized_visit_async_call(self, node: ast.Call) -> None:
    before = set(self.contracts)
    _original_parameterized_visit_call(self, node)

    if not (
        isinstance(node.func, ast.Name)
        and node.func.id in self.parameterized_helpers
        and node.func.id in self.definitions
    ):
        return

    definition = self.definitions[node.func.id]
    if not isinstance(definition, ast.AsyncFunctionDef):
        return

    added = self.contracts - before
    if not added:
        return

    execution = (
        "async-generator:iteration-required"
        if generator_execution._function_is_generator(definition)
        else "coroutine:await-required"
    )
    self.contracts.difference_update(added)
    for raw in added:
        payload = json.loads(raw)
        if payload.get("helper") == node.func.id:
            payload["helperExecution"] = execution
        self.contracts.add(json.dumps(payload, sort_keys=True))


parameterized_active.BranchAwareParameterizedCallSiteVisitor._visit_function = (
    _parameterized_visit_async_function
)
parameterized_active.BranchAwareParameterizedCallSiteVisitor.visit_Call = (
    _parameterized_visit_async_call
)
parameterized_active.base.ParameterizedCallSiteVisitor = (
    parameterized_active.BranchAwareParameterizedCallSiteVisitor
)


class ReleaseCandidateAsyncExecutionRegressionTests(unittest.TestCase):
    def test_sync_to_async_changes_literal_finding_semantics(self):
        synchronous = """
def validate():
    Finding("PUBLIC_CODE", "visible", path="sample")
"""
        asynchronous = """
async def validate():
    Finding("PUBLIC_CODE", "deferred", path="sample")
"""
        sync_signatures = literal_base.finding_semantic_signatures(synchronous)
        async_signatures = literal_base.finding_semantic_signatures(asynchronous)

        self.assertIn("PUBLIC_CODE", sync_signatures)
        self.assertIn("PUBLIC_CODE", async_signatures)
        self.assertNotEqual(sync_signatures, async_signatures)
        payload = json.loads(async_signatures["PUBLIC_CODE"][0])
        self.assertIn(COROUTINE_SUFFIX, payload["function"])

    def test_sync_to_async_changes_literal_reachability_identity(self):
        synchronous = """
def validate():
    Finding("PUBLIC_CODE", "visible")
"""
        asynchronous = """
async def validate():
    Finding("PUBLIC_CODE", "deferred")
"""
        sync_contracts = extended_reachability.reachable_contracts(
            synchronous, "sample.py"
        )
        async_contracts = extended_reachability.reachable_contracts(
            asynchronous, "sample.py"
        )

        self.assertEqual(
            sync_contracts[("sample.py", "validate", "PUBLIC_CODE")],
            1,
        )
        self.assertEqual(
            async_contracts[
                ("sample.py", f"validate{COROUTINE_SUFFIX}", "PUBLIC_CODE")
            ],
            1,
        )
        self.assertNotEqual(sync_contracts, async_contracts)

    def test_async_parameterized_emitter_requires_await(self):
        synchronous = """
def read_text(path, findings, code):
    Finding(code, "decode failed", path="sample")
def validate(root, findings):
    read_text(root / "LICENSE", findings, "LICENSE_ENCODING")
"""
        asynchronous = synchronous.replace(
            "def read_text(path, findings, code):",
            "async def read_text(path, findings, code):",
        )

        sync_contract = next(
            iter(
                parameterized_reachability.reachable_parameterized_contracts(
                    synchronous, "sample.py"
                )
            )
        )
        async_contract = next(
            iter(
                parameterized_reachability.reachable_parameterized_contracts(
                    asynchronous, "sample.py"
                )
            )
        )
        self.assertNotIn("helperExecution", json.loads(sync_contract))
        self.assertEqual(
            json.loads(async_contract)["helperExecution"],
            "coroutine:await-required",
        )
        self.assertNotEqual(sync_contract, async_contract)

    def test_async_parameterized_caller_has_distinct_execution_identity(self):
        synchronous = """
def read_text(path, findings, code):
    Finding(code, "decode failed", path="sample")
def validate(root, findings):
    read_text(root / "LICENSE", findings, "LICENSE_ENCODING")
"""
        asynchronous = synchronous.replace(
            "def validate(root, findings):",
            "async def validate(root, findings):",
        )

        sync_contract = next(
            iter(
                parameterized_reachability.reachable_parameterized_contracts(
                    synchronous, "sample.py"
                )
            )
        )
        async_contract = next(
            iter(
                parameterized_reachability.reachable_parameterized_contracts(
                    asynchronous, "sample.py"
                )
            )
        )
        self.assertEqual(json.loads(sync_contract)["caller"], "validate")
        self.assertIn(
            COROUTINE_SUFFIX,
            json.loads(async_contract)["caller"],
        )
        self.assertNotEqual(sync_contract, async_contract)

    def test_async_generator_has_distinct_execution_identity(self):
        tree = ast.parse(
            """
async def validate():
    yield None
    Finding("PUBLIC_CODE", "deferred")
"""
        )
        function = tree.body[0]
        self.assertIsInstance(function, ast.AsyncFunctionDef)
        renamed = _with_async_execution_name(function)
        self.assertIn(ASYNC_GENERATOR_SUFFIX, renamed.name)


if __name__ == "__main__":
    unittest.main()
