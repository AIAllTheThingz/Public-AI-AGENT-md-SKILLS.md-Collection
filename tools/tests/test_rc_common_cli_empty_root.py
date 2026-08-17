from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

import test_rc_common_cli_behavior as _common


class ReleaseCandidateCommonCliInvalidRootTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.contract = json.loads(_common.TOOL_BEHAVIOR.read_text(encoding="utf-8"))
        cls.tools = cls.contract["commonCliToolPaths"]

    @staticmethod
    def tool_specific_args(
        tool_path: str, *, manifest: Path, output_dir: Path
    ) -> tuple[str, ...]:
        if tool_path == "tools/generate-manifest/generate_manifest.py":
            return (
                "--name",
                "compat-invalid-root",
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

    def test_every_common_tool_rejects_a_root_with_tool_specific_invalidity(self):
        with tempfile.TemporaryDirectory() as temp:
            temp_root = Path(temp)
            manifest = temp_root / "project-manifest.json"
            manifest.write_text(
                json.dumps(
                    {
                        "name": "compat-invalid-root",
                        "profile": "CLI_TOOL",
                        "languages": ["csharp"],
                        "disciplines": [],
                    }
                ),
                encoding="utf-8",
            )

            for index, tool_path in enumerate(self.tools):
                with self.subTest(tool=tool_path):
                    invalid_root = temp_root / f"invalid-root-{index}"
                    invalid_root.mkdir()
                    if tool_path == "tools/check-links/check_links.py":
                        # An empty directory is a valid no-op for the link checker,
                        # so give this tool a root-local broken link. Other common
                        # tools reject the missing repository contract directly.
                        (invalid_root / "README.md").write_text(
                            "[broken](missing-target.md)\n",
                            encoding="utf-8",
                        )

                    output = temp_root / f"invalid-root-{index}.json"
                    output_dir = temp_root / f"bundle-{index}"
                    completed = _common.run_tool(
                        tool_path,
                        "--root",
                        str(invalid_root),
                        "--format",
                        "json",
                        "--output",
                        str(output),
                        "--quiet",
                        *self.tool_specific_args(
                            tool_path,
                            manifest=manifest,
                            output_dir=output_dir,
                        ),
                    )
                    self.assertEqual(completed.stdout, "")
                    self.assertTrue(output.is_file(), f"{tool_path} did not honor --output")
                    payload = json.loads(output.read_text(encoding="utf-8"))
                    _common.assert_published_result_contract(self, payload, self.contract)
                    self.assertNotEqual(
                        completed.returncode,
                        0,
                        f"{tool_path} ignored invalid content under the declared --root",
                    )
                    self.assertNotEqual(
                        payload.get("status"),
                        "passed",
                        f"{tool_path} reported passed for a deliberately invalid --root",
                    )
                    self.assertTrue(
                        payload.get("findings"),
                        f"{tool_path} rejected the alternate root without a finding",
                    )


if __name__ == "__main__":
    unittest.main()
