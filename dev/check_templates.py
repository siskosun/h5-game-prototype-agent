#!/usr/bin/env python3
from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def npm_executable() -> str:
    exe = shutil.which("npm")
    if not exe:
        raise SystemExit("npm not found")
    return exe


def run(argv: list[str], cwd: Path) -> None:
    proc = subprocess.run(
        argv,
        cwd=cwd,
        text=True,
        encoding="utf-8",
        errors="replace",
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    console_encoding = sys.stdout.encoding or "utf-8"
    safe = proc.stdout.encode(console_encoding, errors="replace").decode(console_encoding, errors="replace")
    print(safe, end="")
    if proc.returncode:
        raise SystemExit(proc.returncode)


def check_template(name: str) -> None:
    path = ROOT / "templates" / name
    npm = npm_executable()
    run([npm, "ci"], path)
    run([npm, "test"], path)
    run([npm, "run", "build"], path)
    index = path / "dist" / "index.html"
    if not index.is_file():
        raise SystemExit(f"{name}: missing dist/index.html")
    js = "\n".join(
        file.read_text(encoding="utf-8", errors="replace")
        for file in (path / "dist").rglob("*.js")
    )
    if "__GAME_API__" in js:
        raise SystemExit(f"{name}: production build leaked __GAME_API__")
    print(f"TEMPLATE_OK {name}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("templates", nargs="*", default=["dom", "phaser", "probe"])
    args = parser.parse_args()
    for name in args.templates:
        check_template(name)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
