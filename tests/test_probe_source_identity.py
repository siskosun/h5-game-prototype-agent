from __future__ import annotations

import importlib.util
import subprocess
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]


def load(name: str):
    file = ROOT / "scripts" / (name + ".py")
    spec = importlib.util.spec_from_file_location(name, file)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


identity = load("source_tree_identity")
validator = load("validate_probe_report")
NODE_HASH = (ROOT / "templates/probe/qa/source-tree.mjs").as_uri()


def node_hash(root: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["node", "-e", "import(process.argv[1]).then(m => console.log(m.sourceTreeSha256(process.argv[2])))",
         NODE_HASH, str(root)], capture_output=True, text=True, encoding="utf-8",
    )


class SourceIdentityTests(unittest.TestCase):
    @staticmethod
    def fixture(root: Path) -> None:
        (root / "src").mkdir()
        (root / "src/main.ts").write_text("export const score = 1;\n", encoding="utf-8")
        (root / "probe_card.md").write_text("frozen card\n", encoding="utf-8")

    def test_node_python_hash_parity(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            self.fixture(root)
            (root / "src/中文棋盘.ts").write_text("中文", encoding="utf-8")
            (root / "src/emoji_🐉.ts").write_bytes(b"opaque\x00bytes")
            result = node_hash(root)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stdout.strip(), identity.source_tree_sha256(root))

    def test_dirty_tracked_and_untracked_sources_invalidate(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            self.fixture(root)
            clean = identity.source_tree_sha256(root)
            (root / "src/main.ts").write_text("modified", encoding="utf-8")
            dirty = identity.source_tree_sha256(root)
            self.assertNotEqual(clean, dirty)
            (root / "src/new.ts").write_text("untracked", encoding="utf-8")
            self.assertNotEqual(dirty, identity.source_tree_sha256(root))

    def test_generated_outputs_do_not_change_identity(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            self.fixture(root)
            clean = identity.source_tree_sha256(root)
            for name in identity.SOURCE_EXCLUDES:
                (root / name).mkdir()
                (root / name / "generated.json").write_text("new", encoding="utf-8")
            self.assertEqual(clean, identity.source_tree_sha256(root))

    def test_source_symlink_rejected_in_both_languages(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            self.fixture(root)
            try:
                (root / "src/link.ts").symlink_to(root / "src/main.ts")
            except OSError:
                self.skipTest("symlinks unsupported")
            with self.assertRaisesRegex(ValueError, "symlink"):
                identity.source_tree_sha256(root)
            result = node_hash(root)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("symlink", result.stderr)

    def test_report_new_identity_detects_changes_and_legacy_is_allowed(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            self.fixture(root)
            report = {"agent_verdict": "UNCERTAIN", "card_sha256": "test-digest",
                      "checks": [{"name": "browser_health", "input_source": "PLAYER", "status": "INCONCLUSIVE"}],
                      "source_tree_sha256": identity.source_tree_sha256(root)}
            card = root / "probe_card.md"
            fake = SimpleNamespace(read_card=lambda _: ("text", {}, None),
                                   card_digest=lambda _: "test-digest")
            with patch.object(validator, "load_card_module", return_value=fake):
                self.assertEqual(validator.validate(report, card), [])
                (root / ".probe").mkdir()
                (root / ".probe/report.json").write_text("new evidence", encoding="utf-8")
                self.assertEqual(validator.validate(report, card), [])
                (root / "src/main.ts").write_text("modified", encoding="utf-8")
                self.assertTrue(any("differs" in e for e in validator.validate(report, card)))
                report.pop("source_tree_sha256")
                self.assertEqual(validator.validate(report, card), [])
                report["source_tree_sha256"] = None
                self.assertTrue(any("must be" in e for e in validator.validate(report, card)))

    def test_explicit_source_root(self):
        with tempfile.TemporaryDirectory() as td:
            project = Path(td) / "project"
            project.mkdir()
            self.fixture(project)
            detached = Path(td) / "detached"
            detached.mkdir()
            card = detached / "probe_card.md"
            card.write_text("card", encoding="utf-8")
            report = {"agent_verdict": "UNCERTAIN", "card_sha256": "x",
                      "checks": [{"status": "INCONCLUSIVE", "input_source": "PLAYER"}],
                      "source_tree_sha256": identity.source_tree_sha256(project)}
            fake = SimpleNamespace(read_card=lambda _: ("text", {}, None), card_digest=lambda _: "x")
            with patch.object(validator, "load_card_module", return_value=fake):
                self.assertEqual(validator.validate(report, card, source_root=project), [])
                self.assertTrue(any("differs" in e for e in validator.validate(report, card)))


if __name__ == "__main__":
    unittest.main()
