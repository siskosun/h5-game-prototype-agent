#!/usr/bin/env python3
from __future__ import annotations

import re
import sys
from pathlib import Path

REQUIRED_BLOCK_HEADINGS = [
    "### Locked upstream decisions",
    "### Alternatives",
    "### Comparative axes",
    "### Recommendation",
    "### User decision",
]


def nonempty_field(block: str, label: str) -> bool:
    m = re.search(rf"^- {re.escape(label)}:\s*(.+?)\s*$", block, flags=re.M)
    if not m:
        return False
    value = m.group(1).strip()
    return bool(value) and value not in {"-", "N/A"} and not (value.startswith("<") and value.endswith(">"))


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: validate_design_forks.py <design_forks.md>")
        return 2

    p = Path(sys.argv[1])
    if not p.exists():
        print(f"ERROR: missing file: {p}")
        return 2

    text = p.read_text(encoding="utf-8")
    errors: list[str] = []

    if "# Design Forks" not in text:
        errors.append("missing # Design Forks")

    gate = re.search(r"^- Gate:\s*(OPEN|CONFIRMED|SKIPPED)\s*$", text, flags=re.M)
    if not gate:
        errors.append("missing valid Gate status")
    elif gate.group(1) != "CONFIRMED":
        errors.append(f"gate is {gate.group(1)}; Design-Fork Grill must be CONFIRMED before GDD finalization")

    fork_matches = list(re.finditer(r"^## Fork\s+[^\n]+$", text, flags=re.M))
    if not fork_matches:
        errors.append("missing at least one ## Fork block")

    for i, match in enumerate(fork_matches):
        start = match.start()
        end = fork_matches[i + 1].start() if i + 1 < len(fork_matches) else len(text)
        block = text[start:end]
        name = match.group(0)
        for heading in REQUIRED_BLOCK_HEADINGS:
            if heading not in block:
                errors.append(f"{name}: missing {heading}")
        for label in ("Chosen direction", "Accepted tradeoff", "Rejected direction(s) and why", "Downstream GDD sections unlocked/changed"):
            if not nonempty_field(block, label):
                errors.append(f"{name}: missing resolved field '{label}'")

    unresolved = re.findall(r"<[^>]+>", text)
    if unresolved:
        errors.append("unresolved template placeholders remain")

    if errors:
        print("DESIGN FORKS INVALID")
        for e in errors:
            print(f"- {e}")
        return 1

    print("DESIGN FORKS VALID")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
