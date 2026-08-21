from __future__ import annotations

import ast
import importlib
import unittest
from pathlib import Path


# Proactive final provenance closure for returned ToolResult.from_findings
# aliases. This layer deliberately extends the expression-aware side-car rather
# than replacing the already validated sink-selection machinery.


def _load_overlay(suffix: str):
    matches = sorted(Path(__file__).parent.glob(f"test_rc_*{suffix}.py"))
    if len(matches) != 1:
        raise RuntimeError(f"expected exactly one RC overlay for {suffix!r}")
    return importlib.import_module(matches[0].stem)


expr = _load_overlay("_returned_sink_alias_expression_closure")
alias_layer = expr.alias_layer

_NO = expr._NO
_YES = expr._YES
_MAYBE = expr._MAYBE

_previous_eval_expr = expr._eval_expr
_previous_flow = expr._flow
_previous_initial_aliases = expr._initial_aliases
_previous_static_bind_target = expr._static_bind_target
_previous_markers = alias_layer._aliased_return_markers

_active_module_aliases: dict[str, str] = {}
_active_factory_defs: dict[str, tuple[ast.FunctionDef, str]] = {}
_factory_stack: set[str] = set()


def _literal_string(node: ast.AST) -> str | None:
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    return None


def _simple_factory_return(function: ast.FunctionDef) -> ast.AST | None:
    if function.decorator_list:
        return None
    if (
        function.args.posonlyargs
        or function.args.args
        or function.args.kwonlyargs
        or function.args.vararg is not None
        or function.args.kwarg is not None
    ):
        return None

    body = list(function.body)
    if (
        body
        and isinstance(body[0], ast.Expr)
        and isinstance(body[0].value, ast.Constant)
        and isinstance(body[0].value.value, str)
    ):
        body = body[1:]
    if len(body) == 1 and isinstance(body[0], ast.Return) and body[0].value is not None:
        return body[0].value
    return None


def _eval_factory_call(
    node: ast.Call,
    env: dict[str, str],
    calls: list[tuple[ast.Call, str]] | None,
) -> tuple[str, dict[str, str]] | None:
    if not isinstance(node.func, ast.Name) or node.args or node.keywords:
        return None

    entry = _active_factory_defs.get(node.func.id)
    if entry is None:
        return None
    function, origin = entry
    if origin == "local" and getattr(node, "lineno", 0) <= getattr(function, "lineno", 0):
        return None

    returned = _simple_factory_return(function)
    if returned is None or node.func.id in _factory_stack:
        return None

    _factory_stack.add(node.func.id)
    try:
        factory_env = dict(env) if origin == "local" else dict(_active_module_aliases)
        state, _ = expr._eval_expr(returned, factory_env, None)
    finally:
        _factory_stack.remove(node.func.id)

    # The call itself has no arguments in this deliberately narrow factory
    # model, so evaluating its callee does not create additional alias side
    # effects in the caller. Preserve the caller environment.
    if state == _NO:
        return None
    return state, dict(env)


def _compare_truth(left: ast.AST, op: ast.cmpop, right: ast.AST) -> bool | None:
    try:
        left_value = ast.literal_eval(left)
        right_value = ast.literal_eval(right)
    except (ValueError, TypeError, SyntaxError):
        return None

    try:
        if isinstance(op, ast.Eq):
            return left_value == right_value
        if isinstance(op, ast.NotEq):
            return left_value != right_value
        if isinstance(op, ast.Is):
            return left_value is right_value
        if isinstance(op, ast.IsNot):
            return left_value is not right_value
        if isinstance(op, ast.Lt):
            return left_value < right_value
        if isinstance(op, ast.LtE):
            return left_value <= right_value
        if isinstance(op, ast.Gt):
            return left_value > right_value
        if isinstance(op, ast.GtE):
            return left_value >= right_value
        if isinstance(op, ast.In):
            return left_value in right_value
        if isinstance(op, ast.NotIn):
            return left_value not in right_value
    except Exception:
        return None
    return None


def _eval_compare(
    node: ast.Compare,
    env: dict[str, str],
    calls: list[tuple[ast.Call, str]] | None,
) -> tuple[str, dict[str, str]]:
    _, after_left = expr._eval_expr(node.left, env, calls)

    def walk(index: int, current: dict[str, str]) -> dict[str, str]:
        comparator = node.comparators[index]
        _, after = expr._eval_expr(comparator, current, calls)
        left = node.left if index == 0 else node.comparators[index - 1]
        truth = _compare_truth(left, node.ops[index], comparator)

        if index == len(node.comparators) - 1 or truth is False:
            return after
        if truth is True:
            return walk(index + 1, after)

        continued = walk(index + 1, dict(after))
        merged = expr._merge(after, continued)
        return after if merged is None else merged

    return _NO, walk(0, after_left)


