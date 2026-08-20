from __future__ import annotations

import ast
import builtins
import json
import unittest

import rc_finding_code_contracts_base as literal_base
import test_rc_zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz_final_execution_completion_closure as execution
import test_rc_zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz_returned_sink_selection_closure as returned_selection


# Close the three P1 gaps exposed after exact-head run #515:
# * **kwargs can replace or ambiguously supply the returned findings sink;
# * exception-handler type expressions execute while matching an exception; and
# * context-manager ``as`` targets bind before the with-body executes.
#
# Keep the contract semantic. Add narrow execution-risk classes instead of
# fingerprinting otherwise harmless private implementation syntax.

target_layer = execution.target_layer
parameterized_active = execution.parameterized_active
sink_execution = execution.sink_execution
sink_state = returned_selection.sink_state
post_sink = returned_selection.post_sink

_SAFE = execution._SAFE
_UNKNOWN = execution._UNKNOWN
_RAISES = execution._RAISES

_previous_emission_sink_contract = sink_execution._emission_sink_contract
_previous_literal_blocking_prerequisite = target_layer._literal_blocking_prerequisite
_previous_parameterized_blocking_prerequisite = (
    target_layer._parameterized_blocking_prerequisite
)
_previous_try_state = execution._try_state
_previous_with_state = execution._with_state

_EXPANDED_KEYWORD_PREFIX = "post-returned-local-sink-expanded-keyword:"


# ---------------------------------------------------------------------------
# Returned findings supplied through **kwargs.
# ---------------------------------------------------------------------------


def _is_from_findings_call(call: ast.Call) -> bool:
    return isinstance(call.func, ast.Attribute) and call.func.attr == "from_findings"


def _function_parameter_names(
    function: ast.FunctionDef | ast.AsyncFunctionDef,
) -> set[str]:
    names = {
        argument.arg
        for argument in (
            *function.args.posonlyargs,
            *function.args.args,
            *function.args.kwonlyargs,
        )
    }
    if function.args.vararg is not None:
        names.add(function.args.vararg.arg)
    if function.args.kwarg is not None:
        names.add(function.args.kwarg.arg)
    return names


def _expanded_dict_findings(node: ast.AST) -> tuple[str, ast.AST | None]:
    """Classify one **mapping with respect to the ``findings`` key."""

    if not isinstance(node, ast.Dict):
        return "dynamic", None

    current: ast.AST | None = None
    dynamic_after = False

    for key, value in zip(node.keys, node.values):
        if key is None:
            # A nested **mapping can introduce/override ``findings``.
            current = None
            dynamic_after = True
            continue

        if isinstance(key, ast.Constant) and isinstance(key.value, str):
            if key.value == "findings":
                current = value
                dynamic_after = False
            continue

        # A runtime-computed mapping key could equal ``findings``.
        current = None
        dynamic_after = True

    if current is not None and not dynamic_after:
        return "exact", current
    if dynamic_after:
        return "dynamic", None
    return "absent", None


def _expanded_keyword_state(
    call: ast.Call,
    receiver_name: str,
) -> tuple[str, ast.AST | None] | None:
    if not _is_from_findings_call(call):
        return None

    expansions = [keyword for keyword in call.keywords if keyword.arg is None]
    if not expansions:
        return None

    explicit = next(
        (keyword.value for keyword in call.keywords if keyword.arg == "findings"),
        None,
    )
    positional_candidates = [
        argument
        for argument in call.args
        if returned_selection._contains_name(argument, receiver_name)
    ]
    positional = positional_candidates[0] if len(positional_candidates) == 1 else None
    base_sink = explicit if explicit is not None else positional

    exact_values: list[ast.AST] = []
    saw_dynamic = False
    for keyword in expansions:
        kind, value = _expanded_dict_findings(keyword.value)
        if kind == "dynamic":
            saw_dynamic = True
        elif kind == "exact" and value is not None:
            exact_values.append(value)

    if saw_dynamic:
        # Dynamic expansion can omit findings, replace it, or duplicate an
        # explicit value and make the call fail during argument binding.
        return "dynamic-may-discard-or-fail", None

    if exact_values:
        if base_sink is not None or len(exact_values) > 1:
            # Duplicate keyword values raise before ToolResult is returned.
            return "duplicate-findings-raises", None

        state, selector = returned_selection._selection_state(
            exact_values[0],
            receiver_name,
        )
        if state == "kept":
            return None
        return state, selector

    if base_sink is not None:
        # All static expansions are proven not to contain ``findings``.
        return None

    # No positional/explicit findings and no static expansion supplies it.
    return "missing-findings-raises", None


