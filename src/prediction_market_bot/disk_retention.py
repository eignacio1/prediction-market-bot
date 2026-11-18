"""W118.4 / B-102 Part B: disk retention as code. Append-only evidence is NEVER deleted -- old files are gzip-compressed, verified, then
the plain copy is replaced. Nothing here runs unless a person/cron calls ``--apply``; ``--dry-run`` (the default) changes nothing.

Safety rules (each one tested in tests/test_w118_4_retention.py):
  * only files not modified for ``min_age_days`` (an appender never has its file swapped under it);
  * the .gz is written to ``<name>.gz.tmp``, read back, its sha256 of the DECOMPRESSED bytes must equal the original's, and only then
    is the tmp renamed and the plain file removed -- so a reader that opens the decompressed stream sees byte-identical content
    (``Store.digest()`` hashes those bytes and is unchanged);
  * a target is compressed only when ``readers_verified`` is True: every reader of that tree reads ``X`` or ``X.gz`` through
    ``dated_files`` / ``open_text`` below. Targets whose readers are not taught yet are listed as HELD with the bytes they would free;
  * not enough free space to stage the .gz -> skip that file (reported), never half-write.

Readers: ``open_text(path)`` opens ``path`` or ``path + '.gz'`` transparently; ``dated_files(dir, pattern)`` lists the files matching a
glob (pattern WITHOUT the .gz suffix) once each, whether stored plain or gzipped.
"""
from __future__ import annotations

import argparse
import glob
import gzip
import hashlib
import os
import shutil
import subprocess
import sys
import zlib
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterator, Optional

GZ = ".gz"
SAMPLE_BYTES = 4 * 1024 * 1024
JOURNAL_CAP = "200M"
JOURNAL_DIR = "/var/log/journal"


# ---------------------------------------------------------------- reader helpers (used by the readers named in each target)
def dated_files(directory, pattern: str) -> list:
    """Sorted paths (as the plain name, even when only ``.gz`` exists on disk) matching ``pattern`` in ``directory``; each once."""
    base = str(Path(directory) / pattern)
    names = {p for p in glob.glob(base)} | {p[:-len(GZ)] for p in glob.glob(base + GZ)}
    return sorted(names)


def resolve(path) -> str:
    """The path that exists on disk: ``path`` if present, else ``path.gz``; FileNotFoundError when neither is."""
    p = str(path)
    if os.path.exists(p):
        return p
    if os.path.exists(p + GZ):
        return p + GZ
    raise FileNotFoundError(p)


def open_text(path, mode: str = "r", **kw):
    """Open ``path`` or ``path.gz`` in text mode (``'rb'`` for bytes). Read-only."""
    real = resolve(path)
    if real.endswith(GZ):
        if "b" in mode:
            return gzip.open(real, "rb")
        return gzip.open(real, "rt", encoding=kw.get("encoding", "utf-8"))
    return open(real, mode, **kw)


def read_bytes(path) -> bytes:
    with open_text(path, "rb") as fh:
        return fh.read()


# ---------------------------------------------------------------- policy
@dataclass(frozen=True)
class Target:
    name: str
    pattern: str               # glob under the project root (plain names; the .gz is what we create)
    min_age_days: float
    readers_verified: bool
    note: str


POLICY = (
    Target("kalshi_history_raw", "exp_output/KALSHI_HISTORY/raw/raw_????-??-??.jsonl", 3, True,
           "read by board_survey_sports_store.Store + gate.done_keys + thin_markets/efficiency.load via dated_files/open_text"),
    Target("kalshi_history_thin_raw", "exp_output/KALSHI_HISTORY/thin/raw_????-??-??.jsonl", 3, True,
           "same Store reader; kalshi_thin_history_fetch writes through Store"),
    Target("json_bak", "logs/*.json.bak", 14, True, "one-off migration backups; no reader"),
    Target("price_archive", "exp_output/PRICE_ARCHIVE/prices_????-??-??.jsonl", 14, False,
           "HELD: ~25 readers glob prices_*.jsonl (scripts/, nba_engine/live.py); teach them, then flip readers_verified"),
    Target("kalshi_history_rebuilt", "exp_output/KALSHI_HISTORY/rebuilt_*/candles/*.jsonl", 14, False,
           "HELD: analytics/kalshi_history.py reads these by byte offset (seek)"),
    Target("audit_ledgers", "logs/audit_*.jsonl", 30, False,
           "HELD: live audit ledgers, many readers; MLB is idle until 2027 but the files are append-open"),
)


