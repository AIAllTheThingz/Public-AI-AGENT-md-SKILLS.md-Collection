from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from helpers import json_result, run_tool


class CheckLinksTests(unittest.TestCase):
    def test_relative_link_and_anchor_pass(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "a.md").write_text("# A\n\n[Target](b.md#section)\n", encoding="utf-8")
            (root / "b.md").write_text("# B\n\n## Section\n", encoding="utf-8")
            completed = run_tool("tools/check-links/check_links.py", "--format", "json", root=root)
            self.assertEqual(completed.returncode, 0, completed.stdout)

    def test_missing_link_fails(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "a.md").write_text("[Missing](missing.md)\n", encoding="utf-8")
            completed = run_tool("tools/check-links/check_links.py", "--format", "json", root=root)
            self.assertEqual(completed.returncode, 1)
            codes = {item["code"] for item in json_result(completed)["findings"]}
            self.assertIn("LINK_MISSING_TARGET", codes)

    def test_line_number_counts_lines_inside_code(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            text = "# Doc\n\n```text\none\ntwo\nthree\n```\n\n`multi\nline`\n\n[Missing](missing.md)\n"
            (root / "a.md").write_text(text, encoding="utf-8")
            completed = run_tool("tools/check-links/check_links.py", "--format", "json", root=root)
            findings = json_result(completed)["findings"]
            self.assertEqual([item["line"] for item in findings], [12])


if __name__ == "__main__":
    unittest.main()
