#!/usr/bin/env python3
"""Hash PROBE working-source bytes; advisory only, never trusted Candidate evidence.

The digest excludes generated evidence/build directories but includes untracked source.
Only top-level generated directories are excluded; nested names remain source-visible.
Both this module and the PROBE Node runner use UTF-8 bytewise name ordering and
SHA256(path + NUL + file bytes + NUL) in depth-first traversal order.
"""
from __future__ import annotations

import hashlib
from pathlib import Path

SOURCE_EXCLUDES = frozenset({".git", ".probe", "dist", "node_modules", "artifacts", "coverage", ".cache", ".venv"})


def source_tree_sha256(source_root: Path) -> str:
    root = Path(source_root)
    if root.is_symlink():
        raise ValueError("source root is a symlink")
    root = root.resolve(strict=True)
    if not root.is_dir():
        raise ValueError("source root must be a directory")

    digest = hashlib.sha256()

    def visit(directory: Path) -> None:
        for path in sorted(directory.iterdir(), key=lambda child: child.name.encode("utf-8")):
            if directory == root and path.name in SOURCE_EXCLUDES:
                continue
            relative = path.relative_to(root).as_posix()
            if path.is_symlink():
                raise ValueError(f"source tree contains symlink: {relative}")
            if path.is_dir():
                visit(path)
            elif path.is_file():
                digest.update(relative.encode("utf-8"))
                digest.update(b"\x00")
                with path.open("rb") as infile:
                    while chunk := infile.read(1024 * 1024):
                        digest.update(chunk)
                digest.update(b"\x00")
            else:
                raise ValueError(f"unsupported source tree entry: {relative}")

    visit(root)
    return digest.hexdigest()
