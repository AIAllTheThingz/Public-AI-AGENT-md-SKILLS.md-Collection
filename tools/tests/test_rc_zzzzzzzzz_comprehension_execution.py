from __future__ import annotations

import ast
import copy
import json
import unittest
from dataclasses import dataclass
from typing import Any, Callable

import rc_finding_code_contracts_base as literal_base
import rc_parameterized_finding_codes_base as parameterized_base
import rc_reachability_semantics as reachability_semantics
import test_rc_extended_finding_reachability as extended_reachability
import test_rc_finding_reachability as basic_reachability
import test_rc_parameterized_finding_codes as parameterized_active
import test_rc_parameterized_finding_reachability as parameterized_reachability
import test_rc_zzzz_sink_rebinding_and_parameterized_multiplicity as multiplicity
import test_rc_zzzzzz_short_circuit_execution as short_circuit_execution
import test_rc_zzzzzzzz_guaranteed_nonempty_loop_execution as loop_execution  # noqa: F401


# Eager comprehensions have execution semantics that generic AST traversal does not
# preserve: an empty iterable skips filters/result expressions, a false filter skips
# the result, and a statically multi-item iterable may execute the result repeatedly.
# This layer composes after the BoolOp/IfExp/lexical/sink/loop overlays and patches
# their shared visitors rather than introducing another independent scanner.


@dataclass(frozen=True)
class _ExecutionCount:
    exact: int | None
    may_be_zero: bool

    @staticmethod
    def one() -> "_ExecutionCount":
        return _ExecutionCount(1, False)

    @staticmethod
    def zero() -> "_ExecutionCount":
        return _ExecutionCount(0, True)


@dataclass(frozen=True)
class _IterableInfo:
    exact: int | None
    definitely_nonempty: bool


_UNKNOWN_VALUE = object()


def _safe_unique_count(values: list[object]) -> int | None:
    try:
        return len(set(values))
    except (TypeError, ValueError):
        return None


def _constant_key(node: ast.AST) -> object:
    if isinstance(node, ast.Constant):
        try:
            hash(node.value)
        except TypeError:
            return _UNKNOWN_VALUE
        return node.value
    return _UNKNOWN_VALUE


def _static_int(
    node: ast.AST,
    local_bindings: dict[str, ast.AST],
    module_bindings: dict[str, ast.AST],
) -> int | None:
    value = short_circuit_execution._static_scalar(
        node,
        local_bindings,
        module_bindings,
    )
    return value if isinstance(value, int) and not isinstance(value, bool) else None


def _semantic_iterable_info(
    node: ast.AST,
    local_bindings: dict[str, ast.AST],
    module_bindings: dict[str, ast.AST],
    seen: set[str] | None = None,
) -> _IterableInfo:
    if isinstance(node, (ast.Tuple, ast.List)):
        if any(isinstance(item, ast.Starred) for item in node.elts):
            return _IterableInfo(
                None,
                any(not isinstance(item, ast.Starred) for item in node.elts),
            )
        return _IterableInfo(len(node.elts), bool(node.elts))

    if isinstance(node, ast.Set):
        if not node.elts:
            return _IterableInfo(0, False)
        values = [_constant_key(item) for item in node.elts]
        if all(value is not _UNKNOWN_VALUE for value in values):
            count = _safe_unique_count(values)
            if count is not None:
                return _IterableInfo(count, count > 0)
        return _IterableInfo(None, True)

    if isinstance(node, ast.Dict):
        if not node.keys:
            return _IterableInfo(0, False)
        concrete_keys = [key for key in node.keys if key is not None]
        if len(concrete_keys) == len(node.keys):
            values = [_constant_key(key) for key in concrete_keys]
            if all(value is not _UNKNOWN_VALUE for value in values):
                count = _safe_unique_count(values)
                if count is not None:
                    return _IterableInfo(count, count > 0)
        return _IterableInfo(None, bool(concrete_keys))

    if isinstance(node, ast.Constant):
        if isinstance(node.value, (str, bytes)):
            return _IterableInfo(len(node.value), bool(node.value))
        return _IterableInfo(None, False)

    if isinstance(node, ast.Name):
        active = set() if seen is None else set(seen)
        if node.id in active:
            return _IterableInfo(None, False)
        binding = local_bindings.get(node.id)
        if binding is None:
            binding = module_bindings.get(node.id)
        if binding is None or isinstance(
            binding,
            (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda, ast.ClassDef),
        ):
            return _IterableInfo(None, False)
        active.add(node.id)
        return _semantic_iterable_info(
            binding,
            local_bindings,
            module_bindings,
            active,
        )

    if (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and not node.keywords
    ):
        if node.func.id in {"list", "tuple", "set", "dict"} and not node.args:
            return _IterableInfo(0, False)
        if node.func.id == "range" and 1 <= len(node.args) <= 3:
            arguments = [
                _static_int(argument, local_bindings, module_bindings)
                for argument in node.args
            ]
            if all(argument is not None for argument in arguments):
                try:
                    count = len(range(*arguments))
                except (TypeError, ValueError):
                    return _IterableInfo(None, False)
                return _IterableInfo(count, count > 0)

    return _IterableInfo(None, False)


