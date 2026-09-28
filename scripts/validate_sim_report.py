#!/usr/bin/env python3
from __future__ import annotations
import json
import sys
from pathlib import Path


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: validate_sim_report.py <sim_report.json>")
        return 2
    p = Path(sys.argv[1])
    if not p.exists():
        print(f"SIM REPORT INVALID\n- missing file: {p}")
        return 2
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except Exception as exc:
        print(f"SIM REPORT INVALID\n- invalid json: {exc}")
        return 1
    errors: list[str] = []
    runs = data.get("runs")
    if not isinstance(runs, int) or runs <= 0:
        errors.append("runs must be a positive integer")
    for key in ("runtimeErrors", "invariantFailures", "softlocks"):
        value = data.get(key)
        if not isinstance(value, int):
            errors.append(f"{key} must be an integer")
        elif value != 0:
            errors.append(f"{key} must be 0, got {value}")
    failing = data.get("failingSeeds", [])
    if failing not in ([], None):
        errors.append("failingSeeds must be empty for PASS")
    if errors:
        print("SIM REPORT INVALID")
        for error in errors:
            print(f"- {error}")
        return 1
    print(f"SIM REPORT VALID ({runs} runs)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
