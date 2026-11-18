#!/usr/bin/env python3
"""W118.4 / B-102 Part A: READ-ONLY disk measurement for the box (allowlisted task `disk_read`).

Prints: df -h; the 25 largest directories under the project (du -x, depth 2); logs/ and exp_output/ sizes and their largest files;
sizes by kind (.jsonl / .log / .gz / other); the journald size and /var/log, /var/cache, /tmp; and the 7-day growth from the box's own
history (src/prediction_market_bot/disk_guard.py). Changes nothing. Stdlib only.

  python3 scripts/disk_read.py [--root DIR]
"""
from __future__ import annotations

import argparse
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from prediction_market_bot import disk_guard  # noqa: E402

TOP_DIRS = 25
TOP_FILES = 12
CMD_TIMEOUT_S = 600


def sh(cmd: list, timeout: int = CMD_TIMEOUT_S) -> str:
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return (r.stdout + (("\n" + r.stderr.strip()) if r.returncode and r.stderr.strip() else "")).strip()
    except (OSError, subprocess.TimeoutExpired) as e:
        return "(%s: %s)" % (cmd[0], e)


def human(n: float) -> str:
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if abs(n) < 1024 or unit == "TB":
            return ("%d %s" % (n, unit)) if unit == "B" else ("%.1f %s" % (n, unit))
        n /= 1024.0
    return "%d B" % n


def du_dirs(root: Path, depth: int = 2, top: int = TOP_DIRS) -> list:
    """[(bytes, path)] largest directories at depth 1..depth under root (du -x: never crosses a filesystem)."""
    out = sh(["du", "-x", "-k", "-d", str(depth), str(root)])
    rows = []
    for ln in out.splitlines():
        k, _, p = ln.partition("\t")
        if k.strip().isdigit() and p and Path(p) != root:
            rows.append((int(k) * 1024, p))
    rows.sort(reverse=True)
    return rows[:top]


def walk_sizes(base: Path) -> tuple:
    """(total_bytes, by_kind{kind: bytes}, [(bytes, path)] biggest files). Does not follow symlinks."""
    total, kinds, files = 0, {".jsonl": 0, ".log": 0, ".gz": 0, "other": 0}, []
    for dp, _dn, fn in os.walk(base, followlinks=False):
        for f in fn:
            p = os.path.join(dp, f)
            try:
                st = os.lstat(p)
            except OSError:
                continue
            if not os.path.isfile(p) or os.path.islink(p):
                continue
            total += st.st_size
            ext = ".gz" if f.endswith(".gz") else (".jsonl" if f.endswith(".jsonl") else (".log" if f.endswith(".log") else "other"))
            kinds[ext] += st.st_size
            files.append((st.st_size, p))
    files.sort(reverse=True)
    return total, kinds, files[:TOP_FILES]


def report(root: Path, now: datetime) -> str:
    L = ["# disk_read - %s - %s" % (now.strftime("%Y-%m-%dT%H:%MZ"), root), ""]
    L += ["## df -h (project filesystem, then all)", sh(["df", "-h", str(root)]), "", sh(["df", "-h"]), ""]
    L += ["## 25 largest directories under the project (du -x, depth 2)"]
    for b, p in du_dirs(root):
        L.append("%10s  %s" % (human(b), os.path.relpath(p, root) if p.startswith(str(root)) else p))
    L.append("")
    for name in ("logs", "exp_output"):
        base = root / name
        if not base.exists():
            L += ["## %s: absent" % name, ""]
            continue
        total, kinds, top = walk_sizes(base)
        L.append("## %s/ total %s  (jsonl %s, log %s, gz %s, other %s)" % (
            name, human(total), human(kinds[".jsonl"]), human(kinds[".log"]), human(kinds[".gz"]), human(kinds["other"])))
        L += ["%10s  %s" % (human(b), os.path.relpath(p, root)) for b, p in top]
        L.append("")
    L += ["## journald / system", sh(["journalctl", "--disk-usage"])]
    for p in ("/var/log", "/var/cache", "/tmp"):
        out = sh(["du", "-sx", "-k", p])
        k = out.split("\t")[0].strip()
        L.append("%10s  %s" % (human(int(k) * 1024) if k.isdigit() else out[:60], p))
    L.append("")
    a = disk_guard.assess(root, now)
    L += ["## growth and days to 90% (disk_guard)", disk_guard.render(a)]
    g = a["growth"]
    if g:
        L.append("history: %s .. %s, %d samples from %s" % (g["first_ts"].strftime("%m-%d %H:%MZ"), g["last_ts"].strftime("%m-%d %H:%MZ"),
                                                         g["n"], a["source"]))
        if "bytes_per_day" in g:
            L.append("bytes/day: %s" % human(g["bytes_per_day"]))
    L.append("now: %s used of %s, %s available (%d%%)" % (human(a["usage"]["used_bytes"]), human(a["usage"]["total_bytes"]),
                                                          human(a["usage"]["avail_bytes"]), a["now_pct"]))
    return "\n".join(L)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--root", default=str(ROOT))
    args = ap.parse_args(argv)
    print(report(Path(args.root).resolve(), datetime.now(timezone.utc)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