def _reachability_iterable_info(
    node: ast.AST,
    constants: dict[str, Any],
) -> _IterableInfo:
    if isinstance(node, ast.Name):
        value = constants.get(node.id, reachability_semantics.UNKNOWN)
        if isinstance(value, (str, bytes, tuple, list, set, frozenset, dict, range)):
            return _IterableInfo(len(value), len(value) > 0)

    if (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "range"
        and not node.keywords
        and 1 <= len(node.args) <= 3
    ):
        arguments: list[int] = []
        for argument in node.args:
            value = reachability_semantics.static_value(argument, constants)
            if not isinstance(value, int) or isinstance(value, bool):
                break
            arguments.append(value)
        else:
            try:
                count = len(range(*arguments))
            except (TypeError, ValueError):
                return _IterableInfo(None, False)
            return _IterableInfo(count, count > 0)

    return _semantic_iterable_info(node, {}, {})


def _combine_execution_count(
    current: _ExecutionCount,
    iterable: _IterableInfo,
) -> _ExecutionCount:
    if current.exact == 0:
        return current

    if iterable.exact is not None:
        if iterable.exact == 0:
            return _ExecutionCount.zero()
        if current.exact is not None:
            value = current.exact * iterable.exact
            return _ExecutionCount(value, value == 0)
        return _ExecutionCount(None, current.may_be_zero)

    if iterable.definitely_nonempty:
        return _ExecutionCount(None, current.may_be_zero)

    return _ExecutionCount(None, True)


def _after_unknown_filter(current: _ExecutionCount) -> _ExecutionCount:
    if current.exact == 0:
        return current
    return _ExecutionCount(None, True)


def _execution_marker(
    kind: str,
    phase: str,
    execution: _ExecutionCount,
) -> str | None:
    if execution.exact == 0:
        return None
    if execution.exact == 1 and not execution.may_be_zero:
        return ""
    if execution.exact is not None:
        return f"comprehension:{kind}:{phase}:count:{execution.exact}"
    if execution.may_be_zero:
        return f"comprehension:{kind}:{phase}:maybe-executed"
    return f"comprehension:{kind}:{phase}:nonempty-unknown-count"


def _literal_with_context(
    visitor,
    marker: str,
    expression: ast.AST,
    callback: Callable[[], None],
) -> None:
    visitor.context.append(marker)
    visitor.context_nodes.append(expression)
    try:
        callback()
    finally:
        visitor.context_nodes.pop()
        visitor.context.pop()


def _parameterized_with_context(
    visitor,
    marker: str,
    expression: ast.AST,
    callback: Callable[[], None],
) -> None:
    visitor.context_nodes.append((marker, expression))
    try:
        callback()
    finally:
        visitor.context_nodes.pop()


def _run_under_execution(
    *,
    kind: str,
    phase: str,
    execution: _ExecutionCount,
    expression: ast.AST,
    callback: Callable[[], None],
    with_context: Callable[[str, ast.AST, Callable[[], None]], None] | None,
) -> None:
    marker = _execution_marker(kind, phase, execution)
    if marker is None:
        return
    if marker == "" or with_context is None:
        callback()
        return
    with_context(marker, expression, callback)


