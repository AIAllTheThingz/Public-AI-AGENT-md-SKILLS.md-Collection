from __future__ import annotations

import ast
import json
import unittest

import rc_finding_code_contracts_base as literal_base
import test_rc_alias_and_generator_execution as generator_execution
import test_rc_approved_helper_and_deferred_execution as deferred_execution
import test_rc_extended_finding_reachability as extended_reachability
import test_rc_finding_reachability as basic_reachability
import test_rc_parameterized_finding_codes as parameterized_active
import test_rc_parameterized_finding_reachability as parameterized_reachability
import test_rc_zzz_finding_emission_sink as sink_execution
import test_rc_zzzzzzzzz_comprehension_execution as comprehension_execution
import test_rc_zzzzzzzzzzzzzzzzzzzzzzzzzzzzzz_rendered_markdown_and_attribute_prerequisites as latest_composition
import test_rc_zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz_dynamic_operator_and_archive_root_isolation as _latest_layer  # noqa: F401


# This final composition layer closes two execution-model gaps that can otherwise
# hide a published Finding without changing the compatibility inventory:
#
# 1. The left-to-right call evaluator superseded older deferred lambda/generator
#    visit_Call hooks. Preserve the latest argument-prerequisite behavior while
#    explicitly restoring invoked lambdas and eager generator consumers.
# 2. Eager comprehensions bind each yielded value to generator.target before any
#    filter or result expression runs. Destructuring/complex targets can fail at
#    that point and their structure is part of the execution contract.


# ---------------------------------------------------------------------------
# Final call composition: lambdas and eager generator consumers
# ---------------------------------------------------------------------------


def _reachable_lambda_binding(visitor, node: ast.Call) -> ast.Lambda | None:
    deferred = deferred_execution._lambda_binding_for_call(visitor, node)
    if deferred is not None:
        return deferred
    if isinstance(node.func, ast.Name):
        binding = getattr(visitor, "_deferred_lambdas", {}).get(node.func.id)
        if isinstance(binding, ast.Lambda):
            return binding
    return None


def _invoke_reachable_lambda(visitor, node: ast.Call) -> bool:
    deferred = _reachable_lambda_binding(visitor, node)
    if deferred is None:
        return False

    if isinstance(node.func, ast.Lambda):
        visitor.visit(node.func)
    for argument in node.args:
        visitor.visit(argument)
    for keyword in node.keywords:
        visitor.visit(keyword.value)

    active = getattr(visitor, "_active_lambda_bodies", set())
    marker = id(deferred)
    if marker in active:
        return True

    previous_active = active
    visitor._active_lambda_bodies = set(active) | {marker}
    try:
        visitor.visit(deferred.body)
    finally:
        visitor._active_lambda_bodies = previous_active
    return True


# The rendered/composition layer resolves this helper by module-global name at
# call time, so replacing it repairs every reachability visitor it composed.
latest_composition._invoke_reachable_lambda = _invoke_reachable_lambda


def _eager_generator_bodies(visitor, node: ast.Call) -> list[ast.GeneratorExp]:
    if (
        generator_execution._call_consumer_name(node)
        not in generator_execution._EAGER_GENERATOR_CONSUMERS
    ):
        return []

    result: list[ast.GeneratorExp] = []
    for argument in node.args:
        generator = generator_execution._generator_from_expression(visitor, argument)
        if generator is not None:
            result.append(generator)
    return result


def _visit_literal_generator_bodies(visitor, node: ast.Call) -> None:
    for generator in _eager_generator_bodies(visitor, node):
        marker = id(generator)
        active = getattr(visitor, "_active_generator_bodies", set())
        if marker in active:
            continue
        previous_active = active
        visitor._active_generator_bodies = set(active) | {marker}
        visitor.context.append("generator:iterated")
        try:
            generator_execution._visit_generator_body(visitor, generator)
        finally:
            visitor.context.pop()
            visitor._active_generator_bodies = previous_active


