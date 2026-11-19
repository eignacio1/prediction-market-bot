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


LAYERS = ("1 simulated probability", "2 market state", "3 factor filters as splits", "4 tree chooses the arm",
          "5 per-leaf held-out net per arm", "6 risk and sizing rule", "7 execution with fills measured")
MIN_HELD_GAMES = 10


def filter_layer_sports() -> set:
    """W112.1: sports whose shadow rows really carry per-row filters today (the default supply has data for them)."""
    from prediction_market_bot.decision_trees import filter_supply as fsup

    out = set()
    try:
        fsup.nba_table()
        out.add("nba")
    except (OSError, ValueError):
        pass
    # W115.3 (GG-1941): the default FilterSupply never holds providers (nfl_adapter resolves them lazily), so the old test
    # ``default_supply().nfl_providers is not None`` was false on every host and NFL layer 3 could not count anywhere.
    try:
        from prediction_market_bot.nfl_engine.providers import default_nfl_providers
        if fsup.default_supply().nfl_providers is not None or default_nfl_providers() is not None:
            out.add("nfl")
    except Exception:  # noqa: BLE001 - a host that cannot load the snapshots shows no layer-3 NFL
        pass
    try:
        import glob
        import importlib
        importlib.import_module("prediction_market_bot.nhl_engine.filters")
        # W113.1: the per-row adapter is filter_supply.nhl_filters_for_row; it counts only where the compiled NHL event
        # store is present (a box without the store supplies "nhl_game_not_in_store" and shows no layer-3 NHL).
        if glob.glob(fsup.nhl_store_dir() + "/games_202[56].parquet"):
            out.add("nhl")
    except ImportError:
        pass
    return out


GG1771_EPOCH_ISO = "2026-11-06T01:03:42Z"  # NO-side demo fills before this were mirror-priced: not layer-7 evidence


def order_evidence(orders, fills_for=None, epoch_iso: str = GG1771_EPOCH_ISO) -> Tuple[set, set]:
    """(cells with layer-6 evidence, cells with layer-7 evidence) from the arm order log (W113.1 Part C).
    Layer 6: any logged arm order / would-order / skip for the cell carries a ``size_for`` decision for an arm other than NO_BET (the pregame_shadow package
    may not reach the sizing modules - tests/test_pregame_shadow_safety - so the decision is logged where the arm path runs).
    Layer 7: a placed (ok) ``arm_order`` in the current epoch whose fill outcome is MEASURED - ``fills_for(order_id, ticker)``
    answers with a dict that has a ``fills`` count (0 = no-fill recorded). Pre-epoch NO-side orders are dropped."""
    l6, l7 = set(), set()
    for r in orders or []:
        key = (r.get("market_type"), r.get("band"))
        sf = r.get("size_for")
        if isinstance(sf, dict) and sf.get("arm") not in (None, "NO_BET"):  # W116.3: a NO_BET size (0 by rule) is not sizing
            l6.add(key)
        if r.get("event") != "arm_order" or not r.get("ok") or not r.get("order_id") or fills_for is None:
            continue
        post = str(r.get("ts", "")) >= epoch_iso
        if not post:
            continue
        f = fills_for(r["order_id"], r.get("ticker"))
        if isinstance(f, dict) and f.get("fills") is not None:
            l7.add(key)
    return l6, l7


def ledger_evidence(rows) -> Dict[Tuple[str, str], dict]:
    """W117.3 (GG-1951): per (market_type, band), what the BOX shadow-ledger rows themselves carry.
    p: rows with a logged model p (``p_yes``)  -> layer 1.
    tested: rows whose router block logged a split verdict (``split_kept`` or ``split_logged_only`` non-empty) -> layer 3 STUMP
      (operator 11-17 17:45 PT: layer 3 is present when a cell's splits were tested on box rows and logged with their verdicts, kept or not).
    kept: rows with a non-empty ``split_kept`` -> layer 3 with a kept split (the stricter number, reported beside the stump)."""
    out: Dict[Tuple[str, str], dict] = {}
    for r in rows or []:
        key = (r.get("market_type"), r.get("band"))
        d = out.setdefault(key, {"rows": 0, "p": 0, "tested": 0, "kept": 0})
        rt = r.get("router") or {}
        d["rows"] += 1
        d["p"] += r.get("p_yes") is not None
        d["kept"] += bool(rt.get("split_kept"))
        d["tested"] += bool(rt.get("split_kept") or rt.get("split_logged_only"))
    return out


MIN_STUMP_ROWS = 30  # pooled fit rows a cell needs before its root has a family-level posterior to decide from


def stump_root(leaves: List[dict]) -> Optional[dict]:
    """W119.2 Part C: the tree of a cell whose leaves are thin (or all NO_BET) is a STUMP: the root picks an arm or NO_BET from the
    family-level posterior (the cell's leaves pooled, row-weighted mean net per contract on the fit window, per arm).
    Root arm = the best pooled arm when its pooled mean net is > 0, else NO_BET (a routing result, not a stop: the cell rides
    the market / takes no bet in these leaves). Returns None when the cell has fewer than MIN_STUMP_ROWS pooled fit rows."""
    pooled: Dict[str, List[float]] = {}
    for x in leaves:
        for arm, v in (x.get("fit") or {}).items():
            m, n = v
            a = pooled.setdefault(arm, [0.0, 0])
            a[0] += m * n
            a[1] += n
    rows = max((n for _, n in pooled.values()), default=0)
    if rows < MIN_STUMP_ROWS:
        return None
    means = {arm: (w / n) for arm, (w, n) in pooled.items() if n >= MIN_STUMP_ROWS}
    best = max(means, key=means.get) if means else None
    return {"arm": best if best is not None and means[best] > 0 else "NO_BET",
            "pooled_mean_net": {a: round(m, 5) for a, m in sorted(means.items())}, "rows": rows}