def _eval_expr_with_provenance(
    node: ast.AST,
    env: dict[str, str],
    calls: list[tuple[ast.Call, str]] | None = None,
) -> tuple[str, dict[str, str]]:
    if isinstance(node, ast.Compare) and node.comparators:
        return _eval_compare(node, env, calls)

    if (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "getattr"
        and len(node.args) in {2, 3}
        and not node.keywords
        and _literal_string(node.args[1]) == "from_findings"
    ):
        _, after = expr._eval_expr(node.args[0], env, calls)
        _, after = expr._eval_expr(node.args[1], after, calls)
        if len(node.args) == 3:
            default_state, after = expr._eval_expr(node.args[2], after, calls)
            return expr._join(_YES, default_state), after
        return _YES, after

    if isinstance(node, ast.Call):
        factory = _eval_factory_call(node, env, calls)
        if factory is not None:
            return factory

    return _previous_eval_expr(node, env, calls)


expr._eval_expr = _eval_expr_with_provenance


def _flow_with_assert_expression(
    statements: list[ast.stmt],
    env: dict[str, str],
    return_states: dict[int, dict[str, str]],
) -> dict[str, str] | None:
    # On every path that continues beyond an assert, its test has executed.
    # Model that expression for alias side effects while leaving assertion
    # termination semantics to the already established reachability layers.
    normalized: list[ast.stmt] = []
    for statement in statements:
        if isinstance(statement, ast.Assert):
            replacement = ast.Expr(value=statement.test)
            ast.copy_location(replacement, statement)
            normalized.append(replacement)
        else:
            normalized.append(statement)
    return _previous_flow(normalized, env, return_states)


expr._flow = _flow_with_assert_expression


def _static_bind_target_with_starred(
    target: ast.AST,
    value: ast.AST,
    env: dict[str, str],
) -> dict[str, str]:
    if isinstance(target, (ast.Tuple, ast.List)) and isinstance(
        value,
        (ast.Tuple, ast.List),
    ):
        starred = [index for index, item in enumerate(target.elts) if isinstance(item, ast.Starred)]
        if len(starred) == 1:
            star_index = starred[0]
            before = target.elts[:star_index]
            after_targets = target.elts[star_index + 1 :]
            if len(value.elts) >= len(before) + len(after_targets):
                result = dict(env)
                for target_item, value_item in zip(before, value.elts[: len(before)]):
                    result = expr._static_bind_target(target_item, value_item, result)
                if after_targets:
                    values = value.elts[-len(after_targets) :]
                    for target_item, value_item in zip(after_targets, values):
                        result = expr._static_bind_target(target_item, value_item, result)
                result = expr._kill_target(result, target.elts[star_index])
                return result
    return _previous_static_bind_target(target, value, env)


expr._static_bind_target = _static_bind_target_with_starred


