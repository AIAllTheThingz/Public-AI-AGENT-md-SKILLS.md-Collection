from __future__ import annotations

import ast
import importlib
import json
import unittest
from pathlib import Path

import rc_finding_code_contracts_base as literal_base


# Final expression-aware returned-sink alias closure for PR #71.
#
# This side-car leaves the established constructor-alias flow untouched and
# strengthens only the marker calculation used by the public finding sink
# contract. It follows ToolResult.from_findings identity through expression
# values and NamedExpr side effects in execution order, including nested
# walruses, conditional expressions, short-circuit expressions, and aliases
# created earlier in statement tests. Private alias spellings remain excluded
# from compatibility identity.


def _load_overlay(suffix: str):
    matches = sorted(Path(__file__).parent.glob(f"test_rc_*{suffix}.py"))
    if len(matches) != 1:
        raise RuntimeError(f"expected exactly one RC overlay for {suffix!r}")
    return importlib.import_module(matches[0].stem)


namedexpr_layer = _load_overlay("_named_expression_constructor_aliases")
alias_layer = namedexpr_layer.alias_layer

_NO = alias_layer._ALIAS_NO
_YES = alias_layer._ALIAS_YES
_MAYBE = alias_layer._ALIAS_MAYBE


def _join(left: str, right: str) -> str:
    return alias_layer._join_alias_state(left, right)


def _merge(
    left: dict[str, str] | None,
    right: dict[str, str] | None,
) -> dict[str, str] | None:
    return alias_layer._merge_alias_maps(left, right)


def _bind(env: dict[str, str], name: str, state: str) -> dict[str, str]:
    result = dict(env)
    if state == _NO:
        result.pop(name, None)
    else:
        result[name] = state
    return result


def _kill_target(env: dict[str, str], target: ast.AST | None) -> dict[str, str]:
    result = dict(env)
    if target is None:
        return result
    for name in alias_layer._assigned_names(target):
        result.pop(name, None)
    return result


def _truth(node: ast.AST, state: str) -> bool | None:
    literal = alias_layer._literal_truth(node)
    if literal is not None:
        return literal
    if state == _YES:
        # A bound method object such as ToolResult.from_findings is truthy.
        return True
    if isinstance(node, ast.Lambda):
        return True
    return None


def _eval_boolop(
    node: ast.BoolOp,
    env: dict[str, str],
    calls: list[tuple[ast.Call, str]] | None,
) -> tuple[str, dict[str, str]]:
    values = list(node.values)

    def walk(index: int, current: dict[str, str]) -> tuple[str, dict[str, str]]:
        state, after = _eval_expr(values[index], current, calls)
        if index == len(values) - 1:
            return state, after

        truth = _truth(values[index], state)
        if isinstance(node.op, ast.And):
            if truth is False:
                return state, after
            if truth is True:
                return walk(index + 1, after)
        else:
            if truth is True:
                return state, after
            if truth is False:
                return walk(index + 1, after)

        continued_state, continued_env = walk(index + 1, dict(after))
        merged = _merge(after, continued_env)
        return _join(state, continued_state), (after if merged is None else merged)

    return walk(0, dict(env))


