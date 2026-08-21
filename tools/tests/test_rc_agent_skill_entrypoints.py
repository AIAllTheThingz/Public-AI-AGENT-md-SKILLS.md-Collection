from __future__ import annotations

import json
import re
import subprocess
import unittest

from helpers import REPO_ROOT, sha256_utf8_text_file

CHECKPOINT_COMMIT = "83c73f3ab9a049ff2321d463164fcf98fb453a9c"
CHECKPOINT_PATH = REPO_ROOT / "releases" / "compatibility" / "0.10.0-agent-skill-entrypoints.json"
CHECKPOINT_SHA256 = "635e34c53f967d1b0bff9602037f7c716650cbf815f7aae3efc6f15c936921fb"
_LINK_PATTERN = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")
_TABLE_SEPARATOR = re.compile(r"^:?-{3,}:?$")
_HTML_COMMENT_PATTERN = re.compile(r"<!--.*?-->", re.DOTALL)


def git_source_at(commit: str, relative: str) -> str:
    completed = subprocess.run(
        ["git", "-C", str(REPO_ROOT), "show", f"{commit}:{relative}"],
        text=True,
        capture_output=True,
        check=False,
    )
    if completed.returncode != 0:
        raise AssertionError(completed.stderr.strip() or f"cannot resolve {commit}:{relative}")
    return completed.stdout


def git_object_sha(commit: str, relative: str) -> str:
    completed = subprocess.run(
        ["git", "-C", str(REPO_ROOT), "rev-parse", f"{commit}:{relative}"],
        text=True,
        capture_output=True,
        check=False,
    )
    if completed.returncode != 0:
        raise AssertionError(completed.stderr.strip() or f"cannot resolve {commit}:{relative}")
    return completed.stdout.strip()


def visible_markdown(text: str) -> str:
    return _HTML_COMMENT_PATTERN.sub("", text)


def agent_skill_entry_paths(manifest_text: str) -> set[str]:
    manifest_text = visible_markdown(manifest_text)
    section = manifest_text.split("## Agent skill entry points", 1)[1].split(
        "## Repository licensing", 1
    )[0]
    return set(re.findall(r"^- `([^`]+)`\s*$", section, flags=re.MULTILINE))


def missing_skill_entries(expected: set[str], observed: set[str]) -> list[str]:
    return sorted(expected - observed)


def _normalize_cell(value: str) -> str:
    return re.sub(r"\s+", " ", value.strip())


def _table_cells(line: str) -> list[str] | None:
    stripped = line.strip()
    if not (stripped.startswith("|") and stripped.endswith("|")):
        return None
    return [_normalize_cell(cell) for cell in stripped[1:-1].split("|")]


def _is_separator_row(cells: list[str] | None) -> bool:
    return bool(cells) and all(
        _TABLE_SEPARATOR.fullmatch(cell.replace(" ", "")) is not None
        for cell in cells
    )


def skill_routing_contract(skill_text: str) -> set[str]:
    """Extract stable evidence -> package routing rows from visible router tables."""

    lines = visible_markdown(skill_text).splitlines()
    contracts: set[str] = set()
    index = 0

    while index + 1 < len(lines):
        header = _table_cells(lines[index])
        separator = _table_cells(lines[index + 1])
        if (
            header is None
            or not _is_separator_row(separator)
            or not any("evidence" in cell.casefold() for cell in header)
            or not any("package" in cell.casefold() for cell in header)
        ):
            index += 1
            continue

        row_index = index + 2
        while row_index < len(lines):
            row = _table_cells(lines[row_index])
            if row is None:
                break
            if len(row) != len(header):
                row_index += 1
                continue

            targets = [
                {
                    "label": _normalize_cell(label),
                    "target": _normalize_cell(target),
                }
                for cell in row[1:]
                for label, target in _LINK_PATTERN.findall(cell)
            ]
            if targets:
                contracts.add(
                    json.dumps(
                        {
                            "evidence": row[0],
                            "targets": targets,
                        },
                        sort_keys=True,
                    )
                )
            row_index += 1

        index = row_index

    return contracts


def missing_routing_contracts(expected: set[str], observed: set[str]) -> list[str]:
    return sorted(expected - observed)


