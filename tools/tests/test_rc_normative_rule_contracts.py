from __future__ import annotations

import hashlib
import re

import rc_normative_rule_contracts_base as base

CSHARP_NORMATIVE_ROOT = base.CSHARP_NORMATIVE_ROOT
CSHARP_PROMOTION_EVIDENCE_COMMIT = base.CSHARP_PROMOTION_EVIDENCE_COMMIT
FRONTMATTER_ID_PATTERN = re.compile(r"^id:\s*(\S+)\s*$", re.MULTILINE)
LIST_ITEM_PATTERN = re.compile(r"^(?:[-*]|\d+\.)\s+(?P<text>.+)$")
NON_CONTRACT_SECTIONS = {"Purpose", "Evidence", "Examples", "References", "Rationale"}


def csharp_standard_paths_at(revision: str) -> list[str]:
    prefix = f"{CSHARP_NORMATIVE_ROOT}/"
    return sorted(
        path
        for path in base.git_output(
            "ls-tree", "-r", "--name-only", revision, CSHARP_NORMATIVE_ROOT
        ).splitlines()
        if path.startswith(prefix) and path.endswith("_STANDARD.md")
    )


def candidate_csharp_standard_paths() -> list[str]:
    root = base.REPO_ROOT / CSHARP_NORMATIVE_ROOT
    return sorted(
        path.relative_to(base.REPO_ROOT).as_posix()
        for path in root.glob("*_STANDARD.md")
        if path.is_file()
    )


def frontmatter_id(text: str) -> str:
    if not text.startswith("---\n"):
        raise AssertionError("stable C# standard is missing front matter")
    end = text.find("\n---\n", 4)
    if end < 0:
        raise AssertionError("stable C# standard has unterminated front matter")
    match = FRONTMATTER_ID_PATTERN.search(text[4:end])
    if match is None:
        raise AssertionError("stable C# standard is missing front-matter id")
    return match.group(1)


def markdown_body(text: str) -> str:
    if not text.startswith("---\n"):
        return text
    end = text.find("\n---\n", 4)
    return text if end < 0 else text[end + len("\n---\n") :]


def normalize_contract_text(text: str) -> str:
    return " ".join(text.split())


def extract_csharp_normative_contracts(text: str) -> set[str]:
    """Preserve normative blocks while allowing non-contract editorial/additive evolution."""

    contracts: set[str] = set()
    current_section = ""
    paragraph: list[str] = []
    in_code_fence = False

    def flush_paragraph() -> None:
        nonlocal paragraph
        if paragraph and current_section not in NON_CONTRACT_SECTIONS:
            statement = normalize_contract_text(" ".join(paragraph))
            if statement:
                contracts.add(f"{current_section}::{statement}")
        paragraph = []

    for raw_line in markdown_body(text).splitlines():
        stripped = raw_line.strip()
        if stripped.startswith("```"):
            flush_paragraph()
            in_code_fence = not in_code_fence
            continue
        if in_code_fence:
            continue
        if stripped.startswith("## "):
            flush_paragraph()
            current_section = stripped[3:].strip()
            continue
        if stripped.startswith("# "):
            flush_paragraph()
            continue
        if not stripped:
            flush_paragraph()
            continue
        list_match = LIST_ITEM_PATTERN.match(stripped)
        if list_match is not None:
            flush_paragraph()
            if current_section not in NON_CONTRACT_SECTIONS:
                statement = normalize_contract_text(list_match.group("text"))
                if statement:
                    contracts.add(f"{current_section}::{statement}")
            continue
        paragraph.append(stripped)

    flush_paragraph()
    return contracts


def csharp_standard_snapshot(text: str) -> dict[str, object]:
    return {"id": frontmatter_id(text), "contracts": extract_csharp_normative_contracts(text)}


