from __future__ import annotations

import hashlib
import json
import subprocess
import unittest

from helpers import REPO_ROOT, require_git_history


CHECKPOINT_PATH = REPO_ROOT / "releases/compatibility/0.10.0-checkpoint.json"
LEGAL_STABLE_ROOT_PATHS = ("LICENSE", "NOTICE")
CODEOWNERS_PATH = ".github/CODEOWNERS"


def git_source_at(commit: str, relative: str) -> str:
    completed = subprocess.run(
        ["git", "-C", str(REPO_ROOT), "show", f"{commit}:{relative}"],
        text=True,
        encoding="utf-8",
        capture_output=True,
        check=False,
    )
    if completed.returncode != 0:
        raise AssertionError(completed.stderr.strip() or "git show failed")
    return completed.stdout


def normalize_legal_text(text: str) -> str:
    """Normalize transport-only newline differences, not legal wording."""
    return text.replace("\r\n", "\n").replace("\r", "\n")


def legal_contract(text: str) -> str:
    return hashlib.sha256(
        normalize_legal_text(text).encode("utf-8")
    ).hexdigest()


def legal_contract_findings(
    source_path: str,
    published_text: str,
    candidate_text: str,
) -> list[str]:
    if legal_contract(published_text) == legal_contract(candidate_text):
        return []
    return [f"STABLE_LEGAL_CONTRACT_CHANGED:{source_path}"]


def codeowners_routes(text: str) -> tuple[tuple[str, tuple[str, ...]], ...]:
    routes: list[tuple[str, tuple[str, ...]]] = []
    for raw in text.splitlines():
        stripped = raw.strip()
        if not stripped or stripped.startswith("#"):
            continue
        parts = stripped.split()
        if len(parts) < 2:
            continue
        routes.append((parts[0], tuple(parts[1:])))
    return tuple(routes)


class ReleaseCandidateStableRootContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.checkpoint = json.loads(CHECKPOINT_PATH.read_text(encoding="utf-8"))
        cls.source_commit = cls.checkpoint["sourceCommit"]
        cls.stable_roots = set(cls.checkpoint["stablePathGroups"]["root"])

    def setUp(self) -> None:
        require_git_history(self.source_commit)

    def test_published_non_markdown_legal_roots_are_explicitly_protected(self) -> None:
        self.assertTrue(set(LEGAL_STABLE_ROOT_PATHS).issubset(self.stable_roots))

        for source_path in LEGAL_STABLE_ROOT_PATHS:
            with self.subTest(path=source_path):
                published = git_source_at(self.source_commit, source_path)
                candidate_path = REPO_ROOT / source_path
                self.assertTrue(candidate_path.is_file())
                candidate = candidate_path.read_text(encoding="utf-8")
                self.assertEqual(
                    legal_contract_findings(source_path, published, candidate),
                    [],
                    (
                        f"{source_path} is a published stable legal contract; "
                        "legal-term changes require an explicit compatibility migration/checkpoint, "
                        "not an in-place semantic drift"
                    ),
                )

    def test_incompatible_license_restriction_is_detected(self) -> None:
        published = git_source_at(self.source_commit, "LICENSE")
        mutated = (
            published
            + "\nAdditional restriction: redistribution is prohibited without separate approval.\n"
        )
        self.assertEqual(
            legal_contract_findings("LICENSE", published, mutated),
            ["STABLE_LEGAL_CONTRACT_CHANGED:LICENSE"],
        )

    def test_notice_legal_wording_drift_is_detected(self) -> None:
        published = git_source_at(self.source_commit, "NOTICE")
        mutated = published.replace(
            "Apache License, Version 2.0",
            "a proprietary license",
            1,
        )
        self.assertEqual(
            legal_contract_findings("NOTICE", published, mutated),
            ["STABLE_LEGAL_CONTRACT_CHANGED:NOTICE"],
        )

    def test_all_published_codeowners_routes_are_preserved_semantically(self) -> None:
        self.assertIn(CODEOWNERS_PATH, self.stable_roots)
        published = codeowners_routes(git_source_at(self.source_commit, CODEOWNERS_PATH))
        candidate = codeowners_routes((REPO_ROOT / CODEOWNERS_PATH).read_text(encoding="utf-8"))
        self.assertGreater(len(published), 20)
        self.assertEqual(
            candidate,
            published,
            "stable CODEOWNERS patterns, owners, or precedence changed",
        )

    def test_codeowners_owner_change_is_detected_but_comments_are_editable(self) -> None:
        published_text = git_source_at(self.source_commit, CODEOWNERS_PATH)
        published = codeowners_routes(published_text)

        changed = published_text.replace(
            "/languages/ @AIAllTheThingz",
            "/languages/ @different-owner",
            1,
        )
        self.assertNotEqual(codeowners_routes(changed), published)

        comment_only = "# editorial comment\n" + published_text
        self.assertEqual(codeowners_routes(comment_only), published)


class LegalContractNormalizationTests(unittest.TestCase):
    def test_newline_transport_differences_do_not_change_legal_contract(self) -> None:
        sample = "Line one\nLine two\n"
        self.assertEqual(
            legal_contract(sample),
            legal_contract(sample.replace("\n", "\r\n")),
        )


if __name__ == "__main__":
    unittest.main()
