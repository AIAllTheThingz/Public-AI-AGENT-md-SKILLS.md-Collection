from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from helpers import json_result, make_required_root, run_tool

DUPLICATE_DOC = "---\nid: example.duplicate\n---\n# Example\n"
BAD_UTF8 = b"Example \xff\xfe text\n"

# code -> edits applied to a valid root: (path, old text or None to create, new text or bytes)
CASES = {
    "AGENTS_INCOMPLETE": [("example/AGENTS.md", None, "# Too short\n")],
    "CODEOWNERS_INVALID": [(".github/CODEOWNERS", "* @AIAllTheThingz\n", "* @AIAllTheThingz\n/docs/\n")],
    "CODEOWNERS_OWNER_MISSING": [(".github/CODEOWNERS", "/tools/ @AIAllTheThingz", "/tools/ @example-owner")],
    "DUPLICATE_ID": [("a.md", None, DUPLICATE_DOC), ("b.md", None, DUPLICATE_DOC)],
    "JSON_INVALID": [("example.json", None, "{\n")],
    "LICENSE_DECLARATION_MISSING": [("README.md", "License: Apache-2.0", "License: example")],
    "LICENSING_POLICY_INVALID": [("LICENSING.md", "Apache-2.0", "Example-License")],
    "MAINTAINER_LIMITATION_MISSING": [("MAINTAINERS.md", "one active maintainer", "an example maintainer")],
    "MAINTAINER_ROSTER_INVALID": [("MAINTAINERS.md", "Metello Zuccolini @AIAllTheThingz", "Example Person @example")],
    "MARKDOWN_ENCODING": [("bad.md", None, b"# Bad \xff\xfe encoding\n")],
    "OWNERSHIP_DECLARATION_MISSING": [("AGENTS.md", "`.github/CODEOWNERS`", "the owners file")],
    "SPECIALIST_INDEPENDENCE_MISSING": [("MAINTAINERS.md", "must not be the author", "may be anyone")],
    "TEMPORARY_ARTIFACT": [("profile-build-failure.log", None, "example failure\n")],
    "CODEOWNERS_ENCODING": [(".github/CODEOWNERS", None, BAD_UTF8)],
    "LICENSE_DECLARATION_ENCODING": [("README.md", None, BAD_UTF8)],
    "LICENSE_ENCODING": [("LICENSE", None, BAD_UTF8)],
    "LICENSING_ENCODING": [("LICENSING.md", None, BAD_UTF8)],
    "MAINTAINERS_ENCODING": [("MAINTAINERS.md", None, BAD_UTF8)],
    "NOTICE_ENCODING": [("NOTICE", None, BAD_UTF8)],
    "OWNERSHIP_DECLARATION_ENCODING": [("CONTRIBUTING.md", None, BAD_UTF8)],
    "ROADMAP_ENCODING": [("ROADMAP.md", None, BAD_UTF8)],
}


class ValidateStandardsFindingCodeTests(unittest.TestCase):
    def test_each_finding_code_is_emitted(self):
        for code, edits in CASES.items():
            with self.subTest(code=code), tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                make_required_root(root)
                for name, old, new in edits:
                    path = root / name
                    path.parent.mkdir(parents=True, exist_ok=True)
                    if isinstance(new, bytes):
                        path.write_bytes(new)
                        continue
                    if old is not None:
                        text = path.read_text(encoding="utf-8")
                        self.assertIn(old, text)
                        new = text.replace(old, new)
                    path.write_text(new, encoding="utf-8")
                completed = run_tool(
                    "tools/validate-standards/validate_repository.py", "--format", "json", root=root
                )
                self.assertEqual(completed.returncode, 1, completed.stdout + completed.stderr)
                codes = {item["code"] for item in json_result(completed)["findings"]}
                self.assertIn(code, codes)


if __name__ == "__main__":
    unittest.main()
