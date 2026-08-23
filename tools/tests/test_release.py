from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from helpers import json_result, run_tool

REPO_ROOT = Path(__file__).resolve().parents[2]


def make_release_root(root: Path, version: str = "0.9.0") -> None:
    (root / "releases" / "migrations").mkdir(parents=True)
    (root / ".github" / "workflows").mkdir(parents=True)
    (root / "VERSION").write_text(version + "\n", encoding="utf-8")
    (root / "CHANGELOG.md").write_text(
        f"# Changelog\n\n## [Unreleased]\n\n## [{version}] - 2030-01-01\n",
        encoding="utf-8",
    )
    (root / "RELEASE_POLICY.md").write_text(
        "# Release Policy\n\n"
        "## Repository semantic versioning\n"
        "## Pre-1.0 policy\n"
        "## Deprecation windows\n90 calendar days\n180 calendar days\n"
        "## Release process\n"
        "## Git tags\nvMAJOR.MINOR.PATCH\n"
        "## GitHub releases\n"
        "## Release artifacts and checksums\n"
        "## 1.0.0 compatibility gate\n",
        encoding="utf-8",
    )
    (root / "MATURITY_POLICY.md").write_text(
        "# Maturity\n\n"
        "## Maturity states\n"
        "## Promotion requirements\n"
        "## Baseline to stable review\n"
        "## Demotion and deprecation\n"
        "## Review record\n",
        encoding="utf-8",
    )
    (root / "releases" / f"{version}.md").write_text(
        f"# Public-Access-Agents {version}\n\n"
        "## Breaking changes\nNone.\n"
        "## Normative changes\nNone.\n"
        "## Editorial changes\nNone.\n"
        "## Deprecations\nNone.\n"
        "## Migration notes\nSee migration file.\n"
        "## Security\nNone.\n"
        "## Known limitations\nNone.\n",
        encoding="utf-8",
    )
    (root / "releases" / "migrations" / f"{version}.md").write_text(
        "# Migration\n\n## Required actions\nNone.\n",
        encoding="utf-8",
    )
    (root / ".github" / "workflows" / "release.yml").write_text(
        "tags:\n  - 'v*'\n"
        "run: python tools/release/build_release.py && gh release create tag "
        "dist/SHA256SUMS.txt dist/RELEASE_NOTES.md\n",
        encoding="utf-8",
    )


