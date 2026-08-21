from __future__ import annotations

import ast
import unittest

import test_rc_zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz_expression_statement_prerequisites as prior
import test_rc_zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz_conditional_pre_emission_helper_prerequisites as helper_prerequisites


# Final composition for the two execution gaps reported after exact-head run #511:
#
# * a standalone dynamic call (parameter, attribute, imported callable, etc.) can
#   raise before a following published emission even when it is not a known
#   same-module helper; and
# * a compound `if` can contain a potentially failing execution path whose
#   failure prevents the statement after the branch from being reached.
#
# Preserve the established narrowness: a same-module synchronous helper that is
# proven non-aborting remains compatible, and statically dead failing branches do
# not become part of the public contract. Risk markers encode execution classes,
# not private helper/variable spelling.

assignment_scope = prior.assignment_scope
target_layer = prior.target_layer
literal_base = prior.literal_base
parameterized_active = prior.parameterized_active
sink_execution = prior.sink_execution

_SAFE = prior._SAFE
_UNKNOWN = prior._UNKNOWN
_RAISES = prior._RAISES

_previous_literal_blocking_prerequisite = target_layer._literal_blocking_prerequisite
_previous_parameterized_blocking_prerequisite = (
    target_layer._parameterized_blocking_prerequisite
)


def _merge_sequence_states(states: list[str]) -> str:
    if _RAISES in states:
        return _RAISES
    if _UNKNOWN in states:
        return _UNKNOWN
    return _SAFE


def _merge_alternative_states(states: list[str]) -> str:
    if not states or all(state == _SAFE for state in states):
        return _SAFE
    if all(state == _RAISES for state in states):
        return _RAISES
    return _UNKNOWN


def _definitions(visitor, *, parameterized: bool) -> dict[str, ast.AST]:
    if parameterized:
        definitions = getattr(visitor, "definitions", None)
        if isinstance(definitions, dict):
            return definitions
        module_values = getattr(visitor, "module_values", None)
        if isinstance(module_values, dict):
            return module_values
        return {}

    definitions = getattr(visitor, "module_definitions", None)
    return definitions if isinstance(definitions, dict) else {}


def _call_argument_state(
    visitor,
    call: ast.Call,
    *,
    parameterized: bool,
) -> str:
    states = [
        target_layer._expression_state(
            visitor,
            item,
            parameterized=parameterized,
        )
        for item in [
            *call.args,
            *(keyword.value for keyword in call.keywords),
        ]
    ]
    return _merge_sequence_states(states) if states else _SAFE


def _call_execution_state(
    visitor,
    call: ast.Call,
    *,
    parameterized: bool,
) -> str:
    """Classify completion of a standalone call before the next statement.

    Known same-module functions retain the established helper analysis. This is
    important: blindly classifying every call as unknown would reintroduce the
    implementation-detail false positives closed by the earlier PR #71 layers.
    Dynamic and external callables remain conservative because arbitrary call
    execution can raise.
    """

    definitions = _definitions(visitor, parameterized=parameterized)
    if isinstance(call.func, ast.Name):
        definition = definitions.get(call.func.id)
        if isinstance(definition, (ast.FunctionDef, ast.AsyncFunctionDef)):
            argument_state = _call_argument_state(
                visitor,
                call,
                parameterized=parameterized,
            )
            if argument_state != _SAFE:
                return argument_state

            # Calling async def synchronously creates a coroutine; its body is
            # deferred. Argument evaluation above is still eager.
            if isinstance(definition, ast.AsyncFunctionDef):
                return _SAFE

            return (
                _UNKNOWN
                if helper_prerequisites._helper_may_abort(
                    call.func.id,
                    definitions,
                )
                else _SAFE
            )

    return target_layer._expression_state(
        visitor,
        call,
        parameterized=parameterized,
    )


def _standalone_call_prerequisite(
    visitor,
    statement: ast.stmt,
    *,
    parameterized: bool,
) -> ast.AST | None:
    if not (
        isinstance(statement, ast.Expr)
        and isinstance(statement.value, ast.Call)
    ):
        return None

    state = _call_execution_state(
        visitor,
        statement.value,
        parameterized=parameterized,
    )
    if state == _RAISES:
        return prior._statement_risk_marker("call-raises")
    if state == _UNKNOWN:
        return prior._statement_risk_marker("call-may-fail")
    return None


def _static_truth(
    visitor,
    test: ast.AST,
    *,
    parameterized: bool,
) -> bool | None:
    constants = assignment_scope._constants(
        visitor,
        parameterized=parameterized,
    )
    value = assignment_scope._static_value(test, constants)
    if value is assignment_scope._STATIC_RAISES:
        return None
    if value is assignment_scope._STATIC_UNKNOWN:
        return None
    try:
        return bool(value)
    except Exception:
        return None


def _expression_value_state(
    visitor,
    value: ast.AST,
    *,
    parameterized: bool,
) -> str:
    if isinstance(value, ast.Call):
        return _call_execution_state(
            visitor,
            value,
            parameterized=parameterized,
        )
    return target_layer._expression_state(
        visitor,
        value,
        parameterized=parameterized,
    )


