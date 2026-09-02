from __future__ import annotations

import copy
import json
import re

import rc_compatibility_gate_base as base

SEMVER_RE = re.compile(
    r"^(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)"
    r"(?:-([0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*))?"
    r"(?:\+[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*)?$"
)

_ORIGINAL_SCHEMA_CONTRACT_FINDINGS = base.schema_contract_findings


def _schema_is_unconstrained(schema: object) -> bool:
    """Return whether a schema accepts every instance value."""
    if schema is True:
        return True
    if not isinstance(schema, dict):
        return False
    return all(key in base.SCHEMA_ANNOTATION_KEYS for key in schema)


def schema_contract_findings(
    published: object,
    candidate: object,
    path: str = "$",
) -> list[str]:
    """Strengthen optional-property compatibility for previously open objects."""
    findings = _ORIGINAL_SCHEMA_CONTRACT_FINDINGS(published, candidate, path)
    if not isinstance(published, dict) or not isinstance(candidate, dict):
        return sorted(set(findings))

    candidate_properties = candidate.get("properties")
    if not isinstance(candidate_properties, dict):
        return sorted(set(findings))

    published_properties = published.get("properties")
    known_properties = (
        published_properties if isinstance(published_properties, dict) else {}
    )
    additional = published.get("additionalProperties", True)

    for name, candidate_property in candidate_properties.items():
        if name in known_properties:
            continue

        # A closed published object rejected this name entirely, so admitting a
        # new optional named property is a compatible extension. An open object
        # already accepted the name with its old additionalProperties semantics;
        # the newly named schema must not narrow those previously accepted values.
        if additional is False:
            continue
        if additional is True:
            if not _schema_is_unconstrained(candidate_property):
                findings.append(
                    f"SCHEMA_NEW_PROPERTY_NARROWS_OPEN_OBJECT:{path}.properties.{name}"
                )
            continue
        if isinstance(additional, dict):
            if _schema_is_unconstrained(candidate_property):
                continue
            if _ORIGINAL_SCHEMA_CONTRACT_FINDINGS(
                additional,
                candidate_property,
                f"{path}.additionalProperties->{name}",
            ):
                findings.append(
                    f"SCHEMA_NEW_PROPERTY_NARROWS_OPEN_OBJECT:{path}.properties.{name}"
                )
            continue

        findings.append(
            f"SCHEMA_NEW_PROPERTY_NARROWS_OPEN_OBJECT:{path}.properties.{name}"
        )

    return sorted(set(findings))


# The historical base remains independently readable; the discovered permanent
# gate uses the strengthened comparator, and the base comparator's recursive
# calls resolve through this binding as well.
base.schema_contract_findings = schema_contract_findings


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
        paths = [
            relative
            for relative in self.inventory["stableSchemaPaths"]
            if relative != "schemas/v2/completion-result.schema.json"
        ]
        self.assertEqual(len(paths), 12)
        self.assertIn(
            "schemas/v2/completion-result.schema.json",
            self.inventory["stableSchemaPaths"],
        )
        for relative in paths:
            with self.subTest(schema=relative):
                published = json.loads(
                    base.git_source_at(base.CHECKPOINT_COMMIT, relative)
                )
                candidate = json.loads(
                    (base.REPO_ROOT / relative).read_text(encoding="utf-8")
                )
                if relative == "schemas/completion-result.schema.json":
                    self.assertEqual(candidate["x-schemaVersion"], "2.0.0")
                    self.assertEqual(
                        candidate["x-versionedSchema"],
                        "v2/completion-result.schema.json",
                    )
                    continue
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

    def test_open_schema_object_rejects_narrowing_named_property(self):
        relative = "schemas/artifact-record.schema.json"
        published = json.loads(base.git_source_at(base.CHECKPOINT_COMMIT, relative))

        narrowed = copy.deepcopy(published)
        extensions = narrowed["properties"]["extensions"]
        self.assertIs(extensions["additionalProperties"], True)
        extensions["properties"] = {"vendorFlag": {"type": "boolean"}}
        findings = base.schema_contract_findings(published, narrowed)
        self.assertIn(
            "SCHEMA_NEW_PROPERTY_NARROWS_OPEN_OBJECT:$.properties.extensions.properties.vendorFlag",
            findings,
        )

        unconstrained = copy.deepcopy(published)
        unconstrained["properties"]["extensions"]["properties"] = {
            "vendorFlag": {"description": "Optional vendor extension annotation."}
        }
        self.assertEqual(
            base.schema_contract_findings(published, unconstrained),
            [],
            "annotation-only naming must not narrow a previously open extension key",
        )

    def test_closed_schema_object_allows_new_optional_property(self):
        relative = "schemas/project-manifest.schema.json"
        published = json.loads(base.git_source_at(base.CHECKPOINT_COMMIT, relative))
        self.assertIs(published["additionalProperties"], False)

        candidate = copy.deepcopy(published)
        candidate["properties"]["traceId"] = {"type": "string"}
        self.assertEqual(base.schema_contract_findings(published, candidate), [])


if __name__ == "__main__":
    import unittest

    unittest.main()
