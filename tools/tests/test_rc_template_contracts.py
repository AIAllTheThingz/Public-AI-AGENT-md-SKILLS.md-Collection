from __future__ import annotations

import json
import re
import subprocess
import unittest

from helpers import REPO_ROOT

CHECKPOINT = REPO_ROOT / "releases" / "compatibility" / "0.10.0-checkpoint.json"
PLACEHOLDER_PATTERN = re.compile(r"\{\{(?P<name>[A-Z][A-Z0-9_]*)\}\}")
SECTION_PATTERN = re.compile(r"^##\s+(?P<title>.+?)\s*$", re.MULTILINE)


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


def template_contract(text: str) -> dict[str, set[str]]:
    return {
        "placeholders": set(PLACEHOLDER_PATTERN.findall(text)),
        "sections": {
            normalize_section(match.group("title"))
            for match in SECTION_PATTERN.finditer(text)
        },
    }


def template_contract_findings(
    path: str,
    published: dict[str, set[str]],
    candidate: dict[str, set[str]],
) -> list[str]:
    findings: list[str] = []
    for placeholder in sorted(published["placeholders"] - candidate["placeholders"]):
        findings.append(f"MISSING_TEMPLATE_PLACEHOLDER:{path}:{placeholder}")
    for section in sorted(published["sections"] - candidate["sections"]):
        findings.append(f"MISSING_TEMPLATE_SECTION:{path}:{section}")
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

    def test_placeholder_rename_and_required_section_removal_are_detected(self):
        published_text = """
# Completion
## Validation not performed
{{VALIDATION_NOT_PERFORMED}}
## Human review
{{HUMAN_REVIEW}}
"""
        renamed = published_text.replace(
            "{{VALIDATION_NOT_PERFORMED}}",
            "{{VALIDATION_SKIPPED}}",
        )
        removed_section = published_text.replace(
            "## Human review\n{{HUMAN_REVIEW}}\n",
            "{{HUMAN_REVIEW}}\n",
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

        compatible = published_text.replace("## Human review", "##   HUMAN review")
        self.assertEqual(
            template_contract_findings(
                "sample.md", published, template_contract(compatible)
            ),
            [],
        )


if __name__ == "__main__":
    unittest.main()
