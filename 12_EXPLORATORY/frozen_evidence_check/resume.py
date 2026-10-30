"""W97.2 Part A: the frozen-cell reproduction, resumable inside the box's 900 s task limit (GG-1520).

`repro.py run` makes one pass over the whole archive (~1.4 GB on a 1-core box) and is killed at 900 s. This module splits
the SAME computation into units that each fit, caching derived files under the 12_EXPLORATORY fence:

  prefilter  one streaming pass writes `_cache/pre/<SERIES>/prices_<date>.jsonl` (lines of that series only, order kept),
             per source file, resumable; a source file that grew since (today's) is redone.
  unit       (series, window): runs 89.2's scan/cell test (`exact_fee_recompute.run_89`) or 91.2's ladder build
             (`ladder_ride.load/build_records` + `exact_fee_recompute.ladder_rows`) UNCHANGED on that series' files only.
             Both read per ticker / per (series, event, group), so one series at a time is the same arithmetic.
             The result is cached as JSON; the 91.2 split date needs every ladder series, so trigger rows are cached and
             the split is taken at `combine`.
  step       prefilter, then units until the time budget, then a status line. Re-run until `remaining` is 0.
  combine    classify the 13 cells (k007 as originally reported, and the exact fee) from the cached units.

Applies to: any reproduction whose code path reads series independently. Does not apply to a cell that needs two series at once.
Read-only on the archive and repo; the only writes are the derived cache.
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import re
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import repro as R  # noqa: E402
from _fence import safe_out  # noqa: E402

CACHE = os.path.join("frozen_evidence_check", "_cache")
WINDOWS = (None, "2026-10-28")  # full archive, and the wave window (W94.Q: dates <= 2026-10-27)
ALL_SERIES = tuple(dict.fromkeys(R.SERIES + R.LADDER_SERIES))
_SER = re.compile(r'"series_ticker":\s*"([A-Z0-9]+)"')
_UNIT_GUARD_S = 150.0  # do not start a unit with less than this left unless a faster one is known


def _dir(*parts) -> str:
    return R.under_fence(os.path.join(CACHE, *parts))


def prefilter(archive: str, budget_s: float = 600.0) -> dict:
    """Split each archive file into per-series files. Returns files done / remaining."""
    t0 = time.time()
    files = R.archive_files(archive)
    done = left = 0
    outs = {s: _dir("pre", s) for s in ALL_SERIES}
    for f in files:
        name, size = os.path.basename(f), os.path.getsize(f)
        marker = os.path.join(outs[ALL_SERIES[0]], name + ".src")
        if os.path.exists(marker) and open(marker).read().strip() == str(size):
            continue
        if time.time() - t0 > budget_s:
            left += 1
            continue
        hs = {s: open(safe_out(os.path.join(outs[s], name + ".tmp")), "w") for s in ALL_SERIES}
        try:
            with open(f) as fh:
                for line in fh:
                    m = _SER.search(line)
                    h = hs.get(m.group(1)) if m else None
                    if h is not None:
                        h.write(line)
        finally:
            for h in hs.values():
                h.close()
        for s in ALL_SERIES:
            safe_out(os.path.join(outs[s], name + ".tmp")).replace(safe_out(os.path.join(outs[s], name)))
            with open(safe_out(os.path.join(outs[s], name + ".src")), "w") as fh:
                fh.write(str(size))
        done += 1
    return {"source_files": len(files), "prefiltered_this_call": done, "left": left, "elapsed_s": round(time.time() - t0)}


def _series_dir(series: str, until: str | None) -> str:
    d = _dir("pre", series)
    if not until:
        return d
    sub = _dir("subset", series, f"until_{until}")
    for f in glob.glob(os.path.join(d, "prices_*.jsonl")):
        if R.file_date(f) < until:
            link = os.path.join(sub, os.path.basename(f))
            if not os.path.islink(link):
                safe_out(link).symlink_to(os.path.abspath(f))
    return sub


def _unit_path(series: str, until: str | None) -> str:
    return os.path.join(_dir("units"), f"{series}__{until or 'full'}.json")


def run_unit(series: str, until: str | None, settle: str) -> dict:
    import exact_fee_recompute as X
    sd = _series_dir(series, until)
    if series in R.SERIES:
        cells = [c for c in X.run_89(sd, settle) if c["cell"][0] == series]
        out = {"series": series, "until": until, "kind": "89", "cells": cells}
    else:
        out = {"series": series, "until": until, "kind": "91", "rows": None}
    if series in R.LADDER_SERIES:
        import calib
        import ladder_ride as LR
        st = calib.load_settlements(settle)
        recs, _ = LR.build_records(LR.load(sd))
        rows = {"old": X.ladder_rows(recs, st, lambda s, q: X.fee_k007(q)), "exact": X.ladder_rows(recs, st, X.fee_x)}
        out["rows"] = rows
    with open(safe_out(_unit_path(series, until)), "w") as fh:
        json.dump(out, fh)
    return out


def pending_units() -> list:
    return [(s, w) for w in WINDOWS for s in ALL_SERIES if not os.path.exists(_unit_path(s, w))]


def step(archive: str, settle: str, budget_s: float = 700.0) -> dict:
    t0 = time.time()
    pf = prefilter(archive, budget_s=min(budget_s, 400.0))
    if pf["left"]:
        return {"prefilter": pf, "units_done": 0, "remaining_units": len(pending_units()) + 0, "note": "prefilter incomplete; re-run"}
    done, slowest = 0, 0.0
    for s, w in pending_units():
        left = budget_s - (time.time() - t0)
        if left < max(_UNIT_GUARD_S, 1.3 * slowest):
            break
        t1 = time.time()
        run_unit(s, w, settle)
        slowest = max(slowest, time.time() - t1)
        done += 1
        print(f"[resume] unit {s} {w or 'full'} {time.time() - t1:.0f}s", flush=True)
    return {"prefilter": pf, "units_done": done, "remaining_units": len(pending_units()), "slowest_unit_s": round(slowest),
            "elapsed_s": round(time.time() - t0)}


def _ladder_stat(rs: list):
    from prediction_market_bot.quant.inference import pooled_cluster_test
    if not rs:
        return None
    t = pooled_cluster_test([(r["game"], r["pnl"]) for r in rs], b=1500)
    return {"n": len(rs), "games": t["n_games"], "net": t["mean"], "lo": t["ci95"][0], "hi": t["ci95"][1]}


def combine_window(until: str | None) -> dict:
    units = {s: json.load(open(_unit_path(s, until))) for s in ALL_SERIES if os.path.exists(_unit_path(s, until))}
    missing = [s for s in ALL_SERIES if s not in units]
    import exact_fee_recompute as X
    cells = []
    for fam in R.SERIES:
        for c in units.get(fam, {}).get("cells", []):
            cells.append(c)
    order = {c[:4]: i for i, c in enumerate(X.CELLS_89)}
    cells.sort(key=lambda c: order[tuple(c["cell"])])
    out = []
    for c in cells:
        fam, t, lab, bk = c["cell"]
        if not c.get("n"):
            out.append({"id": f"89.2 {fam} {t} {lab} {bk}", "rep": (c["rep_n"], c["rep_net"], c["rep_lo"]), "n": 0, "status": "NOT REPRODUCED"})
            continue
        out.append({"id": f"89.2 {fam} {t} {lab} {bk} {c['side']}", "rep": (c["rep_n"], c["rep_net"], c["rep_lo"]), "n": c["n"],
                    "games": c["games"], "k007": c["old"], "exact": c["exact"],
                    "status": R.classify(c["rep_n"], c["rep_net"], c["rep_lo"], c["n"], c["old"]["net"], c["old"]["lo"])})
    rows = {tag: [r for s in R.LADDER_SERIES if s in units for r in (units[s]["rows"] or {}).get(tag, [])] for tag in ("old", "exact")}
    dates = sorted({r["date"] for r in rows["old"]})
    split = dates[len(dates) // 2] if dates else ""
    for gap, rep in (("net2-5c", (117, 0.0870, 0.0336)), ("net5c+", (30, 0.2166, 0.0951))):
        sel = {tag: [r for r in rows[tag] if r["series"] == "KXMLBTOTAL" and r["tier"] == "T0-2h" and r["gap"] == gap
                     and r["book"] == "tight" and r["date"] >= split] for tag in rows}
        o, e = _ladder_stat(sel["old"]), _ladder_stat(sel["exact"])
        out.append({"id": f"91.2 KXMLBTOTAL T0-2h {gap} tight (HELD_OUT second half)", "rep": rep, "n": (o or {}).get("n", 0), "games": (o or {}).get("games"),
                    "k007": o, "exact": e,
                    "status": "NOT REPRODUCED" if not o else R.classify(*rep, o["n"], o["net"], o["lo"])})
    return {"until": until, "missing_units": missing, "split": split, "triggers": (len(rows["old"]), len(rows["exact"])), "cells": out}


def render(res: dict) -> str:
    f = lambda d: "—" if not d else f"{d['net']:+.4f} [{d['lo']:+.4f}, {d['hi']:+.4f}]"  # noqa: E731
    L = [f"## window: {'all archive files' if not res['until'] else 'dates < ' + res['until']}", "",
         f"91.2 split date {res['split']}; ladder triggers k007/exact {res['triggers'][0]}/{res['triggers'][1]}; missing units: {res['missing_units'] or 'none'}", "",
         "| cell | reported n/net/lo | re-run n (games) | k007 net [lo,hi] | exact net [lo,hi] | class |", "|---|---|---|---|---|---|"]
    for c in res["cells"]:
        L.append(f"| {c['id']} | {c['rep']} | {c['n']} ({c.get('games')}) | {f(c.get('k007'))} | {f(c.get('exact'))} | {c['status']} |")
    return "\n".join(L) + "\n"


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["step", "combine", "status"])
    ap.add_argument("--archive", default="exp_output/PRICE_ARCHIVE")
    ap.add_argument("--settle", default=os.path.join(CACHE, "settle"))
    ap.add_argument("--budget", type=float, default=700.0)
    a = ap.parse_args(argv)
    settle = a.settle if os.path.isabs(a.settle) else R.under_fence(a.settle)
    R.heartbeat()
    if a.cmd == "step":
        print(json.dumps(step(a.archive, settle, a.budget), indent=1))
    elif a.cmd == "status":
        print(json.dumps({"pending_units": pending_units()}, indent=1))
    else:
        for w in WINDOWS:
            print(render(combine_window(w)))


if __name__ == "__main__":
    main()
