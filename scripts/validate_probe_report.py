#!/usr/bin/env python3
from __future__ import annotations

import argparse
import importlib.util
import json
import re
import sys
from pathlib import Path

VALID_AGENT = {"READY_FOR_PLAYTEST", "MACHINE_REJECT", "UNCERTAIN"}
VALID_STATUS = {"PASS", "FAIL", "INCONCLUSIVE"}
VALID_INPUT = {"PLAYER", "INJECTED", "EMULATED_TOUCH"}


def load_card_module():
    script = Path(__file__).with_name("probe_card.py")
    spec = importlib.util.spec_from_file_location("probe_card", script)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def validate(report: dict, card_path: Path, evidence_root: Path | None = None,
             source_root: Path | None = None) -> list[str]:
    errors: list[str] = []
    evidence_root = evidence_root or card_path.parent
    agent = report.get("agent_verdict")
    if agent == "PASS":
        errors.append("agent_verdict can never be PASS")
    if agent not in VALID_AGENT:
        errors.append("invalid agent_verdict")
    checks = report.get("checks")
    if not isinstance(checks, list) or not checks:
        errors.append("checks must be a non-empty list")
        checks = []
    for index, check in enumerate(checks):
        if check.get("status") not in VALID_STATUS:
            errors.append(f"checks[{index}] invalid status")
        if check.get("input_source") not in VALID_INPUT:
            errors.append(f"checks[{index}] invalid input_source")
        evidence = check.get("evidence")
        if evidence:
            evidence_path = (evidence_root / evidence).resolve()
            if not evidence_path.exists():
                errors.append(f"checks[{index}] evidence missing: {evidence}")
    card_module = load_card_module()
    _, card, _ = card_module.read_card(card_path)
    actual = card_module.card_digest(card)
    if report.get("card_sha256") != actual:
        errors.append("card_sha256 does not match current card")
    if agent == "READY_FOR_PLAYTEST":
        player = next((c for c in checks if c.get("name") == "player_path"), None)
        if not player or player.get("status") != "PASS" or player.get("input_source") != "PLAYER":
            errors.append("READY_FOR_PLAYTEST requires PASS player_path with input_source=PLAYER")
        degenerates = [c for c in checks if str(c.get("name", "")).startswith("degenerate_")]
        if any(c.get("status") == "FAIL" for c in degenerates):
            errors.append("READY_FOR_PLAYTEST cannot contain failed degenerate checks")
        if any(not c.get("evidence") for c in checks):
            errors.append("READY_FOR_PLAYTEST requires evidence for every check")
    if "source_tree_sha256" in report:
        expected = report["source_tree_sha256"]
        if not isinstance(expected, str) or re.fullmatch(r"[0-9a-f]{64}", expected) is None:
            errors.append("source_tree_sha256 must be a lowercase SHA-256 hex string")
        else:
            try:
                script = Path(__file__).with_name("source_tree_identity.py")
                spec = importlib.util.spec_from_file_location("source_tree_identity", script)
                module = importlib.util.module_from_spec(spec)
                assert spec.loader is not None
                spec.loader.exec_module(module)
                current = module.source_tree_sha256(source_root or card_path.parent)
            except (OSError, ValueError) as exc:
                errors.append(f"cannot verify source_tree_sha256: {exc}")
            else:
                if expected != current:
                    errors.append("source_tree_sha256 differs from current working-source bytes")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("report", type=Path)
    parser.add_argument("--card", type=Path, required=True)
    parser.add_argument("--source-root", type=Path,
                        help="working source root, defaults to the directory containing --card")
    args = parser.parse_args()
    try:
        report = json.loads(args.report.read_text(encoding="utf-8"))
        errors = validate(report, args.card, args.card.parent, args.source_root)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        return 2
    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 2
    print("VALID")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
