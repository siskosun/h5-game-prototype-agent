#!/usr/bin/env python3
"""Copy only reports and their referenced PNG/WebM evidence for CI upload."""
from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path, PurePosixPath

ROOT = Path(__file__).resolve().parents[1]
SCENARIOS = {
    "normal": "templates/probe",
    "spam-wins": "tests/fixtures/spam-wins",
    "spam-intended": "tests/fixtures/spam-intended",
}


def allowed_path(value: object, kind: str) -> PurePosixPath:
    if not isinstance(value, str) or "\\" in value:
        raise ValueError(f"invalid {kind} path: {value!r}")
    path = PurePosixPath(value)
    folder, suffix = ("screenshots", ".png") if kind == "screenshot" else ("video", ".webm")
    if (
        len(path.parts) != 3
        or path.parts[:2] != (".probe", folder)
        or path.name.startswith(".")
        or path.suffix != suffix
        or path.as_posix() != value
    ):
        raise ValueError(f"path outside {kind} allowlist: {value!r}")
    return path


def stage(root: Path = ROOT) -> dict:
    output = root / "artifacts" / "probe-evidence"
    if output.exists():
        shutil.rmtree(output)
    output.mkdir(parents=True)
    manifest = {"schema_version": 1, "scenarios": {}, "errors": []}
    for name, source_dir in SCENARIOS.items():
        source = root / source_dir
        files = []
        manifest["scenarios"][name] = {"source_dir": source_dir, "files": files}

        def copy(relative: PurePosixPath) -> None:
            src = source.joinpath(*relative.parts)
            # Reject symlinks, including directory links, rather than copying their targets.
            if any(source.joinpath(*relative.parts[:i]).is_symlink() for i in range(len(relative.parts) + 1)):
                raise ValueError(f"symlink evidence: {relative}")
            data = src.read_bytes()
            if not data:
                raise ValueError(f"empty evidence: {relative}")
            dest = output / name / Path(*relative.parts[1:])
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(data)
            files.append({
                "source": f"{source_dir}/{relative}",
                "path": dest.relative_to(output).as_posix(),
                "size_bytes": len(data),
                "sha256": hashlib.sha256(data).hexdigest(),
            })

        try:
            copy(PurePosixPath(".probe/report.json"))
            # Parse the copied bytes, leaving the original report and verdicts untouched.
            report = json.loads((output / name / "report.json").read_text(encoding="utf-8"))
            if not isinstance(report, dict):
                raise ValueError("report must be an object")
            checks = report.get("checks")
            if not isinstance(checks, list) or not checks:
                raise ValueError("report has no checks")
        except (OSError, ValueError) as exc:
            manifest["errors"].append(f"{name}: {exc}")
            continue

        references = [(c.get("evidence") if isinstance(c, dict) else None, "screenshot") for c in checks]
        references.append((report.get("video"), "video"))
        copied = set()
        for value, kind in references:
            try:
                relative = allowed_path(value, kind)
                if relative not in copied:
                    copy(relative)
                    copied.add(relative)
            except (OSError, ValueError) as exc:
                manifest["errors"].append(f"{name}: {exc}")

    (output / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return manifest


def main() -> int:
    manifest = stage()
    for name, scenario in manifest["scenarios"].items():
        print(f"{name}: staged {len(scenario['files'])} files")
    for error in manifest["errors"]:
        print(f"ERROR: {error}")
    return 1 if manifest["errors"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
