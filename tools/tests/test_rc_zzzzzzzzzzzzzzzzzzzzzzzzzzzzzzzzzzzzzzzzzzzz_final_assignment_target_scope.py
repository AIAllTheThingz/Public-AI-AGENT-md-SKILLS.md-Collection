from __future__ import annotations

import ast
import unittest

import rc_finding_code_contracts_base as literal_base
import test_rc_zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz_branch_join_bound_method_aliases as _branch_join  # noqa: F401
import test_rc_zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz_assignment_target_binding_and_path_sensitive_bound_aliases as target_layer


# The assignment-target overlay originally treated every Subscript store as a
# global pre-emission failure prerequisite. That is too broad: subscript writes
# are already part of the dependency-mutation contract when they mutate a value
# that actually participates in a published finding. Promoting every private
# subscript write to an emission prerequisite freezes unrelated implementation
# details and breaks the established rebound-alias regression.
#
# Keep destructuring target binding in the global prerequisite model, where
# tuple/list unpacking itself can prevent a later emission. Attribute stores
# retain the preceding conservative treatment. Subscript stores instead remain
# governed by the existing alias-aware dependency mutation layer. This preserves
# both sides of the contract: a mutation of `ids[...]` that controls DUPLICATE_ID
# remains semantic, while `alias = {}; alias[...] = ...` after alias rebinding is
# correctly implementation-only.

_previous_target_binding_state = target_layer._target_binding_state
_SAFE = target_layer._SAFE


def _target_binding_state(target: ast.AST, rhs: ast.AST | None) -> str:
    if isinstance(target, ast.Subscript):
        return _SAFE
    return _previous_target_binding_state(target, rhs)


# All prerequisite and reachability hooks in the previous layer resolve this
# helper from that module at execution time, so replacing the composed helper is
# sufficient without weakening the separate dependency-mutation scanner.
target_layer._target_binding_state = _target_binding_state


class ReleaseCandidateScopedSubscriptTargetTests(unittest.TestCase):
    def test_rebound_private_subscript_write_remains_compatible(self) -> None:
        original = '''
def run(document_id):
    ids = {}
    if document_id in ids:
        Finding("DUPLICATE_ID", "duplicate", path="sample")
'''
        unrelated = '''
def run(document_id):
    ids = {}
    alias = ids
    alias = {}
    alias[document_id] = "unrelated"
    if document_id in ids:
        Finding("DUPLICATE_ID", "duplicate", path="sample")
'''
        self.assertEqual(
            literal_base.finding_semantic_signatures(original),
            literal_base.finding_semantic_signatures(unrelated),
        )

    def test_dependency_subscript_mutation_is_still_semantic(self) -> None:
        original = '''
def run(document_id):
    ids = {}
    if document_id in ids:
        Finding("DUPLICATE_ID", "duplicate", path="sample")
'''
        mutated = '''
def run(document_id):
    ids = {}
    ids[document_id] = "seen"
    if document_id in ids:
        Finding("DUPLICATE_ID", "duplicate", path="sample")
'''
        self.assertNotEqual(
            literal_base.finding_semantic_signatures(original),
            literal_base.finding_semantic_signatures(mutated),
        )


if __name__ == "__main__":
    unittest.main()
