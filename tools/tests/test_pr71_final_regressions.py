from __future__ import annotations

import ast
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest
from collections import Counter
from pathlib import Path
from unittest import mock

from helpers import REPO_ROOT
import rc_compatibility_gate_base as compatibility
import rc_finding_code_contracts_base as finding_codes
import rc_normative_rule_contracts_base as normative
import rc_parameterized_finding_codes_base as parameterized_codes
from rc_reachability_semantics import statement_always_terminates
import test_rc_agent_skill_entrypoints as agent_skills
import test_rc_extended_finding_reachability as literal
import test_rc_finding_helper_runtime as finding_runtime
import test_rc_finding_reachability as finding_reachability
import test_rc_parameterized_finding_helper_semantics as parameterized_helpers
import test_rc_parameterized_finding_reachability as parameterized
import test_rc_template_contracts as template_contracts
import test_rc_unnumbered_governance_semantics as unnumbered
import test_rc_writer_safety as writer_safety


CHECKPOINT_INVENTORY_PATH = (
    REPO_ROOT / "releases" / "compatibility" / "0.10.0-checkpoint.json"
)

# These stable root documents are deliberately forward-moving status/index
# surfaces rather than durable policy authorities. Their current-version,
# readiness, and roadmap prose must advance after publication without turning
# every version bump into a compatibility break. Normative root documents such
# as SECURITY.md, CONTRIBUTING.md, MAINTAINERS.md, MATURITY_POLICY.md,
# RELEASE_POLICY.md, and the PR template remain derived from the authenticated
# stable-root checkpoint and protected semantically.
FORWARD_MOVING_INFORMATIONAL_ROOT_PATHS = frozenset(
    {
        "README.md",
        "CATALOG.md",
        "CHANGELOG.md",
        "ROADMAP.md",
    }
)

# This paragraph is deliberately forward-moving release-state narrative, not a
# stable governance obligation.  The immutable v0.10.0 copy said the next
# intended publication was v0.10.0; after publication the correct forward-only
# text names 1.0.0-rc.1.  Keep the rest of the Pre-1.0 policy protected.
MUTABLE_ROOT_NARRATIVE = {
    (
        "RELEASE_POLICY.md",
        "pre-1.0 policy",
    ): "The repository originally prepared ",
}


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


def _stable_root_contracts(text: str, path: str) -> Counter[tuple[str, str, str]]:
    contracts = unnumbered.extract_unnumbered_governance_contracts(text, path)
    for (contract_path, section, statement), count in list(contracts.items()):
        prefix = MUTABLE_ROOT_NARRATIVE.get((contract_path, section))
        if prefix is not None and statement.startswith(prefix):
            del contracts[(contract_path, section, statement)]
    return contracts


def _published_normative_stable_root_paths() -> tuple[str, ...]:
    """Derive durable normative Markdown roots from the authenticated stable-root inventory."""
    checkpoint = json.loads(CHECKPOINT_INVENTORY_PATH.read_text(encoding="utf-8"))
    stable_roots = checkpoint["stablePathGroups"]["root"]
    normative: list[str] = []
    for relative in stable_roots:
        if not relative.endswith(".md"):
            continue
        if relative in FORWARD_MOVING_INFORMATIONAL_ROOT_PATHS:
            continue
        published_text = unnumbered.base.git_source_at(
            unnumbered.base.CHECKPOINT_COMMIT,
            relative,
        )
        if _stable_root_contracts(published_text, relative):
            normative.append(relative)
    return tuple(normative)


def _root_governance_contracts_at_checkpoint() -> Counter[tuple[str, str, str]]:
    contracts: Counter[tuple[str, str, str]] = Counter()
    for relative in _published_normative_stable_root_paths():
        contracts.update(
            _stable_root_contracts(
                unnumbered.base.git_source_at(unnumbered.base.CHECKPOINT_COMMIT, relative),
                relative,
            )
        )
    return contracts


