from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from helpers import REPO_ROOT, json_result, run_tool


class ReleasePublicationBoundaryTests(unittest.TestCase):
    def test_release_state_records_unpublished_0_9_0_and_forward_0_10_0(self):
        state = json.loads((REPO_ROOT / "releases" / "release-state.json").read_text(encoding="utf-8"))

        self.assertIn("0.9.0", state["preparedUnpublishedVersions"])
        self.assertIn("0.10.0", state["publishedVersions"])
        self.assertEqual(state["nextIntendedVersion"], "1.0.0-rc.1")
        self.assertNotIn(state["nextIntendedVersion"], state["preparedUnpublishedVersions"])
        self.assertEqual(state["canonicalRepository"], "AIAllTheThingz/Public-AI-Governance")
        self.assertEqual(state["artifactPrefix"], "Public-Access-Agents")

    def test_validator_rejects_forbidden_v0_9_0_tag(self):
        completed = run_tool(
            "tools/release/validate_release.py",
            "--format",
            "json",
            "--tag",
            "v0.9.0",
        )
        payload = json_result(completed)

        self.assertEqual(completed.returncode, 1, completed.stdout + completed.stderr)
        self.assertTrue(
            any(finding["code"] == "RELEASE_PUBLICATION_BLOCKED" for finding in payload["findings"]),
            payload["findings"],
        )
        self.assertTrue(payload["summary"]["publicationBlocked"])

    def test_builder_rejects_publication_artifacts_for_unpublished_0_9_0(self):
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / "dist"
            completed = subprocess.run(
                [
                    sys.executable,
                    str(REPO_ROOT / "tools" / "release" / "build_release.py"),
                    "--root",
                    str(REPO_ROOT),
                    "--tag",
                    "v0.9.0",
                    "--output-dir",
                    str(output),
                    "--force",
                ],
                cwd=REPO_ROOT,
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertEqual(completed.returncode, 2, completed.stdout + completed.stderr)
            self.assertIn("explicitly recorded as prepared but unpublished", completed.stderr)
            self.assertFalse(output.exists())

    def test_release_workflow_validates_before_build_and_publication(self):
        workflow = (REPO_ROOT / ".github" / "workflows" / "release.yml").read_text(encoding="utf-8")

        validate_position = workflow.index("- name: Validate release tag")
        build_position = workflow.index("- name: Build release artifacts")
        publish_position = workflow.index("- name: Publish GitHub Release")

        self.assertLess(validate_position, build_position)
        self.assertLess(build_position, publish_position)


if __name__ == "__main__":
    unittest.main()