def _sha_stream(fh, chunk: int = 1 << 20) -> str:
    h = hashlib.sha256()
    while True:
        b = fh.read(chunk)
        if not b:
            return h.hexdigest()
        h.update(b)


def estimate_saved(path: str) -> int:
    """Bytes freed if compressed, estimated from a zlib pass over the first 4 MB (ratio applied to the whole file)."""
    size = os.path.getsize(path)
    with open(path, "rb") as fh:
        sample = fh.read(SAMPLE_BYTES)
    if not sample:
        return 0
    ratio = len(zlib.compress(sample, 6)) / len(sample)
    return max(0, int(size * (1 - ratio)))


def candidates(root: Path, now: datetime, targets=POLICY) -> list:
    """[(Target, path, size, age_days)] for every plain file matching a target that is old enough, sorted by size."""
    out = []
    ts = now.timestamp()
    for t in targets:
        for p in glob.glob(str(root / t.pattern)):
            if os.path.islink(p) or not os.path.isfile(p):
                continue
            st = os.stat(p)
            age = (ts - st.st_mtime) / 86400.0
            if age >= t.min_age_days:
                out.append((t, p, st.st_size, age))
    out.sort(key=lambda r: -r[2])
    return out


def compress_verified(path: str, free_margin: int = 200 * 1024 * 1024) -> tuple:
    """gzip ``path`` -> ``path.gz`` with a sha256 round trip, then remove ``path``. Returns (ok, message, bytes_freed)."""
    size = os.path.getsize(path)
    free = shutil.disk_usage(os.path.dirname(path)).free
    if free < size // 2 + free_margin:
        return False, "skipped: only %d MB free to stage the .gz" % (free >> 20), 0
    tmp, dst = path + ".gz.tmp", path + GZ
    mtime = os.stat(path).st_mtime
    try:
        with open(path, "rb") as src, open(tmp, "wb") as raw, gzip.GzipFile(filename="", mode="wb", fileobj=raw, compresslevel=6, mtime=0) as gz:
            h = hashlib.sha256()
            while True:
                b = src.read(1 << 20)
                if not b:
                    break
                h.update(b)
                gz.write(b)
        with gzip.open(tmp, "rb") as back:
            if _sha_stream(back) != h.hexdigest():
                os.unlink(tmp)
                return False, "verify FAILED (sha mismatch); original kept", 0
        if os.stat(path).st_mtime != mtime or os.path.getsize(path) != size:
            os.unlink(tmp)
            return False, "skipped: file changed while compressing; original kept", 0
        os.replace(tmp, dst)
        os.utime(dst, (mtime, mtime))
        os.unlink(path)
    except OSError as e:
        if os.path.exists(tmp):
            os.unlink(tmp)
        return False, "error: %s; original kept" % e, 0
    return True, "compressed", size - os.path.getsize(dst)


def journal_usage_bytes() -> Optional[int]:
    """Bytes under /var/log/journal (None when absent)."""
    if not os.path.isdir(JOURNAL_DIR):
        return None
    out = subprocess.run(["du", "-sk", JOURNAL_DIR], capture_output=True, text=True).stdout.split("\t")[0]
    return int(out) * 1024 if out.isdigit() else None


