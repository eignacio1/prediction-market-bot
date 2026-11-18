#!/usr/bin/env python3
"""W115.3 / B-091: one real game per in-season sport, followed through the seven D6 layers ON THIS HOST. Read-only.

d6_read counts cells; it cannot show where a row stops. This picks, per sport (NBA, NFL, NHL), the started game of the last
--days days with the most cells in the shadow ledgers, and prints for each of its cells what every layer actually wrote:
  1 model p        rows with p_yes, model ids                      (shadow ledger row)
  2 market state   mid, horizon, the move source, the leaf         (shadow ledger row, router block)
  3 factor filters filters_n, filters_note, kept splits            (router block)
  4 tree arm       router branch / reason                          (router block)
  5 held-out net   the leaf's held-out games                       (repo leaf_map.json: NOT a box row)
  6 sizing         size_for decisions on the game's arm-path rows  (logs/arm_orders/orders.jsonl)
  7 fills          the game's ok arm orders and their fill lookups (order log + demo GET, capped)
next to what coverage.d6_layers says for the same cell, so a rule the rows cannot satisfy shows up as a disagreement.
Also host facts (filter data, NFL providers, NHL store) and, for one ERROR row per sport, the exception re-raised with its
message. Writes nothing; prints one JSON document. Box Python is 3.9: timestamps go through arm_orders_read.parse_ts.
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import sys
import traceback
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))
sys.path.insert(0, str(REPO / "src"))
import arm_orders_read as aor  # noqa: E402

SPORTS = ("NBA", "NFL", "NHL")
TAIL_BYTES = 6_000_000
MAX_FILL_LOOKUPS = 8


def ledger_files(repo: Path = REPO) -> List[Path]:
    base = Path(os.environ.get("PM_SHADOW_DIR", str(repo / "exp_output" / "PREGAME_SHADOW")))
    return sorted(base.glob("*.jsonl")) + sorted((repo / "data" / "shadow" / "nhl").glob("*_T[123].jsonl"))


def tail_rows(path: Path, since: datetime) -> List[dict]:
    out: List[dict] = []
    try:
        size = path.stat().st_size
        with path.open("rb") as fh:
            fh.seek(max(0, size - TAIL_BYTES))
            lines = fh.read().decode("utf-8", "ignore").splitlines()
    except OSError:
        return out
    for line in lines[1:] if size > TAIL_BYTES else lines:
        try:
            r = json.loads(line)
        except ValueError:
            continue
        ts = aor.parse_ts(r.get("ts_utc")) if isinstance(r, dict) else None
        if ts is not None and ts >= since and r.get("market_ticker") and r.get("event_ticker"):
            r["_file"] = path.name
            out.append(r)
    return out


def game_key(event_ticker: Any) -> str:
    e = str(event_ticker or "")
    return e.split("-", 1)[1] if "-" in e else e


def pick_game(rows: List[dict], now: datetime) -> Optional[str]:
    """The started game with the most distinct cells, then the most rows; any game when none has started."""
    by: Dict[str, dict] = {}
    for r in rows:
        g = by.setdefault(game_key(r["event_ticker"]), {"cells": set(), "n": 0, "started": False})
        g["cells"].add((r.get("market_type"), r.get("band")))
        g["n"] += 1
        st = aor.parse_ts(r.get("start_time_utc"))
        g["started"] = g["started"] or (st is not None and st <= now)
    if not by:
        return None
    return max(by, key=lambda k: (by[k]["started"], len(by[k]["cells"]), by[k]["n"], k))


def _top(c: Counter, n: int = 4) -> dict:
    return {str(k): v for k, v in c.most_common(n)}


def _rng(vals: list) -> Optional[list]:
    v = [float(x) for x in vals if isinstance(x, (int, float))]
    return [round(min(v), 4), round(max(v), 4)] if v else None


def cell_layers(rows: List[dict], leaves: dict) -> dict:
    """What layers 1-5 look like in the rows of ONE cell."""
    rt = [r.get("router") or {} for r in rows]
    routed = [x for x in rt if x.get("branch") not in (None, "ERROR")]
    leaf_ids = Counter(x.get("leaf_id") for x in routed if x.get("leaf_id"))
    held = {}
    for lid in list(leaf_ids)[:6]:
        rec = leaves.get(lid) or {}
        held[lid] = {"arm": rec.get("arm"), "thin": rec.get("thin"), "test_n_games": (rec.get("test") or {}).get("test_n_games")}
    return {
        "rows": len(rows), "file": rows[0].get("_file"),
        "L1_rows_with_p": sum(r.get("p_yes") is not None for r in rows), "L1_model_ids": _top(Counter(r.get("model_id") for r in rows), 2),
        "L2_mid": _rng([r.get("mid") for r in rows]), "L2_horizon_h": _rng([r.get("horizon_hours_to_start") for r in rows]),
        "L2_rows_with_router": sum(bool(x) for x in rt), "L2_move_source": _top(Counter(x.get("move_source") for x in rt if x)),
        "L3_filters_n": _rng([x.get("filters_n") for x in rt if x]), "L3_filters_note": _top(Counter(x.get("filters_note") for x in rt if x)),
        "L3_rows_with_kept_split": sum(bool(x.get("split_kept")) for x in rt),
        "L4_branch": _top(Counter(x.get("branch", "NO_ROUTER_BLOCK") if x else "NO_ROUTER_BLOCK" for x in rt), 6),
        "L4_reason": _top(Counter(x.get("reason") for x in rt if x)),
        "L5_leaves_seen": held,
        "row_size_for": sum(isinstance(r.get("size_for"), dict) for r in rows),
    }


def order_layers(orders: List[dict], fills_for, budget: List[int]) -> dict:
    """Layers 6-7 for the arm-path rows of ONE cell of the game."""
    ev = Counter((o.get("event"), str(o.get("reason") or "").split(":")[0], o.get("arm")) for o in orders)
    ok = [o for o in orders if o.get("event") == "arm_order" and o.get("ok") and o.get("order_id")]
    post = [o for o in ok if str(o.get("ts", "")) >= "2026-11-06T01:03:42Z"]
    looks = []
    for o in post:
        if fills_for is None or budget[0] <= 0:
            break
        budget[0] -= 1
        try:
            f = fills_for(o["order_id"], o.get("ticker"))
        except Exception as e:  # noqa: BLE001
            f = {"error": type(e).__name__}
        looks.append({"ticker": o.get("ticker"), "side": o.get("side"), "stake_usd": o.get("stake_usd"), "ts": o.get("ts"),
                      "fills": (f or {}).get("fills") if isinstance(f, dict) else None,
                      "lookup": {k: v for k, v in (f or {}).items() if k in ("error", "status", "note")} if isinstance(f, dict) else str(f)})
    return {"arm_path_rows": len(orders), "L6_rows_with_size_for": sum(isinstance(o.get("size_for"), dict) for o in orders),
            "events": {"|".join(map(str, k)): v for k, v in ev.most_common(8)},
            "L7_ok_orders": len(ok), "L7_ok_orders_post_epoch": len(post), "L7_fill_lookups": looks}


def reraise(row: dict) -> dict:
    """Re-run the filter supply and the router on a logged row and return the exception text (nothing is written)."""
    from prediction_market_bot.decision_trees import filter_supply as fsup, shadow_route as sr
    out: dict = {"market_ticker": row.get("market_ticker"), "ts_utc": row.get("ts_utc"), "logged_reason": (row.get("router") or {}).get("reason"),
                 "row_keys_none": sorted(k for k in ("p_yes", "yes_bid", "yes_ask", "mid", "half_spread", "horizon_hours_to_start", "band") if row.get(k) is None)}
    clean = {k: v for k, v in row.items() if k not in ("router", "_file")}
    try:
        flt, note = fsup.default_supply().for_row(clean)
        out["filters"] = {"n": len(flt) if flt else 0, "note": note}
    except Exception:  # noqa: BLE001
        flt, out["filters"] = None, {"raised": traceback.format_exc().splitlines()[-3:]}
    try:
        r = sr.route_row(clean, str(row["market_ticker"]).split("-", 1)[0], prev_mid=row.get("mid"), filters=flt)
        out["now_routes"] = {k: r.get(k) for k in ("branch", "leaf_id", "reason")}
    except Exception:  # noqa: BLE001
        out["router_raised"] = traceback.format_exc().splitlines()[-4:]
    if str(row.get("sport", "")).upper() == "NFL" and (out["filters"].get("note") or "").startswith("filters_error"):
        try:
            fsup.nfl_adapter(clean)
        except Exception:  # noqa: BLE001
            out["nfl_adapter_raised"] = traceback.format_exc().splitlines()[-4:]
    return out


def host_facts(repo: Path = REPO) -> dict:
    from prediction_market_bot.decision_trees import coverage, filter_supply as fsup
    out: dict = {"python": sys.version.split()[0]}
    fd = repo / "src" / "prediction_market_bot" / "decision_trees" / "filter_data"
    out["filter_data_files"] = sorted(p.name for p in fd.glob("*")) if fd.is_dir() else "MISSING DIR"
    try:
        from prediction_market_bot.nfl_engine.providers import NflProviders
        NflProviders(live=False)
        out["nfl_providers"] = "loads"
    except Exception:  # noqa: BLE001
        out["nfl_providers"] = {"raised": traceback.format_exc().splitlines()[-3:]}
    d = fsup.nhl_store_dir()
    out["nhl_store"] = {"dir": d, "exists": os.path.isdir(d), "games": sorted(os.path.basename(p) for p in glob.glob(d + "/games_202[56].parquet"))}
    out["layer3_sports_by_rule"] = sorted(coverage.filter_layer_sports())
    try:
        from prediction_market_bot.decision_trees import arm_orders as ao
        out["arm_orders_mode"] = ao.mode()
    except Exception as e:  # noqa: BLE001
        out["arm_orders_mode"] = "unreadable:" + type(e).__name__
    return out


def build(rows: List[dict], orders: List[dict], fills_for, now: datetime, leaf_doc: Optional[dict] = None,
          d6_cells: Optional[List[dict]] = None, with_reraise: bool = True) -> dict:
    if leaf_doc is None:
        leaf_doc = json.loads((REPO / "src" / "prediction_market_bot" / "decision_trees" / "leaf_map.json").read_text())
    leaves = leaf_doc.get("leaves", {})
    rule = {(c["market_type"], c["band"]): c for c in (d6_cells or [])}
    budget = [MAX_FILL_LOOKUPS * len(SPORTS)]
    out: dict = {"read_utc": now.strftime("%Y-%m-%dT%H:%M:%SZ"), "sports": {}}
    for sport in SPORTS:
        srows = [r for r in rows if str(r.get("sport", "")).upper() == sport]
        board: Dict[str, dict] = {}
        for r in srows:  # every cell of the sport in the window: the row-side evidence next to the rule
            b = board.setdefault(f"{r.get('market_type')}|{r.get('band')}", {"rows": 0, "p": 0, "router": 0, "routed": 0, "error": 0, "filters": 0, "split_kept": 0, "arm": 0})
            x = r.get("router") or {}
            b["rows"] += 1
            b["p"] += r.get("p_yes") is not None
            b["router"] += bool(x)
            b["routed"] += x.get("branch") not in (None, "ERROR")
            b["error"] += x.get("branch") == "ERROR"
            b["filters"] += bool(x.get("filters_n"))
            b["split_kept"] += bool(x.get("split_kept"))   # W116.3 (GG-1951): layer 3 as rows saw it, window-wide, next to the file rule
            b["arm"] += x.get("branch") not in (None, "ERROR", "NO_BET")
        errs = Counter((r.get("router") or {}).get("reason") for r in srows if (r.get("router") or {}).get("branch") == "ERROR")
        s: dict = {"rows_in_window": len(srows), "cells_in_window": board, "error_reasons": _top(errs, 6)}
        first_err = next((r for r in srows if (r.get("router") or {}).get("branch") == "ERROR"), None)
        first_nr = next((r for r in srows if not r.get("router")), None)
        if with_reraise:
            s["error_row_rerun"] = reraise(first_err) if first_err else None
            s["no_router_row_rerun"] = reraise(first_nr) if first_nr else None
        g = pick_game(srows, now)
        s["game"] = g
        if g:
            grows = [r for r in srows if game_key(r["event_ticker"]) == g]
            gord = [o for o in orders if game_key(o.get("event_ticker")) == g and str(o.get("sport", "")).upper() == sport]
            s["game_start_utc"] = next((r.get("start_time_utc") for r in grows if r.get("start_time_utc")), None)
            cells = {}
            for key in sorted({(r.get("market_type"), r.get("band")) for r in grows}, key=str):
                c = cell_layers([r for r in grows if (r.get("market_type"), r.get("band")) == key], leaves)
                c.update(order_layers([o for o in gord if (o.get("market_type"), o.get("band")) == key], fills_for, budget))
                rc = rule.get(key)
                c["rule_says_layers"] = [int(bool(x)) for x in rc["layers"]] if rc else None
                cells[f"{key[0]}|{key[1]}"] = c
            s["cells"] = cells
            s["arm_path_rows_no_cell_match"] = sum(1 for o in gord if f"{o.get('market_type')}|{o.get('band')}" not in cells)
        out["sports"][sport] = s
    return out


def main(argv: Optional[list] = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--days", type=float, default=3.0)
    ap.add_argument("--log", default=str(aor.LOG))
    ap.add_argument("--no-fills", action="store_true")
    a = ap.parse_args(argv)
    now = datetime.now(timezone.utc)
    since = now - timedelta(days=a.days)
    files = ledger_files()
    rows: List[dict] = []
    for f in files:
        rows += tail_rows(f, since)
    orders = [o for o in aor.load_rows(Path(a.log)) if (aor.parse_ts(o.get("ts")) or now) >= since]
    fills_for, note = (None, "fills skipped: --no-fills") if a.no_fills else aor.make_fills_for(orders)
    from prediction_market_bot.decision_trees import coverage
    d6 = coverage.d6_layers(orders=orders, fills_for=None)
    doc = build(rows, orders, fills_for, now, d6_cells=d6)
    doc.update({"window_days": a.days, "ledger_files": len(files), "arm_order_rows_in_window": len(orders),
                "fills_note": note or "ok", "host": host_facts(),
                "rule_note": "rule_says_layers = coverage.d6_layers on the window's order rows, fills not looked up (layer 7 shows 0 here)"})
    print(json.dumps(doc, indent=1, sort_keys=True, default=str))
    return 0


if __name__ == "__main__":
    sys.exit(main())
