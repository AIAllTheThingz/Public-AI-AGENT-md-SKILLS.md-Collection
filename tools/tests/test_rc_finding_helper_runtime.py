from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from helpers import json_result, run_tool


def write_text(root: Path, relative: str, content: str) -> None:
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


class ReleaseCandidateFindingHelperRuntimeTests(unittest.TestCase):
    def test_release_head_tag_missing_is_exercised_through_git_output(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            write_text(root, "VERSION", "1.0.0-rc.1\n")
            write_text(
                root,
                "CHANGELOG.md",
                "# Changelog\n\n## [Unreleased]\n\n- None.\n\n"
                "## [1.0.0-rc.1] - 2026-08-16\n",
            )
            write_text(
                root,
                "RELEASE_POLICY.md",
                "# Release Policy\n\n"
                "## Repository semantic versioning\n\n"
                "## Pre-1.0 policy\n\n"
                "## Deprecation windows\n\n"
                "90 calendar days\n\n180 calendar days\n\n"
                "## Release process\n\n"
                "## Git tags\n\nvMAJOR.MINOR.PATCH\n\n"
                "## GitHub releases\n\n"
                "## Release artifacts and checksums\n\n"
                "## 1.0.0 compatibility gate\n",
            )
            write_text(
                root,
                "MATURITY_POLICY.md",
                "# Maturity Policy\n\n"
                "## Maturity states\n\n"
                "## Promotion requirements\n\n"
                "## Baseline to stable review\n\n"
                "## Demotion and deprecation\n\n"
                "## Review record\n",
            )
            write_text(
                root,
                "releases/1.0.0-rc.1.md",
                "# Public-Access-Agents 1.0.0-rc.1\n\n"
                "## Breaking changes\n\n"
                "## Normative changes\n\n"
                "## Editorial changes\n\n"
                "## Deprecations\n\n"
                "## Migration notes\n\n"
                "## Security\n\n"
                "## Known limitations\n",
            )
            write_text(
                root,
                "releases/migrations/1.0.0-rc.1.md",
                "# Migration\n\n## Required actions\n\n- None.\n",
            )
            write_text(
                root,
                ".github/workflows/release.yml",
                "tags:\n  - 'v*'\n# tools/release/build_release.py\n"
                "# gh release create\n# SHA256SUMS.txt\n",
            )

            completed = run_tool(
                "tools/release/validate_release.py",
                "--format",
                "json",
                "--root",
                str(root),
                "--require-head-tag",
            )

        self.assertEqual(completed.returncode, 1, completed.stdout + completed.stderr)
        findings = json_result(completed).get("findings", [])
        codes = {finding["code"] for finding in findings}
        self.assertIn("RELEASE_HEAD_TAG_MISSING", codes)


if __name__ == "__main__":
    unittest.main()