class _LocalBindingCollector(ast.NodeVisitor):
    def __init__(self, root: ast.FunctionDef | ast.AsyncFunctionDef):
        self.root = root
        self.names: set[str] = set()
        self.global_names: set[str] = set()
        self.nonlocal_names: set[str] = set()
        self.counts: dict[str, int] = {}

    def _add(self, name: str) -> None:
        self.names.add(name)
        self.counts[name] = self.counts.get(name, 0) + 1

    def collect(self) -> tuple[set[str], dict[str, int]]:
        args = self.root.args
        for argument in [
            *args.posonlyargs,
            *args.args,
            *args.kwonlyargs,
        ]:
            self._add(argument.arg)
        if args.vararg is not None:
            self._add(args.vararg.arg)
        if args.kwarg is not None:
            self._add(args.kwarg.arg)
        for statement in self.root.body:
            self.visit(statement)
        excluded = self.global_names | self.nonlocal_names
        return self.names - excluded, {
            name: count for name, count in self.counts.items() if name not in excluded
        }

    def visit_Name(self, node: ast.Name) -> None:
        if isinstance(node.ctx, (ast.Store, ast.Del)):
            self._add(node.id)

    def visit_Global(self, node: ast.Global) -> None:
        self.global_names.update(node.names)

    def visit_Nonlocal(self, node: ast.Nonlocal) -> None:
        self.nonlocal_names.update(node.names)

    def visit_Import(self, node: ast.Import) -> None:
        for item in node.names:
            self._add(item.asname or item.name.split(".", 1)[0])

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        for item in node.names:
            self._add(item.asname or item.name)

    def visit_ExceptHandler(self, node: ast.ExceptHandler) -> None:
        if node.name:
            self._add(node.name)
        if node.type is not None:
            self.visit(node.type)
        for statement in node.body:
            self.visit(statement)

    def visit_MatchAs(self, node: ast.MatchAs) -> None:
        if node.name:
            self._add(node.name)
        if node.pattern is not None:
            self.visit(node.pattern)

    def visit_MatchStar(self, node: ast.MatchStar) -> None:
        if node.name:
            self._add(node.name)

    def visit_MatchMapping(self, node: ast.MatchMapping) -> None:
        if node.rest:
            self._add(node.rest)
        for pattern in node.patterns:
            self.visit(pattern)
        for key in node.keys:
            self.visit(key)

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        if node is self.root:
            return
        self._add(node.name)
        for decorator in node.decorator_list:
            self.visit(decorator)
        for default in node.args.defaults:
            self.visit(default)
        for default in node.args.kw_defaults:
            if default is not None:
                self.visit(default)

    visit_AsyncFunctionDef = visit_FunctionDef

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        self._add(node.name)
        for decorator in node.decorator_list:
            self.visit(decorator)
        for base in node.bases:
            self.visit(base)
        for keyword in node.keywords:
            self.visit(keyword.value)

    def visit_Lambda(self, node: ast.Lambda) -> None:
        for default in node.args.defaults:
            self.visit(default)
        for default in node.args.kw_defaults:
            if default is not None:
                self.visit(default)

    def _visit_comprehension_expression(self, node: ast.AST) -> None:
        generators = node.generators
        for generator in generators:
            self.visit(generator.iter)
            for condition in generator.ifs:
                self.visit(condition)
        if isinstance(node, ast.DictComp):
            self.visit(node.key)
            self.visit(node.value)
        else:
            self.visit(node.elt)

    visit_ListComp = _visit_comprehension_expression
    visit_SetComp = _visit_comprehension_expression
    visit_GeneratorExp = _visit_comprehension_expression
    visit_DictComp = _visit_comprehension_expression


def _module_root(
    node: ast.AST,
    parents: dict[int, ast.AST],
) -> ast.Module | None:
    current = node
    while id(current) in parents:
        current = parents[id(current)]
    return current if isinstance(current, ast.Module) else None


def _module_factories(module: ast.Module) -> dict[str, tuple[ast.FunctionDef, str]]:
    result: dict[str, tuple[ast.FunctionDef, str]] = {}
    for statement in module.body:
        if isinstance(statement, ast.FunctionDef) and _simple_factory_return(statement) is not None:
            result[statement.name] = (statement, "module")
    return result


def _local_factories(
    function: ast.FunctionDef | ast.AsyncFunctionDef,
    counts: dict[str, int],
) -> dict[str, tuple[ast.FunctionDef, str]]:
    result: dict[str, tuple[ast.FunctionDef, str]] = {}
    for statement in function.body:
        if (
            isinstance(statement, ast.FunctionDef)
            and counts.get(statement.name) == 1
            and _simple_factory_return(statement) is not None
        ):
            result[statement.name] = (statement, "local")
    return result


def _module_aliases(module: ast.Module) -> dict[str, str]:
    states: dict[int, dict[str, str]] = {}
    result = expr._flow(module.body, {}, states)
    return {} if result is None else result


def _initial_aliases_with_module(
    function: ast.FunctionDef | ast.AsyncFunctionDef,
) -> dict[str, str]:
    initial = dict(_previous_initial_aliases(function))
    local_names, _ = _LocalBindingCollector(function).collect()
    for name, state in _active_module_aliases.items():
        if name not in local_names and name not in initial:
            initial[name] = state
    return initial


expr._initial_aliases = _initial_aliases_with_module


