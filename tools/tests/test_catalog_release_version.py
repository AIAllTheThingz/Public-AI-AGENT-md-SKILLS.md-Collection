from __future__ import annotations

import re
import unittest

from helpers import REPO_ROOT


SEMVER = r"(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)(?:-[0-9A-Za-z.-]+)?(?:\+[0-9A-Za-z.-]+)?"
CURRENT_CATALOG_VERSION = re.compile(
    rf"The current `(?P<version>{SEMVER})` (?:release candidate|release|baseline) is",
    re.IGNORECASE,
)


class CatalogReleaseVersionTests(unittest.TestCase):
    def test_catalog_current_version_matches_version_file(self):
        version = (REPO_ROOT / "VERSION").read_text(encoding="utf-8").strip()
        catalog = (REPO_ROOT / "CATALOG.md").read_text(encoding="utf-8")
        matches = CURRENT_CATALOG_VERSION.findall(catalog)
        self.assertEqual(
            matches,
            [version],
            f"CATALOG.md current release boundary must match VERSION ({version}).",
        )


if __name__ == "__main__":
    unittest.main()
