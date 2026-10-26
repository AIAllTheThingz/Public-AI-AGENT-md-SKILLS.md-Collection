from __future__ import annotations

import sys
import unittest

from helpers import REPO_ROOT

LIB_ROOT = REPO_ROOT / "tools" / "lib"
if str(LIB_ROOT) not in sys.path:
    sys.path.insert(0, str(LIB_ROOT))

from standards_tools.models import Finding, ToolResult  # noqa: E402

# Public finding codes emitted by the tools published in v0.10.0 (commit 83c73f3).
# Their meaning is a stable interface (tools/RELEASE_AND_COMPATIBILITY.md); never remove one.
PUBLISHED_FINDING_CODES = frozenset(
    {
        "AGENTS_INCOMPLETE",
        "BOOTSTRAP_PRESENT",
        "CHANGELOG_UNRELEASED_MISSING",
        "CHANGELOG_VERSION_MISSING",
        "CODEOWNERS_ENCODING",
        "CODEOWNERS_INVALID",
        "CODEOWNERS_MISSING",
        "CODEOWNERS_OWNER_MISSING",
        "CODEOWNERS_ROUTE_MISSING",
        "COMPOSITION_NO_DISCIPLINES",
        "DEPENDENCY_INPUT_MISSING",
        "DEPENDENCY_LOCK_MISSING",
        "DEPENDENCY_LOCK_OUT_OF_SYNC",
        "DEPENDENCY_LOCK_UNHASHED",
        "DUPLICATE_ID",
        "JSON_INVALID",
        "LICENSE_DECLARATION_ENCODING",
        "LICENSE_DECLARATION_MISSING",
        "LICENSE_ENCODING",
        "LICENSE_INVALID",
        "LICENSE_SELECTION_STALE",
        "LICENSING_ENCODING",
        "LICENSING_POLICY_INVALID",
        "LINK_ABSOLUTE_PATH",
        "LINK_ESCAPES_ROOT",
        "LINK_MISSING_ANCHOR",
        "LINK_MISSING_TARGET",
        "LINK_UNSAFE_SCHEME",
        "MAINTAINERS_ENCODING",
        "MAINTAINERS_POLICY_INCOMPLETE",
        "MAINTAINER_LIMITATION_MISSING",
        "MAINTAINER_ROSTER_INVALID",
        "MANIFEST_NO_DISCIPLINES",
        "MARKDOWN_ENCODING",
        "MATURITY_POLICY_SECTION_MISSING",
        "MIGRATION_NOTES_INCOMPLETE",
        "MIGRATION_NOTES_MISSING",
        "NEGATIVE_EXAMPLE_PASSED",
        "NOTICE_ENCODING",
        "NOTICE_INVALID",
        "OWNERSHIP_DECLARATION_ENCODING",
        "OWNERSHIP_DECLARATION_MISSING",
        "OWNERSHIP_ROADMAP_STALE",
        "PYTHON_CACHE_PRESENT",
        "RELEASE_FILE_MISSING",
        "RELEASE_HEAD_TAG_MISSING",
        "RELEASE_NOTES_MISSING",
        "RELEASE_NOTES_SECTION_MISSING",
        "RELEASE_NOTES_VERSION_MISMATCH",
        "RELEASE_POLICY_MARKER_MISSING",
        "RELEASE_POLICY_SECTION_MISSING",
        "RELEASE_PUBLICATION_BLOCKED",
        "RELEASE_PUBLICATION_VERSION_MISMATCH",
        "RELEASE_STATE_INVALID",
        "RELEASE_TAG_MISMATCH",
        "RELEASE_VERSION_INVALID",
        "RELEASE_WORKFLOW_INCOMPLETE",
        "RELEASE_WORKFLOW_MISSING",
        "ROADMAP_ENCODING",
        "ROOT_FILE_MISSING",
        "SCHEMA_ID_DUPLICATE",
        "SCHEMA_ID_MISSING",
        "SCHEMA_INSTANCE_INVALID",
        "SCHEMA_INVALID",
        "SCHEMA_MISSING",
        "SCHEMA_NEGATIVE_EXAMPLE_MISSING",
        "SCHEMA_POSITIVE_EXAMPLE_MISSING",
        "SCHEMA_REMOTE_REF",
        "SCHEMA_VERSION_MISMATCH",
        "SKILL_BODY_MISSING",
        "SKILL_BODY_TITLE_MISSING",
        "SKILL_BODY_TOO_LONG",
        "SKILL_BODY_TRIGGER_HEADING",
        "SKILL_DESCRIPTION_TOO_LONG",
        "SKILL_DESCRIPTION_TOO_SHORT",
        "SKILL_DESCRIPTION_TRIGGER_MISSING",
        "SKILL_DESCRIPTION_WORDY",
        "SKILL_FILE_ESCAPE",
        "SKILL_FRONTMATTER_FIELD_DUPLICATE",
        "SKILL_FRONTMATTER_FIELD_MISSING",
        "SKILL_FRONTMATTER_INVALID",
        "SKILL_FRONTMATTER_KEY_UNSUPPORTED",
        "SKILL_FRONTMATTER_MISSING",
        "SKILL_FRONTMATTER_UNTERMINATED",
        "SKILL_LINK_ABSOLUTE",
        "SKILL_LINK_ESCAPE",
        "SKILL_LINK_MISSING",
        "SKILL_LINK_UNSAFE_SCHEME",
        "SKILL_METADATA_ESCAPE",
        "SKILL_METADATA_FIELD_MISSING",
        "SKILL_METADATA_ICON_ESCAPE",
        "SKILL_METADATA_ICON_MISSING",
        "SKILL_METADATA_INTERFACE_MISSING",
        "SKILL_METADATA_MISSING",
        "SKILL_METADATA_PROMPT_REFERENCE",
        "SKILL_METADATA_SHORT_DESCRIPTION_LENGTH",
        "SKILL_NAME_DIRECTORY_MISMATCH",
        "SKILL_NAME_DUPLICATE",
        "SKILL_NAME_INVALID",
        "SKILL_NAME_TOO_LONG",
        "SKILL_NONE_FOUND",
        "SKILL_NOT_REGISTERED",
        "SKILL_PACKAGE_DECLARATION_ESCAPE",
        "SKILL_PACKAGE_DECLARATION_MISSING",
        "SKILL_PACKAGE_DISCOVERY_ESCAPE",
        "SKILL_PACKAGE_ROUTE_DUPLICATE",
        "SKILL_PACKAGE_ROUTE_MISSING",
        "SKILL_PLACEHOLDER",
        "SKILL_REGISTRY_DUPLICATE",
        "SKILL_REGISTRY_ESCAPE",
        "SKILL_REGISTRY_MISSING",
        "SKILL_REGISTRY_TARGET_MISSING",
        "SOURCE_REVIEW_AUTHORITATIVE_SOURCE_INVALID",
        "SOURCE_REVIEW_AUTHORITATIVE_SOURCE_MISSING",
        "SOURCE_REVIEW_DATE_FUTURE",
        "SOURCE_REVIEW_DATE_INVALID",
        "SOURCE_REVIEW_EVIDENCE_DATE_MISMATCH",
        "SOURCE_REVIEW_EVIDENCE_ESCAPES_ROOT",
        "SOURCE_REVIEW_EVIDENCE_FILE_MISSING",
        "SOURCE_REVIEW_EVIDENCE_INVALID",
        "SOURCE_REVIEW_EVIDENCE_MISSING",
        "SOURCE_REVIEW_ID_DUPLICATE",
        "SOURCE_REVIEW_ID_INVALID",
        "SOURCE_REVIEW_INTERVAL_INVALID",
        "SOURCE_REVIEW_MATURITY_INVALID",
        "SOURCE_REVIEW_NOT_RUN",
        "SOURCE_REVIEW_RECORDS_MISSING",
        "SOURCE_REVIEW_RECORD_INVALID",
        "SOURCE_REVIEW_SCOPE_ESCAPES_ROOT",
        "SOURCE_REVIEW_SCOPE_INVALID",
        "SOURCE_REVIEW_SCOPE_MISSING",
        "SOURCE_REVIEW_STALE",
        "SPECIALIST_INDEPENDENCE_MISSING",
        "TEMPLATE_CHECKLIST_DECISION",
        "TEMPLATE_COLLECTION_FILE_MISSING",
        "TEMPLATE_EXAMPLE_JSON",
        "TEMPLATE_EXAMPLE_PLACEHOLDER",
        "TEMPLATE_EXAMPLE_SCHEMA",
        "TEMPLATE_EXAMPLE_SECRET",
        "TEMPLATE_EXAMPLE_UNFINISHED",
        "TEMPLATE_ID_DUPLICATE",
        "TEMPLATE_ID_MISSING",
        "TEMPLATE_JSON_INVALID",
        "TEMPLATE_NO_PLACEHOLDERS",
        "TEMPLATE_PACKAGE_FILE_MISSING",
        "TEMPLATE_PLACEHOLDER_INVALID",
        "TEMPLATE_PLACEHOLDER_UNDOCUMENTED",
        "TEMPLATE_README_THIN",
        "TEMPLATE_STABLE_PATH_MISSING",
        "TEMPORARY_ARTIFACT",
        "TOOL_COLLECTION_FILE_MISSING",
        "TOOL_COMPILE",
        "TOOL_CONTRACT_INVALID",
        "TOOL_DOC_ID_DUPLICATE",
        "TOOL_DOC_ID_MISSING",
        "TOOL_PACKAGE_FILE_MISSING",
        "TOOL_README_THIN",
        "TOOL_SHEBANG",
        "TOOL_STILL_PLANNED",
        "TOOL_TESTS_FAILED",
        "TOOL_TEST_COVERAGE",
        "UNIT_TESTS_FAILED",
        "VALIDATOR_FAILED",
        "WORKFLOW_ACTION_INVALID",
        "WORKFLOW_ACTION_NOT_PINNED",
        "WORKFLOW_DOCKER_NOT_PINNED",
        "WORKFLOW_RUNNER_FLOATING",
        "WORKFLOW_RUNNER_UNRESOLVED",
        "WORKFLOW_YAML_INVALID",
        "WORKFLOW_YAML_OUTSIDE_ROOT",
    }
)


