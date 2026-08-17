from __future__ import annotations

import unittest
from collections import Counter

import test_rc_extended_finding_reachability as literal
import test_rc_parameterized_finding_reachability as parameterized


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


if __name__ == "__main__":
    unittest.main()
