#!/usr/bin/env python3
"""Build deterministic release archives, release notes, checksums, and a release manifest."""

from __future__ import annotations

import argparse
import gzip
import hashlib
import io
import json
import shutil
import subprocess
import sys
import tarfile
import tempfile
import zipfile
from pathlib import Path
from typing import Any

from validate_release import read_release_state as validate_release_state

DEFAULT_ROOT = Path(__file__).resolve().parents[2]
BUILDER_VERSION = "1.0.0"
FIXED_ZIP_TIME = (1980, 1, 1, 0, 0, 0)
ARCHIVE_PREFIX = "Public-Access-Agents"
RELEASE_STATE_PATH = Path("releases/release-state.json")


def run_git(root: Path, *args: str) -> str:
    completed = subprocess.run(
        ["git", "-C", str(root), *args],
        text=True,
        capture_output=True,
        check=False,
    )
    if completed.returncode != 0:
        raise RuntimeError(completed.stderr.strip() or f"git {' '.join(args)} failed")
    return completed.stdout.strip()


def read_release_state(root: Path) -> dict[str, Any]:
    """Read release-state metadata through the canonical validator contract."""
    findings = []
    state = validate_release_state(root, findings)
    if findings:
        message = "; ".join(f"{item.code}: {item.message}" for item in findings)
        raise ValueError(f"Release-state metadata is invalid: {message}")
    return state


def ensure_clean_tracked_tree(root: Path) -> None:
    status = run_git(root, "status", "--porcelain", "--untracked-files=no")
    if status:
        raise RuntimeError(
            "Tracked working-tree changes are present. Commit or restore them before building "
            "release artifacts so sourceCommit matches the packaged content."
        )


def tracked_files(root: Path) -> list[Path]:
    raw = subprocess.run(
        ["git", "-C", str(root), "ls-files", "-z"],
        capture_output=True,
        check=False,
    )
    if raw.returncode != 0:
        raise RuntimeError("Unable to enumerate tracked repository files.")
    paths: list[Path] = []
    for item in raw.stdout.split(b"\0"):
        if not item:
            continue
        relative = Path(item.decode("utf-8", errors="surrogateescape"))
        if relative.parts and relative.parts[0] in {".git", "dist"}:
            continue
        path = root / relative
        if path.is_file():
            paths.append(path)
    return sorted(paths, key=lambda path: path.relative_to(root).as_posix())


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def artifact_record(path: Path, role: str) -> dict:
    return {
        "name": path.name,
        "role": role,
        "sha256": sha256(path),
        "sizeBytes": path.stat().st_size,
    }


def write_zip(root: Path, files: list[Path], output: Path, top: str) -> None:
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for path in files:
            relative = path.relative_to(root).as_posix()
            info = zipfile.ZipInfo(f"{top}/{relative}", date_time=FIXED_ZIP_TIME)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.create_system = 3
            info.external_attr = (0o644 & 0xFFFF) << 16
            archive.writestr(info, path.read_bytes())


def write_tar_gz(root: Path, files: list[Path], output: Path, top: str) -> None:
    tar_buffer = io.BytesIO()
    with tarfile.open(fileobj=tar_buffer, mode="w", format=tarfile.PAX_FORMAT) as archive:
        for path in files:
            relative = path.relative_to(root).as_posix()
            data = path.read_bytes()
            info = tarfile.TarInfo(f"{top}/{relative}")
            info.size = len(data)
            info.mtime = 0
            info.uid = 0
            info.gid = 0
            info.uname = ""
            info.gname = ""
            info.mode = 0o644
            archive.addfile(info, io.BytesIO(data))
    with output.open("wb") as handle:
        with gzip.GzipFile(filename="", mode="wb", fileobj=handle, mtime=0, compresslevel=9) as zipped:
            zipped.write(tar_buffer.getvalue())