def init_fixture_repository(root: Path) -> None:
    subprocess.run(["git", "init"], cwd=root, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=root, check=True)
    subprocess.run(["git", "config", "user.email", "test@example.invalid"], cwd=root, check=True)
    subprocess.run(["git", "add", "."], cwd=root, check=True)
    subprocess.run(["git", "commit", "-m", "fixture"], cwd=root, check=True, capture_output=True)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class ReleaseToolTests(unittest.TestCase):
    def test_valid_release_program_passes(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            make_release_root(root)
            completed = run_tool("tools/release/validate_release.py", "--format", "json", root=root)
            self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
            self.assertEqual(json_result(completed)["status"], "passed")

    def test_invalid_semver_fails(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            make_release_root(root, "version-nine")
            completed = run_tool("tools/release/validate_release.py", "--format", "json", root=root)
            self.assertEqual(completed.returncode, 1)
            codes = {item["code"] for item in json_result(completed)["findings"]}
            self.assertIn("RELEASE_VERSION_INVALID", codes)

    def test_release_state_rejects_invalid_next_intended_semver(self):
        invalid_versions = ("01.2.3", "1.2.3-01", "1٢.2.3", "1.2.3-1٢")
        for next_version in invalid_versions:
            with self.subTest(next_version=next_version), tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                make_release_root(root)
                (root / "releases" / "release-state.json").write_text(
                    json.dumps({
                        "preparedUnpublishedVersions": ["0.9.0"],
                        "nextIntendedVersion": next_version,
                    }) + "\n",
                    encoding="utf-8",
                )
                completed = run_tool("tools/release/validate_release.py", "--format", "json", root=root)
                self.assertEqual(completed.returncode, 1, completed.stdout + completed.stderr)
                findings = json_result(completed)["findings"]
                self.assertTrue(
                    any(
                        item["code"] == "RELEASE_STATE_INVALID"
                        and "nextIntendedVersion" in item["message"]
                        for item in findings
                    ),
                    findings,
                )

    def test_release_state_rejects_blocked_next_intended_version(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            make_release_root(root, "1.0.0")
            (root / "releases" / "release-state.json").write_text(
                json.dumps({
                    "preparedUnpublishedVersions": ["1.0.0"],
                    "nextIntendedVersion": "1.0.0",
                }) + "\n",
                encoding="utf-8",
            )
            completed = run_tool("tools/release/validate_release.py", "--format", "json", root=root)
            self.assertEqual(completed.returncode, 1, completed.stdout + completed.stderr)
            findings = json_result(completed)["findings"]
            self.assertTrue(
                any(
                    item["code"] == "RELEASE_STATE_INVALID"
                    and "must not also appear" in item["message"]
                    for item in findings
                ),
                findings,
            )

    def test_publication_attempt_must_match_next_intended_version(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            make_release_root(root, "0.11.0")
            (root / "releases" / "release-state.json").write_text(
                json.dumps({
                    "preparedUnpublishedVersions": ["0.9.0"],
                    "nextIntendedVersion": "0.10.0",
                }) + "\n",
                encoding="utf-8",
            )
            completed = run_tool(
                "tools/release/validate_release.py",
                "--format",
                "json",
                "--tag",
                "v0.11.0",
                root=root,
            )
            self.assertEqual(completed.returncode, 1, completed.stdout + completed.stderr)
            self.assertIn(
                "RELEASE_PUBLICATION_VERSION_MISMATCH",
                {item["code"] for item in json_result(completed)["findings"]},
            )

    def test_builder_requires_next_intended_version(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            make_release_root(root, "0.11.0")
            (root / "releases" / "release-state.json").write_text(
                json.dumps({
                    "preparedUnpublishedVersions": ["0.9.0"],
                    "nextIntendedVersion": "0.10.0",
                }) + "\n",
                encoding="utf-8",
            )
            completed = subprocess.run(
                [
                    sys.executable,
                    str(REPO_ROOT / "tools/release/build_release.py"),
                    "--root",
                    str(root),
                    "--tag",
                    "v0.11.0",
                    "--output-dir",
                    "dist",
                ],
                cwd=REPO_ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(completed.returncode, 2, completed.stdout + completed.stderr)
            self.assertIn("does not match nextIntendedVersion 0.10.0", completed.stderr)
            self.assertFalse((root / "dist").exists())

    def test_valid_semver_prerelease_release_state_passes(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            make_release_root(root)
            (root / "releases" / "release-state.json").write_text(
                json.dumps({
                    "preparedUnpublishedVersions": ["0.9.0"],
                    "nextIntendedVersion": "1.0.0-rc.1+build.001",
                }) + "\n",
                encoding="utf-8",
            )
            completed = run_tool("tools/release/validate_release.py", "--format", "json", root=root)
            self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)

    def test_builder_rejects_invalid_release_state(self):
        invalid_states = (
            {"preparedUnpublishedVersions": [], "nextIntendedVersion": "1.2.3-01"},
            {"preparedUnpublishedVersions": [], "nextIntendedVersion": "1٢.2.3"},
            {"preparedUnpublishedVersions": []},
            {"preparedUnpublishedVersions": ["1.0.0"], "nextIntendedVersion": "1.0.0"},
        )
        for state in invalid_states:
            with self.subTest(state=state), tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                make_release_root(root, "1.0.0")
                (root / "releases" / "release-state.json").write_text(
                    json.dumps(state) + "\n",
                    encoding="utf-8",
                )
                completed = subprocess.run(
                    [
                        sys.executable,
                        str(REPO_ROOT / "tools/release/build_release.py"),
                        "--root",
                        str(root),
                        "--tag",
                        "v1.0.0",
                        "--output-dir",
                        "dist",
                    ],
                    cwd=REPO_ROOT,
                    text=True,
                    capture_output=True,
                    check=False,
                )
                self.assertEqual(completed.returncode, 2, completed.stdout + completed.stderr)
                self.assertIn("Release-state metadata is invalid", completed.stderr)
                self.assertFalse((root / "dist").exists())

    def test_missing_release_notes_fails(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            make_release_root(root)
            (root / "releases" / "0.9.0.md").unlink()
            completed = run_tool("tools/release/validate_release.py", "--format", "json", root=root)
            self.assertEqual(completed.returncode, 1)
            codes = {item["code"] for item in json_result(completed)["findings"]}
            self.assertIn("RELEASE_NOTES_MISSING", codes)

    def test_tag_mismatch_fails(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            make_release_root(root)
            completed = run_tool(
                "tools/release/validate_release.py",
                "--format",
                "json",
                "--tag",
                "v1.0.0",
                root=root,
            )
            self.assertEqual(completed.returncode, 1)
            codes = {item["code"] for item in json_result(completed)["findings"]}
            self.assertIn("RELEASE_TAG_MISMATCH", codes)

    def test_incomplete_release_policy_fails(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            make_release_root(root)
            (root / "RELEASE_POLICY.md").write_text("# Release Policy\n", encoding="utf-8")
            completed = run_tool("tools/release/validate_release.py", "--format", "json", root=root)
            self.assertEqual(completed.returncode, 1)
            codes = {item["code"] for item in json_result(completed)["findings"]}
            self.assertIn("RELEASE_POLICY_SECTION_MISSING", codes)

    def test_publish_workflow_sets_repository_context_for_gh(self):
        workflow = (REPO_ROOT / ".github" / "workflows" / "release.yml").read_text(encoding="utf-8")
        self.assertIn("gh release create", workflow)
        self.assertTrue(
            "GH_REPO: ${{ github.repository }}" in workflow or "--repo" in workflow,
            "Release publication must provide explicit repository context to gh when the publish job has no checkout.",
        )

    def test_dirty_tracked_tree_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            make_release_root(root)
            (root / "README.md").write_text("# Example\n", encoding="utf-8")
            init_fixture_repository(root)
            (root / "README.md").write_text("# Modified after commit\n", encoding="utf-8")
            completed = subprocess.run(
                [
                    sys.executable,
                    str(REPO_ROOT / "tools/release/build_release.py"),
                    "--root",
                    str(root),
                    "--tag",
                    "v0.9.0",
                    "--output-dir",
                    "dist",
                ],
                cwd=REPO_ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(completed.returncode, 2)
            self.assertIn("Tracked working-tree changes are present", completed.stderr)

    def test_release_archives_are_reproducible(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            make_release_root(root)
            (root / "README.md").write_text("# Example\n", encoding="utf-8")
            init_fixture_repository(root)

            outputs = []
            for name in ("dist-one", "dist-two"):
                completed = subprocess.run(
                    [
                        sys.executable,
                        str(REPO_ROOT / "tools/release/build_release.py"),
                        "--root",
                        str(root),
                        "--tag",
                        "v0.9.0",
                        "--output-dir",
                        name,
                    ],
                    cwd=REPO_ROOT,
                    text=True,
                    capture_output=True,
                    check=False,
                )
                self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
                outputs.append(root / name)

            for artifact in (
                "Public-Access-Agents-0.9.0.zip",
                "Public-Access-Agents-0.9.0.tar.gz",
                "SHA256SUMS.txt",
            ):
                self.assertEqual(sha256(outputs[0] / artifact), sha256(outputs[1] / artifact))

            manifest = json.loads((outputs[0] / "release-manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(manifest["sourceCommit"], subprocess.run(
                ["git", "rev-parse", "HEAD"], cwd=root, text=True, encoding="utf-8", capture_output=True, check=True
            ).stdout.strip())
            self.assertEqual(manifest["builderVersion"], "1.0.0")


if __name__ == "__main__":
    unittest.main()
