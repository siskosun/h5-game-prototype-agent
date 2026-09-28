#!/usr/bin/env python3
from __future__ import annotations
import json
import sys
from pathlib import Path

REQUIRED = ["id", "sourceFile", "runtimePath", "type", "role", "loader", "expectedScreen", "expectedNode", "required"]


def main() -> int:
    if len(sys.argv) not in (2, 3):
        print("usage: validate_asset_manifest.py <asset_manifest.json> [project-root]")
        return 2
    manifest_path = Path(sys.argv[1])
    project_root = Path(sys.argv[2]) if len(sys.argv) == 3 else manifest_path.parent.parent
    if not manifest_path.exists():
        print(f"ERROR: missing file: {manifest_path}")
        return 2
    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    assets = data.get("assets")
    errors: list[str] = []
    if not isinstance(assets, list):
        errors.append("assets must be a list")
        assets = []
    ids: set[str] = set()
    for i, asset in enumerate(assets):
        if not isinstance(asset, dict):
            errors.append(f"asset[{i}] must be object")
            continue
        missing = [k for k in REQUIRED if k not in asset]
        if missing:
            errors.append(f"asset[{i}] missing fields: {', '.join(missing)}")
        aid = str(asset.get("id", ""))
        if not aid:
            errors.append(f"asset[{i}] empty id")
        elif aid in ids:
            errors.append(f"duplicate asset id: {aid}")
        ids.add(aid)
        if asset.get("required") and asset.get("sourceFile"):
            source = Path(str(asset["sourceFile"]))
            if not source.is_absolute():
                source = project_root / source
            if not source.exists():
                errors.append(f"required source file missing for {aid}: {source}")
    if errors:
        print("ASSET MANIFEST INVALID")
        for e in errors:
            print(f"- {e}")
        return 1
    print(f"ASSET MANIFEST VALID ({len(assets)} assets)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
