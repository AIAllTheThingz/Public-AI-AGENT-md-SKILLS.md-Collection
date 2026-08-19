from __future__ import annotations

import ast
import builtins
import unittest

import rc_finding_code_contracts_base as literal_base
import test_rc_extended_finding_reachability as extended_reachability
import test_rc_finding_reachability as basic_reachability
import test_rc_parameterized_finding_codes as parameterized_active
import test_rc_parameterized_finding_reachability as parameterized_reachability
import test_rc_zzz_finding_emission_sink as sink_execution
import test_rc_zzzz_sink_rebinding_and_parameterized_multiplicity as parameterized_multiplicity
import test_rc_zzzzzzzzzzzzzzzzz_function_defaults_and_constructor_provenance as defaults_layer
import test_rc_zzzzzzzzzzzzzzzzzzzzzzzzzzz_left_to_right_expression_execution as left_to_right
import test_rc_zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz_final_execution_composition_and_comprehension_binding as _previous_final  # noqa: F401


# Final execution-contract composition for two Python boundaries that occur before
# a finding-producing expression can execute:
#
# 1. Every function default is evaluated when the function definition executes,
#    even when the corresponding parameter is never loaded by the body. Preserve
#    only defaults that can execute/fail; inert literal rewordings remain outside
#    the public finding contract.
# 2. A bare name load is execution-safe only when its binding can be established.
#    Missing and conditionally local names are prerequisites rather than being
#    treated as intrinsically safe expressions.


# ---------------------------------------------------------------------------
# Definition-time execution of unused defaults
# ---------------------------------------------------------------------------

_previous_relevant_default_entries = defaults_layer._relevant_default_entries


def _definition_default_is_inert(node: ast.AST) -> bool:
    # Creating a lambda object does not execute its body.
    if isinstance(node, ast.Lambda):
        return True

    value = left_to_right.prerequisite_execution._static_eval(node, {})
    if value is left_to_right.prerequisite_execution._STATIC_RAISES:
        return False
    if value is left_to_right.prerequisite_execution._STATIC_UNKNOWN:
        return False
    return True


def _all_default_entries(
    node: ast.FunctionDef | ast.AsyncFunctionDef,
) -> list[tuple[str, ast.AST]]:
    result: list[tuple[str, ast.AST]] = []
    positional = [*node.args.posonlyargs, *node.args.args]

    if node.args.defaults:
        result.extend(
            zip(
                (argument.arg for argument in positional[-len(node.args.defaults) :]),
                node.args.defaults,
            )
        )

    result.extend(
        (argument.arg, default)
        for argument, default in zip(node.args.kwonlyargs, node.args.kw_defaults)
        if default is not None
    )
    return result


def _relevant_default_entries(
    node: ast.FunctionDef | ast.AsyncFunctionDef,
) -> list[tuple[str, ast.AST]]:
    # Preserve the earlier body-relevant contract exactly, then add unused
    # defaults only when evaluating the default itself can execute or fail.
    result = list(_previous_relevant_default_entries(node))
    included = {id(default) for _, default in result}

    for name, default in _all_default_entries(node):
        if id(default) in included or _definition_default_is_inert(default):
            continue
        result.append((name, default))
        included.add(id(default))

    return result


# The earlier visitor resolves this helper by module-global name at call time.
defaults_layer._relevant_default_entries = _relevant_default_entries


# ---------------------------------------------------------------------------
# Binding-aware name prerequisites
# ---------------------------------------------------------------------------


