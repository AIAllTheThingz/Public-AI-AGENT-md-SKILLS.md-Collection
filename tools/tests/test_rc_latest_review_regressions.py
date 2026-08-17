from __future__ import annotations

import ast
import json
import unittest
from collections import Counter

import rc_finding_code_contracts_base as finding_base
import test_rc_extended_finding_reachability as literal
import test_rc_parameterized_finding_reachability as parameterized


class ReleaseCandidateLatestReviewRegressions(unittest.TestCase):
    def test_false_match_guard_break_does_not_make_infinite_loop_fall_through(self):
        literal_source = '''
def validate(value):
    while True:
        match value:
            case _ if False:
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
def validate(root, findings, value):
    while True:
        match value:
            case _ if False:
                break
    read_text(root / "LICENSE", findings, "LICENSE_ENCODING")
'''
        self.assertEqual(
            parameterized.reachable_parameterized_contracts(
                parameterized_source, "sample.py"
            ),
            set(),
        )

    @unittest.skipUnless(hasattr(ast, "TryStar"), "requires Python exception groups")
    def test_try_star_regions_have_distinct_literal_finding_contexts(self):
        source = '''
def validate():
    try:
        Finding("PUBLIC_CODE", "body", path="body")
    except* ValueError:
        Finding("PUBLIC_CODE", "handler", path="handler")
    else:
        Finding("PUBLIC_CODE", "else", path="else")
    finally:
        Finding("PUBLIC_CODE", "finally", path="finally")
'''
        signatures = finding_base.finding_semantic_signatures(source)["PUBLIC_CODE"]
        contexts = {
            tuple(json.loads(signature)["context"])
            for signature in signatures
        }
        self.assertEqual(
            contexts,
            {
                ("try-star",),
                ("except-star:Name('ValueError', Load())",),
                ("try-star-else",),
                ("try-star-finally",),
            },
        )

        ordinary = '''
def validate():
    Finding("PUBLIC_CODE", "ordinary", path="sample")
'''
        moved = '''
def validate():
    try:
        pass
    except* ValueError:
        Finding("PUBLIC_CODE", "moved", path="sample")
'''
        self.assertNotEqual(
            finding_base.finding_semantic_signatures(ordinary),
            finding_base.finding_semantic_signatures(moved),
        )


if __name__ == "__main__":
    unittest.main()
