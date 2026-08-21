from __future__ import annotations

import ast
import re
import unittest
from collections import Counter

import rc_finding_code_contracts_base as literal_base
import rc_normative_rule_contracts_base as rule_base
import test_rc_agent_skill_entrypoints as skills
import test_rc_approved_helper_and_deferred_execution as deferred_execution
import test_rc_extended_finding_reachability as extended_reachability
import test_rc_finding_reachability as basic_reachability
import test_rc_numbered_rule_semantics as numbered
import test_rc_parameterized_finding_codes as parameterized_active
import test_rc_parameterized_finding_reachability as parameterized_reachability
import test_rc_template_contracts as templates
import test_rc_unnumbered_governance_semantics as unnumbered
import test_rc_zzz_finding_emission_sink as sink_execution
import test_rc_zzzz_sink_rebinding_and_parameterized_multiplicity as multiplicity
import test_rc_zzzzz_lexical_function_execution as lexical_execution


# Compatibility contracts describe operative rendered guidance, not text that is
# hidden inside HTML comments or fenced code examples. Keep one rendering rule
# for the rule, governance, template, and skill-router scanners so a published
# obligation cannot survive compatibility comparison merely by being moved into
# a non-operative Markdown region.
_HTML_COMMENT_PATTERN = re.compile(r"<!--.*?-->", re.DOTALL)
_FENCE_OPEN_PATTERN = re.compile(r"^[ \t]{0,3}(?P<marker>`{3,}|~{3,})")


def _rendered_markdown(text: str) -> str:
    without_comments = _HTML_COMMENT_PATTERN.sub("", text)
    output: list[str] = []
    fence_character: str | None = None
    fence_length = 0

    for raw_line in without_comments.splitlines(keepends=True):
        candidate = raw_line.rstrip("\r\n")
        leading = candidate[: len(candidate) - len(candidate.lstrip(" \t"))]
        eligible = len(leading.replace("\t", "    ")) <= 3
        stripped = candidate.lstrip(" \t") if eligible else candidate

        if fence_character is None:
            match = _FENCE_OPEN_PATTERN.match(candidate)
            if match is not None:
                marker = match.group("marker")
                fence_character = marker[0]
                fence_length = len(marker)
                output.append("\n" if raw_line.endswith(("\n", "\r")) else "")
                continue
            output.append(raw_line)
            continue

        if eligible:
            closing = re.match(
                rf"^{re.escape(fence_character)}{{{fence_length},}}[ \t]*$",
                stripped,
            )
            if closing is not None:
                fence_character = None
                fence_length = 0
        output.append("\n" if raw_line.endswith(("\n", "\r")) else "")

    return "".join(output)


# Install the shared rendered-content projection on every Markdown semantic
# extractor. Both immutable published source and the current candidate are
# compared under the same rendering rules.
rule_base.rendered_markdown = _rendered_markdown
numbered.visible_markdown = _rendered_markdown
unnumbered.visible_markdown = _rendered_markdown
templates.rendered_markdown = _rendered_markdown
skills.visible_markdown = _rendered_markdown


# The left-to-right execution layer intentionally replaced visit_Call on several
# scanners. That replacement accidentally bypassed the older deferred-lambda and
# lexical-nested-function invocation hooks. Recompose those execution semantics
# around the latest call visitors rather than weakening the prerequisite model.
# Attribute execution remains owned by the dedicated attribute-access layer,
# which distinguishes known-safe builtin attributes from unknown or known-failing
# lookups. Do not replace its structurally-safe classifier here.


def _invoke_reachable_lambda(visitor, node: ast.Call) -> bool:
    deferred = deferred_execution._lambda_binding_for_call(visitor, node)
    if deferred is None:
        return False

    if isinstance(node.func, ast.Lambda):
        visitor.visit(node.func)
    for argument in node.args:
        visitor.visit(argument)
    for keyword in node.keywords:
        visitor.visit(keyword.value)

    active = getattr(visitor, "_active_lambda_bodies", set())
    marker = id(deferred)
    if marker in active:
        return True
    active.add(marker)
    try:
        visitor.visit(deferred.body)
    finally:
        active.remove(marker)
    return True