class _FunctionLocalCollector(ast.NodeVisitor):
    def __init__(self) -> None:
        self.names: set[str] = set()
        self.globals: set[str] = set()
        self.nonlocals: set[str] = set()

    def visit_Name(self, node: ast.Name) -> None:
        if isinstance(node.ctx, (ast.Store, ast.Del)):
            self.names.add(node.id)

    def visit_Global(self, node: ast.Global) -> None:
        self.globals.update(node.names)

    def visit_Nonlocal(self, node: ast.Nonlocal) -> None:
        self.nonlocals.update(node.names)

    def visit_Import(self, node: ast.Import) -> None:
        for alias in node.names:
            self.names.add(alias.asname or alias.name.split(".", 1)[0])

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        for alias in node.names:
            if alias.name != "*":
                self.names.add(alias.asname or alias.name)

    def visit_ExceptHandler(self, node: ast.ExceptHandler) -> None:
        if isinstance(node.name, str):
            self.names.add(node.name)
        for statement in node.body:
            self.visit(statement)

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        # The nested definition name binds in this scope; its body has another
        # local namespace and must not leak assignments into the outer one.
        self.names.add(node.name)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self.names.add(node.name)

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        self.names.add(node.name)

    def visit_Lambda(self, node: ast.Lambda) -> None:
        return

    def visit_ListComp(self, node: ast.ListComp) -> None:
        return

    def visit_SetComp(self, node: ast.SetComp) -> None:
        return

    def visit_DictComp(self, node: ast.DictComp) -> None:
        return

    def visit_GeneratorExp(self, node: ast.GeneratorExp) -> None:
        return


def _function_local_names(
    node: ast.FunctionDef | ast.AsyncFunctionDef,
) -> set[str]:
    collector = _FunctionLocalCollector()
    for statement in node.body:
        collector.visit(statement)
    return collector.names - collector.globals - collector.nonlocals


def _argument_names(node: ast.FunctionDef | ast.AsyncFunctionDef) -> set[str]:
    names = {
        argument.arg
        for argument in (
            *node.args.posonlyargs,
            *node.args.args,
            *node.args.kwonlyargs,
        )
    }
    if node.args.vararg is not None:
        names.add(node.args.vararg.arg)
    if node.args.kwarg is not None:
        names.add(node.args.kwarg.arg)
    return names


def _install_function_binding_scope(visitor_type) -> None:
    current_function = visitor_type.visit_FunctionDef
    current_async_function = visitor_type.visit_AsyncFunctionDef

    def visit_function(self, node: ast.FunctionDef) -> None:
        previous_bound = getattr(self, "_definitely_bound_names", None)
        previous_locals = getattr(self, "_function_local_names", None)

        inherited = set(previous_bound or ())
        self._definitely_bound_names = inherited | _argument_names(node)
        self._function_local_names = _function_local_names(node)
        try:
            current_function(self, node)
        finally:
            if previous_bound is None:
                self.__dict__.pop("_definitely_bound_names", None)
            else:
                self._definitely_bound_names = previous_bound
            if previous_locals is None:
                self.__dict__.pop("_function_local_names", None)
            else:
                self._function_local_names = previous_locals

    def visit_async_function(self, node: ast.AsyncFunctionDef) -> None:
        previous_bound = getattr(self, "_definitely_bound_names", None)
        previous_locals = getattr(self, "_function_local_names", None)

        inherited = set(previous_bound or ())
        self._definitely_bound_names = inherited | _argument_names(node)
        self._function_local_names = _function_local_names(node)
        try:
            current_async_function(self, node)
        finally:
            if previous_bound is None:
                self.__dict__.pop("_definitely_bound_names", None)
            else:
                self._definitely_bound_names = previous_bound
            if previous_locals is None:
                self.__dict__.pop("_function_local_names", None)
            else:
                self._function_local_names = previous_locals

    visitor_type.visit_FunctionDef = visit_function
    visitor_type.visit_AsyncFunctionDef = visit_async_function


_visitor_types: list[type] = [
    literal_base.FindingSignatureVisitor,
    sink_execution.SinkAwareFindingSignatureVisitor,
    basic_reachability.ReachableFindingVisitor,
    extended_reachability.ExtendedReachableFindingVisitor,
    sink_execution.SinkAwareReachableFindingVisitor,
    parameterized_active.BranchAwareParameterizedCallSiteVisitor,
    parameterized_reachability.ReachableParameterizedCallSiteVisitor,
]

