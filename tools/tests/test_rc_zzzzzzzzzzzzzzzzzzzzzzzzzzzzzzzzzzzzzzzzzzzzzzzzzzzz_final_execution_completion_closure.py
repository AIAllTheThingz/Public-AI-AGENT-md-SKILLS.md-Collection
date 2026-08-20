from __future__ import annotations

import ast
import unittest

import rc_finding_code_contracts_base as literal_base
import test_rc_zzzz_sink_rebinding_and_parameterized_multiplicity as multiplicity
import test_rc_zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz_dynamic_calls_and_branch_prerequisites as prior


# Final execution-completion composition for PR #71.
#
# Keep four distinct concerns from bleeding into one another:
# * known helpers must successfully bind call arguments before their bodies run;
# * arbitrary calls remain execution gates, but an operation that is itself a
#   governed finding emission must not become a synthetic blocker for the next
#   identical emission and split multiplicity;
# * failures inside compound statements must propagate to the statement after
#   the compound; and
# * ordinary break/continue control transfer is not itself an exception.

assignment_scope = prior.assignment_scope
target_layer = prior.target_layer
parameterized_active = prior.parameterized_active
sink_execution = prior.sink_execution

_SAFE = prior._SAFE
_UNKNOWN = prior._UNKNOWN
_RAISES = prior._RAISES

_previous_call_execution_state = prior._call_execution_state
_previous_literal_blocking_prerequisite = target_layer._literal_blocking_prerequisite
_previous_parameterized_blocking_prerequisite = (
    target_layer._parameterized_blocking_prerequisite
)


# ---------------------------------------------------------------------------
# Call execution and Python argument binding.
# ---------------------------------------------------------------------------


def _literal_finding_append(call: ast.Call) -> bool:
    if not (
        isinstance(call.func, ast.Attribute)
        and call.func.attr in {"append", "extend", "insert"}
    ):
        return False
    return any(
        isinstance(item, ast.Call)
        and isinstance(item.func, ast.Name)
        and item.func.id == "Finding"
        for item in ast.walk(call)
    )


def _parameterized_finding_helper_call(visitor, call: ast.Call) -> bool:
    helpers = getattr(visitor, "parameterized_helpers", None)
    return (
        isinstance(call.func, ast.Name)
        and isinstance(helpers, (set, dict))
        and call.func.id in helpers
    )


def _governed_emission_call(visitor, call: ast.Call) -> bool:
    return _literal_finding_append(call) or _parameterized_finding_helper_call(
        visitor,
        call,
    )


def _call_binding_state(
    definition: ast.FunctionDef | ast.AsyncFunctionDef,
    call: ast.Call,
) -> str:
    """Classify direct known-helper argument binding without freezing names."""

    # Dynamic expansion can be valid or invalid depending on runtime contents.
    if any(isinstance(argument, ast.Starred) for argument in call.args):
        return _UNKNOWN
    if any(keyword.arg is None for keyword in call.keywords):
        return _UNKNOWN

    args = definition.args
    positional = [*args.posonlyargs, *args.args]
    positional_names = [argument.arg for argument in positional]
    posonly_names = {argument.arg for argument in args.posonlyargs}
    regular_names = {argument.arg for argument in args.args}
    kwonly_names = {argument.arg for argument in args.kwonlyargs}

    positional_count = len(call.args)
    if args.vararg is None and positional_count > len(positional):
        return _RAISES

    bound = set(positional_names[: min(positional_count, len(positional))])
    seen_keywords: set[str] = set()

    for keyword in call.keywords:
        assert keyword.arg is not None
        name = keyword.arg
        if name in seen_keywords:
            return _RAISES
        seen_keywords.add(name)

        if name in posonly_names:
            # Positional-only names may be captured by **kwargs but cannot bind
            # the positional-only parameter itself.
            if args.kwarg is None:
                return _RAISES
            continue

        if name in regular_names or name in kwonly_names:
            if name in bound:
                return _RAISES
            bound.add(name)
            continue

        if args.kwarg is None:
            return _RAISES

    required_positional_count = len(positional) - len(args.defaults)
    required_positional = {
        argument.arg for argument in positional[:required_positional_count]
    }
    if not required_positional.issubset(bound):
        return _RAISES

    required_kwonly = {
        argument.arg
        for argument, default in zip(args.kwonlyargs, args.kw_defaults)
        if default is None
    }
    if not required_kwonly.issubset(bound):
        return _RAISES

    return _SAFE


