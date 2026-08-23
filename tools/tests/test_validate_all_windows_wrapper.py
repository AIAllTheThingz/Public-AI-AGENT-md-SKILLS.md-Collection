from __future__ import annotations

import importlib.util
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from helpers import REPO_ROOT


def load_validate_all_module():
    module_path = REPO_ROOT / "tools" / "validate-all" / "run_all.py"
    spec = importlib.util.spec_from_file_location("validate_all_windows_wrapper", module_path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    previous = sys.dont_write_bytecode
    sys.dont_write_bytecode = True
    try:
        spec.loader.exec_module(module)
    finally:
        sys.dont_write_bytecode = previous
    return module


class ValidateAllWindowsWrapperTests(unittest.TestCase):
    def test_history_wrapper_exposes_windows_cmd_launcher(self):
        module = load_validate_all_module()
        with tempfile.TemporaryDirectory() as temp:
            wrapper = Path(temp) / "git"
            module._write_history_git_wrapper(wrapper)

            self.assertTrue(wrapper.is_file())
            cmd_wrapper = wrapper.with_suffix(".cmd")
            self.assertTrue(
                cmd_wrapper.is_file(),
                "Windows PATH lookup requires a PATHEXT-compatible git.cmd launcher",
            )
            command = cmd_wrapper.read_text(encoding="utf-8")
            self.assertIn(sys.executable, command)
            self.assertIn("%~dp0git", command)
            self.assertIn("%*", command)

    def test_history_wrapper_routes_child_python_git_calls(self):
        module = load_validate_all_module()
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "archive"
            root.mkdir()
            bundle = root / module.COMPATIBILITY_HISTORY_BUNDLE
            bundle.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(REPO_ROOT / module.COMPATIBILITY_HISTORY_BUNDLE, bundle)

            with module.compatibility_history(root):
                completed = subprocess.run(
                    [
                        sys.executable,
                        "-c",
                        (
                            "import subprocess, sys; "
                            "run = subprocess.run("
                            "['git', '-C', sys.argv[1], 'rev-parse', "
                            "'--show-toplevel'], "
                            "text=True, encoding='utf-8', capture_output=True, check=False); "
                            "print(run.stdout, end=''); "
                            "print(run.stderr, end='', file=sys.stderr); "
                            "raise SystemExit(run.returncode)"
                        ),
                        str(root),
                    ],
                    text=True,
                    capture_output=True,
                    check=False,
                )

            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertEqual(Path(completed.stdout.strip()).resolve(), root.resolve())


if __name__ == "__main__":
    unittest.main()