def _visit_comprehension(
    visitor,
    *,
    kind: str,
    generators: list[ast.comprehension],
    result_expressions: list[ast.AST],
    truth: Callable[[ast.AST], bool | None],
    iterable_info: Callable[[ast.AST], _IterableInfo],
    with_context: Callable[[str, ast.AST, Callable[[], None]], None] | None,
) -> None:
    def process_generator(index: int, execution: _ExecutionCount) -> None:
        if execution.exact == 0:
            return

        if index >= len(generators):
            marker_expression = (
                result_expressions[0]
                if result_expressions
                else ast.Constant(value="comprehension-result")
            )

            def visit_result() -> None:
                for expression in result_expressions:
                    visitor.visit(expression)

            _run_under_execution(
                kind=kind,
                phase="result",
                execution=execution,
                expression=marker_expression,
                callback=visit_result,
                with_context=with_context,
            )
            return

        generator = generators[index]

        _run_under_execution(
            kind=kind,
            phase=f"generator:{index}:iter",
            execution=execution,
            expression=generator.iter,
            callback=lambda: visitor.visit(generator.iter),
            with_context=with_context,
        )

        if generator.is_async:
            next_execution = _ExecutionCount(None, True)
        else:
            next_execution = _combine_execution_count(
                execution,
                iterable_info(generator.iter),
            )

        if next_execution.exact == 0:
            return

        def process_filter(filter_index: int, current: _ExecutionCount) -> None:
            if current.exact == 0:
                return
            if filter_index >= len(generator.ifs):
                process_generator(index + 1, current)
                return

            condition = generator.ifs[filter_index]
            _run_under_execution(
                kind=kind,
                phase=f"generator:{index}:filter:{filter_index}",
                execution=current,
                expression=condition,
                callback=lambda: visitor.visit(condition),
                with_context=with_context,
            )

            condition_truth = truth(condition)
            if condition_truth is False:
                return
            if condition_truth is True:
                process_filter(filter_index + 1, current)
                return

            narrowed = _after_unknown_filter(current)
            marker = f"comprehension:{kind}:filter:{index}:{filter_index}:true"

            if with_context is None:
                process_filter(filter_index + 1, narrowed)
            else:
                with_context(
                    marker,
                    condition,
                    lambda: process_filter(filter_index + 1, narrowed),
                )

        process_filter(0, next_execution)

    process_generator(0, _ExecutionCount.one())


def _literal_visit_listcomp(self, node: ast.ListComp) -> None:
    _visit_comprehension(
        self,
        kind="list",
        generators=node.generators,
        result_expressions=[node.elt],
        truth=lambda expression: short_circuit_execution._semantic_truth(
            expression,
            self.local_bindings,
            self.module_definitions,
        ),
        iterable_info=lambda expression: _semantic_iterable_info(
            expression,
            self.local_bindings,
            self.module_definitions,
        ),
        with_context=lambda marker, expression, callback: _literal_with_context(
            self, marker, expression, callback
        ),
    )


def _literal_visit_setcomp(self, node: ast.SetComp) -> None:
    _visit_comprehension(
        self,
        kind="set",
        generators=node.generators,
        result_expressions=[node.elt],
        truth=lambda expression: short_circuit_execution._semantic_truth(
            expression,
            self.local_bindings,
            self.module_definitions,
        ),
        iterable_info=lambda expression: _semantic_iterable_info(
            expression,
            self.local_bindings,
            self.module_definitions,
        ),
        with_context=lambda marker, expression, callback: _literal_with_context(
            self, marker, expression, callback
        ),
    )


def _literal_visit_dictcomp(self, node: ast.DictComp) -> None:
    _visit_comprehension(
        self,
        kind="dict",
        generators=node.generators,
        result_expressions=[node.key, node.value],
        truth=lambda expression: short_circuit_execution._semantic_truth(
            expression,
            self.local_bindings,
            self.module_definitions,
        ),
        iterable_info=lambda expression: _semantic_iterable_info(
            expression,
            self.local_bindings,
            self.module_definitions,
        ),
        with_context=lambda marker, expression, callback: _literal_with_context(
            self, marker, expression, callback
        ),
    )


literal_base.FindingSignatureVisitor.visit_ListComp = _literal_visit_listcomp
literal_base.FindingSignatureVisitor.visit_SetComp = _literal_visit_setcomp
literal_base.FindingSignatureVisitor.visit_DictComp = _literal_visit_dictcomp