def parse_size(s: str) -> int:
    return int(s[:-1]) * {"K": 1 << 10, "M": 1 << 20, "G": 1 << 30}[s[-1].upper()]


def plan(root: Path, now: datetime, targets=POLICY) -> dict:
    """Pure read: what ``--apply`` would do. {'compress': [...], 'held': [...], 'journal': {...}, totals}."""
    comp, held = [], []
    for t, p, size, age in candidates(root, now, targets):
        row = {"target": t.name, "path": os.path.relpath(p, root), "bytes": size, "age_days": round(age, 1), "saved": estimate_saved(p)}
        (comp if t.readers_verified else held).append(row | {"note": t.note})
    ju = journal_usage_bytes()
    cap = parse_size(JOURNAL_CAP)
    j = {"usage": ju, "cap": cap, "saved": max(0, ju - cap) if ju else 0}
    return {"compress": comp, "held": held, "journal": j,
            "saved_compress": sum(r["saved"] for r in comp), "saved_held": sum(r["saved"] for r in held), "saved_journal": j["saved"]}


def apply(root: Path, now: datetime, targets=POLICY) -> list:
    """Compress every verified-reader candidate, one file at a time, oldest-largest first. Returns [(path, ok, msg, freed)]."""
    res = []
    for t, p, _size, _age in candidates(root, now, targets):
        if not t.readers_verified:
            continue
        ok, msg, freed = compress_verified(p)
        res.append((os.path.relpath(p, root), ok, msg, freed))
    return res


def _mb(n: float) -> str:
    return "%.1f MB" % (n / 1048576.0)


def render(pl: dict) -> str:
    L = ["# disk_retention dry run (changes nothing)", "", "## would compress (readers verified): %d files, ~%s freed" % (
        len(pl["compress"]), _mb(pl["saved_compress"]))]
    L += ["%10s -> saves ~%10s  age %5.1fd  %s" % (_mb(r["bytes"]), _mb(r["saved"]), r["age_days"], r["path"]) for r in pl["compress"][:40]]
    L += ["", "## held (readers not taught yet): %d files, ~%s would free once they are" % (len(pl["held"]), _mb(pl["saved_held"]))]
    L += ["%10s -> ~%10s  %-24s %s" % (_mb(r["bytes"]), _mb(r["saved"]), r["target"], r["path"]) for r in pl["held"][:15]]
    j = pl["journal"]
    L += ["", "## journald: %s used, cap %s -> frees ~%s" % (_mb(j["usage"]) if j["usage"] else "n/a", JOURNAL_CAP, _mb(j["saved"])),
          "", "TOTAL if applied now: ~%s (compress %s + journald %s); held adds ~%s" % (
              _mb(pl["saved_compress"] + pl["saved_journal"]), _mb(pl["saved_compress"]), _mb(pl["saved_journal"]), _mb(pl["saved_held"]))]
    return "\n".join(L)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--root", default=str(Path(__file__).resolve().parents[2]))
    ap.add_argument("--apply", action="store_true", help="compress (default is a dry run)")
    a = ap.parse_args(argv)
    root, now = Path(a.root).resolve(), datetime.now(timezone.utc)
    if not a.apply:
        print(render(plan(root, now)))
        return 0
    freed = 0
    for rel, ok, msg, f in apply(root, now):
        print("%s %s: %s (%s freed)" % ("OK  " if ok else "SKIP", rel, msg, _mb(f)))
        freed += f
    if shutil.which("journalctl"):
        r = subprocess.run(["journalctl", "--vacuum-size=" + JOURNAL_CAP], capture_output=True, text=True)
        print("journald vacuum --vacuum-size=%s: rc=%d %s" % (JOURNAL_CAP, r.returncode, (r.stdout + r.stderr).strip().splitlines()[-1:] or ""))
    print("compressed bytes freed: %s" % _mb(freed))
    return 0


if __name__ == "__main__":
    sys.exit(main())