def _invoke_reachable_nested(visitor, node: ast.Call, identity_attribute: str) -> bool:
    def invoke(current, qualified) -> None:
        current._visit_function(qualified)

    return lexical_execution._invoke_nested_function(
        visitor,
        node,
        identity_attribute=identity_attribute,
        invoke=invoke,
    )


_current_literal_visit_call = literal_base.FindingSignatureVisitor.visit_Call
_current_sink_visit_call = sink_execution.SinkAwareFindingSignatureVisitor.visit_Call


def _literal_visit_call(self, node: ast.Call) -> None:
    if deferred_execution._lambda_binding_for_call(self, node) is not None:
        deferred_execution._literal_visit_call(self, node)
        return
    if lexical_execution._invoke_nested_function(
        self,
        node,
        identity_attribute="function",
        invoke=lexical_execution._literal_invoke,
    ):
        return
    _current_literal_visit_call(self, node)


def _sink_visit_call(self, node: ast.Call) -> None:
    if deferred_execution._lambda_binding_for_call(self, node) is not None:
        deferred_execution._literal_visit_call(self, node)
        return
    if lexical_execution._invoke_nested_function(
        self,
        node,
        identity_attribute="function",
        invoke=lexical_execution._literal_invoke,
    ):
        return
    _current_sink_visit_call(self, node)


literal_base.FindingSignatureVisitor.visit_Call = _literal_visit_call
sink_execution.SinkAwareFindingSignatureVisitor.visit_Call = _sink_visit_call


def _compose_reachability_visit_call(visitor_type) -> None:
    current = visitor_type.visit_Call

    def visit_call(self, node: ast.Call) -> None:
        if _invoke_reachable_lambda(self, node):
            return
        if _invoke_reachable_nested(self, node, "function"):
            return
        current(self, node)

    visitor_type.visit_Call = visit_call


for _visitor_type in (
    basic_reachability.ReachableFindingVisitor,
    extended_reachability.ExtendedReachableFindingVisitor,
    sink_execution.SinkAwareReachableFindingVisitor,
):
    _compose_reachability_visit_call(_visitor_type)


_parameterized_visitor = parameterized_active.BranchAwareParameterizedCallSiteVisitor
_current_parameterized_visit_call = _parameterized_visitor.visit_Call


def _parameterized_visit_call(self, node: ast.Call) -> None:
    if deferred_execution._lambda_binding_for_call(self, node) is not None:
        deferred_execution._parameterized_visit_call(self, node)
        return
    if lexical_execution._invoke_nested_function(
        self,
        node,
        identity_attribute="caller",
        invoke=lexical_execution._parameterized_invoke,
    ):
        return
    _current_parameterized_visit_call(self, node)


_parameterized_visitor.visit_Call = _parameterized_visit_call
parameterized_active.base.ParameterizedCallSiteVisitor = _parameterized_visitor


_current_reachable_parameterized_visit_call = (
    parameterized_reachability.ReachableParameterizedCallSiteVisitor.visit_Call
)


def _reachable_parameterized_visit_call(self, node: ast.Call) -> None:
    if deferred_execution._lambda_binding_for_call(self, node) is not None:
        deferred_execution._parameterized_visit_call(self, node)
        return
    if _invoke_reachable_nested(self, node, "caller"):
        return
    _current_reachable_parameterized_visit_call(self, node)


parameterized_reachability.ReachableParameterizedCallSiteVisitor.visit_Call = (
    _reachable_parameterized_visit_call
)


# The counting visitors own concrete visit_Call implementations, so compose the
# same invocation behavior there and point the multiplicity delegation hook at
# the final semantic call visitor.
_current_counting_visit_call = multiplicity._CountingParameterizedCallSiteVisitor.visit_Call
_current_counting_reachable_visit_call = (
    multiplicity._CountingReachableParameterizedCallSiteVisitor.visit_Call
)


