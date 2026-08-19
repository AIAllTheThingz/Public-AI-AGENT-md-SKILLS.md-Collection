from __future__ import annotations

import ast
import json
import unittest
from collections import Counter

import rc_finding_code_contracts_base as literal_base
import test_rc_extended_finding_reachability as extended_reachability
import test_rc_finding_reachability as basic_reachability
import test_rc_parameterized_finding_codes as parameterized_active
import test_rc_parameterized_finding_reachability as parameterized_reachability
import test_rc_zzz_finding_emission_sink as sink_execution
import test_rc_zzzz_sink_rebinding_and_parameterized_multiplicity as sink_state
import test_rc_zzzzzzzzzzzzzzzzzzzz_post_emission_sink_and_codeowners as post_sink
import test_rc_zzzzzzzzzzzzzzzzzzzzzzzzzz_assigned_callable_sink_destructors as _assigned_callable  # noqa: F401
import test_rc_zzzzzzzzzzzzzzzzzzzzzzzzzzz_left_to_right_expression_execution as left_to_right
import test_rc_zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz_final_p1_and_ci_composition as final_composition
import test_rc_zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz_conditional_pre_emission_helper_prerequisites as statement_prerequisites


# Final composition for the latest PR #71 review findings:
#
# * Assignment RHS expressions execute before their binding is committed. A
#   potentially raising RHS therefore participates in the execution contract of
#   a later published finding even when it is not a direct same-module helper
#   call. Reuse the fully composed expression-state evaluator so safe literal
#   assignments stay editorial implementation detail.
# * A destructive sink method can be captured as a local bound callable and
#   invoked later (for example ``clear = findings.clear; clear()``). Preserve
#   that post-emission sink effect while allowing the private alias name itself
#   to change and honoring later rebinding.


# ---------------------------------------------------------------------------
# Assignment RHS execution prerequisites
# ---------------------------------------------------------------------------

_previous_literal_prerequisite = (
    statement_prerequisites.prior._literal_blocking_prerequisite
)
_previous_parameterized_prerequisite = (
    statement_prerequisites.prior._parameterized_blocking_prerequisite
)


def _assignment_rhs(statement: ast.stmt) -> ast.AST | None:
    if isinstance(statement, ast.Assign):
        return statement.value
    if isinstance(statement, ast.AnnAssign):
        return statement.value
    return None


def _known_same_module_function_call(visitor, node: ast.AST) -> bool:
    if not (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
    ):
        return False

    for attribute in ("module_definitions", "definitions"):
        bindings = getattr(visitor, attribute, None)
        if not isinstance(bindings, dict):
            continue
        definition = bindings.get(node.func.id)
        if isinstance(definition, (ast.FunctionDef, ast.AsyncFunctionDef)):
            return True
    return False


def _assignment_rhs_prerequisite(
    visitor,
    statement: ast.stmt,
    *,
    parameterized: bool,
) -> ast.AST | None:
    rhs = _assignment_rhs(statement)
    if rhs is None:
        return None

    # A direct same-module helper call is already analyzed by the preceding
    # helper layer. If that layer did not mark it, keep its deliberate
    # non-freezing behavior instead of classifying every ordinary helper call as
    # an opaque executable prerequisite.
    if _known_same_module_function_call(visitor, rhs):
        return None

    constants = (
        left_to_right._parameterized_constants(visitor)
        if parameterized
        else left_to_right._literal_constants(visitor)
    )
    state = final_composition._visitor_execution_state(visitor, rhs, constants)
    if state in {left_to_right._UNKNOWN, left_to_right._RAISES}:
        return rhs
    return None


def _literal_blocking_prerequisite(visitor, statement: ast.stmt) -> ast.AST | None:
    existing = _previous_literal_prerequisite(visitor, statement)
    if existing is not None:
        return existing
    return _assignment_rhs_prerequisite(
        visitor,
        statement,
        parameterized=False,
    )


def _parameterized_blocking_prerequisite(
    visitor,
    statement: ast.stmt,
) -> ast.AST | None:
    existing = _previous_parameterized_prerequisite(visitor, statement)
    if existing is not None:
        return existing
    return _assignment_rhs_prerequisite(
        visitor,
        statement,
        parameterized=True,
    )


