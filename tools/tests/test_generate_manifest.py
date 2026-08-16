from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from helpers import REPO_ROOT, json_result, run_tool


class GenerateManifestTests(unittest.TestCase):
    def test_dry_run_manifest_validates(self):
        completed = run_tool(
            "tools/generate-manifest/generate_manifest.py",
            "--name", "example-service",
            "--profile", "WEB_API",
            "--language", "python",
            "--virtualization", "kvm-libvirt",
            "--operating-system", "ubuntu",
            "--networking", "cisco-networking",
            "--include-profile-required",
            "--dry-run",
            "--format", "json",
        )
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
        payload = json_result(completed)
        self.assertEqual(payload["metadata"]["manifest"]["profile"], "WEB_API")
        self.assertIn("testing", payload["metadata"]["manifest"]["disciplines"])
        self.assertEqual(payload["metadata"]["manifest"]["schemaVersion"], "1.1.0")
        self.assertEqual(payload["metadata"]["manifest"]["virtualization"], ["kvm-libvirt"])
        self.assertEqual(payload["metadata"]["manifest"]["operatingSystems"], ["ubuntu"])
        self.assertEqual(payload["metadata"]["manifest"]["networking"], ["cisco-networking"])

    def test_secondary_profiles_expand_profile_disciplines(self):
        completed = run_tool(
            "tools/generate-manifest/generate_manifest.py",
            "--name", "mixed-automation-web",
            "--profile", "INTERNAL_AUTOMATION",
            "--secondary-profile", "WEB_APPLICATION",
            "--language", "csharp",
            "--include-profile-required",
            "--dry-run",
            "--format", "json",
        )
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
        manifest = json_result(completed)["metadata"]["manifest"]
        self.assertEqual(manifest["secondaryProfiles"], ["WEB_APPLICATION"])
        self.assertIn("testing", manifest["disciplines"])
        self.assertIn("accessibility", manifest["disciplines"])
        self.assertEqual(len(manifest["disciplines"]), len(set(manifest["disciplines"])))

    def test_legacy_selections_preserve_schema_version(self):
        completed = run_tool(
            "tools/generate-manifest/generate_manifest.py",
            "--name", "legacy-service",
            "--profile", "WEB_API",
            "--language", "python",
            "--dry-run",
            "--format", "json",
        )
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
        payload = json_result(completed)
        self.assertEqual(payload["metadata"]["manifest"]["schemaVersion"], "1.0.0")
        self.assertNotIn("virtualization", payload["metadata"]["manifest"])
        self.assertNotIn("operatingSystems", payload["metadata"]["manifest"])
        self.assertNotIn("networking", payload["metadata"]["manifest"])

    def test_rejects_unknown_infrastructure_package(self):
        completed = run_tool(
            "tools/generate-manifest/generate_manifest.py",
            "--name", "invalid-service",
            "--profile", "WEB_API",
            "--language", "python",
            "--operating-system", "not-a-package",
            "--dry-run",
            "--format", "json",
        )
        self.assertEqual(completed.returncode, 2)

    def test_refuses_overwrite_without_force(self):
        with tempfile.TemporaryDirectory(dir=REPO_ROOT) as temp:
            output = Path(temp) / "manifest.json"
            output.write_text("{}\n", encoding="utf-8")
            completed = run_tool(
                "tools/generate-manifest/generate_manifest.py",
                "--name", "example-service",
                "--profile", "WEB_API",
                "--language", "python",
                "--manifest-output", str(output),
                "--format", "json",
            )
            self.assertEqual(completed.returncode, 2)


if __name__ == "__main__":
    unittest.main()
