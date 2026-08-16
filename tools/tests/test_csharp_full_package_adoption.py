from __future__ import annotations

import hashlib
import json
import re
import shutil
import tempfile
import unittest
from pathlib import Path, PurePosixPath, PureWindowsPath

from helpers import REPO_ROOT

PACKAGE_ROOT = REPO_ROOT / "languages" / "csharp"
MANIFEST_PATH = PACKAGE_ROOT / "MANIFEST.md"
HEX_SHA256 = re.compile(r"^[0-9a-f]{64}$")


def validated_manifest_relative_path(entry: str) -> Path:
    posix_path = PurePosixPath(entry)
    windows_path = PureWindowsPath(entry)
    if (
        not entry
        or posix_path.is_absolute()
        or windows_path.is_absolute()
        or windows_path.drive
        or ".." in posix_path.parts
        or "\\" in entry
        or not posix_path.parts
    ):
        raise AssertionError(f"C# package manifest contains unsafe required-file path: {entry!r}")
    return Path(*posix_path.parts)


def required_surface_paths() -> list[Path]:
    text = MANIFEST_PATH.read_text(encoding="utf-8")
    if "## Required files" not in text or "## Acceptance checks" not in text:
        raise AssertionError("C# package manifest is missing required surface sections")
    section = text.split("## Required files", 1)[1].split("## Acceptance checks", 1)[0]
    entries = re.findall(r"^- `([^`]+)`\s*$", section, flags=re.MULTILINE)
    if not entries:
        raise AssertionError("C# package manifest declares no required files")
    return [validated_manifest_relative_path(entry) for entry in dict.fromkeys(entries)]


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def bind_full_package_surface(destination: Path) -> list[dict[str, str]]:
    records: list[dict[str, str]] = []
    for relative in required_surface_paths():
        source = PACKAGE_ROOT / relative
        if not source.is_file():
            raise FileNotFoundError(f"Manifest-required C# package file is missing: {relative.as_posix()}")
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
        records.append({
            "path": f"languages/csharp/{relative.as_posix()}",
            "sha256": sha256_file(source),
        })
    (destination / "PACKAGE_SURFACE.json").write_text(
        json.dumps({"component": "languages/csharp", "files": records}, indent=2) + "\n",
        encoding="utf-8",
    )
    return records


def validate_bound_surface(destination: Path, records: list[dict[str, str]]) -> list[str]:
    findings: list[str] = []
    package_prefix = Path("languages/csharp")
    for record in records:
        relative = Path(record["path"]).relative_to(package_prefix)
        target = destination / relative
        if not target.is_file():
            findings.append(f"BOUND_SURFACE_MISSING:{record['path']}")
            continue
        if sha256_file(target) != record["sha256"]:
            findings.append(f"BOUND_SURFACE_HASH_MISMATCH:{record['path']}")
    return findings


class CSharpFullPackageAdoptionTests(unittest.TestCase):
    def test_manifest_required_paths_reject_package_escape(self):
        unsafe_entries = (
            "../README.md",
            "standards/../../README.md",
            "/tmp/escape.md",
            "C:/Windows/System32/escape.txt",
            r"C:\Windows\System32\escape.txt",
            r"standards\..\..\README.md",
        )
        for entry in unsafe_entries:
            with self.subTest(entry=entry):
                with self.assertRaises(AssertionError):
                    validated_manifest_relative_path(entry)

        self.assertEqual(
            validated_manifest_relative_path("standards/SECURITY_STANDARD.md"),
            Path("standards/SECURITY_STANDARD.md"),
        )

    def test_complete_csharp_package_surface_is_bound_and_hash_verified(self):
        required = {path.as_posix() for path in required_surface_paths()}
        self.assertTrue({
            "SKILL.md",
            "agents/openai.yaml",
            "AGENTS.md",
            "README.md",
            "MANIFEST.md",
            "examples/ADOPTION_EXAMPLE.md",
        }.issubset(required))
        self.assertTrue(any(path.startswith("standards/") for path in required))
        self.assertTrue(any(path.startswith("templates/") for path in required))

        with tempfile.TemporaryDirectory(dir=REPO_ROOT) as temp:
            destination = Path(temp) / "adopted-csharp-package"
            records = bind_full_package_surface(destination)
            recorded = {record["path"] for record in records}
            expected = {f"languages/csharp/{path}" for path in required}
            self.assertEqual(recorded, expected)
            self.assertEqual(validate_bound_surface(destination, records), [])
            for record in records:
                self.assertRegex(record["sha256"], HEX_SHA256)
            surface = json.loads((destination / "PACKAGE_SURFACE.json").read_text(encoding="utf-8"))
            self.assertEqual(surface["component"], "languages/csharp")
            self.assertEqual({item["path"] for item in surface["files"]}, expected)

    def test_complete_csharp_package_surface_detects_missing_and_tampered_content(self):
        with tempfile.TemporaryDirectory(dir=REPO_ROOT) as temp:
            destination = Path(temp) / "missing-surface"
            records = bind_full_package_surface(destination)
            missing_path = destination / "standards" / "SECURITY_STANDARD.md"
            self.assertTrue(missing_path.is_file())
            missing_path.unlink()
            self.assertIn(
                "BOUND_SURFACE_MISSING:languages/csharp/standards/SECURITY_STANDARD.md",
                validate_bound_surface(destination, records),
            )

        with tempfile.TemporaryDirectory(dir=REPO_ROOT) as temp:
            destination = Path(temp) / "tampered-surface"
            records = bind_full_package_surface(destination)
            tampered_path = destination / "templates" / "UNIT_TEST_TEMPLATE.cs"
            self.assertTrue(tampered_path.is_file())
            tampered_path.write_text(tampered_path.read_text(encoding="utf-8") + "\n// tampered\n", encoding="utf-8")
            self.assertIn(
                "BOUND_SURFACE_HASH_MISMATCH:languages/csharp/templates/UNIT_TEST_TEMPLATE.cs",
                validate_bound_surface(destination, records),
            )


if __name__ == "__main__":
    unittest.main()
