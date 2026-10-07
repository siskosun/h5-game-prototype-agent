from __future__ import annotations

import hashlib
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("stage_probe_evidence", ROOT / "dev" / "stage_probe_evidence.py")
stager = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(stager)


class ProbeEvidenceTests(unittest.TestCase):
    def make_evidence(self, root: Path) -> None:
        for name, source_dir in stager.SCENARIOS.items():
            probe = root / source_dir / ".probe"
            (probe / "screenshots").mkdir(parents=True)
            (probe / "video").mkdir()
            (probe / "screenshots" / "player_path.png").write_bytes(b"png-fixture")
            (probe / "video" / "session.webm").write_bytes(b"webm-fixture")
            verdict = "MACHINE_REJECT" if name == "spam-wins" else "READY_FOR_PLAYTEST"
            report = {
                "source_sha": "source-fixture",
                "build_id": "build-fixture",
                "agent_verdict": verdict,
                "human_verdict": "PENDING",
                "checks": [{"name": "player_path", "evidence": ".probe/screenshots/player_path.png"}],
                "video": ".probe/video/session.webm",
            }
            (probe / "report.json").write_text(json.dumps(report) + "\n", encoding="utf-8")

    def test_complete_artifact_is_allowlisted_and_reports_are_unchanged(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            self.make_evidence(root)
            probe = root / stager.SCENARIOS["normal"] / ".probe"
            for extra in (".env", "notes.json", "screenshots/.secret.png", "screenshots/old.png", "video/old.webm"):
                (probe / extra).write_bytes(b"must-not-upload")
            output = root / "artifacts" / "probe-evidence"
            output.mkdir(parents=True)
            (output / "stale.txt").write_text("old run", encoding="utf-8")

            manifest = stager.stage(root)

            self.assertEqual(manifest["errors"], [])
            paths = {p.relative_to(output).as_posix() for p in output.rglob("*") if p.is_file()}
            expected = {"manifest.json"}
            for name, source_dir in stager.SCENARIOS.items():
                expected.update({f"{name}/report.json", f"{name}/screenshots/player_path.png", f"{name}/video/session.webm"})
                self.assertEqual((output / name / "report.json").read_bytes(), (root / source_dir / ".probe/report.json").read_bytes())
                for entry in manifest["scenarios"][name]["files"]:
                    data = (output / entry["path"]).read_bytes()
                    self.assertEqual(data, (root / entry["source"]).read_bytes())
                    self.assertEqual(entry["sha256"], hashlib.sha256(data).hexdigest())
                    self.assertEqual(entry["size_bytes"], len(data))
            self.assertEqual(paths, expected)

    def test_missing_evidence_in_each_scenario_fails_and_retains_partial_evidence(self):
        for name, source_dir in stager.SCENARIOS.items():
            for missing in ("report.json", "screenshots/player_path.png", "video/session.webm"):
                with self.subTest(scenario=name, missing=missing), tempfile.TemporaryDirectory() as td:
                    root = Path(td)
                    self.make_evidence(root)
                    (root / source_dir / ".probe" / missing).unlink()
                    manifest = stager.stage(root)
                    self.assertTrue(manifest["errors"])
                    self.assertTrue(all(error.startswith(f"{name}:") for error in manifest["errors"]))
                    other = next(n for n in stager.SCENARIOS if n != name)
                    self.assertEqual(len(manifest["scenarios"][other]["files"]), 3)
                    self.assertTrue((root / "artifacts/probe-evidence/manifest.json").is_file())

    def test_empty_media_fails(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            self.make_evidence(root)
            (root / stager.SCENARIOS["normal"] / ".probe/video/session.webm").write_bytes(b"")
            self.assertTrue(any("empty evidence" in e for e in stager.stage(root)["errors"]))

    def test_disallowed_report_references_are_not_copied(self):
        values = [None, "", ".probe/.env", ".probe/screenshots/.secret.png", ".probe/screenshots/../../secret.png", "/tmp/secret.png", ".probe\\screenshots\\player_path.png"]
        for value in values:
            with self.subTest(reference=value), tempfile.TemporaryDirectory() as td:
                root = Path(td)
                self.make_evidence(root)
                report_path = root / stager.SCENARIOS["normal"] / ".probe/report.json"
                report = json.loads(report_path.read_text(encoding="utf-8"))
                report["checks"][0]["evidence"] = value
                report_path.write_text(json.dumps(report), encoding="utf-8")
                manifest = stager.stage(root)
                self.assertTrue(manifest["errors"])
                self.assertEqual(len(manifest["scenarios"]["normal"]["files"]), 2)

    def test_symlink_evidence_is_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            self.make_evidence(root)
            shot = root / stager.SCENARIOS["normal"] / ".probe/screenshots/player_path.png"
            shot.unlink()
            target = root / "private.png"
            target.write_bytes(b"private")
            try:
                shot.symlink_to(target)
            except OSError as exc:
                self.skipTest(f"symlinks unavailable: {exc}")
            manifest = stager.stage(root)
            self.assertTrue(any("symlink evidence" in e for e in manifest["errors"]))
            self.assertFalse((root / "artifacts/probe-evidence/normal/screenshots/player_path.png").exists())

    def test_malformed_report_fails_but_is_preserved_for_diagnosis(self):
        for value in ("{broken", "[]", '{"checks": []}'):
            with self.subTest(report=value), tempfile.TemporaryDirectory() as td:
                root = Path(td)
                self.make_evidence(root)
                report_path = root / stager.SCENARIOS["normal"] / ".probe/report.json"
                report_path.write_text(value, encoding="utf-8")
                manifest = stager.stage(root)
                self.assertTrue(manifest["errors"])
                self.assertEqual((root / "artifacts/probe-evidence/normal/report.json").read_text(encoding="utf-8"), value)


if __name__ == "__main__":
    unittest.main()
