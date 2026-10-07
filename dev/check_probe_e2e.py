#!/usr/bin/env python3
from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PYTHON = sys.executable
NPM = shutil.which("npm")
if not NPM:
    raise SystemExit("npm not found")


def run(argv: list[str], cwd: Path, expected: set[int] = {0}) -> subprocess.CompletedProcess[str]:
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
    if proc.returncode not in expected:
        raise SystemExit(f"unexpected exit={proc.returncode}: {argv}")
    return proc


def ensure_frozen(path: Path) -> None:
    check = run(
        [PYTHON, str(ROOT / "scripts" / "probe_card.py"), "check", "probe_card.md"],
        path,
        expected={0, 1},
    )
    if check.returncode == 1:
        run([PYTHON, str(ROOT / "scripts" / "probe_card.py"), "freeze", "probe_card.md"], path)
        run([PYTHON, str(ROOT / "scripts" / "probe_card.py"), "check", "probe_card.md"], path)


def report(path: Path) -> dict:
    return json.loads((path / ".probe" / "report.json").read_text(encoding="utf-8"))


def main() -> int:
    normal = ROOT / "templates" / "probe"
    bad = ROOT / "tests" / "fixtures" / "spam-wins"
    intended = ROOT / "tests" / "fixtures" / "spam-intended"
    # A failed rerun must not leave evidence from an earlier run looking current.
    for scenario in (normal, bad, intended):
        evidence = scenario / ".probe"
        if evidence.exists():
            shutil.rmtree(evidence)
    ensure_frozen(normal)
    run([NPM, "ci"], normal)
    run([NPM, "run", "probe:check"], normal)
    run(
        [
            PYTHON,
            str(ROOT / "scripts" / "validate_probe_report.py"),
            ".probe/report.json",
            "--card",
            "probe_card.md",
        ],
        normal,
    )
    if report(normal).get("agent_verdict") != "READY_FOR_PLAYTEST":
        raise SystemExit("normal probe must be READY_FOR_PLAYTEST")

    ensure_frozen(bad)
    run([NPM, "ci"], bad)
    run([NPM, "run", "probe:check"], bad, expected={1})
    bad_report = report(bad)
    spam = next(c for c in bad_report["checks"] if c["name"] == "degenerate_spam")
    if bad_report.get("agent_verdict") != "MACHINE_REJECT" or spam.get("status") != "FAIL":
        raise SystemExit("spam-wins fixture was not rejected")

    ensure_frozen(intended)
    run([NPM, "ci"], intended)
    run([NPM, "run", "probe:check"], intended)
    intended_report = report(intended)
    spam = next(c for c in intended_report["checks"] if c["name"] == "degenerate_spam")
    if intended_report.get("agent_verdict") == "MACHINE_REJECT" or spam.get("status") != "PASS":
        raise SystemExit("intended spam strategy was incorrectly rejected")

    print("PROBE_E2E_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