def _eval_expr(
    node: ast.AST,
    env: dict[str, str],
    calls: list[tuple[ast.Call, str]] | None = None,
) -> tuple[str, dict[str, str]]:
    current = dict(env)

    if alias_layer._is_direct_from_findings(node):
        return _YES, current

    if isinstance(node, ast.Name):
        return current.get(node.id, _NO), current

    if isinstance(node, ast.NamedExpr) and isinstance(node.target, ast.Name):
        value_state, after = _eval_expr(node.value, current, calls)
        after = _bind(after, node.target.id, value_state)
        return value_state, after

    if isinstance(node, ast.IfExp):
        _, after_test = _eval_expr(node.test, current, calls)
        truth = alias_layer._literal_truth(node.test)
        if truth is True:
            return _eval_expr(node.body, after_test, calls)
        if truth is False:
            return _eval_expr(node.orelse, after_test, calls)

        body_state, body_env = _eval_expr(node.body, dict(after_test), calls)
        else_state, else_env = _eval_expr(node.orelse, dict(after_test), calls)
        merged = _merge(body_env, else_env)
        return _join(body_state, else_state), (
            after_test if merged is None else merged
        )

    if isinstance(node, ast.BoolOp):
        return _eval_boolop(node, current, calls)

    if isinstance(node, ast.Call):
        func_state, after = _eval_expr(node.func, current, calls)
        if (
            calls is not None
            and not alias_layer._is_direct_from_findings(node.func)
            and func_state != _NO
        ):
            calls.append((node, func_state))

        for argument in node.args:
            _, after = _eval_expr(argument, after, calls)
        for keyword in node.keywords:
            _, after = _eval_expr(keyword.value, after, calls)

        # Handle the simplest immediately-invoked lambda factory without
        # claiming arbitrary calls return constructor aliases.
        if (
            isinstance(node.func, ast.Lambda)
            and not node.args
            and not node.keywords
            and not node.func.args.posonlyargs
            and not node.func.args.args
            and not node.func.args.kwonlyargs
            and node.func.args.vararg is None
            and node.func.args.kwarg is None
        ):
            return _eval_expr(node.func.body, after, calls)
        return _NO, after

    if isinstance(node, ast.Subscript) and isinstance(node.value, ast.Dict):
        after = dict(current)
        entries: list[tuple[object, str]] = []
        for key, value in zip(node.value.keys, node.value.values):
            if key is None:
                _, after = _eval_expr(value, after, calls)
                continue
            _, after = _eval_expr(key, after, calls)
            value_state, after = _eval_expr(value, after, calls)
            try:
                literal_key = ast.literal_eval(key)
            except (ValueError, TypeError, SyntaxError):
                literal_key = object()
            entries.append((literal_key, value_state))
        _, after = _eval_expr(node.slice, after, calls)
        try:
            selected_key = ast.literal_eval(node.slice)
        except (ValueError, TypeError, SyntaxError):
            selected_key = object()
        matches = [state for key, state in entries if key == selected_key]
        if len(matches) == 1:
            return matches[0], after
        if any(state != _NO for _, state in entries):
            return _MAYBE, after
        return _NO, after

    if isinstance(node, ast.Subscript) and isinstance(
        node.value,
        (ast.Tuple, ast.List),
    ):
        states: list[str] = []
        after = dict(current)
        for element in node.value.elts:
            element_state, after = _eval_expr(element, after, calls)
            states.append(element_state)
        _, after = _eval_expr(node.slice, after, calls)
        try:
            index = ast.literal_eval(node.slice)
        except (ValueError, TypeError, SyntaxError):
            index = None
        if isinstance(index, int) and -len(states) <= index < len(states):
            return states[index], after
        if any(state != _NO for state in states):
            return _MAYBE, after
        return _NO, after

    if isinstance(node, ast.Attribute):
        _, after = _eval_expr(node.value, current, calls)
        return _NO, after

    if isinstance(node, ast.Subscript):
        _, after = _eval_expr(node.value, current, calls)
        _, after = _eval_expr(node.slice, after, calls)
        return _NO, after

    if isinstance(node, (ast.Tuple, ast.List, ast.Set)):
        after = dict(current)
        for element in node.elts:
            _, after = _eval_expr(element, after, calls)
        return _NO, after

    if isinstance(node, ast.Dict):
        after = dict(current)
        for key, value in zip(node.keys, node.values):
            if key is not None:
                _, after = _eval_expr(key, after, calls)
            _, after = _eval_expr(value, after, calls)
        return _NO, after

    if isinstance(node, ast.Lambda):
        # Lambda body execution is deferred. Defaults execute at definition.
        after = dict(current)
        for default in node.args.defaults:
            _, after = _eval_expr(default, after, calls)
        for default in node.args.kw_defaults:
            if default is not None:
                _, after = _eval_expr(default, after, calls)
        return _NO, after

    if isinstance(node, ast.GeneratorExp):
        # Generator bodies are deferred; only the outermost iterable is eagerly
        # evaluated at generator creation.
        after = dict(current)
        if node.generators:
            _, after = _eval_expr(node.generators[0].iter, after, calls)
        return _NO, after

    if isinstance(node, (ast.ListComp, ast.SetComp, ast.DictComp)):
        # Eager comprehensions may execute zero times. Retain possible
        # NamedExpr side effects without claiming they definitely occur.
        after_first = dict(current)
        if node.generators:
            _, after_first = _eval_expr(node.generators[0].iter, after_first, calls)

        possible = dict(after_first)
        path = dict(after_first)
        for index, generator in enumerate(node.generators):
            if index:
                _, path = _eval_expr(generator.iter, path, calls)
            for condition in generator.ifs:
                _, path = _eval_expr(condition, path, calls)

        if isinstance(node, ast.DictComp):
            _, path = _eval_expr(node.key, path, calls)
            _, path = _eval_expr(node.value, path, calls)
        else:
            _, path = _eval_expr(node.elt, path, calls)

        merged = _merge(possible, path)
        return _NO, (possible if merged is None else merged)

    # Other expression nodes do not themselves preserve constructor identity.
    # Still walk expression children in field order so nested NamedExpr bindings
    # are not lost.
    after = dict(current)
    for _, value in ast.iter_fields(node):
        if isinstance(value, ast.expr):
            _, after = _eval_expr(value, after, calls)
        elif isinstance(value, list):
            for item in value:
                if isinstance(item, ast.expr):
                    _, after = _eval_expr(item, after, calls)
    return _NO, after


