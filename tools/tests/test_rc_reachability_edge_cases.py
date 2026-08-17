from __future__ import annotations

import ast
import unittest
from collections import Counter

import test_rc_extended_finding_reachability as literal
import test_rc_parameterized_finding_reachability as parameterized
from rc_reachability_semantics import statement_always_terminates


class ReleaseCandidateReachabilityEdgeCaseTests(unittest.TestCase):
    def test_statically_unreachable_break_does_not_make_infinite_loop_fall_through(self):
        literal_source = '''
def validate():
    while True:
        if False:
            break
    Finding("PUBLIC_CODE", "unreachable")
'''
        self.assertEqual(
            literal.reachable_contracts(literal_source, "sample.py"),
            Counter(),
        )

        parameterized_source = '''
def read_text(path, findings, code):
    Finding(code, "decode failed", path="sample")
def validate(root, findings):
    while True:
        if False:
            break
    read_text(root / "LICENSE", findings, "LICENSE_ENCODING")
'''
        self.assertEqual(
            parameterized.reachable_parameterized_contracts(
                parameterized_source, "sample.py"
            ),
            set(),
        )

    def test_non_raising_return_in_try_makes_successor_unreachable(self):
        literal_source = '''
def validate():
    try:
        return None
    except ValueError:
        pass
    Finding("PUBLIC_CODE", "unreachable")
'''
        self.assertEqual(
            literal.reachable_contracts(literal_source, "sample.py"),
            Counter(),
        )

        parameterized_source = '''
def read_text(path, findings, code):
    Finding(code, "decode failed", path="sample")
def validate(root, findings):
    try:
        return None
    except ValueError:
        pass
    read_text(root / "LICENSE", findings, "LICENSE_ENCODING")
'''
        self.assertEqual(
            parameterized.reachable_parameterized_contracts(
                parameterized_source, "sample.py"
            ),
            set(),
        )

    def test_non_raising_return_in_with_makes_successor_unreachable(self):
        literal_source = '''
def validate():
    with nullcontext():
        return None
    Finding("PUBLIC_CODE", "unreachable")
'''
        self.assertEqual(
            literal.reachable_contracts(literal_source, "sample.py"),
            Counter(),
        )

        parameterized_source = '''
def read_text(path, findings, code):
    Finding(code, "decode failed", path="sample")
def validate(root, findings):
    with nullcontext():
        return None
    read_text(root / "LICENSE", findings, "LICENSE_ENCODING")
'''
        self.assertEqual(
            parameterized.reachable_parameterized_contracts(
                parameterized_source, "sample.py"
            ),
            set(),
        )

    def test_non_raising_return_in_async_with_is_terminal(self):
        tree = ast.parse(
            '''
async def validate():
    async with guard():
        return None
'''
        )
        function = tree.body[0]
        self.assertIsInstance(function, ast.AsyncFunctionDef)
        self.assertTrue(statement_always_terminates(function.body[0]))

    def test_raise_in_with_remains_conservatively_fallthrough_capable(self):
        source = '''
def validate():
    with suppress(Exception):
        raise ValueError("suppressed")
    Finding("PUBLIC_CODE", "reachable")
'''
        contracts = literal.reachable_contracts(source, "sample.py")
        self.assertEqual(
            contracts[("sample.py", "validate", "PUBLIC_CODE")],
            1,
            "a context manager may suppress an exception, so a raise-only with body cannot be treated as terminal",
        )

    def test_finally_continue_overrides_pending_outer_break(self):
        literal_source = '''
def validate():
    while True:
        try:
            break
        finally:
            continue
    Finding("PUBLIC_CODE", "unreachable")
'''
        self.assertEqual(
            literal.reachable_contracts(literal_source, "sample.py"),
            Counter(),
        )

        parameterized_source = '''
def read_text(path, findings, code):
    Finding(code, "decode failed", path="sample")
def validate(root, findings):
    while True:
        try:
            break
        finally:
            continue
    read_text(root / "LICENSE", findings, "LICENSE_ENCODING")
'''
        self.assertEqual(
            parameterized.reachable_parameterized_contracts(
                parameterized_source, "sample.py"
            ),
            set(),
        )

    def test_finally_break_overrides_pending_continue(self):
        literal_source = '''
def validate():
    while True:
        try:
            continue
        finally:
            break
    Finding("PUBLIC_CODE", "reachable")
'''
        contracts = literal.reachable_contracts(literal_source, "sample.py")
        self.assertEqual(
            contracts[("sample.py", "validate", "PUBLIC_CODE")],
            1,
        )


if __name__ == "__main__":
    unittest.main()