def _call_execution_state(
    visitor,
    call: ast.Call,
    *,
    parameterized: bool,
) -> str:
    # The finding/sink/call-site contract already owns these emissions. Treating
    # the first one as an opaque blocker for the second turns two identical
    # occurrences into two artificial contexts and breaks multiplicity.
    if _governed_emission_call(visitor, call):
        return _SAFE

    definitions = prior._definitions(visitor, parameterized=parameterized)
    if isinstance(call.func, ast.Name):
        definition = definitions.get(call.func.id)
        if isinstance(definition, (ast.FunctionDef, ast.AsyncFunctionDef)):
            argument_state = prior._call_argument_state(
                visitor,
                call,
                parameterized=parameterized,
            )
            if argument_state != _SAFE:
                return argument_state

            binding_state = _call_binding_state(definition, call)
            if binding_state != _SAFE:
                return binding_state

            # A decorator can replace both behavior and accepted signature.
            if definition.decorator_list:
                return _UNKNOWN

            # Calling async def synchronously creates a coroutine only after
            # eager argument evaluation and binding have succeeded.
            if isinstance(definition, ast.AsyncFunctionDef):
                return _SAFE

            return (
                _UNKNOWN
                if prior.helper_prerequisites._helper_may_abort(
                    call.func.id,
                    definitions,
                )
                else _SAFE
            )

    return _previous_call_execution_state(
        visitor,
        call,
        parameterized=parameterized,
    )


prior._call_execution_state = _call_execution_state


# ---------------------------------------------------------------------------
# Exception state propagated out of compound statements.
# ---------------------------------------------------------------------------


def _sequence_state(states: list[str]) -> str:
    if _RAISES in states:
        return _RAISES
    if _UNKNOWN in states:
        return _UNKNOWN
    return _SAFE


def _alternative_state(states: list[str]) -> str:
    if not states or all(state == _SAFE for state in states):
        return _SAFE
    if all(state == _RAISES for state in states):
        return _RAISES
    return _UNKNOWN


def _expression_state(visitor, node: ast.AST, *, parameterized: bool) -> str:
    if isinstance(node, ast.Call):
        return _call_execution_state(
            visitor,
            node,
            parameterized=parameterized,
        )
    return target_layer._expression_state(
        visitor,
        node,
        parameterized=parameterized,
    )


def _static_value(visitor, node: ast.AST, *, parameterized: bool):
    constants = assignment_scope._constants(
        visitor,
        parameterized=parameterized,
    )
    return assignment_scope._static_value(node, constants)


def _static_truth(visitor, node: ast.AST, *, parameterized: bool) -> bool | None:
    value = _static_value(visitor, node, parameterized=parameterized)
    if value is assignment_scope._STATIC_RAISES:
        return None
    if value is assignment_scope._STATIC_UNKNOWN:
        return None
    try:
        return bool(value)
    except Exception:
        return None


def _assignment_state(visitor, statement: ast.stmt, *, parameterized: bool) -> str:
    if not isinstance(statement, (ast.Assign, ast.AnnAssign, ast.AugAssign)):
        return _SAFE

    value = statement.value
    states = [
        _expression_state(
            visitor,
            value,
            parameterized=parameterized,
        )
    ]

    target_state = getattr(target_layer, "_target_binding_state", None)
    target_getter = getattr(target_layer, "_assignment_targets", None)
    if callable(target_state) and callable(target_getter):
        states.extend(
            target_state(target, value)
            for target in target_getter(statement)
        )
    return _sequence_state(states)


def _block_exception_state(
    visitor,
    statements: list[ast.stmt],
    *,
    parameterized: bool,
) -> str:
    result = _SAFE
    for statement in statements:
        state = _statement_exception_state(
            visitor,
            statement,
            parameterized=parameterized,
        )
        if state == _RAISES:
            return _RAISES
        if state == _UNKNOWN:
            result = _UNKNOWN

        # A safe control transfer ends this block. Reachability layers own that
        # fact; it is not an exception prerequisite for a later outer statement.
        if isinstance(statement, (ast.Return, ast.Break, ast.Continue)):
            break
    return result