def tool_sources() -> str:
    return "\n".join(
        path.read_text(encoding="utf-8")
        for path in sorted((REPO_ROOT / "tools").rglob("*.py"))
        if "tests" not in path.relative_to(REPO_ROOT / "tools").parts
    )


def behavior_test_sources() -> str:
    tests = REPO_ROOT / "tools" / "tests"
    return "\n".join(
        path.read_text(encoding="utf-8")
        for path in sorted(tests.glob("test_*.py"))
        if path.name != "test_published_finding_codes.py"
    )


class PublishedFindingCodeTests(unittest.TestCase):
    def test_every_published_code_is_still_emitted_by_a_tool(self):
        sources = tool_sources()
        for code in sorted(PUBLISHED_FINDING_CODES):
            with self.subTest(code=code):
                self.assertIn(f'"{code}"', sources, "published finding code removed from the tools")

    def test_every_published_code_has_a_behavior_test(self):
        # Each code must be asserted by a test that runs the real tool (tools/tests/test_finding_codes_*.py and peers).
        sources = behavior_test_sources()
        for code in sorted(PUBLISHED_FINDING_CODES):
            with self.subTest(code=code):
                self.assertIn(f'"{code}"', sources, "published finding code has no behavior test")

    def test_every_published_code_round_trips_through_shared_serialization(self):
        for code in sorted(PUBLISHED_FINDING_CODES):
            with self.subTest(code=code):
                finding_payload = Finding(
                    code=code,
                    message="serialization compatibility probe",
                    severity="error",
                    path="probe",
                    line=1,
                ).to_dict()
                self.assertEqual(finding_payload["code"], code)
                result_payload = ToolResult.from_findings(
                    tool="serialization-probe",
                    version="1.0.0",
                    findings=[Finding(code=code, message="serialization compatibility probe")],
                ).to_dict()
                self.assertEqual(result_payload["findings"][0]["code"], code)


if __name__ == "__main__":
    unittest.main()
