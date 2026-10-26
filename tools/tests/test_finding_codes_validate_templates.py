from __future__ import annotations

import shutil
import tempfile
import unittest
from pathlib import Path

from helpers import REPO_ROOT, json_result, run_tool

TOOL = "tools/validate-templates/validate_templates.py"
# Assembled at runtime so this file does not itself contain a secret-like literal.
FAKE_AWS_KEY = "AKIA" + "EXAMPLEFAKEKEY00"


def append(path: Path, text: str) -> None:
    path.write_text(path.read_text(encoding="utf-8") + text, encoding="utf-8")


CASES = {
    "TEMPLATE_COLLECTION_FILE_MISSING": lambda t: (t / "AUTHORING_GUIDE.md").unlink(),
    "TEMPLATE_STABLE_PATH_MISSING": lambda t: (t / "risk" / "RISK_ASSESSMENT_TEMPLATE.md").unlink(),
    "TEMPLATE_PACKAGE_FILE_MISSING": lambda t: (t / "release" / "examples" / "EXAMPLE.md").unlink(),
    "TEMPLATE_ID_MISSING": lambda t: (t / "no_id.md").write_text("# No front matter\n", encoding="utf-8"),
    "TEMPLATE_ID_DUPLICATE": lambda t: shutil.copyfile(t / "README.md", t / "duplicate.md"),
    "TEMPLATE_README_THIN": lambda t: (t / "release" / "README.md").write_text("# Thin\n", encoding="utf-8"),
    "TEMPLATE_NO_PLACEHOLDERS": lambda t: (t / "release" / "RELEASE_PLAN_TEMPLATE.md").write_text("# Plan\n", encoding="utf-8"),
    "TEMPLATE_PLACEHOLDER_INVALID": lambda t: append(t / "release" / "RELEASE_PLAN_TEMPLATE.md", "\n{{bad-name}}\n"),
    "TEMPLATE_PLACEHOLDER_UNDOCUMENTED": lambda t: append(t / "release" / "RELEASE_PLAN_TEMPLATE.md", "\n{{FIXTURE_ONLY_TOKEN}}\n"),
    "TEMPLATE_JSON_INVALID": lambda t: append(t / "project-manifest" / "PROJECT_MANIFEST_TEMPLATE.json", "\n}\n"),
    "TEMPLATE_EXAMPLE_PLACEHOLDER": lambda t: append(t / "release" / "examples" / "EXAMPLE.md", "\n{{LEFTOVER}}\n"),
    "TEMPLATE_EXAMPLE_UNFINISHED": lambda t: append(t / "release" / "examples" / "EXAMPLE.md", "\nOwner: TBD\n"),
    "TEMPLATE_EXAMPLE_SECRET": lambda t: append(t / "release" / "examples" / "EXAMPLE.md", f"\nKey: {FAKE_AWS_KEY}\n"),
    "TEMPLATE_EXAMPLE_SCHEMA": lambda t: (t / "project-manifest" / "examples" / "EXAMPLE.json").write_text("{}\n", encoding="utf-8"),
    "TEMPLATE_EXAMPLE_JSON": lambda t: (t / "project-manifest" / "examples" / "EXAMPLE.json").write_text("{\n", encoding="utf-8"),
    "TEMPLATE_CHECKLIST_DECISION": lambda t: (t / "release" / "REVIEW_CHECKLIST.md").write_text("# Checklist\n", encoding="utf-8"),
}


class ValidateTemplatesFindingCodeTests(unittest.TestCase):
    def test_each_finding_code_is_emitted(self):
        for code, mutate in CASES.items():
            with self.subTest(code=code), tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                shutil.copytree(REPO_ROOT / "templates", root / "templates")
                shutil.copytree(REPO_ROOT / "schemas", root / "schemas")
                mutate(root / "templates")
                completed = run_tool(TOOL, "--format", "json", root=root)
                codes = {finding["code"] for finding in json_result(completed)["findings"]}
                self.assertIn(code, codes, completed.stdout + completed.stderr)
                self.assertNotEqual(completed.returncode, 0)


if __name__ == "__main__":
    unittest.main()
