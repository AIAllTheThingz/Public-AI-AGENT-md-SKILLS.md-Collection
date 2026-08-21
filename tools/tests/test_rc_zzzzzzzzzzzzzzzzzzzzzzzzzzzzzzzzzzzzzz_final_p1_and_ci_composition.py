from __future__ import annotations

import ast
import re
import unittest

import rc_finding_code_contracts_base as literal_base
import test_rc_agent_skill_entrypoints as skills
import test_rc_finding_reachability as basic_reachability
import test_rc_numbered_rule_semantics as numbered
import test_rc_template_contracts as templates
import test_rc_unnumbered_governance_semantics as unnumbered
import test_rc_zzz_finding_emission_sink as sink_execution
import test_rc_zzzzzzzzzzzzzzzzzzzzzzzzzzzzzz_rendered_markdown_and_attribute_prerequisites as rendered_layer
import test_rc_zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz_definition_defaults_and_bound_names as bound_names_layer
import test_rc_zzzzzzzzzzzzzzzzzzzzzzzzzzz_left_to_right_expression_execution as left_to_right


# Final composition for the remaining PR #71 review/CI gaps:
#
# * CommonMark indented code blocks are non-operative examples, just like fenced
#   code and HTML comments, and must be excluded from semantic Markdown contracts.
# * The basic reachability module historically exposed reachable_contracts; later
#   regressions still call that compatibility name after the implementation was
#   renamed to reachable_literal_finding_contracts.
# * A local binding collected from a conditional assignment is not proof that the
#   name is bound on the path reaching a later expression. Apply lexical binding
#   proof before consulting the value snapshot.


# ---------------------------------------------------------------------------
# Rendered Markdown: comments, fenced code, and indented code blocks
# ---------------------------------------------------------------------------

_HTML_COMMENT_PATTERN = re.compile(r"<!--.*?-->", re.DOTALL)
_FENCE_OPEN_PATTERN = re.compile(r"^[ \t]{0,3}(?P<marker>`{3,}|~{3,})")
_ATX_HEADING_PATTERN = re.compile(r"^#{1,6}(?:[ \t]+|$)")
_LIST_MARKER_PATTERN = re.compile(r"^(?:[-+*]|\d{1,9}[.)])(?:[ \t]+|$)")
_SETEXT_OR_RULE_PATTERN = re.compile(r"^(?:=+|-+|(?:\*\s*){3,}|(?:_\s*){3,})[ \t]*$")


def _indent_columns(text: str) -> int:
    columns = 0
    for character in text:
        if character == " ":
            columns += 1
        elif character == "\t":
            columns += 4 - (columns % 4)
        else:
            break
    return columns


def _line_break(raw_line: str) -> str:
    return "\n" if raw_line.endswith(("\n", "\r")) else ""


def _opens_or_continues_paragraph(candidate: str) -> bool:
    """Return whether a following indented line would interrupt paragraph/list text."""

    stripped = candidate.lstrip(" \t")
    if not stripped:
        return False
    if _ATX_HEADING_PATTERN.match(stripped):
        return False
    if stripped.startswith(">"):
        return False
    if _SETEXT_OR_RULE_PATTERN.match(stripped):
        return False
    # List content owns ambiguous indentation ahead of indented-code parsing.
    if _LIST_MARKER_PATTERN.match(stripped):
        return True
    return True


def _rendered_markdown(text: str) -> str:
    """Project Markdown to operative source text for compatibility scanners.

    This intentionally is not a full Markdown renderer. It models the non-rendered
    regions material to these semantic extractors: HTML comments, fenced code,
    and CommonMark indented code blocks. Four-column indentation begins code when
    it does not interrupt an active paragraph/list continuation; headings and
    other block boundaries therefore permit indented code without requiring an
    extra blank line.
    """

    without_comments = _HTML_COMMENT_PATTERN.sub("", text)
    output: list[str] = []
    fence_character: str | None = None
    fence_length = 0
    in_indented_code = False
    paragraph_or_list_open = False

    for raw_line in without_comments.splitlines(keepends=True):
        candidate = raw_line.rstrip("\r\n")
        blank = candidate.strip(" \t") == ""
        leading_columns = _indent_columns(candidate)
        eligible_fence_indent = leading_columns <= 3
        stripped = candidate.lstrip(" \t") if eligible_fence_indent else candidate

        if fence_character is not None:
            if eligible_fence_indent:
                closing = re.match(
                    rf"^{re.escape(fence_character)}{{{fence_length},}}[ \t]*$",
                    stripped,
                )
                if closing is not None:
                    fence_character = None
                    fence_length = 0
            output.append(_line_break(raw_line))
            paragraph_or_list_open = False
            continue

        if in_indented_code:
            if blank or leading_columns >= 4:
                output.append(_line_break(raw_line))
                paragraph_or_list_open = False
                continue
            in_indented_code = False

        match = _FENCE_OPEN_PATTERN.match(candidate)
        if match is not None:
            marker = match.group("marker")
            fence_character = marker[0]
            fence_length = len(marker)
            output.append(_line_break(raw_line))
            paragraph_or_list_open = False
            continue

        if leading_columns >= 4 and not paragraph_or_list_open and not blank:
            in_indented_code = True
            output.append(_line_break(raw_line))
            paragraph_or_list_open = False
            continue

        output.append(raw_line)
        if blank:
            paragraph_or_list_open = False
        elif leading_columns < 4:
            paragraph_or_list_open = _opens_or_continues_paragraph(candidate)

    return "".join(output)