for _name in (
    "CountingParameterizedCallSiteVisitor",
    "ReachableCountingParameterizedCallSiteVisitor",
    "CountingReachableParameterizedCallSiteVisitor",
):
    _candidate = getattr(parameterized_multiplicity, _name, None)
    if isinstance(_candidate, type):
        _visitor_types.append(_candidate)

_seen_visitor_types: set[type] = set()
for _visitor_type in _visitor_types:
    if _visitor_type in _seen_visitor_types:
        continue
    _seen_visitor_types.add(_visitor_type)
    _install_function_binding_scope(_visitor_type)


def _name_is_definitely_bound(visitor, name: str) -> bool:
    bound = getattr(visitor, "_definitely_bound_names", set())
    if name in bound:
        return True

    # A name assigned anywhere in a function is local by Python's lexical rules.
    # Without path-sensitive proof of an earlier assignment, do not fall back to
    # a same-named module or builtin binding: the load may raise UnboundLocalError.
    function_locals = getattr(visitor, "_function_local_names", set())
    if name in function_locals:
        return False

    if name in builtins.__dict__:
        return True

    for attribute in ("module_definitions", "module_values", "constants"):
        bindings = getattr(visitor, attribute, None)
        if isinstance(bindings, dict) and name in bindings:
            return True

    return False


def _visitor_execution_state(
    visitor,
    node: ast.AST,
    constants: dict[str, object],
) -> str:
    if not isinstance(node, ast.Name):
        return left_to_right._execution_state(node, constants)

    value = left_to_right.prerequisite_execution._static_eval(node, constants)
    if value is left_to_right.prerequisite_execution._STATIC_RAISES:
        return left_to_right._RAISES
    if value is not left_to_right.prerequisite_execution._STATIC_UNKNOWN:
        return left_to_right._SAFE

    if _name_is_definitely_bound(visitor, node.id):
        return left_to_right._SAFE
    return left_to_right._UNKNOWN


def _literal_visit_sequence(
    visitor,
    nodes: list[ast.AST],
    marker_prefix: str,
) -> bool:
    prerequisites: list[ast.AST] = []
    constants = left_to_right._literal_constants(visitor)

    for index, node in enumerate(nodes):
        if prerequisites:
            visitor.context.append(
                f"{marker_prefix}:{index}:requires-prior-evaluation"
            )
            visitor.context_nodes.append(
                left_to_right._prerequisite_node(prerequisites)
            )
            try:
                visitor.visit(node)
            finally:
                visitor.context_nodes.pop()
                visitor.context.pop()
        else:
            visitor.visit(node)

        state = _visitor_execution_state(visitor, node, constants)
        if state == left_to_right._RAISES:
            return False
        if state == left_to_right._UNKNOWN:
            prerequisites.append(node)
    return True


def _parameterized_visit_sequence(
    visitor,
    nodes: list[ast.AST],
    marker_prefix: str,
) -> bool:
    prerequisites: list[ast.AST] = []
    constants = left_to_right._parameterized_constants(visitor)

    for index, node in enumerate(nodes):
        if prerequisites:
            visitor.context_nodes.append(
                (
                    f"{marker_prefix}:{index}:requires-prior-evaluation",
                    left_to_right._prerequisite_node(prerequisites),
                )
            )
            try:
                visitor.visit(node)
            finally:
                visitor.context_nodes.pop()
        else:
            visitor.visit(node)

        state = _visitor_execution_state(visitor, node, constants)
        if state == left_to_right._RAISES:
            return False
        if state == left_to_right._UNKNOWN:
            prerequisites.append(node)
    return True


def _reachability_visit_sequence(visitor, nodes: list[ast.AST]) -> bool:
    constants = getattr(visitor, "constants", {})
    for node in nodes:
        visitor.visit(node)
        if (
            _visitor_execution_state(visitor, node, constants)
            == left_to_right._RAISES
        ):
            return False
    return True


