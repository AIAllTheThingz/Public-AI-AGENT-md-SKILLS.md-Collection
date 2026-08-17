from __future__ import annotations

import importlib.util
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from helpers import REPO_ROOT


class ValidateAllBytecodeSideEffectTests(unittest.TestCase):
    def _load_validate_all_module(self):
        module_path = REPO_ROOT / "tools" / "validate-all" / "run_all.py"
        spec = importlib.util.spec_from_file_location(
            "validate_all_bytecode_side_effects", module_path
        )
        module = importlib.util.module_from_spec(spec)
        assert spec.loader is not None
        before = sys.dont_write_bytecode
        spec.loader.exec_module(module)
        self.assertEqual(
            sys.dont_write_bytecode,
            before,
            "importing validate-all must restore the caller's bytecode policy",
        )
        return module

    def test_python_bytecode_disabled_context_applies_to_children_and_restores_parent(self):
        module = self._load_validate_all_module()

        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            fixture = root / "fixture_module.py"
            fixture.write_text("VALUE = 42\n", encoding="utf-8")

            baseline_environment = os.environ.copy()
            baseline_environment.pop("PYTHONDONTWRITEBYTECODE", None)
            baseline_environment.pop("PYTHONPYCACHEPREFIX", None)
            baseline = subprocess.run(
                [sys.executable, "-c", "import fixture_module; print(fixture_module.VALUE)"],
                cwd=root,
                env=baseline_environment,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(baseline.returncode, 0, baseline.stdout + baseline.stderr)
            self.assertEqual(baseline.stdout.strip(), "42")
            self.assertTrue(
                list(root.rglob("*.pyc")),
                "control invocation must demonstrate that the fixture normally writes bytecode",
            )

            for cache in root.rglob("__pycache__"):
                shutil.rmtree(cache)

            previous_environment = os.environ.get("PYTHONDONTWRITEBYTECODE")
            previous_runtime = sys.dont_write_bytecode
            with module.python_bytecode_disabled():
                self.assertEqual(os.environ.get("PYTHONDONTWRITEBYTECODE"), "1")
                self.assertTrue(sys.dont_write_bytecode)
                read_only = subprocess.run(
                    [sys.executable, "-c", "import fixture_module; print(fixture_module.VALUE)"],
                    cwd=root,
                    text=True,
                    capture_output=True,
                    check=False,
                )

            self.assertEqual(os.environ.get("PYTHONDONTWRITEBYTECODE"), previous_environment)
            self.assertEqual(sys.dont_write_bytecode, previous_runtime)
            self.assertEqual(read_only.returncode, 0, read_only.stdout + read_only.stderr)
            self.assertEqual(read_only.stdout.strip(), "42")
            self.assertFalse(
                list(root.rglob("*.pyc")),
                "validation child processes must not write Python bytecode into the source tree",
            )
            self.assertFalse(
                list(root.rglob("__pycache__")),
                "validation child processes must not create __pycache__ directories in the source tree",
            )


if __name__ == "__main__":
    unittest.main()