def _visit_parameterized_generator_bodies(visitor, node: ast.Call) -> None:
    for generator in _eager_generator_bodies(visitor, node):
        marker = id(generator)
        active = getattr(visitor, "_active_generator_bodies", set())
        if marker in active:
            continue
        previous_active = active
        visitor._active_generator_bodies = set(active) | {marker}
        visitor.context_nodes.append(
            ("generator:iterated", ast.Constant(value="generator"))
        )
        try:
            generator_execution._visit_generator_body(visitor, generator)
        finally:
            visitor.context_nodes.pop()
            visitor._active_generator_bodies = previous_active


def _visit_reachable_generator_bodies(visitor, node: ast.Call) -> None:
    for generator in _eager_generator_bodies(visitor, node):
        marker = id(generator)
        active = getattr(visitor, "_active_generator_bodies", set())
        if marker in active:
            continue
        previous_active = active
        visitor._active_generator_bodies = set(active) | {marker}
        try:
            generator_execution._visit_generator_body(visitor, generator)
        finally:
            visitor._active_generator_bodies = previous_active


_previous_literal_current = latest_composition._current_literal_visit_call
_previous_sink_current = latest_composition._current_sink_visit_call
_previous_parameterized_current = latest_composition._current_parameterized_visit_call
_previous_reachable_parameterized_current = (
    latest_composition._current_reachable_parameterized_visit_call
)
_previous_counting_current = latest_composition._current_counting_visit_call
_previous_counting_reachable_current = (
    latest_composition._current_counting_reachable_visit_call
)


def _literal_current_with_generators(self, node: ast.Call) -> None:
    _previous_literal_current(self, node)
    _visit_literal_generator_bodies(self, node)


def _sink_current_with_generators(self, node: ast.Call) -> None:
    _previous_sink_current(self, node)
    _visit_literal_generator_bodies(self, node)


def _parameterized_current_with_generators(self, node: ast.Call) -> None:
    _previous_parameterized_current(self, node)
    _visit_parameterized_generator_bodies(self, node)


def _reachable_parameterized_current_with_generators(
    self, node: ast.Call
) -> None:
    _previous_reachable_parameterized_current(self, node)
    _visit_parameterized_generator_bodies(self, node)


def _counting_current_with_generators(self, node: ast.Call) -> None:
    _previous_counting_current(self, node)
    _visit_parameterized_generator_bodies(self, node)


def _counting_reachable_current_with_generators(self, node: ast.Call) -> None:
    _previous_counting_reachable_current(self, node)
    _visit_parameterized_generator_bodies(self, node)


latest_composition._current_literal_visit_call = _literal_current_with_generators
latest_composition._current_sink_visit_call = _sink_current_with_generators
latest_composition._current_parameterized_visit_call = (
    _parameterized_current_with_generators
)
latest_composition._current_reachable_parameterized_visit_call = (
    _reachable_parameterized_current_with_generators
)
latest_composition._current_counting_visit_call = _counting_current_with_generators
latest_composition._current_counting_reachable_visit_call = (
    _counting_reachable_current_with_generators
)


def _compose_reachable_generator_calls(visitor_type) -> None:
    current = visitor_type.visit_Call

    def visit_call(self, node: ast.Call) -> None:
        current(self, node)
        _visit_reachable_generator_bodies(self, node)

    visitor_type.visit_Call = visit_call


for _visitor_type in (
    basic_reachability.ReachableFindingVisitor,
    extended_reachability.ExtendedReachableFindingVisitor,
    sink_execution.SinkAwareReachableFindingVisitor,
):
    _compose_reachable_generator_calls(_visitor_type)


# ---------------------------------------------------------------------------
# Comprehension target binding
# ---------------------------------------------------------------------------

_SAFE = "safe"
_RAISES = "raises"
_UNKNOWN = "unknown"
_NON_ITERABLE = object()


