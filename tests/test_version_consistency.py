from __future__ import annotations

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class VersionConsistencyTests(unittest.TestCase):
    def test_documentation_matches_version(self):
        version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
        self.assertRegex(version, r"^\d+\.\d+\.\d+$")
        readmes = ["README.md"]

        for name in readmes:
            with self.subTest(file=name):
                text = (ROOT / name).read_text(encoding="utf-8")
                title = re.search(r"^# [^\n]*\b(\d+\.\d+\.\d+)[ \t]*$", text, re.MULTILINE)
                current = re.search(r"^## (\d+\.\d+\.\d+)(?=[ \t：:\r\n]|$)", text, re.MULTILINE)
                self.assertIsNotNone(title, f"{name}: missing version in main title")
                self.assertIsNotNone(current, f"{name}: missing current version section")
                self.assertEqual(title.group(1), version, f"{name}: stale main title")
                self.assertEqual(current.group(1), version, f"{name}: stale current version section")

        changelog = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
        latest = re.search(r"^## (\d+\.\d+\.\d+) - ", changelog, re.MULTILINE)
        self.assertIsNotNone(latest, "CHANGELOG.md: missing release entry")
        self.assertEqual(latest.group(1), version, "CHANGELOG.md: latest release differs from VERSION")


if __name__ == "__main__":
    unittest.main()
