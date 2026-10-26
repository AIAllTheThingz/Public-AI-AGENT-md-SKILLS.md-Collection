from __future__ import annotations

import json
import unittest
from pathlib import Path

import rc_normative_rule_contracts_base as rule_base
import test_rc_agent_skill_entrypoints as skills
import test_rc_numbered_rule_semantics as numbered
import test_rc_template_contracts as templates
import test_rc_unnumbered_governance_semantics as unnumbered
from helpers import require_git_history

# Regressions for the Markdown rule-contract family: rendered-content projection,
# candidate-only weakening of numbered rules and unnumbered governance, and the
# reviewed stable-root governance projection.

_CHECKPOINT_PATH = (
    rule_base.REPO_ROOT / "releases" / "compatibility" / "0.10.0-checkpoint.json"
)


def _is_root_policy_path(relative: str) -> bool:
    if not relative.endswith(".md"):
        return False
    name = Path(relative).name.casefold()
    return (
        name in {
            "agents.md",
            "maintainers.md",
            "security.md",
            "contributing.md",
            "pull_request_template.md",
        }
        or "policy" in name
    )


def _stable_root_policy_paths() -> tuple[str, ...]:
    checkpoint = json.loads(_CHECKPOINT_PATH.read_text(encoding="utf-8"))
    roots = checkpoint["stablePathGroups"]["root"]
    return tuple(sorted(path for path in roots if _is_root_policy_path(path)))


class RenderedMarkdownRuleContractTests(unittest.TestCase):
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
        self.assertIn("continuation text", rule_base.rendered_markdown(text))

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
        published = rule_base.extract_rule_contracts(
            published_text, "governance/demo.md"
        )
        candidate = rule_base.extract_rule_contracts(
            indented_text, "governance/demo.md"
        )
        self.assertTrue(
            rule_base.rule_contract_findings(published, candidate)
        )


