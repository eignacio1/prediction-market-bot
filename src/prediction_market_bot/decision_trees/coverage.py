"""W110.3 Part A -- route coverage: which registered (MarketType, band) cells the multi-arm router decides on.

Pure and read-only: reads the registry, the two cell tables and the DEFAULT_SERIES the board runner scans.
Orders are untouched. Applies to pre-game cells (T1/T2/T3); T4/T5 and the T4* sub-bands are in-play and the
router returns NO_BET for them by construction (ADR-0068: shallow, paid for by speed, not by this router).
"""
from __future__ import annotations

from collections import Counter
from typing import Dict, List, Optional, Tuple

from prediction_market_bot.c5_execution.market_type_registry import (
    MARKET_TYPE_REGISTRY, series_ticker_for, sport_for)
from prediction_market_bot.decision_trees import longshot, ride
from prediction_market_bot.decision_trees.router import FADE, MOMENTUM_FOLLOW, NO_BET, POT_OF_GOLD, RIDE

PREGAME_BANDS = ("T1", "T2", "T3")
# ADR-0068: the longer the horizon the deeper the tree.
DEPTH = {"T1": "deep", "T2": "intermediate", "T3": "shallow"}
# band -> calib.tier values the board can assign inside that band's window
BAND_TIERS = {"T1": ("T>24h", "T6-24h"), "T2": ("T2-6h", "T6-24h"), "T3": ("T0-2h",)}
# Families the board runner scans (scripts/run_ride_board.DEFAULT_SERIES). Kept in sync by a test.
BOARD_SERIES = ("KXNBAGAME", "KXNBASPREAD", "KXNBATOTAL", "KXNHLGAME", "KXNHLSPREAD", "KXNHLTOTAL",
                "KXNFLGAME", "KXNFLSPREAD", "KXNFLTOTAL")


def band_class(band: str) -> str:
    return "pregame" if band in PREGAME_BANDS else "inplay"


def _families(table_cells) -> Dict[str, set]:
    out: Dict[str, set] = {}
    for c in table_cells:
        out.setdefault(c.family, set()).add(c.tier)
    return out


def cell_rows(ride_table: Optional[ride.Table] = None, long_table: Optional[longshot.Table] = None) -> List[dict]:
    rt = ride_table if ride_table is not None else ride.load()
    lt = long_table if long_table is not None else longshot.load()
    ride_f = _families(rt.c.values())
    long_f = _families(lt._c.values())
    rows = []
    for (mt, band), cell in sorted(MARKET_TYPE_REGISTRY.items(), key=lambda kv: (kv[0][0].name, kv[0][1].value)):
        b = band.value
        fam = series_ticker_for(mt)
        pre = b in PREGAME_BANDS
        branches = [NO_BET]
        if pre:
            if fam in ride_f:
                branches.append(RIDE)
            if fam in long_f:
                branches.append(POT_OF_GOLD)
        routed = pre and fam in BOARD_SERIES
        rows.append({
            "market_type": mt.name, "family": fam, "sport": sport_for(mt), "band": b, "status": cell.status.value,
            "class": band_class(b), "depth": DEPTH.get(b, "stripped"),
            "tiers": list(BAND_TIERS.get(b, ())),
            "branches_with_evidence": sorted(branches),
            # FADE needs a skill record (ci_lo>0) + forecaster model_p; MOMENTUM needs a move_1h + table.
            "branches_pending_evidence": [FADE, MOMENTUM_FOLLOW] if pre else [],
            "routed_today": routed,
            "reason": ("board runner scans this family" if routed else
                       "in-play band: NO_BET by construction" if not pre else "family not in board scan"),
        })
    return rows


def summarize(rows: List[dict]) -> dict:
    pre = [r for r in rows if r["class"] == "pregame"]
    by_sport: Dict[str, Tuple[int, int]] = {}
    for s in sorted({r["sport"] for r in pre}):
        sr = [r for r in pre if r["sport"] == s]
        by_sport[s] = (sum(r["routed_today"] for r in sr), len(sr))
    return {
        "registered": len(rows), "pregame_registered": len(pre), "inplay_registered": len(rows) - len(pre),
        "routed": sum(r["routed_today"] for r in rows),
        "by_sport_routed_of_pregame": {k: list(v) for k, v in by_sport.items()},
        "status_counts": dict(Counter(r["status"] for r in rows)),
    }


def render_md(rows: List[dict]) -> str:
    s = summarize(rows)
    out = ["# Route coverage (W110.3)", "",
           f"Registered cells: {s['registered']} ({s['pregame_registered']} pre-game T1-T3, {s['inplay_registered']} in-play).",
           f"Routed today: {s['routed']} of {s['registered']}.", "",
           "| sport | routed / pre-game registered |", "|---|---|"]
    out += [f"| {k} | {a} / {b} |" for k, (a, b) in s["by_sport_routed_of_pregame"].items()]
    out += ["", "| market type | band | status | depth | branches | routed | reason |", "|---|---|---|---|---|---|---|"]
    for r in rows:
        out.append(f"| {r['market_type']} | {r['band']} | {r['status']} | {r['depth']} | "
                   f"{','.join(r['branches_with_evidence'])} | {'Y' if r['routed_today'] else '-'} | {r['reason']} |")
    return "\n".join(out) + "\n"


if __name__ == "__main__":  # pragma: no cover
    import json
    import sys
    rs = cell_rows()
    sys.stdout.write(render_md(rs) if "--md" in sys.argv else json.dumps({"summary": summarize(rs), "cells": rs}, indent=1))
