from __future__ import annotations

import hashlib
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from helpers import REPO_ROOT, json_result, run_tool


def git_metadata_snapshot(git_dir: Path) -> dict[str, str]:
    snapshot: dict[str, str] = {}
    for path in sorted(item for item in git_dir.rglob("*") if item.is_file()):
        snapshot[path.relative_to(git_dir).as_posix()] = hashlib.sha256(
            path.read_bytes()
        ).hexdigest()
    return snapshot


class ValidateAllTests(unittest.TestCase):
    def test_list_contains_all_validators(self):
        completed = run_tool("tools/validate-all/run_all.py", "--list")
        self.assertEqual(completed.returncode, 0)
        for validator in (
            "validate-standards",
            "check-links",
            "validate-skills",
            "validate-schemas",
            "validate-templates",
            "validate-tools",
            "validate-release",
        ):
            self.assertIn(validator, completed.stdout)

    def test_single_validator_aggregates(self):
        completed = run_tool("tools/validate-all/run_all.py", "--tool", "validate-standards", "--format", "json")
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
        payload = json_result(completed)
        self.assertEqual(payload["summary"]["validatorsCompleted"], 1)

    def test_release_validator_aggregates(self):
        completed = run_tool("tools/validate-all/run_all.py", "--tool", "validate-release", "--format", "json")
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
        payload = json_result(completed)
        self.assertEqual(payload["summary"]["validatorsCompleted"], 1)
        self.assertEqual(payload["metadata"]["results"][0]["tool"], "validate-release")

    def test_skill_validator_aggregates(self):
        completed = run_tool("tools/validate-all/run_all.py", "--tool", "validate-skills", "--format", "json")
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
        payload = json_result(completed)
        self.assertEqual(payload["summary"]["validatorsCompleted"], 1)
        self.assertEqual(payload["metadata"]["results"][0]["tool"], "validate-skills")

    def _load_validate_all_module(self):
        import importlib.util

        module_path = REPO_ROOT / "tools" / "validate-all" / "run_all.py"
        spec = importlib.util.spec_from_file_location("validate_all_portability", module_path)
        module = importlib.util.module_from_spec(spec)
        assert spec.loader is not None
        previous = sys.dont_write_bytecode
        sys.dont_write_bytecode = True
        try:
            spec.loader.exec_module(module)
        finally:
            sys.dont_write_bytecode = previous
        return module

    def _copy_history_bundle(self, module, root: Path) -> None:
        import shutil

        bundle_target = root / module.COMPATIBILITY_HISTORY_BUNDLE
        bundle_target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(REPO_ROOT / module.COMPATIBILITY_HISTORY_BUNDLE, bundle_target)

    def test_compatibility_history_uses_temporary_git_metadata_for_archives(self):
        module = self._load_validate_all_module()

        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self._copy_history_bundle(module, root)

            self.assertFalse((root / ".git").exists())
            with module.compatibility_history(root):
                self.assertFalse(
                    (root / ".git").exists(),
                    "archive compatibility bootstrap must not create Git metadata in the source root",
                )
                for commit in module.COMPATIBILITY_HISTORY_REFS:
                    completed = subprocess.run(
                        ["git", "-C", str(root), "cat-file", "-e", f"{commit}^{{commit}}"],
                        text=True,
                        capture_output=True,
                        check=False,
                    )
                    self.assertEqual(completed.returncode, 0, completed.stderr)

                fixture = root / "fixture-repository"
                fixture.mkdir()
                commands = (
                    ["git", "init", "--quiet"],
                    ["git", "config", "user.name", "Compatibility Fixture"],
                    ["git", "config", "user.email", "fixture@example.invalid"],
                )
                for command in commands:
                    completed = subprocess.run(
                        command,
                        cwd=fixture,
                        text=True,
                        capture_output=True,
                        check=False,
                    )
                    self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
                (fixture / "fixture.txt").write_text("fixture\n", encoding="utf-8")
                for command in (
                    ["git", "add", "fixture.txt"],
                    ["git", "commit", "--quiet", "-m", "fixture"],
                ):
                    completed = subprocess.run(
                        command,
                        cwd=fixture,
                        text=True,
                        capture_output=True,
                        check=False,
                    )
                    self.assertEqual(
                        completed.returncode,
                        0,
                        "compatibility history must not leak into fixture repositories: "
                        + completed.stdout
                        + completed.stderr,
                    )

            self.assertFalse(
                (root / ".git").exists(),
                "validation must leave an extracted source archive free of Git metadata",
            )

    def test_compatibility_history_does_not_mutate_existing_shallow_style_repository(self):
        module = self._load_validate_all_module()

        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            commands = (
                ["git", "init", "--quiet"],
                ["git", "config", "user.name", "Compatibility Fixture"],
                ["git", "config", "user.email", "fixture@example.invalid"],
            )
            for command in commands:
                completed = subprocess.run(
                    command,
                    cwd=root,
                    text=True,
                    capture_output=True,
                    check=False,
                )
                self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)

            (root / "source.txt").write_text("source\n", encoding="utf-8")
            for command in (
                ["git", "add", "source.txt"],
                ["git", "commit", "--quiet", "-m", "source"],
            ):
                completed = subprocess.run(
                    command,
                    cwd=root,
                    text=True,
                    capture_output=True,
                    check=False,
                )
                self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)

            self._copy_history_bundle(module, root)
            git_dir = root / ".git"
            before = git_metadata_snapshot(git_dir)

            with module.compatibility_history(root):
                for commit in module.COMPATIBILITY_HISTORY_REFS:
                    completed = subprocess.run(
                        ["git", "-C", str(root), "cat-file", "-e", f"{commit}^{{commit}}"],
                        text=True,
                        capture_output=True,
                        check=False,
                    )
                    self.assertEqual(completed.returncode, 0, completed.stderr)

            after = git_metadata_snapshot(git_dir)
            self.assertEqual(
                before,
                after,
                "validation-only compatibility bootstrap must not add refs, objects, or config to an existing history-deficient repository",
            )
            for ref in module.COMPATIBILITY_HISTORY_REFS.values():
                completed = subprocess.run(
                    ["git", "-C", str(root), "show-ref", "--verify", "--quiet", ref],
                    text=True,
                    capture_output=True,
                    check=False,
                )
                self.assertNotEqual(
                    completed.returncode,
                    0,
                    f"temporary compatibility ref leaked into source repository: {ref}",
                )


if __name__ == "__main__":
    unittest.main()
