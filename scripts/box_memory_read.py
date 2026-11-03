#!/usr/bin/env python3
"""W98.3: READ-ONLY box memory probe (GG-1581). Runs ON the box via scripts/box_tasks.py. Writes nothing.

  python scripts/box_memory_read.py [--since "2026-11-03 00:00"]

Prints: memory/swap totals, load, per-process live RSS + peak RSS (VmHWM) + swap for the python/bot processes grouped by
script (so stacked copies show), OOM kills since --since (default: last 24 h) by killed process, and the t3_skips.jsonl
tally. Peak RSS of already-finished runs is not recoverable from the kernel; the OOM line carries the RSS at kill time.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OOM_RE = re.compile(r"Out of memory: Killed process (\d+) \((\S+)\).*?anon-rss:(\d+)kB")


def parse_oom(text: str) -> list[dict]:
    return [{"pid": int(m.group(1)), "comm": m.group(2), "anon_rss_mb": round(int(m.group(3)) / 1024, 1)}
            for m in OOM_RE.finditer(text)]


def _status(pid: str) -> dict:
    out = {}
    try:
        for ln in Path("/proc/%s/status" % pid).read_text().splitlines():
            k, _, v = ln.partition(":")
            if k in ("VmRSS", "VmHWM", "VmSwap"):
                out[k] = int(v.split()[0]) / 1024.0
    except OSError:
        pass
    return out


def processes() -> list[dict]:
    rows = []
    for p in Path("/proc").iterdir():
        if not p.name.isdigit():
            continue
        try:
            cmd = (p / "cmdline").read_bytes().replace(b"\0", b" ").decode(errors="replace").strip()
        except OSError:
            continue
        if "python" not in cmd or ("scripts/" not in cmd and "prediction_market_bot" not in cmd):
            continue
        m = re.search(r"(scripts/\S+\.py(?: --bands? \S+)?|-m prediction_market_bot\.\S+)", cmd)
        st = _status(p.name)
        if st:
            rows.append({"pid": int(p.name), "what": m.group(1) if m else cmd[:80], **st})
    return rows


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--since", default="24 hours ago")
    a = ap.parse_args(argv)
    print("== meminfo / load ==")
    for ln in Path("/proc/meminfo").read_text().splitlines():
        if ln.split(":")[0] in ("MemTotal", "MemAvailable", "SwapTotal", "SwapFree"):
            print("  " + ln)
    print("  loadavg: " + Path("/proc/loadavg").read_text().strip())
    rows = processes()
    print("\n== bot python processes now (%d) ==" % len(rows))
    by = Counter(r["what"] for r in rows)
    for r in sorted(rows, key=lambda r: -r.get("VmRSS", 0)):
        print("  pid %-7d %-58s rss %6.1f MB  peak %6.1f MB  swap %6.1f MB%s" % (
            r["pid"], r["what"][:58], r.get("VmRSS", 0), r.get("VmHWM", 0), r.get("VmSwap", 0),
            "   <-- %d copies running" % by[r["what"]] if by[r["what"]] > 1 else ""))
    k = subprocess.run(["journalctl", "-k", "--since", a.since, "--no-pager", "-o", "short-iso"],
                       capture_output=True, text=True)
    oom = parse_oom(k.stdout if k.returncode == 0 else subprocess.run(["dmesg", "-T"], capture_output=True, text=True).stdout)
    print("\n== OOM kills since %r: %d ==" % (a.since, len(oom)))
    for comm, n in Counter(o["comm"] for o in oom).most_common():
        big = max(o["anon_rss_mb"] for o in oom if o["comm"] == comm)
        print("  %-20s kills %-3d largest anon-rss at kill %.1f MB" % (comm, n, big))
    sk = ROOT / "logs" / "t3_skips.jsonl"
    rws = [json.loads(x) for x in sk.read_text().splitlines() if x.strip()] if sk.exists() else []
    print("\n== lock skips (logs/t3_skips.jsonl): %d  %s ==" % (len(rws), json.dumps(Counter(r.get("runner") for r in rws))))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