def _target_pattern(target: ast.AST) -> str:
    if isinstance(target, ast.Name):
        return "name"
    if isinstance(target, ast.Starred):
        return f"starred({_target_pattern(target.value)})"
    if isinstance(target, ast.Tuple):
        return "tuple(" + ",".join(_target_pattern(item) for item in target.elts) + ")"
    if isinstance(target, ast.List):
        return "list(" + ",".join(_target_pattern(item) for item in target.elts) + ")"
    if isinstance(target, ast.Attribute):
        return "attribute"
    if isinstance(target, ast.Subscript):
        return "subscript"
    return type(target).__name__.lower()


def _resolve_binding_source(
    visitor,
    node: ast.AST,
    seen: set[str] | None = None,
):
    if not isinstance(node, ast.Name) or visitor is None:
        return node

    active = set() if seen is None else set(seen)
    if node.id in active:
        return node
    active.add(node.id)

    for attribute in ("local_bindings", "module_definitions", "module_values"):
        bindings = getattr(visitor, attribute, {})
        binding = bindings.get(node.id)
        if binding is None or isinstance(
            binding,
            (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda, ast.ClassDef),
        ):
            continue
        if isinstance(binding, ast.AST):
            return _resolve_binding_source(visitor, binding, active)
        return binding

    constants = getattr(visitor, "constants", {})
    if node.id in constants:
        return constants[node.id]
    return node


def _literal_range_elements(node: ast.Call) -> list[int] | None:
    if (
        not isinstance(node.func, ast.Name)
        or node.func.id != "range"
        or node.keywords
        or not 1 <= len(node.args) <= 3
    ):
        return None
    values: list[int] = []
    for argument in node.args:
        if (
            not isinstance(argument, ast.Constant)
            or not isinstance(argument.value, int)
            or isinstance(argument.value, bool)
        ):
            return None
        values.append(argument.value)
    try:
        return list(range(*values))
    except (TypeError, ValueError):
        return None


def _known_iterable_elements(visitor, node: ast.AST):
    source = _resolve_binding_source(visitor, node)

    if isinstance(source, (ast.Tuple, ast.List)):
        if any(isinstance(item, ast.Starred) for item in source.elts):
            return None
        return list(source.elts), True

    if isinstance(source, ast.Set):
        if any(isinstance(item, ast.Starred) for item in source.elts):
            return None
        return list(source.elts), False

    if isinstance(source, ast.Dict):
        if any(key is None for key in source.keys):
            return None
        return [key for key in source.keys if key is not None], True

    if isinstance(source, ast.Call):
        values = _literal_range_elements(source)
        if values is not None:
            return values, True
        return None

    if isinstance(source, ast.Constant):
        source = source.value

    if isinstance(source, dict):
        return list(source.keys()), True
    if isinstance(source, (list, tuple, range, str, bytes)):
        return list(source), True
    if isinstance(source, (set, frozenset)):
        return list(source), False
    return None


def _sequence_for_unpack(visitor, value):
    if isinstance(value, ast.AST):
        value = _resolve_binding_source(visitor, value)

    if isinstance(value, (ast.Tuple, ast.List)):
        if any(isinstance(item, ast.Starred) for item in value.elts):
            return None
        return list(value.elts)

    if isinstance(value, ast.Set):
        if any(isinstance(item, ast.Starred) for item in value.elts):
            return None
        return list(value.elts)

    if isinstance(value, ast.Dict):
        if any(key is None for key in value.keys):
            return None
        return [key for key in value.keys if key is not None]

    if isinstance(value, ast.Constant):
        value = value.value

    if isinstance(value, dict):
        return list(value.keys())
    if isinstance(value, (list, tuple, range, str, bytes, set, frozenset)):
        return list(value)
    if isinstance(value, (int, float, complex, bool, type(None))):
        return _NON_ITERABLE
    if isinstance(value, ast.AST):
        return None
    return None