def _candidate_root_governance_contracts() -> Counter[tuple[str, str, str]]:
    contracts: Counter[tuple[str, str, str]] = Counter()
    for relative in _published_normative_stable_root_paths():
        contracts.update(
            _stable_root_contracts(
                (REPO_ROOT / relative).read_text(encoding="utf-8"),
                relative,
            )
        )
    return contracts


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
        wrapper_test = (
            REPO_ROOT / "tools/tests/test_validate_all_windows_wrapper.py"
        ).read_text(encoding="utf-8")
        self.assertIn(
            '"text=True, encoding=\'utf-8\', capture_output=True, check=False); "',
            wrapper_test,
        )

    def test_checkpoint_git_sources_use_utf8_under_non_utf8_locale(self):
        build_release = _load_module(
            "pr71_build_release_regression",
            "tools/release/build_release.py",
        )
        validate_release = _load_module(
            "pr71_validate_release_regression",
            "tools/release/validate_release.py",
        )
        validate_all = _load_validate_all_module()
        revision = compatibility.CHECKPOINT_COMMIT
        relative = "RELEASE_POLICY.md"

        with mock.patch("locale.getencoding", return_value="cp1252"):
            checkpoints = (
                compatibility.git_source_at(revision, relative),
                normative.git_source_at(revision, relative),
                finding_codes.git_source_at(revision, relative),
                parameterized_codes.git_source_at(revision, relative),
                agent_skills.git_source_at(revision, relative),
                finding_reachability.git_source_at(revision, relative),
                parameterized_helpers.git_source_at(revision, relative),
                template_contracts.git_source_at(revision, relative),
                writer_safety.git_output("show", f"{revision}:{relative}"),
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
                validate_all._git(
                    REPO_ROOT,
                    "show",
                    f"{revision}:{relative}",
                ).stdout,
            )
            finding_runtime.run_git(
                REPO_ROOT,
                "show",
                f"{revision}:{relative}",
            )
            object_sha = agent_skills.git_object_sha(revision, relative)

        for checkpoint in checkpoints:
            self.assertIn("\u201cProbably compatible\u201d", checkpoint)
        self.assertRegex(object_sha, r"\A[0-9a-f]{40}\Z")

    def test_checkpoint_git_source_preserves_git_errors(self):
        asserting_helpers = (
            compatibility.git_source_at,
            normative.git_source_at,
            finding_codes.git_source_at,
            parameterized_codes.git_source_at,
            agent_skills.git_source_at,
            finding_reachability.git_source_at,
            parameterized_helpers.git_source_at,
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
            writer_safety.git_output("show", "missing-checkpoint-revision:RELEASE_POLICY.md")
        with self.assertRaises(AssertionError):
            agent_skills.git_object_sha(
                "missing-checkpoint-revision",
                "RELEASE_POLICY.md",
            )
        with self.assertRaises(AssertionError):
            finding_runtime.run_git(
                REPO_ROOT,
                "show",
                "missing-checkpoint-revision:RELEASE_POLICY.md",
            )

        build_release = _load_module(
            "pr71_build_release_error_regression",
            "tools/release/build_release.py",
        )
        validate_release = _load_module(
            "pr71_validate_release_error_regression",
            "tools/release/validate_release.py",
        )
        validate_all = _load_validate_all_module()
        with self.assertRaises(RuntimeError):
            build_release.run_git(REPO_ROOT, "show", "missing-checkpoint-revision:path")
        self.assertIsNone(
            validate_release.git_output(
                REPO_ROOT,
                "show",
                "missing-checkpoint-revision:path",
            )
        )
        self.assertNotEqual(
            validate_all._git(
                REPO_ROOT,
                "show",
                "missing-checkpoint-revision:path",
            ).returncode,
            0,
        )

    def test_root_governance_unnumbered_controls_are_preserved(self):
        root_paths = _published_normative_stable_root_paths()
        published = _root_governance_contracts_at_checkpoint()
        candidate = _candidate_root_governance_contracts()

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
            FORWARD_MOVING_INFORMATIONAL_ROOT_PATHS & set(root_paths),
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
        checkpoint = unnumbered.base.git_source_at(
            unnumbered.base.CHECKPOINT_COMMIT,
            "SECURITY.md",
        )
        published = _stable_root_contracts(checkpoint, "SECURITY.md")
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
        candidate = _stable_root_contracts(weakened, "SECURITY.md")
        self.assertTrue(
            unnumbered.unnumbered_contract_findings(published, candidate),
            "weakening the published confidential-reporting control must be detected",
        )

    def test_forward_release_state_narrative_is_not_a_frozen_contract(self):
        checkpoint = unnumbered.base.git_source_at(
            unnumbered.base.CHECKPOINT_COMMIT,
            "RELEASE_POLICY.md",
        )
        raw = unnumbered.extract_unnumbered_governance_contracts(
            checkpoint,
            "RELEASE_POLICY.md",
        )
        stable = _stable_root_contracts(checkpoint, "RELEASE_POLICY.md")

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

    def test_statically_false_assert_makes_successor_unreachable(self):
        literal_source = '''
def validate():
    assert False
    Finding("PUBLIC_CODE", "unreachable")
'''
        self.assertEqual(
            literal.reachable_contracts(literal_source, "sample.py"),
            Counter(),
        )

        parameterized_source = '''
def read_text(path, findings, code):
    Finding(code, "decode failed", path="sample")
def validate(root, findings):
    enabled = False
    assert enabled
    read_text(root / "LICENSE", findings, "LICENSE_ENCODING")
'''
        self.assertEqual(
            parameterized.reachable_parameterized_contracts(
                parameterized_source, "sample.py"
            ),
            set(),
        )

        unknown_assert = '''
def validate(flag):
    assert flag
    Finding("PUBLIC_CODE", "reachable")
'''
        self.assertEqual(
            literal.reachable_contracts(unknown_assert, "sample.py")[
                ("sample.py", "validate", "PUBLIC_CODE")
            ],
            1,
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
