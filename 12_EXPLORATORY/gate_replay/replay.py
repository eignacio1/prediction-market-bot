"""W85.2 Part A: replay of the operator-accepted gate on the demo orders already placed.

READ-ONLY on a local snapshot of the box's shadow rows, order log and markouts. Counts come first;
the settlement-minus-price block is DESCRIPTIVE and no gate parameter is chosen from it.

Accepted gate (operator, 2026-10-21 20:28 PT): one position per market per band; the model is pulled
toward the market by its measured skill; an order goes in only when what is left clears the fee plus
the model's measured error; a game's ladder counts as one exposure.

usage: python3 replay.py SNAPSHOT_DIR [OUT_DIR]
"""
from __future__ import annotations

import csv
import json
import math
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from _fence import safe_out  # noqa: E402

SPORTS = (("KXMLB", "MLB"), ("KXNBA", "NBA"), ("KXNHL", "NHL"), ("KXNFL", "NFL"))
# Skill weight per frozen model from held-out Brier AGAINST THE MARKET. No models/*heldout* file carries
# a market-referenced Brier (they compare to climatology only), so the rule's fallback applies: 0.
SKILL_W_RULE = 0.0
SENSITIVITY_W = (0.0, 0.1, 0.25, 0.5, 1.0)  # counts only; nothing is selected from outcomes
FAR = 0.25  # |mid - 0.5| above this = "far ladder strike"


def sport_of(ticker: Any) -> str:
    t = str(ticker or "").upper()
    return next((s for p, s in SPORTS if t.startswith(p)), "OTHER")


def game_of(ticker: Any) -> str:
    parts = str(ticker or "").upper().split("-")
    return f"{sport_of(ticker)}|{parts[1] if len(parts) > 1 else parts[0]}"


def jl(path: Path):
    with open(path) as fh:
        for line in fh:
            line = line.strip()
            if line:
                try:
                    yield json.loads(line)
                except ValueError:
                    continue


def load_rows(snap: Path) -> Dict[Tuple[str, str], dict]:
    rows: Dict[Tuple[str, str], dict] = {}
    for d in (snap / "PS", snap / "nhl"):
        for f in sorted(d.glob("*.jsonl")):
            for r in jl(f):
                rows[(r["run_id"], r["market_ticker"])] = r
    for d in (snap / "settled", snap / "nhl_settled"):
        for f in sorted(d.glob("*.jsonl")):
            for r in jl(f):
                y = r.get("y", r.get("outcome"))
                k = (r["run_id"], r["market_ticker"])
                if y is not None and k in rows:
                    rows[k]["_y"] = float(y)
    return rows


def sigma_table(rows: Dict[Tuple[str, str], dict]) -> Dict[Tuple[str, str], float]:
    """Spread (sd) of model-minus-market disagreement per (sport, market_type), over ledger rows.

    Substitute for held-out disagreement spread, which no artifact carries. Uses no outcomes."""
    acc: Dict[Tuple[str, str], List[float]] = defaultdict(list)
    for r in rows.values():
        acc[(r["sport"], r["market_type"])].append(r["p_yes"] - r["mid"])
    out = {}
    for k, v in acc.items():
        m = sum(v) / len(v)
        out[k] = math.sqrt(sum((x - m) ** 2 for x in v) / max(len(v) - 1, 1))
    return out


def side_of(order: dict, row: dict) -> str:
    s = str(order.get("side") or "").lower()
    if s in ("yes", "no"):
        return s
    return "yes" if row["e_net_yes_k007"] >= row["e_net_no_k007"] else "no"


def adj_edge(row: dict, side: str, w: float) -> float:
    """Net edge after pulling the model toward the market: p_adj = mid + w*(p - mid)."""
    p = row["mid"] + w * (row["p_yes"] - row["mid"])
    if side == "yes":
        return p - row["yes_ask"] - row["fee_k007"]
    return row["yes_bid"] - p - row["fee_k007"]


def payoff(order_price_yes: float, side: str, y: float) -> float:
    """As-if-filled at the limit: settlement minus price paid, per contract."""
    return (y - order_price_yes) if side == "yes" else ((1 - y) - (1 - order_price_yes))


def clustered(by_game: Dict[str, List[float]]) -> Optional[dict]:
    n = sum(len(v) for v in by_game.values())
    if n == 0:
        return None
    m = sum(sum(v) for v in by_game.values()) / n
    var = sum((sum(v) - m * len(v)) ** 2 for v in by_game.values()) / (n * n)
    se = math.sqrt(var)
    return {"n": n, "games": len(by_game), "mean": round(m, 4), "lo95": round(m - 1.96 * se, 4),
            "hi95": round(m + 1.96 * se, 4)}


