from __future__ import annotations

import ast
import importlib.util
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from helpers import REPO_ROOT, require_git_history
import rc_compatibility_gate_base as compatibility
import rc_normative_rule_contracts_base as normative
import test_rc_agent_skill_entrypoints as agent_skills
import test_rc_template_contracts as template_contracts
import test_rc_unnumbered_governance_semantics as unnumbered


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


def _load_module(name: str, relative: str):
    module_path = REPO_ROOT / relative
    spec = importlib.util.spec_from_file_location(name, module_path)
    if spec is None or spec.loader is None:
        raise AssertionError(f"cannot load {relative}")
    module = importlib.util.module_from_spec(spec)
    previous = sys.dont_write_bytecode
    module_directory = str(module_path.parent)
    sys.dont_write_bytecode = True
    sys.path.insert(0, module_directory)
    try:
        spec.loader.exec_module(module)
    finally:
        sys.path.remove(module_directory)
        sys.dont_write_bytecode = previous
    return module


def _keyword_constant(call: ast.Call, name: str):
    for keyword in call.keywords:
        if keyword.arg == name and isinstance(keyword.value, ast.Constant):
            return keyword.value.value
    return None


def _is_git_text_subprocess(call: ast.Call, relative: Path) -> bool:
    if not (
        isinstance(call.func, ast.Attribute)
        and isinstance(call.func.value, ast.Name)
        and call.func.value.id == "subprocess"
        and call.func.attr in {"run", "Popen"}
        and _keyword_constant(call, "text") is True
        and call.args
    ):
        return False

    command = call.args[0]
    if isinstance(command, (ast.List, ast.Tuple)) and command.elts:
        executable = command.elts[0]
        if isinstance(executable, ast.Constant) and isinstance(executable.value, str):
            return executable.value.casefold() in {"git", "git.exe", "git.cmd", "git.bat"}
        if isinstance(executable, ast.Name):
            return executable.id == "real_git"
    return (
        relative.as_posix() == "tools/tests/test_validate_all.py"
        and isinstance(command, ast.Name)
        and command.id == "command"
    )


