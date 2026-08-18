from __future__ import annotations

import json
import re
import subprocess
import unittest

from helpers import REPO_ROOT

CHECKPOINT = REPO_ROOT / "releases" / "compatibility" / "0.10.0-checkpoint.json"
PLACEHOLDER_PATTERN = re.compile(r"\{\{(?P<name>[A-Z][A-Z0-9_]*)\}\}")
SECTION_PATTERN = re.compile(
    r"^##\s+(?P<title>.+?)\s*$\n(?P<body>.*?)(?=^##\s+|\Z)",
    re.MULTILINE | re.DOTALL,
)
SECTION_HEADING_PATTERN = re.compile(r"^##\s+(?P<title>.+?)\s*$")
OBLIGATION_PATTERN = re.compile(
    r"\b(must(?:\s+not)?|shall(?:\s+not)?|may\s+not|cannot|do\s+not|only|required)\b",
    re.IGNORECASE,
)
ORDERED_LIST_PATTERN = re.compile(r"^\d+[.)]\s+")
LIST_MARKER_PATTERN = re.compile(r"^(?:[-*+]|\d+[.)])\s+")
BLOCKQUOTE_PATTERN = re.compile(r"^(?:>\s*)+")
IMPERATIVE_PREFIXES = (
    "include ",
    "record ",
    "document ",
    "provide ",
    "identify ",
    "verify ",
    "capture ",
    "retain ",
    "preserve ",
    "replace ",
    "remove ",
    "state ",
    "describe ",
    "list ",
    "explain ",
    "link ",
    "mark ",
    "report ",
    "note ",
    "select ",
    "use ",
    "keep ",
    "confirm ",
    "review ",
    "validate ",
    "test ",
    "ensure ",
    "obtain ",
)
ROOT_SECTION = "<root>"


def git_output(*args: str) -> str:
    completed = subprocess.run(
        ["git", "-C", str(REPO_ROOT), *args],
        text=True,
        capture_output=True,
        check=False,
    )
    if completed.returncode != 0:
        raise AssertionError(completed.stderr.strip() or "git command failed")
    return completed.stdout


def git_source_at(revision: str, relative: str) -> str:
    return git_output("show", f"{revision}:{relative}")


def normalize_section(title: str) -> str:
    return " ".join(title.split()).casefold()


def normalize_obligation(line: str) -> str:
    value = re.sub(r"[`*_]+", "", line.strip())
    value = re.sub(r"\s+", " ", value).strip()
    return value.rstrip(". :;").casefold()


def normalize_placeholder_field_label(line: str) -> str:
    """Return the stable field label preceding a placeholder, if one exists."""
    value = BLOCKQUOTE_PATTERN.sub("", line.strip())
    value = LIST_MARKER_PATTERN.sub("", value)
    value = re.sub(r"[`*_]+", "", value).strip()
    first_placeholder = PLACEHOLDER_PATTERN.search(value)
    if first_placeholder is None:
        return ""
    prefix = value[: first_placeholder.start()].strip()
    if not prefix.endswith(":"):
        return ""
    return " ".join(prefix[:-1].split()).casefold()


