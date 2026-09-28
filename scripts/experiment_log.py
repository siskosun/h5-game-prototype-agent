#!/usr/bin/env python3
from __future__ import annotations
import argparse
import json
from datetime import datetime, timezone
from pathlib import Path


def log_path(workspace: str) -> Path:
    p = Path(workspace) / "logs" / "experiments.jsonl"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.touch(exist_ok=True)
    return p


def read_events(path: Path) -> list[dict]:
    out = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            out.append(json.loads(line))
        except json.JSONDecodeError:
            raise SystemExit(f"ERROR: malformed JSONL in {path}")
    return out


def next_id(events: list[dict]) -> str:
    nums = []
    for e in events:
        eid = str(e.get("id", ""))
        if eid.startswith("E") and eid[1:].isdigit():
            nums.append(int(eid[1:]))
    return f"E{(max(nums) + 1 if nums else 1):03d}"


def append(path: Path, obj: dict) -> None:
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(obj, ensure_ascii=False) + "\n")


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def cmd_begin(a: argparse.Namespace) -> int:
    path = log_path(a.workspace)
    events = read_events(path)
    eid = next_id(events)
    signature = {"phase": a.phase, "hypothesis": a.hypothesis.strip(), "change": a.change.strip(), "setup": a.setup.strip()}
    prior = [e for e in events if e.get("event") == "begin" and e.get("signature") == signature]
    if prior and not a.allow_repeat:
        print(f"ERROR: exact experiment signature already exists as {prior[-1].get('id')}; use --allow-repeat only for an intentional retest")
        return 1
    append(path, {
        "event": "begin", "id": eid, "time": now(), "phase": a.phase,
        "hypothesis": a.hypothesis, "change": a.change, "setup": a.setup,
        "expected": a.expected, "commit": a.commit, "diffSummary": a.diff, "signature": signature,
    })
    print(eid)
    return 0


def cmd_finish(a: argparse.Namespace) -> int:
    path = log_path(a.workspace)
    events = read_events(path)
    begins = [e for e in events if e.get("event") == "begin" and e.get("id") == a.id]
    if not begins:
        print(f"ERROR: unknown experiment id: {a.id}")
        return 1
    if any(e.get("event") == "finish" and e.get("id") == a.id for e in events):
        print(f"ERROR: experiment already finished: {a.id}")
        return 1
    append(path, {
        "event": "finish", "id": a.id, "time": now(), "outcome": a.outcome,
        "classification": a.classification, "evidence": a.evidence, "next": a.next,
    })
    print(a.id)
    return 0


def cmd_recent(a: argparse.Namespace) -> int:
    path = log_path(a.workspace)
    events = read_events(path)
    for e in events[-a.limit:]:
        print(json.dumps(e, ensure_ascii=False))
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)

    b = sub.add_parser("begin")
    b.add_argument("workspace")
    b.add_argument("--phase", required=True)
    b.add_argument("--hypothesis", required=True)
    b.add_argument("--change", required=True)
    b.add_argument("--setup", default="")
    b.add_argument("--expected", default="")
    b.add_argument("--commit", default="")
    b.add_argument("--diff", default="")
    b.add_argument("--allow-repeat", action="store_true")
    b.set_defaults(func=cmd_begin)

    f = sub.add_parser("finish")
    f.add_argument("workspace")
    f.add_argument("--id", required=True)
    f.add_argument("--outcome", required=True, choices=["PASS", "FAIL", "PARTIAL", "INVALID"])
    f.add_argument("--classification", default="")
    f.add_argument("--evidence", default="")
    f.add_argument("--next", default="")
    f.set_defaults(func=cmd_finish)

    r = sub.add_parser("recent")
    r.add_argument("workspace")
    r.add_argument("--limit", type=int, default=10)
    r.set_defaults(func=cmd_recent)

    a = ap.parse_args()
    return a.func(a)


if __name__ == "__main__":
    raise SystemExit(main())
