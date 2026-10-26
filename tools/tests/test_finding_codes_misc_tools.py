"""Behavior tests: each published finding code of these tools is emitted by the real tool."""

from __future__ import annotations

import json
import shutil
import tempfile
import unittest
from pathlib import Path

from helpers import REPO_ROOT, json_result, run_tool


def codes(completed) -> set[str]:
    return {finding["code"] for finding in json_result(completed)["findings"]}


class CheckLinksFindingCodes(unittest.TestCase):
    def test_link_codes(self):
        cases = {
            "LINK_ABSOLUTE_PATH": "[x](/etc/passwd)",
            "LINK_ESCAPES_ROOT": "[x](../outside.md)",
            "LINK_MISSING_ANCHOR": "[x](#no-such-heading)",
            "LINK_UNSAFE_SCHEME": "[x](javascript:alert(1))",
        }
        for code, link in cases.items():
            with self.subTest(code=code), tempfile.TemporaryDirectory() as temp:
                root = Path(temp) / "root"
                root.mkdir()
                (root / "README.md").write_text(f"# Title\n\n{link}\n", encoding="utf-8")
                completed = run_tool("tools/check-links/check_links.py", "--format", "json", root=root)
                self.assertIn(code, codes(completed), completed.stdout + completed.stderr)


class ValidateSchemasFindingCodes(unittest.TestCase):
    def run_schemas(self, root: Path):
        return run_tool(
            "tools/validate-schemas/validate_schemas.py",
            "--skip-repository-instances",
            "--format",
            "json",
            root=root,
        )

    def test_schema_missing(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "schemas").mkdir()
            completed = self.run_schemas(root)
            self.assertIn("SCHEMA_MISSING", codes(completed), completed.stdout + completed.stderr)

    def test_schema_id_duplicate(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            shutil.copytree(REPO_ROOT / "schemas", root / "schemas")
            source = json.loads((root / "schemas" / "artifact-record.schema.json").read_text(encoding="utf-8"))
            target_path = root / "schemas" / "completion-result.schema.json"
            target = json.loads(target_path.read_text(encoding="utf-8"))
            target["$id"] = source["$id"]
            target_path.write_text(json.dumps(target), encoding="utf-8")
            completed = self.run_schemas(root)
            self.assertIn("SCHEMA_ID_DUPLICATE", codes(completed), completed.stdout + completed.stderr)


class ComposeAgentsFindingCodes(unittest.TestCase):
    def test_composition_no_disciplines(self):
        with tempfile.TemporaryDirectory() as temp:
            manifest = Path(temp) / "project-manifest.json"
            manifest.write_text(json.dumps({
                "schemaVersion": "1.0.0",
                "name": "example-service",
                "profile": "WEB_API",
                "languages": ["python"],
                "disciplines": [],
            }), encoding="utf-8")
            completed = run_tool(
                "tools/compose-agents/compose_agents.py",
                "--manifest", str(manifest),
                "--dry-run",
                "--format", "json",
            )
            self.assertIn("COMPOSITION_NO_DISCIPLINES", codes(completed), completed.stdout + completed.stderr)


class ValidateAllFindingCodes(unittest.TestCase):
    def test_validator_and_unit_test_failures(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            ignore = shutil.ignore_patterns("__pycache__")
            for name in ("check-links", "lib"):
                shutil.copytree(REPO_ROOT / "tools" / name, root / "tools" / name, ignore=ignore)
            (root / "README.md").write_text("[x](missing.md)\n", encoding="utf-8")
            tests = root / "tools" / "tests"
            tests.mkdir()
            (tests / "test_x.py").write_text(
                "import unittest\n\n\nclass X(unittest.TestCase):\n"
                "    def test_fails(self):\n        self.fail('fixture')\n",
                encoding="utf-8",
            )
            completed = run_tool(
                "tools/validate-all/run_all.py",
                "--tool", "check-links",
                "--include-tests",
                "--format", "json",
                root=root,
            )
            found = codes(completed)
            for code in ("VALIDATOR_FAILED", "UNIT_TESTS_FAILED"):
                with self.subTest(code=code):
                    self.assertIn(code, found, completed.stdout + completed.stderr)


if __name__ == "__main__":
    unittest.main()
