from __future__ import annotations

import ast
import json
import re
import unittest

import rc_normative_rule_contracts_base as rule_base
import test_rc_agent_skill_entrypoints as skills
import test_rc_numbered_rule_semantics as numbered
import test_rc_template_contracts as templates
import test_rc_unnumbered_governance_semantics as unnumbered
import test_rc_zzzzzzzzzzzzzzzzzzzzzzzzzzz_left_to_right_expression_execution as expression_execution


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
# extractor. These lookups are global at call time, so both immutable published
# source and the current candidate are compared under the same rendering rules.
rule_base.rendered_markdown = _rendered_markdown
numbered.visible_markdown = _rendered_markdown
unnumbered.visible_markdown = _rendered_markdown
templates.rendered_markdown = _rendered_markdown
skills.visible_markdown = _rendered_markdown


# Attribute lookup can execute user code or fail even when evaluating its
# receiver is harmless. It is therefore an execution prerequisite, not a
# structurally safe sibling. Retain the previous narrow safe classifier for all
# other expression forms while making attribute success conservative/unknown.
_previous_structurally_safe = expression_execution._structurally_safe


def _structurally_safe(node: ast.AST) -> bool:
    if isinstance(node, ast.Attribute):
        return False
    return _previous_structurally_safe(node)


expression_execution._structurally_safe = _structurally_safe


class ReleaseCandidateRenderedMarkdownAndAttributePrerequisiteTests(unittest.TestCase):
    def test_attribute_lookup_before_literal_finding_is_an_execution_prerequisite(self) -> None:
        direct = '''
def validate(findings):
    findings.append(Finding("PUBLIC_CODE", "visible"))
'''
        guarded = '''
def validate(findings):
    obj = None
    (obj.missing, findings.append(Finding("PUBLIC_CODE", "visible")))
'''
        expected = expression_execution.literal_base.finding_semantic_signatures(direct)
        actual = expression_execution.literal_base.finding_semantic_signatures(guarded)
        self.assertNotEqual(expected, actual)

        sink_expected = expression_execution.sink_execution.finding_semantic_signatures_with_sink(direct)
        sink_actual = expression_execution.sink_execution.finding_semantic_signatures_with_sink(guarded)
        self.assertNotEqual(sink_expected, sink_actual)

        payload = json.loads(actual["PUBLIC_CODE"][0])
        self.assertTrue(
            any(
                marker.startswith("tuple:1:requires-prior-evaluation")
                for marker in payload["context"]
            ),
            payload,
        )

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


if __name__ == "__main__":
    unittest.main()
