#!/usr/bin/env python3
"""W110.3 Part C: replay the multi-arm router over the last 14 days of the local price archive (NBA/NHL/NFL game,
spread, total). Read-only: archive files + Kalshi PUBLIC market GETs for settled results. No order path.

One decision per (ticker, tier), at the first archived snapshot in that tier (later snapshots of the same market are
serially correlated and would inflate n). Evidence = the ride table only (no skill/momentum evidence exists for these
families), so the reachable branches are RIDE, POT_OF_GOLD, NO_BET. P&L per contract = calib.side_pnl (taker, k007 fee),
intervals = game-clustered bootstrap. Unsettled markets are counted, not scored.

  PYTHONPATH=src python3 scripts/replay_router_w110_3.py --archive <PRICE_ARCHIVE> --out <dir> [--days 14] [--no-fetch]
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import re
import sys
import urllib.request
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "12_EXPLORATORY" / "longshot_bias"))

import calib  # noqa: E402
from prediction_market_bot.decision_trees import ride  # noqa: E402
from prediction_market_bot.decision_trees.router import NO_BET, Evidence, Situation, route  # noqa: E402
from prediction_market_bot.quant.inference import cluster_bootstrap  # noqa: E402

SERIES = ("KXNBAGAME", "KXNBASPREAD", "KXNBATOTAL", "KXNHLGAME", "KXNHLSPREAD", "KXNHLTOTAL",
          "KXNFLGAME", "KXNFLSPREAD", "KXNFLTOTAL")
API = "https://api.elections.kalshi.com/trade-api/v2/markets/"


def decisions(archive: str, days: int):
    files = sorted(glob.glob(os.path.join(archive, "prices_*.jsonl")))[-days:]
    ev = Evidence(ride=ride.load())
    seen, out = set(), []
    for f in files:
        for line in open(f):
            r = json.loads(line)
            if r["series_ticker"] not in SERIES:
                continue
            try:
                bid, ask = float(r["yes_bid"]), float(r["yes_ask"])
            except (TypeError, ValueError):
                continue
            ts = calib.parse_ts(r["run_ts"])
            tier = calib.tier(r["event_ticker"], ts)
            key = (r["ticker"], tier)
            if key in seen:
                continue
            seen.add(key)
            s = Situation(sport=r["series_ticker"][2:5].lower(), family=r["series_ticker"], ticker=r["ticker"],
                          event=r["event_ticker"], tier=tier, yes_bid=bid, yes_ask=ask, half_spread=(ask - bid) / 2)
            d = route(s, ev)
            out.append({"series": r["series_ticker"], "ticker": r["ticker"], "event": r["event_ticker"], "tier": tier,
                        "bid": bid, "ask": ask, "branch": d.tree, "side": d.side,
                        "reason": ";".join(map(str, d.reasons))})
    return out, [os.path.basename(f) for f in files]


def result_for(ticker: str):
    try:
        with urllib.request.urlopen(API + ticker, timeout=15) as h:
            m = json.load(h).get("market", {})
        return {"yes": 1.0, "no": 0.0}.get(m.get("result"))
    except Exception:  # noqa: BLE001 - unreachable or unknown = unscored, counted
        return None


def score(rows, fetch: bool):
    cache, by = {}, defaultdict(lambda: defaultdict(list))
    unsettled = Counter()
    for r in rows:
        if r["branch"] == NO_BET or r["side"] not in ("yes", "no"):
            continue
        if r["ticker"] not in cache:
            cache[r["ticker"]] = result_for(r["ticker"]) if fetch else None
        y = cache[r["ticker"]]
        if y is None:
            unsettled[r["branch"]] += 1
            continue
        gross = (y - r["ask"]) if r["side"] == "yes" else ((1 - y) - (1 - r["bid"]))
        by[r["branch"]][r["event"]].append((gross, calib.side_pnl(r["side"], y, r["bid"], r["ask"])))
    res = {}
    for b, games in by.items():
        n = sum(len(v) for v in games.values())
        g = {k: [x[0] for x in v] for k, v in games.items()}
        nt = {k: [x[1] for x in v] for k, v in games.items()}
        gm, _, _ = cluster_bootstrap(g, b=1000, seed=7)
        nm, lo, hi = cluster_bootstrap(nt, b=1000, seed=7)
        res[b] = {"n": n, "games": len(games), "gross_mean": gm, "net_mean": nm, "net_lo": lo, "net_hi": hi}
    return res, dict(unsettled)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--archive", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--days", type=int, default=14)
    ap.add_argument("--no-fetch", action="store_true")
    a = ap.parse_args()
    rows, files = decisions(a.archive, a.days)
    scored, unsettled = score(rows, not a.no_fetch)
    by_sport = Counter((r["series"][2:5], r["branch"]) for r in rows)
    summary = {"files": files, "decisions": len(rows), "branch_counts": dict(Counter(r["branch"] for r in rows)),
               "by_sport_branch": {f"{k[0]}:{k[1]}": v for k, v in sorted(by_sport.items())},
               "no_bet_reasons": dict(Counter(re.sub(r"[0-9]+\.[0-9]+|for KX\S+", "#", r["reason"]) for r in rows if r["branch"] == NO_BET)),
               "scored": scored, "unsettled_by_branch": unsettled}
    os.makedirs(a.out, exist_ok=True)
    Path(a.out, "W110_3_replay.json").write_text(json.dumps(summary, indent=1, sort_keys=True))
    print(json.dumps(summary, indent=1, sort_keys=True))


if __name__ == "__main__":
    main()