def _branch_block_state(
    visitor,
    statements: list[ast.stmt],
    *,
    parameterized: bool,
) -> str:
    result = _SAFE

    for statement in statements:
        if isinstance(statement, ast.Raise):
            return _RAISES

        if isinstance(statement, (ast.Return, ast.Break, ast.Continue)):
            # This path does not complete into the following outer statement.
            # It is not a guaranteed exception, but it is an execution boundary.
            return _UNKNOWN

        if isinstance(statement, ast.Expr):
            state = _expression_value_state(
                visitor,
                statement.value,
                parameterized=parameterized,
            )
            if state == _RAISES:
                return _RAISES
            if state == _UNKNOWN:
                result = _UNKNOWN
            continue

        if isinstance(statement, ast.Assert):
            state = prior.prior._assert_static_state(
                visitor,
                statement,
                parameterized=parameterized,
            )
            if state == _RAISES:
                return _RAISES
            if state == _UNKNOWN:
                result = _UNKNOWN
            continue

        if isinstance(statement, (ast.Assign, ast.AnnAssign, ast.AugAssign)):
            value = statement.value
            state = _expression_value_state(
                visitor,
                value,
                parameterized=parameterized,
            )
            if state == _RAISES:
                return _RAISES
            if state == _UNKNOWN:
                result = _UNKNOWN
            continue

        if isinstance(statement, ast.If):
            state = _if_execution_state(
                visitor,
                statement,
                parameterized=parameterized,
            )
            if state == _RAISES:
                return _RAISES
            if state == _UNKNOWN:
                result = _UNKNOWN
            continue

        if isinstance(statement, (ast.Import, ast.ImportFrom, ast.Delete)):
            # Import resolution and deletion can fail at runtime. The straight-
            # line layers already model these forms; branch propagation must not
            # silently erase the same execution boundary merely because they sit
            # inside an if-body.
            result = _UNKNOWN

    return result


def _if_execution_state(
    visitor,
    statement: ast.If,
    *,
    parameterized: bool,
) -> str:
    test_state = target_layer._expression_state(
        visitor,
        statement.test,
        parameterized=parameterized,
    )
    if test_state == _RAISES:
        return _RAISES

    truth = _static_truth(
        visitor,
        statement.test,
        parameterized=parameterized,
    )
    if truth is True:
        branch_state = _branch_block_state(
            visitor,
            statement.body,
            parameterized=parameterized,
        )
    elif truth is False:
        branch_state = _branch_block_state(
            visitor,
            statement.orelse,
            parameterized=parameterized,
        )
    else:
        branch_state = _merge_alternative_states(
            [
                _branch_block_state(
                    visitor,
                    statement.body,
                    parameterized=parameterized,
                ),
                _branch_block_state(
                    visitor,
                    statement.orelse,
                    parameterized=parameterized,
                ),
            ]
        )

    if test_state == _UNKNOWN and branch_state == _SAFE:
        return _UNKNOWN
    if test_state == _UNKNOWN and branch_state == _RAISES:
        return _UNKNOWN
    return branch_state


def _if_prerequisite(
    visitor,
    statement: ast.stmt,
    *,
    parameterized: bool,
) -> ast.AST | None:
    if not isinstance(statement, ast.If):
        return None

    state = _if_execution_state(
        visitor,
        statement,
        parameterized=parameterized,
    )
    if state == _RAISES:
        return prior._statement_risk_marker("if-raises")
    if state == _UNKNOWN:
        return prior._statement_risk_marker("if-may-fail")
    return None


def _literal_blocking_prerequisite(
    visitor,
    statement: ast.stmt,
) -> ast.AST | None:
    existing = _previous_literal_blocking_prerequisite(visitor, statement)
    parts: list[ast.AST] = []
    if existing is not None:
        parts.append(existing)

    if existing is None:
        dynamic_call = _standalone_call_prerequisite(
            visitor,
            statement,
            parameterized=False,
        )
        if dynamic_call is not None:
            parts.append(dynamic_call)

    branch = _if_prerequisite(
        visitor,
        statement,
        parameterized=False,
    )
    if branch is not None:
        parts.append(branch)

    return target_layer._combine_prerequisites(parts)


def _parameterized_blocking_prerequisite(
    visitor,
    statement: ast.stmt,
) -> ast.AST | None:
    existing = _previous_parameterized_blocking_prerequisite(visitor, statement)
    parts: list[ast.AST] = []
    if existing is not None:
        parts.append(existing)

    if existing is None:
        dynamic_call = _standalone_call_prerequisite(
            visitor,
            statement,
            parameterized=True,
        )
        if dynamic_call is not None:
            parts.append(dynamic_call)

    branch = _if_prerequisite(
        visitor,
        statement,
        parameterized=True,
    )
    if branch is not None:
        parts.append(branch)

    return target_layer._combine_prerequisites(parts)