def placeholder_bindings(text: str) -> set[tuple[str, str, str]]:
    """Bind each placeholder to its H2 section and published field label."""
    bindings: set[tuple[str, str, str]] = set()
    current_section = ROOT_SECTION
    in_fence = False

    for raw_line in text.splitlines():
        stripped = raw_line.strip()
        if stripped.startswith("```") or stripped.startswith("~~~"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue

        heading = SECTION_HEADING_PATTERN.match(raw_line)
        if heading is not None:
            current_section = normalize_section(heading.group("title"))
            continue

        names = PLACEHOLDER_PATTERN.findall(raw_line)
        if not names:
            continue
        label = normalize_placeholder_field_label(raw_line)
        for name in names:
            bindings.add((name, current_section, label))

    return bindings


def section_obligations(body: str) -> set[str]:
    obligations: set[str] = set()
    for raw_line in body.splitlines():
        line = BLOCKQUOTE_PATTERN.sub("", raw_line.strip())
        if not line or PLACEHOLDER_PATTERN.fullmatch(line):
            continue
        ordered = ORDERED_LIST_PATTERN.match(line) is not None
        plain = LIST_MARKER_PATTERN.sub("", line)
        normalized = normalize_obligation(plain)
        # Published ordered steps are themselves behavioral instructions. Preserve
        # them even when the imperative verb is outside the common-prefix list;
        # this prevents numbered requirements from disappearing merely because the
        # list marker obscures the leading verb during classification.
        if (
            ordered
            or OBLIGATION_PATTERN.search(plain)
            or normalized.startswith(IMPERATIVE_PREFIXES)
        ):
            obligations.add(normalized)
    return obligations


def template_contract(text: str) -> dict[str, object]:
    sections: set[str] = set()
    obligations: dict[str, set[str]] = {}
    for match in SECTION_PATTERN.finditer(text):
        title = normalize_section(match.group("title"))
        sections.add(title)
        obligations[title] = section_obligations(match.group("body"))
    return {
        "placeholders": set(PLACEHOLDER_PATTERN.findall(text)),
        "placeholderBindings": placeholder_bindings(text),
        "sections": sections,
        "obligations": obligations,
    }


def template_contract_findings(
    path: str,
    published: dict[str, object],
    candidate: dict[str, object],
) -> list[str]:
    findings: list[str] = []
    published_placeholders = published["placeholders"]
    candidate_placeholders = candidate["placeholders"]
    published_bindings = published["placeholderBindings"]
    candidate_bindings = candidate["placeholderBindings"]
    published_sections = published["sections"]
    candidate_sections = candidate["sections"]
    published_obligations = published["obligations"]
    candidate_obligations = candidate["obligations"]

    for placeholder in sorted(published_placeholders - candidate_placeholders):
        findings.append(f"MISSING_TEMPLATE_PLACEHOLDER:{path}:{placeholder}")
    for placeholder, section, label in sorted(published_bindings - candidate_bindings):
        findings.append(
            "MISSING_TEMPLATE_PLACEHOLDER_BINDING:"
            f"{path}:{placeholder}:{section}:{label or '<standalone>'}"
        )
    for section in sorted(published_sections - candidate_sections):
        findings.append(f"MISSING_TEMPLATE_SECTION:{path}:{section}")
    for section, expected in sorted(published_obligations.items()):
        current = candidate_obligations.get(section, set())
        for obligation in sorted(expected - current):
            findings.append(
                f"MISSING_TEMPLATE_OBLIGATION:{path}:{section}:{obligation}"
            )
    return findings


class ReleaseCandidateTemplateContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.checkpoint = json.loads(CHECKPOINT.read_text(encoding="utf-8"))
        cls.source_commit = cls.checkpoint["sourceCommit"]
        cls.template_paths = cls.checkpoint["stablePathGroups"]["templates"]

    def test_every_published_stable_template_contract_is_preserved(self):
        self.assertEqual(len(self.template_paths), 7)
        for relative in self.template_paths:
            with self.subTest(template=relative):
                published = template_contract(
                    git_source_at(self.source_commit, relative)
                )
                candidate_path = REPO_ROOT / relative
                self.assertTrue(candidate_path.is_file())
                candidate = template_contract(
                    candidate_path.read_text(encoding="utf-8")
                )
                self.assertEqual(
                    template_contract_findings(relative, published, candidate),
                    [],
                )

        completion_path = "templates/completion/COMPLETION_REPORT_TEMPLATE.md"
        completion = template_contract(
            git_source_at(self.source_commit, completion_path)
        )
        self.assertIn("VALIDATION_NOT_PERFORMED", completion["placeholders"])
        self.assertIn("HUMAN_REVIEW", completion["placeholders"])
        self.assertIn("human review", completion["sections"])
        self.assertIn(
            "the report must not claim a stronger state than the evidence supports",
            completion["obligations"]["human review"],
        )

        exception_path = "templates/exception/EXCEPTION_RECORD_TEMPLATE.md"
        exception = template_contract(git_source_at(self.source_commit, exception_path))
        self.assertIn(
            ("APPROVER", "approval", "approver"),
            exception["placeholderBindings"],
        )
        self.assertIn(
            "approval must come from an accountable human with delegated authority",
            exception["obligations"]["approval"],
        )

    def test_numbered_template_imperatives_are_preserved(self):
        published_text = """
## Instructions
1. Record the exact validation command.
5. Preserve compatibility unless an approved migration says otherwise.
"""
        published = template_contract(published_text)
        self.assertIn(
            "preserve compatibility unless an approved migration says otherwise",
            published["obligations"]["instructions"],
        )
        removed = published_text.replace(
            "5. Preserve compatibility unless an approved migration says otherwise.\n",
            "",
        )
        self.assertIn(
            "MISSING_TEMPLATE_OBLIGATION:sample.md:instructions:preserve compatibility unless an approved migration says otherwise",
            template_contract_findings(
                "sample.md", published, template_contract(removed)
            ),
        )

    def test_blockquoted_template_imperatives_are_preserved(self):
        published_text = """
## Adoption
> Replace every documented placeholder before adoption. Remove this note after validation.
"""
        published = template_contract(published_text)
        obligation = (
            "replace every documented placeholder before adoption. remove this note after validation"
        )
        self.assertIn(obligation, published["obligations"]["adoption"])
        removed = published_text.replace(
            "> Replace every documented placeholder before adoption. Remove this note after validation.\n",
            "",
        )
        self.assertIn(
            f"MISSING_TEMPLATE_OBLIGATION:sample.md:adoption:{obligation}",
            template_contract_findings(
                "sample.md", published, template_contract(removed)
            ),
        )

    def test_placeholder_section_and_field_label_are_preserved(self):
        published_text = """
# Exception
## Business need
{{BUSINESS_NEED}}
## Approval
- Approver: {{APPROVER}}
- Approval date: `{{APPROVAL_DATE}}`
"""
        published = template_contract(published_text)
        moved = published_text.replace(
            "## Business need\n{{BUSINESS_NEED}}\n## Approval\n- Approver: {{APPROVER}}\n",
            "## Business need\n{{BUSINESS_NEED}}\n- Approver: {{APPROVER}}\n## Approval\n",
        )
        relabeled = published_text.replace(
            "- Approver: {{APPROVER}}",
            "- Reviewer: {{APPROVER}}",
        )

        binding = "MISSING_TEMPLATE_PLACEHOLDER_BINDING:sample.md:APPROVER:approval:approver"
        self.assertIn(
            binding,
            template_contract_findings(
                "sample.md", published, template_contract(moved)
            ),
        )
        self.assertIn(
            binding,
            template_contract_findings(
                "sample.md", published, template_contract(relabeled)
            ),
        )

        compatible = published_text.replace(
            "- Approver: {{APPROVER}}",
            "* **Approver:** {{APPROVER}}",
        )
        self.assertEqual(
            template_contract_findings(
                "sample.md", published, template_contract(compatible)
            ),
            [],
        )

    def test_root_placeholder_field_labels_are_preserved(self):
        published_text = """
# Authorization
- Requested by: {{REQUESTED_BY}}
- Owner: `{{OWNER}}`
## Scope
{{SCOPE}}
"""
        published = template_contract(published_text)
        self.assertIn(
            ("REQUESTED_BY", ROOT_SECTION, "requested by"),
            published["placeholderBindings"],
        )
        self.assertIn(
            ("OWNER", ROOT_SECTION, "owner"),
            published["placeholderBindings"],
        )
        self.assertIn(
            ("SCOPE", "scope", ""),
            published["placeholderBindings"],
        )

    def test_placeholder_section_and_normative_meaning_changes_are_detected(self):
        published_text = """
# Completion
## Validation not performed
{{VALIDATION_NOT_PERFORMED}}
## Human review
{{HUMAN_REVIEW}}
The report must not claim a stronger state than the evidence supports.
## Approval
Approval must come from an accountable human with delegated authority.
"""
        renamed = published_text.replace(
            "{{VALIDATION_NOT_PERFORMED}}",
            "{{VALIDATION_SKIPPED}}",
        )
        removed_section = published_text.replace(
            "## Human review\n{{HUMAN_REVIEW}}\n",
            "{{HUMAN_REVIEW}}\n",
        )
        weakened_review = published_text.replace(
            "The report must not claim a stronger state than the evidence supports.\n",
            "The report summarizes the work.\n",
        )
        weakened_approval = published_text.replace(
            "Approval must come from an accountable human with delegated authority.\n",
            "Approval may be recorded here.\n",
        )
        published = template_contract(published_text)

        self.assertIn(
            "MISSING_TEMPLATE_PLACEHOLDER:sample.md:VALIDATION_NOT_PERFORMED",
            template_contract_findings(
                "sample.md", published, template_contract(renamed)
            ),
        )
        self.assertIn(
            "MISSING_TEMPLATE_SECTION:sample.md:human review",
            template_contract_findings(
                "sample.md", published, template_contract(removed_section)
            ),
        )
        self.assertTrue(
            any(
                finding.startswith(
                    "MISSING_TEMPLATE_OBLIGATION:sample.md:human review:"
                )
                for finding in template_contract_findings(
                    "sample.md", published, template_contract(weakened_review)
                )
            )
        )
        self.assertTrue(
            any(
                finding.startswith("MISSING_TEMPLATE_OBLIGATION:sample.md:approval:")
                for finding in template_contract_findings(
                    "sample.md", published, template_contract(weakened_approval)
                )
            )
        )

        compatible = published_text.replace("## Human review", "##   HUMAN review")
        self.assertEqual(
            template_contract_findings(
                "sample.md", published, template_contract(compatible)
            ),
            [],
        )


if __name__ == "__main__":
    unittest.main()
