"""W129.3 Part C: one 2026 regular-season slate day replayed through the seven D6 layers in dry mode, per game cell.

usage: PYTHONPATH=src:. python3 12_EXPLORATORY/mlb_engine/dry_run_w129_3.py [slate_date] [archive_dir] [store_root]
Reads: the price archive (prices_<day>.jsonl, the day and the day before so T1 rows exist), the local engine store tables for
the day's games, the v1 leaf map and filter splits. No outcome is read (home_runs / away_runs are never touched), no order,
no ledger write, no network. Writes RESULT_W129_3_C.json next to this file (or $W129_3_OUT).

For each of the 12 cells (4 families x T1, T2, T3) it reports which layer is present and what is missing; nothing is imputed:
  L1 model p (engine price for the row's rung)      L2 market state (bid/ask/mid/prev mid)     L3 factor filters as splits
  L4 tree arm (router leaf)                         L5 held-out net per arm (forward)          L6 risk / sizing (kelly 0)
  L7 execution with fills measured
A layer is PRESENT only if it fired on at least one row of the cell; the count and the reason it did not are reported."""
from __future__ import annotations

import json
import os
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from prediction_market_bot.decision_trees import row_sizing  # noqa: E402
from prediction_market_bot.decision_trees.shadow_route import route_row  # noqa: E402
from prediction_market_bot.mlb_engine.forecaster import MLBEngineForecaster  # noqa: E402
from prediction_market_bot.pregame_shadow.bands import band_for_horizon  # noqa: E402
from prediction_market_bot.pregame_shadow.mlb_forecaster import ET, SERIES_TO_TYPE, parse_market_ticker  # noqa: E402

SLATE = sys.argv[1] if len(sys.argv) > 1 else "2026-08-15"
ARCH = Path(sys.argv[2]) if len(sys.argv) > 2 else Path(os.environ.get("W129_3_ARCHIVE", ROOT / "exp_output" / "PRICE_ARCHIVE"))
STORE = Path(sys.argv[3]) if len(sys.argv) > 3 else Path.home() / "mlb_store"
OUT = Path(os.environ.get("W129_3_OUT", HERE / "RESULT_W129_3_C.json"))
TYPES = ("MLB_MONEYLINE", "MLB_RUN_LINE", "MLB_GAME_TOTAL", "MLB_TEAM_TOTAL")
BANDS = ("T1", "T2", "T3")
LAYERS = ("L1_model_p", "L2_market_state", "L3_factor_filters", "L4_tree_arm", "L5_heldout_net_forward", "L6_sizing", "L7_fills")


def load_rows(day: str):
    prev = (pd.Timestamp(day) - pd.Timedelta(days=1)).date().isoformat()
    for d in (prev, day):
        p = ARCH / ("prices_%s.jsonl" % d)
        if not p.exists():
            continue
        with p.open() as f:
            for ln in f:
                r = json.loads(ln)
                if r.get("series_ticker") in SERIES_TO_TYPE:
                    yield r


