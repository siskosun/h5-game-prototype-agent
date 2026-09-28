#!/usr/bin/env python3
from __future__ import annotations
import re
import sys
from pathlib import Path

REQUIRED = [
    "# Gameplay Contract",
    "## 1. Player Promise and Scope",
    "## 2. Core Loop",
    "## 3. State and Legal Actions",
    "## 4. Mechanics and Numeric Envelope",
    "### Meaningful-Choice Audit",
    "## 5. Screens, Input, and Feedback",
    "## 6. Mechanic Curriculum",
    "## 7. Persistence",
    "## 8. Headless Simulation Contract",
    "## 9. Acceptance Tests",
    "## 10. Out of Scope",
]
BANNED = [r"\bTODO\b", r"\bTBD\b", r"<required>", r"<fill>"]


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: validate_gameplay_contract.py <gameplay_contract.md>")
        return 2
    path = Path(sys.argv[1])
    if not path.exists():
        print(f"CONTRACT INVALID\n- missing file: {path}")
        return 2
    text = path.read_text(encoding="utf-8")
    errors: list[str] = []
    pos = -1
    for heading in REQUIRED:
        idx = text.find(heading)
        if idx < 0:
            errors.append(f"missing heading: {heading}")
        elif idx < pos:
            errors.append(f"heading out of order: {heading}")
        else:
            pos = idx
    for pattern in BANNED:
        if re.search(pattern, text, flags=re.I):
            errors.append(f"unresolved placeholder matched: {pattern}")
    for marker in ("Trigger", "Preconditions", "Player Action", "State Delta", "Feedback", "Termination"):
        if marker not in text:
            errors.append(f"missing mechanic contract marker: {marker}")
    for marker in ("render_game_to_text", "advanceTime", "__GAME_API__"):
        if marker not in text:
            errors.append(f"missing browser/headless contract marker: {marker}")
    if not all(re.search(rf"\b{word}\b", text) for word in ("Given", "When", "Then")):
        errors.append("Acceptance Tests must include Given / When / Then")
    persistence_disabled = "Persistence: none" in text or "persistence: none" in text.lower()
    persistence_section = text[text.find("## 7. Persistence") : text.find("## 8. Headless Simulation Contract")]
    if not persistence_disabled and "schema" not in persistence_section.lower():
        errors.append("persistence is enabled but no schema version/evolution rule is stated")
    if errors:
        print("CONTRACT INVALID")
        for error in errors:
            print(f"- {error}")
        return 1
    print("CONTRACT VALID")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