# All left-to-right visitor methods resolve these helpers through the original
# module globals, so replacing them composes with the already-installed tuple,
# call, sink, parameterized, and reachability handlers.
left_to_right._literal_visit_sequence = _literal_visit_sequence
left_to_right._parameterized_visit_sequence = _parameterized_visit_sequence
left_to_right._reachability_visit_sequence = _reachability_visit_sequence


# ---------------------------------------------------------------------------
# Permanent regressions
# ---------------------------------------------------------------------------


class ReleaseCandidateDefinitionDefaultsAndBoundNamesTests(unittest.TestCase):
    def test_unused_executable_default_changes_finding_semantics(self) -> None:
        inert = """
from standards_tools import Finding

def run(unused="harmless"):
    Finding("PUBLIC_CODE", "message")
"""
        executable = inert.replace('unused="harmless"', "unused=explode()")

        expected = literal_base.finding_semantic_signatures(inert)
        actual = literal_base.finding_semantic_signatures(executable)
        self.assertNotEqual(expected, actual)
        self.assertTrue(
            any(
                "function-default" in signature
                for signature in actual["PUBLIC_CODE"]
            )
        )

    def test_unused_literal_default_rewording_remains_compatible(self) -> None:
        first = """
from standards_tools import Finding

def run(unused="first"):
    Finding("PUBLIC_CODE", "message")
"""
        second = first.replace('unused="first"', 'unused="second"')
        self.assertEqual(
            literal_base.finding_semantic_signatures(first),
            literal_base.finding_semantic_signatures(second),
        )

    def test_unused_kw_only_executable_default_is_tracked(self) -> None:
        inert = """
from standards_tools import Finding

def run(*, unused=None):
    Finding("PUBLIC_CODE", "message")
"""
        executable = inert.replace("unused=None", "unused=explode()")
        self.assertNotEqual(
            literal_base.finding_semantic_signatures(inert),
            literal_base.finding_semantic_signatures(executable),
        )

    def test_unbound_name_load_becomes_execution_prerequisite(self) -> None:
        direct = """
from standards_tools import Finding

def run(findings):
    findings.append(Finding("PUBLIC_CODE", "message"))
"""
        unbound = """
from standards_tools import Finding

def run(findings):
    (undefined_name, findings.append(Finding("PUBLIC_CODE", "message")))
"""

        expected = literal_base.finding_semantic_signatures(direct)
        actual = literal_base.finding_semantic_signatures(unbound)
        self.assertNotEqual(expected, actual)
        self.assertTrue(
            any(
                "requires-prior-evaluation" in signature
                for signature in actual["PUBLIC_CODE"]
            )
        )

        expected_sink = sink_execution.finding_semantic_signatures_with_sink(direct)
        actual_sink = sink_execution.finding_semantic_signatures_with_sink(unbound)
        self.assertNotEqual(expected_sink, actual_sink)

    def test_bound_parameter_name_load_remains_safe(self) -> None:
        direct = """
from standards_tools import Finding

def run(findings, value):
    findings.append(Finding("PUBLIC_CODE", "message"))
"""
        preceded = """
from standards_tools import Finding

def run(findings, value):
    (value, findings.append(Finding("PUBLIC_CODE", "message")))
"""
        self.assertEqual(
            literal_base.finding_semantic_signatures(direct),
            literal_base.finding_semantic_signatures(preceded),
        )

    def test_conditionally_bound_local_name_is_not_treated_as_safe(self) -> None:
        direct = """
from standards_tools import Finding

def run(findings, enabled):
    findings.append(Finding("PUBLIC_CODE", "message"))
"""
        conditional = """
from standards_tools import Finding

def run(findings, enabled):
    if enabled:
        maybe = 1
    (maybe, findings.append(Finding("PUBLIC_CODE", "message")))
"""
        self.assertNotEqual(
            literal_base.finding_semantic_signatures(direct),
            literal_base.finding_semantic_signatures(conditional),
        )


if __name__ == "__main__":
    unittest.main()