def _target_binding_state(visitor, target: ast.AST, value) -> str:
    if isinstance(target, ast.Name):
        return _SAFE

    if isinstance(target, ast.Attribute):
        return _UNKNOWN

    if isinstance(target, ast.Subscript):
        return _UNKNOWN

    if isinstance(target, ast.Starred):
        if isinstance(target.value, ast.Name):
            return _SAFE
        if isinstance(target.value, (ast.Attribute, ast.Subscript)):
            return _UNKNOWN
        return _target_binding_state(visitor, target.value, [])

    if not isinstance(target, (ast.Tuple, ast.List)):
        return _UNKNOWN

    values = _sequence_for_unpack(visitor, value)
    if values is _NON_ITERABLE:
        return _RAISES
    if values is None:
        return _UNKNOWN

    starred = [
        index
        for index, item in enumerate(target.elts)
        if isinstance(item, ast.Starred)
    ]
    if len(starred) > 1:
        return _RAISES

    states: list[str] = []
    if not starred:
        if len(values) != len(target.elts):
            return _RAISES
        states = [
            _target_binding_state(visitor, item, current)
            for item, current in zip(target.elts, values)
        ]
    else:
        star_index = starred[0]
        minimum = len(target.elts) - 1
        if len(values) < minimum:
            return _RAISES

        before = target.elts[:star_index]
        after = target.elts[star_index + 1 :]
        before_values = values[:star_index]
        after_values = values[len(values) - len(after) :] if after else []

        states.extend(
            _target_binding_state(visitor, item, current)
            for item, current in zip(before, before_values)
        )

        starred_target = target.elts[star_index]
        assert isinstance(starred_target, ast.Starred)
        states.append(
            _target_binding_state(
                visitor,
                starred_target,
                values[star_index : len(values) - len(after) if after else len(values)],
            )
        )
        states.extend(
            _target_binding_state(visitor, item, current)
            for item, current in zip(after, after_values)
        )

    if _RAISES in states:
        return _RAISES
    if _UNKNOWN in states:
        return _UNKNOWN
    return _SAFE


def _target_binding_execution(
    visitor,
    target: ast.AST,
    iterable: ast.AST,
    outer: comprehension_execution._ExecutionCount,
    after_iterable: comprehension_execution._ExecutionCount,
):
    if isinstance(target, ast.Name) or after_iterable.exact == 0:
        return after_iterable, None

    pattern = _target_pattern(target)
    known = _known_iterable_elements(visitor, iterable)
    if known is None:
        return (
            comprehension_execution._ExecutionCount(None, True),
            f"target:{pattern}:maybe-fails",
        )

    elements, ordered = known
    if not elements:
        return after_iterable, None

    states = [
        _target_binding_state(visitor, target, element)
        for element in elements
    ]

    if all(state == _SAFE for state in states):
        return after_iterable, f"target:{pattern}:safe"

    if ordered:
        for index, state in enumerate(states):
            if state == _UNKNOWN:
                return (
                    comprehension_execution._ExecutionCount(None, True),
                    f"target:{pattern}:maybe-fails",
                )
            if state == _RAISES:
                if index == 0 and not outer.may_be_zero:
                    return (
                        comprehension_execution._ExecutionCount.zero(),
                        f"target:{pattern}:raises-before-result",
                    )
                if index > 0 and not outer.may_be_zero:
                    return (
                        comprehension_execution._ExecutionCount(index, False),
                        f"target:{pattern}:raises-after:{index}",
                    )
                return (
                    comprehension_execution._ExecutionCount(None, True),
                    f"target:{pattern}:maybe-fails",
                )

    if all(state == _RAISES for state in states) and not outer.may_be_zero:
        return (
            comprehension_execution._ExecutionCount.zero(),
            f"target:{pattern}:raises-before-result",
        )

    return (
        comprehension_execution._ExecutionCount(None, True),
        f"target:{pattern}:maybe-fails",
    )


def _target_context_expression(marker: str) -> ast.Constant:
    return ast.Constant(value=marker)