def _expanded_keyword_return_markers(
    finding: ast.Call,
    receiver: ast.AST,
    parents: dict[int, ast.AST],
) -> list[str]:
    function = sink_state._enclosing_function(finding, parents)
    if function is None:
        return []

    receiver_name = sink_state._root_name(receiver)
    if receiver_name is None or receiver_name in _function_parameter_names(function):
        return []

    finding_line = getattr(finding, "lineno", 10**9)
    markers: list[tuple[int, int, str]] = []

    for returned in ast.walk(function):
        if not (
            isinstance(returned, ast.Return)
            and returned.value is not None
            and sink_state._belongs_to_function(returned, function, parents)
            and getattr(returned, "lineno", 0) > finding_line
            and post_sink._can_share_execution_path(
                finding,
                returned,
                function,
                parents,
            )
        ):
            continue

        for call in ast.walk(returned.value):
            if not isinstance(call, ast.Call):
                continue
            state = _expanded_keyword_state(call, receiver_name)
            if state is None:
                continue

            selection, selector = state
            payload: dict[str, object] = {
                "context": sink_state._sink_state_context(
                    returned,
                    function,
                    parents,
                ),
                "selection": selection,
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


def _emission_sink_contract_with_expanded_keywords(
    node: ast.Call,
    parents: dict[int, ast.AST],
) -> list[str]:
    contract = list(_previous_emission_sink_contract(node, parents))
    receiver = sink_state._finding_sink_receiver(node, parents)
    if receiver is None:
        return contract

    markers = _expanded_keyword_return_markers(node, receiver, parents)
    if markers:
        contract.append(_EXPANDED_KEYWORD_PREFIX + json.dumps(markers, sort_keys=True))
    return contract


sink_execution._emission_sink_contract = _emission_sink_contract_with_expanded_keywords


# ---------------------------------------------------------------------------
# Exception-handler type execution.
# ---------------------------------------------------------------------------


def _exception_type_state(
    visitor,
    node: ast.AST,
    *,
    parameterized: bool,
) -> str:
    if isinstance(node, ast.Tuple):
        return execution._sequence_state(
            [
                _exception_type_state(
                    visitor,
                    item,
                    parameterized=parameterized,
                )
                for item in node.elts
            ]
        )

    if isinstance(node, ast.Name):
        value = getattr(builtins, node.id, None)
        if isinstance(value, type):
            try:
                if issubclass(value, BaseException):
                    return _SAFE
            except TypeError:
                pass

        definitions = execution.prior._definitions(
            visitor,
            parameterized=parameterized,
        )
        if node.id in definitions:
            # Resolving a source-defined class/name is safe, but whether the
            # object is a valid exception class is not proven by this layer.
            return _UNKNOWN
        return _UNKNOWN

    # Attribute lookup or any other computed handler type can execute arbitrary
    # lookup/coercion behavior and can also evaluate to a non-exception object.
    state = execution._expression_state(
        visitor,
        node,
        parameterized=parameterized,
    )
    return _RAISES if state == _RAISES else _UNKNOWN


def _handler_type_execution_state(
    visitor,
    statement: ast.AST,
    *,
    parameterized: bool,
) -> str:
    body_state = execution._block_exception_state(
        visitor,
        statement.body,
        parameterized=parameterized,
    )
    if body_state == _SAFE:
        # No exception from the try body means handler types are not evaluated.
        return _SAFE

    result = _SAFE
    for handler in statement.handlers:
        if handler.type is None:
            break

        state = _exception_type_state(
            visitor,
            handler.type,
            parameterized=parameterized,
        )
        if state == _RAISES:
            return _RAISES if body_state == _RAISES else _UNKNOWN
        if state == _UNKNOWN:
            result = _UNKNOWN

        if execution._handler_is_catchall(handler):
            break

    return result


def _try_state_with_handler_types(
    visitor,
    statement: ast.AST,
    *,
    parameterized: bool,
) -> str:
    base = _previous_try_state(
        visitor,
        statement,
        parameterized=parameterized,
    )
    handler_state = _handler_type_execution_state(
        visitor,
        statement,
        parameterized=parameterized,
    )
    if handler_state == _RAISES:
        return _RAISES
    if handler_state == _UNKNOWN:
        return _UNKNOWN
    return base


execution._try_state = _try_state_with_handler_types


# ---------------------------------------------------------------------------
# Context-manager target binding.
# ---------------------------------------------------------------------------


def _with_target_binding_state(statement: ast.With | ast.AsyncWith) -> str:
    for item in statement.items:
        target = item.optional_vars
        if target is None or isinstance(target, ast.Name):
            continue

        # ``__enter__``/``__aenter__`` results are runtime values. Tuple/list
        # destructuring can fail to unpack; attribute/subscript targets can fail
        # during the store. Without a proven entry value, these are conditional.
        return _UNKNOWN

    return _SAFE


def _with_state_with_target_binding(
    visitor,
    statement: ast.With | ast.AsyncWith,
    *,
    parameterized: bool,
) -> str:
    base = _previous_with_state(
        visitor,
        statement,
        parameterized=parameterized,
    )
    target_state = _with_target_binding_state(statement)
    if target_state == _RAISES:
        return _RAISES
    if target_state == _UNKNOWN:
        return _UNKNOWN
    return base


execution._with_state = _with_state_with_target_binding


# ---------------------------------------------------------------------------
# Add stable targeted prerequisite classes so the newly modeled risks remain
# distinguishable even when the enclosing compound was already "may-fail".
# ---------------------------------------------------------------------------


def _targeted_compound_prerequisite(
    visitor,
    statement: ast.stmt,
    *,
    parameterized: bool,
) -> ast.AST | None:
    markers: list[ast.AST] = []

    try_types = (ast.Try,)
    if hasattr(ast, "TryStar"):
        try_types = (*try_types, ast.TryStar)

    if isinstance(statement, try_types):
        state = _handler_type_execution_state(
            visitor,
            statement,
            parameterized=parameterized,
        )
        if state == _RAISES:
            markers.append(
                execution.prior.prior._statement_risk_marker("handler-type-raises")
            )
        elif state == _UNKNOWN:
            markers.append(
                execution.prior.prior._statement_risk_marker("handler-type-may-fail")
            )

    if isinstance(statement, (ast.With, ast.AsyncWith)):
        state = _with_target_binding_state(statement)
        if state == _RAISES:
            markers.append(
                execution.prior.prior._statement_risk_marker(
                    "with-target-binding-raises"
                )
            )
        elif state == _UNKNOWN:
            markers.append(
                execution.prior.prior._statement_risk_marker(
                    "with-target-binding-may-fail"
                )
            )

    return target_layer._combine_prerequisites(markers)


def _literal_blocking_prerequisite(
    visitor,
    statement: ast.stmt,
) -> ast.AST | None:
    existing = _previous_literal_blocking_prerequisite(visitor, statement)
    targeted = _targeted_compound_prerequisite(
        visitor,
        statement,
        parameterized=False,
    )
    return target_layer._combine_prerequisites(
        [item for item in (existing, targeted) if item is not None]
    )


def _parameterized_blocking_prerequisite(
    visitor,
    statement: ast.stmt,
) -> ast.AST | None:
    existing = _previous_parameterized_blocking_prerequisite(visitor, statement)
    targeted = _targeted_compound_prerequisite(
        visitor,
        statement,
        parameterized=True,
    )
    return target_layer._combine_prerequisites(
        [item for item in (existing, targeted) if item is not None]
    )


target_layer._literal_blocking_prerequisite = _literal_blocking_prerequisite
target_layer._parameterized_blocking_prerequisite = _parameterized_blocking_prerequisite


# ---------------------------------------------------------------------------
# Permanent regressions for the exact P1 reproductions.
# ---------------------------------------------------------------------------


class ReleaseCandidateExpandedKeywordsHandlerTypesAndWithTargetsTests(
    unittest.TestCase
):
    def test_static_expanded_findings_discard_changes_literal_and_sink(self) -> None:
        direct = '''
def validate():
    findings = []
    findings.append(Finding("PUBLIC_CODE", "visible"))
    return ToolResult.from_findings(
        tool="validate",
        version="1",
        findings=findings,
    )
'''
        discarded = '''
def validate():
    findings = []
    findings.append(Finding("PUBLIC_CODE", "visible"))
    return ToolResult.from_findings(
        tool="validate",
        version="1",
        **{"findings": []},
    )
'''
        self.assertNotEqual(
            literal_base.finding_semantic_signatures(direct),
            literal_base.finding_semantic_signatures(discarded),
        )
        self.assertNotEqual(
            sink_execution.finding_semantic_signatures_with_sink(direct),
            sink_execution.finding_semantic_signatures_with_sink(discarded),
        )

    def test_static_expanded_original_sink_remains_compatible(self) -> None:
        direct = '''
def validate():
    findings = []
    findings.append(Finding("PUBLIC_CODE", "visible"))
    return ToolResult.from_findings(
        tool="validate",
        version="1",
        findings=findings,
    )
'''
        expanded = '''
def validate():
    findings = []
    findings.append(Finding("PUBLIC_CODE", "visible"))
    return ToolResult.from_findings(
        tool="validate",
        version="1",
        **{"findings": findings},
    )
'''
        self.assertEqual(
            literal_base.finding_semantic_signatures(direct),
            literal_base.finding_semantic_signatures(expanded),
        )

    def test_dynamic_expanded_findings_is_conservative(self) -> None:
        direct = '''
def validate(payload):
    findings = []
    findings.append(Finding("PUBLIC_CODE", "visible"))
    return ToolResult.from_findings(
        tool="validate",
        version="1",
        findings=findings,
    )
'''
        dynamic = '''
def validate(payload):
    findings = []
    findings.append(Finding("PUBLIC_CODE", "visible"))
    return ToolResult.from_findings(
        tool="validate",
        version="1",
        **payload,
    )
'''
        self.assertNotEqual(
            literal_base.finding_semantic_signatures(direct),
            literal_base.finding_semantic_signatures(dynamic),
        )

    def test_handler_type_lookup_changes_following_literal_and_sink(self) -> None:
        safe = '''
def explode():
    raise ValueError("stop")
def run(findings):
    try:
        explode()
    except Exception:
        pass
    findings.append(Finding("PUBLIC_CODE", "message"))
'''
        risky = safe.replace("except Exception:", "except MissingType:")
        self.assertNotEqual(
            literal_base.finding_semantic_signatures(safe),
            literal_base.finding_semantic_signatures(risky),
        )
        self.assertNotEqual(
            sink_execution.finding_semantic_signatures_with_sink(safe),
            sink_execution.finding_semantic_signatures_with_sink(risky),
        )

    def test_handler_type_lookup_changes_parameterized_contract(self) -> None:
        safe = '''
def read_text(path, findings, code):
    Finding(code, "decode failed", path="sample")
def explode():
    raise ValueError("stop")
def validate(path, findings):
    try:
        explode()
    except Exception:
        pass
    read_text(path, findings, "PUBLIC_CODE")
'''
        risky = safe.replace("except Exception:", "except MissingType:")
        self.assertNotEqual(
            parameterized_active.parameterized_finding_contracts(safe, "sample.py"),
            parameterized_active.parameterized_finding_contracts(risky, "sample.py"),
        )

    def test_with_target_binding_changes_following_literal_and_sink(self) -> None:
        simple = '''
def run(findings, manager):
    with manager as item:
        pass
    findings.append(Finding("PUBLIC_CODE", "message"))
'''
        destructured = '''
def run(findings, manager):
    with manager as (left, right):
        pass
    findings.append(Finding("PUBLIC_CODE", "message"))
'''
        self.assertNotEqual(
            literal_base.finding_semantic_signatures(simple),
            literal_base.finding_semantic_signatures(destructured),
        )
        self.assertNotEqual(
            sink_execution.finding_semantic_signatures_with_sink(simple),
            sink_execution.finding_semantic_signatures_with_sink(destructured),
        )

    def test_with_target_binding_changes_parameterized_contract(self) -> None:
        simple = '''
def read_text(path, findings, code):
    Finding(code, "decode failed", path="sample")
def validate(path, findings, manager):
    with manager as item:
        pass
    read_text(path, findings, "PUBLIC_CODE")
'''
        destructured = simple.replace(
            "with manager as item:",
            "with manager as (left, right):",
        )
        self.assertNotEqual(
            parameterized_active.parameterized_finding_contracts(simple, "sample.py"),
            parameterized_active.parameterized_finding_contracts(
                destructured,
                "sample.py",
            ),
        )


if __name__ == "__main__":
    unittest.main()
