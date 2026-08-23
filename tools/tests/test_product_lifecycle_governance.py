from __future__ import annotations

import re
import unittest
from pathlib import Path

from helpers import json_result, run_tool


REPO_ROOT = Path(__file__).resolve().parents[2]

CANONICAL_PROFILE_PACKAGES = (
    ("AI_AGENT_APPLICATION.md", "ai-agent-application"),
    ("CLI_TOOL.md", "cli-tool"),
    ("DATA_PIPELINE.md", "data-pipeline"),
    ("DESKTOP_APPLICATION.md", "desktop-application"),
    ("INTERNAL_AUTOMATION.md", "internal-automation"),
    ("MOBILE_APPLICATION.md", "mobile-application"),
    ("MULTI_TENANT_SAAS.md", "multi-tenant-saas"),
    ("PUBLIC_LIBRARY.md", "public-library"),
    ("SECURITY_TOOL.md", "security-tool"),
    ("SERVERLESS_FUNCTION.md", "serverless-function"),
    ("WEB_API.md", "web-api"),
    ("WEB_APPLICATION.md", "web-application"),
    ("WORKER_SERVICE.md", "worker-service"),
)

CONDITIONAL_PRODUCT_OVERLAYS = (
    "disciplines/product-management",
    "disciplines/user-experience",
)

GENERAL_NONFUNCTIONAL_BEHAVIOR = (
    "Define performance, load, resilience, recovery, security, accessibility, "
    "and compatibility tests when risk requires them.",
    "Define scope, ownership, inputs, outputs, assumptions, dependencies, and "
    "supported operating conditions.",
    "Use explicit, reviewable configuration and documented defaults rather than "
    "hidden environment assumptions.",
    "Apply controls proportionate to change risk, data sensitivity, trust "
    "boundaries, reversibility, and operational impact.",
    "Define positive behavior, negative behavior, boundary conditions, partial "
    "failure, recovery, and safe stopping conditions.",
    "Keep implementation, configuration, examples, and evidence free of "
    "credentials, internal production identifiers, and sensitive data.",
    "Preserve existing contracts unless an authorized change includes "
    "compatibility, migration, and communication work.",
    "Record exceptions through the repository exception process instead of "
    "weakening the standard silently.",
)

GENERAL_NONFUNCTIONAL_EVIDENCE = (
    "design, configuration, contract, diagram, or decision records",
    "implementation or review evidence tied to the requirement",
    "positive, negative, boundary, and failure-path tests",
    "operational, security, privacy, compatibility, or recovery evidence",
    "commands run, environments used, results, and checks not run",
    "known limitations, assumptions, unresolved risks, owners, and follow-up work",
)

GENERAL_NONFUNCTIONAL_REVIEW = (
    "Is this standard applicable to the change, and is the chosen scope documented?",
    "Are ownership and trust boundaries explicit?",
    "Are unsafe defaults, ambiguity, and hidden coupling avoided?",
    "Are failure, retry, rollback, recovery, and partial-success behaviors defined "
    "where relevant?",
    "Does the evidence prove the claim rather than merely describe intent?",
    "Are exceptions approved, time-bounded, and visible?",
)


def read(relative: str) -> str:
    return (REPO_ROOT / relative).read_text(encoding="utf-8")


def h2_section(text: str, heading: str) -> str:
    match = re.search(
        rf"^## {re.escape(heading)}\s*$\n(?P<body>.*?)(?=^## |\Z)",
        text,
        flags=re.MULTILINE | re.DOTALL,
    )
    if match is None:
        raise AssertionError(f"missing section: {heading}")
    return match.group("body")


def h3_section(text: str, heading: str) -> str:
    match = re.search(
        rf"^### {re.escape(heading)}\s*$\n(?P<body>.*?)(?=^#{{1,3}} |\Z)",
        text,
        flags=re.MULTILINE | re.DOTALL,
    )
    if match is None:
        raise AssertionError(f"missing subsection: {heading}")
    return match.group("body")


def bullet_items(text: str, heading: str) -> list[str]:
    items: list[str] = []
    current: list[str] = []
    for line in h2_section(text, heading).splitlines():
        if line.startswith("- "):
            if current:
                items.append(" ".join(current))
            current = [line[2:].strip()]
        elif current and line.strip():
            current.append(line.strip())
    if current:
        items.append(" ".join(current))
    return [re.sub(r"\s+", " ", item).strip() for item in items]


def table_areas(text: str, heading: str) -> list[str]:
    areas: list[str] = []
    for line in h2_section(text, heading).splitlines():
        if not line.startswith("|"):
            continue
        first_cell = line.strip().strip("|").split("|", 1)[0].strip()
        if first_cell in {"Area", ""} or set(first_cell) <= {"-", ":"}:
            continue
        areas.append(first_cell)
    return areas