target_layer._literal_blocking_prerequisite = _literal_blocking_prerequisite
target_layer._parameterized_blocking_prerequisite = (
    _parameterized_blocking_prerequisite
)


class ReleaseCandidateDynamicCallAndBranchPrerequisiteTests(unittest.TestCase):
    def test_dynamic_callback_statement_changes_literal_and_sink_contracts(self) -> None:
        direct = '''
def run(findings, callback):
    findings.append(Finding("PUBLIC_CODE", "message"))
'''
        preceded = '''
def run(findings, callback):
    callback()
    findings.append(Finding("PUBLIC_CODE", "message"))
'''
        expected = literal_base.finding_semantic_signatures(direct)
        actual = literal_base.finding_semantic_signatures(preceded)
        self.assertNotEqual(expected, actual)
        self.assertTrue(
            any("statement-execution:call-may-fail" in item for item in actual["PUBLIC_CODE"])
        )
        self.assertNotEqual(
            sink_execution.finding_semantic_signatures_with_sink(direct),
            sink_execution.finding_semantic_signatures_with_sink(preceded),
        )

    def test_dynamic_callback_statement_changes_parameterized_contract(self) -> None:
        direct = '''
def read_text(path, findings, code):
    Finding(code, "decode failed", path="sample")
def validate(root, findings, callback):
    read_text(root / "LICENSE", findings, "LICENSE_ENCODING")
'''
        preceded = '''
def read_text(path, findings, code):
    Finding(code, "decode failed", path="sample")
def validate(root, findings, callback):
    callback()
    read_text(root / "LICENSE", findings, "LICENSE_ENCODING")
'''
        self.assertNotEqual(
            parameterized_active.parameterized_finding_contracts(direct, "sample.py"),
            parameterized_active.parameterized_finding_contracts(preceded, "sample.py"),
        )

    def test_proven_nonaborting_same_module_helper_remains_compatible(self) -> None:
        direct = '''
def run(findings):
    findings.append(Finding("PUBLIC_CODE", "message"))
'''
        preceded = '''
def harmless():
    return 1

def run(findings):
    harmless()
    findings.append(Finding("PUBLIC_CODE", "message"))
'''
        self.assertEqual(
            literal_base.finding_semantic_signatures(direct),
            literal_base.finding_semantic_signatures(preceded),
        )

    def test_potentially_failing_if_branch_changes_literal_and_sink_contracts(self) -> None:
        direct = '''
def run(findings, flag):
    findings.append(Finding("PUBLIC_CODE", "message"))
'''
        preceded = '''
def explode():
    raise RuntimeError("stop")

def run(findings, flag):
    if flag:
        explode()
    findings.append(Finding("PUBLIC_CODE", "message"))
'''
        expected = literal_base.finding_semantic_signatures(direct)
        actual = literal_base.finding_semantic_signatures(preceded)
        self.assertNotEqual(expected, actual)
        self.assertTrue(
            any("statement-execution:if-may-fail" in item for item in actual["PUBLIC_CODE"])
        )
        self.assertNotEqual(
            sink_execution.finding_semantic_signatures_with_sink(direct),
            sink_execution.finding_semantic_signatures_with_sink(preceded),
        )

    def test_potentially_failing_if_branch_changes_parameterized_contract(self) -> None:
        direct = '''
def read_text(path, findings, code):
    Finding(code, "decode failed", path="sample")
def validate(root, findings, flag):
    read_text(root / "LICENSE", findings, "LICENSE_ENCODING")
'''
        preceded = '''
def read_text(path, findings, code):
    Finding(code, "decode failed", path="sample")
def explode():
    raise RuntimeError("stop")
def validate(root, findings, flag):
    if flag:
        explode()
    read_text(root / "LICENSE", findings, "LICENSE_ENCODING")
'''
        self.assertNotEqual(
            parameterized_active.parameterized_finding_contracts(direct, "sample.py"),
            parameterized_active.parameterized_finding_contracts(preceded, "sample.py"),
        )

    def test_statically_dead_failing_branch_does_not_freeze_detail(self) -> None:
        direct = '''
def run(findings):
    findings.append(Finding("PUBLIC_CODE", "message"))
'''
        preceded = '''
def explode():
    raise RuntimeError("stop")

def run(findings):
    if False:
        explode()
    findings.append(Finding("PUBLIC_CODE", "message"))
'''
        self.assertEqual(
            literal_base.finding_semantic_signatures(direct),
            literal_base.finding_semantic_signatures(preceded),
        )

    def test_nonaborting_branch_remains_compatible(self) -> None:
        direct = '''
def run(findings, flag):
    findings.append(Finding("PUBLIC_CODE", "message"))
'''
        preceded = '''
def harmless():
    return 1

def run(findings, flag):
    if flag:
        harmless()
    findings.append(Finding("PUBLIC_CODE", "message"))
'''
        self.assertEqual(
            literal_base.finding_semantic_signatures(direct),
            literal_base.finding_semantic_signatures(preceded),
        )


if __name__ == "__main__":
    unittest.main()
