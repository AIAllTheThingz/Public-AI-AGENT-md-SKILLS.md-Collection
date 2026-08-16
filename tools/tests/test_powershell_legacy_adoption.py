from __future__ import annotations

import unittest

from helpers import REPO_ROOT


class PowerShellLegacyAdoptionTests(unittest.TestCase):
    def test_powershell_7_remains_default(self):
        readme = (REPO_ROOT / "languages" / "powershell" / "README.md").read_text(encoding="utf-8")
        agents = (REPO_ROOT / "languages" / "powershell" / "AGENTS.md").read_text(encoding="utf-8")
        self.assertIn("Target PowerShell 7.x and execute with `pwsh`", readme)
        self.assertIn("PowerShell 7.x executed with `pwsh` is the default runtime for new work", agents)

    def test_explicit_windows_powershell_51_path_is_evidence_bounded(self):
        overlay = (REPO_ROOT / "languages" / "powershell" / "standards" / "WINDOWS_POWERSHELL_51_COMPATIBILITY.md").read_text(encoding="utf-8")
        self.assertIn("Windows PowerShell 5.1", overlay)
        self.assertIn("requires validation with **`powershell.exe`**", overlay)
        self.assertIn("does not prove Windows PowerShell 5.1 runtime compatibility", overlay)
        self.assertIn("`NotRun` or `Blocked`", overlay)
        self.assertIn("does not make Windows PowerShell 5.1 a current greenfield baseline", overlay)

    def test_package_routes_explicit_legacy_adoption_to_overlay(self):
        readme = (REPO_ROOT / "languages" / "powershell" / "README.md").read_text(encoding="utf-8")
        agents = (REPO_ROOT / "languages" / "powershell" / "AGENTS.md").read_text(encoding="utf-8")
        for text in (readme, agents):
            self.assertIn("WINDOWS_POWERSHELL_51_COMPATIBILITY.md", text)
        self.assertIn("a `pwsh` result is not 5.1 runtime proof", readme)


if __name__ == "__main__":
    unittest.main()
