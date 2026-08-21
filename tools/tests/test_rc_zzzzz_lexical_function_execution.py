from __future__ import annotations

import ast
import copy
import json
import unittest
from collections import Counter

import rc_finding_code_contracts_base as literal_base
import test_rc_extended_finding_reachability as extended_reachability
import test_rc_finding_reachability as basic_reachability
import test_rc_parameterized_finding_codes as parameterized_active
import test_rc_parameterized_finding_reachability as parameterized_reachability
import test_rc_zzz_finding_emission_sink as sink_execution
import test_rc_zzzz_sink_rebinding_and_parameterized_multiplicity as latest_sink_state


# The receiver-state layer strengthens the sink contract function in
# test_rc_zzz_finding_emission_sink. Make the sink-aware entry point the
# authoritative literal semantic scanner as well, so callers of the base module
# cannot accidentally bypass the composed sink contract.
literal_base.finding_semantic_signatures = (
    sink_execution.finding_semantic_signatures_with_sink
)


def _visit_definition_time_expressions(
    visitor: ast.NodeVisitor,
    node: ast.FunctionDef | ast.AsyncFunctionDef,
) -> None:
    """Visit expressions Python evaluates when a nested function is defined."""

    for decorator in node.decorator_list:
        visitor.visit(decorator)

    args = node.args
    for default in args.defaults:
        visitor.visit(default)
    for default in args.kw_defaults:
        if default is not None:
            visitor.visit(default)

    arguments = [*args.posonlyargs, *args.args, *args.kwonlyargs]
    if args.vararg is not None:
        arguments.append(args.vararg)
    if args.kwarg is not None:
        arguments.append(args.kwarg)
    for argument in arguments:
        if argument.annotation is not None:
            visitor.visit(argument.annotation)

    if node.returns is not None:
        visitor.visit(node.returns)
    for type_parameter in getattr(node, "type_params", []):
        visitor.visit(type_parameter)


def _lexical_state(visitor) -> tuple[
    list[int],
    dict[tuple[int, ...], dict[str, ast.FunctionDef | ast.AsyncFunctionDef]],
    set[int],
]:
    if not hasattr(visitor, "_lexical_scope_stack"):
        visitor._lexical_scope_stack = []
        visitor._lexical_nested_definitions = {}
        visitor._active_lexical_functions = set()
    return (
        visitor._lexical_scope_stack,
        visitor._lexical_nested_definitions,
        visitor._active_lexical_functions,
    )


def _register_nested_function(
    visitor,
    node: ast.FunctionDef | ast.AsyncFunctionDef,
) -> None:
    stack, definitions, _ = _lexical_state(visitor)
    definitions.setdefault(tuple(stack), {})[node.name] = node


def _lookup_nested_function(
    visitor,
    name: str,
) -> ast.FunctionDef | ast.AsyncFunctionDef | None:
    stack, definitions, _ = _lexical_state(visitor)
    for depth in range(len(stack), 0, -1):
        candidate = definitions.get(tuple(stack[:depth]), {}).get(name)
        if candidate is not None:
            return candidate
    return None


def _qualified_nested_function(
    node: ast.FunctionDef | ast.AsyncFunctionDef,
    parent_identity: str,
) -> ast.FunctionDef | ast.AsyncFunctionDef:
    cloned = copy.copy(node)
    cloned.name = f"{parent_identity}.<locals>.{node.name}"
    return cloned


def _visit_call_arguments(visitor: ast.NodeVisitor, node: ast.Call) -> None:
    visitor.visit(node.func)
    for argument in node.args:
        visitor.visit(argument)
    for keyword in node.keywords:
        visitor.visit(keyword.value)


def _invoke_nested_function(
    visitor,
    node: ast.Call,
    *,
    identity_attribute: str,
    invoke,
) -> bool:
    if not isinstance(node.func, ast.Name):
        return False

    nested = _lookup_nested_function(visitor, node.func.id)
    if nested is None:
        return False

    _visit_call_arguments(visitor, node)
    stack, _, active = _lexical_state(visitor)
    marker = id(nested)
    if marker in active:
        return True

    parent_identity = getattr(visitor, identity_attribute)
    qualified = _qualified_nested_function(nested, parent_identity)
    active.add(marker)
    stack.append(marker)
    try:
        invoke(visitor, qualified)
    finally:
        stack.pop()
        active.remove(marker)
    return True


# ---------------------------------------------------------------------------
# Literal finding semantics
# ---------------------------------------------------------------------------

_composed_literal_visit_function = literal_base.FindingSignatureVisitor.visit_FunctionDef
_composed_literal_visit_async_function = (
    literal_base.FindingSignatureVisitor.visit_AsyncFunctionDef
)
_composed_literal_visit_call = literal_base.FindingSignatureVisitor.visit_Call


