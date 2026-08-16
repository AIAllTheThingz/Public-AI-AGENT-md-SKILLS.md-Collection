from __future__ import annotations

import unittest

from helpers import REPO_ROOT


class DownstreamAdoptionEvidenceTests(unittest.TestCase):
    def test_first_pilot_record_is_real_and_pinned(self):
        record = (REPO_ROOT / "adoption-pilots" / "2026-08-16.md").read_text(encoding="utf-8")
        self.assertIn("`v0.10.0`", record)
        self.assertIn("`83c73f3ab9a049ff2321d463164fcf98fb453a9c`", record)
        for repo in (
            "AIAllTheThingz/TheCertMaster",
            "AIAllTheThingz/Enterprise-PS-Scripts",
            "AIAllTheThingz/WindowsScriptRunner",
        ):
            self.assertIn(repo, record)
        for shape in (
            "application/service software",
            "infrastructure/internal automation",
            "mixed application/infrastructure system",
        ):
            self.assertIn(shape, record)

    def test_pilot_record_preserves_nonpassing_evidence_and_findings(self):
        record = (REPO_ROOT / "adoption-pilots" / "2026-08-16.md").read_text(encoding="utf-8")
        self.assertIn("**Failed** because no `*.Tests.ps1` files were found", record)
        self.assertIn("**Failed on Ubuntu**", record)
        self.assertIn("baseline review `Blocked`", record)
        self.assertIn("issue #65", record)
        self.assertIn("issue #66", record)
        self.assertIn("Enterprise-PS-Scripts#1", record)

    def test_pilot_record_does_not_overstate_maturity(self):
        record = (REPO_ROOT / "adoption-pilots" / "2026-08-16.md").read_text(encoding="utf-8")
        self.assertIn("They do not promote any package automatically", record)
        self.assertIn("Terraform/OpenTofu", record)
        self.assertIn("insufficient for a Terraform/OpenTofu stable-maturity decision", record)
        self.assertIn("independent specialist review", record)


if __name__ == "__main__":
    unittest.main()