def _patch_reachability_comprehensions(visitor_type) -> None:
    def visit_listcomp(self, node: ast.ListComp) -> None:
        _visit_comprehension(
            self,
            kind="list",
            generators=node.generators,
            result_expressions=[node.elt],
            truth=lambda expression: reachability_semantics.static_truth(
                expression, self.constants
            ),
            iterable_info=lambda expression: _reachability_iterable_info(
                expression, self.constants
            ),
            with_context=None,
        )

    def visit_setcomp(self, node: ast.SetComp) -> None:
        _visit_comprehension(
            self,
            kind="set",
            generators=node.generators,
            result_expressions=[node.elt],
            truth=lambda expression: reachability_semantics.static_truth(
                expression, self.constants
            ),
            iterable_info=lambda expression: _reachability_iterable_info(
                expression, self.constants
            ),
            with_context=None,
        )

    def visit_dictcomp(self, node: ast.DictComp) -> None:
        _visit_comprehension(
            self,
            kind="dict",
            generators=node.generators,
            result_expressions=[node.key, node.value],
            truth=lambda expression: reachability_semantics.static_truth(
                expression, self.constants
            ),
            iterable_info=lambda expression: _reachability_iterable_info(
                expression, self.constants
            ),
            with_context=None,
        )

    visitor_type.visit_ListComp = visit_listcomp
    visitor_type.visit_SetComp = visit_setcomp
    visitor_type.visit_DictComp = visit_dictcomp


_patch_reachability_comprehensions(basic_reachability.ReachableFindingVisitor)
_patch_reachability_comprehensions(extended_reachability.ExtendedReachableFindingVisitor)


_parameterized_visitor = parameterized_active.BranchAwareParameterizedCallSiteVisitor


def _parameterized_visit_listcomp(self, node: ast.ListComp) -> None:
    _visit_comprehension(
        self,
        kind="list",
        generators=node.generators,
        result_expressions=[node.elt],
        truth=lambda expression: short_circuit_execution._semantic_truth(
            expression, self.local_bindings, self.module_values
        ),
        iterable_info=lambda expression: _semantic_iterable_info(
            expression, self.local_bindings, self.module_values
        ),
        with_context=lambda marker, expression, callback: _parameterized_with_context(
            self, marker, expression, callback
        ),
    )


def _parameterized_visit_setcomp(self, node: ast.SetComp) -> None:
    _visit_comprehension(
        self,
        kind="set",
        generators=node.generators,
        result_expressions=[node.elt],
        truth=lambda expression: short_circuit_execution._semantic_truth(
            expression, self.local_bindings, self.module_values
        ),
        iterable_info=lambda expression: _semantic_iterable_info(
            expression, self.local_bindings, self.module_values
        ),
        with_context=lambda marker, expression, callback: _parameterized_with_context(
            self, marker, expression, callback
        ),
    )


def _parameterized_visit_dictcomp(self, node: ast.DictComp) -> None:
    _visit_comprehension(
        self,
        kind="dict",
        generators=node.generators,
        result_expressions=[node.key, node.value],
        truth=lambda expression: short_circuit_execution._semantic_truth(
            expression, self.local_bindings, self.module_values
        ),
        iterable_info=lambda expression: _semantic_iterable_info(
            expression, self.local_bindings, self.module_values
        ),
        with_context=lambda marker, expression, callback: _parameterized_with_context(
            self, marker, expression, callback
        ),
    )


_parameterized_visitor.visit_ListComp = _parameterized_visit_listcomp
_parameterized_visitor.visit_SetComp = _parameterized_visit_setcomp
_parameterized_visitor.visit_DictComp = _parameterized_visit_dictcomp
parameterized_active.base.ParameterizedCallSiteVisitor = _parameterized_visitor


def _patch_reachable_parameterized_comprehensions(visitor_type) -> None:
    def with_context(self, marker, expression, callback):
        self.context_nodes.append((marker, expression))
        try:
            callback()
        finally:
            self.context_nodes.pop()

    def visit_listcomp(self, node: ast.ListComp) -> None:
        _visit_comprehension(
            self,
            kind="list",
            generators=node.generators,
            result_expressions=[node.elt],
            truth=lambda expression: reachability_semantics.static_truth(
                expression, self.constants
            ),
            iterable_info=lambda expression: _reachability_iterable_info(
                expression, self.constants
            ),
            with_context=lambda marker, expression, callback: with_context(
                self, marker, expression, callback
            ),
        )

    def visit_setcomp(self, node: ast.SetComp) -> None:
        _visit_comprehension(
            self,
            kind="set",
            generators=node.generators,
            result_expressions=[node.elt],
            truth=lambda expression: reachability_semantics.static_truth(
                expression, self.constants
            ),
            iterable_info=lambda expression: _reachability_iterable_info(
                expression, self.constants
            ),
            with_context=lambda marker, expression, callback: with_context(
                self, marker, expression, callback
            ),
        )

    def visit_dictcomp(self, node: ast.DictComp) -> None:
        _visit_comprehension(
            self,
            kind="dict",
            generators=node.generators,
            result_expressions=[node.key, node.value],
            truth=lambda expression: reachability_semantics.static_truth(
                expression, self.constants
            ),
            iterable_info=lambda expression: _reachability_iterable_info(
                expression, self.constants
            ),
            with_context=lambda marker, expression, callback: with_context(
                self, marker, expression, callback
            ),
        )

    visitor_type.visit_ListComp = visit_listcomp
    visitor_type.visit_SetComp = visit_setcomp
    visitor_type.visit_DictComp = visit_dictcomp