class CandidateOnlyWeakeningTests(unittest.TestCase):
    def test_candidate_only_exception_field_is_incompatible(self) -> None:
        published_text = """
### SAMPLE-001

**Requirement:** Authentication is required.
"""
        weakened_text = published_text + """
**Exceptions:** Authentication may be skipped when documented.
"""
        editorial_text = published_text + """
**Rationale:** Authentication protects the service boundary.
"""

        published = numbered.extract_rule_field_contracts(
            published_text,
            "sample.md",
        )
        weakened = numbered.extract_rule_field_contracts(
            weakened_text,
            "sample.md",
        )
        editorial = numbered.extract_rule_field_contracts(
            editorial_text,
            "sample.md",
        )

        self.assertIn(
            "RULE_BEHAVIORAL_FIELD_ADDED:sample.md:SAMPLE-001:exceptions",
            numbered.rule_field_contract_findings(published, weakened),
        )
        self.assertEqual(
            numbered.rule_field_contract_findings(published, editorial),
            [],
        )

    def test_candidate_only_governance_permission_expansion_is_rejected(self) -> None:
        published_text = """
## Independent review

Independent review is required before high-risk work is merged.
"""
        candidate_text = published_text + """
- An author may merge without independent review when the change is urgent.
"""
        compatible_text = published_text + """
- Record additional independent-review evidence when available.
"""

        published = unnumbered.extract_unnumbered_governance_contracts(
            published_text,
            "AGENTS.md",
        )
        weakened = unnumbered.extract_unnumbered_governance_contracts(
            candidate_text,
            "AGENTS.md",
        )
        compatible = unnumbered.extract_unnumbered_governance_contracts(
            compatible_text,
            "AGENTS.md",
        )

        self.assertTrue(
            any(
                item.startswith("UNNUMBERED_GOVERNANCE_WEAKENING_ADDED:")
                for item in unnumbered.unnumbered_contract_findings(
                    published,
                    weakened,
                )
            )
        )
        self.assertEqual(
            unnumbered.unnumbered_contract_findings(published, compatible),
            [],
        )

    def test_exemption_label_is_behavioral(self) -> None:
        published_text = """
### SAMPLE-001

**Requirement:** Authentication is required.
"""
        candidate_text = published_text + """
**Exemptions:** Authentication may be skipped when documented.
"""
        published = numbered.extract_rule_field_contracts(published_text, "sample.md")
        candidate = numbered.extract_rule_field_contracts(candidate_text, "sample.md")
        self.assertIn(
            "RULE_BEHAVIORAL_FIELD_ADDED:sample.md:SAMPLE-001:exemptions",
            numbered.rule_field_contract_findings(published, candidate),
        )

    def test_neutral_label_cannot_hide_permission_expansion(self) -> None:
        published_text = """
### SAMPLE-001

**Requirement:** Authentication is required.
"""
        candidate_text = published_text + """
**Notes:** Authentication may be skipped when documented.
"""
        published = numbered.extract_rule_field_contracts(published_text, "sample.md")
        candidate = numbered.extract_rule_field_contracts(candidate_text, "sample.md")
        self.assertIn(
            "RULE_BEHAVIORAL_FIELD_ADDED:sample.md:SAMPLE-001:notes",
            numbered.rule_field_contract_findings(published, candidate),
        )

    def test_neutral_label_no_longer_mandatory_is_permission_expansion(self) -> None:
        published_text = """
### SAMPLE-001

**Requirement:** Authentication is required.
"""
        candidate_text = published_text + """
**Notes:** Authentication is no longer mandatory.
"""
        published = numbered.extract_rule_field_contracts(published_text, "sample.md")
        candidate = numbered.extract_rule_field_contracts(candidate_text, "sample.md")
        self.assertIn(
            "RULE_BEHAVIORAL_FIELD_ADDED:sample.md:SAMPLE-001:notes",
            numbered.rule_field_contract_findings(published, candidate),
        )

    def test_neutral_label_not_mandatory_is_permission_expansion(self) -> None:
        published_text = """
### SAMPLE-001

**Requirement:** Authentication is required.
"""
        candidate_text = published_text + """
**Notes:** Authentication is not mandatory.
"""
        published = numbered.extract_rule_field_contracts(published_text, "sample.md")
        candidate = numbered.extract_rule_field_contracts(candidate_text, "sample.md")
        self.assertIn(
            "RULE_BEHAVIORAL_FIELD_ADDED:sample.md:SAMPLE-001:notes",
            numbered.rule_field_contract_findings(published, candidate),
        )

    def test_neutral_label_deobligation_family_is_permission_expansion(self) -> None:
        published_text = """
### SAMPLE-001

**Requirement:** Authentication is required.
"""
        expected = "RULE_BEHAVIORAL_FIELD_ADDED:sample.md:SAMPLE-001:notes"
        for value in (
            "Authentication is not compulsory.",
            "Authentication is no longer obligatory.",
            "Authentication is not necessary.",
            "Authentication need not be performed.",
            "Authentication does not have to be performed.",
            "Authentication may be omitted.",
            "Authentication can be waived.",
        ):
            with self.subTest(value=value):
                candidate = numbered.extract_rule_field_contracts(
                    published_text + f"\n**Notes:** {value}\n",
                    "sample.md",
                )
                published = numbered.extract_rule_field_contracts(
                    published_text,
                    "sample.md",
                )
                self.assertIn(
                    expected,
                    numbered.rule_field_contract_findings(published, candidate),
                )

    def test_neutral_label_restrictive_deontic_text_is_not_permission_expansion(
        self,
    ) -> None:
        published_text = """
### SAMPLE-001

**Requirement:** Authentication is required.
"""
        for value in (
            "Authentication is not optional.",
            "Authentication is no longer optional.",
            "Authentication must not be skipped.",
            "Authentication may not be omitted.",
            "No waiver is permitted.",
            "Exceptions are not allowed.",
        ):
            with self.subTest(value=value):
                candidate = numbered.extract_rule_field_contracts(
                    published_text + f"\n**Notes:** {value}\n",
                    "sample.md",
                )
                published = numbered.extract_rule_field_contracts(
                    published_text,
                    "sample.md",
                )
                self.assertEqual(
                    numbered.rule_field_contract_findings(published, candidate),
                    [],
                )

    def test_neutral_editorial_label_is_not_permission_expansion(self) -> None:
        published_text = """
### SAMPLE-001

**Requirement:** Authentication is required.
"""
        candidate_text = published_text + """
**Notes:** Authentication terminology is used consistently in this section.
"""
        published = numbered.extract_rule_field_contracts(published_text, "sample.md")
        candidate = numbered.extract_rule_field_contracts(candidate_text, "sample.md")
        self.assertEqual(
            numbered.rule_field_contract_findings(published, candidate),
            [],
        )

    def test_unless_exception_to_published_obligation_is_rejected(self) -> None:
        published_text = """
## Independent review

Independent review is required before high-risk work is merged.
"""
        candidate_text = published_text + """
Independent review is required unless the author marks the change urgent.
"""
        published = unnumbered.extract_unnumbered_governance_contracts(
            published_text,
            "AGENTS.md",
        )
        candidate = unnumbered.extract_unnumbered_governance_contracts(
            candidate_text,
            "AGENTS.md",
        )
        self.assertTrue(
            any(
                item.startswith("UNNUMBERED_GOVERNANCE_WEAKENING_ADDED:")
                for item in unnumbered.unnumbered_contract_findings(
                    published,
                    candidate,
                )
            )
        )

    def test_modal_restatement_unless_exception_is_rejected(self) -> None:
        published_text = """
## Independent review

Independent review is required before high-risk work is merged.
"""
        candidate_text = published_text + """
Independent review must be performed unless the author marks the change urgent.
"""
        published = unnumbered.extract_unnumbered_governance_contracts(
            published_text,
            "AGENTS.md",
        )
        candidate = unnumbered.extract_unnumbered_governance_contracts(
            candidate_text,
            "AGENTS.md",
        )
        self.assertTrue(
            any(
                item.startswith("UNNUMBERED_GOVERNANCE_WEAKENING_ADDED:")
                for item in unnumbered.unnumbered_contract_findings(
                    published,
                    candidate,
                )
            )
        )

    def test_except_when_exception_to_published_obligation_is_rejected(self) -> None:
        published_text = """
## Independent review

Independent review is required before high-risk work is merged.
"""
        candidate_text = published_text + """
Independent review is required except when the author marks the change urgent.
"""
        published = unnumbered.extract_unnumbered_governance_contracts(
            published_text,
            "AGENTS.md",
        )
        candidate = unnumbered.extract_unnumbered_governance_contracts(
            candidate_text,
            "AGENTS.md",
        )
        self.assertTrue(
            unnumbered.unnumbered_contract_findings(published, candidate)
        )

    def test_additive_restrictive_unless_rule_is_not_misclassified(self) -> None:
        published_text = """
## Independent review

Independent review is required before high-risk work is merged.
"""
        candidate_text = published_text + """
Do not merge unless independent review succeeds.
"""
        published = unnumbered.extract_unnumbered_governance_contracts(
            published_text,
            "AGENTS.md",
        )
        candidate = unnumbered.extract_unnumbered_governance_contracts(
            candidate_text,
            "AGENTS.md",
        )
        self.assertEqual(
            unnumbered.unnumbered_contract_findings(published, candidate),
            [],
        )


