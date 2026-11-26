#!/usr/bin/env python3
"""W129.1: pull Muse's NHL goalie and referee snapshot files at the PINNED archive SHA into NHL_MUSE_DIR (read-only to the archive).

Source: eignacio1/sports-intel-archive, ``L3-snapshots/nhl/{goalies,refs}-YYYY-MM-DD.jsonl``, read through the GitHub API at the pin
(``filters.nhl_depth.ARCHIVE_SHA``) -- never a clone, never a write to the archive. Writes only under NHL_MUSE_DIR (default
``exp_output/NHL_MUSE``); idempotent (a file already present with the same byte size is skipped); byte-capped per file and in total.
The token comes from GH_TOKEN / GITHUB_TOKEN, else the box's ``.env`` (GH_TOKEN= or GITHUB_TOKEN= line). No token, no fetch: it says so.
Output: file count per type, date range, bytes. Exit 0 only when every wanted file is on disk.
"""
from __future__ import annotations

import json
import os
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from prediction_market_bot.decision_trees.filters.nhl_depth import ARCHIVE_REPO, ARCHIVE_SHA  # noqa: E402

API = "https://api.github.com"
WANT = re.compile(r"^L3-snapshots/nhl/(goalies|refs)-(\d{4}-\d{2}-\d{2})\.jsonl$")
MAX_FILE_BYTES = 1_000_000
MAX_TOTAL_BYTES = 8_000_000
MAX_FILES = 400


def token() -> str | None:
    for k in ("GH_TOKEN", "GITHUB_TOKEN"):
        if os.environ.get(k):
            return os.environ[k]
    env = ROOT / ".env"
    if env.is_file():
        for line in env.read_text().splitlines():
            m = re.match(r"^\s*(?:export\s+)?(GH_TOKEN|GITHUB_TOKEN)\s*=\s*(.+?)\s*$", line)
            if m:
                return m.group(2).strip("'\"")
    return None


def _get(url: str, tok: str | None, raw: bool = False) -> bytes:
    h = {"User-Agent": "pm-bot-nhl-muse-fetch", "X-GitHub-Api-Version": "2022-11-28",
         "Accept": "application/vnd.github.raw" if raw else "application/vnd.github+json"}
    if tok:
        h["Authorization"] = f"Bearer {tok}"
    with urllib.request.urlopen(urllib.request.Request(url, headers=h), timeout=60) as r:
        return r.read(MAX_FILE_BYTES + 1) if raw else r.read()


def wanted(tree: list) -> list[dict]:
    """Blobs in the pinned tree that are NHL goalie / referee snapshot files, oldest first, capped."""
    out = [t for t in tree if t.get("type") == "blob" and WANT.match(t.get("path", ""))]
    return sorted(out, key=lambda t: t["path"])[:MAX_FILES]


def summarize(directory: Path) -> dict:
    by: dict = {}
    for p in sorted(directory.glob("*.jsonl")):
        m = re.match(r"^(goalies|refs)-(\d{4}-\d{2}-\d{2})\.jsonl$", p.name)
        if m:
            by.setdefault(m.group(1), []).append(m.group(2))
    return {k: {"files": len(v), "first": min(v), "last": max(v)} for k, v in by.items()}


def run(directory: Path, tok: str | None, sha: str = ARCHIVE_SHA) -> int:
    directory.mkdir(parents=True, exist_ok=True)
    if not tok:
        print("NO_TOKEN: the archive is private; set GH_TOKEN / GITHUB_TOKEN (env or .env). Nothing fetched.")
        return 3
    try:
        tree = json.loads(_get(f"{API}/repos/{ARCHIVE_REPO}/git/trees/{sha}?recursive=1", tok))
    except (urllib.error.URLError, OSError, ValueError) as e:
        print(f"TREE_FAIL {type(e).__name__}: {str(e)[:160]}")
        return 2
    if tree.get("truncated"):
        print("TREE_TRUNCATED: refusing to guess the file list")
        return 2
    files, total, got, skipped, failed = wanted(tree.get("tree", [])), 0, 0, 0, []
    for t in files:
        dest = directory / Path(t["path"]).name
        size = int(t.get("size") or 0)
        if size > MAX_FILE_BYTES:
            failed.append((t["path"], "over_file_cap"))
            continue
        if dest.is_file() and dest.stat().st_size == size:
            skipped += 1
            total += size
            continue
        if total + size > MAX_TOTAL_BYTES:
            failed.append((t["path"], "over_total_cap"))
            continue
        try:
            body = _get(f"{API}/repos/{ARCHIVE_REPO}/contents/{t['path']}?ref={sha}", tok, raw=True)
        except (urllib.error.URLError, OSError) as e:
            failed.append((t["path"], type(e).__name__))
            continue
        if len(body) != size:
            failed.append((t["path"], f"size_{len(body)}_vs_{size}"))
            continue
        tmp = dest.with_suffix(".tmp")
        tmp.write_bytes(body)
        os.replace(tmp, dest)
        got += 1
        total += size
    print(f"MUSE_FETCH sha={sha[:10]} wanted={len(files)} fetched={got} already_present={skipped} failed={len(failed)} bytes={total}")
    for f in failed[:10]:
        print("FAILED", *f)
    print("ON_DISK", json.dumps(summarize(directory), sort_keys=True))
    return 0 if not failed else 1


def main() -> int:
    d = Path(os.environ.get("NHL_MUSE_DIR") or ROOT / "exp_output" / "NHL_MUSE")
    return run(d, token())


if __name__ == "__main__":
    sys.exit(main())