def main(snap: Path, out_dir: Path) -> None:
    rows = load_rows(snap)
    sig = sigma_table(rows)
    orders = []
    unmatched = 0
    for e in jl(snap / "demo_fill_policy.jsonl"):
        if e.get("event") != "shadow_order" or not e.get("ok"):
            continue
        rid, _, tk = str(e.get("row_id", "")).partition("|")
        r = rows.get((rid, tk))
        if r is None:
            # NHL row_ids carry a T-prefix label (e.g. T3-20261014T0006); fall back to ticker + nearest ts
            unmatched += 1
            continue
        orders.append((e, r))
    report: Dict[str, Any] = {"snapshot_rows": len(rows), "ok_orders": len(orders), "unmatched_ok_orders": unmatched,
                              "skill_weight_rule": SKILL_W_RULE, "far_threshold": FAR,
                              "sigma_note": "sd of (p_yes - mid) per (sport, market_type) over ledger rows; substitute for held-out spread (none exists)",
                              "cells": {}, "gate": {}, "descriptive": {}}
    cell: Dict[Tuple[str, str, str], List[Tuple[dict, dict]]] = defaultdict(list)
    for e, r in orders:
        cell[(r["sport"], r["band"], r["market_type"])].append((e, r))

    csv_rows = []
    for (sp, band, mt), lst in sorted(cell.items()):
        positions = {(r["market_ticker"], r["band"]) for _, r in lst}
        games = {game_of(r["market_ticker"]) for _, r in lst}
        ladders: Dict[Tuple[str, str], List[str]] = defaultdict(list)
        for e, r in lst:
            ladders[(game_of(r["market_ticker"]), r["market_type"])].append(side_of(e, r))
        multi = [v for v in ladders.values() if len(v) >= 2]
        agree = [max(v.count("yes"), v.count("no")) / len(v) for v in multi]
        far = sum(1 for _, r in lst if abs(r["mid"] - 0.5) > FAR) / len(lst)
        rec = {"orders": len(lst), "positions": len(positions), "games": len(games),
               "orders_per_position": round(len(lst) / len(positions), 2),
               "orders_per_game": round(len(lst) / len(games), 1),
               "far_strike_share": round(far, 3),
               "ladders_multi": len(multi),
               "ladder_side_agreement": round(sum(agree) / len(agree), 3) if agree else None}
        report["cells"]["%s|%s|%s" % (sp, band, mt)] = rec
        csv_rows.append(dict(sport=sp, band=band, market_type=mt, **rec))

    # gate replay
    for w in SENSITIVITY_W:
        agg: Dict[Tuple[str, str], Dict[str, Any]] = {}
        kept_by_class: Dict[str, Dict[str, List[float]]] = {"kept": defaultdict(list), "dropped": defaultdict(list)}
        seen_pos = set()
        placed_sorted = sorted(orders, key=lambda x: x[1]["ts_utc"])
        for e, r in placed_sorted:
            sp, band = r["sport"], r["band"]
            side = side_of(e, r)
            a = agg.setdefault((sp, band), {"orders_kept": 0, "orders_total": 0, "positions": set(), "ladders": set()})
            a["orders_total"] += 1
            sg = sig[(sp, r["market_type"])]
            ok = adj_edge(r, side, w) > sg
            pk = (r["market_ticker"], band)
            kept = ok and pk not in seen_pos
            if kept:
                seen_pos.add(pk)
                a["orders_kept"] += 1
                a["positions"].add(pk)
                a["ladders"].add((game_of(r["market_ticker"]), r["market_type"], side))
            if "_y" in r:
                price = e.get("price_yes", r["mid"])
                kept_by_class["kept" if kept else "dropped"][game_of(r["market_ticker"])].append(
                    payoff(price, side, r["_y"]))
        report["gate"]["w=%s" % w] = {
            "%s|%s" % k: {"orders_total": v["orders_total"], "orders_kept": v["orders_kept"],
                          "positions_kept": len(v["positions"]), "ladder_exposures_kept": len(v["ladders"])}
            for k, v in sorted(agg.items())}
        report["descriptive"]["w=%s" % w] = {"label": "DESCRIPTIVE ONLY; never used to choose a parameter",
                                             "kept": clustered(kept_by_class["kept"]),
                                             "dropped": clustered(kept_by_class["dropped"])}

    safe_out(out_dir / "replay_W85_2.json").write_text(json.dumps(report, indent=1, sort_keys=True))
    with open(safe_out(out_dir / "replay_W85_2_cells.csv"), "w", newline="") as fh:
        wr = csv.DictWriter(fh, fieldnames=list(csv_rows[0]))
        wr.writeheader()
        wr.writerows(csv_rows)
    print(json.dumps({k: report[k] for k in ("snapshot_rows", "ok_orders", "unmatched_ok_orders")}))


if __name__ == "__main__":
    main(Path(sys.argv[1]), Path(sys.argv[2]) if len(sys.argv) > 2 else Path(__file__).resolve().parent)
