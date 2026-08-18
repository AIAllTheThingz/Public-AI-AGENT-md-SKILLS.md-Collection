from __future__ import annotations

import ast
import unittest
from collections import Counter
from typing import Any

import rc_reachability_semantics as semantics
import test_rc_extended_finding_reachability as extended_reachability
import test_rc_finding_reachability as basic_reachability
import test_rc_parameterized_finding_reachability as parameterized_reachability
import test_rc_zzzzzzz_conditional_expression_execution as conditional_execution  # noqa: F401


_NEXT = "next"
_EXIT_SCOPE = "exit-scope"
_BREAK_LOOP = "break-loop"
_CONTINUE_LOOP = "continue-loop"


def _static_int(node: ast.AST, constants: dict[str, Any]) -> int | None:
    value = semantics.static_value(node, constants)
    if isinstance(value, int):
        return value
    return None


def _iterable_definitely_nonempty(
    node: ast.AST,
    constants: dict[str, Any],
) -> bool:
    """Recognize only iterables whose non-emptiness is certain without execution."""

    if isinstance(node, (ast.Tuple, ast.List, ast.Set)):
        return bool(node.elts)

    if isinstance(node, ast.Dict):
        # A concrete key guarantees at least one resulting mapping entry. Pure
        # ``**mapping`` construction remains unknown because the mapping may be empty.
        return any(key is not None for key in node.keys)

    if isinstance(node, ast.Constant):
        return isinstance(node.value, (str, bytes)) and len(node.value) > 0

    if isinstance(node, ast.Name):
        value = constants.get(node.id, semantics.UNKNOWN)
        if isinstance(value, (str, bytes, tuple, list, set, frozenset, dict, range)):
            return len(value) > 0
        return False

    if (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "range"
        and not node.keywords
        and 1 <= len(node.args) <= 3
    ):
        arguments = [_static_int(argument, constants) for argument in node.args]
        if any(argument is None for argument in arguments):
            return False
        try:
            return len(range(*arguments)) > 0
        except (TypeError, ValueError):
            return False

    return False


def _block_outcomes(
    statements: list[ast.stmt],
    constants: dict[str, Any],
) -> set[str]:
    """Return conservative first-iteration control outcomes for a loop body."""

    state = dict(constants)
    outcomes: set[str] = {_NEXT}

    for statement in statements:
        if _NEXT not in outcomes:
            break

        statement_outcomes = _statement_outcomes(statement, state)
        outcomes.remove(_NEXT)
        outcomes.update(statement_outcomes)

        if _NEXT in statement_outcomes:
            semantics.update_known_constants(statement, state)

    return outcomes


def _statement_outcomes(
    node: ast.stmt,
    constants: dict[str, Any],
) -> set[str]:
    if isinstance(node, (ast.Return, ast.Raise)):
        return {_EXIT_SCOPE}

    if isinstance(node, ast.Break):
        return {_BREAK_LOOP}

    if isinstance(node, ast.Continue):
        return {_CONTINUE_LOOP}

    if semantics._explicit_process_exit(node) is not None:
        return {_EXIT_SCOPE}

    if isinstance(node, ast.Assert):
        if semantics.static_truth(node.test, constants) is False:
            return {_EXIT_SCOPE}
        return {_NEXT}

    if isinstance(node, ast.If):
        truth = semantics.static_truth(node.test, constants)
        if truth is True:
            return _block_outcomes(node.body, constants)
        if truth is False:
            return _block_outcomes(node.orelse, constants) if node.orelse else {_NEXT}

        positive = _block_outcomes(node.body, constants)
        negative = _block_outcomes(node.orelse, constants) if node.orelse else {_NEXT}
        return positive | negative

    if isinstance(node, ast.While):
        truth = semantics.static_truth(node.test, constants)
        if truth is False:
            return _block_outcomes(node.orelse, constants) if node.orelse else {_NEXT}
        if truth is True and not semantics.loop_body_has_break(node.body, constants):
            # The loop either exits the enclosing scope from its body or never
            # reaches the following statement. Both make the successor unreachable.
            return {_EXIT_SCOPE}
        return {_NEXT}

    if isinstance(node, ast.For):
        if _iterable_definitely_nonempty(node.iter, constants):
            body_outcomes = _block_outcomes(node.body, constants)
            if body_outcomes == {_EXIT_SCOPE}:
                return {_EXIT_SCOPE}
        return {_NEXT}

    if isinstance(node, ast.AsyncFor):
        # Async iteration can execute arbitrary protocol code; do not infer
        # non-emptiness from syntax alone.
        return {_NEXT}

    if isinstance(node, (ast.With, ast.AsyncWith)):
        # A context manager may suppress an exception raised by its body. Preserve
        # explicit loop control, but otherwise remain conservative about fallthrough.
        body_outcomes = _block_outcomes(node.body, constants)
        propagated = body_outcomes & {_BREAK_LOOP, _CONTINUE_LOOP}
        return propagated | {_NEXT}

    # Try/try*, match, and arbitrary executable statements are deliberately left
    # conservative here. The proof only needs to recognize a guaranteed exit; an
    # unknown statement cannot justify declaring the loop terminal.
    return {_NEXT}


