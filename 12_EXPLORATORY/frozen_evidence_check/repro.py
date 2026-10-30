"""W95.2 Part A: do the frozen ride cells (EXP-042's 11, EXP-043's 2) reproduce from the FULL archive?

Runs 89.2's and 91.2's code UNCHANGED (calib.scan/cell_test, ladder_ride.load/build_records) plus 94.Q's exact-fee
variants, on whatever archive and settlement cache it is pointed at, and compares to the reported figures.
Read-only on the archive and the repo. Its only write is the settlement cache (`fetch`), a derived file outside the repo
tree (public unauthenticated Kalshi GETs, resumable, time-budgeted).

  repro.py inventory --archive D
  repro.py fetch --archive D --cache C [--budget 780]
  repro.py run --archive D --settle C [--until 2026-10-27]      # --until builds a symlink subset in a temp dir

Classification (per cell, k007 re-run vs the reported figures): REPRODUCED = same n and net/lo within rounding of the
reported 3-decimal figures; DIFFERS = a re-run exists but n or net differ (reason column says which window);
NOT REPRODUCED = zero re-run rows. Applies to: any cell whose reported n/net came from the same code path.
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import re
import sys
import time
import urllib.request
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from _fence import safe_out  # noqa: E402


def under_fence(p: str) -> str:
    """Relative paths resolve against 12_EXPLORATORY/ (the only place this module may write)."""
    return str(safe_out(os.path.join(p, ".keep")).parent)

HERE = os.path.dirname(os.path.abspath(__file__))
EXP = os.path.dirname(HERE)
for sub in ("", "longshot_bias", "ride_ladder", "quant_w94"):
    sys.path.insert(0, os.path.join(EXP, sub))
sys.path.insert(0, os.path.join(EXP, "..", "src"))

# 89.2 cells: (family, tier, bucket, book, reported n, reported net, reported lo) -- copied by import, not retyped
SERIES = ("KXMLBHIT", "KXMLBF5TOTAL", "KXNFLTOTAL", "KXMLBSPREAD", "KXMLBTEAMTOTAL", "KXMLBF5", "KXMLBTOTAL", "KXMLBF7")
LADDER_SERIES = ("KXNFLTOTAL", "KXNFLSPREAD", "KXNFLTEAMTOTAL", "KXMLBTOTAL", "KXMLBSPREAD", "KXMLBTEAMTOTAL")
BASE = "https://api.elections.kalshi.com/trade-api/v2/"
NET_TOL = 0.0006  # reported nets are printed to 3 decimals (lo to 4)


def archive_files(archive: str) -> list:
    return sorted(glob.glob(os.path.join(archive, "prices_*.jsonl")))


def file_date(path: str) -> str:
    return os.path.basename(path)[7:17]


def subset(archive: str, until: str | None) -> str:
    """Symlink subset of prices_*.jsonl with date < until (exclusive), in a temp dir; the archive is never touched."""
    if not until:
        return archive
    d = under_fence(os.path.join("frozen_evidence_check", "_subset", f"until_{until}"))
    for f in archive_files(archive):
        if file_date(f) < until:
            link = safe_out(os.path.join(d, os.path.basename(f)))
            if not link.is_symlink():
                link.symlink_to(os.path.abspath(f))
    return d


def inventory(archive: str) -> dict:
    """File count, date range, row counts per target series, and the two-sided pre-start KXMLBHIT rows `scan` can read."""
    import calib as C
    files = archive_files(archive)
    rows, two_sided, hit_pre = Counter(), Counter(), 0
    for f in files:
        with open(f) as fh:
            for line in fh:
                try:
                    r = json.loads(line)
                except ValueError:
                    continue
                s = r.get("series_ticker")
                if s not in SERIES and s not in LADDER_SERIES:
                    continue
                rows[s] += 1
                try:
                    b, a = float(r.get("yes_bid")), float(r.get("yes_ask"))
                except (TypeError, ValueError):
                    continue
                if b and a and a >= b:
                    two_sided[s] += 1
                    if s == "KXMLBHIT" and C.tier(r["event_ticker"], C.parse_ts(r["run_ts"])) is not None:
                        hit_pre += 1
    return {"files": len(files), "first": file_date(files[0]) if files else None, "last": file_date(files[-1]) if files else None,
            "rows_by_series": dict(rows), "two_sided_by_series": dict(two_sided), "KXMLBHIT_two_sided_prestart": hit_pre}


def _get(path: str) -> dict:
    for i in range(3):
        try:
            return json.load(urllib.request.urlopen(BASE + path, timeout=25))
        except Exception:
            time.sleep(1 + i)
    return {}


def _event_markets(event: str) -> dict:
    """{ticker: {result, ...}} for settled markets of one event; live endpoint then historical; cursor-paginated."""
    for base in ("markets?event_ticker=%s&limit=200", "historical/markets?event_ticker=%s&limit=200"):
        out, cur = {}, ""
        for _ in range(20):
            d = _get((base % event) + (("&cursor=" + cur) if cur else ""))
            for m in d.get("markets", []):
                if m.get("result") in ("yes", "no"):
                    out[m["ticker"]] = {"result": m["result"], "settle_ts": m.get("settlement_ts") or m.get("expiration_time"),
                                        "close_time": m.get("close_time")}
            cur = d.get("cursor") or ""
            if not cur:
                break
        if out:
            return out
    return {}


def fetch(archive: str, cache: str, budget_s: float = 780.0, workers: int = 4) -> dict:
    """Resumable: one cache file per event (events with no settled markets are recorded as empty so they are not retried
    until the event could have settled -- an empty file older than 1 day is retried)."""
    cache = under_fence(cache)
    events = set()
    for f in archive_files(archive):
        with open(f) as fh:
            for line in fh:
                m = re.search(r'"event_ticker":\s*"([^"]+)"', line)
                s = re.search(r'"series_ticker":\s*"([^"]+)"', line)
                if m and s and s.group(1) in SERIES + LADDER_SERIES:
                    events.add(m.group(1))
    def todo(e):
        p = os.path.join(cache, e + ".json")
        return not os.path.exists(p) or (os.path.getsize(p) <= 2 and time.time() - os.path.getmtime(p) > 86400)
    pending = sorted(e for e in events if todo(e))
    t0, done = time.time(), 0

    def one(e):
        if time.time() - t0 > budget_s:
            return False
        res = _event_markets(e)
        with open(safe_out(os.path.join(cache, e + ".json")), "w") as fh:
            json.dump(res, fh)
        time.sleep(0.15)
        return True
    with ThreadPoolExecutor(workers) as ex:
        for ok in ex.map(one, pending):
            done += bool(ok)
    left = sum(1 for e in events if todo(e))
    return {"events": len(events), "fetched_this_call": done, "remaining": left, "elapsed_s": round(time.time() - t0)}


def classify(rep_n, rep_net, rep_lo, n, net, lo) -> str:
    if not n:
        return "NOT REPRODUCED"
    same = n == rep_n and abs(net - rep_net) <= NET_TOL and abs(lo - rep_lo) <= NET_TOL
    return "REPRODUCED" if same else "DIFFERS"


def run(archive: str, settle: str, until: str | None) -> dict:
    import exact_fee_recompute as X
    settle = settle if os.path.isabs(settle) else under_fence(settle)
    sub = subset(archive, until)
    r89 = X.run_89(sub, settle)
    r91 = X.run_91(sub, settle)
    cells = []
    for c in r89:
        fam, t, lab, bk = c["cell"]
        if not c.get("n"):
            cells.append({"id": f"89.2 {fam} {t} {lab} {bk}", "rep": (c["rep_n"], c["rep_net"], c["rep_lo"]), "n": 0,
                          "status": "NOT REPRODUCED"})
            continue
        cells.append({"id": f"89.2 {fam} {t} {lab} {bk} {c['side']}", "rep": (c["rep_n"], c["rep_net"], c["rep_lo"]),
                      "n": c["n"], "games": c["games"], "k007": c["old"], "exact": c["exact"],
                      "status": classify(c["rep_n"], c["rep_net"], c["rep_lo"], c["n"], c["old"]["net"], c["old"]["lo"])})
    for gap, rep in (("net2-5c", (117, 0.0870, 0.0336)), ("net5c+", None)):
        o, e = r91["cells"][gap]["old"], r91["cells"][gap]["exact"]
        cells.append({"id": f"91.2 KXMLBTOTAL T0-2h {gap} tight (HELD_OUT second half)", "rep": rep, "n": (o or {}).get("n", 0),
                      "k007": o, "exact": e,
                      "status": ("NOT REPRODUCED" if not o else classify(*rep, o["n"], o["net"], o["lo"]) if rep else "NO REPORTED FIGURE")})
    return {"until": until, "archive": inventory(sub), "cells": cells, "split": r91["split"],
            "triggers": (r91["triggers_old"], r91["triggers_exact"])}


def render(res: dict) -> str:
    inv = res["archive"]
    L = [f"# repro run (until={res['until'] or 'all'})", "",
         f"archive: {inv['files']} files {inv['first']}..{inv['last']}; KXMLBHIT two-sided pre-start rows: {inv['KXMLBHIT_two_sided_prestart']}",
         f"91.2 split date {res['split']}; triggers k007/exact {res['triggers'][0]}/{res['triggers'][1]}", "",
         "| cell | reported n/net/lo | re-run n | k007 net [lo,hi] | exact net [lo,hi] | status |", "|---|---|---|---|---|---|"]
    f = lambda d: "—" if not d else f"{d['net']:+.4f} [{d['lo']:+.4f}, {d['hi']:+.4f}]"  # noqa: E731
    for c in res["cells"]:
        L.append(f"| {c['id']} | {c['rep']} | {c['n']} | {f(c.get('k007'))} | {f(c.get('exact'))} | {c['status']} |")
    return "\n".join(L) + "\n"


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["inventory", "fetch", "run"])
    ap.add_argument("--archive", required=True)
    ap.add_argument("--cache")
    ap.add_argument("--settle")
    ap.add_argument("--until")
    ap.add_argument("--budget", type=float, default=780.0)
    a = ap.parse_args(argv)
    if a.cmd == "inventory":
        print(json.dumps(inventory(a.archive), indent=1))
    elif a.cmd == "fetch":
        print(json.dumps(fetch(a.archive, a.cache, a.budget), indent=1))
    else:
        print(render(run(a.archive, a.settle, a.until)))


if __name__ == "__main__":
    main()
