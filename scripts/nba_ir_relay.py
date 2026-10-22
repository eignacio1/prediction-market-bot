#!/usr/bin/env python3
"""W84.1 / GG-1030: relay the official NBA injury-report PDFs from a GitHub runner (the box's IP is 403'd by Akamai).

Writes each not-yet-relayed slot's PDF to --out plus new_manifest.jsonl (file, last_modified, sha256, size, fetched_utc).
Same URLs as nba_lineup_window_capture.IR_URL; bytes are stored untouched. Public unauthenticated GETs only.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).resolve().parent))
import nba_lineup_window_capture as cap  # noqa: E402

DATA_BRANCH = "data/nba-injury-reports"


def known_files() -> set:
    p = subprocess.run(["git", "show", "origin/%s:manifest.jsonl" % DATA_BRANCH], capture_output=True, text=True)
    out = set()
    for ln in p.stdout.splitlines():
        try:
            out.add(json.loads(ln)["file"])
        except Exception:  # noqa: BLE001
            pass
    return out


def relay(out: Path, now: datetime, known: set, get=requests.get) -> list:
    out.mkdir(parents=True, exist_ok=True)
    rows = []
    for slot in cap.slot_candidates(now, n=3):
        url = cap.slot_url(slot)
        name = url.rsplit("/", 1)[1]
        if name in known:
            continue
        r = get(url, timeout=30, headers={"User-Agent": "Mozilla/5.0"})
        if r.status_code != 200:
            continue
        (out / name).write_bytes(r.content)
        rows.append({"file": name, "last_modified": r.headers.get("Last-Modified"),
                     "sha256": hashlib.sha256(r.content).hexdigest(), "size": len(r.content),
                     "fetched_utc": now.strftime("%Y-%m-%dT%H:%M:%SZ")})
    (out / "new_manifest.jsonl").write_text("".join(json.dumps(x, sort_keys=True) + "\n" for x in rows))
    return rows


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    subprocess.run(["git", "fetch", "origin", DATA_BRANCH], capture_output=True)
    rows = relay(Path(a.out), datetime.now(timezone.utc), known_files())
    print("relayed %d new report(s): %s" % (len(rows), [r["file"] for r in rows]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