_patch_reachable_parameterized_comprehensions(
    parameterized_reachability.ReachableParameterizedCallSiteVisitor
)


# Helper discovery already has execution-aware lambda/generator handling. Preserve
# that implementation and present it with a copy of the AST in which only
# definitely dead eager-comprehension result paths have been pruned.
_previous_parameterized_finding_parameters = parameterized_active.parameterized_finding_parameters


class _PruneDeadEagerComprehensions(ast.NodeTransformer):
    def _prune(
        self,
        node: ast.ListComp | ast.SetComp | ast.DictComp,
    ) -> ast.AST:
        node = self.generic_visit(node)
        prefix: list[ast.AST] = []
        execution = _ExecutionCount.one()
        dead = False

        for generator in node.generators:
            if execution.exact == 0:
                dead = True
                break

            prefix.append(generator.iter)
            if generator.is_async:
                execution = _ExecutionCount(None, True)
            else:
                execution = _combine_execution_count(
                    execution,
                    _semantic_iterable_info(generator.iter, {}, {}),
                )

            if execution.exact == 0:
                dead = True
                break

            for condition in generator.ifs:
                prefix.append(condition)
                condition_truth = short_circuit_execution._semantic_truth(
                    condition, {}, {}
                )
                if condition_truth is False:
                    dead = True
                    execution = _ExecutionCount.zero()
                    break
                if condition_truth is None:
                    execution = _after_unknown_filter(execution)

            if dead:
                break

        if not dead:
            return node

        replacement = ast.Tuple(
            elts=prefix or [ast.Constant(value=None)],
            ctx=ast.Load(),
        )
        return ast.copy_location(replacement, node)

    def visit_ListComp(self, node: ast.ListComp) -> ast.AST:
        return self._prune(node)

    def visit_SetComp(self, node: ast.SetComp) -> ast.AST:
        return self._prune(node)

    def visit_DictComp(self, node: ast.DictComp) -> ast.AST:
        return self._prune(node)


def _comprehension_aware_parameterized_finding_parameters(
    tree: ast.Module,
) -> dict[str, set[str]]:
    transformed = _PruneDeadEagerComprehensions().visit(copy.deepcopy(tree))
    ast.fix_missing_locations(transformed)
    return _previous_parameterized_finding_parameters(transformed)


parameterized_base.parameterized_finding_parameters = (
    _comprehension_aware_parameterized_finding_parameters
)
parameterized_active.base.parameterized_finding_parameters = (
    _comprehension_aware_parameterized_finding_parameters
)
parameterized_active.parameterized_finding_parameters = (
    _comprehension_aware_parameterized_finding_parameters
)


