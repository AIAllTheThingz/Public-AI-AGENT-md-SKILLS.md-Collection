from __future__ import annotations

import ast
import json
import unittest

import rc_finding_code_contracts_base as literal_base
import test_rc_zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz_final_pr71_closure as returned_sink
import test_rc_zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz_final_execution_completion_closure as prior


# Final returned-sink selection closure for PR #71.
#
# The earlier returned-local-sink remediation proved that rebinding a local
# findings list before returning it changes the public sink contract. Complete
# that model here by preserving how ToolResult.from_findings selects the sink:
# a conditional or otherwise indirect expression can discard an already-emitted
# Finding without rebinding the local name itself.

sink_execution = prior.sink_execution
sink_state = returned_sink.sink_state
post_sink = returned_sink.post_sink

_previous_emission_sink_contract = sink_execution._emission_sink_contract
_SELECTION_PREFIX = "post-returned-local-sink-selection:"


def _function_parameter_names(
    function: ast.FunctionDef | ast.AsyncFunctionDef,
) -> set[str]:
    names = {
        argument.arg
        for argument in (
            *function.args.posonlyargs,
            *function.args.args,
            *function.args.kwonlyargs,
        )
    }
    if function.args.vararg is not None:
        names.add(function.args.vararg.arg)
    if function.args.kwarg is not None:
        names.add(function.args.kwarg.arg)
    return names


def _contains_name(node: ast.AST | None, name: str) -> bool:
    return node is not None and any(
        isinstance(item, ast.Name)
        and isinstance(item.ctx, ast.Load)
        and item.id == name
        for item in ast.walk(node)
    )


def _literal_truth(node: ast.AST) -> bool | None:
    if isinstance(node, ast.Constant):
        try:
            return bool(node.value)
        except Exception:
            return None
    return None


def _selection_state(
    node: ast.AST,
    receiver_name: str,
) -> tuple[str, ast.AST | None]:
    """Classify whether an expression preserves the emitted local sink."""

    if isinstance(node, ast.Name):
        return (
            ("kept", None)
            if node.id == receiver_name
            else ("discarded", None)
        )

    if isinstance(node, ast.IfExp):
        truth = _literal_truth(node.test)
        if truth is True:
            return _selection_state(node.body, receiver_name)
        if truth is False:
            return _selection_state(node.orelse, receiver_name)

        body_state, _ = _selection_state(node.body, receiver_name)
        else_state, _ = _selection_state(node.orelse, receiver_name)
        if body_state == else_state == "kept":
            return "kept", None
        if body_state == else_state == "discarded":
            return "discarded", None
        return "conditional-may-discard", node.test

    if isinstance(node, ast.BoolOp):
        if not _contains_name(node, receiver_name):
            return "discarded", None
        # and/or choose an operand value at runtime. If the sink participates in
        # that choice but is not the whole expression, returning it is conditional.
        return "conditional-may-discard", node

    if _contains_name(node, receiver_name):
        # Preserve a semantic risk class rather than fingerprinting arbitrary
        # private syntax. A nested reference does not prove that the expression
        # itself evaluates to the original findings list.
        return "may-discard", node

    return "discarded", None


def _from_findings_sink_expression(
    call: ast.Call,
    receiver_name: str,
) -> ast.AST | None:
    if not (
        isinstance(call.func, ast.Attribute)
        and call.func.attr == "from_findings"
    ):
        return None

    for keyword in call.keywords:
        if keyword.arg == "findings":
            return keyword.value

    # The production API is keyword-only, but compatibility fixtures also use a
    # compact positional form. Select the unique positional expression that
    # carries the known sink instead of hard-coding a private argument index.
    candidates = [
        argument
        for argument in call.args
        if _contains_name(argument, receiver_name)
    ]
    return candidates[0] if len(candidates) == 1 else None