def promoted_csharp_standard_contracts() -> dict[str, dict[str, object]]:
    return {
        path: csharp_standard_snapshot(base.git_source_at(CSHARP_PROMOTION_EVIDENCE_COMMIT, path))
        for path in csharp_standard_paths_at(CSHARP_PROMOTION_EVIDENCE_COMMIT)
    }


def candidate_csharp_standard_contracts() -> dict[str, dict[str, object]]:
    return {
        path: csharp_standard_snapshot((base.REPO_ROOT / path).read_text(encoding="utf-8"))
        for path in candidate_csharp_standard_paths()
    }


def csharp_standard_contract_findings(
    promoted: dict[str, dict[str, object]],
    candidate: dict[str, dict[str, object]],
) -> list[str]:
    findings: list[str] = []
    for path, expected in promoted.items():
        actual = candidate.get(path)
        if actual is None:
            findings.append(f"MISSING_CSHARP_STANDARD:{path}")
            continue
        if actual["id"] != expected["id"]:
            findings.append(f"CHANGED_CSHARP_STANDARD_ID:{path}")
        for statement in sorted(set(expected["contracts"]) - set(actual["contracts"])):
            digest = hashlib.sha256(statement.encode("utf-8")).hexdigest()[:12]
            findings.append(f"MISSING_CSHARP_NORMATIVE_CONTRACT:{path}:{digest}")
    return sorted(findings)


class ReleaseCandidateNormativeRuleContractTests(base.ReleaseCandidateNormativeRuleContractTests):
    def test_full_csharp_normative_standards_match_promotion_evidence_candidate(self):
        """Override the former whole-tree equality with semantic promoted-contract preservation."""

        promoted = promoted_csharp_standard_contracts()
        candidate = candidate_csharp_standard_contracts()
        self.assertGreaterEqual(len(promoted), 8)
        self.assertGreater(sum(len(set(item["contracts"])) for item in promoted.values()), 50)
        security = promoted[f"{CSHARP_NORMATIVE_ROOT}/SECURITY_STANDARD.md"]
        self.assertEqual(security["id"], "CSHARP-SECURITY-001")
        self.assertEqual(csharp_standard_contract_findings(promoted, candidate), [])

    def test_csharp_contract_gate_allows_editorial_and_additive_evolution(self):
        promoted_text = '''
---
id: CSHARP-SAMPLE-001
title: Sample
version: 0.1.0
status: stable
---
# Sample
## Purpose
Original explanatory purpose text.
## Requirements
- Preserve this promoted requirement.
## Evidence
Original evidence guidance.
'''.lstrip()
        compatible_text = promoted_text.replace(
            "Original explanatory purpose text.", "Corrected explanatory purpose text."
        ).replace(
            "Original evidence guidance.", "Improved evidence guidance."
        ).replace(
            "- Preserve this promoted requirement.",
            "- Preserve this promoted requirement.\n- Add a new optional compatible requirement.",
        )
        promoted = {"sample_STANDARD.md": csharp_standard_snapshot(promoted_text)}
        compatible = {"sample_STANDARD.md": csharp_standard_snapshot(compatible_text)}
        self.assertEqual(csharp_standard_contract_findings(promoted, compatible), [])

        changed = {
            "sample_STANDARD.md": csharp_standard_snapshot(
                compatible_text.replace(
                    "Preserve this promoted requirement.", "Weaken this promoted requirement."
                )
            )
        }
        self.assertTrue(
            any(
                finding.startswith("MISSING_CSHARP_NORMATIVE_CONTRACT:sample_STANDARD.md:")
                for finding in csharp_standard_contract_findings(promoted, changed)
            )
        )

        changed_id = {
            "sample_STANDARD.md": csharp_standard_snapshot(
                compatible_text.replace("CSHARP-SAMPLE-001", "CSHARP-SAMPLE-002")
            )
        }
        self.assertIn(
            "CHANGED_CSHARP_STANDARD_ID:sample_STANDARD.md",
            csharp_standard_contract_findings(promoted, changed_id),
        )
