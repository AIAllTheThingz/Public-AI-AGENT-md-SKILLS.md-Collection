from __future__ import annotations

import json
import re
import unittest
from pathlib import Path

from helpers import REPO_ROOT

REVIEW_COMMIT = "ba4901c72f4c1fccda517280946f1fb1b6d2824c"


class MaturityDecisionTests(unittest.TestCase):
    def test_csharp_package_status_is_consistently_stable(self):
        status_files = []
        for path in sorted((REPO_ROOT / "languages" / "csharp").rglob("*.md")):
            text = path.read_text(encoding="utf-8")
            if not text.startswith("---\n"):
                continue
            end = text.find("\n---\n", 4)
            if end < 0:
                continue
            frontmatter = text[:end]
            match = re.search(r"^status:\s*(\S+)\s*$", frontmatter, re.MULTILINE)
            if match:
                status_files.append(path.relative_to(REPO_ROOT).as_posix())
                self.assertEqual(match.group(1), "stable", path)
        self.assertGreaterEqual(len(status_files), 10)

    def test_registry_promotes_only_csharp_from_initial_candidate_cohort(self):
        registry = json.loads((REPO_ROOT / "SOURCE_REVIEWS.json").read_text(encoding="utf-8"))
        maturity = {record["id"]: record["maturity"] for record in registry["records"]}
        self.assertEqual(maturity["languages-csharp"], "stable")
        self.assertEqual(maturity["languages-powershell"], "baseline")
        self.assertEqual(maturity["languages-terraform-opentofu"], "baseline")

    def test_csharp_review_pins_evidence_and_independent_gate(self):
        review = (REPO_ROOT / "maturity-reviews" / "csharp-baseline-to-stable-2026-08-16.md").read_text(encoding="utf-8")
        self.assertIn(REVIEW_COMMIT, review)
        self.assertIn("31962412526", review)
        self.assertIn("AIAllTheThingz/TheCertMaster", review)
        self.assertIn("AIAllTheThingz/WindowsScriptRunner", review)
        self.assertIn("2026-08-15", review)
        self.assertIn("independent C# specialist", review)
        self.assertIn("`approved`", review)
        self.assertIn("does **not** promote the separate `languages/dotnet` package", review)

    def test_deferred_candidates_record_real_blockers(self):
        powershell = (REPO_ROOT / "maturity-reviews" / "powershell-baseline-to-stable-2026-08-16.md").read_text(encoding="utf-8")
        terraform = (REPO_ROOT / "maturity-reviews" / "terraform-opentofu-baseline-to-stable-2026-08-16.md").read_text(encoding="utf-8")
        self.assertIn("`deferred`", powershell)
        self.assertIn("no `*.Tests.ps1` files", powershell)
        self.assertIn("`powershell.exe`", powershell)
        self.assertIn("`deferred`", terraform)
        self.assertIn("current count from #41 is zero", terraform)
        self.assertIn("two representative", terraform)

    def test_language_index_and_changelog_expose_decision_without_overclaim(self):
        language_index = (REPO_ROOT / "languages" / "README.md").read_text(encoding="utf-8")
        self.assertIn("| [C#](csharp/)", language_index)
        self.assertRegex(language_index, r"\| \[C#\]\(csharp/\).*\| Stable \|")
        changelog = (REPO_ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
        self.assertIn("proposed C# `baseline` → `stable`", changelog)
        self.assertIn("deferred PowerShell and Terraform/OpenTofu", changelog)


if __name__ == "__main__":
    unittest.main()