def _if_state(visitor, statement: ast.If, *, parameterized: bool) -> str:
    test_state = _expression_state(
        visitor,
        statement.test,
        parameterized=parameterized,
    )
    if test_state == _RAISES:
        return _RAISES

    truth = _static_truth(visitor, statement.test, parameterized=parameterized)
    if truth is True:
        branch_state = _block_exception_state(
            visitor,
            statement.body,
            parameterized=parameterized,
        )
    elif truth is False:
        branch_state = _block_exception_state(
            visitor,
            statement.orelse,
            parameterized=parameterized,
        )
    else:
        branch_state = _alternative_state(
            [
                _block_exception_state(
                    visitor,
                    statement.body,
                    parameterized=parameterized,
                ),
                _block_exception_state(
                    visitor,
                    statement.orelse,
                    parameterized=parameterized,
                ),
            ]
        )

    if test_state == _UNKNOWN and branch_state != _UNKNOWN:
        return _UNKNOWN
    return branch_state


def _iter_presence(visitor, node: ast.AST, *, parameterized: bool) -> str:
    value = _static_value(visitor, node, parameterized=parameterized)
    if value is assignment_scope._STATIC_RAISES:
        return "raises"
    if value is assignment_scope._STATIC_UNKNOWN:
        return "unknown"
    try:
        iterator = iter(value)
        next(iterator)
    except StopIteration:
        return "empty"
    except Exception:
        return "raises"
    return "nonempty"


def _for_state(
    visitor,
    statement: ast.For | ast.AsyncFor,
    *,
    parameterized: bool,
) -> str:
    iter_state = _expression_state(
        visitor,
        statement.iter,
        parameterized=parameterized,
    )
    if iter_state == _RAISES:
        return _RAISES

    body_state = _block_exception_state(
        visitor,
        statement.body,
        parameterized=parameterized,
    )
    else_state = _block_exception_state(
        visitor,
        statement.orelse,
        parameterized=parameterized,
    )

    if isinstance(statement, ast.AsyncFor):
        return _UNKNOWN if body_state != _SAFE or iter_state != _SAFE else _UNKNOWN

    presence = _iter_presence(
        visitor,
        statement.iter,
        parameterized=parameterized,
    )
    if presence == "raises":
        return _RAISES
    if presence == "empty":
        return _sequence_state([iter_state, else_state])
    if presence == "nonempty":
        if body_state == _RAISES:
            return _RAISES
        return _sequence_state([iter_state, body_state, else_state])

    if body_state != _SAFE:
        return _UNKNOWN
    return _sequence_state([iter_state, else_state])


def _while_state(visitor, statement: ast.While, *, parameterized: bool) -> str:
    test_state = _expression_state(
        visitor,
        statement.test,
        parameterized=parameterized,
    )
    if test_state == _RAISES:
        return _RAISES

    body_state = _block_exception_state(
        visitor,
        statement.body,
        parameterized=parameterized,
    )
    else_state = _block_exception_state(
        visitor,
        statement.orelse,
        parameterized=parameterized,
    )
    truth = _static_truth(visitor, statement.test, parameterized=parameterized)

    if truth is False:
        return _sequence_state([test_state, else_state])
    if truth is True:
        if body_state == _RAISES:
            return _RAISES
        return _sequence_state([test_state, body_state, else_state])
    if body_state != _SAFE:
        return _UNKNOWN
    return _sequence_state([test_state, else_state])


def _handler_is_catchall(handler: ast.ExceptHandler) -> bool:
    return handler.type is None or (
        isinstance(handler.type, ast.Name)
        and handler.type.id == "BaseException"
    )


