from __future__ import annotations

import contextlib
import importlib.util
import io
import json
import sys
import unittest
from pathlib import Path

from helpers import REPO_ROOT

LIB_ROOT = REPO_ROOT / "tools" / "lib"
if str(LIB_ROOT) not in sys.path:
    sys.path.insert(0, str(LIB_ROOT))

from standards_tools import Finding, ToolResult

TOOL_BEHAVIOR = REPO_ROOT / "releases" / "compatibility" / "0.10.0-tool-behavior.json"


def load_tool(path: str, index: int):
    module_path = REPO_ROOT / path
    spec = importlib.util.spec_from_file_location(f"rc_cli_exit_probe_{index}", module_path)
    if spec is None or spec.loader is None:
        raise AssertionError(f"cannot load stable CLI: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class ReleaseCandidateCommonCliExitCodeTests(unittest.TestCase):
    def test_every_common_cli_maps_failed_tool_result_to_validation_failure(self):
        contract = json.loads(TOOL_BEHAVIOR.read_text(encoding="utf-8"))
        expected = contract["exitCodeContract"]["validationFailure"]
        self.assertEqual(expected, 1)

        def failed_result(_args):
            return ToolResult.from_findings(
                tool="compat-exit-probe",
                version="1.0.0",
                findings=[Finding("COMPAT_EXIT_PROBE", "expected validation failure")],
            )

        for index, tool_path in enumerate(contract["commonCliToolPaths"]):
            with self.subTest(tool=tool_path):
                module = load_tool(tool_path, index)
                self.assertTrue(hasattr(module, "main"), tool_path)
                self.assertTrue(hasattr(module, "run"), tool_path)
                module.run = failed_result
                stdout = io.StringIO()
                stderr = io.StringIO()
                with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
                    return_code = module.main(["--format", "json"])
                self.assertEqual(
                    return_code,
                    expected,
                    f"{tool_path} did not map a failed ToolResult to validationFailure",
                )


if __name__ == "__main__":
    unittest.main()