def _value_state(node: ast.AST, env: dict[str, str]) -> str:
    state, _ = _eval_expr(node, env)
    return state


def _static_bind_target(
    target: ast.AST,
    value: ast.AST,
    env: dict[str, str],
) -> dict[str, str]:
    if isinstance(target, ast.Name):
        return _bind(env, target.id, _value_state(value, env))

    if isinstance(target, (ast.Tuple, ast.List)) and isinstance(
        value,
        (ast.Tuple, ast.List),
    ):
        if (
            not any(isinstance(item, ast.Starred) for item in target.elts)
            and len(target.elts) == len(value.elts)
        ):
            result = dict(env)
            for target_item, value_item in zip(target.elts, value.elts):
                result = _static_bind_target(target_item, value_item, result)
            return result

    return _kill_target(env, target)


def _assign(
    statement: ast.Assign | ast.AnnAssign,
    env: dict[str, str],
) -> dict[str, str]:
    if isinstance(statement, ast.AnnAssign):
        if statement.value is None:
            return dict(env)
        targets = [statement.target]
        value = statement.value
    else:
        targets = list(statement.targets)
        value = statement.value

    state, after = _eval_expr(value, env)

    if all(isinstance(target, ast.Name) for target in targets):
        for target in targets:
            after = _bind(after, target.id, state)
        return after

    if len(targets) == 1:
        return _static_bind_target(targets[0], value, after)

    result = dict(after)
    for target in targets:
        result = _kill_target(result, target)
    return result


def _literal_iterable_state(
    iterable: ast.AST,
    env: dict[str, str],
) -> str | None:
    if not isinstance(iterable, (ast.Tuple, ast.List, ast.Set)):
        return None
    if not iterable.elts:
        return _NO
    states = [_value_state(element, env) for element in iterable.elts]
    state = states[0]
    for other in states[1:]:
        state = _join(state, other)
    return state


def _pattern_names(pattern: ast.pattern) -> set[str]:
    names: set[str] = set()
    for node in ast.walk(pattern):
        if isinstance(node, ast.MatchAs) and node.name:
            names.add(node.name)
        elif isinstance(node, ast.MatchStar) and node.name:
            names.add(node.name)
        elif isinstance(node, ast.MatchMapping) and node.rest:
            names.add(node.rest)
    return names