_previous_statement_always_terminates = semantics.statement_always_terminates


def _statement_always_terminates(
    node: ast.stmt,
    constants: dict[str, Any] | None = None,
) -> bool:
    state = {} if constants is None else constants

    if isinstance(node, ast.For) and _iterable_definitely_nonempty(node.iter, state):
        if _block_outcomes(node.body, state) == {_EXIT_SCOPE}:
            return True

    return _previous_statement_always_terminates(node, state)


# Install the stronger shared reachability predicate everywhere earlier scanner
# modules imported it by value. Later execution overlays subclass these visitors,
# so they inherit the corrected loop semantics without replacing their BoolOp,
# IfExp, generator, async, lexical-scope, or sink behavior.
semantics.statement_always_terminates = _statement_always_terminates
basic_reachability.statement_always_terminates = _statement_always_terminates
extended_reachability.statement_always_terminates = _statement_always_terminates
parameterized_reachability.statement_always_terminates = _statement_always_terminates


class ReleaseCandidateGuaranteedNonemptyLoopExecutionTests(unittest.TestCase):
    def test_nonempty_literal_for_return_suppresses_literal_finding(self):
        source = '''
def validate(findings):
    for _ in (1,):
        return
    findings.append(Finding("PUBLIC_CODE", "unreachable"))
'''
        self.assertEqual(
            extended_reachability.reachable_contracts(source, "sample.py"),
            Counter(),
        )

    def test_nonempty_literal_for_return_suppresses_parameterized_call(self):
        source = '''
def read_text(path, findings, code):
    Finding(code, "decode failed", path="sample")
def validate(root, findings):
    for _ in [1]:
        return
    read_text(root / "LICENSE", findings, "LICENSE_ENCODING")
'''
        self.assertEqual(
            parameterized_reachability.reachable_parameterized_contracts(
                source,
                "sample.py",
            ),
            set(),
        )

    def test_empty_loop_does_not_suppress_successor(self):
        source = '''
def validate(findings):
    for _ in ():
        return
    findings.append(Finding("PUBLIC_CODE", "reachable"))
'''
        contracts = extended_reachability.reachable_contracts(source, "sample.py")
        self.assertEqual(contracts[("sample.py", "validate", "PUBLIC_CODE")], 1)

    def test_break_and_continue_do_not_count_as_enclosing_exit(self):
        templates = {
            "break": '''
def validate(findings):
    for _ in (1,):
        break
    findings.append(Finding("PUBLIC_CODE", "reachable"))
''',
            "continue": '''
def validate(findings):
    for _ in (1,):
        continue
    findings.append(Finding("PUBLIC_CODE", "reachable"))
''',
        }
        for name, source in templates.items():
            with self.subTest(name=name):
                contracts = extended_reachability.reachable_contracts(
                    source,
                    "sample.py",
                )
                self.assertEqual(
                    contracts[("sample.py", "validate", "PUBLIC_CODE")],
                    1,
                )

    def test_all_if_paths_must_exit_on_first_iteration(self):
        terminating = '''
def validate(flag, findings):
    for _ in range(1):
        if flag:
            return
        else:
            raise RuntimeError("stop")
    findings.append(Finding("PUBLIC_CODE", "unreachable"))
'''
        fallthrough = '''
def validate(flag, findings):
    for _ in range(1):
        if flag:
            return
    findings.append(Finding("PUBLIC_CODE", "reachable"))
'''
        self.assertEqual(
            extended_reachability.reachable_contracts(terminating, "sample.py"),
            Counter(),
        )
        contracts = extended_reachability.reachable_contracts(
            fallthrough,
            "sample.py",
        )
        self.assertEqual(contracts[("sample.py", "validate", "PUBLIC_CODE")], 1)


if __name__ == "__main__":
    unittest.main()