class ProductLifecycleGovernanceRegressionTests(unittest.TestCase):
    def test_product_inception_lifecycle_is_explicitly_selected(self) -> None:
        optional_adoption_surfaces = (
            ("README.md", "governance/PRODUCT_INCEPTION_LIFECYCLE.md"),
            ("profiles/README.md", "../governance/PRODUCT_INCEPTION_LIFECYCLE.md"),
        )
        for relative, target in optional_adoption_surfaces:
            with self.subTest(surface=relative):
                matching_lines = [
                    line
                    for line in read(relative).splitlines()
                    if target in line
                ]
                self.assertTrue(matching_lines)
                for line in matching_lines:
                    integration = line.casefold()
                    self.assertIn("optional", integration)
                    self.assertIn("select", integration)

        governance_integration = next(
            line
            for line in read("governance/README.md").splitlines()
            if "PRODUCT_INCEPTION_LIFECYCLE.md" in line
        ).casefold()
        self.assertIn("explicitly select", governance_integration)
        self.assertIn("not activated", governance_integration)

        for relative in (
            "examples/full-stack/AGENTS.md",
            "examples/web-api/AGENTS.md",
        ):
            with self.subTest(selected_example=relative):
                selected = h2_section(read(relative), "Selected standards")
                self.assertIn(
                    "governance/PRODUCT_INCEPTION_LIFECYCLE.md",
                    selected,
                )

    def test_normal_implementation_requires_explicit_build_gate_pass(self) -> None:
        lifecycle = read("governance/PRODUCT_INCEPTION_LIFECYCLE.md")
        build_gate = h3_section(lifecycle, "Build Gate")
        self.assertIn(
            "Normal production implementation must not start unless the Build Gate "
            "decision is explicitly `Pass`.",
            build_gate,
        )

        prototype_exception = h2_section(
            lifecycle,
            "Prototype and experiment exception",
        )
        self.assertIn(
            "An explicitly authorized prototype or experiment may begin before all "
            "normal inception evidence exists",
            prototype_exception,
        )
        self.assertIn(
            "Prototype work must not silently become normal production implementation",
            prototype_exception,
        )

    def test_product_and_ux_overlays_are_conditional_in_every_profile_surface(
        self,
    ) -> None:
        self.assertEqual(len(CANONICAL_PROFILE_PACKAGES), 13)
        for canonical_name, package_slug in CANONICAL_PROFILE_PACKAGES:
            surfaces = (
                (
                    Path("profiles") / canonical_name,
                    "Required discipline overlays",
                    "Conditionally required disciplines",
                ),
                (
                    Path("profiles") / package_slug / "README.md",
                    "Required disciplines",
                    "Conditional disciplines",
                ),
            )
            for relative, required_heading, conditional_heading in surfaces:
                with self.subTest(profile=package_slug, surface=relative.as_posix()):
                    profile = read(relative.as_posix())
                    required = h2_section(profile, required_heading)
                    conditional = h2_section(profile, conditional_heading)
                    for overlay in CONDITIONAL_PRODUCT_OVERLAYS:
                        self.assertNotIn(overlay, required)
                        self.assertIn(overlay, conditional)

    def test_conditional_overlays_are_not_auto_selected_by_profile_expansion(
        self,
    ) -> None:
        for canonical_name, package_slug in CANONICAL_PROFILE_PACKAGES:
            completed = run_tool(
                "tools/generate-manifest/generate_manifest.py",
                "--name",
                f"conditional-overlay-{package_slug}",
                "--profile",
                Path(canonical_name).stem,
                "--language",
                "python",
                "--include-profile-required",
                "--dry-run",
                "--format",
                "json",
            )
            with self.subTest(profile=package_slug):
                self.assertEqual(
                    completed.returncode,
                    0,
                    completed.stdout + completed.stderr,
                )
                disciplines = json_result(completed)["metadata"]["manifest"][
                    "disciplines"
                ]
                self.assertNotIn("product-management", disciplines)
                self.assertNotIn("user-experience", disciplines)

    def test_representative_project_example_selects_conditional_overlays(self) -> None:
        selected_packages = h2_section(
            read("examples/full-stack/composition/STANDARDS_SELECTION.md"),
            "Selected packages",
        )
        for discipline in ("Product Management", "User Experience"):
            with self.subTest(discipline=discipline):
                self.assertRegex(
                    selected_packages,
                    rf"(?m)^\| Discipline: {re.escape(discipline)} \| "
                    r"Promoted from the profile's conditional overlays\b",
                )

    def test_nonfunctional_standard_retains_general_contract(self) -> None:
        standard = read(
            "disciplines/testing/standards/NONFUNCTIONAL_TESTING_STANDARD.md"
        )
        section_contracts = (
            ("Required behavior", GENERAL_NONFUNCTIONAL_BEHAVIOR),
            ("Required evidence", GENERAL_NONFUNCTIONAL_EVIDENCE),
            ("Review questions", GENERAL_NONFUNCTIONAL_REVIEW),
        )
        for heading, expected in section_contracts:
            observed = bullet_items(standard, heading)
            for item in expected:
                with self.subTest(section=heading, item=item):
                    self.assertIn(item, observed)

    def test_nonfunctional_completion_gate_retains_general_scope(self) -> None:
        standard = read(
            "disciplines/testing/standards/NONFUNCTIONAL_TESTING_STANDARD.md"
        )
        required_behavior = h2_section(standard, "Required behavior")
        for test_type in (
            "baseline",
            "load",
            "stress",
            "spike",
            "soak or endurance",
            "scaling",
            "failure-under-load",
            "recovery-under-load",
        ):
            with self.subTest(performance_test_type=test_type):
                self.assertIn(test_type, required_behavior)
        for state in (
            "`Applicable`",
            "`NotApplicable`",
            "`NotRun`",
            "`Blocked`",
            "`Tested`",
        ):
            with self.subTest(evidence_state=state):
                self.assertIn(state, required_behavior)

        completion_gate = h2_section(standard, "Completion gate")
        self.assertIn(
            "Do not report this area complete until the applicable requirements "
            "are implemented, evidence is recorded, unsupported claims are removed, "
            "and remaining risk is stated plainly.",
            completion_gate,
        )
        self.assertIn(
            "Do not report performance or scalability validated until every "
            "applicable test type has current evidence",
            completion_gate,
        )

    def test_readiness_template_has_one_result_per_standard_area(self) -> None:
        standard = read(
            "disciplines/sre/standards/PRODUCTION_READINESS_STANDARD.md"
        )
        template = read("disciplines/sre/templates/EVIDENCE_RECORD_TEMPLATE.md")
        standard_areas = table_areas(standard, "Readiness areas")
        self.assertIn(
            "Privacy",
            standard_areas,
            "Privacy must remain distinct from the Security readiness area.",
        )
        self.assertIn(
            "Data migration",
            standard_areas,
            "Data migration must remain a distinct production-readiness area.",
        )
        self.assertEqual(
            table_areas(template, "Production readiness"),
            standard_areas,
        )

    def test_mandatory_sre_and_testing_changes_are_breaking_with_migration(self) -> None:
        unreleased = h2_section(read("CHANGELOG.md"), "[Unreleased]")
        breaking = h3_section(unreleased, "Breaking changes")
        migration = h3_section(unreleased, "Migration notes")

        for package in (
            "Site Reliability Engineering",
            "Testing and Quality Engineering",
        ):
            with self.subTest(package=package):
                self.assertIn(package, breaking)
        self.assertIn("must migrate", breaking)

        for rule_id in ("SRE-READINESS-006", "SRE-SCALING-007"):
            with self.subTest(rule=rule_id):
                self.assertIn(rule_id, migration)
        for test_type in (
            "baseline",
            "load",
            "stress",
            "spike",
            "soak or endurance",
            "scaling",
            "failure-under-load",
            "recovery-under-load",
        ):
            with self.subTest(test_type=test_type):
                self.assertIn(test_type, migration)

    def test_readiness_template_records_overall_decision_and_authority(self) -> None:
        standard = read(
            "disciplines/sre/standards/PRODUCTION_READINESS_STANDARD.md"
        )
        decision_gate = h2_section(standard, "Decision gate")
        outcomes = tuple(re.findall(r"(?m)^- `([^`]+)`", decision_gate))
        self.assertEqual(outcomes, ("Pass", "Fail", "Blocked", "NotApplicable"))

        readiness_record = h2_section(
            read("disciplines/sre/templates/EVIDENCE_RECORD_TEMPLATE.md"),
            "Production readiness",
        )
        self.assertIn(
            "- Overall readiness result (`Pass`, `Fail`, `Blocked`, "
            "`NotApplicable`):",
            readiness_record,
        )
        self.assertIn("- Decision authority:", readiness_record)

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

    def test_ux_evidence_separates_research_and_validation_records(self) -> None:
        template = read(
            "disciplines/user-experience/templates/EVIDENCE_RECORD_TEMPLATE.md"
        )
        context = h2_section(template, "Context")
        evidence = h2_section(template, "Method and evidence")

        self.assertIn("- Research state:", context)
        self.assertIn("- Validation state:", context)
        self.assertIn("- Research evidence or rationale:", evidence)
        self.assertIn("- Validation evidence or rationale:", evidence)
        self.assertNotIn("Research/validation state", template)

    def test_usability_review_records_environment_and_date(self) -> None:
        plan = h2_section(
            read(
                "disciplines/user-experience/templates/USABILITY_REVIEW_TEMPLATE.md"
            ),
            "Plan",
        )
        self.assertIn("- Environment:", plan)
        self.assertIn("- Review date:", plan)

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