def _counting_visit_call(self, node: ast.Call) -> None:
    if deferred_execution._lambda_binding_for_call(self, node) is not None:
        deferred_execution._parameterized_visit_call(self, node)
        return
    if _invoke_reachable_nested(self, node, "caller"):
        return
    _current_counting_visit_call(self, node)


def _counting_reachable_visit_call(self, node: ast.Call) -> None:
    if deferred_execution._lambda_binding_for_call(self, node) is not None:
        deferred_execution._parameterized_visit_call(self, node)
        return
    if _invoke_reachable_nested(self, node, "caller"):
        return
    _current_counting_reachable_visit_call(self, node)


multiplicity._CountingParameterizedCallSiteVisitor.visit_Call = _counting_visit_call
multiplicity._CountingReachableParameterizedCallSiteVisitor.visit_Call = (
    _counting_reachable_visit_call
)
multiplicity._COMPOSED_PARAMETERIZED_VISIT_CALL = _parameterized_visit_call


class ReleaseCandidateRenderedMarkdownAndCompositionTests(unittest.TestCase):
    def test_fenced_numbered_rule_is_not_an_operative_contract(self) -> None:
        published_text = '''
### GOV-DEMO-001

**Requirement:** Preserve the published behavior.
'''
        fenced_text = '''
```markdown
### GOV-DEMO-001

**Requirement:** Preserve the published behavior.
```
'''
        published = rule_base.extract_rule_contracts(published_text, "governance/demo.md")
        candidate = rule_base.extract_rule_contracts(fenced_text, "governance/demo.md")
        self.assertTrue(rule_base.rule_contract_findings(published, candidate))

    def test_hidden_numbered_rule_field_is_not_preserved(self) -> None:
        published_text = '''
### GOV-DEMO-001

**Requirement:** Preserve the published behavior.
**Expected evidence:** Tests demonstrate the behavior.
'''
        hidden_text = '''
### GOV-DEMO-001

**Requirement:** Preserve the published behavior.
<!--
**Expected evidence:** Tests demonstrate the behavior.
-->
'''
        published = numbered.extract_rule_field_contracts(
            published_text,
            "governance/demo.md",
        )
        candidate = numbered.extract_rule_field_contracts(
            hidden_text,
            "governance/demo.md",
        )
        self.assertTrue(numbered.rule_field_contract_findings(published, candidate))

    def test_fenced_numbered_rule_field_is_not_preserved(self) -> None:
        published_text = '''
### GOV-DEMO-001

**Requirement:** Preserve the published behavior.
**Expected evidence:** Tests demonstrate the behavior.
'''
        fenced_text = '''
### GOV-DEMO-001

**Requirement:** Preserve the published behavior.
```text
**Expected evidence:** Tests demonstrate the behavior.
```
'''
        published = numbered.extract_rule_field_contracts(
            published_text,
            "governance/demo.md",
        )
        candidate = numbered.extract_rule_field_contracts(
            fenced_text,
            "governance/demo.md",
        )
        self.assertTrue(numbered.rule_field_contract_findings(published, candidate))

    def test_hidden_unnumbered_control_is_not_preserved(self) -> None:
        published_text = '''
## Decision gates

- No closure until the deviation is removed.
'''
        hidden_text = '''
## Decision gates

<!--
- No closure until the deviation is removed.
-->
'''
        published = unnumbered.extract_unnumbered_governance_contracts(
            published_text,
            "governance/demo.md",
        )
        candidate = unnumbered.extract_unnumbered_governance_contracts(
            hidden_text,
            "governance/demo.md",
        )
        self.assertTrue(unnumbered.unnumbered_contract_findings(published, candidate))

    def test_fenced_unnumbered_control_is_not_preserved(self) -> None:
        published_text = '''
## Decision gates

- No closure until the deviation is removed.
'''
        fenced_text = '''
## Decision gates

```markdown
- No closure until the deviation is removed.
```
'''
        published = unnumbered.extract_unnumbered_governance_contracts(
            published_text,
            "governance/demo.md",
        )
        candidate = unnumbered.extract_unnumbered_governance_contracts(
            fenced_text,
            "governance/demo.md",
        )
        self.assertTrue(unnumbered.unnumbered_contract_findings(published, candidate))

    def test_hidden_template_field_and_obligation_are_not_preserved(self) -> None:
        published_text = '''
## Approval

- Approver: {{APPROVER}}
- Approval must come from an accountable human.
'''
        hidden_text = '''
## Approval

<!--
- Approver: {{APPROVER}}
- Approval must come from an accountable human.
-->
'''
        published = templates.template_contract(published_text)
        candidate = templates.template_contract(hidden_text)
        self.assertTrue(
            templates.template_contract_findings("templates/demo.md", published, candidate)
        )

    def test_fenced_template_obligation_is_not_preserved(self) -> None:
        published_text = '''
## Approval

- Approver: {{APPROVER}}
- Approval must come from an accountable human.
'''
        fenced_text = '''
## Approval

- Approver: {{APPROVER}}
```markdown
- Approval must come from an accountable human.
```
'''
        published = templates.template_contract(published_text)
        candidate = templates.template_contract(fenced_text)
        self.assertTrue(
            templates.template_contract_findings("templates/demo.md", published, candidate)
        )

    def test_hidden_skill_router_table_is_not_preserved(self) -> None:
        published_text = '''
| Evidence | Package |
| --- | --- |
| `.py` | [Python](python/) |
'''
        hidden_text = '''
<!--
| Evidence | Package |
| --- | --- |
| `.py` | [Python](python/) |
-->
'''
        published = skills.skill_routing_contract(published_text)
        candidate = skills.skill_routing_contract(hidden_text)
        self.assertTrue(published)
        self.assertTrue(skills.missing_routing_contracts(published, candidate))

    def test_fenced_skill_router_table_is_not_preserved(self) -> None:
        published_text = '''
| Evidence | Package |
| --- | --- |
| `.py` | [Python](python/) |
'''
        fenced_text = '''
```markdown
| Evidence | Package |
| --- | --- |
| `.py` | [Python](python/) |
```
'''
        published = skills.skill_routing_contract(published_text)
        candidate = skills.skill_routing_contract(fenced_text)
        self.assertTrue(published)
        self.assertTrue(skills.missing_routing_contracts(published, candidate))

    def test_latest_composition_preserves_invoked_lambda_and_nested_reachability(self) -> None:
        lambda_source = '''
def validate():
    deferred = lambda: Finding("PUBLIC_CODE", "visible")
    deferred()
'''
        self.assertEqual(
            extended_reachability.reachable_contracts(lambda_source, "sample.py")[(
                "sample.py",
                "validate",
                "PUBLIC_CODE",
            )],
            1,
        )

        nested_source = '''
def validate():
    def emit():
        Finding("PUBLIC_CODE", "visible")
    emit()
'''
        self.assertEqual(
            extended_reachability.reachable_contracts(nested_source, "sample.py")[(
                "sample.py",
                "validate.<locals>.emit",
                "PUBLIC_CODE",
            )],
            1,
        )

    def test_latest_composition_preserves_parameterized_lambda_and_nested_reachability(self) -> None:
        lambda_source = '''
def read_text(path, findings, code):
    Finding(code, "decode failed", path="sample")
def validate(root, findings):
    deferred = lambda: read_text(root / "LICENSE", findings, "LICENSE_ENCODING")
    deferred()
'''
        lambda_contracts = parameterized_reachability.reachable_parameterized_contracts(
            lambda_source,
            "sample.py",
        )
        self.assertEqual(len(lambda_contracts), 1)

        nested_source = '''
def read_text(path, findings, code):
    Finding(code, "decode failed", path="sample")
def validate(root, findings):
    def emit():
        read_text(root / "LICENSE", findings, "LICENSE_ENCODING")
    emit()
'''
        nested_contracts = parameterized_reachability.reachable_parameterized_contracts(
            nested_source,
            "sample.py",
        )
        self.assertEqual(len(nested_contracts), 1)


if __name__ == "__main__":
    unittest.main()
