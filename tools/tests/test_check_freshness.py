from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from helpers import REPO_ROOT, json_result, run_tool


class CheckFreshnessTests(unittest.TestCase):
    def write_registry(
        self,
        root: Path,
        *,
        last_reviewed: str | None,
        interval: int = 90,
        scope: str = "sample",
        registry: str = "SOURCE_REVIEWS.json",
    ) -> Path:
        (root / "sample").mkdir(parents=True, exist_ok=True)
        payload = {
            "formatVersion": "1.0.0",
            "defaultReviewIntervalDays": 180,
            "records": [
                {
                    "id": "sample",
                    "scope": scope,
                    "maturity": "baseline",
                    "owner": "Test owner",
                    "reviewIntervalDays": interval,
                    "lastReviewed": last_reviewed,
                    "authoritativeSources": [
                        {
                            "name": "Example authoritative source",
                            "url": "https://example.com/docs",
                        }
                    ],
                }
            ],
        }
        path = root / registry
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        return path

    def test_fresh_review_reports_passed(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self.write_registry(root, last_reviewed="2026-06-15", interval=90)

            completed = run_tool(
                "tools/check-freshness/check_freshness.py",
                "--format",
                "json",
                "--as-of",
                "2026-08-15",
                root=root,
            )
            payload = json_result(completed)

            self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
            self.assertEqual(payload["status"], "passed")
            self.assertEqual(payload["summary"]["freshnessState"], "Passed")
            self.assertEqual(payload["summary"]["passed"], 1)
            self.assertEqual(payload["summary"]["liveSourceVerification"], "NotRun")
            self.assertEqual(payload["findings"], [])

    def test_stale_review_is_warning_without_strict_mode(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self.write_registry(root, last_reviewed="2026-01-01", interval=90)

            completed = run_tool(
                "tools/check-freshness/check_freshness.py",
                "--format",
                "json",
                "--as-of",
                "2026-08-15",
                root=root,
            )
            payload = json_result(completed)

            self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
            self.assertEqual(payload["status"], "passed")
            self.assertEqual(payload["summary"]["freshnessState"], "Warning")
            self.assertEqual(payload["summary"]["warnings"], 1)
            self.assertTrue(
                any(
                    item["code"] == "SOURCE_REVIEW_STALE"
                    and item["severity"] == "warning"
                    for item in payload["findings"]
                ),
                payload["findings"],
            )

    def test_missing_review_date_reports_not_run(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self.write_registry(root, last_reviewed=None)

            completed = run_tool(
                "tools/check-freshness/check_freshness.py",
                "--format",
                "json",
                "--as-of",
                "2026-08-15",
                root=root,
            )
            payload = json_result(completed)

            self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
            self.assertEqual(payload["status"], "passed")
            self.assertEqual(payload["summary"]["freshnessState"], "NotRun")
            self.assertEqual(payload["summary"]["notRun"], 1)
            self.assertEqual(payload["summary"]["liveSourceVerification"], "NotRun")
            self.assertTrue(
                any(
                    item["code"] == "SOURCE_REVIEW_NOT_RUN"
                    and item["severity"] == "warning"
                    for item in payload["findings"]
                ),
                payload["findings"],
            )

    def test_strict_mode_blocks_stale_review(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self.write_registry(root, last_reviewed="2026-01-01", interval=90)

            completed = run_tool(
                "tools/check-freshness/check_freshness.py",
                "--format",
                "json",
                "--as-of",
                "2026-08-15",
                "--strict",
                root=root,
            )
            payload = json_result(completed)

            self.assertEqual(completed.returncode, 1, completed.stdout + completed.stderr)
            self.assertEqual(payload["status"], "failed")
            self.assertEqual(payload["summary"]["freshnessState"], "Warning")
            self.assertTrue(
                any(
                    item["code"] == "SOURCE_REVIEW_STALE"
                    and item["severity"] == "error"
                    for item in payload["findings"]
                ),
                payload["findings"],
            )

    def test_strict_mode_blocks_not_run_review(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self.write_registry(root, last_reviewed=None)

            completed = run_tool(
                "tools/check-freshness/check_freshness.py",
                "--format",
                "json",
                "--as-of",
                "2026-08-15",
                "--strict",
                root=root,
            )
            payload = json_result(completed)

            self.assertEqual(completed.returncode, 1, completed.stdout + completed.stderr)
            self.assertEqual(payload["status"], "failed")
            self.assertEqual(payload["summary"]["freshnessState"], "NotRun")

    def test_future_review_date_is_invalid(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self.write_registry(root, last_reviewed="2026-08-16")

            completed = run_tool(
                "tools/check-freshness/check_freshness.py",
                "--format",
                "json",
                "--as-of",
                "2026-08-15",
                root=root,
            )
            payload = json_result(completed)

            self.assertEqual(completed.returncode, 1, completed.stdout + completed.stderr)
            self.assertEqual(payload["status"], "failed")
            self.assertEqual(payload["summary"]["freshnessState"], "Invalid")
            self.assertIn(
                "SOURCE_REVIEW_DATE_FUTURE",
                {item["code"] for item in payload["findings"]},
            )

    def test_scope_escape_is_rejected_and_state_is_invalid(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "repo"
            root.mkdir()
            self.write_registry(root, last_reviewed="2026-08-01", scope="../outside")

            completed = run_tool(
                "tools/check-freshness/check_freshness.py",
                "--format",
                "json",
                "--as-of",
                "2026-08-15",
                root=root,
            )
            payload = json_result(completed)

            self.assertEqual(completed.returncode, 1, completed.stdout + completed.stderr)
            self.assertEqual(payload["summary"]["freshnessState"], "Invalid")
            self.assertIn(
                "SOURCE_REVIEW_SCOPE_ESCAPES_ROOT",
                {item["code"] for item in payload["findings"]},
            )

    def test_registry_path_must_be_repository_relative(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "repo"
            root.mkdir()
            outside = Path(temp) / "outside.json"
            outside.write_text("{}\n", encoding="utf-8")

            completed = run_tool(
                "tools/check-freshness/check_freshness.py",
                "--format",
                "json",
                "--registry",
                str(outside),
                root=root,
            )
            payload = json_result(completed)

            self.assertEqual(completed.returncode, 2, completed.stdout + completed.stderr)
            self.assertEqual(payload["status"], "error")
            self.assertEqual(payload["findings"][0]["code"], "INPUT_ERROR")
            self.assertIn("repository-relative", payload["findings"][0]["message"])

    def test_custom_registry_path_is_reported_in_findings(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self.write_registry(
                root,
                last_reviewed=None,
                registry="maintenance/source-reviews.json",
            )

            completed = run_tool(
                "tools/check-freshness/check_freshness.py",
                "--format",
                "json",
                "--registry",
                "maintenance/source-reviews.json",
                "--as-of",
                "2026-08-15",
                root=root,
            )
            payload = json_result(completed)

            self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
            self.assertEqual(payload["metadata"]["registry"], "maintenance/source-reviews.json")
            self.assertTrue(
                all(
                    item.get("path") == "maintenance/source-reviews.json"
                    for item in payload["findings"]
                ),
                payload["findings"],
            )

    def test_repository_registry_is_valid_and_truthful_about_live_checks(self):
        completed = run_tool(
            "tools/check-freshness/check_freshness.py",
            "--format",
            "json",
            "--as-of",
            "2026-08-15",
        )
        payload = json_result(completed)

        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
        self.assertEqual(payload["status"], "passed")
        self.assertEqual(payload["summary"]["freshnessState"], "NotRun")
        self.assertEqual(payload["summary"]["liveSourceVerification"], "NotRun")
        self.assertGreater(payload["summary"]["records"], 0)

    def test_scheduled_workflow_uses_offline_checker_and_pinned_actions(self):
        workflow = (REPO_ROOT / ".github" / "workflows" / "source-freshness.yml").read_text(encoding="utf-8")

        self.assertIn("schedule:", workflow)
        self.assertIn("workflow_dispatch:", workflow)
        self.assertIn("tools/check-freshness/check_freshness.py", workflow)
        self.assertIn("runs-on: ubuntu-24.04", workflow)
        self.assertIn("actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1", workflow)
        self.assertIn("actions/setup-python@5fda3b95a4ea91299a34e894583c3862153e4b97", workflow)
        self.assertNotIn("curl ", workflow)
        self.assertNotIn("wget ", workflow)


if __name__ == "__main__":
    unittest.main()