def _try_state(visitor, statement: ast.AST, *, parameterized: bool) -> str:
    body_state = _block_exception_state(
        visitor,
        statement.body,
        parameterized=parameterized,
    )
    handler_states = [
        _block_exception_state(
            visitor,
            handler.body,
            parameterized=parameterized,
        )
        for handler in statement.handlers
    ]
    else_state = _block_exception_state(
        visitor,
        statement.orelse,
        parameterized=parameterized,
    )
    final_state = _block_exception_state(
        visitor,
        statement.finalbody,
        parameterized=parameterized,
    )

    if final_state == _RAISES:
        return _RAISES
    if final_state == _UNKNOWN:
        return _UNKNOWN
    if any(state != _SAFE for state in handler_states):
        return _UNKNOWN
    if else_state != _SAFE:
        return _UNKNOWN
    if body_state == _SAFE:
        return _SAFE
    if body_state == _RAISES and not statement.handlers:
        return _RAISES
    if body_state != _SAFE and any(
        _handler_is_catchall(handler) for handler in statement.handlers
    ):
        return _SAFE
    return _UNKNOWN


def _with_state(
    visitor,
    statement: ast.With | ast.AsyncWith,
    *,
    parameterized: bool,
) -> str:
    context_states = [
        _expression_state(
            visitor,
            item.context_expr,
            parameterized=parameterized,
        )
        for item in statement.items
    ]
    if _RAISES in context_states:
        return _RAISES

    body_state = _block_exception_state(
        visitor,
        statement.body,
        parameterized=parameterized,
    )
    if body_state != _SAFE or _UNKNOWN in context_states:
        return _UNKNOWN

    # Enter/exit protocol methods are executable even when the expression that
    # produced the manager is statically safe.
    return _UNKNOWN if statement.items else _SAFE


def _match_state(visitor, statement: ast.Match, *, parameterized: bool) -> str:
    subject_state = _expression_state(
        visitor,
        statement.subject,
        parameterized=parameterized,
    )
    if subject_state == _RAISES:
        return _RAISES

    states = [subject_state]
    for case in statement.cases:
        if case.guard is not None:
            truth = _static_truth(
                visitor,
                case.guard,
                parameterized=parameterized,
            )
            if truth is False:
                continue
            guard_state = _expression_state(
                visitor,
                case.guard,
                parameterized=parameterized,
            )
            if guard_state != _SAFE:
                states.append(_UNKNOWN)

        body_state = _block_exception_state(
            visitor,
            case.body,
            parameterized=parameterized,
        )
        if body_state != _SAFE:
            states.append(_UNKNOWN)
    return _sequence_state(states)


def _statement_exception_state(
    visitor,
    statement: ast.stmt,
    *,
    parameterized: bool,
) -> str:
    if isinstance(statement, ast.Raise):
        return _RAISES

    if isinstance(statement, ast.Return):
        if statement.value is None:
            return _SAFE
        return _expression_state(
            visitor,
            statement.value,
            parameterized=parameterized,
        )

    if isinstance(statement, (ast.Break, ast.Continue, ast.Pass)):
        return _SAFE

    if isinstance(statement, ast.Expr):
        return _expression_state(
            visitor,
            statement.value,
            parameterized=parameterized,
        )

    if isinstance(statement, ast.Assert):
        return prior.prior.prior._assert_static_state(
            visitor,
            statement,
            parameterized=parameterized,
        )

    if isinstance(statement, (ast.Assign, ast.AnnAssign, ast.AugAssign)):
        return _assignment_state(
            visitor,
            statement,
            parameterized=parameterized,
        )

    if isinstance(statement, ast.If):
        return _if_state(
            visitor,
            statement,
            parameterized=parameterized,
        )

    if isinstance(statement, (ast.For, ast.AsyncFor)):
        return _for_state(
            visitor,
            statement,
            parameterized=parameterized,
        )

    if isinstance(statement, ast.While):
        return _while_state(
            visitor,
            statement,
            parameterized=parameterized,
        )

    try_types = (ast.Try,)
    if hasattr(ast, "TryStar"):
        try_types = (*try_types, ast.TryStar)
    if isinstance(statement, try_types):
        return _try_state(
            visitor,
            statement,
            parameterized=parameterized,
        )

    if isinstance(statement, (ast.With, ast.AsyncWith)):
        return _with_state(
            visitor,
            statement,
            parameterized=parameterized,
        )

    if isinstance(statement, ast.Match):
        return _match_state(
            visitor,
            statement,
            parameterized=parameterized,
        )

    if isinstance(statement, (ast.Import, ast.ImportFrom, ast.Delete)):
        return _UNKNOWN

    # Definition-time defaults/decorators/class construction are owned by the
    # earlier dedicated compatibility layers.
    return _SAFE


