#!/usr/bin/env python3
from __future__ import annotations
import re
import sys
from pathlib import Path

TARGETS = {"LOCALHOST_URL", "ZIP_BUNDLE", "SINGLE_HTML"}
REQUIRED = [
    "DeliveryTarget",
    "Final artifact / server root name",
    "Root entrypoint",
    "Runtime network dependency allowed",
    "Exact open/start instructions",
    "Final smoke method",
    "QA evidence path",
]


def field(text: str, label: str) -> str | None:
    match = re.search(rf"(?mi)^\s*-?\s*{re.escape(label)}\s*:\s*(.+?)\s*$", text)
    return match.group(1).strip() if match else None


def unresolved(value: str | None) -> bool:
    return not value or value in {"-", "TBD", "TODO", "<fill>"}


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: validate_delivery.py <delivery_contract.md>")
        return 2
    path = Path(sys.argv[1])
    if not path.exists():
        print(f"DELIVERY CONTRACT INVALID\n- missing file: {path}")
        return 2
    text = path.read_text(encoding="utf-8")
    errors: list[str] = []
    for label in REQUIRED:
        if unresolved(field(text, label)):
            errors.append(f"missing or unresolved field: {label}")
    target_raw = field(text, "DeliveryTarget") or ""
    target = next((x for x in TARGETS if re.search(rf"\b{x}\b", target_raw)), None)
    if target is None:
        errors.append("DeliveryTarget must be LOCALHOST_URL, ZIP_BUNDLE, or SINGLE_HTML")
    entry = field(text, "Root entrypoint") or ""
    artifact = field(text, "Final artifact / server root name") or ""
    if target == "LOCALHOST_URL":
        root = field(text, "Server root")
        url = field(text, "Expected local URL") or ""
        if unresolved(root) or root == "N/A":
            errors.append("LOCALHOST_URL requires a concrete Server root")
        if not re.match(r"^http://127\.0\.0\.1(?::\d+)?(?:/|$)", url):
            errors.append("LOCALHOST_URL requires Expected local URL on http://127.0.0.1")
        if "index.html" not in entry:
            errors.append("LOCALHOST_URL requires a root HTML entrypoint")
    if target == "ZIP_BUNDLE":
        if not artifact.lower().endswith(".zip"):
            errors.append("ZIP_BUNDLE requires a .zip final artifact name")
        start = field(text, "ZIP start method")
        if unresolved(start) or start == "N/A":
            errors.append("ZIP_BUNDLE requires a ZIP start method")
    if target == "SINGLE_HTML":
        single = field(text, "Single HTML file") or artifact
        if not single.lower().endswith(".html"):
            errors.append("SINGLE_HTML requires a .html file name")
    if errors:
        print("DELIVERY CONTRACT INVALID")
        for error in errors:
            print(f"- {error}")
        return 1
    print(f"DELIVERY CONTRACT VALID ({target})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
