#!/usr/bin/env python3
"""W112.1 Part B: replay the last N days of the local price archive through the router twice -- without and with
per-row filters (kept filter splits) -- and count decisions per arm before vs after. Read-only: archive files only,
no network, no order path. Same one-decision-per-(ticker, tier) rule and tier->band map as replay_router_w110_3.

Only NBA has a filter adapter wired today; NFL (weather forecast + matchup book not stored) and NHL (112.4 not merged)
supply no filters, so their before/after are identical by construction -- reported, not hidden.

  PYTHONPATH=src python3 scripts/replay_filter_splits_w112_1.py --archive <PRICE_ARCHIVE> --out <dir> [--days 14]
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "12_EXPLORATORY" / "longshot_bias"))

import calib  # noqa: E402
from replay_router_w110_3 import SERIES, TIER_BAND, market_type_for  # noqa: E402

from prediction_market_bot.decision_trees import leaf_map as lm  # noqa: E402
from prediction_market_bot.decision_trees import ride  # noqa: E402
from prediction_market_bot.decision_trees.filter_supply import FilterSupply  # noqa: E402
from prediction_market_bot.decision_trees.router import Evidence, Situation, route  # noqa: E402


def replay(archive: str, days: int):
    files = sorted(glob.glob(os.path.join(archive, "prices_*.jsonl")))[-days:]
    ev = Evidence(ride=ride.load(), leaf_map=lm.default_map(), filter_splits=lm.default_splits())
    supply = FilterSupply()
    seen, rows, notes = set(), [], Counter()
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
            band = TIER_BAND.get(tier)
            if not band:
                continue
            sport, mt = market_type_for(r["series_ticker"])
            flt, note = supply.for_row({"sport": sport, "event_ticker": r["event_ticker"], "ts_utc": datetime.fromtimestamp(ts, timezone.utc).isoformat()})
            notes[f"{sport}:{note or 'filters_supplied'}"] += 1
            base = dict(sport=sport, family=r["series_ticker"], ticker=r["ticker"], event=r["event_ticker"], tier=tier,
                        yes_bid=bid, yes_ask=ask, half_spread=(ask - bid) / 2, market_type=mt, band=band)
            before = route(Situation(**base), ev)
            after = route(Situation(**base, filters=flt), ev)
            rows.append({"sport": sport, "series": r["series_ticker"], "before": before.tree, "after": after.tree,
                         "kept": bool(after.split and after.split.get("arm")),
                         "changed": before.tree != after.tree or before.side != after.side})
    return rows, [os.path.basename(f) for f in files], notes


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--archive", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--days", type=int, default=14)
    a = ap.parse_args()
    rows, files, notes = replay(a.archive, a.days)
    out = {"files": files, "decisions": len(rows), "filter_notes": dict(notes),
           "before": dict(Counter(r["before"] for r in rows)), "after": dict(Counter(r["after"] for r in rows)),
           "changed": sum(r["changed"] for r in rows), "kept_split_fired": sum(r["kept"] for r in rows),
           "by_sport": {}}
    for sp in sorted({r["sport"] for r in rows}):
        sub = [r for r in rows if r["sport"] == sp]
        out["by_sport"][sp] = {"decisions": len(sub), "before": dict(Counter(r["before"] for r in sub)),
                               "after": dict(Counter(r["after"] for r in sub)), "changed": sum(r["changed"] for r in sub)}
    os.makedirs(a.out, exist_ok=True)
    Path(a.out, "W112_1_replay.json").write_text(json.dumps(out, indent=1, sort_keys=True))
    print(json.dumps(out, indent=1, sort_keys=True))


if __name__ == "__main__":
    main()