def _flow(
    statements: list[ast.stmt],
    env: dict[str, str],
    return_states: dict[int, dict[str, str]],
) -> dict[str, str] | None:
    current: dict[str, str] | None = dict(env)

    for statement in statements:
        if current is None:
            break

        if isinstance(statement, ast.Return):
            return_states[id(statement)] = dict(current)
            return None

        if isinstance(statement, ast.Raise):
            return None

        if isinstance(statement, (ast.Break, ast.Continue)):
            return None

        if isinstance(statement, (ast.Assign, ast.AnnAssign)):
            current = _assign(statement, current)
            continue

        if isinstance(statement, ast.Expr):
            _, current = _eval_expr(statement.value, current)
            continue

        if isinstance(statement, ast.AugAssign):
            _, current = _eval_expr(statement.value, current)
            current = _kill_target(current, statement.target)
            continue

        if isinstance(statement, ast.Delete):
            for target in statement.targets:
                current = _kill_target(current, target)
            continue

        if isinstance(statement, (ast.FunctionDef, ast.AsyncFunctionDef)):
            for decorator in statement.decorator_list:
                _, current = _eval_expr(decorator, current)
            for default in statement.args.defaults:
                _, current = _eval_expr(default, current)
            for default in statement.args.kw_defaults:
                if default is not None:
                    _, current = _eval_expr(default, current)
            current.pop(statement.name, None)
            continue

        if isinstance(statement, ast.ClassDef):
            for decorator in statement.decorator_list:
                _, current = _eval_expr(decorator, current)
            for base in statement.bases:
                _, current = _eval_expr(base, current)
            for keyword in statement.keywords:
                _, current = _eval_expr(keyword.value, current)
            current.pop(statement.name, None)
            continue

        if isinstance(statement, (ast.Import, ast.ImportFrom)):
            current = alias_layer._kill_bound_names(statement, current)
            continue

        if isinstance(statement, ast.If):
            test_state, after_test = _eval_expr(statement.test, current)
            truth = _truth(statement.test, test_state)
            if truth is True:
                current = _flow(statement.body, after_test, return_states)
                continue
            if truth is False:
                current = _flow(statement.orelse, after_test, return_states)
                continue

            body_state = _flow(statement.body, dict(after_test), return_states)
            else_state = (
                _flow(statement.orelse, dict(after_test), return_states)
                if statement.orelse
                else dict(after_test)
            )
            current = _merge(body_state, else_state)
            continue

        if isinstance(statement, (ast.With, ast.AsyncWith)):
            entered = dict(current)
            for item in statement.items:
                _, entered = _eval_expr(item.context_expr, entered)
                entered = _kill_target(entered, item.optional_vars)
            current = _flow(statement.body, entered, return_states)
            continue

        if isinstance(statement, (ast.For, ast.AsyncFor)):
            _, after_iter = _eval_expr(statement.iter, current)
            body_start = _kill_target(after_iter, statement.target)
            literal_state = _literal_iterable_state(statement.iter, after_iter)
            if isinstance(statement.target, ast.Name) and literal_state is not None:
                body_start = _bind(body_start, statement.target.id, literal_state)

            body_state = _flow(statement.body, body_start, return_states)
            joined = _merge(after_iter, body_state)
            if joined is None:
                joined = dict(after_iter)
            current = (
                _flow(statement.orelse, joined, return_states)
                if statement.orelse
                else joined
            )
            continue

        if isinstance(statement, ast.While):
            test_state, after_test = _eval_expr(statement.test, current)
            truth = _truth(statement.test, test_state)
            if truth is False:
                current = (
                    _flow(statement.orelse, after_test, return_states)
                    if statement.orelse
                    else after_test
                )
                continue

            body_state = _flow(statement.body, dict(after_test), return_states)
            joined = _merge(after_test, body_state)
            if joined is None:
                joined = dict(after_test)
            current = (
                _flow(statement.orelse, joined, return_states)
                if statement.orelse
                else joined
            )
            continue

        try_types = (ast.Try,)
        if hasattr(ast, "TryStar"):
            try_types = (*try_types, ast.TryStar)
        if isinstance(statement, try_types):
            body_state = _flow(statement.body, dict(current), return_states)
            normal_state = (
                _flow(statement.orelse, body_state, return_states)
                if body_state is not None and statement.orelse
                else body_state
            )

            merged = normal_state
            for handler in statement.handlers:
                handler_env = dict(current)
                if handler.type is not None:
                    _, handler_env = _eval_expr(handler.type, handler_env)
                if handler.name:
                    handler_env.pop(handler.name, None)
                handler_state = _flow(handler.body, handler_env, return_states)
                merged = _merge(merged, handler_state)

            current = (
                _flow(statement.finalbody, merged, return_states)
                if statement.finalbody and merged is not None
                else merged
            )
            continue

        if isinstance(statement, ast.Match):
            subject_state, after_subject = _eval_expr(statement.subject, current)
            merged: dict[str, str] | None = None
            catchall = False
            for case in statement.cases:
                case_env = dict(after_subject)
                if (
                    isinstance(case.pattern, ast.MatchAs)
                    and case.pattern.pattern is None
                    and case.pattern.name
                ):
                    case_env = _bind(
                        case_env,
                        case.pattern.name,
                        subject_state,
                    )
                else:
                    for name in _pattern_names(case.pattern):
                        case_env.pop(name, None)

                if case.guard is not None:
                    guard_state, case_env = _eval_expr(case.guard, case_env)
                    if _truth(case.guard, guard_state) is False:
                        continue

                case_state = _flow(case.body, case_env, return_states)
                merged = _merge(merged, case_state)
                if (
                    case.guard is None
                    and isinstance(case.pattern, ast.MatchAs)
                    and case.pattern.pattern is None
                ):
                    catchall = True

            if not catchall:
                merged = _merge(merged, after_subject)
            current = merged
            continue

    return current