# Replace the prior rendered-content projection everywhere it is resolved at
# call time. Immutable checkpoint source and candidate source use the same rule.
rendered_layer._rendered_markdown = _rendered_markdown
rendered_layer.rule_base.rendered_markdown = _rendered_markdown
numbered.visible_markdown = _rendered_markdown
unnumbered.visible_markdown = _rendered_markdown
templates.rendered_markdown = _rendered_markdown
skills.visible_markdown = _rendered_markdown


# ---------------------------------------------------------------------------
# CI composition: restore the basic reachability compatibility entry point
# ---------------------------------------------------------------------------


def _basic_reachable_contracts(text: str, source_path: str):
    return basic_reachability.reachable_literal_finding_contracts(text, source_path)


basic_reachability.reachable_contracts = _basic_reachable_contracts


# ---------------------------------------------------------------------------
# Binding-aware left-to-right name evaluation
# ---------------------------------------------------------------------------

_previous_visitor_execution_state = bound_names_layer._visitor_execution_state


def _visitor_execution_state(visitor, node: ast.AST, constants: dict[str, object]) -> str:
    if isinstance(node, ast.Name):
        function_locals = getattr(visitor, "_function_local_names", set())
        definitely_bound = getattr(visitor, "_definitely_bound_names", set())

        # Python decides that a name is local for the whole function when it is
        # assigned anywhere in that function. A value snapshot from one branch
        # therefore cannot prove a later load is bound on all paths.
        if node.id in function_locals and node.id not in definitely_bound:
            return left_to_right._UNKNOWN

    return _previous_visitor_execution_state(visitor, node, constants)


# The final left-to-right sequence helpers resolve this function through the
# bound-names layer's module globals, so the stronger ordering applies to tuple,
# list, call, sink, parameterized, and reachability sequence traversal.
bound_names_layer._visitor_execution_state = _visitor_execution_state


# Parameterized helper calls have a specialized visit_Call path that also
# evaluates call prerequisites directly. Add the same binding-aware prerequisite
# marker around that already-composed implementation so caller-supplied finding
# codes cannot bypass the name-binding contract.
_parameterized_visitor = rendered_layer.parameterized_active.BranchAwareParameterizedCallSiteVisitor
_current_parameterized_visit_call = _parameterized_visitor.visit_Call


def _parameterized_visit_call(self, node: ast.Call) -> None:
    is_helper = (
        isinstance(node.func, ast.Name)
        and node.func.id in getattr(self, "parameterized_helpers", {})
    )
    if not is_helper:
        _current_parameterized_visit_call(self, node)
        return

    constants = left_to_right._parameterized_constants(self)
    evaluation_nodes = left_to_right._call_evaluation_nodes(node)
    prerequisites = [
        item
        for item in evaluation_nodes
        if _visitor_execution_state(self, item, constants) == left_to_right._UNKNOWN
    ]

    if not prerequisites:
        _current_parameterized_visit_call(self, node)
        return

    self.context_nodes.append(
        (
            "call:invocation:requires-bound-name-evaluation",
            left_to_right._prerequisite_node(prerequisites),
        )
    )
    try:
        _current_parameterized_visit_call(self, node)
    finally:
        self.context_nodes.pop()


_parameterized_visitor.visit_Call = _parameterized_visit_call
rendered_layer.parameterized_active.base.ParameterizedCallSiteVisitor = _parameterized_visitor


# ---------------------------------------------------------------------------
# Permanent regressions
# ---------------------------------------------------------------------------


