from __future__ import annotations

import unittest
from collections import Counter

import test_pr71_final_regressions as root_final
import test_rc_unnumbered_governance_semantics as unnumbered

# The terminal closure extends unnumbered governance to stable root policies.
# Reuse the already-reviewed root projection from test_pr71_final_regressions
# rather than duplicating it: that projection derives normative roots from the
# authenticated stable-root checkpoint and removes only explicitly forward-
# moving release-state narrative while retaining durable policy obligations.
terminal = __import__(
    next(
        path.stem
        for path in sorted(root_final.REPO_ROOT.joinpath("tools", "tests").glob("test_rc_*_pr71_terminal_closure.py"))
    )
)

_governance_only_published = terminal._previous_published_contracts
_governance_only_candidate = terminal._previous_candidate_contracts


def _published_contracts_with_reviewed_root_projection() -> Counter[tuple[str, str, str]]:
    contracts = Counter(_governance_only_published())
    contracts.update(root_final._root_governance_contracts_at_checkpoint())
    return contracts


def _candidate_contracts_with_reviewed_root_projection() -> Counter[tuple[str, str, str]]:
    contracts = Counter(_governance_only_candidate())
    contracts.update(root_final._candidate_root_governance_contracts())
    return contracts


unnumbered.published_contracts = _published_contracts_with_reviewed_root_projection
unnumbered.candidate_contracts = _candidate_contracts_with_reviewed_root_projection


class ReleaseCandidateRootGovernanceProjectionReuseTests(unittest.TestCase):
    def test_current_governance_contracts_remain_compatible(self) -> None:
        self.assertEqual(
            unnumbered.unnumbered_contract_findings(
                unnumbered.published_contracts(),
                unnumbered.candidate_contracts(),
            ),
            [],
        )

    def test_forward_release_narrative_stays_mutable(self) -> None:
        checkpoint = unnumbered.base.git_source_at(
            unnumbered.base.CHECKPOINT_COMMIT,
            "RELEASE_POLICY.md",
        )
        raw = unnumbered.extract_unnumbered_governance_contracts(
            checkpoint,
            "RELEASE_POLICY.md",
        )
        stable = root_final._stable_root_contracts(
            checkpoint,
            "RELEASE_POLICY.md",
        )
        historical = [
            contract
            for contract in raw
            if contract[0] == "RELEASE_POLICY.md"
            and contract[1] == "pre-1.0 policy"
            and contract[2].startswith("The repository originally prepared ")
        ]
        self.assertEqual(len(historical), 1)
        self.assertNotIn(historical[0], stable)

    def test_reported_root_policies_are_in_reviewed_projection(self) -> None:
        self.assertTrue(
            {
                "AGENTS.md",
                "MAINTAINERS.md",
                "RELEASE_POLICY.md",
                "MATURITY_POLICY.md",
                "SECURITY.md",
            }.issubset(set(root_final._published_normative_stable_root_paths()))
        )


if __name__ == "__main__":
    unittest.main()