class ReleaseCandidateAgentSkillEntryPointTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.checkpoint_bytes = CHECKPOINT_PATH.read_bytes()
        cls.checkpoint = json.loads(cls.checkpoint_bytes.decode("utf-8"))

    def test_checkpoint_is_immutable_and_derived_from_published_manifest(self):
        self.assertEqual(sha256_utf8_text_file(CHECKPOINT_PATH), CHECKPOINT_SHA256)
        self.assertEqual(self.checkpoint["releaseVersion"], "0.10.0")
        self.assertEqual(self.checkpoint["tag"], "v0.10.0")
        self.assertEqual(self.checkpoint["sourceCommit"], CHECKPOINT_COMMIT)

        source_manifest = self.checkpoint["sourceManifest"]
        self.assertEqual(source_manifest["path"], "MANIFEST.md")
        self.assertEqual(
            git_object_sha(CHECKPOINT_COMMIT, source_manifest["path"]),
            source_manifest["blobSha"],
        )

        published = agent_skill_entry_paths(
            git_source_at(CHECKPOINT_COMMIT, source_manifest["path"])
        )
        self.assertEqual(
            set(self.checkpoint["stableAgentSkillEntryPaths"]),
            published,
        )

    def test_candidate_preserves_every_published_agent_skill_entry_path(self):
        expected = set(self.checkpoint["stableAgentSkillEntryPaths"])
        current_manifest = (REPO_ROOT / "MANIFEST.md").read_text(encoding="utf-8")
        observed = agent_skill_entry_paths(current_manifest)
        self.assertEqual(missing_skill_entries(expected, observed), [])

        for relative in expected:
            with self.subTest(path=relative):
                self.assertTrue((REPO_ROOT / relative).is_file(), relative)

    def test_candidate_preserves_published_router_trigger_and_target_semantics(self):
        router_count = 0
        for relative in self.checkpoint["stableAgentSkillEntryPaths"]:
            published = skill_routing_contract(
                git_source_at(CHECKPOINT_COMMIT, relative)
            )
            if not published:
                continue
            router_count += 1
            candidate = skill_routing_contract(
                (REPO_ROOT / relative).read_text(encoding="utf-8")
            )
            with self.subTest(path=relative):
                self.assertEqual(
                    missing_routing_contracts(published, candidate),
                    [],
                    f"published skill routing semantics changed for {relative}",
                )

        # Six published collection routers select packages by evidence. The
        # seventh stable entry point is the direct C# skill, not a router.
        self.assertEqual(router_count, 6)

    def test_candidate_comparison_detects_removed_language_skill_entry(self):
        expected = set(self.checkpoint["stableAgentSkillEntryPaths"])
        observed = set(expected)
        observed.remove("languages/SKILL.md")
        self.assertEqual(
            missing_skill_entries(expected, observed),
            ["languages/SKILL.md"],
        )

    def test_language_router_detects_trigger_mapping_change(self):
        published_text = git_source_at(CHECKPOINT_COMMIT, "languages/SKILL.md")
        published = skill_routing_contract(published_text)
        changed = published_text.replace(
            "| `.py`, `pyproject.toml`, Python packages, services, CLIs, or automation |",
            "| `.rb`, `pyproject.toml`, Python packages, services, CLIs, or automation |",
            1,
        )
        self.assertNotEqual(changed, published_text)
        self.assertNotEqual(skill_routing_contract(changed), published)
        self.assertTrue(
            missing_routing_contracts(published, skill_routing_contract(changed))
        )

    def test_language_router_detects_package_target_change(self):
        published_text = git_source_at(CHECKPOINT_COMMIT, "languages/SKILL.md")
        published = skill_routing_contract(published_text)
        changed = published_text.replace(
            "[`python/`](python/)",
            "[`python/`](ruby/)",
            1,
        )
        self.assertNotEqual(changed, published_text)
        self.assertNotEqual(skill_routing_contract(changed), published)
        self.assertTrue(
            missing_routing_contracts(published, skill_routing_contract(changed))
        )

    def test_commented_out_router_table_does_not_count_as_routing(self):
        published_text = """
| Evidence | Package |
|---|---|
| `.py` | [`python/`](python/) |
"""
        candidate_text = """
<!--
| Evidence | Package |
|---|---|
| `.py` | [`python/`](python/) |
-->
"""
        published = skill_routing_contract(published_text)
        candidate = skill_routing_contract(candidate_text)
        self.assertEqual(len(published), 1)
        self.assertEqual(candidate, set())
        self.assertTrue(missing_routing_contracts(published, candidate))


if __name__ == "__main__":
    unittest.main()
