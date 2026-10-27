"""W89.2 -- calibration of Kalshi's own sports prices by price bucket, time-to-start and book depth, plus
overreaction after large pre-game moves. Measures the MARKET only: no model, order, gate or sizing is touched.

Methods (each carries when-it-applies; see results_W89.md for the measured results with n and intervals):

* cell_test -- cluster-robust z-test that mean(y - p) = 0 within a cell (rows grouped by game).
  Applies when a cell has >= MIN_EVENTS games and >= MIN_EXPECTED expected events on both sides (so the normal
  approximation holds); otherwise the cell is DESCRIPTIVE and carries no p-value.
* net_edge -- mean per-contract P&L of the side the cell's gap points to, after the k007 taker fee, entered at
  the quote (YES at the ask, NO at 1 - bid), with a game-clustered bootstrap interval.
* reversion cells -- after a pre-game one-step move of >= MOVE_MIN, mean of -sign(move) * (later mid - mid after
  the move), minus a round-trip cost; clustered by game. Pre-game only: with no score in play, a pre-game move
  is news or flow, never a score change.
"""
from __future__ import annotations

import json
import math
import re
from collections import defaultdict
from datetime import datetime, timezone
from statistics import NormalDist
from zoneinfo import ZoneInfo

from prediction_market_bot.quant.inference import benjamini_hochberg, cluster_bootstrap
from prediction_market_bot.quant.money import fee_k007

_N = NormalDist()
ET = ZoneInfo("America/New_York")
EDGES = [0.0, 0.01, 0.05, 0.10, 0.15, 0.20, 0.25, 0.30, 0.35, 0.40, 0.45, 0.50, 0.55, 0.60, 0.65, 0.70, 0.75,
         0.80, 0.85, 0.90, 0.95, 0.99, 1.0001]
MIN_EVENTS, MIN_EXPECTED = 30, 5.0
MOVE_MIN = 0.05
BH_Q = 0.10
SEED = 20261027

_TK = re.compile(r"-(\d{2})([A-Z]{3})(\d{2})(\d{4})?")
_MON = {m: i for i, m in enumerate("JAN FEB MAR APR MAY JUN JUL AUG SEP OCT NOV DEC".split(), 1)}


def parse_ts(s: str) -> float:
    """Tolerant ISO-8601 parse (Kalshi emits 5-digit fractional seconds). Returns epoch seconds."""
    s = re.sub(r"Z$", "+00:00", s)
    m = re.match(r"(.*?)(\.\d+)?(\+.*)?$", s)
    base, frac, tz = m.group(1), m.group(2) or "", m.group(3) or "+00:00"
    frac = (frac + "000000")[:7] if frac else ""
    return datetime.fromisoformat(base + frac + tz).timestamp()


def game_start(event_ticker: str):
    """(start_epoch or None, game_date_ET) from the event ticker. MLB carries HHMM (read as ET -- assumption,
    consistent with run_ts vs ticker on a 2026-10-27 20:00 game); NFL carries the date only, so start is None."""
    m = _TK.search(event_ticker)
    if not m:
        return None, None
    yy, mon, dd, hhmm = m.groups()
    y, mo, d = 2000 + int(yy), _MON[mon], int(dd)
    if hhmm:
        dt = datetime(y, mo, d, int(hhmm[:2]), int(hhmm[2:]), tzinfo=ET)
        return dt.timestamp(), dt.date()
    return None, datetime(y, mo, d).date()


def tier(event_ticker: str, ts: float):
    """Time-to-start tier at snapshot time ts, or None if the game has started / is unparseable.
    MLB: hours before first pitch. NFL (date only): ET calendar days before game date."""
    start, gdate = game_start(event_ticker)
    if gdate is None:
        return None
    if start is not None:
        h = (start - ts) / 3600.0
        if h <= 0:
            return None
        return "T>24h" if h >= 24 else "T6-24h" if h >= 6 else "T2-6h" if h >= 2 else "T0-2h"
    days = (gdate - datetime.fromtimestamp(ts, ET).date()).days
    if days < 0:
        return None
    return "D0" if days == 0 else "D1" if days == 1 else "D2+"


