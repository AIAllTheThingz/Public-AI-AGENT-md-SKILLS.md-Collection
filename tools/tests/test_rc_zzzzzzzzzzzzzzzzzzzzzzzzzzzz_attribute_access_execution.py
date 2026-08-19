from __future__ import annotations

import ast
import inspect
import json
import unittest
from collections import Counter
from typing import Any

import rc_finding_code_contracts_base as literal_base
import test_rc_extended_finding_reachability as extended_reachability
import test_rc_finding_reachability as basic_reachability
import test_rc_parameterized_finding_codes as parameterized_active
import test_rc_parameterized_finding_reachability as parameterized_reachability
import test_rc_zzz_finding_emission_sink as sink_execution
import test_rc_zzzzzzzzzzzz_execution_prerequisites as prerequisite_execution
import test_rc_zzzzzzzzzzzzzzzzzzz_post_emission_completion as completion_execution
import test_rc_zzzzzzzzzzzzzzzzzzzzzzzzzzz_left_to_right_expression_execution as left_to_right


# Attribute lookup is executable. A structurally simple receiver does not prove
# that ``receiver.attribute`` succeeds: ``None.missing`` raises before any later
# sibling expression can execute. Strengthen only execution-state classification
# so existing deferred lambda/nested-function semantics remain intact.

_PREVIOUS_EXECUTION_STATE = left_to_right._execution_state

# Values produced by the static evaluator are deliberately limited to ordinary
# immutable/container builtins. ``inspect.getattr_static`` checks lookup
# availability without invoking descriptors or user code.
_STATIC_ATTRIBUTE_RECEIVER_TYPES = (
    type(None),
    bool,
    int,
    float,
    complex,
    str,
    bytes,
    tuple,
    list,
    dict,
    set,
    frozenset,
    range,
)


def _attribute_execution_state(
    node: ast.Attribute,
    constants: dict[str, Any],
) -> str:
    receiver = prerequisite_execution._static_eval(node.value, constants)
    if receiver is prerequisite_execution._STATIC_RAISES:
        return left_to_right._RAISES
    if receiver is prerequisite_execution._STATIC_UNKNOWN:
        return left_to_right._UNKNOWN

    if not isinstance(receiver, _STATIC_ATTRIBUTE_RECEIVER_TYPES):
        return left_to_right._UNKNOWN

    try:
        inspect.getattr_static(receiver, node.attr)
    except AttributeError:
        return left_to_right._RAISES
    return left_to_right._SAFE


def _execution_state(node: ast.AST, constants: dict[str, Any]) -> str:
    attribute_states = [
        _attribute_execution_state(item, constants)
        for item in ast.walk(node)
        if isinstance(item, ast.Attribute)
    ]
    if left_to_right._RAISES in attribute_states:
        return left_to_right._RAISES
    if left_to_right._UNKNOWN in attribute_states:
        return left_to_right._UNKNOWN
    return _PREVIOUS_EXECUTION_STATE(node, constants)


# The sequence visitors installed by the preceding layer resolve this global
# dynamically. Do not replace ``_structurally_safe``: doing so changes deferred
# callable execution semantics outside the left-to-right prerequisite boundary.
left_to_right._execution_state = _execution_state


class ReleaseCandidateAttributeAccessExecutionTests(unittest.TestCase):
    def test_known_missing_attribute_hides_later_literal_finding(self) -> None:
        source = '''
def validate(findings):
    obj = None
    (obj.missing, findings.append(Finding("PUBLIC_CODE", "hidden")))
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
            basic_reachability.reachable_contracts(source, "sample.py"),
            Counter(),
        )
        self.assertEqual(
            extended_reachability.reachable_contracts(source, "sample.py"),
            Counter(),
        )
        self.assertEqual(
            sink_execution.reachable_emission_contracts(source, "sample.py"),
            Counter(),
        )
        normal, abnormal = completion_execution._completion_counts(
            source,
            "sample.py",
        )
        key = ("sample.py", "validate", "PUBLIC_CODE")
        self.assertEqual(normal[key], 0)
        self.assertEqual(abnormal[key], 0)

    def test_known_missing_attribute_hides_parameterized_finding_call(self) -> None:
        source = '''
def read_text(path, findings, code):
    Finding(code, "decode failed", path="sample")
def validate(root, findings):
    obj = None
    (obj.missing, read_text(root / "LICENSE", findings, "LICENSE_ENCODING"))
'''
        self.assertEqual(
            parameterized_active.parameterized_finding_contracts(
                source,
                "sample.py",
            ),
            set(),
        )
        self.assertEqual(
            parameterized_reachability.reachable_parameterized_contracts(
                source,
                "sample.py",
            ),
            set(),
        )

    def test_unknown_attribute_adds_execution_prerequisite(self) -> None:
        direct = '''
def validate(obj, findings):
    findings.append(Finding("PUBLIC_CODE", "visible"))
'''
        guarded = '''
def validate(obj, findings):
    (obj.value, findings.append(Finding("PUBLIC_CODE", "visible")))
'''
        expected = literal_base.finding_semantic_signatures(direct)
        actual = literal_base.finding_semantic_signatures(guarded)
        self.assertNotEqual(expected, actual)
        payload = json.loads(actual["PUBLIC_CODE"][0])
        self.assertTrue(
            any(
                marker.startswith("tuple:1:requires-prior-evaluation")
                for marker in payload["context"]
            )
        )

    def test_nested_unknown_attribute_is_an_execution_prerequisite(self) -> None:
        direct = '''
def validate(obj, findings):
    findings.append(Finding("PUBLIC_CODE", "visible"))
'''
        guarded = '''
def validate(obj, findings):
    (obj.value + 1, findings.append(Finding("PUBLIC_CODE", "visible")))
'''
        self.assertNotEqual(
            literal_base.finding_semantic_signatures(direct),
            literal_base.finding_semantic_signatures(guarded),
        )

    def test_known_existing_builtin_attribute_is_not_false_positive(self) -> None:
        direct = '''
def validate(findings):
    findings.append(Finding("PUBLIC_CODE", "visible"))
'''
        guarded = '''
def validate(findings):
    value = "text"
    (value.upper, findings.append(Finding("PUBLIC_CODE", "visible")))
'''
        self.assertEqual(
            literal_base.finding_semantic_signatures(direct),
            literal_base.finding_semantic_signatures(guarded),
        )


if __name__ == "__main__":
    unittest.main()
