#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
from pathlib import Path

AGENT = {"READY_FOR_PLAYTEST", "MACHINE_REJECT", "UNCERTAIN"}
HUMAN = {"PENDING", "PASS", "REJECT", "UNCERTAIN"}
FAILURE = {"MECHANIC", "IMPLEMENTATION", "PRESENTATION", "HARNESS", ""}
REQUIRED = [
    "probe_id", "date", "title", "hypothesis", "kill_criteria",
    "agent_verdict", "human_verdict", "final_status", "failure_class",
    "reason", "revisit_when", "repo_path", "source_sha",
]


def read_rows(path: Path) -> list[dict]:
    if not path.exists():
        return []
    rows: list[dict] = []
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ValueError(f"line {number}: invalid JSON: {exc}") from exc
        if not isinstance(row, dict):
            raise ValueError(f"line {number}: expected object")
        rows.append(row)
    return rows


def validate_row(row: dict) -> list[str]:
    errors = [f"missing {key}" for key in REQUIRED if key not in row]
    if row.get("agent_verdict") not in AGENT:
        errors.append("invalid agent_verdict")
    if row.get("human_verdict") not in HUMAN:
        errors.append("invalid human_verdict")
    if row.get("failure_class", "") not in FAILURE:
        errors.append("invalid failure_class")
    return errors


def final_status(agent: str, human: str) -> str:
    if agent == "MACHINE_REJECT":
        return "REJECT"
    if human == "PENDING":
        return "WAITING_FOR_PLAYTEST"
    return human


def write_rows(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = "".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows)
    path.write_text(text, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--file", type=Path, default=Path("probes.jsonl"))
    sub = parser.add_subparsers(dest="command", required=True)
    add = sub.add_parser("add"); add.add_argument("--json", type=Path, required=True)
    update = sub.add_parser("update"); update.add_argument("probe_id"); update.add_argument("--human-verdict", choices=sorted(HUMAN)); update.add_argument("--playtest-record", type=Path); update.add_argument("--agent-verdict", choices=sorted(AGENT)); update.add_argument("--failure-class", choices=sorted(FAILURE)); update.add_argument("--reason"); update.add_argument("--revisit-when")
    search = sub.add_parser("search"); search.add_argument("keyword")
    listing = sub.add_parser("list"); listing.add_argument("--status")
    sub.add_parser("validate")
    args = parser.parse_args()
    try:
        rows = read_rows(args.file)
    except (OSError, ValueError) as exc:
        print(str(exc), file=sys.stderr); return 2
    if args.command == "add":
        row = json.loads(args.json.read_text(encoding="utf-8")); row.setdefault("date", dt.date.today().isoformat()); row["final_status"] = final_status(row.get("agent_verdict", ""), row.get("human_verdict", "PENDING")); errors = validate_row(row)
        if errors: print("; ".join(errors), file=sys.stderr); return 2
        if any(existing.get("probe_id") == row["probe_id"] for existing in rows): print("duplicate probe_id", file=sys.stderr); return 3
        rows.append(row); write_rows(args.file, rows); print(row["probe_id"]); return 0
    if args.command == "update":
        target = next((row for row in rows if row.get("probe_id") == args.probe_id), None)
        if target is None: print("probe not found", file=sys.stderr); return 4
        if args.human_verdict and args.human_verdict != "PENDING":
            if not args.playtest_record or not args.playtest_record.exists(): print("human verdict requires an existing playtest record path", file=sys.stderr); return 5
            target["human_verdict"] = args.human_verdict; target["playtest_record"] = str(args.playtest_record)
        elif args.human_verdict: target["human_verdict"] = args.human_verdict
        if args.agent_verdict: target["agent_verdict"] = args.agent_verdict
        if args.failure_class is not None: target["failure_class"] = args.failure_class
        if args.reason is not None: target["reason"] = args.reason
        if args.revisit_when is not None: target["revisit_when"] = args.revisit_when
        target["final_status"] = final_status(target["agent_verdict"], target["human_verdict"]); errors = validate_row(target)
        if errors: print("; ".join(errors), file=sys.stderr); return 2
        write_rows(args.file, rows); print(target["final_status"]); return 0
    if args.command == "search":
        key = args.keyword.casefold(); [print(json.dumps(row, ensure_ascii=False)) for row in rows if key in json.dumps(row, ensure_ascii=False).casefold()]; return 0
    if args.command == "list":
        [print(json.dumps(row, ensure_ascii=False)) for row in rows if not args.status or row.get("final_status") == args.status]; return 0
    errors=[]; ids=set()
    for row in rows:
        errors.extend(f"{row.get('probe_id','?')}: {e}" for e in validate_row(row)); pid=row.get("probe_id"); errors.extend([f"duplicate probe_id: {pid}"] if pid in ids else []); ids.add(pid)
    if errors: print("\n".join(errors), file=sys.stderr); return 2
    print(f"VALID rows={len(rows)}"); return 0

if __name__ == "__main__":
    raise SystemExit(main())