def _branch_block_state(
    visitor,
    statements: list[ast.stmt],
    *,
    parameterized: bool,
) -> str:
    return _block_exception_state(
        visitor,
        statements,
        parameterized=parameterized,
    )


# The prior if analysis resolves this helper through module globals at runtime.
prior._branch_block_state = _branch_block_state


def _compound_prerequisite(
    visitor,
    statement: ast.stmt,
    *,
    parameterized: bool,
) -> ast.AST | None:
    # If retains the preceding layer's established marker/tests; everything else
    # gets one semantic compound completion class rather than raw private AST.
    compound_types = (
        ast.For,
        ast.AsyncFor,
        ast.While,
        ast.Try,
        ast.With,
        ast.AsyncWith,
        ast.Match,
    )
    if hasattr(ast, "TryStar"):
        compound_types = (*compound_types, ast.TryStar)

    if not isinstance(statement, compound_types):
        return None

    state = _statement_exception_state(
        visitor,
        statement,
        parameterized=parameterized,
    )
    if state == _RAISES:
        return prior.prior._statement_risk_marker("compound-raises")
    if state == _UNKNOWN:
        return prior.prior._statement_risk_marker("compound-may-fail")
    return None


def _literal_blocking_prerequisite(visitor, statement: ast.stmt) -> ast.AST | None:
    existing = _previous_literal_blocking_prerequisite(visitor, statement)
    compound = _compound_prerequisite(
        visitor,
        statement,
        parameterized=False,
    )
    return target_layer._combine_prerequisites(
        [item for item in (existing, compound) if item is not None]
    )


def _parameterized_blocking_prerequisite(
    visitor,
    statement: ast.stmt,
) -> ast.AST | None:
    existing = _previous_parameterized_blocking_prerequisite(visitor, statement)
    compound = _compound_prerequisite(
        visitor,
        statement,
        parameterized=True,
    )
    return target_layer._combine_prerequisites(
        [item for item in (existing, compound) if item is not None]
    )


target_layer._literal_blocking_prerequisite = _literal_blocking_prerequisite
target_layer._parameterized_blocking_prerequisite = (
    _parameterized_blocking_prerequisite
)


# ---------------------------------------------------------------------------
# Permanent regressions for the four review findings and #512 regression.
# ---------------------------------------------------------------------------


