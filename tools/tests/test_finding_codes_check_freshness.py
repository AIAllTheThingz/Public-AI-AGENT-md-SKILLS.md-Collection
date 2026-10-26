from __future__ import annotations

import copy
import json
import tempfile
import unittest
from pathlib import Path

from helpers import json_result, run_tool

VALID = {
    "formatVersion": "1.0.0",
    "defaultReviewIntervalDays": 180,
    "records": [
        {
            "id": "sample",
            "scope": "sample",
            "maturity": "baseline",
            "reviewIntervalDays": 90,
            "lastReviewed": "2026-06-15",
            "reviewEvidence": "source-reviews/2026-06-15.md",
            "authoritativeSources": [{"name": "Example source", "url": "https://example.invalid/docs"}],
        }
    ],
}


def record(payload):
    return payload["records"][0]


CASES = {
    "SOURCE_REVIEW_AUTHORITATIVE_SOURCE_INVALID": lambda p: record(p).update(
        authoritativeSources=[{"name": "Example source", "url": "http://example.invalid/docs"}]
    ),
    "SOURCE_REVIEW_AUTHORITATIVE_SOURCE_MISSING": lambda p: record(p).update(authoritativeSources=[]),
    "SOURCE_REVIEW_DATE_INVALID": lambda p: record(p).update(lastReviewed="2026-13-40"),
    "SOURCE_REVIEW_EVIDENCE_INVALID": lambda p: record(p).update(reviewEvidence=""),
    "SOURCE_REVIEW_ID_DUPLICATE": lambda p: p["records"].append(copy.deepcopy(record(p))),
    "SOURCE_REVIEW_ID_INVALID": lambda p: record(p).update(id=""),
    "SOURCE_REVIEW_INTERVAL_INVALID": lambda p: record(p).update(reviewIntervalDays=0),
    "SOURCE_REVIEW_MATURITY_INVALID": lambda p: record(p).update(maturity="unknown"),
    "SOURCE_REVIEW_RECORDS_MISSING": lambda p: p.update(records=[]),
    "SOURCE_REVIEW_RECORD_INVALID": lambda p: p.update(records=["not-an-object"]),
    "SOURCE_REVIEW_SCOPE_INVALID": lambda p: record(p).update(scope=""),
    "SOURCE_REVIEW_SCOPE_MISSING": lambda p: record(p).update(scope="missing"),
}


class CheckFreshnessFindingCodeTests(unittest.TestCase):
    def run_registry(self, payload):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "sample").mkdir()
            (root / "source-reviews").mkdir()
            (root / "source-reviews" / "2026-06-15.md").write_text("# Review evidence\n", encoding="utf-8")
            (root / "SOURCE_REVIEWS.json").write_text(json.dumps(payload), encoding="utf-8")
            completed = run_tool(
                "tools/check-freshness/check_freshness.py",
                "--format",
                "json",
                "--as-of",
                "2026-08-15",
                root=root,
            )
        return completed, json_result(completed)

    def test_valid_baseline_has_no_findings(self):
        completed, payload = self.run_registry(VALID)
        self.assertEqual(payload["findings"], [], completed.stdout + completed.stderr)

    def test_each_finding_code_is_emitted(self):
        for code, mutate in CASES.items():
            with self.subTest(code=code):
                payload = copy.deepcopy(VALID)
                mutate(payload)
                completed, result = self.run_registry(payload)
                codes = [item["code"] for item in result["findings"]]
                self.assertIn(code, codes, completed.stdout + completed.stderr)


if __name__ == "__main__":
    unittest.main()
