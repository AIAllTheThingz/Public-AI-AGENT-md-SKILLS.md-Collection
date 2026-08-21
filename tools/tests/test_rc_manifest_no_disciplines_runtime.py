from __future__ import annotations

import unittest

from helpers import REPO_ROOT, json_result, run_tool


class ReleaseCandidateManifestNoDisciplinesRuntimeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.language = next(
            path.name
            for path in sorted((REPO_ROOT / "languages").iterdir())
            if path.is_dir()
        )

    def _generate(self, *profile_args: str) -> dict:
        completed = run_tool(
            "tools/generate-manifest/generate_manifest.py",
            "--format",
            "json",
            "--name",
            "rc-no-disciplines-contract",
            "--language",
            self.language,
            "--include-profile-required",
            "--dry-run",
            *profile_args,
        )
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
        return json_result(completed)

    def _assert_profile_expansion_suppresses_warning(self, payload: dict) -> list[str]:
        manifest = payload["metadata"]["manifest"]
        disciplines = manifest["disciplines"]
        self.assertTrue(
            disciplines,
            "profile-required expansion must supply disciplines when no --discipline is given",
        )
        codes = {finding["code"] for finding in payload.get("findings", [])}
        self.assertNotIn(
            "MANIFEST_NO_DISCIPLINES",
            codes,
            "warning must follow the generated manifest, not only explicit CLI discipline arguments",
        )
        return disciplines

    def test_primary_profile_required_disciplines_suppress_warning(self):
        payload = self._generate("--profile", "CLI_TOOL")
        disciplines = self._assert_profile_expansion_suppresses_warning(payload)
        self.assertIn("application-security", disciplines)
        self.assertIn("testing", disciplines)

    def test_secondary_profile_required_disciplines_suppress_warning(self):
        payload = self._generate(
            "--profile",
            "CLI_TOOL",
            "--secondary-profile",
            "AI_AGENT_APPLICATION",
        )
        disciplines = self._assert_profile_expansion_suppresses_warning(payload)
        self.assertIn(
            "api-engineering",
            disciplines,
            "secondary-profile-only required discipline must be expanded into the generated manifest",
        )


if __name__ == "__main__":
    unittest.main()
