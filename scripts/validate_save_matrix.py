#!/usr/bin/env python3
from __future__ import annotations
import sys
from pathlib import Path

REQUIRED = [
    "Stable checkpoint -> reload",
    "Repeat settlement same runId",
    "Corrupt save",
    "Incompatible schema",
]


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: validate_save_matrix.py <save_matrix.md>")
        return 2
    path = Path(sys.argv[1])
    if not path.exists():
        print(f"SAVE MATRIX INVALID\n- missing file: {path}")
        return 2
    text = path.read_text(encoding="utf-8")
    errors = [f"missing scenario: {row}" for row in REQUIRED if row not in text]
    if "TBD" in text:
        errors.append("unresolved TBD result remains")
    if errors:
        print("SAVE MATRIX INVALID")
        for error in errors:
            print(f"- {error}")
        return 1
    print("SAVE MATRIX VALID")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
