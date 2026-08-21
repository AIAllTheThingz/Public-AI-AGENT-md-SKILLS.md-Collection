from __future__ import annotations

import json
import unittest
from collections import Counter

import rc_finding_code_contracts_base as base
import test_rc_finding_code_contracts as semantic_active
import test_rc_zzzzzzzzzzzzzzzzz_function_defaults_and_constructor_provenance as _defaults_and_provenance  # noqa: F401


def _signature_counts(sources: list[tuple[str, str]]) -> dict[str, Counter[str]]:
    result: dict[str, Counter[str]] = {}
    for source_path, text in sources:
        for code, signatures in base.finding_semantic_signatures(text, source_path).items():
            result.setdefault(code, Counter()).update(signatures)
    return result


def _published_counts() -> dict[str, Counter[str]]:
    return _signature_counts(
        [
            (relative, base.git_source_at(base.CHECKPOINT_COMMIT, relative))
            for relative in base.published_python_paths()
        ]
    )


def _candidate_counts() -> dict[str, Counter[str]]:
    return _signature_counts(
        [
            (
                path.relative_to(base.REPO_ROOT).as_posix(),
                path.read_text(encoding="utf-8"),
            )
            for path in base.candidate_python_paths()
        ]
    )


def _project_counts(
    counts: Counter[str], code: str, contract: dict
) -> Counter[str]:
    projected: Counter[str] = Counter()
    for signature, count in counts.items():
        projected[
            base.project_approved_helper_changes(signature, code, contract)
        ] += count
    return projected


class ReleaseCandidateLiteralFindingMultiplicityTests(unittest.TestCase):
    def test_published_literal_finding_occurrence_counts_are_preserved(self) -> None:
        contract = json.loads(base.CHECKPOINT_PATH.read_text(encoding="utf-8"))
        published = _published_counts()
        candidate = _candidate_counts()
        approved = contract["approvedAdditivePublishedCodeContexts"]

        self.assertGreater(len(published), 20)
        for code, expected_counts in published.items():
            with self.subTest(code=code):
                behavior_bound = semantic_active._BEHAVIOR_BOUND_FINDING_CONTEXTS.get(code)
                if behavior_bound is not None:
                    # This code has a reviewed post-v0.10 implementation change and is
                    # intentionally protected by two-sided runtime coverage instead of
                    # exact v0.10 AST identity. Multiplicity still matters: the candidate
                    # must retain exactly one production occurrence at the reviewed
                    # source/function, so an accidental duplicate cannot hide behind the
                    # behavior-bound exemption.
                    current_counts = candidate.get(code, Counter())
                    self.assertEqual(
                        sum(current_counts.values()),
                        1,
                        f"behavior-bound public code {code} must retain exactly one literal occurrence",
                    )
                    signatures = [
                        signature
                        for signature, count in current_counts.items()
                        for _ in range(count)
                    ]
                    payload = json.loads(signatures[0])
                    self.assertEqual(payload["sourcePath"], behavior_bound["sourcePath"])
                    self.assertEqual(payload["function"], behavior_bound["function"])
                    continue

                expected = _project_counts(expected_counts, code, contract)
                current = _project_counts(candidate.get(code, Counter()), code, contract)

                for signature, count in expected.items():
                    self.assertEqual(
                        current[signature],
                        count,
                        f"published literal finding multiplicity changed for {code}",
                    )

                additional = current - expected
                if code in approved:
                    self.assertEqual(
                        sum(additional.values()),
                        approved[code]["count"],
                        f"approved additive literal contexts changed for {code}",
                    )
                    if code == "RELEASE_STATE_INVALID":
                        self.assertTrue(
                            all(
                                json.loads(signature)["function"] == "read_release_state"
                                for signature in additional
                            )
                        )
                else:
                    self.assertEqual(
                        additional,
                        Counter(),
                        f"unreviewed duplicate/additional literal finding for {code}",
                    )

    def test_duplicate_identical_literal_emission_changes_multiplicity(self) -> None:
        single = '''
from standards_tools import Finding

def run(findings):
    findings.append(Finding("PUBLIC_CODE", "message"))
'''
        duplicate = '''
from standards_tools import Finding

def run(findings):
    findings.append(Finding("PUBLIC_CODE", "message"))
    findings.append(Finding("PUBLIC_CODE", "message"))
'''
        single_counts = _signature_counts([("sample.py", single)])
        duplicate_counts = _signature_counts([("sample.py", duplicate)])

        self.assertEqual(sum(single_counts["PUBLIC_CODE"].values()), 1)
        self.assertEqual(sum(duplicate_counts["PUBLIC_CODE"].values()), 2)
        self.assertNotEqual(
            single_counts["PUBLIC_CODE"],
            duplicate_counts["PUBLIC_CODE"],
        )


if __name__ == "__main__":
    unittest.main()