class Pr71FinalRegressionTests(unittest.TestCase):
    def test_git_text_subprocess_boundaries_declare_utf8(self):
        offenders: list[str] = []
        tools_root = REPO_ROOT / "tools"
        for path in sorted(tools_root.rglob("*.py")):
            relative = path.relative_to(REPO_ROOT)
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(relative))
            for call in (node for node in ast.walk(tree) if isinstance(node, ast.Call)):
                if not _is_git_text_subprocess(call, relative):
                    continue
                if _keyword_constant(call, "encoding") != "utf-8":
                    offenders.append(f"{relative.as_posix()}:{call.lineno}")

        self.assertEqual(offenders, [])

    def test_checkpoint_git_sources_use_utf8_under_non_utf8_locale(self):
        require_git_history(compatibility.CHECKPOINT_COMMIT)
        build_release = _load_module(
            "pr71_build_release_regression",
            "tools/release/build_release.py",
        )
        validate_release = _load_module(
            "pr71_validate_release_regression",
            "tools/release/validate_release.py",
        )
        revision = compatibility.CHECKPOINT_COMMIT
        relative = "RELEASE_POLICY.md"

        with mock.patch("locale.getencoding", return_value="cp1252"):
            checkpoints = (
                compatibility.git_source_at(revision, relative),
                normative.git_source_at(revision, relative),
                agent_skills.git_source_at(revision, relative),
                template_contracts.git_source_at(revision, relative),
                build_release.run_git(
                    REPO_ROOT,
                    "show",
                    f"{revision}:{relative}",
                ),
                validate_release.git_output(
                    REPO_ROOT,
                    "show",
                    f"{revision}:{relative}",
                ),
            )
            object_sha = agent_skills.git_object_sha(revision, relative)

        for checkpoint in checkpoints:
            self.assertIn("\u201cProbably compatible\u201d", checkpoint)
        self.assertRegex(object_sha, r"\A[0-9a-f]{40}\Z")

    def test_checkpoint_git_source_preserves_git_errors(self):
        asserting_helpers = (
            compatibility.git_source_at,
            normative.git_source_at,
            agent_skills.git_source_at,
            template_contracts.git_source_at,
        )
        for source_at in asserting_helpers:
            with self.subTest(helper=source_at.__module__):
                with self.assertRaises(AssertionError):
                    source_at(
                        "missing-checkpoint-revision",
                        "RELEASE_POLICY.md",
                    )

        with self.assertRaises(AssertionError):
            agent_skills.git_object_sha(
                "missing-checkpoint-revision",
                "RELEASE_POLICY.md",
            )

        build_release = _load_module(
            "pr71_build_release_error_regression",
            "tools/release/build_release.py",
        )
        validate_release = _load_module(
            "pr71_validate_release_error_regression",
            "tools/release/validate_release.py",
        )
        with self.assertRaises(RuntimeError):
            build_release.run_git(REPO_ROOT, "show", "missing-checkpoint-revision:path")
        self.assertIsNone(
            validate_release.git_output(
                REPO_ROOT,
                "show",
                "missing-checkpoint-revision:path",
            )
        )

    def test_root_governance_unnumbered_controls_are_preserved(self):
        require_git_history(unnumbered.base.CHECKPOINT_COMMIT)
        root_paths = unnumbered._published_normative_stable_root_paths()
        published = unnumbered._root_governance_contracts_at_checkpoint()
        candidate = unnumbered._candidate_root_governance_contracts()

        # These were the concrete gaps that exposed the danger of a four-file
        # hand-maintained list. Keep them as sentinels while deriving the full
        # protected set from the published stable-root checkpoint.
        self.assertTrue(
            {
                "AGENTS.md",
                "MAINTAINERS.md",
                "RELEASE_POLICY.md",
                "MATURITY_POLICY.md",
                "SECURITY.md",
                "CONTRIBUTING.md",
                ".github/pull_request_template.md",
            }.issubset(set(root_paths)),
            root_paths,
        )
        self.assertFalse(
            unnumbered.FORWARD_MOVING_INFORMATIONAL_ROOT_PATHS & set(root_paths),
            "release/index/status documents must remain forward-mutable",
        )

        for relative in root_paths:
            self.assertTrue(
                any(path == relative for path, _section, _statement in published),
                f"checkpoint root governance contract unexpectedly empty for {relative}",
            )

        self.assertEqual(
            unnumbered.unnumbered_contract_findings(published, candidate),
            [],
            "normative stable-root obligations must remain compatible with v0.10.0",
        )

    def test_security_reporting_prohibition_is_a_stable_root_contract(self):
        require_git_history(unnumbered.base.CHECKPOINT_COMMIT)
        checkpoint = unnumbered.base.git_source_at(
            unnumbered.base.CHECKPOINT_COMMIT,
            "SECURITY.md",
        )
        published = unnumbered._stable_root_contracts(checkpoint, "SECURITY.md")
        reporting_controls = [
            statement
            for path, _section, statement in published
            if path == "SECURITY.md"
            and "do not open a public issue for an exploitable vulnerability"
            in statement.casefold()
        ]
        self.assertEqual(len(reporting_controls), 1)

        weakened = checkpoint.replace(
            "Do not open a public issue for an exploitable vulnerability",
            "A public issue may be opened for an exploitable vulnerability",
            1,
        )
        candidate = unnumbered._stable_root_contracts(weakened, "SECURITY.md")
        self.assertTrue(
            unnumbered.unnumbered_contract_findings(published, candidate),
            "weakening the published confidential-reporting control must be detected",
        )

    def test_forward_release_state_narrative_is_not_a_frozen_contract(self):
        require_git_history(unnumbered.base.CHECKPOINT_COMMIT)
        checkpoint = unnumbered.base.git_source_at(
            unnumbered.base.CHECKPOINT_COMMIT,
            "RELEASE_POLICY.md",
        )
        raw = unnumbered.extract_unnumbered_governance_contracts(
            checkpoint,
            "RELEASE_POLICY.md",
        )
        stable = unnumbered._stable_root_contracts(checkpoint, "RELEASE_POLICY.md")

        historical = [
            contract
            for contract in raw
            if contract[0] == "RELEASE_POLICY.md"
            and contract[1] == "pre-1.0 policy"
            and contract[2].startswith("The repository originally prepared ")
        ]
        self.assertEqual(len(historical), 1)
        self.assertNotIn(historical[0], stable)
        self.assertTrue(
            any(
                path == "RELEASE_POLICY.md" and section == "pre-1.0 policy"
                for path, section, _statement in stable
            ),
            "durable Pre-1.0 obligations must remain protected",
        )

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
