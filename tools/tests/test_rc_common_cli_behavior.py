from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from helpers import REPO_ROOT

TOOL_BEHAVIOR = REPO_ROOT / "releases" / "compatibility" / "0.10.0-tool-behavior.json"


def run_tool(tool_path: str, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(REPO_ROOT / tool_path), *args],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )


class ReleaseCandidateCommonCliBehaviorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.contract = json.loads(TOOL_BEHAVIOR.read_text(encoding="utf-8"))
        cls.tools = cls.contract["commonCliToolPaths"]

    def tool_specific_args(
        self, tool_path: str, *, manifest: Path, output_dir: Path
    ) -> tuple[str, ...]:
        if tool_path == "tools/generate-manifest/generate_manifest.py":
            return (
                "--name",
                "compat-common-cli",
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

    def invoke(
        self,
        tool_path: str,
        *,
        root: Path,
        result_output: Path,
        manifest: Path,
        output_dir: Path,
    ) -> tuple[subprocess.CompletedProcess[str], dict[str, object]]:
        completed = run_tool(
            tool_path,
            "--root",
            str(root),
            "--format",
            "json",
            "--output",
            str(result_output),
            "--quiet",
            *self.tool_specific_args(
                tool_path, manifest=manifest, output_dir=output_dir
            ),
        )
        self.assertEqual(
            completed.stdout,
            "",
            f"{tool_path} did not honor --quiet",
        )
        self.assertTrue(
            result_output.is_file(),
            f"{tool_path} did not honor --output",
        )
        payload = json.loads(result_output.read_text(encoding="utf-8"))
        self.assertIn(payload.get("status"), {"passed", "failed", "error"})
        return completed, payload

    def test_root_output_and_quiet_behavior_for_every_common_stable_tool(self):
        self.assertGreaterEqual(len(self.tools), 10)

        with tempfile.TemporaryDirectory() as temp:
            temp_root = Path(temp)
            empty_root = temp_root / "empty-root"
            empty_root.mkdir()
            manifest = temp_root / "project-manifest.json"
            manifest.write_text(
                json.dumps(
                    {
                        "name": "compat-common-cli",
                        "profile": "CLI_TOOL",
                        "languages": ["csharp"],
                        "disciplines": [],
                    }
                ),
                encoding="utf-8",
            )

            for index, tool_path in enumerate(self.tools):
                with self.subTest(tool=tool_path):
                    valid_output = temp_root / f"valid-{index}.json"
                    invalid_output = temp_root / f"invalid-{index}.json"
                    output_dir = temp_root / f"bundle-{index}"

                    valid_completed, valid_payload = self.invoke(
                        tool_path,
                        root=REPO_ROOT,
                        result_output=valid_output,
                        manifest=manifest,
                        output_dir=output_dir,
                    )
                    invalid_completed, invalid_payload = self.invoke(
                        tool_path,
                        root=empty_root,
                        result_output=invalid_output,
                        manifest=manifest,
                        output_dir=output_dir,
                    )

                    self.assertEqual(
                        valid_completed.returncode,
                        0,
                        f"{tool_path} did not successfully exercise the published root",
                    )
                    self.assertTrue(
                        invalid_completed.returncode != valid_completed.returncode
                        or invalid_payload != valid_payload,
                        f"{tool_path} appears to ignore --root",
                    )
                    self.assertFalse(
                        invalid_completed.returncode == 0
                        and invalid_payload.get("status") == "passed"
                        and invalid_payload == valid_payload,
                        f"{tool_path} produced the same passing result for an empty --root",
                    )


if __name__ == "__main__":
    unittest.main()
