from __future__ import annotations

import json
import unittest

from helpers import REPO_ROOT, run_tool

TOOL_BEHAVIOR_PATH = (
    REPO_ROOT / "releases" / "compatibility" / "0.10.0-tool-behavior.json"
)


class ReleaseCandidateCliFormatValueTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.contract = json.loads(TOOL_BEHAVIOR_PATH.read_text(encoding="utf-8"))

    def test_every_published_format_value_is_accepted_by_common_tools(self):
        values = self.contract["formatValues"]
        self.assertEqual(set(values), {"text", "json"})
        for relative in self.contract["commonCliToolPaths"]:
            for value in values:
                with self.subTest(tool=relative, format=value):
                    # Put --format before --help so argparse must accept the published
                    # value before the help action exits. This exercises the stable
                    # parser contract without requiring tool-specific operational input.
                    completed = run_tool(relative, "--format", value, "--help")
                    self.assertEqual(
                        completed.returncode,
                        0,
                        completed.stdout + completed.stderr,
                    )
                    self.assertIn("--format", completed.stdout)


if __name__ == "__main__":
    unittest.main()