class ReleaseCandidateFinalExecutionCompletionTests(unittest.TestCase):
    def test_known_helper_argument_binding_failure_changes_literal_and_sink(self) -> None:
        direct = '''
def run(findings):
    findings.append(Finding("PUBLIC_CODE", "message"))
'''
        blocked = '''
def harmless():
    return 1
def run(findings):
    harmless(1)
    findings.append(Finding("PUBLIC_CODE", "message"))
'''
        self.assertNotEqual(
            literal_base.finding_semantic_signatures(direct),
            literal_base.finding_semantic_signatures(blocked),
        )
        self.assertNotEqual(
            sink_execution.finding_semantic_signatures_with_sink(direct),
            sink_execution.finding_semantic_signatures_with_sink(blocked),
        )

    def test_known_helper_missing_required_argument_is_detected(self) -> None:
        direct = '''
def run(findings):
    findings.append(Finding("PUBLIC_CODE", "message"))
'''
        blocked = '''
def helper(required):
    return required
def run(findings):
    helper()
    findings.append(Finding("PUBLIC_CODE", "message"))
'''
        self.assertNotEqual(
            literal_base.finding_semantic_signatures(direct),
            literal_base.finding_semantic_signatures(blocked),
        )

    def test_identical_parameterized_emissions_keep_multiplicity(self) -> None:
        single = '''
def read_text(path, findings, code):
    Finding(code, "decode failed", path="sample")
def validate(root, findings):
    read_text(root / "LICENSE", findings, "LICENSE_ENCODING")
'''
        duplicate = single.replace(
            '    read_text(root / "LICENSE", findings, "LICENSE_ENCODING")',
            '    read_text(root / "LICENSE", findings, "LICENSE_ENCODING")\n'
            '    read_text(root / "LICENSE", findings, "LICENSE_ENCODING")',
        )
        expected = multiplicity._reachable_parameterized_counts(single, "sample.py")
        actual = multiplicity._reachable_parameterized_counts(duplicate, "sample.py")
        self.assertEqual(sum(expected.values()), 1)
        self.assertEqual(sum(actual.values()), 2)
        contract = next(iter(expected))
        self.assertEqual(actual[contract], 2)

    def test_identical_literal_emissions_keep_multiplicity(self) -> None:
        single = '''
def run(findings):
    findings.append(Finding("PUBLIC_CODE", "message"))
'''
        duplicate = '''
def run(findings):
    findings.append(Finding("PUBLIC_CODE", "message"))
    findings.append(Finding("PUBLIC_CODE", "message"))
'''
        one = literal_base.finding_semantic_signatures(single)["PUBLIC_CODE"]
        two = literal_base.finding_semantic_signatures(duplicate)["PUBLIC_CODE"]
        self.assertEqual(len(one), 1)
        self.assertEqual(len(two), 2)
        self.assertEqual(two[0], two[1])

    def test_compound_failures_propagate_to_following_literal_and_sink(self) -> None:
        direct = '''
def run(findings, flag, value):
    findings.append(Finding("PUBLIC_CODE", "message"))
'''
        cases = {
            "for": '''
def explode():
    raise RuntimeError("stop")
def run(findings, flag, value):
    for item in [1]:
        explode()
    findings.append(Finding("PUBLIC_CODE", "message"))
''',
            "while": '''
def explode():
    raise RuntimeError("stop")
def run(findings, flag, value):
    while flag:
        explode()
    findings.append(Finding("PUBLIC_CODE", "message"))
''',
            "try": '''
def explode():
    raise RuntimeError("stop")
def run(findings, flag, value):
    try:
        explode()
    finally:
        marker = 1
    findings.append(Finding("PUBLIC_CODE", "message"))
''',
            "with": '''
from contextlib import nullcontext
def explode():
    raise RuntimeError("stop")
def run(findings, flag, value):
    with nullcontext():
        explode()
    findings.append(Finding("PUBLIC_CODE", "message"))
''',
            "match": '''
def explode():
    raise RuntimeError("stop")
def run(findings, flag, value):
    match value:
        case 1:
            explode()
        case _:
            pass
    findings.append(Finding("PUBLIC_CODE", "message"))
''',
        }
        expected = literal_base.finding_semantic_signatures(direct)
        expected_sink = sink_execution.finding_semantic_signatures_with_sink(direct)
        for name, source in cases.items():
            with self.subTest(compound=name):
                self.assertNotEqual(
                    expected,
                    literal_base.finding_semantic_signatures(source),
                )
                self.assertNotEqual(
                    expected_sink,
                    sink_execution.finding_semantic_signatures_with_sink(source),
                )

    def test_for_failure_propagates_to_parameterized_emission(self) -> None:
        direct = '''
def read_text(path, findings, code):
    Finding(code, "decode failed", path="sample")
def validate(root, findings):
    read_text(root / "LICENSE", findings, "LICENSE_ENCODING")
'''
        blocked = '''
def read_text(path, findings, code):
    Finding(code, "decode failed", path="sample")
def explode():
    raise RuntimeError("stop")
def validate(root, findings):
    for item in [1]:
        explode()
    read_text(root / "LICENSE", findings, "LICENSE_ENCODING")
'''
        self.assertNotEqual(
            parameterized_active.parameterized_finding_contracts(
                direct,
                "sample.py",
            ),
            parameterized_active.parameterized_finding_contracts(
                blocked,
                "sample.py",
            ),
        )

    def test_dead_for_failure_does_not_freeze_detail(self) -> None:
        direct = '''
def run(findings):
    findings.append(Finding("PUBLIC_CODE", "message"))
'''
        dead = '''
def explode():
    raise RuntimeError("stop")
def run(findings):
    for item in []:
        explode()
    findings.append(Finding("PUBLIC_CODE", "message"))
'''
        self.assertEqual(
            literal_base.finding_semantic_signatures(direct),
            literal_base.finding_semantic_signatures(dead),
        )


if __name__ == "__main__":
    unittest.main()
