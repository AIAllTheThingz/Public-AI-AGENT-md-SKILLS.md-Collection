from __future__ import annotations

import json
import re

import rc_compatibility_gate_base as base

SEMVER_RE = re.compile(
    r"^(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)"
    r"(?:-([0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*))?"
    r"(?:\+[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*)?$"
)


def semver_key(value: str) -> tuple:
    match = SEMVER_RE.fullmatch(value)
    if match is None:
        raise AssertionError(f"invalid Semantic Version in RC history test: {value!r}")
    major, minor, patch = (int(match.group(index)) for index in (1, 2, 3))
    prerelease = match.group(4)
    if prerelease is None:
        return (major, minor, patch, 1, ())
    parts = []
    for token in prerelease.split("."):
        parts.append((0, int(token)) if token.isdigit() else (1, token))
    return (major, minor, patch, 0, tuple(parts))


def assert_candidate_state_is_forward_only(
    test_case,
    current_version: str,
    state: dict,
) -> None:
    published = set(state["publishedVersions"])
    prepared = set(state["preparedUnpublishedVersions"])
    next_intended = state["nextIntendedVersion"]

    test_case.assertIn(base.CHECKPOINT, published)
    test_case.assertNotIn(next_intended, published)
    test_case.assertNotIn(next_intended, prepared)

    candidate_published = base.CANDIDATE in published
    candidate_abandoned = base.CANDIDATE in prepared
    test_case.assertFalse(
        candidate_published and candidate_abandoned,
        "a historical RC cannot be both published and prepared-unpublished",
    )

    if candidate_published or candidate_abandoned:
        transition = "publication" if candidate_published else "explicit abandonment"
        test_case.assertGreater(
            semver_key(current_version),
            semver_key(base.CANDIDATE),
            f"after rc.1 {transition} VERSION must advance beyond the historical candidate",
        )
        test_case.assertGreater(
            semver_key(next_intended),
            semver_key(base.CANDIDATE),
            f"after rc.1 {transition} nextIntendedVersion must advance beyond rc.1",
        )
        return

    test_case.assertEqual(current_version, base.CANDIDATE)
    test_case.assertEqual(next_intended, base.CANDIDATE)


class ReleaseCandidateCompatibilityGateTests(
    base.ReleaseCandidateCompatibilityGateTests
):
    def test_candidate_and_release_state_are_forward_only(self):
        current_version = (base.REPO_ROOT / "VERSION").read_text(
            encoding="utf-8"
        ).strip()
        state = json.loads(
            (base.REPO_ROOT / "releases" / "release-state.json").read_text(
                encoding="utf-8"
            )
        )
        assert_candidate_state_is_forward_only(self, current_version, state)

    def test_candidate_state_allows_explicit_abandonment(self):
        state = {
            "publishedVersions": [base.CHECKPOINT],
            "preparedUnpublishedVersions": [base.CANDIDATE],
            "nextIntendedVersion": "1.0.0-rc.2",
        }
        assert_candidate_state_is_forward_only(self, "1.0.0-rc.2", state)

    def test_release_validator_accepts_rc_tag_contract(self):
        current_version = (base.REPO_ROOT / "VERSION").read_text(
            encoding="utf-8"
        ).strip()
        state = json.loads(
            (base.REPO_ROOT / "releases" / "release-state.json").read_text(
                encoding="utf-8"
            )
        )

        # This is a preparation-state runtime assertion, not a permanent demand
        # that every future repository version continue accepting the historical
        # rc.1 tag. Once rc.1 is published or explicitly abandoned, the forward-
        # only state test above owns the historical transition and this transient
        # runtime exercise is complete.
        if current_version != base.CANDIDATE:
            historical = set(state["publishedVersions"]) | set(
                state["preparedUnpublishedVersions"]
            )
            self.assertIn(
                base.CANDIDATE,
                historical,
                "rc.1 may stop being the current tag contract only after publication or explicit abandonment",
            )
            self.assertGreater(semver_key(current_version), semver_key(base.CANDIDATE))
            return

        completed = base.run_tool(
            "tools/release/validate_release.py",
            "--format",
            "json",
            "--tag",
            f"v{base.CANDIDATE}",
        )
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
        payload = base.json_result(completed)
        self.assertEqual(payload["status"], "passed")
        self.assertEqual(payload["summary"]["repositoryVersion"], base.CANDIDATE)
        self.assertEqual(payload["summary"]["expectedTag"], f"v{base.CANDIDATE}")

    def test_every_published_stable_schema_contract_remains_compatible(self):
        paths = self.inventory["stableSchemaPaths"]
        self.assertEqual(len(paths), 12)
        for relative in paths:
            with self.subTest(schema=relative):
                published = json.loads(
                    base.git_source_at(base.CHECKPOINT_COMMIT, relative)
                )
                candidate = json.loads(
                    (base.REPO_ROOT / relative).read_text(encoding="utf-8")
                )
                self.assertEqual(
                    base.schema_contract_findings(published, candidate),
                    [],
                    f"published stable schema contract changed for {relative}",
                )

    def test_stable_schema_gate_detects_required_and_type_breaks(self):
        relative = "schemas/project-manifest.schema.json"
        published = json.loads(base.git_source_at(base.CHECKPOINT_COMMIT, relative))

        removed_required = json.loads(json.dumps(published))
        removed_required["required"].remove("name")
        self.assertIn(
            "SCHEMA_REQUIRED_CHANGED:$",
            base.schema_contract_findings(published, removed_required),
        )

        changed_type = json.loads(json.dumps(published))
        changed_type["properties"]["name"]["type"] = "integer"
        self.assertIn(
            "SCHEMA_CONTRACT_CHANGED:$.properties.name:type",
            base.schema_contract_findings(published, changed_type),
        )


if __name__ == "__main__":
    import unittest

    unittest.main()
