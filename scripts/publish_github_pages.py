#!/usr/bin/env python3
"""Publish an immutable static playable to GitHub Pages using the authenticated gh CLI."""
from __future__ import annotations

import argparse
import base64
import hashlib
import html
import json
import re
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

API_VERSION = "2026-03-10"
DEFAULT_BRANCH = "gh-pages"
SAFE_VERSION_RE = re.compile(r"[A-Za-z0-9._-]{1,96}")
REPO_RE = re.compile(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+")
MAX_BLOB_BYTES = 95 * 1024 * 1024


class PublishError(RuntimeError):
    pass


def _http_status(text: str) -> int | None:
    match = re.search(r"(?:HTTP|status[^0-9]*)\s*([45][0-9]{2})", text, re.I)
    return int(match.group(1)) if match else None


def gh_api(
    endpoint: str,
    *,
    method: str = "GET",
    payload: dict[str, Any] | None = None,
    allow_statuses: set[int] | None = None,
) -> Any:
    gh = shutil.which("gh")
    if not gh:
        raise PublishError("GitHub CLI (gh) is required")
    argv = [
        gh,
        "api",
        endpoint,
        "--method",
        method,
        "-H",
        "Accept: application/vnd.github+json",
        "-H",
        f"X-GitHub-Api-Version: {API_VERSION}",
    ]
    data = None
    if payload is not None:
        argv.extend(["--input", "-"])
        data = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    proc = subprocess.run(
        argv,
        input=data,
        text=True,
        encoding="utf-8",
        errors="replace",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if proc.returncode:
        combined = (proc.stdout + "\n" + proc.stderr).strip()
        status = _http_status(combined)
        if allow_statuses and status in allow_statuses:
            return {"_http_status": status}
        raise PublishError(
            f"GitHub API failed for {endpoint}: {combined[-2000:] or proc.returncode}"
        )
    raw = proc.stdout.strip()
    if not raw:
        return {}
    try:
        return json.loads(raw)
    except json.JSONDecodeError as exc:
        raise PublishError(f"GitHub API returned invalid JSON for {endpoint}") from exc


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def collect_payload(root: Path) -> list[tuple[str, Path]]:
    root = root.expanduser().resolve()
    if not root.is_dir():
        raise PublishError(f"source directory not found: {root}")
    index = root / "index.html"
    if not index.is_file():
        raise PublishError("source directory must contain index.html")
    rows: list[tuple[str, Path]] = []
    for path in sorted(root.rglob("*")):
        if path.is_symlink():
            raise PublishError(f"symlinks are not allowed in published payload: {path}")
        if not path.is_file():
            continue
        rel = path.relative_to(root).as_posix()
        if rel == "_game_exp_build.json":
            raise PublishError("source must not contain reserved _game_exp_build.json")
        size = path.stat().st_size
        if size > MAX_BLOB_BYTES:
            raise PublishError(
                f"file exceeds safe GitHub blob size ({MAX_BLOB_BYTES} bytes): {rel}"
            )
        rows.append((rel, path))
    if not rows:
        raise PublishError("source directory is empty")
    return rows


def payload_sha256(files: list[tuple[str, Path]]) -> str:
    digest = hashlib.sha256()
    for rel, path in files:
        size = path.stat().st_size
        file_digest = _sha256_file(path)
        digest.update(rel.encode("utf-8"))
        digest.update(b"\0")
        digest.update(str(size).encode("ascii"))
        digest.update(b"\0")
        digest.update(file_digest.encode("ascii"))
        digest.update(b"\n")
    return digest.hexdigest()


def validate_relative_entrypoint(index: Path) -> None:
    text = index.read_text(encoding="utf-8", errors="replace")
    if re.search(r"""(?i)(?:src|href)\s*=\s*["']/(?!/)""", text):
        raise PublishError(
            "index.html contains root-absolute src/href paths; build with relative assets "
            "(for Vite use base: './') before publishing to a versioned Pages path"
        )


def generated_files(
    *,
    version_key: str,
    payload_digest: str,
    file_count: int,
    producer: str,
) -> dict[str, bytes]:
    version_path = f"play/{version_key}/"
    marker = {
        "schema_version": 1,
        "version_key": version_key,
        "payload_sha256": payload_digest,
        "file_count": file_count,
        "producer": producer,
        "path": version_path,
    }
    latest = {
        "schema_version": 1,
        "version_key": version_key,
        "payload_sha256": payload_digest,
        "path": version_path,
    }
    escaped = html.escape(version_path, quote=True)
    root_index = (
        "<!doctype html><meta charset=\"utf-8\">"
        "<meta name=\"viewport\" content=\"width=device-width,initial-scale=1\">"
        f"<meta http-equiv=\"refresh\" content=\"0; url=./{escaped}\">"
        "<title>Playable</title>"
        f"<p><a href=\"./{escaped}\">Open latest playable</a></p>"
        f"<script>location.replace('./{escaped}')</script>"
    ).encode("utf-8")
    return {
        ".nojekyll": b"",
        "index.html": root_index,
        "latest.json": (json.dumps(latest, ensure_ascii=False, sort_keys=True) + "\n").encode("utf-8"),
        f"{version_path}_game_exp_build.json": (
            json.dumps(marker, ensure_ascii=False, sort_keys=True) + "\n"
        ).encode("utf-8"),
    }


def _blob(repo: str, content: bytes) -> str:
    result = gh_api(
        f"repos/{repo}/git/blobs",
        method="POST",
        payload={
            "content": base64.b64encode(content).decode("ascii"),
            "encoding": "base64",
        },
    )
    sha = result.get("sha") if isinstance(result, dict) else None
    if not isinstance(sha, str):
        raise PublishError("GitHub did not return a blob sha")
    return sha


def _branch_state(repo: str, branch: str) -> tuple[str, str] | None:
    ref = gh_api(
        f"repos/{repo}/git/ref/heads/{urllib.parse.quote(branch, safe='')}",
        allow_statuses={404},
    )
    if isinstance(ref, dict) and ref.get("_http_status") == 404:
        return None
    obj = ref.get("object") if isinstance(ref, dict) else None
    commit_sha = obj.get("sha") if isinstance(obj, dict) else None
    if not isinstance(commit_sha, str):
        raise PublishError("invalid Pages branch ref response")
    commit = gh_api(f"repos/{repo}/git/commits/{commit_sha}")
    tree = commit.get("tree") if isinstance(commit, dict) else None
    tree_sha = tree.get("sha") if isinstance(tree, dict) else None
    if not isinstance(tree_sha, str):
        raise PublishError("invalid Pages branch commit response")
    return commit_sha, tree_sha


def _contents(repo: str, branch: str, path: str) -> Any | None:
    endpoint = (
        f"repos/{repo}/contents/{urllib.parse.quote(path, safe='/')}"
        f"?ref={urllib.parse.quote(branch, safe='')}"
    )
    result = gh_api(endpoint, allow_statuses={404})
    if isinstance(result, dict) and result.get("_http_status") == 404:
        return None
    return result


def existing_marker(repo: str, branch: str, version_key: str) -> dict[str, Any] | None:
    result = _contents(repo, branch, f"play/{version_key}/_game_exp_build.json")
    if result is None:
        return None
    if not isinstance(result, dict) or result.get("encoding") != "base64":
        raise PublishError("existing publish marker has unexpected GitHub representation")
    raw = result.get("content")
    if not isinstance(raw, str):
        raise PublishError("existing publish marker is unreadable")
    try:
        decoded = base64.b64decode(raw).decode("utf-8")
        value = json.loads(decoded)
    except Exception as exc:
        raise PublishError("existing publish marker is invalid") from exc
    if not isinstance(value, dict):
        raise PublishError("existing publish marker must be a JSON object")
    return value


def _create_tree(repo: str, base_tree: str | None, entries: list[dict[str, str]]) -> str:
    payload: dict[str, Any] = {"tree": entries}
    if base_tree is not None:
        payload["base_tree"] = base_tree
    result = gh_api(f"repos/{repo}/git/trees", method="POST", payload=payload)
    sha = result.get("sha") if isinstance(result, dict) else None
    if not isinstance(sha, str):
        raise PublishError("GitHub did not return a tree sha")
    return sha


def _create_commit(repo: str, tree_sha: str, parent: str | None, message: str) -> str:
    payload: dict[str, Any] = {
        "message": message,
        "tree": tree_sha,
        "parents": [parent] if parent else [],
    }
    result = gh_api(f"repos/{repo}/git/commits", method="POST", payload=payload)
    sha = result.get("sha") if isinstance(result, dict) else None
    if not isinstance(sha, str):
        raise PublishError("GitHub did not return a commit sha")
    return sha


def update_pages_branch(
    repo: str,
    branch: str,
    entries: list[dict[str, str]],
    *,
    message: str,
    attempts: int = 3,
) -> str:
    last_error: Exception | None = None
    for _ in range(attempts):
        state = _branch_state(repo, branch)
        parent = state[0] if state else None
        base_tree = state[1] if state else None
        tree_sha = _create_tree(repo, base_tree, entries)
        commit_sha = _create_commit(repo, tree_sha, parent, message)
        try:
            if parent is None:
                gh_api(
                    f"repos/{repo}/git/refs",
                    method="POST",
                    payload={"ref": f"refs/heads/{branch}", "sha": commit_sha},
                )
            else:
                gh_api(
                    f"repos/{repo}/git/refs/heads/{urllib.parse.quote(branch, safe='')}",
                    method="PATCH",
                    payload={"sha": commit_sha, "force": False},
                )
            return commit_sha
        except PublishError as exc:
            last_error = exc
            text = str(exc)
            if "422" not in text and "409" not in text and "fast forward" not in text.lower():
                raise
    raise PublishError(f"Pages branch changed concurrently: {last_error}")


def ensure_pages(repo: str, branch: str) -> dict[str, Any]:
    pages = gh_api(f"repos/{repo}/pages", allow_statuses={404})
    if isinstance(pages, dict) and pages.get("_http_status") == 404:
        pages = gh_api(
            f"repos/{repo}/pages",
            method="POST",
            payload={
                "build_type": "legacy",
                "source": {"branch": branch, "path": "/"},
            },
        )
    if not isinstance(pages, dict):
        raise PublishError("GitHub Pages response is invalid")
    source = pages.get("source")
    if not isinstance(source, dict):
        raise PublishError(
            "repository already uses a Pages configuration without a branch source; "
            "refusing to replace it automatically"
        )
    if source.get("branch") != branch or source.get("path") != "/":
        raise PublishError(
            "repository already has a different GitHub Pages source; "
            "refusing to reconfigure it automatically"
        )
    build_type = pages.get("build_type")
    if build_type not in (None, "legacy"):
        raise PublishError(
            f"repository Pages build type is {build_type!r}; refusing to replace it automatically"
        )
    html_url = pages.get("html_url")
    if not isinstance(html_url, str) or not html_url.startswith("https://"):
        raise PublishError("GitHub Pages did not provide an HTTPS site URL")
    return pages


def version_url(pages_html_url: str, version_key: str) -> str:
    base = pages_html_url.rstrip("/") + "/"
    return urllib.parse.urljoin(base, f"play/{version_key}/")


def verify_deployment(
    url: str,
    *,
    version_key: str,
    payload_digest: str,
    timeout_seconds: int,
) -> None:
    marker_url = urllib.parse.urljoin(url, "_game_exp_build.json")
    deadline = time.monotonic() + max(1, timeout_seconds)
    last_error = "not attempted"
    while time.monotonic() < deadline:
        probe = marker_url + "?v=" + payload_digest[:16]
        try:
            request = urllib.request.Request(
                probe,
                headers={
                    "User-Agent": "game-exp-playable-publisher/1",
                    "Cache-Control": "no-cache",
                },
            )
            with urllib.request.urlopen(request, timeout=10) as response:
                raw = response.read()
            marker = json.loads(raw.decode("utf-8"))
            if (
                marker.get("version_key") == version_key
                and marker.get("payload_sha256") == payload_digest
            ):
                index_request = urllib.request.Request(
                    url + "?v=" + payload_digest[:16],
                    headers={"User-Agent": "game-exp-playable-publisher/1"},
                )
                with urllib.request.urlopen(index_request, timeout=10) as response:
                    if not response.read(4096):
                        raise PublishError("published index.html is empty")
                return
            last_error = "served marker does not match this payload"
        except (OSError, ValueError, urllib.error.URLError, urllib.error.HTTPError, PublishError) as exc:
            last_error = str(exc)
        time.sleep(3)
    raise PublishError(
        f"GitHub Pages did not serve the expected immutable build before timeout: {last_error}"
    )


def publish(
    *,
    repo: str,
    source: Path,
    version_key: str,
    producer: str,
    branch: str = DEFAULT_BRANCH,
    require_relative_entrypoint: bool = False,
    wait: bool = True,
    timeout_seconds: int = 180,
) -> dict[str, Any]:
    if not REPO_RE.fullmatch(repo):
        raise PublishError("repo must be owner/name")
    if not SAFE_VERSION_RE.fullmatch(version_key):
        raise PublishError(
            "version-key must be 1-96 characters using letters, numbers, dot, underscore, or hyphen"
        )
    metadata = gh_api(f"repos/{repo}")
    if not isinstance(metadata, dict) or metadata.get("private") is not False:
        raise PublishError(
            "automatic GitHub Pages publishing is limited to public repositories"
        )
    files = collect_payload(source)
    if require_relative_entrypoint:
        validate_relative_entrypoint(source.expanduser().resolve() / "index.html")
    digest = payload_sha256(files)

    state = _branch_state(repo, branch)
    if state is not None:
        marker = existing_marker(repo, branch, version_key)
        if marker is not None:
            if marker.get("payload_sha256") != digest:
                raise PublishError(
                    "version-key already exists with a different payload; immutable URLs are never overwritten"
                )
            pages = ensure_pages(repo, branch)
            url = version_url(pages["html_url"], version_key)
            if wait:
                verify_deployment(
                    url,
                    version_key=version_key,
                    payload_digest=digest,
                    timeout_seconds=timeout_seconds,
                )
            return {
                "status": "PASS",
                "repo": repo,
                "version_key": version_key,
                "payload_sha256": digest,
                "pages_branch": branch,
                "pages_commit_sha": state[0],
                "url": url,
                "marker_url": urllib.parse.urljoin(url, "_game_exp_build.json"),
                "deployment_verified": bool(wait),
                "idempotent": True,
            }
        prefix = _contents(repo, branch, f"play/{version_key}")
        if prefix is not None:
            raise PublishError(
                "version path already exists without a valid marker; refusing to overwrite it"
            )

    blobs: list[dict[str, str]] = []
    prefix = f"play/{version_key}/"
    for rel, path in files:
        blobs.append(
            {
                "path": prefix + rel,
                "mode": "100644",
                "type": "blob",
                "sha": _blob(repo, path.read_bytes()),
            }
        )
    for rel, content in generated_files(
        version_key=version_key,
        payload_digest=digest,
        file_count=len(files),
        producer=producer,
    ).items():
        blobs.append(
            {
                "path": rel,
                "mode": "100644",
                "type": "blob",
                "sha": _blob(repo, content),
            }
        )

    commit_sha = update_pages_branch(
        repo,
        branch,
        blobs,
        message=f"Publish playable {version_key}",
    )
    pages = ensure_pages(repo, branch)
    url = version_url(pages["html_url"], version_key)
    if wait:
        verify_deployment(
            url,
            version_key=version_key,
            payload_digest=digest,
            timeout_seconds=timeout_seconds,
        )
    return {
        "status": "PASS",
        "repo": repo,
        "version_key": version_key,
        "payload_sha256": digest,
        "pages_branch": branch,
        "pages_commit_sha": commit_sha,
        "url": url,
        "marker_url": urllib.parse.urljoin(url, "_game_exp_build.json"),
        "deployment_verified": bool(wait),
        "idempotent": False,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Publish a static build to an immutable versioned path on GitHub Pages. "
            "The repository must be public and gh must already be authenticated."
        )
    )
    parser.add_argument("--repo", required=True, help="GitHub repository in owner/name form")
    parser.add_argument("--source", required=True, help="static build directory containing index.html")
    parser.add_argument("--version-key", required=True, help="immutable build key, preferably the source SHA")
    parser.add_argument("--producer", default="prototype-executor")
    parser.add_argument("--branch", default=DEFAULT_BRANCH)
    parser.add_argument(
        "--require-relative-entrypoint",
        action="store_true",
        help="reject root-absolute src/href paths that break versioned project-site URLs",
    )
    parser.add_argument("--no-wait", action="store_true", help="do not verify the served marker/index")
    parser.add_argument("--timeout", type=int, default=180)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    try:
        result = publish(
            repo=args.repo,
            source=Path(args.source),
            version_key=args.version_key,
            producer=args.producer,
            branch=args.branch,
            require_relative_entrypoint=args.require_relative_entrypoint,
            wait=not args.no_wait,
            timeout_seconds=args.timeout,
        )
    except PublishError as exc:
        result = {"status": "REJECTED", "error": str(exc)}
        if args.json:
            print(json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2))
        else:
            print(f"REJECTED: {exc}")
        return 2
    if args.json:
        print(json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2))
    else:
        print(result["url"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
