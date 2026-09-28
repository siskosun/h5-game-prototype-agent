#!/usr/bin/env python3
from __future__ import annotations
import argparse
import hashlib
import json
import re
import zipfile
from pathlib import Path


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def sha256_tree(root: Path) -> tuple[str, int, int]:
    h = hashlib.sha256()
    files = sorted((p for p in root.rglob("*") if p.is_file()), key=lambda p: p.relative_to(root).as_posix())
    total = 0
    for path in files:
        rel = path.relative_to(root).as_posix().encode("utf-8")
        data = path.read_bytes()
        total += len(data)
        h.update(len(rel).to_bytes(8, "big"))
        h.update(rel)
        h.update(len(data).to_bytes(8, "big"))
        h.update(data)
    return h.hexdigest(), len(files), total


def validate_evidence(path: Path, digest: str, target: str, errors: list[str], report: dict[str, object]) -> None:
    if not path.exists():
        errors.append(f"evidence file missing: {path}")
        return
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        errors.append(f"invalid evidence json: {exc}")
        return
    report["evidence"] = str(path)
    if data.get("artifactSha256") != digest:
        errors.append("QA evidence artifactSha256 does not match the final result")
    if data.get("completedLoop") is not True:
        errors.append("QA evidence does not confirm completedLoop=true")
    for key in ("consoleErrors", "pageErrors", "networkFailures", "blockedInputs"):
        if data.get(key, []):
            errors.append(f"QA evidence {key} is non-zero/non-empty")
    if target == "LOCALHOST_URL":
        url = str(data.get("testedUrl", ""))
        if not re.match(r"^http://127\.0\.0\.1(?::\d+)?(?:/|$)", url):
            errors.append("LOCALHOST_URL evidence must record a testedUrl on http://127.0.0.1")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("artifact")
    parser.add_argument("--target", required=True, choices=["LOCALHOST_URL", "ZIP_BUNDLE", "SINGLE_HTML"])
    parser.add_argument("--evidence")
    args = parser.parse_args()

    artifact = Path(args.artifact)
    errors: list[str] = []
    report: dict[str, object] = {"artifact": str(artifact), "target": args.target}

    if not artifact.exists():
        print("RELEASE ARTIFACT INVALID\n- artifact missing")
        return 1

    digest = ""
    if args.target == "LOCALHOST_URL":
        if not artifact.is_dir():
            errors.append("LOCALHOST_URL artifact must be the frozen server-root directory")
        else:
            if not (artifact / "index.html").is_file():
                errors.append("LOCALHOST_URL server root missing index.html")
            digest, count, total = sha256_tree(artifact)
            report["fileCount"] = count
            report["size"] = total

    elif args.target == "ZIP_BUNDLE":
        if not artifact.is_file() or artifact.suffix.lower() != ".zip":
            errors.append("ZIP_BUNDLE artifact must be a .zip file")
        else:
            try:
                with zipfile.ZipFile(artifact) as zf:
                    bad = zf.testzip()
                    if bad:
                        errors.append(f"corrupt ZIP member: {bad}")
                    names = {name.rstrip("/") for name in zf.namelist() if name and not name.endswith("/")}
                    if "index.html" not in names:
                        errors.append("ZIP_BUNDLE requires root index.html")
                    report["files"] = len(names)
            except zipfile.BadZipFile:
                errors.append("invalid ZIP")
            digest = sha256_file(artifact)
            report["size"] = artifact.stat().st_size

    elif args.target == "SINGLE_HTML":
        if not artifact.is_file() or artifact.suffix.lower() != ".html":
            errors.append("SINGLE_HTML artifact must be a .html file")
        else:
            text = artifact.read_text(encoding="utf-8", errors="replace")
            if "<html" not in text.lower() or "<script" not in text.lower():
                errors.append("SINGLE_HTML does not look like a runnable HTML document")
            forbidden = {
                "external script": r"<script[^>]+src\s*=\s*['\"]https?://",
                "external stylesheet": r"<link[^>]+href\s*=\s*['\"]https?://",
                "runtime fetch": r"\bfetch\s*\(",
                "ES module": r"<script[^>]+type\s*=\s*['\"]module['\"]",
            }
            found = [label for label, pattern in forbidden.items() if re.search(pattern, text, flags=re.I)]
            if found:
                errors.append("SINGLE_HTML contains non-self-contained dependency patterns: " + ", ".join(found))
            digest = sha256_file(artifact)
            report["size"] = artifact.stat().st_size

    report["sha256"] = digest
    report["runtimeSmoke"] = "NOT_EXECUTED_BY_STATIC_VALIDATOR"

    if args.evidence and digest:
        validate_evidence(Path(args.evidence), digest, args.target, errors, report)

    print(json.dumps(report, ensure_ascii=False, indent=2))
    if errors:
        print("RELEASE ARTIFACT INVALID")
        for error in errors:
            print(f"- {error}")
        return 1
    if args.evidence:
        print("RELEASE ARTIFACT PASS; evidence hash matches the exact final result")
    else:
        print("RELEASE ARTIFACT STATIC PASS; runtime smoke/evidence binding still required")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
