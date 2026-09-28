from __future__ import annotations

import importlib.util
import tempfile
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def load_packager():
    path = ROOT / "dev" / "build_skill_zip.py"
    spec = importlib.util.spec_from_file_location("build_skill_zip", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module

packager = load_packager()

class PackagingTests(unittest.TestCase):
    def test_runtime_zip_is_whitelisted(self):
        with tempfile.TemporaryDirectory() as td:
            out = Path(td) / "skill.zip"
            names = packager.build(out)
            self.assertIn("SKILL.md", names)
            self.assertIn("agents/openai.yaml", names)
            self.assertIn("templates/probe/qa/probe-check.mjs", names)
            self.assertFalse(any(n.startswith("tests/") for n in names))
            self.assertFalse(any(n.startswith("dev/") for n in names))
            self.assertFalse(any(n.startswith(".github/") for n in names))
            self.assertFalse(any("node_modules/" in n for n in names))
            self.assertFalse(any(n.startswith("ut-") for n in names))
            with zipfile.ZipFile(out) as zf:
                self.assertEqual(sorted(names), sorted(zf.namelist()))

if __name__ == "__main__":
    unittest.main()