def build(root: Path, output_dir: Path, tag: str | None, force: bool) -> dict:
    version = (root / "VERSION").read_text(encoding="utf-8").strip()
    expected_tag = f"v{version}"
    release_state = read_release_state(root)
    blocked_versions = set(release_state.get("preparedUnpublishedVersions", []))
    requested_tag_version = tag[1:] if tag and tag.startswith("v") else None

    if requested_tag_version in blocked_versions:
        raise ValueError(
            f"Release build is blocked for version {requested_tag_version}: it is explicitly recorded as prepared but unpublished. "
            "Select and prepare the intended forward release version before building publication artifacts."
        )

    if version in blocked_versions:
        raise ValueError(
            f"Release build is blocked for version {version}: it is explicitly recorded as prepared but unpublished. "
            "Select and prepare the intended forward release version before building publication artifacts."
        )
    next_intended_version = release_state.get("nextIntendedVersion")
    if isinstance(next_intended_version, str) and version != next_intended_version:
        raise ValueError(
            f"Release build version {version} does not match nextIntendedVersion {next_intended_version}."
        )
    if tag and tag != expected_tag:
        raise ValueError(f"Tag {tag!r} does not match VERSION; expected {expected_tag!r}.")

    ensure_clean_tracked_tree(root)

    release_notes = root / "releases" / f"{version}.md"
    migration_notes = root / "releases" / "migrations" / f"{version}.md"
    for path in (release_notes, migration_notes):
        if not path.is_file():
            raise FileNotFoundError(path)

    if output_dir.exists():
        if not force:
            raise FileExistsError(f"Output directory already exists: {output_dir}")
        shutil.rmtree(output_dir)
    output_dir.parent.mkdir(parents=True, exist_ok=True)

    files = tracked_files(root)
    commit = run_git(root, "rev-parse", "HEAD")
    top = f"{ARCHIVE_PREFIX}-{version}"

    with tempfile.TemporaryDirectory(prefix="release-", dir=output_dir.parent) as temp:
        staging = Path(temp) / "dist"
        staging.mkdir()

        zip_path = staging / f"{top}.zip"
        tar_path = staging / f"{top}.tar.gz"
        release_asset = staging / "RELEASE_NOTES.md"
        migration_asset = staging / "MIGRATION_NOTES.md"
        manifest_path = staging / "release-manifest.json"

        write_zip(root, files, zip_path, top)
        write_tar_gz(root, files, tar_path, top)
        release_asset.write_text(release_notes.read_text(encoding="utf-8"), encoding="utf-8")
        migration_asset.write_text(migration_notes.read_text(encoding="utf-8"), encoding="utf-8")

        artifacts = [
            artifact_record(zip_path, "source-archive-zip"),
            artifact_record(tar_path, "source-archive-tar-gz"),
            artifact_record(release_asset, "release-notes"),
            artifact_record(migration_asset, "migration-notes"),
        ]

        manifest = {
            "formatVersion": "1.0.0",
            "builderVersion": BUILDER_VERSION,
            "project": "Public-Access-Agents",
            "version": version,
            "tag": tag or expected_tag,
            "sourceCommit": commit,
            "archiveRoot": top,
            "trackedFiles": len(files),
            "artifacts": artifacts,
            "releaseNotes": release_asset.name,
            "migrationNotes": migration_asset.name,
            "checksums": "SHA256SUMS.txt",
        }
        manifest_path.write_text(
            json.dumps(manifest, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )

        checksum_targets = [zip_path, tar_path, release_asset, migration_asset, manifest_path]
        (staging / "SHA256SUMS.txt").write_text(
            "".join(
                f"{sha256(path)}  {path.name}\n"
                for path in sorted(checksum_targets, key=lambda value: value.name)
            ),
            encoding="utf-8",
        )
        shutil.move(str(staging), output_dir)

    return manifest


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=DEFAULT_ROOT)
    parser.add_argument("--output-dir", type=Path, default=Path("dist"))
    parser.add_argument("--tag")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args(argv)

    root = args.root.resolve()
    output = args.output_dir if args.output_dir.is_absolute() else root / args.output_dir
    try:
        manifest = build(root, output, args.tag, args.force)
    except (ValueError, FileNotFoundError, FileExistsError, RuntimeError) as exc:
        print(f"Release build failed: {exc}", file=sys.stderr)
        return 2

    print(json.dumps(manifest, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
