from __future__ import annotations

import re
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]


def read(relative: str) -> str:
    return (REPO_ROOT / relative).read_text(encoding="utf-8")


def table_areas(text: str, heading: str) -> list[str]:
    match = re.search(
        rf"^## {re.escape(heading)}\s*$\n(?P<body>.*?)(?=^## |\Z)",
        text,
        flags=re.MULTILINE | re.DOTALL,
    )
    if match is None:
        raise AssertionError(f"missing section: {heading}")

    areas: list[str] = []
    for line in match.group("body").splitlines():
        if not line.startswith("|"):
            continue
        first_cell = line.strip().strip("|").split("|", 1)[0].strip()
        if first_cell in {"Area", ""} or set(first_cell) <= {"-", ":"}:
            continue
        areas.append(first_cell)
    return areas


class ProductLifecycleGovernanceRegressionTests(unittest.TestCase):
    def test_nonfunctional_completion_gate_retains_general_scope(self) -> None:
        standard = read(
            "disciplines/testing/standards/NONFUNCTIONAL_TESTING_STANDARD.md"
        )
        self.assertIn(
            "Do not report this area complete until the applicable requirements "
            "are implemented, evidence is recorded, unsupported claims are removed, "
            "and remaining risk is stated plainly.",
            standard,
        )
        self.assertIn(
            "Do not report performance or scalability validated until every "
            "applicable test type has current evidence",
            standard,
        )

    def test_readiness_template_has_one_result_per_standard_area(self) -> None:
        standard = read(
            "disciplines/sre/standards/PRODUCTION_READINESS_STANDARD.md"
        )
        template = read("disciplines/sre/templates/EVIDENCE_RECORD_TEMPLATE.md")
        self.assertEqual(
            table_areas(template, "Production readiness"),
            table_areas(standard, "Readiness areas"),
        )

    def test_scaling_template_has_one_state_per_standard_area(self) -> None:
        standard = read("disciplines/sre/standards/SCALING_STRATEGY_STANDARD.md")
        template = read("disciplines/sre/templates/EVIDENCE_RECORD_TEMPLATE.md")
        self.assertEqual(
            table_areas(template, "Scaling strategy"),
            table_areas(standard, "Required decisions"),
        )

    def test_traceability_template_records_independent_stage_states(self) -> None:
        template = read(
            "disciplines/product-management/templates/EVIDENCE_RECORD_TEMPLATE.md"
        )
        expected_stages = (
            "Idea/source",
            "Requirement",
            "Architecture decision",
            "Implementation",
            "Test",
            "Release/deployment",
            "Production evidence",
        )
        self.assertIn(
            "| Requirement | Lifecycle stage | State | Evidence | Owner |", template
        )
        for stage in expected_stages:
            with self.subTest(stage=stage):
                self.assertRegex(
                    template,
                    rf"(?m)^\| `REQ-___-___` \| {re.escape(stage)} \| "
                    r"`(?:Planned|Implemented|Tested|Reviewed|OperationallyVerified|"
                    r"NotRun|Blocked|NotApplicable)` \|",
                )

    def test_lifecycle_applicability_does_not_add_an_implicit_exception(self) -> None:
        lifecycle = read("governance/PRODUCT_INCEPTION_LIFECYCLE.md")
        applicability = re.search(
            r"^## Applicability\s*$\n(?P<body>.*?)(?=^## |\Z)",
            lifecycle,
            flags=re.MULTILINE | re.DOTALL,
        )
        self.assertIsNotNone(applicability)
        body = applicability.group("body")
        for weakening_phrase in (
            "does not require",
            "not required",
            "need not",
            "may skip",
            "may bypass",
        ):
            with self.subTest(weakening_phrase=weakening_phrase):
                self.assertNotIn(weakening_phrase, body.casefold())


if __name__ == "__main__":
    unittest.main()
