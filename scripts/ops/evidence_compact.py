#!/usr/bin/env python3
"""W120.3 / B-103: keep the Mac evidence copy compressed. Run ON THE MAC (evidence_pull.sh calls it after a verified pull).

Touches ONLY the Mac copy (DEST/data). The box is never contacted. Nothing is removed unless its content is proven kept:
  1. DUPLICATES: ``X`` and ``X.gz`` both present -> the plain ``X`` is removed only when the decompressed stream of ``X.gz`` has the
     same sha256 as ``X``, or ``X`` is an exact byte-prefix of it (the .gz is the newer superset). Anything else: both kept, reported.
  2. OLDER PLAIN FILES: every file the box's retention policy would compress (same patterns, same minimum age, readers verified) is
     compressed here with the same sha256 round trip (disk_retention.compress_verified).
Usage: evidence_compact.py [DATA_DIR] [--dry-run]     (default DATA_DIR = ~/PredictionMarketEvidence/data)
"""
from __future__ import annotations

import gzip
import hashlib
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))
from prediction_market_bot import disk_retention as dr  # noqa: E402

CHUNK = 1 << 20


def _sha_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for b in iter(lambda: fh.read(CHUNK), b""):
            h.update(b)
    return h.hexdigest()


def plain_is_covered_by_gz(plain: str, gz: str) -> str:
    """'equal' | 'prefix' | '' - how the decompressed .gz covers the plain file."""
    size = os.path.getsize(plain)
    hp, hg, got = hashlib.sha256(), hashlib.sha256(), 0
    with gzip.open(gz, "rb") as g:
        for b in iter(lambda: g.read(CHUNK), b""):
            hg.update(b)
            if got < size:
                hp.update(b[: size - got])
            got += len(b)
    if got < size:
        return ""
    plain_sha = _sha_file(plain)
    if got == size:
        return "equal" if hg.hexdigest() == plain_sha else ""
    return "prefix" if hp.hexdigest() == plain_sha else ""


def folder_bytes(data: Path) -> int:
    return sum(f.stat().st_size for f in data.rglob("*") if f.is_file())


def run(data: Path, dry: bool = False, now: datetime = None) -> dict:
    now = now or datetime.now(timezone.utc)
    rep = {"before": folder_bytes(data), "dup_removed": [], "dup_kept": [], "compressed": [], "failed": []}
    for gz in sorted(data.rglob("*.gz")):
        plain = Path(str(gz)[:-3])
        if not plain.is_file() or plain.is_symlink():
            continue
        how = plain_is_covered_by_gz(str(plain), str(gz))
        if how:
            if not dry:
                plain.unlink()
            rep["dup_removed"].append((str(plain.relative_to(data)), how, plain.stat().st_size if dry else 0))
        else:
            rep["dup_kept"].append(str(plain.relative_to(data)))
    for t, p, size, _age in dr.candidates(data, now):
        if not t.readers_verified:
            continue
        rel = os.path.relpath(p, data)
        if os.path.exists(p + dr.GZ):  # a .gz sibling that step 1 could not prove equal: never overwrite it
            continue
        if dry:
            rep["compressed"].append((rel, size))
            continue
        ok, msg, freed = dr.compress_verified(p)
        (rep["compressed"] if ok else rep["failed"]).append((rel, freed) if ok else (rel, msg))
    rep["after"] = folder_bytes(data)
    return rep


def main(argv) -> int:
    dry = "--dry-run" in argv
    args = [a for a in argv if not a.startswith("--")]
    data = Path(args[0] if args else os.path.expanduser("~/PredictionMarketEvidence/data"))
    if not data.is_dir():
        print("evidence_compact: no such dir %s" % data, file=sys.stderr)
        return 2
    r = run(data, dry)
    gb = lambda n: "%.2f GB" % (n / 1e9)
    print("evidence_compact%s: %s -> %s | plain duplicates removed %d (kept %d unverified) | older plain compressed %d | failed %d" % (
        " (DRY RUN)" if dry else "", gb(r["before"]), gb(r["after"]), len(r["dup_removed"]), len(r["dup_kept"]), len(r["compressed"]), len(r["failed"])))
    for rel in r["dup_kept"]:
        print("  KEPT BOTH (gz does not cover plain): %s" % rel)
    for rel, msg in r["failed"]:
        print("  FAILED %s: %s" % (rel, msg))
    return 1 if r["failed"] or r["dup_kept"] else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
