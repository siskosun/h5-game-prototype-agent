#!/usr/bin/env python3
from __future__ import annotations
import json
import sys
from pathlib import Path


def dominates(a: dict, b: dict, dims: dict[str, str]) -> bool:
    better = False
    for dim, direction in dims.items():
        av = float(a.get("metrics", {}).get(dim, 0))
        bv = float(b.get("metrics", {}).get(dim, 0))
        if direction == "max":
            if av < bv:
                return False
            better |= av > bv
        elif direction == "min":
            if av > bv:
                return False
            better |= av < bv
        else:
            raise ValueError(f"unknown direction {direction!r} for {dim}")
    return better


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: validate_choice_space.py <choice-space.json>")
        return 2
    data = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    dims = data.get("dimensions", {})
    options = data.get("options", [])
    if not dims or len(options) < 2:
        print("CHOICE SPACE INVALID: require dimensions and at least two options")
        return 2
    errors: list[str] = []
    for opt in options:
        if not opt.get("rationalContexts"):
            errors.append(f"option {opt.get('id')} has no rationalContexts")
    for i, a in enumerate(options):
        for j, b in enumerate(options):
            if i == j:
                continue
            if dominates(a, b, dims) and not b.get("compensatingTradeoff"):
                errors.append(f"strict dominance: {a.get('id')} dominates {b.get('id')}")
    if errors:
        print("CHOICE SPACE FAILED")
        for e in errors:
            print(f"- {e}")
        return 1
    print("CHOICE SPACE PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
