"""W86.2 Part B: within-snapshot coherence of Kalshi sports ladders from PRICE_ARCHIVE (read-only copy).

usage: python part_b.py <prices_games.jsonl.gz> <depth.jsonl.gz> [out_json]
Counts violations per 1,000 strike-snapshots: raw gross>0 -> net of k007 fees on every leg -> net AND
displayed size >=1 on every leg (depth is sampled; legs without a same-run_ts sample are 'unknown').
Persistence = consecutive 20-min runs of the same (type, legs) violation with net>0 (lower bound: a gap
in the archive ends the streak). 95% CIs bootstrap EVENTS (snapshots of one event are not independent).
"""
from __future__ import annotations

import gzip
import json
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parent))
import coherence as C  # noqa: E402
from ladder import parse_ticker  # noqa: E402
from _fence import safe_out  # noqa: E402

RNG = np.random.default_rng(88)
LADDER = {"KXNFLSPREAD": "team", "KXMLBSPREAD": "team", "KXMLBF5SPREAD": "team",
          "KXNFLTOTAL": "event", "KXMLBTOTAL": "event", "KXMLBF5TOTAL": "event",
          "KXNFLTEAMTOTAL": "team", "KXMLBTEAMTOTAL": "team"}
EXCL = {"KXMLBGAME": (2, True), "KXMLBF3": (3, True), "KXMLBF5": (3, True), "KXMLBF7": (3, True), "KXNFLGAME": (2, False)}


