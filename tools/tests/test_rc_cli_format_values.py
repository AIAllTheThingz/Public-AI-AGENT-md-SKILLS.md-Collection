from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from helpers import REPO_ROOT

TOOL_BEHAVIOR_PATH = (
    REPO_ROOT / "releases" / "compatibility" / "0.10.0-tool-behavior.json"
)


def run_tool(tool_path: str, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(REPO_ROOT / tool_path), *args],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )


def tool_specific_args(
    tool_path: str, *, manifest: Path, output_dir: Path
) -> tuple[str, ...]:
    if tool_path == "tools/generate-manifest/generate_manifest.py":
        return (
            "--name",
            "compat-format-rendering",
            "--profile",
            "CLI_TOOL",
            "--language",
            "csharp",
            "--dry-run",
        )
    if tool_path == "tools/compose-agents/compose_agents.py":
        return (
            "--manifest",
            str(manifest),
            "--output-dir",
            str(output_dir),
            "--dry-run",
        )
    return ()


def assert_json_contract(
    testcase: unittest.TestCase,
    payload: dict[str, object],
    contract: dict[str, object],
) -> None:
    result_contract = contract["resultContract"]
    for field in result_contract["requiredTopLevelFields"]:
        testcase.assertIn(field, payload)
    testcase.assertIsInstance(payload["tool"], str)
    testcase.assertTrue(payload["tool"])
    testcase.assertIsInstance(payload["version"], str)
    testcase.assertTrue(payload["version"])
    testcase.assertIn(payload["status"], set(result_contract["statusValues"]))
    testcase.assertIsInstance(payload["summary"], dict)
    testcase.assertIsInstance(payload["findings"], list)
    testcase.assertIsInstance(payload["metadata"], dict)
    for finding in payload["findings"]:
        testcase.assertIsInstance(finding, dict)
        for field in result_contract["requiredFindingFields"]:
            testcase.assertIn(field, finding)
        testcase.assertIsInstance(finding["code"], str)
        testcase.assertTrue(finding["code"])
        testcase.assertIn(
            finding["severity"],
            set(result_contract["findingSeverityValues"]),
        )
        testcase.assertIsInstance(finding["message"], str)
        testcase.assertTrue(finding["message"])


class ReleaseCandidateCliFormatValueTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.contract = json.loads(TOOL_BEHAVIOR_PATH.read_text(encoding="utf-8"))

    def test_every_published_format_value_renders_real_tool_results(self):
        values = self.contract["formatValues"]
        self.assertEqual(set(values), {"text", "json"})

        with tempfile.TemporaryDirectory() as temp:
            temp_root = Path(temp)
            manifest = temp_root / "project-manifest.json"
            manifest.write_text(
                json.dumps(
                    {
                        "name": "compat-format-rendering",
                        "profile": "CLI_TOOL",
                        "languages": ["csharp"],
                        "disciplines": [],
                    }
                ),
                encoding="utf-8",
            )

            for index, relative in enumerate(self.contract["commonCliToolPaths"]):
                with self.subTest(tool=relative):
                    output_dir = temp_root / f"bundle-{index}"
                    rendered: dict[str, str] = {}
                    json_payload: dict[str, object] | None = None

                    for value in values:
                        output = temp_root / f"result-{index}-{value}.txt"
                        completed = run_tool(
                            relative,
                            "--root",
                            str(REPO_ROOT),
                            "--format",
                            value,
                            "--output",
                            str(output),
                            "--quiet",
                            *tool_specific_args(
                                relative,
                                manifest=manifest,
                                output_dir=output_dir,
                            ),
                        )
                        self.assertEqual(
                            completed.returncode,
                            0,
                            completed.stdout + completed.stderr,
                        )
                        self.assertEqual(completed.stdout, "")
                        self.assertTrue(output.is_file())
                        rendered[value] = output.read_text(encoding="utf-8")

                        if value == "json":
                            json_payload = json.loads(rendered[value])
                            assert_json_contract(self, json_payload, self.contract)

                    self.assertIsNotNone(json_payload)
                    assert json_payload is not None
                    text = rendered["text"]
                    self.assertFalse(text.lstrip().startswith("{"))
                    self.assertEqual(
                        text.splitlines()[0],
                        f"{json_payload['tool']}: {json_payload['status']}",
                    )
                    for key, summary_value in sorted(json_payload["summary"].items()):
                        self.assertIn(f"  {key}: {summary_value}", text)
                    for finding in json_payload["findings"]:
                        self.assertIn(
                            f"[{finding['severity'].upper()}] {finding['code']}",
                            text,
                        )
                    if (
                        not json_payload["findings"]
                        and json_payload["status"] == "passed"
                    ):
                        self.assertIn("No findings.", text)


if __name__ == "__main__":
    unittest.main()
