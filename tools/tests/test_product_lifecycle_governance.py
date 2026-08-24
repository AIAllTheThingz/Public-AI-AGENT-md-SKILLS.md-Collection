from __future__ import annotations

import json
import re
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator

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

REPRESENTATIVE_LIFECYCLE_EXAMPLES = (
    "full-stack",
    "web-api",
)
LIFECYCLE_STANDARD = "governance/PRODUCT_INCEPTION_LIFECYCLE.md"
LIFECYCLE_MANIFEST_EXTENSION = "AIAllTheThingz.governanceSelections"

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

    def test_design_gate_records_an_explicit_decision(self) -> None:
        design_gate = h3_section(
            read("governance/PRODUCT_INCEPTION_LIFECYCLE.md"),
            "Design Gate",
        )
        self.assertIn(
            "**Decision:** `Pass`, `Fail`, or `Blocked`.",
            design_gate,
        )
        self.assertIn(
            "A pass requires reviewed design evidence for every applicable area",
            design_gate,
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

    def test_representative_lifecycle_selection_is_synchronized(self) -> None:
        schema = json.loads(read("schemas/v1/project-manifest.schema.json"))
        validator = Draft202012Validator(schema)

        for example in REPRESENTATIVE_LIFECYCLE_EXAMPLES:
            text_surfaces = (
                (f"examples/{example}/AGENTS.md", "../../" + LIFECYCLE_STANDARD),
                (f"examples/{example}/README.md", "../../" + LIFECYCLE_STANDARD),
                (f"examples/{example}/MANIFEST.md", "../../" + LIFECYCLE_STANDARD),
                (
                    f"examples/{example}/composition/STANDARDS_SELECTION.md",
                    "../../../" + LIFECYCLE_STANDARD,
                ),
                (
                    f"examples/{example}/docs/COMPLETION_EVIDENCE.md",
                    "../../../" + LIFECYCLE_STANDARD,
                ),
            )
            for relative, link_target in text_surfaces:
                with self.subTest(example=example, surface=relative):
                    matching_lines = [
                        line
                        for line in read(relative).splitlines()
                        if link_target in line
                    ]
                    self.assertTrue(matching_lines, f"missing selection: {link_target}")
                    self.assertTrue(
                        any("select" in line.casefold() for line in matching_lines),
                        f"selection is not explicit: {relative}",
                    )

            manifest_path = f"examples/{example}/project-manifest.json"
            with self.subTest(example=example, surface=manifest_path):
                manifest = json.loads(read(manifest_path))
                self.assertEqual(
                    manifest.get("extensions", {}).get(
                        LIFECYCLE_MANIFEST_EXTENSION
                    ),
                    [LIFECYCLE_STANDARD],
                )
                self.assertNotIn(
                    "product-inception-lifecycle",
                    manifest["disciplines"],
                )
                errors = sorted(
                    validator.iter_errors(manifest),
                    key=lambda error: list(error.absolute_path),
                )
                self.assertEqual(errors, [], f"{manifest_path}: {errors}")

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
        testing_agents = read("disciplines/testing/AGENTS.md")
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
        for outcome in ("`Pass`", "`Fail`", "`Blocked`", "`NotApplicable`"):
            with self.subTest(performance_outcome=outcome):
                self.assertIn(outcome, required_behavior)
        self.assertIn("### TEST-PERFORMANCE-006", testing_agents)
        self.assertIn(
            "execution state separately from outcome",
            h3_section(testing_agents, "TEST-PERFORMANCE-006"),
        )

        completion_gate = h2_section(standard, "Completion gate")
        self.assertIn(
            "Do not report this area complete until the applicable requirements "
            "are implemented, evidence is recorded, unsupported claims are removed, "
            "and remaining risk is stated plainly.",
            completion_gate,
        )
        self.assertIn(
            "Do not report performance or scalability validated until every "
            "applicable test type has state `Tested` and a separate current "
            "explicit outcome of `Pass`",
            completion_gate,
        )
        self.assertIn(
            "Any applicable `Fail`, `Blocked`, `NotRun`, missing, stale, or "
            "different-artifact result prevents the validated claim",
            completion_gate,
        )

    def test_performance_matrix_retains_per_test_safety_ownership(self) -> None:
        performance = h2_section(
            read("disciplines/testing/templates/EVIDENCE_RECORD_TEMPLATE.md"),
            "Performance validation",
        )
        table = [
            [cell.strip() for cell in line.strip().strip("|").split("|")]
            for line in performance.splitlines()
            if line.startswith("|")
        ]
        self.assertGreaterEqual(len(table), 10)
        header = table[0]
        for required_column in (
            "Outcome (`Pass`, `Fail`, `Blocked`, `NotApplicable`)",
            "Owner",
            "Authorization and safeguards",
            "Stop conditions",
            "Primary evidence/result",
        ):
            with self.subTest(column=required_column):
                self.assertIn(required_column, header)

        separator, *rows = table[1:]
        self.assertTrue(all(set(cell) <= {"-", ":"} for cell in separator))
        self.assertEqual(
            [row[0] for row in rows],
            [
                "Baseline",
                "Load",
                "Stress",
                "Spike",
                "Soak/endurance",
                "Scaling",
                "Failure under load",
                "Recovery under load",
            ],
        )
        for row in rows:
            with self.subTest(test_type=row[0]):
                self.assertEqual(len(row), len(header))
        self.assertIn("`Tested` records execution evidence and does not imply `Pass`", performance)

    def test_acceptance_decisions_are_separate_from_evidence_states(self) -> None:
        lifecycle = read("governance/PRODUCT_INCEPTION_LIFECYCLE.md")
        product_agents = h3_section(
            read("disciplines/product-management/AGENTS.md"),
            "PROD-ACCEPT-004",
        )
        acceptance_standard = read(
            "disciplines/product-management/standards/ACCEPTANCE_CRITERIA_STANDARD.md"
        )
        evidence_template = h2_section(
            read("disciplines/product-management/templates/EVIDENCE_RECORD_TEMPLATE.md"),
            "Acceptance validation",
        )
        production_rule = h3_section(lifecycle, "GOV-PRODUCT-INCEPTION-009")
        production_gate = h2_section(lifecycle, "Production-candidate gate")

        for contract in (
            "acceptance separately from execution or evidence state",
            "every applicable criterion has a current explicit `Pass`",
        ):
            with self.subTest(product_acceptance=contract):
                self.assertIn(contract, product_agents)
        for contract in (
            "an execution or evidence state such as `Tested` or `Reviewed` is not "
            "an acceptance result",
            "Every applicable criterion must have a current explicit `Pass`",
        ):
            with self.subTest(acceptance_standard_contract=contract):
                self.assertIn(contract, acceptance_standard)
        for result in ("`Pass`", "`Fail`", "`Blocked`", "`NotRun`", "`NotApplicable`"):
            with self.subTest(acceptance_result=result):
                self.assertIn(result, evidence_template)
        self.assertIn("`Tested` and the presence of output do not imply `Pass`", evidence_template)

        for contract in (
            "every material requirement is implemented",
            "every applicable functional and nonfunctional acceptance criterion",
            "current explicit `Pass`",
            "Any acceptance criterion with a `Fail`, `Blocked`, `NotRun`, missing, "
            "stale, or different-candidate result prevents the transition",
        ):
            with self.subTest(lifecycle_acceptance=contract):
                self.assertIn(contract, production_rule)
        self.assertIn(
            "`Tested`, `Reviewed`, or the presence of test output does not imply `Pass`",
            production_gate,
        )
        self.assertIn(
            "Production-readiness results do not replace functional or nonfunctional "
            "acceptance decisions",
            production_gate,
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
        release = h2_section(
            read("CHANGELOG.md"), "[1.0.0-rc.1] - 2026-08-16"
        )
        breaking = h3_section(release, "Breaking changes")
        migration = h3_section(release, "Migration notes")

        for package in (
            "Site Reliability Engineering",
            "Testing and Quality Engineering",
        ):
            with self.subTest(package=package):
                self.assertIn(package, breaking)
        self.assertIn("must migrate", breaking)

        for rule_id in (
            "SRE-READINESS-006",
            "SRE-SCALING-007",
            "TEST-PERFORMANCE-006",
        ):
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

    def test_conditional_product_overlays_have_breaking_profile_migration(self) -> None:
        release = h2_section(
            read("CHANGELOG.md"), "[1.0.0-rc.1] - 2026-08-16"
        )
        breaking = h3_section(release, "Breaking changes")
        migration = h3_section(release, "Migration notes")

        for overlay in ("Product Management", "User Experience"):
            with self.subTest(overlay=overlay):
                self.assertIn(overlay, breaking)
                self.assertIn(overlay, migration)
        self.assertIn("conditional overlays", breaking)
        self.assertIn("all 13 canonical project profiles", breaking)
        self.assertIn("becomes mandatory", breaking)

        for canonical_name, _package_slug in CANONICAL_PROFILE_PACKAGES:
            with self.subTest(existing_profile=canonical_name):
                self.assertIn(f"`{Path(canonical_name).stem}`", migration)
        self.assertIn("selected primary and secondary profile", migration)
        self.assertIn("predicate is not satisfied", migration)
        self.assertIn("omission rationale", migration)

        versioned_notes = read("releases/1.0.0-rc.1.md")
        versioned_migration = read("releases/migrations/1.0.0-rc.1.md")
        for document in (versioned_notes, versioned_migration):
            with self.subTest(versioned_document=document[:40]):
                self.assertIn("Product Management", document)
                self.assertIn("User Experience", document)
                self.assertIn("breaking", document.casefold())
        self.assertNotIn(
            "The candidate is compatible with published `v0.10.0`",
            versioned_notes,
        )
        self.assertNotIn("declares no breaking change", versioned_migration)

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

    def test_scaling_overall_verification_requires_every_applicable_area(self) -> None:
        standard = read("disciplines/sre/standards/SCALING_STRATEGY_STANDARD.md")
        completion_gate = h2_section(standard, "Completion gate")
        for required_contract in (
            "overall scaling-strategy `Verified` claim",
            "every applicable area to be `Verified`",
            "`Applicable`, `NotRun`, `Blocked`, or `Failed` prevents",
            "`Failed` must remain distinct from unresolved work",
            "`NotApplicable` requires recorded justification",
        ):
            with self.subTest(required_contract=required_contract):
                self.assertIn(required_contract, completion_gate)

        scaling_record = h2_section(
            read("disciplines/sre/templates/EVIDENCE_RECORD_TEMPLATE.md"),
            "Scaling strategy",
        )
        self.assertIn(
            "- Overall scaling-strategy state (`Verified`, `Failed`, `NotRun`, "
            "`Blocked`, `NotApplicable`):",
            scaling_record,
        )
        self.assertIn(
            "State (`Applicable`, `NotApplicable`, `NotRun`, `Blocked`, `Failed`, "
            "`Verified`)",
            scaling_record,
        )
        self.assertIn(
            "Use `Failed` when representative validation executes but misses "
            "authorized criteria",
            scaling_record,
        )
        self.assertIn("- Decision authority:", scaling_record)
        self.assertIn("- Supported workload and operating envelope:", scaling_record)

        scaling_rule = h3_section(
            read("disciplines/sre/AGENTS.md"),
            "SRE-SCALING-007",
        )
        self.assertIn(
            "Record representative validation that misses authorized criteria as "
            "`Failed`",
            scaling_rule,
        )
        self.assertIn(
            "any `Applicable`, `NotRun`, `Blocked`, or `Failed` area prevents",
            scaling_rule,
        )

    def test_product_brief_defines_standalone_research_states(self) -> None:
        brief = h2_section(
            read("disciplines/product-management/templates/PRODUCT_BRIEF_TEMPLATE.md"),
            "Scope and evidence",
        )
        outcome_standard = read(
            "disciplines/product-management/standards/USER_OUTCOME_STANDARD.md"
        )
        evidence = h2_section(
            read("disciplines/product-management/templates/EVIDENCE_RECORD_TEMPLATE.md"),
            "Context",
        )
        for state in ("`Performed`", "`NotRun`", "`Blocked`", "`NotApplicable`"):
            with self.subTest(product_research_state=state):
                self.assertIn(state, brief)
                self.assertIn(state, outcome_standard)
                self.assertIn(state, evidence)
        self.assertIn("- Research evidence or rationale:", brief)
        self.assertIn(
            "Use `Performed` only when actual research was completed and "
            "attributable evidence exists",
            brief,
        )
        self.assertIn(
            "Product Management can record these states without selecting the "
            "separate User Experience package",
            brief,
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
        ux_agents = h3_section(
            read("disciplines/user-experience/AGENTS.md"),
            "UX-VALIDATE-005",
        )
        research_standard = read(
            "disciplines/user-experience/standards/USER_RESEARCH_STANDARD.md"
        )
        validation_standard = read(
            "disciplines/user-experience/standards/UX_VALIDATION_STANDARD.md"
        )
        context = h2_section(template, "Context")
        evidence = h2_section(template, "Method and evidence")
        results = h2_section(template, "Results")

        self.assertIn(
            "- Research state (`Performed`, `NotRun`, `Blocked`, or "
            "`NotApplicable`):",
            context,
        )
        self.assertIn(
            "- Validation state (`Tested`, `Reviewed`, `OperationallyVerified`, "
            "`NotRun`, `Blocked`, or `NotApplicable`):",
            context,
        )
        self.assertIn(
            "- Overall validation outcome (`Pass`, `Fail`, `Blocked`, or "
            "`NotApplicable`):",
            context,
        )
        self.assertIn("- Validation decision authority and date:", context)
        self.assertIn("- Research evidence or rationale:", evidence)
        self.assertIn("- Validation evidence or rationale:", evidence)
        self.assertNotIn("Research/validation state", template)
        for state in ("`Performed`", "`NotRun`", "`Blocked`", "`NotApplicable`"):
            with self.subTest(research_state=state):
                self.assertIn(state, research_standard)
        for contract in (
            "validation state separately from outcome",
            "independent overall `Pass`",
            "successful outcomes for every applicable validation method and claim",
        ):
            with self.subTest(ux_rule_contract=contract):
                self.assertIn(contract, ux_agents)
        for contract in (
            "independent `Pass`, `Fail`, `Blocked`, or justified `NotApplicable` "
            "outcome",
            "Execution or evidence state does not imply `Pass`",
            "Any applicable `Fail`, `Blocked`, `NotRun`, missing, stale, or "
            "different-version result prevents the overall pass",
            "separate overall validation outcome is not `Pass`",
        ):
            with self.subTest(ux_validation_contract=contract):
                self.assertIn(contract, validation_standard)
        for column in (
            "Authorized criteria",
            "Primary evidence",
            "State",
            "Outcome (`Pass`, `Fail`, `Blocked`, `NotApplicable`)",
            "Owner",
        ):
            with self.subTest(ux_result_column=column):
                self.assertIn(column, results)
        self.assertIn(
            "`Tested`, `Reviewed`, or `OperationallyVerified` does not imply `Pass`",
            context,
        )
        self.assertIn(
            "Any applicable `Fail`, `Blocked`, `NotRun`, missing, stale, or "
            "different-version result prevents a UX-validated claim",
            results,
        )

    def test_lifecycle_normative_controls_have_stable_rule_ids(self) -> None:
        lifecycle = read("governance/PRODUCT_INCEPTION_LIFECYCLE.md")
        expected_ids = [
            f"GOV-PRODUCT-INCEPTION-{number:03d}" for number in range(1, 13)
        ]
        observed_ids = re.findall(
            r"(?m)^### (GOV-PRODUCT-INCEPTION-\d{3})$",
            lifecycle,
        )
        self.assertEqual(observed_ids, expected_ids)

        for rule_id in expected_ids:
            with self.subTest(rule_id=rule_id):
                rule = h3_section(lifecycle, rule_id)
                self.assertIn("**Requirement:**", rule)
                self.assertIn("**Expected evidence:**", rule)
                self.assertIn(f"(#{rule_id.lower()})", lifecycle)

        build_rule = h3_section(lifecycle, "GOV-PRODUCT-INCEPTION-006")
        self.assertIn(
            "Normal production implementation must not start unless the Concept, "
            "Requirements, Design, and Build Gate decisions are explicitly `Pass`",
            build_rule,
        )

    def test_scaled_production_requires_full_scaling_verification(self) -> None:
        lifecycle = read("governance/PRODUCT_INCEPTION_LIFECYCLE.md")
        lifecycle_rule = h3_section(lifecycle, "GOV-PRODUCT-INCEPTION-008")
        lifecycle_states = h2_section(lifecycle, "Product lifecycle states")
        for contract in (
            "explicitly selecting the Site Reliability Engineering package",
            "complete [Scaling Strategy Standard]",
            "every applicable scaling area is `Verified`",
            "`Applicable`, `NotRun`, `Blocked`, or `Failed` area prevents",
            "every `NotApplicable` area requires justification",
        ):
            with self.subTest(contract=contract):
                self.assertIn(contract, lifecycle_rule)
        for contract in (
            "the Site Reliability Engineering package is selected",
            "complete Scaling Strategy Standard is satisfied",
            "every applicable scaling area is `Verified`",
            "Any `Applicable`, `NotRun`, `Blocked`, or `Failed` area prevents this "
            "state",
        ):
            with self.subTest(state_contract=contract):
                self.assertIn(contract, lifecycle_states)

    def test_later_lifecycle_states_require_complete_sre_contracts(self) -> None:
        lifecycle = read("governance/PRODUCT_INCEPTION_LIFECYCLE.md")
        readiness = read(
            "disciplines/sre/standards/PRODUCTION_READINESS_STANDARD.md"
        )
        production_rule = h3_section(lifecycle, "GOV-PRODUCT-INCEPTION-009")
        production_gate = h2_section(lifecycle, "Production-candidate gate")
        scaling_rule = h3_section(lifecycle, "GOV-PRODUCT-INCEPTION-008")

        self.assertIn("- GOV-PROD", lifecycle)
        self.assertIn("- GOV-EXCEPTION", lifecycle)
        for contract in (
            "Build Gate and its prerequisite Concept, Requirements, and Design "
            "Gates are `Pass`",
            "every material requirement is implemented",
            "every applicable functional and nonfunctional acceptance criterion",
            "current explicit `Pass`",
            "Site Reliability Engineering package is explicitly selected",
            "complete [Production Readiness Standard]",
            "readiness overall decision must be `Pass`",
            "no applicable area may be `Fail`, `Blocked`, or `NotRun`",
        ):
            with self.subTest(readiness_contract=contract):
                self.assertIn(contract, production_rule)
        self.assertIn("Linked prerequisite gate decisions", production_rule)
        for readiness_area in table_areas(readiness, "Readiness areas"):
            with self.subTest(readiness_area=readiness_area):
                self.assertIn(readiness_area, production_gate)
        self.assertIn("separate overall `Pass`", production_gate)
        self.assertIn("accountable decision authority", production_gate)

        for contract in (
            "`production` evidence boundary remains satisfied",
            "explicitly selecting the Site Reliability Engineering package",
            "complete [Scaling Strategy Standard]",
            "overall scaling-strategy decision is `Verified`",
            "every applicable scaling area is `Verified`",
            "`Applicable`, `NotRun`, `Blocked`, or `Failed` area prevents",
        ):
            with self.subTest(scaling_contract=contract):
                self.assertIn(contract, scaling_rule)
        for evidence_contract in (
            "retains the production approval",
            "overall `Verified` decision",
            "supported envelope",
        ):
            with self.subTest(scaling_evidence=evidence_contract):
                self.assertIn(evidence_contract, scaling_rule)

    def test_production_requires_exact_artifact_deployment_evidence(self) -> None:
        lifecycle = read("governance/PRODUCT_INCEPTION_LIFECYCLE.md")
        lifecycle_rule = h3_section(lifecycle, "GOV-PRODUCT-INCEPTION-008")
        lifecycle_states = h2_section(lifecycle, "Product lifecycle states")
        production_transition = h2_section(lifecycle, "Production transition")
        product_evidence = h2_section(
            read("disciplines/product-management/templates/EVIDENCE_RECORD_TEMPLATE.md"),
            "Production transition",
        )
        sre_evidence = h2_section(
            read("disciplines/sre/templates/EVIDENCE_RECORD_TEMPLATE.md"),
            "Production transition evidence",
        )

        for contract in (
            "complete `production-candidate` boundary remains satisfied",
            "accountable delegated approval is recorded",
            "exact approved artifact and configuration were successfully deployed",
            "are operating within the stated production environment and scope",
            "failed, blocked, not-run, missing, stale, or different-artifact",
            "prevents `production`",
        ):
            with self.subTest(production_rule=contract):
                self.assertIn(contract, lifecycle_rule)
        for contract in (
            "successfully deployed into and are operating within the stated production",
            "failed, blocked, not-run, missing, stale, or different-artifact",
        ):
            with self.subTest(production_state=contract):
                self.assertIn(contract, lifecycle_states)
        for contract in (
            "deployment identifier",
            "start and completion time",
            "post-deployment health or monitoring verification",
            "rollback or recovery readiness",
            "readiness `Pass`, approval to deploy, deployment plan",
            "does not establish the `production` state",
        ):
            with self.subTest(production_transition=contract):
                self.assertIn(contract, production_transition)
        for template in (product_evidence, sre_evidence):
            for contract in (
                "Exact approved artifact, source revision, and configuration",
                "Deployment record, owner, start time, and completion time",
                "Post-deployment health, monitoring, and representative operational evidence",
                "Rollback or recovery readiness",
                "`OperationallyVerified`, `NotRun`, or `Blocked`",
            ):
                with self.subTest(template_contract=contract):
                    self.assertIn(contract, template)

    def test_lifecycle_states_and_exceptions_fail_closed(self) -> None:
        lifecycle = read("governance/PRODUCT_INCEPTION_LIFECYCLE.md")
        evidence_states = h2_section(lifecycle, "Evidence states")
        lifecycle_states = h2_section(lifecycle, "Product lifecycle states")
        exceptions = h2_section(lifecycle, "Exceptions and prohibited shortcuts")

        self.assertIn("Lifecycle evidence records use only", evidence_states)
        for state in (
            "`Planned`",
            "`Implemented`",
            "`Tested`",
            "`Reviewed`",
            "`OperationallyVerified`",
            "`NotRun`",
            "`Blocked`",
            "`NotApplicable`",
        ):
            with self.subTest(evidence_state=state):
                self.assertIn(state, evidence_states)

        for state_contract in (
            "| `defined` | The Concept and Requirements gates are `Pass`",
            "| `MVP` | The Build Gate is `Pass`",
            "| `beta` | The Build Gate is `Pass`",
            "The label does not authorize production exposure",
            "| `production-candidate` | The Build Gate and its prerequisite",
            "| `production` | The `production-candidate` evidence boundary",
            "| `scaled-production` | The `production` evidence boundary",
            "every evidence boundary and prerequisite for the resulting state",
        ):
            with self.subTest(state_contract=state_contract):
                self.assertIn(state_contract, lifecycle_states)

        self.assertIn(
            "Do not use an exception to convert `Fail`, `Blocked`, `NotRun`, or "
            "missing package evidence into `Pass`, `Verified`, or a later "
            "lifecycle state",
            exceptions,
        )

    def test_build_gate_requires_applicable_package_selection(self) -> None:
        lifecycle = read("governance/PRODUCT_INCEPTION_LIFECYCLE.md")
        build_rule = h3_section(lifecycle, "GOV-PRODUCT-INCEPTION-006")
        traceability_rule = h3_section(lifecycle, "GOV-PRODUCT-INCEPTION-010")
        build_gate = h2_section(lifecycle, "Inception gates")
        applicability = h2_section(lifecycle, "Applicability")
        self.assertIn(
            "Concept, Requirements, Design, and Build Gate decisions are "
            "explicitly `Pass`",
            build_rule,
        )
        self.assertIn(
            "every applicable package and technology selection or justified "
            "`NotApplicable` decision",
            build_rule,
        )
        self.assertIn(
            "Linked `Pass` decisions for the prerequisite Concept, Requirements, "
            "and Design Gates",
            build_rule,
        )
        self.assertIn(
            "selected every applicable governance, language, discipline, "
            "framework, platform, virtualization, operating-system, and "
            "networking package",
            build_gate,
        )
        self.assertIn(
            "`Pass` decisions for the Concept, Requirements, and Design Gates",
            build_gate,
        )
        for contract in (
            "Product Management package",
            "Requirement Traceability Standard",
            "for every material requirement",
        ):
            with self.subTest(traceability_contract=contract):
                self.assertIn(contract, applicability)
                self.assertIn(contract, traceability_rule)

    def test_lifecycle_links_its_normative_dependencies(self) -> None:
        lifecycle = read("governance/PRODUCT_INCEPTION_LIFECYCLE.md")
        related = h2_section(lifecycle, "Related policies, standards, and templates")
        for target in (
            "ORGANIZATION_CONTRACT.md",
            "AGENT_WORKING_METHOD.md",
            "RISK_CLASSIFICATION.md",
            "COMPLETION_EVIDENCE.md",
            "PRODUCTION_READINESS.md",
            "EXCEPTION_PROCESS.md",
            "../disciplines/product-management/standards/TRACEABILITY_STANDARD.md",
            "../disciplines/sre/standards/PRODUCTION_READINESS_STANDARD.md",
            "../disciplines/sre/standards/SCALING_STRATEGY_STANDARD.md",
        ):
            with self.subTest(dependency=target):
                self.assertIn(target, related)

    def test_web_api_example_does_not_claim_unavailable_later_states(self) -> None:
        example_surfaces = (
            "examples/web-api/README.md",
            "examples/web-api/composition/STANDARDS_SELECTION.md",
            "examples/web-api/docs/COMPLETION_EVIDENCE.md",
        )
        for relative in example_surfaces:
            with self.subTest(surface=relative):
                surface = read(relative)
                self.assertIn("production-candidate", surface)
                self.assertIn("Site Reliability Engineering", surface)
                self.assertTrue(
                    any(
                        boundary in surface.casefold()
                        for boundary in (
                            "does not claim `production-candidate`",
                            "claims no `production-candidate`",
                            "no `production-candidate`",
                        )
                    ),
                    f"missing explicit later-state boundary: {relative}",
                )

    def test_usability_review_records_environment_and_date(self) -> None:
        template = read(
            "disciplines/user-experience/templates/USABILITY_REVIEW_TEMPLATE.md"
        )
        plan = h2_section(template, "Plan")
        results = h2_section(template, "Results")
        self.assertIn("- Environment:", plan)
        self.assertIn("- Review date:", plan)
        for column in (
            "Observed task result",
            "Authorized criteria",
            "Validation outcome (`Pass`, `Fail`, `Blocked`, `NotApplicable`)",
            "Primary evidence",
        ):
            with self.subTest(usability_result_column=column):
                self.assertIn(column, results)
        self.assertIn(
            "- Validation state (`Tested`, `Reviewed`, `OperationallyVerified`, "
            "`NotRun`, `Blocked`, or `NotApplicable`):",
            results,
        )
        self.assertIn(
            "- Overall validation outcome (`Pass`, `Fail`, `Blocked`, or "
            "`NotApplicable`):",
            results,
        )
        self.assertIn("- Validation decision authority:", results)
        self.assertIn("Validation state does not imply outcome", results)
        self.assertIn(
            "Any applicable `Fail`, `Blocked`, `NotRun`, missing, stale, or "
            "different-version result prevents a UX-validated claim",
            results,
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
            "without sre",
        ):
            with self.subTest(weakening_phrase=weakening_phrase):
                self.assertNotIn(weakening_phrase, body.casefold())


if __name__ == "__main__":
    unittest.main()
