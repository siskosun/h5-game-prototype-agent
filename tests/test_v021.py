from __future__ import annotations

import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]


class IterationDeliveryV021Tests(unittest.TestCase):
    def test_version_and_skill_contract(self):
        self.assertEqual((ROOT / "VERSION").read_text(encoding="utf-8").strip(), "0.2.2")
        skill = (ROOT / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("iteration_delivery", skill)
        self.assertIn("participant-reported implementation context", skill)

    def test_game_exp_delivery_contract_preserves_probe_and_human_gates(self):
        text = (ROOT / "references" / "game-exp-integration.md").read_text(encoding="utf-8")
        for phrase in (
            "SHAREABLE_URL | LOCAL_URL | ARTIFACT_ONLY | MISSING",
            "producer",
            "previous_candidate_id",
            "participant_reported",
            "experiment_panel.delivery_card",
            "never invent a URL",
            "READY_FOR_PLAYTEST",
            "human PASS",
            "publish_github_pages.py",
            "play/<result_source_sha>/",
            "real browser",
        ):
            self.assertIn(phrase, text)

    def test_templates_are_safe_for_versioned_pages_paths(self):
        for name in ("probe", "dom", "phaser"):
            config = (ROOT / "templates" / name / "vite.config.ts").read_text(
                encoding="utf-8"
            )
            self.assertIn('base: "./"', config)


if __name__ == "__main__":
    unittest.main()
