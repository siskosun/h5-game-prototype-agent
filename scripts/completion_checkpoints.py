#!/usr/bin/env python3
"""Validate a game's player-path checkpoint evidence and changed-file impact.

This validates evidence identities and consistency, NOT the underlying gameplay.
Browser/engine automation must produce actual trace files and independently
confirm the observed behavior before marking a checkpoint PASS.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import re

IDENTIFIER = re.compile(r"^[a-zA-Z][a-zA-Z0-9_-]{0,63}$")
SHA256 = re.compile(r"^[0-9a-f]{64}$")
STATUSES = {"PASS", "FAIL", "UNVERIFIED", "STALE"}
ORIGINS = {"OS_INPUT", "BROWSER_INPUT", "ENGINE_INPUT", "MODEL_CALL", "STATE_SETUP"}


class EvidenceError(ValueError):
    pass


def confined(root: pathlib.Path, relative: str) -> pathlib.Path:
    if not isinstance(relative, str) or not relative or "\\" in relative or ":" in relative:
        raise EvidenceError("invalid relative evidence path")
    part = pathlib.PurePosixPath(relative)
    if part.is_absolute() or any(p in (".", "..") for p in part.parts):
        raise EvidenceError("evidence path escapes workspace")
    candidate = root.joinpath(*part.parts)
    if candidate.is_symlink() or not candidate.resolve().is_relative_to(root.resolve()):
        raise EvidenceError("unsafe evidence file")
    return candidate


def verify(document: dict, root: pathlib.Path, *, changed=(), require_completion=False,
           expected_artifact=None) -> dict:
    if not isinstance(document, dict) or document.get("schema_version") != 1:
        raise EvidenceError("invalid schema version")
    artifact = document.get("artifact_sha256")
    if not isinstance(artifact, str) or not SHA256.fullmatch(artifact):
        raise EvidenceError("missing exact artifact identity")
    if expected_artifact is not None and expected_artifact != artifact:
        raise EvidenceError("artifact identity mismatch")
    steps = document.get("checkpoints")
    if not isinstance(steps, list) or not steps or len(steps) > 256:
        raise EvidenceError("invalid checkpoint list")
    entries = {}
    order = []
    errors = []
    for pos, item in enumerate(steps):
        if not isinstance(item, dict):
            raise EvidenceError(f"checkpoint {pos} must be an object")
        cid = item.get("id")
        if not isinstance(cid, str) or not IDENTIFIER.fullmatch(cid) or cid in entries:
            raise EvidenceError("duplicate or invalid checkpoint id")
        prior = item.get("requires", [])
        if not isinstance(prior, list) or any(not isinstance(x, str) or x not in entries for x in prior) or len(set(prior)) != len(prior):
            raise EvidenceError(f"checkpoint {cid}: requires unknown or later checkpoint")
        src = item.get("source_files", [])
        if not isinstance(src, list) or any(not isinstance(x, str) for x in src):
            raise EvidenceError(f"checkpoint {cid}: invalid source files")
        for f in src:
            confined(root, f)  # validates relative path, file need not exist in archive
        status = item.get("status")
        origin = item.get("input_origin")
        if status not in STATUSES or origin not in ORIGINS:
            raise EvidenceError(f"checkpoint {cid}: invalid state/input provenance")
        evidence = item.get("evidence", [])
        if not isinstance(evidence, list):
            raise EvidenceError(f"checkpoint {cid}: invalid evidence list")
        if status == "PASS" and not evidence:
            errors.append(f"{cid}: PASS requires executed evidence")
        for entry in evidence:
            if not isinstance(entry, dict) or entry.get("type") not in ("input", "state", "screen", "log"):
                raise EvidenceError(f"checkpoint {cid}: invalid evidence type")
            path = confined(root, entry.get("path"))
            digest = entry.get("sha256")
            if not isinstance(digest, str) or not SHA256.fullmatch(digest):
                raise EvidenceError(f"checkpoint {cid}: evidence digest invalid")
            if status == "PASS":
                if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != digest:
                    errors.append(f"{cid}: evidence is missing or differs")
        if status == "PASS" and origin in ("MODEL_CALL", "STATE_SETUP") and item.get("normal_player_path"):
            errors.append(f"{cid}: direct state/model calls cannot prove normal player input")
        if status == "PASS" and any(entries[dep]["status"] != "PASS" for dep in prior):
            errors.append(f"{cid}: PASS depends on non-PASS checkpoint")
        entries[cid] = item
        order.append(cid)
    invalidated = set()
    changed_set = set()
    for f in changed:
        confined(root, f)
        changed_set.add(f)
    for cid in order:
        item = entries[cid]
        if set(item.get("source_files", [])) & changed_set or any(x in invalidated for x in item.get("requires", [])):
            invalidated.add(cid)
    required = [c for c in order if entries[c].get("required", True)]
    terminals = [c for c in required if entries[c].get("terminal")]
    if require_completion and not terminals:
        errors.append("at least one required terminal checkpoint is needed")
    if require_completion and not any(entries[c].get("normal_player_path") and entries[c].get("input_origin") in ("OS_INPUT", "BROWSER_INPUT", "ENGINE_INPUT") for c in order):
        errors.append("normal player input path is missing")
    if require_completion:
        for cid in required:
            if entries[cid]["status"] != "PASS" or cid in invalidated:
                errors.append(f"{cid}: required checkpoint not verified on current source")
    return {"status": "PASS" if not errors else "FAIL", "artifact_sha256": artifact,
            "checkpoints": len(steps), "required": len(required),
            "passed": len([c for c in required if entries[c]["status"] == "PASS" and c not in invalidated]),
            "invalidated": sorted(invalidated), "errors": errors,
            "assurance": "EVIDENCE_INTEGRITY_ONLY_NOT_AUTONOMOUS_PLAY_PROOF"}


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("report", type=pathlib.Path)
    parser.add_argument("--root", type=pathlib.Path, default=pathlib.Path.cwd())
    parser.add_argument("--changed", action="append", default=[], help="relative source path that changed")
    parser.add_argument("--expected-artifact")
    parser.add_argument("--require-completion", action="store_true")
    args = parser.parse_args(argv)
    try:
        doc = json.loads(args.report.read_text(encoding="utf-8"))
        output = verify(doc,args.root.resolve(),changed=args.changed,require_completion=args.require_completion,
                        expected_artifact=args.expected_artifact)
    except (ValueError,OSError,UnicodeError) as exc:
        output = {"status":"FAIL","errors":[str(exc)]}
    print(json.dumps(output,ensure_ascii=False,indent=2))
    return 0 if output["status"]=="PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
