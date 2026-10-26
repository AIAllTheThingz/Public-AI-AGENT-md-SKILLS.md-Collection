from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from helpers import json_result, run_tool

SCRIPT = "tools/validate-tools/validate_tools.py"


def write(root: Path, files: dict[str, str]) -> None:
    for name, content in files.items():
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")


class ValidateToolsFindingCodeTests(unittest.TestCase):
    def codes(self, files: dict[str, str], *args: str) -> set[str]:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "tools").mkdir()
            write(root, files)
            completed = run_tool(SCRIPT, "--format", "json", *args, root=root)
            return {finding["code"] for finding in json_result(completed)["findings"]}

    def assert_codes(self, codes: set[str], expected: list[str]) -> None:
        for code in expected:
            with self.subTest(code=code):
                self.assertIn(code, codes)

    def test_empty_tools_tree(self):
        codes = self.codes({})
        self.assert_codes(codes, [
            "DEPENDENCY_INPUT_MISSING",
            "TOOL_COLLECTION_FILE_MISSING",
            "TOOL_CONTRACT_INVALID",
            "TOOL_PACKAGE_FILE_MISSING",
            "TOOL_TEST_COVERAGE",
        ])

    def test_broken_tools_tree(self):
        codes = self.codes({
            "tools/no-id.md": "# No front matter\n",
            "tools/first.md": "---\nid: example-doc\n---\n",
            "tools/second.md": "---\nid: example-doc\n---\n",
            "tools/validate-standards/README.md": "This is a planned tool.\n",
            "tools/validate-standards/validate_repository.py": "def broken(:\n",
            "tools/validate-schemas/requirements.txt": "PyYAML==6.0.3\n",
            "tools/tests/test_fails.py": "import unittest\n\nclass T(unittest.TestCase):\n    def test_fails(self):\n        self.fail()\n",
            ".github/workflows/invalid.yml": "jobs: [\n",
            ".github/workflows/actions.yml": (
                "jobs:\n  build:\n    steps:\n      - uses: 5\n      - uses: docker://example.invalid/image:1\n"
            ),
        }, "--run-unit-tests")
        self.assert_codes(codes, [
            "DEPENDENCY_LOCK_MISSING",
            "TOOL_COMPILE",
            "TOOL_DOC_ID_DUPLICATE",
            "TOOL_DOC_ID_MISSING",
            "TOOL_README_THIN",
            "TOOL_SHEBANG",
            "TOOL_STILL_PLANNED",
            "TOOL_TESTS_FAILED",
            "WORKFLOW_ACTION_INVALID",
            "WORKFLOW_DOCKER_NOT_PINNED",
            "WORKFLOW_YAML_INVALID",
        ])


if __name__ == "__main__":
    unittest.main()