# The block visitors installed by the prior statement layer resolve these names
# from that module at execution time. Replace both public composition hooks so
# semantic, sink-aware, parameterized, and reachable-parameterized traversal use
# the same stronger assignment prerequisite model.
statement_prerequisites._literal_blocking_prerequisite = (
    _literal_blocking_prerequisite
)
statement_prerequisites._parameterized_blocking_prerequisite = (
    _parameterized_blocking_prerequisite
)
statement_prerequisites.prior._literal_blocking_prerequisite = (
    _literal_blocking_prerequisite
)
statement_prerequisites.prior._parameterized_blocking_prerequisite = (
    _parameterized_blocking_prerequisite
)


# ---------------------------------------------------------------------------
# Local aliases of destructive bound sink methods
# ---------------------------------------------------------------------------

_previous_sink_contract = sink_execution._emission_sink_contract


def _simple_assignment_targets(statement: ast.stmt) -> list[str]:
    targets: list[ast.AST]
    if isinstance(statement, ast.Assign):
        targets = list(statement.targets)
    elif isinstance(statement, ast.AnnAssign):
        targets = [statement.target]
    else:
        return []
    return [target.id for target in targets if isinstance(target, ast.Name)]


def _assignment_value(statement: ast.stmt) -> ast.AST | None:
    if isinstance(statement, ast.Assign):
        return statement.value
    if isinstance(statement, ast.AnnAssign):
        return statement.value
    return None


def _bound_destructive_aliases_before(
    function: ast.FunctionDef | ast.AsyncFunctionDef,
    receiver: ast.AST,
    finding: ast.Call,
    call: ast.Call,
    parents: dict[int, ast.AST],
) -> dict[str, str]:
    cutoff = getattr(call, "lineno", 10**9)
    aliases: dict[str, str] = {}

    bindings = sorted(
        (
            item
            for item in ast.walk(function)
            if isinstance(item, (ast.Assign, ast.AnnAssign, ast.Delete))
            and sink_state._belongs_to_function(item, function, parents)
            and getattr(item, "lineno", cutoff + 1) < cutoff
        ),
        key=lambda item: (
            getattr(item, "lineno", 0),
            getattr(item, "col_offset", 0),
        ),
    )

    for item in bindings:
        # Ignore bindings that cannot occur on the same execution path as both
        # the published finding and the eventual alias call. This mirrors the
        # existing post-emission sink path filter and prevents mutually exclusive
        # branches from spuriously creating or invalidating an alias.
        if not post_sink._can_share_execution_path(
            finding, item, function, parents
        ):
            continue
        if not post_sink._can_share_execution_path(
            item, call, function, parents
        ):
            continue

        if isinstance(item, ast.Delete):
            for target in item.targets:
                if isinstance(target, ast.Name):
                    aliases.pop(target.id, None)
            continue

        value = _assignment_value(item)
        target_names = _simple_assignment_targets(item)
        if value is None or not target_names:
            continue

        method: str | None = None
        if (
            isinstance(value, ast.Attribute)
            and value.attr in sink_state._DESTRUCTIVE_SINK_METHODS
        ):
            receiver_aliases = sink_state._receiver_aliases_before(
                function,
                receiver,
                parents,
                getattr(item, "lineno", 0) + 1,
            )
            if sink_state._root_name(value.value) in receiver_aliases:
                method = value.attr
        elif isinstance(value, ast.Name):
            method = aliases.get(value.id)

        for target_name in target_names:
            if method is None:
                aliases.pop(target_name, None)
            else:
                aliases[target_name] = method

    return aliases