def _visit_comprehension_with_target_binding(
    visitor,
    *,
    kind: str,
    generators: list[ast.comprehension],
    result_expressions: list[ast.AST],
    truth,
    iterable_info,
    with_context,
) -> None:
    def process_generator(
        index: int,
        execution: comprehension_execution._ExecutionCount,
    ) -> None:
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

            comprehension_execution._run_under_execution(
                kind=kind,
                phase="result",
                execution=execution,
                expression=marker_expression,
                callback=visit_result,
                with_context=with_context,
            )
            return

        generator = generators[index]

        comprehension_execution._run_under_execution(
            kind=kind,
            phase=f"generator:{index}:iter",
            execution=execution,
            expression=generator.iter,
            callback=lambda: visitor.visit(generator.iter),
            with_context=with_context,
        )

        if generator.is_async:
            after_iterable = comprehension_execution._ExecutionCount(None, True)
        else:
            after_iterable = comprehension_execution._combine_execution_count(
                execution,
                iterable_info(generator.iter),
            )

        if after_iterable.exact == 0:
            return

        bound_execution, target_marker = _target_binding_execution(
            visitor,
            generator.target,
            generator.iter,
            execution,
            after_iterable,
        )
        if bound_execution.exact == 0:
            return

        def process_filter(
            filter_index: int,
            current: comprehension_execution._ExecutionCount,
        ) -> None:
            if current.exact == 0:
                return
            if filter_index >= len(generator.ifs):
                process_generator(index + 1, current)
                return

            condition = generator.ifs[filter_index]
            comprehension_execution._run_under_execution(
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

            narrowed = comprehension_execution._after_unknown_filter(current)
            marker = f"comprehension:{kind}:filter:{index}:{filter_index}:true"

            if with_context is None:
                process_filter(filter_index + 1, narrowed)
            else:
                with_context(
                    marker,
                    condition,
                    lambda: process_filter(filter_index + 1, narrowed),
                )

        if target_marker is None or with_context is None:
            process_filter(0, bound_execution)
        else:
            marker = f"comprehension:{kind}:generator:{index}:{target_marker}"
            with_context(
                marker,
                _target_context_expression(marker),
                lambda: process_filter(0, bound_execution),
            )

    process_generator(0, comprehension_execution._ExecutionCount.one())


# Every comprehension visitor in the earlier layer resolves this global at call
# time. Replacing it updates literal, sink-aware, reachability, parameterized,
# and counting scans without cloning each visitor again.
comprehension_execution._visit_comprehension = (
    _visit_comprehension_with_target_binding
)


def _target_aware_prune(
    self,
    node: ast.ListComp | ast.SetComp | ast.DictComp,
) -> ast.AST:
    node = self.generic_visit(node)
    prefix: list[ast.AST] = []
    execution = comprehension_execution._ExecutionCount.one()
    dead = False

    for generator in node.generators:
        if execution.exact == 0:
            dead = True
            break

        prefix.append(generator.iter)
        before = execution
        if generator.is_async:
            execution = comprehension_execution._ExecutionCount(None, True)
        else:
            execution = comprehension_execution._combine_execution_count(
                execution,
                comprehension_execution._semantic_iterable_info(
                    generator.iter, {}, {}
                ),
            )

        if execution.exact == 0:
            dead = True
            break

        execution, _ = _target_binding_execution(
            None,
            generator.target,
            generator.iter,
            before,
            execution,
        )
        if execution.exact == 0:
            dead = True
            break

        for condition in generator.ifs:
            prefix.append(condition)
            condition_truth = (
                comprehension_execution.short_circuit_execution._semantic_truth(
                    condition, {}, {}
                )
            )
            if condition_truth is False:
                dead = True
                execution = comprehension_execution._ExecutionCount.zero()
                break
            if condition_truth is None:
                execution = comprehension_execution._after_unknown_filter(execution)

        if dead:
            break

    if not dead:
        return node

    replacement = ast.Tuple(
        elts=prefix or [ast.Constant(value=None)],
        ctx=ast.Load(),
    )
    return ast.copy_location(replacement, node)


comprehension_execution._PruneDeadEagerComprehensions._prune = _target_aware_prune


# ---------------------------------------------------------------------------
# Focused regressions
# ---------------------------------------------------------------------------


class ReleaseCandidateFinalExecutionCompositionTests(unittest.TestCase):
    def test_consumed_generator_body_survives_latest_call_composition(self) -> None:
        source = '''
def validate():
    list(Finding("PUBLIC_CODE", "visible") for _ in [1])
'''
        self.assertIn(
            "PUBLIC_CODE",
            literal_base.finding_semantic_signatures(source),
        )
        self.assertEqual(
            extended_reachability.reachable_contracts(
                source, "sample.py"
            )[("sample.py", "validate", "PUBLIC_CODE")],
            1,
        )

    def test_assigned_lambda_body_survives_latest_reachability_composition(self) -> None:
        source = '''
def validate():
    deferred = lambda: Finding("PUBLIC_CODE", "visible")
    deferred()
'''
        self.assertEqual(
            extended_reachability.reachable_contracts(
                source, "sample.py"
            )[("sample.py", "validate", "PUBLIC_CODE")],
            1,
        )

    def test_parameterized_generator_survives_latest_call_composition(self) -> None:
        source = '''
def read_text(path, findings, code):
    Finding(code, "decode failed", path="sample")
def validate(root, findings):
    list(read_text(root / "LICENSE", findings, "LICENSE_ENCODING") for _ in [1])
'''
        contracts = parameterized_reachability.reachable_parameterized_contracts(
            source,
            "sample.py",
        )
        self.assertEqual(len(contracts), 1)
        self.assertEqual(
            json.loads(next(iter(contracts)))["code"],
            "LICENSE_ENCODING",
        )


class ReleaseCandidateComprehensionTargetBindingTests(unittest.TestCase):
    def test_destructuring_failure_hides_literal_and_sink_finding(self) -> None:
        source = '''
def validate(findings):
    [findings.append(Finding("PUBLIC_CODE", "hidden")) for item, extra in [1]]
'''
        self.assertNotIn(
            "PUBLIC_CODE",
            literal_base.finding_semantic_signatures(source),
        )
        self.assertNotIn(
            "PUBLIC_CODE",
            sink_execution.finding_semantic_signatures_with_sink(source),
        )
        self.assertEqual(
            extended_reachability.reachable_contracts(source, "sample.py"),
            {},
        )

    def test_successful_destructuring_is_part_of_semantic_identity(self) -> None:
        plain = '''
def validate(findings):
    [findings.append(Finding("PUBLIC_CODE", "visible")) for item in [(1, 2)]]
'''
        destructured = '''
def validate(findings):
    [findings.append(Finding("PUBLIC_CODE", "visible")) for item, extra in [(1, 2)]]
'''
        plain_signatures = literal_base.finding_semantic_signatures(plain)
        destructured_signatures = literal_base.finding_semantic_signatures(
            destructured
        )
        self.assertIn("PUBLIC_CODE", plain_signatures)
        self.assertIn("PUBLIC_CODE", destructured_signatures)
        self.assertNotEqual(plain_signatures, destructured_signatures)

        payload = json.loads(destructured_signatures["PUBLIC_CODE"][0])
        self.assertTrue(
            any(
                marker.startswith(
                    "comprehension:list:generator:0:target:tuple(name,name):safe"
                )
                for marker in payload["context"]
            ),
            payload,
        )

    def test_destructuring_failure_prunes_parameterized_helper_call(self) -> None:
        source = '''
def read_text(path, findings, code):
    Finding(code, "decode failed", path="sample")
def validate(root, findings):
    [read_text(root / "LICENSE", findings, "LICENSE_ENCODING") for item, extra in [1]]
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


if __name__ == "__main__":
    unittest.main()