def bucket(p: float) -> int:
    for i in range(len(EDGES) - 1):
        if EDGES[i] <= p < EDGES[i + 1]:
            return i
    return len(EDGES) - 2


def bucket_label(i: int) -> str:
    return f"{int(round(EDGES[i] * 100))}-{min(int(round(EDGES[i + 1] * 100)), 100)}c"


def side_pnl(side: str, y: float, bid: float, ask: float) -> float:
    """Per-contract P&L after k007 taker fee: YES bought at the ask, NO at 1 - bid."""
    if side == "yes":
        return y - ask - fee_k007(ask)
    q = 1.0 - bid
    return (1.0 - y) - q - fee_k007(q)


def cell_test(rows: list[dict], boot: int = 1000) -> dict:
    """rows: dicts with keys game, p, y, bid, ask. Returns n, games, pbar, f, gap, z, p_value (None when DESCRIPTIVE),
    the side the gap points to, and that side's mean net P&L with a game-clustered 95% interval."""
    n = len(rows)
    games = defaultdict(list)
    for r in rows:
        games[r["game"]].append(r)
    g = len(games)
    pbar = sum(r["p"] for r in rows) / n
    f = sum(r["y"] for r in rows) / n
    gap = f - pbar
    testable = g >= MIN_EVENTS and n * pbar >= MIN_EXPECTED and n * (1 - pbar) >= MIN_EXPECTED
    out = {"n": n, "games": g, "pbar": pbar, "f": f, "gap": gap, "testable": testable, "z": None, "p_value": None}
    if testable:
        res = [r["y"] - r["p"] for r in rows]
        mu = sum(res) / n
        s2 = sum((sum(r["y"] - r["p"] - mu for r in grp)) ** 2 for grp in games.values())
        se = math.sqrt(s2) / n
        if se > 0:
            out["z"] = mu / se
            out["p_value"] = 2 * (1 - _N.cdf(abs(out["z"])))
    side = "yes" if gap > 0 else "no"
    out["side"] = side
    vals = {k: [side_pnl(side, r["y"], r["bid"], r["ask"]) for r in grp] for k, grp in games.items()}
    mean, lo, hi = cluster_bootstrap(vals, b=boot, seed=SEED)
    out.update(net_mean=mean, net_lo=lo, net_hi=hi)
    return out


def bh_flags(cells: dict, q: float = BH_Q) -> dict:
    """Run BH across every testable cell (family-wise statement: FDR <= q over ALL testable cells in `cells`)."""
    keys = [k for k, c in cells.items() if c["p_value"] is not None]
    flags = benjamini_hochberg([cells[k]["p_value"] for k in keys], q)
    for c in cells.values():
        c["bh"] = False
    for k, fl in zip(keys, flags):
        cells[k]["bh"] = bool(fl)
    return {"tested": len(keys), "flagged": sum(flags), "q": q}


def reversion_cell(moves: list[dict], boot: int = 1000) -> dict:
    """moves: dicts with game, rev (= -sign(move) * (later mid - mid after move)), cost. Net = mean(rev - cost),
    game-clustered 95% interval and one-sided-free two-sided cluster-robust z for net != 0."""
    games = defaultdict(list)
    for m in moves:
        games[m["game"]].append(m["rev"] - m["cost"])
    n = sum(len(v) for v in games.values())
    g = len(games)
    mean, lo, hi = cluster_bootstrap(games, b=boot, seed=SEED)
    gross = sum(m["rev"] for m in moves) / n
    out = {"n": n, "games": g, "gross": gross, "net": mean, "net_lo": lo, "net_hi": hi, "p_value": None, "testable": g >= MIN_EVENTS}
    if g >= MIN_EVENTS:
        s2 = sum((sum(v) - len(v) * mean) ** 2 for v in games.values())
        se = math.sqrt(s2) / n
        if se > 0:
            z = mean / se
            out["z"] = z
            out["p_value"] = 2 * (1 - _N.cdf(abs(z)))
    return out


def load_settlements(settle_dir: str) -> dict:
    import glob
    import os
    res = {}
    for f in glob.glob(os.path.join(settle_dir, "*.json")):
        for t, v in json.load(open(f)).items():
            if v.get("result") in ("yes", "no"):
                res[t] = 1.0 if v["result"] == "yes" else 0.0
    return res