def f(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def main() -> int:
    import mlb_board_daily as bd
    tabs = {n: pd.read_parquet(STORE / "tables" / ("%s.parquet" % n)) for n in ("games", "lineups", "pa")}
    games = tabs["games"]
    day_games = games[games["game_date"].astype(str).str[:10] == SLATE]
    # point-in-time: price_slate builds history from games BEFORE each game's date (PAHistory); the day's own result columns are
    # never read by this script.
    board = bd.price_slate(day_games, tabs["lineups"], tabs["pa"], n_draws=2000)
    fc = MLBEngineForecaster({tuple(k.split("|")): v for k, v in board.items()})   # same conversion as mlb_board_daily.load_board

    rows, last_mid = [], {}
    for r in sorted(load_rows(SLATE), key=lambda x: x["run_ts"]):
        p = parse_market_ticker(r["ticker"])
        if p is None or p["start_utc"].astimezone(ET).date().isoformat() != SLATE:
            continue
        ts = datetime.strptime(r["run_ts"], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
        hours = (p["start_utc"] - ts).total_seconds() / 3600.0
        bid, ask = f(r.get("yes_bid")), f(r.get("yes_ask"))
        prev = last_mid.get(r["ticker"])
        if bid is not None and ask is not None:
            last_mid[r["ticker"]] = (bid + ask) / 2.0
        band = band_for_horizon(hours)
        if band is None or bid is None or ask is None or ask <= bid or bid <= 0 or ask >= 1:
            rows.append({"type": p["market_type"], "band": band, "skip": "no_band" if band is None else "no_two_sided_quote"})
            continue
        fcst = fc.forecast(r["ticker"], ts)
        row = {"sport": "MLB", "market_type": p["market_type"], "band": band, "horizon_hours_to_start": round(hours, 4),
               "event_ticker": p["event_ticker"], "market_ticker": r["ticker"], "p_yes": fcst.p_yes if fcst else None,
               "yes_bid": bid, "yes_ask": ask, "mid": (bid + ask) / 2.0, "half_spread": (ask - bid) / 2.0}
        out = {"type": p["market_type"], "band": band, "game": (p["home"], p["away"]), "L1": fcst is not None,
               "L2": True, "L2_prev_mid": prev is not None}
        try:
            rt = route_row(row, r["series_ticker"], prev_mid=prev, filters=None, filters_note="no per-row MLB filter input",
                           depth=None)
            out["L3"] = bool(rt.get("filters_n"))
            out["L4"] = rt.get("arm") is not None
            out["arm"] = rt.get("arm")
            out["thin"] = rt.get("thin")
            out["arm_source"] = rt.get("arm_source")
            out["leaf"] = rt.get("leaf_id")
            out["reason"] = str(rt.get("reason"))[:80]
            sz = row_sizing.row_decision(row, rt)
            out["L6"] = sz is not None
            out["kelly_zero"] = (sz or {}).get("size_for", {}).get("kelly_fraction", None)
        except Exception as e:  # noqa: BLE001 -- reported, not hidden
            out.update({"L3": False, "L4": False, "L6": False, "route_error": "%s:%s" % (type(e).__name__, str(e)[:80])})
        rows.append(out)

    cells = {}
    for t in TYPES:
        for b in BANDS:
            rs = [x for x in rows if x["type"] == t and x["band"] == b and "skip" not in x]
            sk = Counter(x["skip"] for x in rows if x["type"] == t and x["band"] == b and "skip" in x)
            n = len(rs)
            c = {"rows": n, "games": len({x["game"] for x in rs}), "skips": dict(sk)}
            c["L1_model_p"] = sum(x["L1"] for x in rs)
            c["L2_market_state"] = n
            c["L2_with_prev_mid"] = sum(x["L2_prev_mid"] for x in rs)
            c["L3_factor_filters"] = sum(x.get("L3", False) for x in rs)
            c["L4_tree_arm"] = sum(x.get("L4", False) for x in rs)
            c["arms"] = dict(Counter(x.get("arm") for x in rs if x.get("L4")))
            c["L4_thin"] = sum(1 for x in rs if x.get("thin"))
            c["L5_heldout_net_forward"] = 0
            c["L6_sizing"] = sum(x.get("L6", False) for x in rs)
            c["L7_fills"] = 0
            c["route_errors"] = dict(Counter(x["route_error"] for x in rs if "route_error" in x))
            miss = []
            if n == 0:
                miss.append("no archive rows in this band on this slate day (runs only 22-05Z; see note)")
            else:
                if c["L1_model_p"] < n:
                    miss.append("L1 on %d of %d rows (rung off the priced ladder or no board for the game)" % (c["L1_model_p"], n))
                if c["L2_with_prev_mid"] < n:
                    miss.append("prev mid absent on %d rows (first sighting; move filter has no input)" % (n - c["L2_with_prev_mid"]))
                if not c["L3_factor_filters"]:
                    miss.append("L3: no MLB per-row factor-filter supply exists (filters None; not imputed)")
                if c["L4_tree_arm"] < n:
                    miss.append("L4 on %d of %d rows" % (c["L4_tree_arm"], n))
                miss.append("L5: v1 leaf nets are 2026 look-back only; no forward held-out net per arm exists before 2027")
                if c["L6_sizing"] < n:
                    miss.append("L6 on %d of %d rows" % (c["L6_sizing"], n))
                miss.append("L7: no MLB order or fill exists (MLB idle; no arm-order demo book for MLB)")
            c["missing"] = miss
            c["layers_present"] = [k for k in LAYERS if c.get(k)]
            cells["%s|%s" % (t, b)] = c

    res = {"slate_date": SLATE, "games_in_store": int(len(day_games)), "games_priced": len(board),
           "engine_input_note": "lineups are the as-played store lineups, not posted lineups; the posted-lineup feed does not exist",
           "outcomes_read": False, "cells": cells,
           "archive_run_hours_utc_note": "price archive logs 22:00-05:59Z only on this day, so T2 and T3 rows exist only for late games"}
    OUT.write_text(json.dumps(res, indent=1, default=str))
    print("%-22s %-3s %5s %5s  %s" % ("cell", "", "rows", "games", "layers present"))
    for k, c in cells.items():
        print("%-22s %5d %5d  %s" % (k, c["rows"], c["games"], ",".join(x.split("_")[0] for x in c["layers_present"]) or "-"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
