#!/usr/bin/env python3
from pathlib import Path
import sys

DIRS = ["research", "spec", "game", "tests", "logs", "release"]


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: init_workspace.py <workspace-dir>")
        return 2
    root = Path(sys.argv[1])
    root.mkdir(parents=True, exist_ok=True)
    for name in DIRS:
        (root / name).mkdir(exist_ok=True)
    (root / "logs" / "experiments.jsonl").touch(exist_ok=True)
    progress = root / "progress.md"
    if not progress.exists():
        progress.write_text(
            "# Progress\n\n"
            "Skill version: 0.1\n\n"
            "TaskMode: <NEW_BUILD|FEATURE_CHANGE|BUGFIX|POLISH_QA|RELEASE>\n\n"
            "## Current goal\n<fill>\n\n"
            "## Verified state\n<fill as work progresses>\n\n"
            "## Next default action\n<fill>\n",
            encoding="utf-8",
        )
    print(root)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
