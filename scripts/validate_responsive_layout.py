#!/usr/bin/env python3
from __future__ import annotations
import json
import sys
from pathlib import Path

DEFAULT_VIEWPORTS = {(360, 800), (390, 844)}


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: validate_responsive_layout.py <layout_report.json>")
        return 2
    path = Path(sys.argv[1])
    data = json.loads(path.read_text(encoding="utf-8"))
    rows = data.get("viewports", [])
    errors: list[str] = []
    if data.get("requireDefaultMobileViewports", True):
        seen = {(int(r.get("width", 0)), int(r.get("height", 0))) for r in rows}
        for vp in DEFAULT_VIEWPORTS - seen:
            errors.append(f"missing required viewport: {vp[0]}x{vp[1]}")
    for row in rows:
        name = f"{row.get('width')}x{row.get('height')}"
        if row.get("horizontalOverflow", 0) not in (0, False, None):
            errors.append(f"{name}: horizontal overflow")
        if row.get("criticalObjectsVisible") is not True:
            errors.append(f"{name}: critical gameplay objects not all visible")
        if row.get("primaryGesturePass") is not True:
            errors.append(f"{name}: primary gesture failed or conflicts with page behavior")
        if row.get("rolesLegible") not in (True, "N/A"):
            errors.append(f"{name}: mechanically distinct roles not proven legible")
        min_target = row.get("minTapTarget")
        if isinstance(min_target, (int, float)) and min_target < 44:
            errors.append(f"{name}: min tap target <44")
    if errors:
        print("RESPONSIVE LAYOUT FAILED")
        for error in errors:
            print(f"- {error}")
        return 1
    print("RESPONSIVE LAYOUT PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
