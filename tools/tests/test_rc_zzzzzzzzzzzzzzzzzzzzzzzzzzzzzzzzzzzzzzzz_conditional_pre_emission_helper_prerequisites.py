from __future__ import annotations

import ast
import unittest

import test_rc_parameterized_finding_codes as parameterized_active
import test_rc_parameterized_finding_reachability as parameterized_reachability
import test_rc_zzz_finding_emission_sink as sink_execution
import test_rc_zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz_pre_emission_statement_prerequisites as prior


# The previous layer deliberately narrowed statement prerequisites after an
# over-broad implementation froze unrelated implementation details. Preserve
# that narrowness while closing the remaining gap: a same-module helper can
# return normally on some inputs and still raise on another reachable path.
# Such a helper is an execution prerequisite for a following published finding.


def _block_may_abort(
    statements: list[ast.stmt],
    definitions: dict[str, ast.AST],
    seen: set[str],
) -> bool:
    constants: dict[str, object] = {}

    for statement in statements:
        if isinstance(statement, ast.Raise):
            return True
        if isinstance(statement, ast.Return):
            return False

        if isinstance(statement, ast.Expr):
            if prior._is_explicit_process_exit(statement.value):
                return True
            helper_name = prior._call_name(statement.value)
            if helper_name and _helper_may_abort(
                helper_name,
                definitions,
                seen,
            ):
                return True

        if isinstance(statement, ast.If):
            truth = prior._static_bool(statement.test)
            if truth is True:
                branches = (statement.body,)
            elif truth is False:
                branches = (statement.orelse,)
            else:
                branches = (statement.body, statement.orelse)

            if any(
                branch and _block_may_abort(branch, definitions, seen)
                for branch in branches
            ):
                return True

        # Do not inspect arbitrary unknown operations here. That was the source
        # of the earlier 35-signature regression. We only follow explicit local
        # exceptional paths, then use the existing reachability model to avoid
        # treating statements after an unconditional terminator as reachable.
        if parameterized_reachability.statement_always_terminates(
            statement,
            constants,
        ):
            return False
        parameterized_reachability.update_known_constants(statement, constants)

    return False


def _helper_may_abort(
    name: str,
    definitions: dict[str, ast.AST],
    seen: set[str] | None = None,
) -> bool:
    definition = definitions.get(name)
    # Calling async def only creates a coroutine at a synchronous call site.
    if not isinstance(definition, ast.FunctionDef):
        return False

    active = set(seen or ())
    if name in active:
        return False
    active.add(name)

    body = list(definition.body)
    if (
        body
        and isinstance(body[0], ast.Expr)
        and isinstance(body[0].value, ast.Constant)
        and isinstance(body[0].value.value, str)
    ):
        body = body[1:]

    return _block_may_abort(body, definitions, active)


_previous_literal_blocking_prerequisite = prior._literal_blocking_prerequisite
_previous_parameterized_blocking_prerequisite = prior._parameterized_blocking_prerequisite


def _literal_blocking_prerequisite(visitor, statement: ast.stmt) -> ast.AST | None:
    existing = _previous_literal_blocking_prerequisite(visitor, statement)
    if existing is not None:
        return existing
    if not isinstance(statement, ast.Expr):
        return None
    helper_name = prior._call_name(statement.value)
    if helper_name is None:
        return None
    if _helper_may_abort(helper_name, visitor.module_definitions):
        return statement.value
    return None


def _parameterized_blocking_prerequisite(
    visitor,
    statement: ast.stmt,
) -> ast.AST | None:
    existing = _previous_parameterized_blocking_prerequisite(visitor, statement)
    if existing is not None:
        return existing
    if not isinstance(statement, ast.Expr):
        return None
    helper_name = prior._call_name(statement.value)
    if helper_name is None:
        return None
    if _helper_may_abort(helper_name, visitor.definitions):
        return statement.value
    return None


# The block visitors installed by the prior layer resolve these helpers through
# that module's globals at runtime, so updating the globals composes this fix
# without replacing the already-proven import and guaranteed-abort behavior.
prior._literal_blocking_prerequisite = _literal_blocking_prerequisite
prior._parameterized_blocking_prerequisite = _parameterized_blocking_prerequisite


class ReleaseCandidateConditionalPreEmissionHelperTests(unittest.TestCase):
    def test_conditionally_raising_helper_changes_literal_and_sink_contracts(self) -> None:
        direct = '''
from standards_tools import Finding

def run(findings, flag):
    findings.append(Finding("PUBLIC_CODE", "message"))
'''
        preceded = '''
from standards_tools import Finding

def maybe_stop(flag):
    if flag:
        raise RuntimeError("stop")
    return 1

def run(findings, flag):
    maybe_stop(flag)
    findings.append(Finding("PUBLIC_CODE", "message"))
'''
        self.assertNotEqual(
            prior.literal_base.finding_semantic_signatures(direct),
            prior.literal_base.finding_semantic_signatures(preceded),
        )
        self.assertNotEqual(
            sink_execution.finding_semantic_signatures_with_sink(direct),
            sink_execution.finding_semantic_signatures_with_sink(preceded),
        )

    def test_conditionally_raising_helper_changes_parameterized_contracts(self) -> None:
        direct = '''
def read_text(path, findings, code):
    Finding(code, "decode failed", path="sample")
def validate(root, findings, flag):
    read_text(root / "LICENSE", findings, "LICENSE_ENCODING")
'''
        preceded = '''
def read_text(path, findings, code):
    Finding(code, "decode failed", path="sample")
def maybe_stop(flag):
    if flag:
        raise RuntimeError("stop")
    return 1
def validate(root, findings, flag):
    maybe_stop(flag)
    read_text(root / "LICENSE", findings, "LICENSE_ENCODING")
'''
        self.assertNotEqual(
            parameterized_active.parameterized_finding_contracts(
                direct,
                "sample.py",
            ),
            parameterized_active.parameterized_finding_contracts(
                preceded,
                "sample.py",
            ),
        )
        self.assertNotEqual(
            parameterized_reachability.reachable_parameterized_contracts(
                direct,
                "sample.py",
            ),
            parameterized_reachability.reachable_parameterized_contracts(
                preceded,
                "sample.py",
            ),
        )

    def test_transitively_conditional_abort_is_preserved(self) -> None:
        direct = '''
from standards_tools import Finding

def run(findings, flag):
    findings.append(Finding("PUBLIC_CODE", "message"))
'''
        preceded = '''
from standards_tools import Finding

def maybe_stop(flag):
    if flag:
        raise RuntimeError("stop")
    return 1
def wrapper(flag):
    maybe_stop(flag)
def run(findings, flag):
    wrapper(flag)
    findings.append(Finding("PUBLIC_CODE", "message"))
'''
        self.assertNotEqual(
            prior.literal_base.finding_semantic_signatures(direct),
            prior.literal_base.finding_semantic_signatures(preceded),
        )

    def test_statically_unreachable_raise_does_not_freeze_normal_helper(self) -> None:
        direct = '''
from standards_tools import Finding

def run(findings, flag):
    findings.append(Finding("PUBLIC_CODE", "message"))
'''
        preceded = '''
from standards_tools import Finding

def observe(flag):
    if False:
        raise RuntimeError("unreachable")
    return flag

def run(findings, flag):
    observe(flag)
    findings.append(Finding("PUBLIC_CODE", "message"))
'''
        self.assertEqual(
            prior.literal_base.finding_semantic_signatures(direct),
            prior.literal_base.finding_semantic_signatures(preceded),
        )


if __name__ == "__main__":
    unittest.main()