class ReleaseCandidateFinalP1AndCICompositionTests(unittest.TestCase):
    def test_basic_reachability_compatibility_entrypoint_is_restored(self) -> None:
        source = '''
def validate():
    Finding("PUBLIC_CODE", "visible")
'''
        contracts = basic_reachability.reachable_contracts(source, "sample.py")
        self.assertEqual(contracts[("sample.py", "validate", "PUBLIC_CODE")], 1)

    def test_four_space_indented_template_obligation_is_not_operative(self) -> None:
        published_text = '''
## Approval

- Approval must come from an accountable human.
'''
        indented_text = '''
## Approval

    - Approval must come from an accountable human.
'''
        published = templates.template_contract(published_text)
        candidate = templates.template_contract(indented_text)
        self.assertTrue(
            templates.template_contract_findings(
                "templates/demo.md", published, candidate
            )
        )

    def test_indented_code_can_follow_heading_without_blank_line(self) -> None:
        published_text = '''
## Approval
- Approval must come from an accountable human.
'''
        indented_text = '''
## Approval
    - Approval must come from an accountable human.
'''
        published = templates.template_contract(published_text)
        candidate = templates.template_contract(indented_text)
        self.assertTrue(
            templates.template_contract_findings(
                "templates/demo.md", published, candidate
            )
        )

    def test_indentation_does_not_interrupt_plain_paragraph(self) -> None:
        text = "Paragraph text\n    continuation text\n"
        self.assertIn("continuation text", _rendered_markdown(text))

    def test_four_space_indented_governance_control_is_not_operative(self) -> None:
        published_text = '''
## Decision gates

- No closure until the deviation is removed.
'''
        indented_text = '''
## Decision gates

    - No closure until the deviation is removed.
'''
        published = unnumbered.extract_unnumbered_governance_contracts(
            published_text, "governance/demo.md"
        )
        candidate = unnumbered.extract_unnumbered_governance_contracts(
            indented_text, "governance/demo.md"
        )
        self.assertTrue(
            unnumbered.unnumbered_contract_findings(published, candidate)
        )

    def test_four_space_indented_skill_router_table_is_not_operative(self) -> None:
        published_text = '''
| Evidence | Package |
| --- | --- |
| `.py` | [Python](python/) |
'''
        indented_text = '''
    | Evidence | Package |
    | --- | --- |
    | `.py` | [Python](python/) |
'''
        published = skills.skill_routing_contract(published_text)
        candidate = skills.skill_routing_contract(indented_text)
        self.assertTrue(published)
        self.assertTrue(skills.missing_routing_contracts(published, candidate))

    def test_four_space_indented_numbered_rule_is_not_operative(self) -> None:
        published_text = '''
### GOV-DEMO-001

**Requirement:** Preserve the published behavior.
'''
        indented_text = '''
    ### GOV-DEMO-001

    **Requirement:** Preserve the published behavior.
'''
        published = rendered_layer.rule_base.extract_rule_contracts(
            published_text, "governance/demo.md"
        )
        candidate = rendered_layer.rule_base.extract_rule_contracts(
            indented_text, "governance/demo.md"
        )
        self.assertTrue(
            rendered_layer.rule_base.rule_contract_findings(published, candidate)
        )

    def test_conditionally_bound_local_is_an_execution_prerequisite(self) -> None:
        direct = '''
from standards_tools import Finding

def run(enabled):
    Finding("PUBLIC_CODE", "message")
'''
        conditional = '''
from standards_tools import Finding

def run(enabled):
    if enabled:
        maybe = 1
    (maybe, Finding("PUBLIC_CODE", "message"))
'''
        expected = literal_base.finding_semantic_signatures(direct)
        actual = literal_base.finding_semantic_signatures(conditional)
        self.assertNotEqual(expected, actual)
        self.assertTrue(
            any(
                "requires-prior-evaluation" in signature
                for signature in actual["PUBLIC_CODE"]
            )
        )

    def test_conditionally_bound_local_changes_sink_contract_too(self) -> None:
        direct = '''
from standards_tools import Finding

def run(findings, enabled):
    findings.append(Finding("PUBLIC_CODE", "message"))
'''
        conditional = '''
from standards_tools import Finding

def run(findings, enabled):
    if enabled:
        maybe = 1
    (maybe, findings.append(Finding("PUBLIC_CODE", "message")))
'''
        self.assertNotEqual(
            sink_execution.finding_semantic_signatures_with_sink(direct),
            sink_execution.finding_semantic_signatures_with_sink(conditional),
        )


if __name__ == "__main__":
    unittest.main()