class ReleaseCandidateComprehensionExecutionTests(unittest.TestCase):
    def test_empty_eager_comprehensions_hide_literal_finding(self):
        sources = {
            "list": '''
def validate(findings):
    [findings.append(Finding("PUBLIC_CODE", "hidden")) for _ in ()]
''',
            "set": '''
def validate(findings):
    {findings.append(Finding("PUBLIC_CODE", "hidden")) for _ in []}
''',
            "dict": '''
def validate(findings):
    {_: findings.append(Finding("PUBLIC_CODE", "hidden")) for _ in range(0)}
''',
        }
        for name, source in sources.items():
            with self.subTest(name=name):
                self.assertNotIn(
                    "PUBLIC_CODE",
                    literal_base.finding_semantic_signatures(source),
                )
                self.assertEqual(
                    extended_reachability.reachable_contracts(source, "sample.py"),
                    {},
                )

    def test_false_comprehension_filter_hides_literal_finding(self):
        source = '''
def validate(findings):
    [findings.append(Finding("PUBLIC_CODE", "hidden")) for _ in (1,) if False]
'''
        self.assertNotIn(
            "PUBLIC_CODE",
            literal_base.finding_semantic_signatures(source),
        )
        self.assertEqual(
            extended_reachability.reachable_contracts(source, "sample.py"),
            {},
        )

    def test_single_static_iteration_preserves_literal_execution_identity(self):
        direct = '''
def validate(findings):
    findings.append(Finding("PUBLIC_CODE", "visible"))
'''
        comprehension = '''
def validate(findings):
    [findings.append(Finding("PUBLIC_CODE", "visible")) for _ in (1,)]
'''
        self.assertEqual(
            literal_base.finding_semantic_signatures(direct),
            literal_base.finding_semantic_signatures(comprehension),
        )

    def test_multiple_static_iterations_change_literal_semantic_identity(self):
        source = '''
def validate(findings):
    [findings.append(Finding("PUBLIC_CODE", "visible")) for _ in (1, 2)]
'''
        signatures = literal_base.finding_semantic_signatures(source)
        payload = json.loads(signatures["PUBLIC_CODE"][0])
        self.assertTrue(
            any(
                marker == "comprehension:list:result:count:2"
                for marker in payload["context"]
            ),
            payload,
        )

    def test_unknown_iterable_adds_literal_maybe_execution_identity(self):
        source = '''
def validate(items, findings):
    [findings.append(Finding("PUBLIC_CODE", "visible")) for _ in items]
'''
        signatures = literal_base.finding_semantic_signatures(source)
        payload = json.loads(signatures["PUBLIC_CODE"][0])
        self.assertTrue(
            any(
                marker == "comprehension:list:result:maybe-executed"
                for marker in payload["context"]
            ),
            payload,
        )

    def test_empty_and_false_filter_hide_parameterized_call(self):
        template = '''
def read_text(path, findings, code):
    Finding(code, "decode failed", path="sample")
def validate(root, findings):
    {expression}
'''
        expressions = {
            "empty": (
                '[read_text(root / "LICENSE", findings, "LICENSE_ENCODING") '
                'for _ in ()]'
            ),
            "false-filter": (
                '[read_text(root / "LICENSE", findings, "LICENSE_ENCODING") '
                'for _ in (1,) if False]'
            ),
        }
        for name, expression in expressions.items():
            source = template.format(expression=expression)
            with self.subTest(name=name):
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

    def test_false_filter_inside_parameterized_helper_removes_public_call_contract(self):
        source = '''
def read_text(path, findings, code):
    [Finding(code, "decode failed", path="sample") for _ in (1,) if False]
def validate(root, findings):
    read_text(root / "LICENSE", findings, "LICENSE_ENCODING")
'''
        self.assertEqual(
            parameterized_active.parameterized_finding_contracts(
                source, "sample.py"
            ),
            set(),
        )

    def test_unknown_parameterized_filter_adds_branch_identity(self):
        source = '''
def read_text(path, findings, code):
    Finding(code, "decode failed", path="sample")
def validate(flag, root, findings):
    [read_text(root / "LICENSE", findings, "LICENSE_ENCODING") for _ in (1,) if flag]
'''
        contracts = parameterized_active.parameterized_finding_contracts(
            source, "sample.py"
        )
        payload = json.loads(next(iter(contracts)))
        self.assertTrue(
            any(
                item["branch"] == "comprehension:list:filter:0:0:true"
                for item in payload["context"]
            ),
            payload,
        )

    def test_multiple_parameterized_iterations_encode_multiplicity(self):
        source = '''
def read_text(path, findings, code):
    Finding(code, "decode failed", path="sample")
def validate(root, findings):
    [read_text(root / "LICENSE", findings, "LICENSE_ENCODING") for _ in (1, 2)]
'''
        contracts = parameterized_active.parameterized_finding_contracts(
            source, "sample.py"
        )
        payload = json.loads(next(iter(contracts)))
        self.assertTrue(
            any(
                item["branch"] == "comprehension:list:result:count:2"
                for item in payload["context"]
            ),
            payload,
        )

        counted = multiplicity._reachable_parameterized_counts(source, "sample.py")
        self.assertEqual(sum(counted.values()), 1)
        counted_payload = json.loads(next(iter(counted)))
        self.assertTrue(
            any(
                item["branch"] == "comprehension:list:result:count:2"
                for item in counted_payload["context"]
            ),
            counted_payload,
        )


if __name__ == "__main__":
    unittest.main()