def _post_emission_bound_method_history(
    node: ast.Call,
    receiver: ast.AST,
    parents: dict[int, ast.AST],
) -> list[str]:
    function = sink_state._enclosing_function(node, parents)
    if function is None:
        return []

    cutoff = getattr(node, "lineno", 10**9)
    changes: list[tuple[int, int, str]] = []

    for item in ast.walk(function):
        if not (
            isinstance(item, ast.Call)
            and isinstance(item.func, ast.Name)
            and sink_state._belongs_to_function(item, function, parents)
        ):
            continue

        line = getattr(item, "lineno", 0)
        if line <= cutoff:
            continue
        if not post_sink._can_share_execution_path(
            node, item, function, parents
        ):
            continue

        aliases = _bound_destructive_aliases_before(
            function,
            receiver,
            node,
            item,
            parents,
        )
        method = aliases.get(item.func.id)
        if method is None:
            continue

        # Deliberately omit the private alias identifier from the compatibility
        # payload. The stable behavior is the destructive bound operation on the
        # published sink, not whether the implementation called it ``clear``,
        # ``wipe``, or another local name.
        changes.append(
            (
                line,
                getattr(item, "col_offset", 0),
                json.dumps(
                    {
                        "context": sink_state._sink_state_context(
                            item, function, parents
                        ),
                        "operation": {
                            "kind": "bound-destructive-sink-method",
                            "method": method,
                        },
                    },
                    sort_keys=True,
                ),
            )
        )

    changes.sort()
    return [value for _, _, value in changes]


def _emission_sink_contract_with_bound_method_aliases(
    node: ast.Call,
    parents: dict[int, ast.AST],
) -> list[str]:
    contract = list(_previous_sink_contract(node, parents))
    receiver = sink_state._finding_sink_receiver(node, parents)
    if receiver is None:
        return contract

    history = _post_emission_bound_method_history(node, receiver, parents)
    if history:
        contract.append(
            "post-bound-method-receiver-state:"
            + json.dumps(history, sort_keys=True)
        )
    return contract


sink_execution._emission_sink_contract = (
    _emission_sink_contract_with_bound_method_aliases
)


# ---------------------------------------------------------------------------
# Permanent regressions
# ---------------------------------------------------------------------------

class ReleaseCandidateAssignmentRhsPrerequisiteTests(unittest.TestCase):
    def test_dynamic_assignment_rhs_changes_literal_and_sink_contracts(self) -> None:
        direct = '''
from standards_tools import Finding

def run(findings, value):
    findings.append(Finding("PUBLIC_CODE", "message"))
'''
        preceded = '''
from standards_tools import Finding

def run(findings, value):
    ignored = value + 1
    findings.append(Finding("PUBLIC_CODE", "message"))
'''
        self.assertNotEqual(
            literal_base.finding_semantic_signatures(direct),
            literal_base.finding_semantic_signatures(preceded),
        )
        self.assertNotEqual(
            sink_execution.finding_semantic_signatures_with_sink(direct),
            sink_execution.finding_semantic_signatures_with_sink(preceded),
        )

    def test_dynamic_assignment_rhs_changes_parameterized_contracts(self) -> None:
        direct = '''
def read_text(path, findings, code):
    Finding(code, "decode failed", path="sample")
def validate(path, findings, value):
    read_text(path, findings, "PUBLIC_CODE")
'''
        preceded = '''
def read_text(path, findings, code):
    Finding(code, "decode failed", path="sample")
def validate(path, findings, value):
    ignored = value + 1
    read_text(path, findings, "PUBLIC_CODE")
'''
        self.assertNotEqual(
            parameterized_active.parameterized_finding_contracts(
                direct, "sample.py"
            ),
            parameterized_active.parameterized_finding_contracts(
                preceded, "sample.py"
            ),
        )
        self.assertNotEqual(
            parameterized_reachability.reachable_parameterized_contracts(
                direct, "sample.py"
            ),
            parameterized_reachability.reachable_parameterized_contracts(
                preceded, "sample.py"
            ),
        )

    def test_statically_safe_assignment_rhs_does_not_add_noise(self) -> None:
        direct = '''
from standards_tools import Finding

def run(findings):
    findings.append(Finding("PUBLIC_CODE", "message"))
'''
        preceded = '''
from standards_tools import Finding

def run(findings):
    ignored = 1 + 1
    findings.append(Finding("PUBLIC_CODE", "message"))
'''
        self.assertEqual(
            literal_base.finding_semantic_signatures(direct),
            literal_base.finding_semantic_signatures(preceded),
        )

    def test_known_safe_same_module_assigned_helper_remains_compatible(self) -> None:
        direct = '''
from standards_tools import Finding

def run(findings):
    findings.append(Finding("PUBLIC_CODE", "message"))
'''
        preceded = '''
from standards_tools import Finding

def observe():
    return 1
def run(findings):
    ignored = observe()
    findings.append(Finding("PUBLIC_CODE", "message"))
'''
        self.assertEqual(
            literal_base.finding_semantic_signatures(direct),
            literal_base.finding_semantic_signatures(preceded),
        )

    def test_statically_raising_assignment_rhs_hides_literal_reachability(self) -> None:
        source = '''
def validate():
    ignored = None + 1
    Finding("PUBLIC_CODE", "unreachable")
'''
        self.assertEqual(
            basic_reachability.reachable_contracts(source, "sample.py"),
            Counter(),
        )
        self.assertEqual(
            extended_reachability.reachable_contracts(source, "sample.py"),
            Counter(),
        )