def f(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def team_of(ticker):
    suffix = ticker.rsplit("-", 1)[-1]
    if suffix == "TIE":
        return "TIE"
    try:
        return parse_ticker(ticker)[1]
    except ValueError:  # winner-style contracts (GAME, F3/F5/F7) carry only the team code
        return suffix


def load(prices, depth):
    snaps = defaultdict(lambda: defaultdict(list))       # run_ts -> event -> rows
    with gzip.open(prices, "rt") as fh:
        for line in fh:
            r = json.loads(line)
            if r["status"] != "active":
                continue
            row = {"ticker": r["ticker"], "event": r["event_ticker"], "series": r["series_ticker"],
                   "bid": f(r["yes_bid"]), "ask": f(r["yes_ask"]), "no_bid": f(r["no_bid"]), "no_ask": f(r["no_ask"])}
            snaps[r["run_ts"]][r["event_ticker"]].append(row)
    dep = defaultdict(dict)                               # run_ts -> ticker -> {'yes','no'}
    with gzip.open(depth, "rt") as fh:
        for line in fh:
            d = json.loads(line)
            if d.get("usable") and d.get("top_of_book_contracts"):
                dep[d["run_ts"]][d["ticker"]] = d["top_of_book_contracts"]
    return snaps, dep


def key_of(ticker):
    """event key without series prefix, for joining GAME to SPREAD events."""
    return ticker.split("-", 1)[1]


def scan(snaps):
    """Yield (run_ts, series, vtype, event, violation)."""
    for run_ts in sorted(snaps):
        evs = snaps[run_ts]
        by_key = defaultdict(dict)
        for ev, rows in evs.items():
            by_key[key_of(ev)][rows[0]["series"]] = rows
        for ev, rows in evs.items():
            series = rows[0]["series"]
            for r in rows:
                for v in C.same_contract(r):
                    yield run_ts, series, v
            if series in LADDER:
                groups = defaultdict(list)
                for r in rows:
                    groups[team_of(r["ticker"]) if LADDER[series] == "team" else ""].append(r)
                for team, g in groups.items():
                    for v in C.adjacent_monotonic(ev, team, g):
                        yield run_ts, series, v
                if series in ("KXNFLSPREAD", "KXMLBSPREAD"):  # opposite-team zero-strike pair is exclusive
                    low = {}
                    for r in rows:
                        t = team_of(r["ticker"]); k = parse_ticker(r["ticker"])[2]
                        if t not in low or k < parse_ticker(low[t]["ticker"])[2]:
                            low[t] = r
                    if len(low) == 2:
                        for v in C.exclusive_set(ev, list(low.values()), False):
                            yield run_ts, series, v
            if series in EXCL:
                n, exh = EXCL[series]
                if len(rows) == n:
                    for v in C.exclusive_set(ev, rows, exh):
                        yield run_ts, series, v
        # moneyline vs spread zero strike (same run_ts, same game key)
        for k, ss in by_key.items():
            for gs, sps, n_sp in (("KXNFLGAME", "KXNFLSPREAD", 1), ("KXMLBGAME", "KXMLBSPREAD", 2)):
                if gs in ss and sps in ss:
                    ml = {team_of(r["ticker"]): r for r in ss[gs]}
                    for r in ss[sps]:
                        t = team_of(r["ticker"])
                        if parse_ticker(r["ticker"])[2] == n_sp - 0.5 and t in ml:
                            for v in C.dominates(ss[sps][0]["event"], r, ml[t]):
                                yield run_ts, sps, v


def summarise(snaps, dep):
    run_ts = sorted(snaps)
    ridx = {t: i for i, t in enumerate(run_ts)}
    n_row = defaultdict(lambda: defaultdict(int)); n_snap = defaultdict(lambda: defaultdict(int))
    for t in run_ts:
        for ev, rows in snaps[t].items():
            s = rows[0]["series"]
            n_row[s][ev] += len(rows); n_snap[s][ev] += 1
    cnt = defaultdict(lambda: defaultdict(lambda: defaultdict(int)))  # (series,vtype) -> stage -> event -> n
    streak_src = defaultdict(list)                                    # (series,vtype,legs) -> [ridx]
    for t, series, v in scan(snaps):
        k = (series, v["type"]); e = v["event"]
        if v["gross"] <= 0:
            continue
        cnt[k]["raw"][e] += 1
        if v["net"] > 0:
            cnt[k]["net"][e] += 1
            sz = C.sized(v, dep.get(t, {}))
            if sz is None:
                cnt[k]["net_size_unknown"][e] += 1
            elif sz >= 1:
                cnt[k]["net_size_ok"][e] += 1
            else:
                cnt[k]["net_size_zero"][e] += 1
            streak_src[(series, v["type"], v["legs"])].append(ridx[t])
    streaks = defaultdict(list)
    for (series, vt, _), idx in streak_src.items():
        idx = sorted(set(idx)); run = 1
        for a, b in zip(idx, idx[1:] + [None]):
            if b is not None and b == a + 1:
                run += 1
            else:
                streaks[(series, vt)].append(run); run = 1
    out = {}
    for (series, vt), stages in sorted(cnt.items()):
        events = list(n_row[series])
        nr = np.array([n_row[series][e] for e in events], float)
        ns = np.array([n_snap[series][e] for e in events], float)
        rec = {"strike_snapshots": int(nr.sum()), "event_snapshots": int(ns.sum()), "events": len(events)}
        for stage, d in stages.items():
            c = np.array([d.get(e, 0) for e in events], float)
            idx = RNG.integers(0, len(events), (1500, len(events)))
            bs = c[idx].sum(1) / nr[idx].sum(1) * 1000
            rec[stage] = {"count": int(c.sum()), "per_1000_strike_snaps": float(c.sum() / nr.sum() * 1000),
                          "ci95": [float(np.percentile(bs, 2.5)), float(np.percentile(bs, 97.5))]}
        s = streaks.get((series, vt))
        if s:
            rec["net_streak_runs"] = {"n_streaks": len(s), "median": float(np.median(s)), "p90": float(np.percentile(s, 90)), "max": int(max(s)),
                                      "share_len1": float(np.mean(np.array(s) == 1))}
        out[f"{series}|{vt}"] = rec
    denom = {s: {"strike_snapshots": int(sum(n_row[s].values())), "event_snapshots": int(sum(n_snap[s].values())), "events": len(n_row[s])} for s in n_row}
    return {"runs": len(run_ts), "depth_runs_with_samples": len(dep), "denominators": denom, "violations": out}


if __name__ == "__main__":
    snaps, dep = load(sys.argv[1], sys.argv[2])
    res = summarise(snaps, dep)
    p = safe_out(Path(sys.argv[3]) if len(sys.argv) > 3 else HERE / "out" / "part_b_summary.json")
    json.dump(res, open(p, "w"), indent=1)
    print(json.dumps({k: v for k, v in res.items() if k != "violations"}, indent=1))
    for k, v in res["violations"].items():
        print(k, {s: v[s]["count"] for s in v if isinstance(v[s], dict) and "count" in v[s]}, v.get("net_streak_runs"))
