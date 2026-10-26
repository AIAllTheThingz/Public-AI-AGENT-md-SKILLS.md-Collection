from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path

from helpers import json_result, run_tool
from test_validate_skills import manifest, skill, write

TOOL = "tools/validate-skills/validate_skills.py"
VALID_METADATA = "interface:\n  display_name: Sample\n  short_description: Sample skill for fictitious checks\n  default_prompt: Use $sample now.\n"


def link_dir(link: Path, target: Path) -> None:
    try:
        link.symlink_to(target, target_is_directory=True)
    except OSError as exc:
        if os.name != "nt":
            raise unittest.SkipTest(f"symlinks unavailable in test environment: {exc}")
        import _winapi

        # Junctions need no Windows symlink privilege and resolve like directory symlinks.
        _winapi.CreateJunction(str(target), str(link))


def registered(root: Path, content: str, name: str = "sample") -> None:
    write(root, f"{name}/SKILL.md", content)
    write(root, "MANIFEST.md", manifest(f"{name}/SKILL.md"))


def file_escape(root: Path, outside: Path) -> None:
    write(outside, "SKILL.md", skill("linked"))
    write(root, "MANIFEST.md", manifest())
    link_dir(root / "linked", outside)


def metadata_escape(root: Path, outside: Path) -> None:
    registered(root, skill("sample"))
    write(outside, "openai.yaml", VALID_METADATA)
    link_dir(root / "sample" / "agents", outside)


def discovery_escape(root: Path, outside: Path) -> None:
    registered(root, skill("sample"))
    write(outside, "AGENTS.md", "# Outside\n")
    write(outside, "README.md", "# Outside\n")
    link_dir(root / "sample" / "pkg", outside)


def declared(raw_path: str):
    def build(root: Path, outside: Path) -> None:
        registered(root, skill("sample"))
        write(root, "sample/MANIFEST.md", f"# Sample\n\n## Complete packages\n\n- `{raw_path}`\n")
    return build


def metadata(content: str):
    def build(root: Path, outside: Path) -> None:
        registered(root, skill("sample"))
        write(root, "sample/agents/openai.yaml", content)
    return build


def registry(content: str | None):
    def build(root: Path, outside: Path) -> None:
        write(root, "sample/SKILL.md", skill("sample"))
        if content is not None:
            write(root, "MANIFEST.md", content)
    return build


DESCRIPTION = "description: Route fictitious sample work. Use when Codex must apply sample standards."
CASES = {
    "SKILL_BODY_MISSING": lambda root, outside: registered(root, f"---\nname: sample\n{DESCRIPTION}\n---\n"),
    "SKILL_BODY_TITLE_MISSING": lambda root, outside: registered(root, skill("sample", body="No heading here.\n")),
    "SKILL_DESCRIPTION_TOO_LONG": lambda root, outside: registered(root, skill("sample", description="Use when " + "x" * 1100)),
    "SKILL_DESCRIPTION_WORDY": lambda root, outside: registered(root, skill("sample", description="Use when " + "word " * 101)),
    "SKILL_FILE_ESCAPE": file_escape,
    "SKILL_FRONTMATTER_FIELD_DUPLICATE": lambda root, outside: registered(root, f"---\nname: sample\nname: sample\n{DESCRIPTION}\n---\n\n# Sample\n"),
    "SKILL_FRONTMATTER_FIELD_MISSING": lambda root, outside: registered(root, "---\nname: sample\n---\n\n# Sample\n"),
    "SKILL_FRONTMATTER_INVALID": lambda root, outside: registered(root, "---\nname: sample\ndescription: |\n---\n\n# Sample\n"),
    "SKILL_METADATA_ESCAPE": metadata_escape,
    "SKILL_METADATA_FIELD_MISSING": metadata("interface:\n  display_name: Sample\n"),
    "SKILL_METADATA_ICON_MISSING": metadata(VALID_METADATA + "  icon_small: missing.png\n"),
    "SKILL_METADATA_INTERFACE_MISSING": metadata("display_name: Sample\n"),
    "SKILL_NAME_TOO_LONG": lambda root, outside: registered(root, skill("a" * 65), name="a" * 65),
    "SKILL_NONE_FOUND": lambda root, outside: write(root, "MANIFEST.md", manifest()),
    "SKILL_PACKAGE_DECLARATION_ESCAPE": declared("../outside"),
    "SKILL_PACKAGE_DECLARATION_MISSING": declared("absent"),
    "SKILL_PACKAGE_DISCOVERY_ESCAPE": discovery_escape,
    "SKILL_REGISTRY_DUPLICATE": registry(manifest("sample/SKILL.md", "sample/SKILL.md")),
    "SKILL_REGISTRY_ESCAPE": registry(manifest("sample/SKILL.md", "../outside/SKILL.md")),
    "SKILL_REGISTRY_MISSING": registry(None),
}


class ValidateSkillsFindingCodeTests(unittest.TestCase):
    def test_each_finding_code_is_emitted(self):
        for code, build in CASES.items():
            with self.subTest(code=code), tempfile.TemporaryDirectory() as directory:
                root = Path(directory) / "repo"
                root.mkdir()
                build(root, Path(directory) / "outside")
                completed = run_tool(TOOL, "--format", "json", root=root)
                codes = {item["code"] for item in json_result(completed)["findings"]}
                self.assertIn(code, codes, completed.stdout + completed.stderr)

    def test_valid_fixture_emits_none_of_the_codes(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            registered(root, skill("sample"))
            write(root, "sample/agents/openai.yaml", VALID_METADATA)
            completed = run_tool(TOOL, "--format", "json", root=root)
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
        self.assertEqual(json_result(completed)["findings"], [])


if __name__ == "__main__":
    unittest.main()