def _markers_with_module_and_factory_provenance(
    finding: ast.Call,
    receiver: ast.AST,
    parents: dict[int, ast.AST],
) -> list[str]:
    global _active_module_aliases, _active_factory_defs

    function = alias_layer.sink_state._enclosing_function(finding, parents)
    module = _module_root(function, parents) if function is not None else None
    if function is None or module is None:
        return _previous_markers(finding, receiver, parents)

    local_names, counts = _LocalBindingCollector(function).collect()
    module_factories = {
        name: entry
        for name, entry in _module_factories(module).items()
        if name not in local_names
    }
    local_factories = _local_factories(function, counts)

    old_aliases = _active_module_aliases
    old_factories = _active_factory_defs
    try:
        _active_factory_defs = {**module_factories, **local_factories}
        # Module-level simple assignments are evaluated only after the available
        # simple factory set is known, allowing `maker = factory()` without
        # executing candidate source.
        _active_module_aliases = _module_aliases(module)
        return _previous_markers(finding, receiver, parents)
    finally:
        _active_module_aliases = old_aliases
        _active_factory_defs = old_factories


alias_layer._aliased_return_markers = _markers_with_module_and_factory_provenance


class ReleaseCandidateReturnedSinkAliasProvenanceFinalTests(unittest.TestCase):
    def _has_marker(self, source: str) -> bool:
        sink = expr.ReleaseCandidateReturnedSinkAliasExpressionClosureTests()._sink(source)
        return any(item.startswith(alias_layer._ALIAS_SELECTION_PREFIX) for item in sink)

    def test_module_level_constructor_alias_is_tracked(self) -> None:
        source = """
from standards_tools import Finding, ToolResult

maker = ToolResult.from_findings

def validate():
    findings = []
    findings.append(Finding("PUBLIC_CODE", "visible"))
    return maker(tool="validate", version="1", findings=[])
"""
        self.assertTrue(self._has_marker(source))

    def test_local_binding_shadows_module_constructor_alias(self) -> None:
        source = """
from standards_tools import Finding, ToolResult

maker = ToolResult.from_findings

def harmless(**kwargs):
    return kwargs

def validate():
    maker = harmless
    findings = []
    findings.append(Finding("PUBLIC_CODE", "visible"))
    return maker(tool="validate", version="1", findings=[])
"""
        self.assertFalse(self._has_marker(source))

    def test_getattr_constructor_alias_is_tracked(self) -> None:
        source = """
from standards_tools import Finding, ToolResult

def validate():
    findings = []
    maker = getattr(ToolResult, "from_findings")
    findings.append(Finding("PUBLIC_CODE", "visible"))
    return maker(tool="validate", version="1", findings=[])
"""
        self.assertTrue(self._has_marker(source))

    def test_simple_module_factory_returning_constructor_is_tracked(self) -> None:
        source = """
from standards_tools import Finding, ToolResult

def sink_factory():
    return ToolResult.from_findings

def validate():
    findings = []
    maker = sink_factory()
    findings.append(Finding("PUBLIC_CODE", "visible"))
    return maker(tool="validate", version="1", findings=[])
"""
        self.assertTrue(self._has_marker(source))

    def test_simple_local_factory_returning_constructor_is_tracked(self) -> None:
        source = """
from standards_tools import Finding, ToolResult

def validate():
    def sink_factory():
        return ToolResult.from_findings
    findings = []
    maker = sink_factory()
    findings.append(Finding("PUBLIC_CODE", "visible"))
    return maker(tool="validate", version="1", findings=[])
"""
        self.assertTrue(self._has_marker(source))

    def test_assert_walrus_alias_side_effect_is_tracked(self) -> None:
        source = """
from standards_tools import Finding, ToolResult

def validate():
    findings = []
    assert (maker := ToolResult.from_findings)
    findings.append(Finding("PUBLIC_CODE", "visible"))
    return maker(tool="validate", version="1", findings=[])
"""
        self.assertTrue(self._has_marker(source))

    def test_statically_short_circuited_compare_does_not_bind_alias(self) -> None:
        source = """
from standards_tools import Finding, ToolResult

def harmless(**kwargs):
    return kwargs

def validate():
    maker = harmless
    findings = []
    1 > 2 > (maker := ToolResult.from_findings)
    findings.append(Finding("PUBLIC_CODE", "visible"))
    return maker(tool="validate", version="1", findings=[])
"""
        self.assertFalse(self._has_marker(source))

    def test_starred_destructuring_preserves_tail_alias(self) -> None:
        source = """
from standards_tools import Finding, ToolResult

def harmless(**kwargs):
    return kwargs

def validate():
    first, *rest, maker = (harmless, harmless, ToolResult.from_findings)
    findings = []
    findings.append(Finding("PUBLIC_CODE", "visible"))
    return maker(tool="validate", version="1", findings=[])
"""
        self.assertTrue(self._has_marker(source))


if __name__ == "__main__":
    unittest.main()