def _initial_aliases(
    function: ast.FunctionDef | ast.AsyncFunctionDef,
) -> dict[str, str]:
    initial: dict[str, str] = {}
    positional = [*function.args.posonlyargs, *function.args.args]
    defaults = list(function.args.defaults)
    if defaults:
        for argument, default in zip(positional[-len(defaults):], defaults):
            state = _value_state(default, {})
            if state != _NO:
                initial[argument.arg] = _MAYBE

    for argument, default in zip(function.args.kwonlyargs, function.args.kw_defaults):
        if default is None:
            continue
        state = _value_state(default, {})
        if state != _NO:
            initial[argument.arg] = _MAYBE
    return initial


def _return_states(
    function: ast.FunctionDef | ast.AsyncFunctionDef,
) -> dict[int, dict[str, str]]:
    states: dict[int, dict[str, str]] = {}
    _flow(function.body, _initial_aliases(function), states)
    return states


def _return_calls(
    expression: ast.AST,
    env: dict[str, str],
) -> list[tuple[ast.Call, str]]:
    calls: list[tuple[ast.Call, str]] = []
    _eval_expr(expression, env, calls)
    return calls


def _aliased_return_markers_expression_aware(
    finding: ast.Call,
    receiver: ast.AST,
    parents: dict[int, ast.AST],
) -> list[str]:
    function = alias_layer.sink_state._enclosing_function(finding, parents)
    if function is None:
        return []

    receiver_name = alias_layer.sink_state._root_name(receiver)
    if (
        receiver_name is None
        or receiver_name
        in alias_layer.returned_selection._function_parameter_names(function)
    ):
        return []

    finding_line = getattr(finding, "lineno", 10**9)
    return_states = _return_states(function)
    markers: list[tuple[int, int, str]] = []

    for returned in ast.walk(function):
        if not (
            isinstance(returned, ast.Return)
            and returned.value is not None
            and alias_layer.sink_state._belongs_to_function(returned, function, parents)
            and getattr(returned, "lineno", 0) > finding_line
            and alias_layer.post_sink._can_share_execution_path(
                finding,
                returned,
                function,
                parents,
            )
        ):
            continue

        env = return_states.get(id(returned), {})
        for call, alias_state in _return_calls(returned.value, env):
            if alias_layer._is_direct_from_findings(call.func):
                continue

            selection = alias_layer._aliased_sink_selection(call, receiver_name)
            if selection is None:
                continue

            state, selector = selection
            if state == "kept":
                continue

            payload: dict[str, object] = {
                "context": alias_layer.sink_state._sink_state_context(
                    returned,
                    function,
                    parents,
                ),
                "constructor": (
                    "definite-alias"
                    if alias_state == _YES
                    else "possible-alias"
                ),
                "selection": state,
            }
            if selector is not None:
                payload["selector"] = literal_base.canonical_ast(selector)

            markers.append(
                (
                    getattr(returned, "lineno", 0),
                    getattr(returned, "col_offset", 0),
                    json.dumps(payload, sort_keys=True),
                )
            )

    markers.sort()
    return [value for _, _, value in markers]


# The existing emission-sink closure resolves this function through the alias
# module's globals at call time, so replacing only this side-car preserves all
# previously validated sink selection and expanded-keyword behavior.
alias_layer._aliased_return_markers = _aliased_return_markers_expression_aware


