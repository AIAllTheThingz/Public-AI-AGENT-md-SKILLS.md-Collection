from __future__ import annotations

import ast
import importlib
import json
import unittest
from pathlib import Path

import rc_finding_code_contracts_base as literal_base


# Final NamedExpr alias closure for PR #71.
#
# The returned-sink constructor-alias layer already models ordinary assignments,
# branch joins, definite rebindings, and return-callee walruses. A standalone
# assignment expression is the same local binding event at runtime, so normalize
# that one executable statement form into the established assignment flow rather
# than introducing a second alias analysis.


def _load_overlay(suffix: str):
    matches = sorted(Path(__file__).parent.glob(f"test_rc_*{suffix}.py"))
    if len(matches) != 1:
        raise RuntimeError(f"expected exactly one RC overlay for {suffix!r}")
    return importlib.import_module(matches[0].stem)


alias_layer = _load_overlay("_returned_sink_constructor_aliases")
_previous_flow_block = alias_layer._flow_block


def _standalone_named_expression_assignment(statement: ast.stmt) -> ast.stmt:
    if not (
        isinstance(statement, ast.Expr)
        and isinstance(statement.value, ast.NamedExpr)
        and isinstance(statement.value.target, ast.Name)
    ):
        return statement

    assignment = ast.Assign(
        targets=[statement.value.target],
        value=statement.value.value,
    )
    return ast.copy_location(assignment, statement)


def _flow_block_with_standalone_named_expressions(
    statements: list[ast.stmt],
    aliases: dict[str, str],
    return_states: dict[int, dict[str, str]],
) -> dict[str, str] | None:
    normalized = [
        _standalone_named_expression_assignment(statement)
        for statement in statements
    ]
    return _previous_flow_block(normalized, aliases, return_states)


# The previous flow routine resolves recursive block traversal through its module
# global name, so installing this wrapper also covers nested if/loop/try/with/
# match blocks while retaining the already-reviewed reachability and branch joins.
alias_layer._flow_block = _flow_block_with_standalone_named_expressions


class ReleaseCandidateNamedExpressionConstructorAliasTests(unittest.TestCase):
    def _sink(self, source: str) -> list[str]:
        signature = literal_base.finding_semantic_signatures(
            source,
            "sample.py",
        )["PUBLIC_CODE"][0]
        return json.loads(signature)["sink"]

    def _has_alias_marker(self, source: str) -> bool:
        return any(
            item.startswith(alias_layer._ALIAS_SELECTION_PREFIX)
            for item in self._sink(source)
        )

    def test_standalone_named_expression_alias_discard_is_tracked(self) -> None:
        kept = """
from standards_tools import Finding, ToolResult

def validate():
    findings = []
    (maker := ToolResult.from_findings)
    findings.append(Finding("PUBLIC_CODE", "visible"))
    return maker(tool="validate", version="1", findings=findings)
"""
        discarded = """
from standards_tools import Finding, ToolResult

def validate():
    findings = []
    (maker := ToolResult.from_findings)
    findings.append(Finding("PUBLIC_CODE", "visible"))
    return maker(tool="validate", version="1", findings=[])
"""
        self.assertFalse(self._has_alias_marker(kept))
        self.assertTrue(self._has_alias_marker(discarded))
        self.assertNotEqual(
            literal_base.finding_semantic_signatures(kept, "sample.py"),
            literal_base.finding_semantic_signatures(discarded, "sample.py"),
        )

    def test_standalone_named_expression_rebinding_removes_alias(self) -> None:
        source = """
from standards_tools import Finding, ToolResult

def harmless(**kwargs):
    return kwargs

def validate():
    findings = []
    (maker := ToolResult.from_findings)
    (maker := harmless)
    findings.append(Finding("PUBLIC_CODE", "visible"))
    return maker(tool="validate", version="1", findings=[])
"""
        self.assertFalse(self._has_alias_marker(source))

    def test_statically_dead_named_expression_alias_does_not_create_risk(self) -> None:
        source = """
from standards_tools import Finding, ToolResult

def harmless(**kwargs):
    return kwargs

def validate():
    findings = []
    maker = harmless
    if False:
        (maker := ToolResult.from_findings)
    findings.append(Finding("PUBLIC_CODE", "visible"))
    return maker(tool="validate", version="1", findings=[])
"""
        self.assertFalse(self._has_alias_marker(source))


if __name__ == "__main__":
    unittest.main()
