#!/usr/bin/env python3
from __future__ import annotations

import argparse
import copy
import datetime as dt
import hashlib
import json
import re
import sys
from pathlib import Path

JSON_BLOCK = re.compile(r"```json\s*(\{.*?\})\s*```", re.DOTALL)
REQUIRED = [
    "probe_id", "experience_goal", "core_mechanic", "hypothesis",
    "kill_criteria", "target_viewport", "input_mode", "time_box",
    "human_observation_points", "frozen_at", "frozen_sha256",
]
VALID_INPUT = {"mouse", "touch", "keyboard"}

class CardError(ValueError):
    pass


def read_card(path: Path):
    text = path.read_text(encoding="utf-8")
    match = JSON_BLOCK.search(text)
    if not match:
        raise CardError("probe card must contain one JSON code block")
    try:
        data = json.loads(match.group(1))
    except json.JSONDecodeError as exc:
        raise CardError(f"invalid JSON: {exc}") from exc
    if not isinstance(data, dict):
        raise CardError("probe card JSON must be an object")
    return text, data, match


def canonical_payload(data: dict) -> str:
    payload = copy.deepcopy(data)
    payload.pop("frozen_at", None)
    payload.pop("frozen_sha256", None)
    return json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def card_digest(data: dict) -> str:
    return hashlib.sha256(canonical_payload(data).encode("utf-8")).hexdigest()


def digest(data: dict) -> str:
    return card_digest(data)


def validate_data(data: dict) -> list[str]:
    errors: list[str] = []
    for key in REQUIRED:
        if key not in data:
            errors.append(f"missing field: {key}")
    for key in ("probe_id", "experience_goal", "core_mechanic", "hypothesis", "target_viewport", "input_mode", "time_box"):
        if not str(data.get(key, "")).strip():
            errors.append(f"{key} must be non-empty")
    if data.get("input_mode") not in VALID_INPUT:
        errors.append("input_mode must be mouse, touch, or keyboard")
    viewport = data.get("target_viewport")
    if isinstance(viewport, dict):
        if not isinstance(viewport.get("width"), int) or not isinstance(viewport.get("height"), int):
            errors.append("target_viewport width/height must be integers")
    elif isinstance(viewport, str):
        if not re.fullmatch(r"\d+x\d+", viewport.strip()):
            errors.append("target_viewport must be WIDTHxHEIGHT or an object")
    else:
        errors.append("target_viewport must be WIDTHxHEIGHT or an object")
    kills = data.get("kill_criteria")
    if not isinstance(kills, list) or not kills or not all(str(x).strip() for x in kills):
        errors.append("kill_criteria must be a non-empty list")
    else:
        vague = {"不好玩", "不有趣", "没意思", "not fun", "boring"}
        for item in kills:
            normalized = str(item).strip().lower().rstrip("。.!！")
            if normalized in vague:
                errors.append("kill_criteria is not observable; describe a behavior or outcome")
    points = data.get("human_observation_points")
    if not isinstance(points, list) or not 2 <= len(points) <= 3 or not all(str(x).strip() for x in points):
        errors.append("human_observation_points must contain 2-3 non-empty items")
    intended = data.get("intended_degenerate_strategies", [])
    if not isinstance(intended, list):
        errors.append("intended_degenerate_strategies must be a list")
    return errors


def rewrite(path: Path, text: str, match: re.Match[str], data: dict) -> None:
    block = "```json\n" + json.dumps(data, ensure_ascii=False, indent=2) + "\n```"
    path.write_text(text[:match.start()] + block + text[match.end():], encoding="utf-8")


def cmd_validate(path: Path) -> int:
    _, data, _ = read_card(path)
    errors = validate_data(data)
    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 2
    print("VALID")
    return 0


def cmd_freeze(path: Path) -> int:
    text, data, match = read_card(path)
    errors = validate_data(data)
    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 2
    data["frozen_at"] = dt.datetime.now(dt.timezone.utc).isoformat()
    data["frozen_sha256"] = card_digest(data)
    rewrite(path, text, match, data)
    print(data["frozen_sha256"])
    return 0


def cmd_check(path: Path) -> int:
    _, data, _ = read_card(path)
    errors = validate_data(data)
    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 2
    expected = data.get("frozen_sha256")
    if not expected:
        print("card is not frozen", file=sys.stderr)
        return 1
    actual = card_digest(data)
    if actual != expected:
        print(f"FROZEN_CARD_DRIFT expected={expected} actual={actual}", file=sys.stderr)
        return 1
    print("FROZEN_OK")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=["validate", "freeze", "check"])
    parser.add_argument("card", type=Path)
    args = parser.parse_args()
    try:
        if args.command == "validate":
            return cmd_validate(args.card)
        if args.command == "freeze":
            return cmd_freeze(args.card)
        return cmd_check(args.card)
    except (OSError, CardError) as exc:
        print(str(exc), file=sys.stderr)
        return 2

if __name__ == "__main__":
    raise SystemExit(main())