class ReleaseCandidateBoundMethodSinkAliasTests(unittest.TestCase):
    def test_bound_clear_alias_after_emission_changes_contract(self) -> None:
        emitted = '''
def validate(findings):
    findings.append(Finding("PUBLIC_CODE", "visible"))
'''
        cleared = '''
def validate(findings):
    findings.append(Finding("PUBLIC_CODE", "visible"))
    clear = findings.clear
    clear()
'''
        expected = literal_base.finding_semantic_signatures(emitted)
        actual = literal_base.finding_semantic_signatures(cleared)
        self.assertNotEqual(expected, actual)
        sink = json.loads(actual["PUBLIC_CODE"][0])["sink"]
        self.assertTrue(
            any(
                item.startswith("post-bound-method-receiver-state:")
                for item in sink
            ),
            sink,
        )

    def test_bound_method_alias_can_be_created_before_emission(self) -> None:
        direct = '''
def validate(findings):
    findings.append(Finding("PUBLIC_CODE", "visible"))
'''
        aliased = '''
def validate(findings):
    clear = findings.clear
    findings.append(Finding("PUBLIC_CODE", "visible"))
    clear()
'''
        self.assertNotEqual(
            literal_base.finding_semantic_signatures(direct),
            literal_base.finding_semantic_signatures(aliased),
        )

    def test_bound_method_alias_tracks_receiver_alias(self) -> None:
        direct = '''
def validate(findings):
    findings.append(Finding("PUBLIC_CODE", "visible"))
'''
        aliased = '''
def validate(findings):
    findings.append(Finding("PUBLIC_CODE", "visible"))
    sink_alias = findings
    clear = sink_alias.clear
    clear()
'''
        self.assertNotEqual(
            literal_base.finding_semantic_signatures(direct),
            literal_base.finding_semantic_signatures(aliased),
        )

    def test_bound_method_alias_rebinding_removes_destructive_effect(self) -> None:
        direct = '''
def harmless():
    return None
def validate(findings):
    findings.append(Finding("PUBLIC_CODE", "visible"))
'''
        rebound = '''
def harmless():
    return None
def validate(findings):
    findings.append(Finding("PUBLIC_CODE", "visible"))
    clear = findings.clear
    clear = harmless
    clear()
'''
        direct_sink = json.loads(
            literal_base.finding_semantic_signatures(direct)["PUBLIC_CODE"][0]
        )["sink"]
        rebound_sink = json.loads(
            literal_base.finding_semantic_signatures(rebound)["PUBLIC_CODE"][0]
        )["sink"]
        self.assertEqual(direct_sink, rebound_sink)

    def test_transitive_bound_method_alias_is_tracked(self) -> None:
        direct = '''
def validate(findings):
    findings.append(Finding("PUBLIC_CODE", "visible"))
'''
        aliased = '''
def validate(findings):
    findings.append(Finding("PUBLIC_CODE", "visible"))
    clear = findings.clear
    wipe = clear
    wipe()
'''
        self.assertNotEqual(
            literal_base.finding_semantic_signatures(direct),
            literal_base.finding_semantic_signatures(aliased),
        )


if __name__ == "__main__":
    unittest.main()
