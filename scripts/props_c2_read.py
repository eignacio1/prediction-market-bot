#!/usr/bin/env python3
"""READ-ONLY (W128.2 Part C): NBA props C2 vs EXP-047, DESCRIPTIVE, on rows logged since a date, plus the forward look schedule.

Pairs the box's C2 shadow rows (exp_output/PREGAME_SHADOW_EXP047_C2) with EXP-047 rows (PREGAME_SHADOW_EXP047) on (market_ticker, run_id)
and prints per stat: paired rows, games, how often the two prices differ, mean / mean-abs price difference. No outcome is read, no verdict.
Schedule: games per stat to put the 95% interval of the retrospective log-loss gain (RESULT_C2.json) off zero, if the forward effect equals
the retrospective one (an assumption, stated), and the date that is reached at the observed games per day. Writes nothing: stdout only."""
from __future__ import annotations

import argparse
import json
import math
import os
import sys
from collections import defaultdict
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent
STATS = {"NBA_PLAYER_POINTS": "points", "NBA_PLAYER_REBOUNDS": "rebounds", "NBA_PLAYER_ASSISTS": "assists", "NBA_PLAYER_THREES": "threes"}
RESULT = REPO / "12_EXPLORATORY" / "nba_props_role" / "RESULT_C2.json"


def read_rows(d: Path, since: str):
    for f in sorted(d.glob("NBAENG_*.jsonl")):
        try:
            fh = f.open("r", encoding="utf-8", errors="ignore")
        except OSError:
            continue
        with fh:
            for line in fh:
                try:
                    r = json.loads(line)
                except ValueError:
                    continue
                if isinstance(r, dict) and str(r.get("ts_utc", ""))[:10] >= since and r.get("market_type") in STATS:
                    yield r


def compare(base_dir: Path, c2_dir: Path, since: str) -> dict:
    base = {(r["market_ticker"], r.get("run_id")): r["p_yes"] for r in read_rows(base_dir, since)}
    out = {s: {"pairs": 0, "differ": 0, "sum": 0.0, "abs": 0.0, "games": set(), "days": set()} for s in STATS.values()}
    for r in read_rows(c2_dir, since):
        b = base.get((r["market_ticker"], r.get("run_id")))
        if b is None:
            continue
        o = out[STATS[r["market_type"]]]
        d = r["p_yes"] - b
        o["pairs"] += 1
        o["differ"] += abs(d) > 1e-9
        o["sum"] += d
        o["abs"] += abs(d)
        o["games"].add(r.get("event_ticker"))
        o["days"].add(str(r["ts_utc"])[:10])
    return out


def schedule(result: dict, games_per_day: dict, today: date) -> dict:
    out = {}
    for s, st in result["stats"].items():
        lo, hi, diff, n = st["ci95"][0], st["ci95"][1], st["ll_diff"], st["n_games"]
        sd = (hi - lo) / 3.92 * math.sqrt(n)                      # per-game sd of the log-loss difference, from the retro interval
        need = math.ceil((1.96 * sd / abs(diff)) ** 2) if diff else None
        gpd = games_per_day.get(s) or 0.0
        out[s] = {"games_to_judge": need, "games_per_day_observed": round(gpd, 2),
                  "date_reached": (today + timedelta(days=math.ceil(need / gpd))).isoformat() if need and gpd > 0 else None}
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--since", default="2026-11-25")
    a = ap.parse_args(argv)
    ex = REPO / "exp_output"
    cmp_ = compare(ex / "PREGAME_SHADOW_EXP047", ex / "PREGAME_SHADOW_EXP047_C2", a.since)
    today = datetime.now(timezone.utc).date()
    gpd = {}
    for s, o in cmp_.items():
        n_days = len(o["days"])
        gpd[s] = len(o["games"]) / n_days if n_days else 0.0
        print(f"{s:9} pairs={o['pairs']} games={len(o['games'])} days={n_days} differ={o['differ']}"
              + (f" mean_diff={o['sum'] / o['pairs']:+.4f} mean_abs_diff={o['abs'] / o['pairs']:.4f}" if o["pairs"] else " (no paired rows)"))
    if RESULT.exists():
        print("forward look (assumes the forward effect equals the retrospective one; judged by the router per leaf on net, not by this):")
        for s, v in schedule(json.loads(RESULT.read_text()), gpd, today).items():
            print(f"  {s:9} {v}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