class ReleaseCandidateReturnedSinkAliasExpressionClosureTests(unittest.TestCase):
    def _sink(self, source: str) -> list[str]:
        signature = literal_base.finding_semantic_signatures(
            source,
            "sample.py",
        )["PUBLIC_CODE"][0]
        return json.loads(signature)["sink"]

    def _has_alias_marker(self, source: str) -> bool:
        return any(
            item.startswith(alias_layer._ALIAS_SELECTION_PREFIX)
            for item in self._sink(source)
        )

    def test_nested_walrus_alias_discard_is_tracked(self) -> None:
        source = """
from standards_tools import Finding, ToolResult

def validate():
    findings = []
    True and (maker := ToolResult.from_findings)
    findings.append(Finding("PUBLIC_CODE", "visible"))
    return maker(tool="validate", version="1", findings=[])
"""
        self.assertTrue(self._has_alias_marker(source))

    def test_short_circuited_nested_walrus_does_not_bind(self) -> None:
        source = """
from standards_tools import Finding, ToolResult

def harmless(**kwargs):
    return kwargs

def validate():
    findings = []
    maker = harmless
    False and (maker := ToolResult.from_findings)
    findings.append(Finding("PUBLIC_CODE", "visible"))
    return maker(tool="validate", version="1", findings=[])
"""
        self.assertFalse(self._has_alias_marker(source))

    def test_conditional_expression_alias_is_joined(self) -> None:
        source = """
from standards_tools import Finding, ToolResult

def harmless(**kwargs):
    return kwargs

def validate(flag):
    findings = []
    maker = ToolResult.from_findings if flag else harmless
    findings.append(Finding("PUBLIC_CODE", "visible"))
    return maker(tool="validate", version="1", findings=[])
"""
        self.assertTrue(self._has_alias_marker(source))

    def test_if_test_walrus_persists_after_statement(self) -> None:
        source = """
from standards_tools import Finding, ToolResult

def validate():
    findings = []
    if (maker := ToolResult.from_findings):
        pass
    findings.append(Finding("PUBLIC_CODE", "visible"))
    return maker(tool="validate", version="1", findings=[])
"""
        self.assertTrue(self._has_alias_marker(source))

    def test_return_expression_walrus_precedes_aliased_call(self) -> None:
        source = """
from standards_tools import Finding, ToolResult

def validate():
    findings = []
    findings.append(Finding("PUBLIC_CODE", "visible"))
    return (
        (maker := ToolResult.from_findings),
        maker(tool="validate", version="1", findings=[]),
    )[1]
"""
        self.assertTrue(self._has_alias_marker(source))

    def test_short_circuit_value_alias_is_conservative(self) -> None:
        source = """
from standards_tools import Finding, ToolResult

def validate(flag):
    findings = []
    maker = flag and ToolResult.from_findings
    findings.append(Finding("PUBLIC_CODE", "visible"))
    return maker(tool="validate", version="1", findings=[])
"""
        self.assertTrue(self._has_alias_marker(source))

    def test_literal_sequence_selection_tracks_alias(self) -> None:
        source = """
from standards_tools import Finding, ToolResult

def harmless(**kwargs):
    return kwargs

def validate():
    findings = []
    maker = (harmless, ToolResult.from_findings)[1]
    findings.append(Finding("PUBLIC_CODE", "visible"))
    return maker(tool="validate", version="1", findings=[])
"""
        self.assertTrue(self._has_alias_marker(source))

    def test_destructured_constructor_alias_is_tracked(self) -> None:
        source = """
from standards_tools import Finding, ToolResult

def harmless(**kwargs):
    return kwargs

def validate():
    findings = []
    maker, other = ToolResult.from_findings, harmless
    findings.append(Finding("PUBLIC_CODE", "visible"))
    return maker(tool="validate", version="1", findings=[])
"""
        self.assertTrue(self._has_alias_marker(source))

    def test_literal_mapping_selection_tracks_alias(self) -> None:
        source = """
from standards_tools import Finding, ToolResult

def harmless(**kwargs):
    return kwargs

def validate():
    findings = []
    maker = {
        "safe": harmless,
        "sink": ToolResult.from_findings,
    }["sink"]
    findings.append(Finding("PUBLIC_CODE", "visible"))
    return maker(tool="validate", version="1", findings=[])
"""
        self.assertTrue(self._has_alias_marker(source))

    def test_literal_loop_target_alias_is_tracked(self) -> None:
        source = """
from standards_tools import Finding, ToolResult

def validate():
    findings = []
    for maker in [ToolResult.from_findings]:
        pass
    findings.append(Finding("PUBLIC_CODE", "visible"))
    return maker(tool="validate", version="1", findings=[])
"""
        self.assertTrue(self._has_alias_marker(source))

    def test_match_capture_of_constructor_alias_is_tracked(self) -> None:
        source = """
from standards_tools import Finding, ToolResult

def validate():
    findings = []
    match ToolResult.from_findings:
        case maker:
            pass
    findings.append(Finding("PUBLIC_CODE", "visible"))
    return maker(tool="validate", version="1", findings=[])
"""
        self.assertTrue(self._has_alias_marker(source))


if __name__ == "__main__":
    unittest.main()