def _return_sink_selections(
    finding: ast.Call,
    receiver: ast.AST,
    parents: dict[int, ast.AST],
) -> list[str]:
    function = sink_state._enclosing_function(finding, parents)
    if function is None:
        return []

    receiver_name = sink_state._root_name(receiver)
    if (
        receiver_name is None
        or receiver_name in _function_parameter_names(function)
    ):
        return []

    finding_line = getattr(finding, "lineno", 10**9)
    selections: list[tuple[int, int, str]] = []

    for returned in ast.walk(function):
        if not (
            isinstance(returned, ast.Return)
            and returned.value is not None
            and sink_state._belongs_to_function(returned, function, parents)
            and getattr(returned, "lineno", 0) > finding_line
            and post_sink._can_share_execution_path(
                finding,
                returned,
                function,
                parents,
            )
        ):
            continue

        for call in ast.walk(returned.value):
            if not isinstance(call, ast.Call):
                continue
            sink_expression = _from_findings_sink_expression(
                call,
                receiver_name,
            )
            if sink_expression is None:
                continue

            state, selector = _selection_state(
                sink_expression,
                receiver_name,
            )
            if state == "kept":
                continue

            payload = {
                "context": sink_state._sink_state_context(
                    returned,
                    function,
                    parents,
                ),
                "selection": state,
            }
            if selector is not None:
                payload["selector"] = literal_base.canonical_ast(selector)

            selections.append(
                (
                    getattr(returned, "lineno", 0),
                    getattr(returned, "col_offset", 0),
                    json.dumps(payload, sort_keys=True),
                )
            )

    selections.sort()
    return [value for _, _, value in selections]


def _emission_sink_contract_with_return_selection(
    node: ast.Call,
    parents: dict[int, ast.AST],
) -> list[str]:
    contract = list(_previous_emission_sink_contract(node, parents))
    receiver = sink_state._finding_sink_receiver(node, parents)
    if receiver is None:
        return contract

    selections = _return_sink_selections(node, receiver, parents)
    if selections:
        contract.append(
            _SELECTION_PREFIX + json.dumps(selections, sort_keys=True)
        )
    return contract


sink_execution._emission_sink_contract = (
    _emission_sink_contract_with_return_selection
)


class ReleaseCandidateReturnedSinkSelectionTests(unittest.TestCase):
    def test_conditional_returned_sink_changes_literal_and_sink_contract(self) -> None:
        direct = """
def validate(flag):
    findings = []
    findings.append(Finding("PUBLIC_CODE", "visible"))
    return ToolResult.from_findings("validate", findings)
"""
        conditional = """
def validate(flag):
    findings = []
    findings.append(Finding("PUBLIC_CODE", "visible"))
    return ToolResult.from_findings(
        "validate",
        findings if flag else [],
    )
"""
        expected = literal_base.finding_semantic_signatures(direct)
        actual = literal_base.finding_semantic_signatures(conditional)
        self.assertNotEqual(expected, actual)
        sink = json.loads(actual["PUBLIC_CODE"][0])["sink"]
        self.assertTrue(
            any(item.startswith(_SELECTION_PREFIX) for item in sink),
            sink,
        )

        self.assertNotEqual(
            sink_execution.finding_semantic_signatures_with_sink(direct),
            sink_execution.finding_semantic_signatures_with_sink(conditional),
        )

    def test_same_sink_on_both_conditional_paths_remains_compatible(self) -> None:
        direct = """
def validate(flag):
    findings = []
    findings.append(Finding("PUBLIC_CODE", "visible"))
    return ToolResult.from_findings("validate", findings)
"""
        same_sink = """
def validate(flag):
    findings = []
    findings.append(Finding("PUBLIC_CODE", "visible"))
    return ToolResult.from_findings(
        "validate",
        findings if flag else findings,
    )
"""
        self.assertEqual(
            literal_base.finding_semantic_signatures(direct),
            literal_base.finding_semantic_signatures(same_sink),
        )

    def test_statically_selected_sink_remains_compatible(self) -> None:
        direct = """
def validate():
    findings = []
    findings.append(Finding("PUBLIC_CODE", "visible"))
    return ToolResult.from_findings("validate", findings)
"""
        selected = """
def validate():
    findings = []
    findings.append(Finding("PUBLIC_CODE", "visible"))
    return ToolResult.from_findings(
        "validate",
        findings if True else [],
    )
"""
        self.assertEqual(
            literal_base.finding_semantic_signatures(direct),
            literal_base.finding_semantic_signatures(selected),
        )

    def test_returning_a_different_sink_is_detected(self) -> None:
        direct = """
def validate():
    findings = []
    findings.append(Finding("PUBLIC_CODE", "visible"))
    return ToolResult.from_findings(findings=findings)
"""
        discarded = """
def validate():
    findings = []
    findings.append(Finding("PUBLIC_CODE", "visible"))
    return ToolResult.from_findings(findings=[])
"""
        self.assertNotEqual(
            literal_base.finding_semantic_signatures(direct),
            literal_base.finding_semantic_signatures(discarded),
        )


if __name__ == "__main__":
    unittest.main()