class RootGovernanceProjectionTests(unittest.TestCase):
    def test_stable_root_policy_paths_come_from_published_checkpoint(self) -> None:
        paths = set(_stable_root_policy_paths())
        self.assertTrue(
            {
                "AGENTS.md",
                "MAINTAINERS.md",
                "RELEASE_POLICY.md",
                "MATURITY_POLICY.md",
                "SECURITY.md",
            }.issubset(paths)
        )

    def test_current_governance_contracts_remain_compatible(self) -> None:
        require_git_history(rule_base.CHECKPOINT_COMMIT)
        self.assertEqual(
            unnumbered.unnumbered_contract_findings(
                unnumbered.published_contracts(),
                unnumbered.candidate_contracts(),
            ),
            [],
        )

    def test_forward_release_narrative_stays_mutable(self) -> None:
        require_git_history(rule_base.CHECKPOINT_COMMIT)
        checkpoint = unnumbered.base.git_source_at(
            unnumbered.base.CHECKPOINT_COMMIT,
            "RELEASE_POLICY.md",
        )
        raw = unnumbered.extract_unnumbered_governance_contracts(
            checkpoint,
            "RELEASE_POLICY.md",
        )
        stable = unnumbered._stable_root_contracts(
            checkpoint,
            "RELEASE_POLICY.md",
        )
        historical = [
            contract
            for contract in raw
            if contract[0] == "RELEASE_POLICY.md"
            and contract[1] == "pre-1.0 policy"
            and contract[2].startswith("The repository originally prepared ")
        ]
        self.assertEqual(len(historical), 1)
        self.assertNotIn(historical[0], stable)

    def test_reported_root_policies_are_in_reviewed_projection(self) -> None:
        require_git_history(rule_base.CHECKPOINT_COMMIT)
        self.assertTrue(
            {
                "AGENTS.md",
                "MAINTAINERS.md",
                "RELEASE_POLICY.md",
                "MATURITY_POLICY.md",
                "SECURITY.md",
            }.issubset(set(unnumbered._published_normative_stable_root_paths()))
        )


class NumberedRuleEvidenceTests(unittest.TestCase):
    def test_gov_secdev_002_expected_evidence_is_explicitly_protected(self):
        require_git_history(rule_base.CHECKPOINT_COMMIT)
        path = "governance/SECURE_DEVELOPMENT_POLICY.md"
        published_text = numbered.base.git_source_at(
            numbered.base.CHECKPOINT_COMMIT,
            path,
        )
        published = numbered.extract_rule_field_contracts(
            published_text,
            path,
        )
        matching = [
            fields
            for contract_path, rule_id, fields in published
            if contract_path == path and rule_id == "GOV-SECDEV-002"
        ]
        self.assertEqual(len(matching), 1)
        self.assertEqual(
            matching[0]["expected evidence"],
            "Configuration and tests demonstrate secure behavior.",
        )

        weakened_text = published_text.replace(
            "\n\n**Expected evidence:** Configuration and tests demonstrate secure behavior.",
            "",
            1,
        )
        findings = numbered.rule_field_contract_findings(
            published,
            numbered.extract_rule_field_contracts(weakened_text, path),
        )
        self.assertIn(
            f"RULE_FIELD_MISSING:{path}:GOV-SECDEV-002:expected evidence",
            findings,
        )


if __name__ == "__main__":
    unittest.main()
