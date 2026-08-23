from __future__ import annotations

import json
import re
import unittest
from pathlib import Path

from helpers import REPO_ROOT


NEW_BASELINE_SOURCE_REVIEWS = {
    "disciplines-product-management": "disciplines/product-management",
    "disciplines-sre": "disciplines/sre",
    "disciplines-testing": "disciplines/testing",
    "disciplines-user-experience": "disciplines/user-experience",
    "governance-product-inception-lifecycle": (
        "governance/PRODUCT_INCEPTION_LIFECYCLE.md"
    ),
}

FINAL_2026_08_23_NORMATIVE_REVISION = (
    "389055732b1afa0d35886b578194ae8789b40aaf"
)


class SourceReviewEvidenceTests(unittest.TestCase):
    def test_new_baseline_components_have_durable_source_reviews(self):
        registry = json.loads(
            (REPO_ROOT / "SOURCE_REVIEWS.json").read_text(encoding="utf-8")
        )
        records = {record["id"]: record for record in registry["records"]}

        for record_id, expected_scope in NEW_BASELINE_SOURCE_REVIEWS.items():
            with self.subTest(record=record_id):
                record = records.get(record_id)
                self.assertIsNotNone(record, f"missing source-review record: {record_id}")
                assert record is not None
                self.assertEqual(record["scope"], expected_scope)
                self.assertEqual(record["maturity"], "baseline")
                self.assertIsNotNone(record["lastReviewed"])
                self.assertEqual(
                    record["reviewEvidence"],
                    f"source-reviews/{record['lastReviewed']}.md",
                )

                evidence_path = REPO_ROOT / record["reviewEvidence"]
                self.assertTrue(evidence_path.is_file(), record["reviewEvidence"])
                evidence = evidence_path.read_text(encoding="utf-8")
                self.assertIn(expected_scope, evidence)

    def test_final_lifecycle_sre_and_testing_surfaces_are_in_the_durable_review(self):
        evidence = (
            REPO_ROOT / "source-reviews" / "2026-08-23.md"
        ).read_text(encoding="utf-8")
        revisions = set(
            re.findall(
                r"(?im)^- [^\n]*repository source revision reviewed"
                r"[^:\n]*: `([0-9a-f]{40})`",
                evidence,
            )
        )
        self.assertEqual(revisions, {FINAL_2026_08_23_NORMATIVE_REVISION})
        self.assertIn(
            "Final-revision content re-review: **Performed** for all five "
            "registered scopes",
            evidence,
        )

        lifecycle_review = evidence.split(
            "### Product Inception Lifecycle "
            "(`governance/PRODUCT_INCEPTION_LIFECYCLE.md`)",
            1,
        )[1].split("## Authoritative sources reviewed", 1)[0]
        for contract in (
            "explicitly selected",
            "Design Gate",
            "Build Gate",
            "`GOV-PRODUCT-INCEPTION-001`",
            "`GOV-PRODUCT-INCEPTION-006`",
            "`GOV-PRODUCT-INCEPTION-012`",
            "`scaled-production`",
            "every applicable scaling area is `Verified`",
            "`Applicable`, `NotRun`, or `Blocked` area prevents",
            "even when the SRE package is not otherwise selected",
            "`Pass`",
            "`Fail`",
            "`Blocked`",
        ):
            with self.subTest(lifecycle_contract=contract):
                self.assertIn(contract, lifecycle_review)

        ux_review = evidence.split(
            "### User Experience (`disciplines/user-experience`)",
            1,
        )[1].split("### Site Reliability Engineering", 1)[0]
        for research_state in (
            "`Performed`",
            "`NotRun`",
            "`Blocked`",
            "`NotApplicable`",
        ):
            with self.subTest(research_state=research_state):
                self.assertIn(research_state, ux_review)
        self.assertIn("evidence template", ux_review)
        self.assertIn("repository-authored evidence controls", ux_review)

        sre_review = evidence.split(
            "### Site Reliability Engineering (`disciplines/sre`)",
            1,
        )[1].split("### Testing and Quality Engineering", 1)[0]
        for readiness_area in ("Privacy", "Data migration"):
            with self.subTest(sre_readiness_area=readiness_area):
                self.assertIn(readiness_area, sre_review)
        for scaling_contract in (
            "overall scaling-strategy `Verified` claim",
            "every applicable area is `Verified`",
            "`Applicable`, `NotRun`, or `Blocked`",
            "`NotApplicable` requires justification",
        ):
            with self.subTest(scaling_contract=scaling_contract):
                self.assertIn(scaling_contract, sre_review)
        self.assertIn("repository-authored evidence controls", sre_review)

        testing_review = evidence.split(
            "### Testing and Quality Engineering (`disciplines/testing`)",
            1,
        )[1].split("### Product Inception Lifecycle", 1)[0]
        for control in (
            "per-test owner",
            "explicit execution authorization and safeguards",
            "safe stop conditions",
            "evidence template",
        ):
            with self.subTest(testing_control=control):
                self.assertIn(control, testing_review)
        self.assertIn("repository-authored evidence controls", testing_review)

        for limitation in (
            "Full ISO standards text: **NotRun**",
            "Later direct HTTP reachability recheck of the five ISO catalog "
            "URLs: **Blocked** by HTTP 403",
            "No user research, participant study, usability review, product "
            "adoption, lifecycle-gate execution",
            "No SRE adoption, readiness decision, scaling validation, "
            "performance test, failure test, recovery test",
            "it did not perform a second network retrieval and does not claim "
            "that every source remained reachable",
        ):
            with self.subTest(limitation=limitation):
                self.assertIn(limitation, evidence)

    def test_production_registry_is_granular_and_evidence_backed(self):
        registry = json.loads((REPO_ROOT / "SOURCE_REVIEWS.json").read_text(encoding="utf-8"))
        records = registry["records"]

        self.assertGreaterEqual(len(records), 37)
        ids = {record["id"] for record in records}
        self.assertEqual(len(ids), len(records))

        coarse_scopes = {"languages", "platforms", "virtualization", "operating-systems", "networking"}
        self.assertFalse(
            any(record["scope"] in coarse_scopes for record in records),
            "Source-review records must remain package/scoped rather than collection-wide.",
        )

        expected_language_scopes = {
            "languages/powershell",
            "languages/csharp",
            "languages/dotnet",
            "languages/javascript-typescript",
            "languages/python",
            "languages/java",
            "languages/go",
            "languages/rust",
            "languages/bash",
            "languages/sql",
            "languages/terraform-opentofu",
        }
        actual_language_scopes = {
            record["scope"]
            for record in records
            if record["scope"].startswith("languages/")
        }
        self.assertEqual(actual_language_scopes, expected_language_scopes)

        for record in records:
            with self.subTest(record=record["id"]):
                evidence = record.get("reviewEvidence")
                self.assertIsInstance(evidence, str)
                self.assertTrue(evidence)
                evidence_path = (REPO_ROOT / evidence).resolve()
                evidence_path.relative_to(REPO_ROOT.resolve())
                self.assertTrue(evidence_path.is_file(), evidence)

                for source in record["authoritativeSources"]:
                    self.assertTrue(source["url"].startswith("https://"), source)

                if record["lastReviewed"] is not None:
                    self.assertEqual(
                        evidence,
                        f"source-reviews/{record['lastReviewed']}.md",
                        "Reviewed records must point to a durable record named for the review date.",
                    )

        expected_not_run = {
            "languages-javascript-typescript",
            "languages-python",
            "languages-java",
            "languages-go",
            "languages-rust",
            "languages-bash",
            "languages-sql",
            "virtualization-vsphere",
        }
        actual_not_run = {
            record["id"] for record in records if record["lastReviewed"] is None
        }
        self.assertEqual(actual_not_run, expected_not_run)
        for record in records:
            if record["id"] in expected_not_run:
                self.assertIn("NotRun", record["notes"])

        reviewed = [record for record in records if record["lastReviewed"] is not None]
        self.assertGreaterEqual(len(reviewed), 25)

    def test_material_lifecycle_corrections_are_retained(self):
        xen_root = REPO_ROOT / "virtualization" / "xenserver-citrix-hypervisor"
        xenserver = (xen_root / "README.md").read_text(encoding="utf-8")
        xen_ops = (xen_root / "standards" / "OPERATIONS_AND_AUTOMATION_STANDARD.md").read_text(encoding="utf-8")

        rhv_root = REPO_ROOT / "virtualization" / "red-hat-virtualization"
        rhv = (rhv_root / "README.md").read_text(encoding="utf-8")
        rhv_agents = (rhv_root / "AGENTS.md").read_text(encoding="utf-8")
        rhv_ops = (rhv_root / "standards" / "OPERATIONS_AND_AUTOMATION_STANDARD.md").read_text(encoding="utf-8")

        oracle_root = REPO_ROOT / "virtualization" / "oracle-linux-kvm"
        oracle_readme = (oracle_root / "README.md").read_text(encoding="utf-8")
        oracle_agents = (oracle_root / "AGENTS.md").read_text(encoding="utf-8")
        oracle_ops = (oracle_root / "standards" / "OPERATIONS_AND_AUTOMATION_STANDARD.md").read_text(encoding="utf-8")

        evidence = (REPO_ROOT / "source-reviews" / "2026-08-15.md").read_text(encoding="utf-8")

        self.assertIn("XenServer 9 is the current GA family", xenserver)
        self.assertIn("XenServer 9 is the current GA family", xen_ops)
        self.assertNotIn("docs.xenserver.com/en-us/xenserver/8/", xenserver)
        self.assertNotIn("docs.xenserver.com/en-us/xenserver/8/", xen_ops)
        self.assertIn("docs.xenserver.com/en-us/xenserver/9/", xen_ops)

        for name, text in (("README", rhv), ("AGENTS", rhv_agents), ("operations", rhv_ops)):
            with self.subTest(rhv_document=name):
                self.assertIn("does not include new bug fixes, security fixes, hardware enablement, or root-cause analysis", text)
                self.assertNotIn("through August 31, 2026", text)
                self.assertIn("OpenShift Virtualization", text)

        for name, text in (("README", oracle_readme), ("AGENTS", oracle_agents), ("operations", oracle_ops)):
            with self.subTest(oracle_document=name):
                self.assertIn("Oracle Linux 8", text)
                self.assertIn("legacy managed boundary", text)
                self.assertNotIn("OLVM for Oracle Linux 9/10", text)
                self.assertNotIn("OLVM into current 9/10", text)

        self.assertIn("Manual GitHub Actions `source-freshness` dispatch: **Blocked**", evidence)
        self.assertIn("vSphere product documentation review: **NotRun/Blocked**", evidence)
        self.assertIn("Repository source revision reviewed: `90784f344e7920d594de4837b0bfecdcdea514e2`", evidence)
        self.assertNotIn("Repository source revision reviewed: `main`", evidence)
        self.assertIn("JavaScript/TypeScript, Python, Java, Go, Rust, Bash, and SQL were not reviewed", evidence)

    def test_reviewed_virtualization_packages_do_not_duplicate_review_dates(self):
        paths = [
            "virtualization/proxmox-ve/README.md",
            "virtualization/xcp-ng/README.md",
            "virtualization/kvm-libvirt/README.md",
            "virtualization/nutanix-ahv/README.md",
            "virtualization/microsoft-hyper-v/README.md",
        ]
        for path in paths:
            text = (REPO_ROOT / path).read_text(encoding="utf-8")
            with self.subTest(path=path):
                self.assertNotIn("Last repository source review:", text)
                self.assertIn("SOURCE_REVIEWS.json", text)
                self.assertIn("source-reviews/", text)

    def test_reviewed_csharp_package_uses_registry_evidence_authority(self):
        paths = [
            "languages/csharp/README.md",
            "languages/csharp/AGENTS.md",
        ]
        for path in paths:
            text = (REPO_ROOT / path).read_text(encoding="utf-8")
            with self.subTest(path=path):
                self.assertNotIn("2026-07-16", text)
                self.assertIn("SOURCE_REVIEWS.json", text)
                self.assertIn("source-reviews/", text)
                self.assertIn("2026-08-15", text)

    def test_powercli_standard_uses_accountable_review_evidence(self):
        powercli = (REPO_ROOT / "virtualization" / "vsphere-esxi" / "standards" / "POWERCLI_AUTOMATION_STANDARD.md").read_text(encoding="utf-8")
        self.assertNotIn("2026-07-15", powercli)
        self.assertIn("SOURCE_REVIEWS.json", powercli)
        self.assertIn("source-reviews/", powercli)
        self.assertIn("2026-08-15", powercli)

    def test_olvm_scope_narrowing_is_classified_as_breaking(self):
        changelog = (REPO_ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
        release = (REPO_ROOT / "releases" / "0.10.0.md").read_text(encoding="utf-8")
        changelog_0100 = changelog.split("## [0.10.0] - 2026-08-16", 1)[1].split("## [0.9.0]", 1)[0]
        documents = (
            ("CHANGELOG.md#0.10.0", changelog_0100, "### Breaking changes", "### Normative changes"),
            ("releases/0.10.0.md", release, "## Breaking changes", "## Normative changes"),
        )
        for name, text, breaking_heading, normative_heading in documents:
            breaking = text.split(breaking_heading, 1)[1].split(normative_heading, 1)[0]
            with self.subTest(document=name):
                self.assertIn("Oracle Linux Virtualization Manager (OLVM)", breaking)
                self.assertIn("Oracle Linux 9/10", breaking)

    def test_migration_notes_disclose_lifecycle_and_source_review_boundaries(self):
        migration = (REPO_ROOT / "releases" / "migrations" / "0.10.0.md").read_text(encoding="utf-8")

        self.assertIn("XenServer 9", migration)
        self.assertIn("Red Hat Virtualization", migration)
        self.assertIn("OpenShift Virtualization", migration)
        self.assertIn("Oracle Linux 9/10 KVM", migration)
        self.assertIn("Oracle Linux 8/OLVM legacy support boundary", migration)
        self.assertIn("SOURCE_REVIEWS.json", migration)
        self.assertIn("NotRun`/`Blocked", migration)

    def test_changelog_discloses_lifecycle_corrections(self):
        changelog = (REPO_ROOT / "CHANGELOG.md").read_text(encoding="utf-8")

        self.assertIn("XenServer 9 is the current GA family", changelog)
        self.assertIn("Red Hat Virtualization guidance", changelog)
        self.assertIn("no new bug/security fixes", changelog)
        self.assertIn("Oracle Linux KVM guidance", changelog)
        self.assertIn("OLVM", changelog)
        self.assertIn("unreviewed package records remain `lastReviewed: null`", changelog)

    def test_source_catalog_points_to_current_review_boundaries(self):
        sources = (REPO_ROOT / "SOURCES.md").read_text(encoding="utf-8")

        self.assertIn("XenServer 9 product documentation", sources)
        self.assertIn("Cisco IOS XE lifecycle support statement", sources)
        self.assertIn("Red Hat Virtualization lifecycle policy", sources)
        self.assertIn("Nutanix support policies and FAQs", sources)
        self.assertIn("source-reviews/", sources)


if __name__ == "__main__":
    unittest.main()