def d6_layers(leaf_map_doc: Optional[dict] = None, rows: Optional[List[dict]] = None, splits_doc: Optional[dict] = None,
              filter_sports: Optional[set] = None, orders=None, fills_for=None, box_evidence: Optional[dict] = None) -> List[dict]:
    """W111.3 Part C -- D6: for every registered cell, which of the seven layers are present AND evidenced.
    Evidence only, no credit for intent: layer 1 = the cell's leaves carry a logged model p (a MODEL_FADE fit entry);
    2 = the cell has leaves split on market state; 3 = factor filters reach the router as per-row splits (W112.1: the sport's
    adapter has data AND the cell's series has a KEPT tested split, i.e. a split a tested leaf uses); 4 = at least one non-thin leaf routed to an arm, or (W119.2) the cell's tree is a stump whose root decides from the pooled family posterior (stump_root; ``l4_stump``); 5 = at least one leaf with
    10+ held-out games; 6 = the cell's arm-path rows carry a size_for decision for an arm other than NO_BET (order_evidence); 7 = the cell's current-epoch arm orders have fills
    measured, fill or no-fill (shadow rows are not fills). A cell is 'wired' only with all seven. When it applies: pre-game cells (T1-T3).
    In-play bands score 0 layers by construction (router returns NO_BET).
    W117.3: with ``box_evidence`` (ledger_evidence of the host's shadow rows) layer 1 is ALSO present when the cell's rows carry a logged
    model p, and layer 3 is the approved STUMP rule (splits tested on box rows and logged with verdicts, kept or not) read from the rows,
    not from the split file (GG-1951). Each cell then reports ``l3_kept`` (a kept split on box rows) beside it. Without it: the old rules."""
    import json
    import os
    if leaf_map_doc is None:
        with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "leaf_map.json")) as fh:
            leaf_map_doc = json.load(fh)
    if splits_doc is None:
        with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "filter_splits.json")) as fh:
            splits_doc = json.load(fh)
    fsports = filter_layer_sports() if filter_sports is None else filter_sports
    kept = [x for x in splits_doc["splits"] if x["kept"]]
    by: Dict[Tuple[str, str], List[dict]] = {}
    for key, rec in leaf_map_doc["leaves"].items():
        sport, mt, band = key.split("|")[:3]
        by.setdefault((mt, band), []).append(rec)
    l6_cells, l7_cells = order_evidence(orders, fills_for)
    out = []
    for r in (rows if rows is not None else cell_rows()):
        ls = by.get((r["market_type"], r["band"]), [])
        ev = (box_evidence or {}).get((r["market_type"], r["band"]), {})
        l3_file = bool(ls) and str(r["sport"]).lower() in fsports and any(
            x["sport"].lower() == str(r["sport"]).lower() and x["series"] in (None, r.get("family")) for x in kept)
        arm_leaf = any(not x["thin"] and x["arm"] != "NO_BET" for x in ls)
        stump = None if arm_leaf else stump_root(ls)   # W119.2: no arm leaf -> the cell's tree is a stump (root decides)
        have = [
            any("MODEL_FADE" in x.get("fit", {}) for x in ls) or bool(ev.get("p")),
            bool(ls),
            bool(ev.get("tested")) if box_evidence is not None else l3_file,
            arm_leaf or stump is not None,
            any((x.get("test") or {}).get("test_n_games", 0) >= MIN_HELD_GAMES for x in ls),
            (r["market_type"], r["band"]) in l6_cells,
            (r["market_type"], r["band"]) in l7_cells,
        ]
        out.append({"market_type": r["market_type"], "band": r["band"], "sport": r["sport"], "layers": have,
                    "n_layers": sum(have), "wired": all(have),
                    "l4_stump": stump is not None, "stump_arm": stump["arm"] if stump else None,
                    "l3_kept": bool(ev.get("kept")) if box_evidence is not None else l3_file})
    return out


LAYER_NAMES = ("1 model p", "2 market state", "3 factor filters", "4 tree arm", "5 held-out net", "6 sizing", "7 fills")


def missing_one_layer(cells: List[dict]) -> List[dict]:
    """Cells that have six of seven layers, with the one they lack (W113.1 Part C)."""
    return [{"market_type": c["market_type"], "band": c["band"], "sport": c["sport"],
             "missing": LAYER_NAMES[c["layers"].index(False)]} for c in cells if c["n_layers"] == 6]


def d6_summary(cells: List[dict]) -> dict:
    """Per sport: cells wired end to end / registered, and cells per layer. The number scripts/distance_to_optimum reads."""
    sports: Dict[str, dict] = {}
    for c in cells:
        d = sports.setdefault(c["sport"], {"registered": 0, "wired": 0, "per_layer": [0] * 7, "l3_stump": 0, "l3_kept": 0, "l4_stump": 0})
        d["registered"] += 1
        d["l3_stump"] += bool(c["layers"][2])
        d["l3_kept"] += bool(c.get("l3_kept"))
        d["l4_stump"] += bool(c.get("l4_stump"))
        d["wired"] += c["wired"]
        for i, h in enumerate(c["layers"]):
            d["per_layer"][i] += h
    return {"wired": sum(d["wired"] for d in sports.values()), "registered": len(cells), "by_sport": sports}


if __name__ == "__main__":  # pragma: no cover
    import json
    import sys
    rs = cell_rows()
    sys.stdout.write(render_md(rs) if "--md" in sys.argv else json.dumps({"summary": summarize(rs), "cells": rs}, indent=1))
