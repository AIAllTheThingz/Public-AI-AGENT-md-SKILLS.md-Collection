from __future__ import annotations

import json
import sys
import unittest

from helpers import REPO_ROOT
from test_rc_finding_code_contracts import published_signatures
from test_rc_parameterized_finding_codes import (
    published_contracts as published_parameterized_contracts,
)

LIB_ROOT = REPO_ROOT / "tools" / "lib"
if str(LIB_ROOT) not in sys.path:
    sys.path.insert(0, str(LIB_ROOT))

from standards_tools.models import Finding, ToolResult


def published_codes() -> set[str]:
    codes = set(published_signatures())
    codes.update(
        json.loads(contract)["code"]
        for contract in published_parameterized_contracts()
    )
    return codes


class ReleaseCandidateFindingSerializationTests(unittest.TestCase):
    def test_every_published_code_round_trips_through_shared_serialization(self):
        codes = published_codes()
        self.assertGreater(len(codes), 20)

        for code in sorted(codes):
            with self.subTest(code=code):
                finding_payload = Finding(
                    code=code,
                    message="serialization compatibility probe",
                    severity="error",
                    path="probe",
                    line=1,
                ).to_dict()
                self.assertEqual(
                    finding_payload["code"],
                    code,
                    "Finding.to_dict() changed a published automation code",
                )

                result_payload = ToolResult.from_findings(
                    tool="serialization-probe",
                    version="1.0.0",
                    findings=[
                        Finding(
                            code=code,
                            message="serialization compatibility probe",
                            severity="error",
                        )
                    ],
                ).to_dict()
                self.assertEqual(
                    result_payload["findings"][0]["code"],
                    code,
                    "ToolResult serialization changed a published automation code",
                )


if __name__ == "__main__":
    unittest.main()
