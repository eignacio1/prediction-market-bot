"""W125.1 Part A (B-095 / B-113): the fill model, per arm x family x hours-to-start. PURE: records in, tables out, no I/O.

Input is placement.join.model_records output (one epoch at a time; the caller never pools the pre-epoch YES-only and the
post-epoch all-sides populations). Per cell it reports, DESCRIPTIVELY:

  fill rate        k fills / n placed, Wilson 95%
  adverse sel.     win rate filled vs unfilled (E3) and the edge gap (won - price | filled) - (won - price | unfilled)
  net per filled   settled (won - fill price - maker/taker fee actually charged) per FILLED contract, 90% game-clustered
                   (quant.variance.clustered_mean, CR1) with n in orders AND games
  markout          mean held-side mid minus fill price at +5 and +30 min, where the candle archive had it
  partial pool     the per-cell net-per-filled shrunk across cells of one arm with quant.variance.partial_pool

DESCRIPTIVE where it overlaps H-EXEC-4's frozen forward population (12_EXPLORATORY/edge_location/exec_fills): this table
never reads as a verdict on that test. A cell below MIN_GAMES games carries its numbers and ``supported`` False.
"""
from __future__ import annotations

import math
from typing import Dict, Iterable, List, Optional, Sequence

from prediction_market_bot.c5_execution.placement import model as pm
from prediction_market_bot.quant import variance as qv

MIN_GAMES = 20          # same bar as placement.policy.MIN_GAMES: games, not orders, are the n
LEVEL = 0.90


def family_of(series: Optional[str]) -> str:
    """Market family from the Kalshi series prefix (KXNBAGAME -> moneyline, ...SPREAD, ...TOTAL, ...TEAMTOTAL, props)."""
    s = str(series or "").upper()
    if "TEAMTOTAL" in s or "TT" == s[-2:]:
        return "team_total"
    if "SPREAD" in s:
        return "spread"
    if "TOTAL" in s:
        return "total"
    if "GAME" in s or "WINNER" in s or "ML" == s[-2:]:
        return "moneyline"
    if any(k in s for k in ("PTS", "REB", "AST", "3PT", "HIT", "HR", "SOG", "GOAL", "PASS", "RUSH", "REC", "TD", "PROP")):
        return "prop"
    return "other"


def _r(x: Optional[float], nd: int = 4) -> Optional[float]:
    return None if x is None or (isinstance(x, float) and math.isnan(x)) else round(x, nd)


def net_per_filled(r: dict) -> Optional[float]:
    """Settled value of one FILLED contract: won - fill price - the fee charged (maker when it rested, taker when it crossed).
    None until the market resolves or when the order did not fill. The fee is the table fee at the placement's own role."""
    if not r.get("filled") or r.get("won") is None or r.get("price") is None:
        return None
    fee = r.get("fee_per_contract")  # the fee Kalshi actually charged on the fills (maker or taker, per fill)
    if fee is None:
        fee = pm._fee(r, float(r["price"]), "taker" if r.get("placement") == "cross" else "maker")
    return (1.0 if r["won"] else 0.0) - float(r["price"]) - float(fee)


def cell_key(r: dict) -> str:
    return "|".join((str(r.get("arm")), family_of(r.get("series")), pm.hours_bucket(r.get("hours"))))


def _mean(v: Sequence[float]) -> Optional[float]:
    return sum(v) / len(v) if v else None


