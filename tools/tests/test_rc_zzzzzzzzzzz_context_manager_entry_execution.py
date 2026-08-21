from __future__ import annotations

import ast
import copy
import hashlib
import json
import unittest
from collections import Counter

import rc_finding_code_contracts_base as literal_base
import rc_parameterized_finding_codes_base as parameterized_base
import test_rc_extended_finding_reachability as extended_reachability
import test_rc_finding_reachability as basic_reachability
import test_rc_parameterized_finding_codes as parameterized_active
import test_rc_parameterized_finding_reachability as parameterized_reachability
import test_rc_zzzzzzzzzz_chained_comparison_execution as comparison_execution  # noqa: F401


# A with/async-with body executes only after every context expression and entry
# protocol succeeds. Generic AST traversal makes the body look unconditional and
# loses the semantic dependency on the manager that can prevent body execution.

_ENTRY_FAILS = False
_ENTRY_SUCCEEDS = True
_ENTRY_UNKNOWN = None


def _module_runtime_definitions(node: ast.Module):
    return {
        statement.name: statement
        for statement in node.body
        if isinstance(statement, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
    }


def _first_effective_statement(statements: list[ast.stmt]) -> ast.stmt | None:
    for statement in statements:
        if (
            isinstance(statement, ast.Expr)
            and isinstance(statement.value, ast.Constant)
            and isinstance(statement.value.value, str)
        ):
            continue
        if isinstance(statement, ast.Pass):
            continue
        return statement
    return None


def _safe_return_expression(node: ast.AST | None) -> bool:
    if node is None or isinstance(node, (ast.Constant, ast.Name)):
        return True
    if isinstance(node, (ast.Tuple, ast.List, ast.Set)):
        return all(
            not isinstance(item, ast.Starred) and _safe_return_expression(item)
            for item in node.elts
        )
    if isinstance(node, ast.Dict):
        return all(
            key is not None
            and _safe_return_expression(key)
            and _safe_return_expression(value)
            for key, value in zip(node.keys, node.values)
        )
    return False


def _callable_direct_outcome(node: ast.FunctionDef | ast.AsyncFunctionDef):
    if node.decorator_list:
        return _ENTRY_UNKNOWN
    statement = _first_effective_statement(node.body)
    if statement is None:
        return _ENTRY_SUCCEEDS
    if isinstance(statement, ast.Raise):
        return _ENTRY_FAILS
    if (
        isinstance(statement, ast.Assert)
        and isinstance(statement.test, ast.Constant)
        and not bool(statement.test.value)
    ):
        return _ENTRY_FAILS
    if isinstance(statement, ast.Return) and _safe_return_expression(statement.value):
        return _ENTRY_SUCCEEDS
    return _ENTRY_UNKNOWN


def _class_entry_method(node: ast.ClassDef, *, async_mode: bool):
    method_name = "__aenter__" if async_mode else "__enter__"
    return next(
        (
            statement
            for statement in node.body
            if isinstance(statement, (ast.FunctionDef, ast.AsyncFunctionDef))
            and statement.name == method_name
        ),
        None,
    )


def _returned_expression(node: ast.FunctionDef | ast.AsyncFunctionDef):
    if node.decorator_list:
        return None
    statement = _first_effective_statement(node.body)
    return statement.value if isinstance(statement, ast.Return) else None


def _context_entry_outcome(expression: ast.AST, definitions: dict[str, ast.AST], *, async_mode: bool, seen=None):
    # Literal objects do not implement the context manager protocol.
    if isinstance(expression, ast.Constant):
        return _ENTRY_FAILS
    if not isinstance(expression, ast.Call) or not isinstance(expression.func, ast.Name):
        return _ENTRY_UNKNOWN

    active = set() if seen is None else set(seen)
    name = expression.func.id
    if name in active:
        return _ENTRY_UNKNOWN
    active.add(name)
    definition = definitions.get(name)

    if isinstance(definition, ast.ClassDef):
        method = _class_entry_method(definition, async_mode=async_mode)
        if method is None:
            return _ENTRY_FAILS if not definition.bases else _ENTRY_UNKNOWN
        return _callable_direct_outcome(method)

    if isinstance(definition, (ast.FunctionDef, ast.AsyncFunctionDef)):
        if _callable_direct_outcome(definition) is _ENTRY_FAILS:
            return _ENTRY_FAILS
        returned = _returned_expression(definition)
        if returned is not None:
            nested = _context_entry_outcome(
                returned,
                definitions,
                async_mode=async_mode,
                seen=active,
            )
            if nested is not _ENTRY_UNKNOWN:
                return nested
    return _ENTRY_UNKNOWN


def _entry_contract_text(expression: ast.AST, definitions: dict[str, ast.AST], *, async_mode: bool) -> str:
    parts = [literal_base.normalized_semantic_ast(expression)]
    if isinstance(expression, ast.Call) and isinstance(expression.func, ast.Name):
        definition = definitions.get(expression.func.id)
        if isinstance(definition, ast.ClassDef):
            method = _class_entry_method(definition, async_mode=async_mode)
            if method is not None:
                parts.append(literal_base.normalized_semantic_ast(method))
            elif definition.bases:
                parts.append(
                    "bases:"
                    + ",".join(
                        literal_base.normalized_semantic_ast(base)
                        for base in definition.bases
                    )
                )
        elif isinstance(definition, (ast.FunctionDef, ast.AsyncFunctionDef)):
            parts.append(literal_base.normalized_semantic_ast(definition))
    return "\n".join(parts)


def _entry_digest(items: list[ast.withitem], definitions: dict[str, ast.AST], *, async_mode: bool) -> str:
    payload = "\n--item--\n".join(
        _entry_contract_text(item.context_expr, definitions, async_mode=async_mode)
        + (
            "\nas-target:" + literal_base.normalized_semantic_ast(item.optional_vars)
            if item.optional_vars is not None
            else ""
        )
        for item in items
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]


def _acquisition_dependency(items: list[ast.withitem]) -> ast.AST:
    values: list[ast.AST] = []
    for item in items:
        values.append(copy.deepcopy(item.context_expr))
        if item.optional_vars is not None:
            values.append(
                ast.Constant(
                    value="as:" + literal_base.normalized_semantic_ast(item.optional_vars)
                )
            )
    return values[0] if len(values) == 1 else ast.Tuple(elts=values, ctx=ast.Load())


def _marker(prefix: str, phase: str, digest: str) -> str:
    return f"{prefix}:{phase}:entry-contract:{digest}"


def _literal_expression_context(visitor, marker: str, dependency: ast.AST, expression: ast.AST) -> None:
    visitor.context.append(marker)
    visitor.context_nodes.append(dependency)
    try:
        visitor.visit(expression)
    finally:
        visitor.context_nodes.pop()
        visitor.context.pop()


def _parameterized_expression_context(visitor, marker: str, dependency: ast.AST, expression: ast.AST) -> None:
    visitor.context_nodes.append((marker, dependency))
    try:
        visitor.visit(expression)
    finally:
        visitor.context_nodes.pop()


def _literal_visit_module(self, node: ast.Module) -> None:
    previous = getattr(self, "_context_manager_definitions", None)
    self._context_manager_definitions = _module_runtime_definitions(node)
    try:
        for statement in node.body:
            self.visit(statement)
    finally:
        if previous is None:
            del self._context_manager_definitions
        else:
            self._context_manager_definitions = previous


def _visit_with_literal(self, node: ast.With | ast.AsyncWith, *, async_mode: bool) -> None:
    definitions = getattr(self, "_context_manager_definitions", {})
    prefix = "async-with" if async_mode else "with"
    acquired: list[ast.withitem] = []
    for index, item in enumerate(node.items):
        if acquired:
            digest = _entry_digest(acquired, definitions, async_mode=async_mode)
            _literal_expression_context(
                self,
                _marker(prefix, f"item:{index}:requires-prior", digest),
                _acquisition_dependency(acquired),
                item.context_expr,
            )
        else:
            self.visit(item.context_expr)
        acquired.append(item)
        if _context_entry_outcome(
            item.context_expr, definitions, async_mode=async_mode
        ) is _ENTRY_FAILS:
            return

    digest = _entry_digest(acquired, definitions, async_mode=async_mode)
    self._with_context(
        _marker(prefix, "body:requires-entry", digest),
        _acquisition_dependency(acquired),
        node.body,
    )


literal_base.FindingSignatureVisitor.visit_Module = _literal_visit_module
literal_base.FindingSignatureVisitor.visit_With = lambda self, node: _visit_with_literal(
    self, node, async_mode=False
)
literal_base.FindingSignatureVisitor.visit_AsyncWith = lambda self, node: _visit_with_literal(
    self, node, async_mode=True
)


def _patch_reachability_with(visitor_type) -> None:
    composed_visit_module = visitor_type.visit_Module

    def visit_module(self, node: ast.Module) -> None:
        previous = getattr(self, "_context_manager_definitions", None)
        self._context_manager_definitions = _module_runtime_definitions(node)
        try:
            composed_visit_module(self, node)
        finally:
            if previous is None:
                del self._context_manager_definitions
            else:
                self._context_manager_definitions = previous

    def visit_common(self, node: ast.With | ast.AsyncWith, *, async_mode: bool) -> None:
        definitions = getattr(self, "_context_manager_definitions", {})
        for item in node.items:
            self.visit(item.context_expr)
            if _context_entry_outcome(
                item.context_expr, definitions, async_mode=async_mode
            ) is _ENTRY_FAILS:
                return
        self._visit_block(node.body)

    visitor_type.visit_Module = visit_module
    visitor_type.visit_With = lambda self, node: visit_common(
        self, node, async_mode=False
    )
    visitor_type.visit_AsyncWith = lambda self, node: visit_common(
        self, node, async_mode=True
    )


_patch_reachability_with(basic_reachability.ReachableFindingVisitor)
_patch_reachability_with(extended_reachability.ExtendedReachableFindingVisitor)


_parameterized_visitor = parameterized_active.BranchAwareParameterizedCallSiteVisitor


def _parameterized_visit_module(self, node: ast.Module) -> None:
    previous = getattr(self, "_context_manager_definitions", None)
    self._context_manager_definitions = _module_runtime_definitions(node)
    try:
        for statement in node.body:
            self.visit(statement)
    finally:
        if previous is None:
            del self._context_manager_definitions
        else:
            self._context_manager_definitions = previous


def _visit_with_parameterized(self, node: ast.With | ast.AsyncWith, *, async_mode: bool) -> None:
    definitions = getattr(self, "_context_manager_definitions", {})
    prefix = "async-with" if async_mode else "with"
    acquired: list[ast.withitem] = []
    for index, item in enumerate(node.items):
        if acquired:
            digest = _entry_digest(acquired, definitions, async_mode=async_mode)
            _parameterized_expression_context(
                self,
                _marker(prefix, f"item:{index}:requires-prior", digest),
                _acquisition_dependency(acquired),
                item.context_expr,
            )
        else:
            self.visit(item.context_expr)
        acquired.append(item)
        if _context_entry_outcome(
            item.context_expr, definitions, async_mode=async_mode
        ) is _ENTRY_FAILS:
            return

    digest = _entry_digest(acquired, definitions, async_mode=async_mode)
    self._with_context(
        _marker(prefix, "body:requires-entry", digest),
        _acquisition_dependency(acquired),
        node.body,
    )


_parameterized_visitor.visit_Module = _parameterized_visit_module
_parameterized_visitor.visit_With = lambda self, node: _visit_with_parameterized(
    self, node, async_mode=False
)
_parameterized_visitor.visit_AsyncWith = lambda self, node: _visit_with_parameterized(
    self, node, async_mode=True
)
parameterized_active.base.ParameterizedCallSiteVisitor = _parameterized_visitor


_composed_reachable_module = parameterized_reachability.ReachableParameterizedCallSiteVisitor.visit_Module


def _reachable_parameterized_visit_module(self, node: ast.Module) -> None:
    previous = getattr(self, "_context_manager_definitions", None)
    self._context_manager_definitions = _module_runtime_definitions(node)
    try:
        _composed_reachable_module(self, node)
    finally:
        if previous is None:
            del self._context_manager_definitions
        else:
            self._context_manager_definitions = previous


def _visit_with_reachable_parameterized(self, node: ast.With | ast.AsyncWith, *, async_mode: bool) -> None:
    definitions = getattr(self, "_context_manager_definitions", {})
    prefix = "async-with" if async_mode else "with"
    acquired: list[ast.withitem] = []
    for index, item in enumerate(node.items):
        if acquired:
            digest = _entry_digest(acquired, definitions, async_mode=async_mode)
            self.context_nodes.append(
                (
                    _marker(prefix, f"item:{index}:requires-prior", digest),
                    _acquisition_dependency(acquired),
                )
            )
            try:
                self.visit(item.context_expr)
            finally:
                self.context_nodes.pop()
        else:
            self.visit(item.context_expr)
        acquired.append(item)
        if _context_entry_outcome(
            item.context_expr, definitions, async_mode=async_mode
        ) is _ENTRY_FAILS:
            return

    digest = _entry_digest(acquired, definitions, async_mode=async_mode)
    self._with_context(
        _marker(prefix, "body:requires-entry", digest),
        _acquisition_dependency(acquired),
        node.body,
    )


parameterized_reachability.ReachableParameterizedCallSiteVisitor.visit_Module = (
    _reachable_parameterized_visit_module
)
parameterized_reachability.ReachableParameterizedCallSiteVisitor.visit_With = (
    lambda self, node: _visit_with_reachable_parameterized(
        self, node, async_mode=False
    )
)
parameterized_reachability.ReachableParameterizedCallSiteVisitor.visit_AsyncWith = (
    lambda self, node: _visit_with_reachable_parameterized(
        self, node, async_mode=True
    )
)


# Parameterized helper discovery must also ignore a Finding(code, ...) that exists
# only behind a context manager whose entry is statically guaranteed to fail.
_previous_parameterized_finding_parameters = parameterized_active.parameterized_finding_parameters


class _PruneFailedContextManagers(ast.NodeTransformer):
    def __init__(self) -> None:
        self.definitions: dict[str, ast.AST] = {}

    def visit_Module(self, node: ast.Module) -> ast.AST:
        previous = self.definitions
        self.definitions = _module_runtime_definitions(node)
        try:
            return self.generic_visit(node)
        finally:
            self.definitions = previous

    def _visit_with(self, node: ast.With | ast.AsyncWith, *, async_mode: bool) -> ast.AST:
        for item in node.items:
            self.visit(item.context_expr)
            if _context_entry_outcome(
                item.context_expr, self.definitions, async_mode=async_mode
            ) is _ENTRY_FAILS:
                node.body = []
                return node
        node.body = [self.visit(statement) for statement in node.body]
        return node

    def visit_With(self, node: ast.With) -> ast.AST:
        return self._visit_with(node, async_mode=False)

    def visit_AsyncWith(self, node: ast.AsyncWith) -> ast.AST:
        return self._visit_with(node, async_mode=True)


def _context_aware_parameterized_finding_parameters(tree: ast.Module):
    transformed = _PruneFailedContextManagers().visit(copy.deepcopy(tree))
    ast.fix_missing_locations(transformed)
    return _previous_parameterized_finding_parameters(transformed)


parameterized_base.parameterized_finding_parameters = _context_aware_parameterized_finding_parameters
parameterized_active.base.parameterized_finding_parameters = _context_aware_parameterized_finding_parameters
parameterized_active.parameterized_finding_parameters = _context_aware_parameterized_finding_parameters


class ReleaseCandidateContextManagerEntryExecutionTests(unittest.TestCase):
    def test_wrapping_literal_finding_adds_context_entry_contract(self):
        direct = '''
def validate(findings):
    findings.append(Finding("PUBLIC_CODE", "visible"))
'''
        wrapped = '''
def manager():
    return unknown_context_manager()
def validate(findings):
    with manager():
        findings.append(Finding("PUBLIC_CODE", "visible"))
'''
        expected = literal_base.finding_semantic_signatures(direct)
        actual = literal_base.finding_semantic_signatures(wrapped)
        self.assertNotEqual(expected, actual)
        payload = json.loads(actual["PUBLIC_CODE"][0])
        self.assertTrue(
            any(marker.startswith("with:body:requires-entry") for marker in payload["context"])
        )

    def test_sync_enter_raise_hides_literal_finding(self):
        source = '''
class Exploding:
    def __enter__(self):
        raise RuntimeError("stop")
    def __exit__(self, exc_type, exc, tb):
        return False

def validate(findings):
    with Exploding():
        findings.append(Finding("PUBLIC_CODE", "hidden"))
'''
        self.assertNotIn("PUBLIC_CODE", literal_base.finding_semantic_signatures(source))
        self.assertEqual(
            extended_reachability.reachable_contracts(source, "sample.py"), Counter()
        )

    def test_async_enter_raise_hides_literal_finding(self):
        source = '''
class Exploding:
    async def __aenter__(self):
        raise RuntimeError("stop")
    async def __aexit__(self, exc_type, exc, tb):
        return False

async def validate(findings):
    async with Exploding():
        findings.append(Finding("PUBLIC_CODE", "hidden"))
'''
        self.assertNotIn("PUBLIC_CODE", literal_base.finding_semantic_signatures(source))
        self.assertEqual(
            extended_reachability.reachable_contracts(source, "sample.py"), Counter()
        )

    def test_entry_implementation_changes_literal_identity(self):
        original = '''
class Gate:
    def __enter__(self):
        return self
    def __exit__(self, exc_type, exc, tb):
        return False

def validate(findings):
    with Gate():
        findings.append(Finding("PUBLIC_CODE", "visible"))
'''
        changed = original.replace(
            "        return self\n    def __exit__",
            "        prepare()\n        return self\n    def __exit__",
        )
        self.assertNotEqual(
            literal_base.finding_semantic_signatures(original),
            literal_base.finding_semantic_signatures(changed),
        )

    def test_wrapping_parameterized_call_adds_entry_context(self):
        direct = '''
def read_text(path, findings, code):
    Finding(code, "decode failed", path="sample")
def validate(root, findings):
    read_text(root / "LICENSE", findings, "LICENSE_ENCODING")
'''
        wrapped = '''
def manager():
    return unknown_context_manager()
def read_text(path, findings, code):
    Finding(code, "decode failed", path="sample")
def validate(root, findings):
    with manager():
        read_text(root / "LICENSE", findings, "LICENSE_ENCODING")
'''
        expected = parameterized_active.parameterized_finding_contracts(direct, "sample.py")
        actual = parameterized_active.parameterized_finding_contracts(wrapped, "sample.py")
        self.assertNotEqual(expected, actual)
        payload = json.loads(next(iter(actual)))
        self.assertTrue(
            any(item["branch"].startswith("with:body:requires-entry") for item in payload["context"])
        )

    def test_enter_raise_hides_parameterized_call(self):
        source = '''
class Exploding:
    def __enter__(self):
        raise RuntimeError("stop")
    def __exit__(self, exc_type, exc, tb):
        return False

def read_text(path, findings, code):
    Finding(code, "decode failed", path="sample")

def validate(root, findings):
    with Exploding():
        read_text(root / "LICENSE", findings, "LICENSE_ENCODING")
'''
        self.assertEqual(
            parameterized_active.parameterized_finding_contracts(source, "sample.py"),
            set(),
        )
        self.assertEqual(
            parameterized_reachability.reachable_parameterized_contracts(source, "sample.py"),
            set(),
        )

    def test_later_context_expression_requires_prior_entry(self):
        source = '''
def validate(findings):
    with unknown_first(), findings.append(Finding("PUBLIC_CODE", "acquisition")):
        pass
'''
        payload = json.loads(
            literal_base.finding_semantic_signatures(source)["PUBLIC_CODE"][0]
        )
        self.assertTrue(
            any(marker.startswith("with:item:1:requires-prior") for marker in payload["context"])
        )


if __name__ == "__main__":
    unittest.main()
