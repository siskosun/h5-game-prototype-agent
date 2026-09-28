from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def load(name: str):
    path = ROOT / "scripts" / f"{name}.py"
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module

probe_card = load("probe_card")
probe_log = load("probe_log")
validate_report = load("validate_probe_report")

BASE_CARD = {
    "probe_id": "p-1",
    "experience_goal": "玩家会等待时机再行动。",
    "core_mechanic": "在窗口内点击。",
    "hypothesis": "错误点击有代价时，玩家会观察时机。",
    "kill_criteria": ["连续点击无需观察时机即可获胜"],
    "intended_degenerate_strategies": [],
    "target_viewport": {"width": 390, "height": 844},
    "input_mode": "mouse",
    "time_box": "4h",
    "human_observation_points": ["第一局是否观察", "失败后是否调整"],
    "frozen_at": "",
    "frozen_sha256": "",
}

def write_card(path: Path, data: dict) -> None:
    path.write_text("# Probe\n\n```json\n" + json.dumps(data, ensure_ascii=False, indent=2) + "\n```\n", encoding="utf-8")

class ProbeCardTests(unittest.TestCase):
    def test_validate_freeze_and_detect_tampering(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "probe_card.md"
            write_card(path, dict(BASE_CARD))
            self.assertEqual(probe_card.cmd_validate(path), 0)
            self.assertEqual(probe_card.cmd_freeze(path), 0)
            self.assertEqual(probe_card.cmd_check(path), 0)
            text, data, match = probe_card.read_card(path)
            data["hypothesis"] = "偷偷改过"
            probe_card.rewrite(path, text, match, data)
            self.assertEqual(probe_card.cmd_check(path), 1)

    def test_vague_kill_criterion_rejected(self):
        data = dict(BASE_CARD)
        data["kill_criteria"] = ["不好玩"]
        self.assertTrue(any("not observable" in e for e in probe_card.validate_data(data)))

class ProbeLogTests(unittest.TestCase):
    def test_final_status_derivation(self):
        self.assertEqual(probe_log.final_status("MACHINE_REJECT", "PENDING"), "REJECT")
        self.assertEqual(probe_log.final_status("READY_FOR_PLAYTEST", "PENDING"), "WAITING_FOR_PLAYTEST")
        self.assertEqual(probe_log.final_status("READY_FOR_PLAYTEST", "PASS"), "PASS")

    def test_human_update_requires_playtest_record(self):
        row = {
            "probe_id": "p-1", "date": "2026-09-28", "title": "x",
            "hypothesis": "h", "kill_criteria": ["observable"],
            "agent_verdict": "READY_FOR_PLAYTEST", "human_verdict": "PASS",
            "final_status": "PASS", "failure_class": "", "reason": "",
            "revisit_when": "", "repo_path": ".", "source_sha": "abc"
        }
        self.assertEqual(probe_log.validate_row(row), [])

class ProbeLogCliTests(unittest.TestCase):
    def run_cli(self, cwd: Path, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "probe_log.py"), *args],
            cwd=cwd,
            text=True,
            encoding="utf-8",
            errors="replace",
            capture_output=True,
        )

    def test_add_search_list_validate_and_human_update_gate(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            payload = root / "row.json"
            payload.write_text(json.dumps({
                "probe_id": "p-cli",
                "title": "节奏探针",
                "hypothesis": "玩家会等待时机",
                "kill_criteria": ["连续乱点可以获胜"],
                "agent_verdict": "READY_FOR_PLAYTEST",
                "human_verdict": "PENDING",
                "failure_class": "",
                "reason": "",
                "revisit_when": "窗口规则变化",
                "repo_path": ".",
                "source_sha": "abc123"
            }, ensure_ascii=False), encoding="utf-8")

            added = self.run_cli(root, "add", "--json", str(payload))
            self.assertEqual(added.returncode, 0, added.stderr)
            self.assertTrue((root / "probes.jsonl").exists())

            searched = self.run_cli(root, "search", "节奏")
            self.assertEqual(searched.returncode, 0, searched.stderr)
            self.assertIn("p-cli", searched.stdout)

            listed = self.run_cli(root, "list", "--status", "WAITING_FOR_PLAYTEST")
            self.assertEqual(listed.returncode, 0, listed.stderr)
            self.assertIn("p-cli", listed.stdout)

            valid = self.run_cli(root, "validate")
            self.assertEqual(valid.returncode, 0, valid.stderr)

            blocked = self.run_cli(root, "update", "p-cli", "--human-verdict", "PASS")
            self.assertNotEqual(blocked.returncode, 0)
            self.assertIn("playtest record", blocked.stderr)

            playtest = root / "playtest.md"
            playtest.write_text("human session", encoding="utf-8")
            updated = self.run_cli(
                root, "update", "p-cli", "--human-verdict", "PASS",
                "--playtest-record", str(playtest)
            )
            self.assertEqual(updated.returncode, 0, updated.stderr)
            self.assertIn("PASS", updated.stdout)


class ProbeReportTests(unittest.TestCase):
    def frozen_card(self, root: Path) -> tuple[Path, str]:
        card = root / "probe_card.md"
        data = dict(BASE_CARD)
        digest = probe_card.card_digest(data)
        data["frozen_at"] = "2026-09-28T00:00:00Z"
        data["frozen_sha256"] = digest
        write_card(card, data)
        return card, digest

    def test_ready_report_validates(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            card, digest = self.frozen_card(root)
            evidence = root / "shot.png"
            evidence.write_bytes(b"fixture")
            checks = [
                {"name": "player_path", "input_source": "PLAYER", "status": "PASS", "evidence": "shot.png"},
                {"name": "degenerate_spam", "input_source": "PLAYER", "status": "PASS", "evidence": "shot.png"},
                {"name": "degenerate_idle", "input_source": "INJECTED", "status": "PASS", "evidence": "shot.png"},
                {"name": "degenerate_repeat", "input_source": "PLAYER", "status": "PASS", "evidence": "shot.png"},
            ]
            report = {"agent_verdict": "READY_FOR_PLAYTEST", "card_sha256": digest, "checks": checks}
            self.assertEqual(validate_report.validate(report, card, root), [])

    def test_rejects_agent_pass_injected_player_path_missing_evidence_and_bad_hash(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            card, _ = self.frozen_card(root)
            report = {
                "agent_verdict": "PASS",
                "card_sha256": "bad",
                "checks": [{"name": "player_path", "input_source": "INJECTED", "status": "PASS", "evidence": "missing.png"}],
            }
            errors = validate_report.validate(report, card, root)
            joined = " | ".join(errors)
            self.assertIn("can never be PASS", joined)
            self.assertIn("does not match", joined)
            self.assertIn("evidence missing", joined)

if __name__ == "__main__":
    unittest.main()
