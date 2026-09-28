#!/usr/bin/env python3
from __future__ import annotations

import argparse
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUNTIME_TOP = {"SKILL.md", "VERSION", "agents", "assets", "references", "scripts", "templates"}
EXCLUDED_DIRS = {"__pycache__", "node_modules", "dist", ".prototype", ".probe", ".git"}
EXCLUDED_FILES = {"probes.jsonl"}

def include(path: Path) -> bool:
    rel = path.relative_to(ROOT)
    parts = rel.parts
    if not parts or parts[0] not in RUNTIME_TOP:
        return False
    if any(part in EXCLUDED_DIRS for part in parts):
        return False
    if path.name in EXCLUDED_FILES or path.name.startswith("ut-") or path.suffix in {".pyc", ".log"}:
        return False
    return path.is_file()

def build(out: Path) -> list[str]:
    files = sorted((p for p in ROOT.rglob("*") if include(p)), key=lambda p: p.relative_to(ROOT).as_posix())
    names = [p.relative_to(ROOT).as_posix() for p in files]
    required = {"SKILL.md", "VERSION", "agents/openai.yaml"}
    missing = required - set(names)
    if missing:
        raise SystemExit(f"missing required runtime files: {sorted(missing)}")
    out.parent.mkdir(parents=True, exist_ok=True)
    if out.exists():
        out.unlink()
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as archive:
        for path, name in zip(files, names):
            archive.write(path, name)
    return names

def main() -> int:
    parser = argparse.ArgumentParser(description="Build runtime-only skill.zip.")
    parser.add_argument("--out", default="dist/skill.zip")
    args = parser.parse_args()
    out = (ROOT / args.out).resolve() if not Path(args.out).is_absolute() else Path(args.out).resolve()
    names = build(out)
    print(f"built: {out}")
    print(f"files: {len(names)}")
    for name in names:
        print(name)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