def _literal_visit_function(self, node: ast.FunctionDef) -> None:
    stack, _, _ = _lexical_state(self)
    if stack:
        _visit_definition_time_expressions(self, node)
        _register_nested_function(self, node)
        return

    stack.append(id(node))
    try:
        _composed_literal_visit_function(self, node)
    finally:
        stack.pop()


def _literal_visit_async_function(self, node: ast.AsyncFunctionDef) -> None:
    stack, _, _ = _lexical_state(self)
    if stack:
        _visit_definition_time_expressions(self, node)
        _register_nested_function(self, node)
        return

    stack.append(id(node))
    try:
        _composed_literal_visit_async_function(self, node)
    finally:
        stack.pop()


def _literal_invoke(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> None:
    if isinstance(node, ast.AsyncFunctionDef):
        _composed_literal_visit_async_function(self, node)
    else:
        _composed_literal_visit_function(self, node)


def _literal_visit_call(self, node: ast.Call) -> None:
    if _invoke_nested_function(
        self,
        node,
        identity_attribute="function",
        invoke=_literal_invoke,
    ):
        return
    _composed_literal_visit_call(self, node)


literal_base.FindingSignatureVisitor.visit_FunctionDef = _literal_visit_function
literal_base.FindingSignatureVisitor.visit_AsyncFunctionDef = _literal_visit_async_function
literal_base.FindingSignatureVisitor.visit_Call = _literal_visit_call


# Sink-aware semantic scanning subclasses the literal visitor but owns its call
# hook, so compose nested invocation into that hook explicitly as well.
_composed_sink_visit_call = sink_execution.SinkAwareFindingSignatureVisitor.visit_Call


def _sink_visit_call(self, node: ast.Call) -> None:
    if _invoke_nested_function(
        self,
        node,
        identity_attribute="function",
        invoke=_literal_invoke,
    ):
        return
    _composed_sink_visit_call(self, node)


sink_execution.SinkAwareFindingSignatureVisitor.visit_Call = _sink_visit_call


# ---------------------------------------------------------------------------
# Literal finding reachability
# ---------------------------------------------------------------------------


def _patch_reachability_lexical_functions(visitor_type) -> None:
    composed_visit_function = visitor_type.visit_FunctionDef
    composed_visit_async_function = visitor_type.visit_AsyncFunctionDef
    composed_visit_call = visitor_type.visit_Call

    def visit_function(self, node: ast.FunctionDef) -> None:
        stack, _, _ = _lexical_state(self)
        if stack:
            _visit_definition_time_expressions(self, node)
            _register_nested_function(self, node)
            return
        stack.append(id(node))
        try:
            composed_visit_function(self, node)
        finally:
            stack.pop()

    def visit_async_function(self, node: ast.AsyncFunctionDef) -> None:
        stack, _, _ = _lexical_state(self)
        if stack:
            _visit_definition_time_expressions(self, node)
            _register_nested_function(self, node)
            return
        stack.append(id(node))
        try:
            composed_visit_async_function(self, node)
        finally:
            stack.pop()

    def invoke(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> None:
        self._visit_function(node)

    def visit_call(self, node: ast.Call) -> None:
        if _invoke_nested_function(
            self,
            node,
            identity_attribute="function",
            invoke=invoke,
        ):
            return
        composed_visit_call(self, node)

    visitor_type.visit_FunctionDef = visit_function
    visitor_type.visit_AsyncFunctionDef = visit_async_function
    visitor_type.visit_Call = visit_call


_patch_reachability_lexical_functions(basic_reachability.ReachableFindingVisitor)
_patch_reachability_lexical_functions(extended_reachability.ExtendedReachableFindingVisitor)


# The sink-aware reachability visitor owns its call hook separately.
_composed_sink_reachability_visit_call = (
    sink_execution.SinkAwareReachableFindingVisitor.visit_Call
)


def _sink_reachability_invoke(
    self,
    node: ast.FunctionDef | ast.AsyncFunctionDef,
) -> None:
    self._visit_function(node)


def _sink_reachability_visit_call(self, node: ast.Call) -> None:
    if _invoke_nested_function(
        self,
        node,
        identity_attribute="function",
        invoke=_sink_reachability_invoke,
    ):
        return
    _composed_sink_reachability_visit_call(self, node)


sink_execution.SinkAwareReachableFindingVisitor.visit_Call = (
    _sink_reachability_visit_call
)


# ---------------------------------------------------------------------------
# Caller-supplied / parameterized finding semantics and reachability
# ---------------------------------------------------------------------------

_parameterized_visitor = parameterized_active.BranchAwareParameterizedCallSiteVisitor
_composed_parameterized_visit_function = _parameterized_visitor.visit_FunctionDef
_composed_parameterized_visit_async_function = _parameterized_visitor.visit_AsyncFunctionDef
_composed_parameterized_visit_call = _parameterized_visitor.visit_Call


def _parameterized_visit_function(self, node: ast.FunctionDef) -> None:
    stack, _, _ = _lexical_state(self)
    if stack:
        _visit_definition_time_expressions(self, node)
        _register_nested_function(self, node)
        return
    stack.append(id(node))
    try:
        _composed_parameterized_visit_function(self, node)
    finally:
        stack.pop()


def _parameterized_visit_async_function(self, node: ast.AsyncFunctionDef) -> None:
    stack, _, _ = _lexical_state(self)
    if stack:
        _visit_definition_time_expressions(self, node)
        _register_nested_function(self, node)
        return
    stack.append(id(node))
    try:
        _composed_parameterized_visit_async_function(self, node)
    finally:
        stack.pop()


def _parameterized_invoke(
    self,
    node: ast.FunctionDef | ast.AsyncFunctionDef,
) -> None:
    self._visit_function(node)


def _parameterized_visit_call(self, node: ast.Call) -> None:
    if _invoke_nested_function(
        self,
        node,
        identity_attribute="caller",
        invoke=_parameterized_invoke,
    ):
        return
    _composed_parameterized_visit_call(self, node)


_parameterized_visitor.visit_FunctionDef = _parameterized_visit_function
_parameterized_visitor.visit_AsyncFunctionDef = _parameterized_visit_async_function
_parameterized_visitor.visit_Call = _parameterized_visit_call
parameterized_active.base.ParameterizedCallSiteVisitor = _parameterized_visitor

# The multiplicity layer deliberately delegates non-helper calls through this
# composed hook. Point it at the lexical-aware hook so invoked nested wrappers
# participate in reachable call counts as well.
latest_sink_state._COMPOSED_PARAMETERIZED_VISIT_CALL = _parameterized_visit_call


class ReleaseCandidateLexicalFunctionExecutionTests(unittest.TestCase):
    def test_base_semantic_entrypoint_is_sink_aware(self):
        source = '''
def validate(findings):
    findings.append(Finding("PUBLIC_CODE", "visible"))
'''
        payload = json.loads(
            literal_base.finding_semantic_signatures(source)["PUBLIC_CODE"][0]
        )
        self.assertIn("sink", payload)
        self.assertTrue(any(item.startswith("call-arg:") for item in payload["sink"]))

    def test_uncalled_same_name_nested_function_does_not_emit_semantically(self):
        direct = '''
def validate():
    Finding("PUBLIC_CODE", "visible")
'''
        nested = '''
def validate():
    def validate():
        Finding("PUBLIC_CODE", "hidden")
'''
        self.assertIn("PUBLIC_CODE", literal_base.finding_semantic_signatures(direct))
        self.assertNotIn("PUBLIC_CODE", literal_base.finding_semantic_signatures(nested))

    def test_invoked_nested_function_uses_lexical_semantic_identity(self):
        source = '''
def validate(findings):
    def emit():
        findings.append(Finding("PUBLIC_CODE", "visible"))
    emit()
'''
        payload = json.loads(
            literal_base.finding_semantic_signatures(source)["PUBLIC_CODE"][0]
        )
        self.assertEqual(payload["function"], "validate.<locals>.emit")
        self.assertIn("sink", payload)

    def test_uncalled_nested_function_is_not_reachable(self):
        source = '''
def validate():
    def emit():
        Finding("PUBLIC_CODE", "hidden")
'''
        self.assertEqual(
            extended_reachability.reachable_contracts(source, "sample.py"),
            Counter(),
        )

    def test_invoked_nested_function_has_lexical_reachability_identity(self):
        source = '''
def validate():
    def emit():
        Finding("PUBLIC_CODE", "visible")
    emit()
'''
        contracts = extended_reachability.reachable_contracts(source, "sample.py")
        self.assertEqual(
            contracts[("sample.py", "validate.<locals>.emit", "PUBLIC_CODE")],
            1,
        )

    def test_uncalled_nested_parameterized_call_is_not_reachable(self):
        source = '''
def read_text(path, findings, code):
    Finding(code, "decode failed", path="sample")
def validate(root, findings):
    def emit():
        read_text(root / "LICENSE", findings, "LICENSE_ENCODING")
'''
        self.assertEqual(
            parameterized_reachability.reachable_parameterized_contracts(
                source,
                "sample.py",
            ),
            set(),
        )

    def test_invoked_nested_parameterized_call_uses_lexical_caller(self):
        source = '''
def read_text(path, findings, code):
    Finding(code, "decode failed", path="sample")
def validate(root, findings):
    def emit():
        read_text(root / "LICENSE", findings, "LICENSE_ENCODING")
    emit()
'''
        contracts = parameterized_reachability.reachable_parameterized_contracts(
            source,
            "sample.py",
        )
        self.assertEqual(len(contracts), 1)
        payload = json.loads(next(iter(contracts)))
        self.assertEqual(payload["code"], "LICENSE_ENCODING")
        self.assertEqual(payload["caller"], "validate.<locals>.emit")


if __name__ == "__main__":
    unittest.main()
