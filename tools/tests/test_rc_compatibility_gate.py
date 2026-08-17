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
        published = set(state["publishedVersions"])
        prepared = set(state["preparedUnpublishedVersions"])
        next_intended = state["nextIntendedVersion"]

        self.assertIn(base.CHECKPOINT, published)
        self.assertNotIn(base.CANDIDATE, prepared)
        self.assertNotIn(next_intended, published)
        self.assertNotIn(next_intended, prepared)

        if base.CANDIDATE in published:
            self.assertGreater(
                semver_key(current_version),
                semver_key(base.CANDIDATE),
                "after rc.1 publication VERSION must advance beyond the historical candidate",
            )
            self.assertGreater(
                semver_key(next_intended),
                semver_key(base.CANDIDATE),
                "after rc.1 publication nextIntendedVersion must advance beyond rc.1",
            )
        else:
            self.assertEqual(current_version, base.CANDIDATE)
            self.assertEqual(next_intended, base.CANDIDATE)

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