def cell_row(rs: List[dict], markouts: Optional[Dict[str, List[float]]] = None) -> dict:
    n = len(rs)
    k = sum(1 for r in rs if r.get("filled"))
    lo, hi = pm.wilson(k, n)
    f = [(r, net_per_filled(r)) for r in rs]
    f = [(r, v) for r, v in f if v is not None]
    cm = qv.clustered_mean([v for _, v in f], [pm.game_of(r) for r, _ in f], LEVEL) if f else None
    wf = [1.0 if r["won"] else 0.0 for r in rs if r.get("filled") and r.get("won") is not None]
    wu = [1.0 if r["won"] else 0.0 for r in rs if r.get("filled") is False and r.get("won") is not None]
    ef = [pm.edge(r) for r in rs if r.get("filled") and pm.edge(r) is not None]
    eu = [pm.edge(r) for r in rs if r.get("filled") is False and pm.edge(r) is not None]
    games = len({pm.game_of(r) for r in rs})
    out = {"n": n, "fills": k, "p_fill": _r(k / n) if n else None, "fill_ci": [_r(lo), _r(hi)], "n_games": games,
           "win_filled": _r(_mean(wf)), "win_unfilled": _r(_mean(wu)), "n_won_f": len(wf), "n_won_u": len(wu),
           "adverse_sel": _r(_mean(ef) - _mean(eu)) if ef and eu else None,
           "net_filled": _r(cm["mean"]) if cm else None,
           "net_filled_ci90": [_r(cm["lo"]), _r(cm["hi"])] if cm else [None, None],
           "n_settled_filled": len(f), "n_games_settled_filled": cm["n_clusters"] if cm else 0,
           "supported": bool(cm and cm["n_clusters"] >= MIN_GAMES)}
    if markouts:
        out["markout"] = {h: {"mean": _r(_mean(v)), "n": len(v)} for h, v in sorted(markouts.items())}
    return out


def pooled(rows_by_cell: Dict[str, dict]) -> Dict[str, dict]:
    """Partial pooling of net-per-filled across the cells of ONE arm (exchangeable: same arm, other families / horizons). Needs a
    finite positive clustered se per cell; a cell without one is reported unpooled. Returns {cell: {shrunk, lo, hi, B}} and the
    arm's mu / tau under key "_arm|<arm>"."""
    by_arm: Dict[str, Dict[str, tuple]] = {}
    for c, v in rows_by_cell.items():
        ci = v.get("net_filled_ci90") or [None, None]
        if v.get("net_filled") is None or ci[0] is None or ci[1] is None:
            continue
        se = (ci[1] - ci[0]) / (2 * qv._z(LEVEL))
        if se > 0:
            by_arm.setdefault(c.split("|")[0], {})[c] = (v["net_filled"], se)
    out: Dict[str, dict] = {}
    for arm, cells in by_arm.items():
        if len(cells) < 2:
            continue
        pp = qv.partial_pool(cells, LEVEL)
        out["_arm|" + arm] = {"mu": _r(pp["mu"]), "tau": _r(pp["tau"]), "k": len(cells)}
        for c in pp["cells"]:
            out[c["cell"]] = {"shrunk": _r(c["shrunk"]), "lo": _r(c["lo"]), "hi": _r(c["hi"]), "B": _r(c["B"], 3)}
    return out


def fill_model(records: Iterable[dict], min_orders: int = 5) -> dict:
    """The whole table for one epoch. Markouts come from each record's own ``markout`` {"h5": x, "h30": y} (filled orders only).
    Cells under ``min_orders`` placed are counted, not listed (the box output is capped at 60 KB)."""
    recs = [r for r in records if r.get("filled") is not None]
    cells: Dict[str, List[dict]] = {}
    for r in recs:
        cells.setdefault(cell_key(r), []).append(r)
    rows: Dict[str, dict] = {}
    dropped = 0
    for c, rs in sorted(cells.items()):
        if len(rs) < min_orders:
            dropped += 1
            continue
        mk: Dict[str, List[float]] = {}
        for r in rs:
            for h, v in (r.get("markout") or {}).items():
                if v is not None and h in ("h5", "h30") and r.get("filled"):
                    mk.setdefault(h, []).append(v)
        rows[c] = cell_row(rs, mk)
    pool = pooled(rows)
    for c, v in rows.items():
        if c in pool:
            v["pooled"] = pool[c]
    return {"cells": rows, "arm_pool": {k: v for k, v in pool.items() if k.startswith("_arm|")},
            "cells_below_min_orders_dropped": dropped, "n_orders": len(recs), "min_games": MIN_GAMES, "level": LEVEL}
