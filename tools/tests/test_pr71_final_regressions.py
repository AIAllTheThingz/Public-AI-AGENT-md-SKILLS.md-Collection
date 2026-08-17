from __future__ import annotations

import ast
import importlib.util
import os
import subprocess
import sys
import tempfile
import unittest
from collections import Counter
from pathlib import Path

from helpers import REPO_ROOT
from rc_reachability_semantics import statement_always_terminates
import test_rc_extended_finding_reachability as literal
import test_rc_parameterized_finding_reachability as parameterized
import test_rc_unnumbered_governance_semantics as unnumbered


ROOT_GOVERNANCE_PATHS = (
    "AGENTS.md",
    "MAINTAINERS.md",
    "RELEASE_POLICY.md",
    "MATURITY_POLICY.md",
)


def _load_validate_all_module():
    module_path = REPO_ROOT / "tools" / "validate-all" / "run_all.py"
    spec = importlib.util.spec_from_file_location("pr71_validate_all_regression", module_path)
    if spec is None or spec.loader is None:
        raise AssertionError("cannot load validate-all")
    module = importlib.util.module_from_spec(spec)
    previous = sys.dont_write_bytecode
    sys.dont_write_bytecode = True
    try:
        spec.loader.exec_module(module)
    finally:
        sys.dont_write_bytecode = previous
    return module


def _root_governance_contracts_at_checkpoint() -> Counter[tuple[str, str, str]]:
    contracts: Counter[tuple[str, str, str]] = Counter()
    for relative in ROOT_GOVERNANCE_PATHS:
        contracts.update(
            unnumbered.extract_unnumbered_governance_contracts(
                unnumbered.base.git_source_at(unnumbered.base.CHECKPOINT_COMMIT, relative),
                relative,
            )
        )
    return contracts


def _candidate_root_governance_contracts() -> Counter[tuple[str, str, str]]:
    contracts: Counter[tuple[str, str, str]] = Counter()
    for relative in ROOT_GOVERNANCE_PATHS:
        contracts.update(
            unnumbered.extract_unnumbered_governance_contracts(
                (REPO_ROOT / relative).read_text(encoding="utf-8"),
                relative,
            )
        )
    return contracts


class Pr71FinalRegressionTests(unittest.TestCase):
    def test_root_governance_unnumbered_controls_are_preserved(self):
        published = _root_governance_contracts_at_checkpoint()
        candidate = _candidate_root_governance_contracts()

        for relative in ROOT_GOVERNANCE_PATHS:
            self.assertTrue(
                any(path == relative for path, _section, _statement in published),
                f"checkpoint root governance contract unexpectedly empty for {relative}",
            )

        self.assertEqual(
            unnumbered.unnumbered_contract_findings(published, candidate),
            [],
            "root-level governance obligations must remain compatible with v0.10.0",
        )

    def test_exhaustive_match_with_terminal_catchall_makes_successor_unreachable(self):
        literal_source = '''
def validate(value):
    match value:
        case "known":
            return None
        case _:
            return None
    Finding("PUBLIC_CODE", "unreachable")
'''
        self.assertEqual(
            literal.reachable_contracts(literal_source, "sample.py"),
            Counter(),
        )

        parameterized_source = '''
def read_text(path, findings, code):
    Finding(code, "decode failed", path="sample")
def validate(root, findings, value):
    match value:
        case "known":
            return None
        case _:
            return None
    read_text(root / "LICENSE", findings, "LICENSE_ENCODING")
'''
        self.assertEqual(
            parameterized.reachable_parameterized_contracts(
                parameterized_source, "sample.py"
            ),
            set(),
        )

    def test_non_exhaustive_or_guarded_match_remains_fallthrough_capable(self):
        for source in (
            '''
def validate(value):
    match value:
        case "known":
            return None
    Finding("PUBLIC_CODE", "reachable")
''',
            '''
def validate(value, flag):
    match value:
        case _ if flag:
            return None
    Finding("PUBLIC_CODE", "reachable")
''',
        ):
            with self.subTest(source=source):
                contracts = literal.reachable_contracts(source, "sample.py")
                self.assertEqual(
                    contracts[("sample.py", "validate", "PUBLIC_CODE")],
                    1,
                )

    def test_capture_pattern_without_guard_is_irrefutable_and_terminal(self):
        tree = ast.parse(
            '''
def validate(value):
    match value:
        case captured:
            return None
'''
        )
        function = tree.body[0]
        self.assertIsInstance(function, ast.FunctionDef)
        self.assertTrue(statement_always_terminates(function.body[0]))

    def test_bytecode_reenabled_by_child_is_redirected_outside_source(self):
        module = _load_validate_all_module()
        with tempfile.TemporaryDirectory() as temp:
            source_root = Path(temp)
            fixture = source_root / "fixture_module.py"
            fixture.write_text("VALUE = 42\n", encoding="utf-8")

            previous_environment = {
                "PYTHONDONTWRITEBYTECODE": os.environ.get("PYTHONDONTWRITEBYTECODE"),
                "PYTHONPYCACHEPREFIX": os.environ.get("PYTHONPYCACHEPREFIX"),
            }
            previous_runtime = sys.dont_write_bytecode
            previous_prefix = sys.pycache_prefix

            with module.python_bytecode_disabled():
                cache_prefix = Path(os.environ["PYTHONPYCACHEPREFIX"])
                self.assertNotEqual(cache_prefix, source_root)
                completed = subprocess.run(
                    [
                        sys.executable,
                        "-c",
                        (
                            "import sys; "
                            "sys.dont_write_bytecode = False; "
                            "import fixture_module; "
                            "print(fixture_module.VALUE)"
                        ),
                    ],
                    cwd=source_root,
                    text=True,
                    capture_output=True,
                    check=False,
                )
                self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
                self.assertEqual(completed.stdout.strip(), "42")
                self.assertTrue(
                    list(cache_prefix.rglob("*.pyc")),
                    "the adversarial import should prove bytecode was redirected externally",
                )

            self.assertFalse(list(source_root.rglob("*.pyc")))
            self.assertFalse(list(source_root.rglob("__pycache__")))
            self.assertEqual(sys.dont_write_bytecode, previous_runtime)
            self.assertEqual(sys.pycache_prefix, previous_prefix)
            for name, value in previous_environment.items():
                self.assertEqual(os.environ.get(name), value)


if __name__ == "__main__":
    unittest.main()
