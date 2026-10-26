from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from helpers import json_result, run_tool
from test_release import make_release_root


def _replace(path: str, old: str, new: str = ""):
    def mutate(root: Path) -> None:
        target = root / path
        text = target.read_text(encoding="utf-8")
        assert old in text, (path, old)
        target.write_text(text.replace(old, new), encoding="utf-8")
    return mutate


def _delete(path: str):
    return lambda root: (root / path).unlink()


CASES = {
    "CHANGELOG_UNRELEASED_MISSING": _replace("CHANGELOG.md", "## [Unreleased]\n"),
    "CHANGELOG_VERSION_MISSING": _replace("CHANGELOG.md", "## [0.9.0] - 2030-01-01\n"),
    "MATURITY_POLICY_SECTION_MISSING": _replace("MATURITY_POLICY.md", "## Review record\n"),
    "MIGRATION_NOTES_INCOMPLETE": _replace("releases/migrations/0.9.0.md", "## Required actions\n"),
    "MIGRATION_NOTES_MISSING": _delete("releases/migrations/0.9.0.md"),
    "RELEASE_FILE_MISSING": _delete("MATURITY_POLICY.md"),
    "RELEASE_NOTES_SECTION_MISSING": _replace("releases/0.9.0.md", "## Security\n"),
    "RELEASE_NOTES_VERSION_MISMATCH": _replace("releases/0.9.0.md", "# Public-Access-Agents 0.9.0", "# Public-Access-Agents 0.8.0"),
    "RELEASE_POLICY_MARKER_MISSING": _replace("RELEASE_POLICY.md", "90 calendar days\n"),
    "RELEASE_WORKFLOW_INCOMPLETE": _replace(".github/workflows/release.yml", "gh release create"),
    "RELEASE_WORKFLOW_MISSING": _delete(".github/workflows/release.yml"),
}


class ValidateReleaseFindingCodeTests(unittest.TestCase):
    def test_each_finding_code_is_emitted(self):
        for code, mutate in CASES.items():
            with self.subTest(code=code), tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                make_release_root(root)
                mutate(root)
                completed = run_tool("tools/release/validate_release.py", "--format", "json", root=root)
                codes = {item["code"] for item in json_result(completed)["findings"]}
                self.assertIn(code, codes, completed.stdout + completed.stderr)


if __name__ == "__main__":
    unittest.main()
