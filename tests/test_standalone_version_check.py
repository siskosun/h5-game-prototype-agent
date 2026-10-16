from __future__ import annotations
import importlib.util
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("standalone_version_check", ROOT / "scripts/standalone_version_check.py")
checker = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(checker)

class StandaloneVersionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / "skill"
        self.root.mkdir()
        (self.root / "SKILL.md").write_text("---\nname: h5-game-prototype-agent\n---\n", encoding="utf-8")
        (self.root / "VERSION").write_text("0.2.6\n", encoding="utf-8")
        self.lock = {"schema_version": 1, "policy": "released-pins-only", "bundle_version": "0.4.4", "components": {
            "h5-game-prototype-agent": {"repository": "siskosun/h5-game-prototype-agent", "version": "0.2.6", "min_version": "0.2.6",
                       "skill_git_blob_sha1": checker.blob_sha1(self.root / "SKILL.md")}}}

    def fetch(self, url):
        if url == checker.LOCK_URL: return self.lock
        if url == checker.API + "h5-game-prototype-agent/releases/latest":
            return {"tag_name": "v0.2.6", "draft": False, "prerelease": False}
        raise ValueError("unexpected URL")

    def test_current_exact_pin(self):
        self.assertEqual(checker.evaluate(self.root, fetch=self.fetch)["status"], "CURRENT")

    def test_newer_release_advisory(self):
        def newer(url):
            return {"tag_name": "v0.2.7"} if url.endswith("/releases/latest") else self.fetch(url)
        self.assertEqual(checker.evaluate(self.root, fetch=newer)["status"], "UPDATE_AVAILABLE")

    def test_outdated_installed_version_blocks(self):
        (self.root / "VERSION").write_text("0.2.4\n", encoding="utf-8")
        self.assertEqual(checker.evaluate(self.root, fetch=self.fetch)["status"], "INCOMPATIBLE")

    def test_unreviewed_newer_self_not_auto_approved(self):
        (self.root / "VERSION").write_text("0.2.7\n", encoding="utf-8")
        self.assertEqual(checker.evaluate(self.root, fetch=self.fetch)["status"], "UNVERIFIED")

    def test_modified_entrypoint_blocks(self):
        with (self.root / "SKILL.md").open("a", encoding="utf-8") as out: out.write("tampered")
        self.assertEqual(checker.evaluate(self.root, fetch=self.fetch)["status"], "INCOMPATIBLE")

    def test_unknown_network_blocks_only_dependent_flow(self):
        def offline(url): raise ValueError("offline")
        self.assertEqual(checker.evaluate(self.root, fetch=offline)["status"], "UNVERIFIED")

    def test_missing_companion_dependency_fails_closed(self):
        r = checker.evaluate(self.root, fetch=self.fetch, harness="codex",
                             home=Path(self.temp.name), peers=("game-exp",))
        self.assertEqual(r["status"], "UNVERIFIED")
        self.assertEqual(r["peers"]["game-exp"]["status"], "UNVERIFIED")

    def test_explicit_stable_release_only(self):
        def prerelease(url):
            return {"tag_name":"v0.2.7-rc1", "prerelease":True} if url.endswith("/releases/latest") else self.fetch(url)
        self.assertEqual(checker.evaluate(self.root, fetch=prerelease)["status"], "UNVERIFIED")

if __name__ == "__main__":
    unittest.main()
