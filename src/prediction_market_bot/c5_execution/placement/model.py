"""W115.2 / B-095 (EXECUTION): what a resting order is worth, measured from demo orders with a known fill outcome.

PURE: no I/O, no order path. Input is a list of order records (dicts), one per order PLACED:

  arm, sport      what placed it
  placement       how it was placed: "rest_touch" (own side's best bid, cancelled after 60 s - the ADR-0072 rule and every
                  arm order so far) or "rest_inside" (a limit inside the spread: one tick inside, or the mid when the spread is 2
                  ticks or more; W119.3 - cancelled at 60 s like every arm order). "cross" is never observed: it is valued from
                  the unselected population.
  cancel_rule     GG-1943: "cancel_60s" (every arm order; the default when absent) or anything else (the ADR-0072 control posts
                  the row's mid and is never cancelled). Only cancel_60s records are evidence for rest_touch or rest_inside;
                  a never-cancelled fill is never pooled into the arm estimate.
  price           what the order bid for one contract of its own side, in (0, 1)
  filled          True / False
  won             True / False once the market resolved, None before. For an unfilled order it is the counterfactual:
                  would the side it wanted have won
  spread          the yes ask minus the yes bid at submit, in dollars (None when it was not logged)
  depth           contracts resting at the order's own touch at submit (None when not logged)
  hours           hours to the scheduled start at submit (None when not logged)
  series          the market's series ticker, for the exact fee

Three questions, each answered per cell with its n and a 95% interval:

  fill_table        P(fill | cell). Wilson interval.
  selection_table   E(won - price | filled) minus E(won - price | not filled): the adverse-selection term. Negative means the
                    orders that fill are the ones that go on to lose (the market picked us off); positive means fills are the
                    better orders. "won - price" is the per-contract result before fees, so the term is price-adjusted: an arm
                    that fills more often on cheap contracts is not mistaken for one that is being selected against.
  option_table      expected net per order placed, after exact fees and after selection, for each placement option:
                      rest_touch    P(fill) x E(won - price - maker fee | filled)          measured
                      rest_inside   the same, on the rest_inside orders                      measured where that arm exists
                      cross         E(won - (price + spread) - taker fee), over ALL orders   computed: pays the spread and the
                                    taker fee, fills always, so no selection
                      no_place      0

WHEN IT APPLIES. The records must be orders the rule placed without knowing the outcome, and a cell needs resolved orders on
both sides (filled and unfilled) before the selection term means anything; ``MIN_N`` marks the cells that do not have them.
"cross" assumes the order would have filled at the far touch for its size - true for the $1 demo stake where the touch holds
$1 in 95.7-98.4% of samples (12_EXPLORATORY/fill_markout, W94.3C), not true for size. WHAT THE DATA CANNOT SUPPORT: queue
position (logged nowhere), depth beyond the top level, and any offset the two rules never posted.
"""
from __future__ import annotations

import math
from typing import Any, Callable, Dict, Iterable, List, Optional, Sequence, Tuple

from prediction_market_bot.quant import money

OPTIONS = ("rest_touch", "rest_inside", "cross", "no_place")
MIN_N = 30            # resolved orders per side of a comparison before a cell is called supported
Z95 = 1.959964
DEFAULT_SPREAD = 0.02  # used for "cross" only when a record has no logged spread; W94.3C: about 2c (6c NHL)
SPREAD_BY_SPORT = {"nhl": 0.06}


def wilson(k: float, n: float, z: float = Z95) -> Tuple[Optional[float], Optional[float]]:
    """Wilson score interval for a proportion. (None, None) when n is 0."""
    if n <= 0:
        return None, None
    p = k / n
    d = 1.0 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return max(0.0, c - h), min(1.0, c + h)


def mean_ci(v: Sequence[float], z: float = Z95) -> dict:
    """Mean with a normal 95% interval (sample variance). n < 2 has no interval."""
    n = len(v)
    if n == 0:
        return {"n": 0, "mean": None, "lo": None, "hi": None, "var": None}
    m = sum(v) / n
    if n < 2:
        return {"n": n, "mean": m, "lo": None, "hi": None, "var": None}
    var = sum((x - m) ** 2 for x in v) / (n - 1)
    h = z * math.sqrt(var / n)
    return {"n": n, "mean": m, "lo": m - h, "hi": m + h, "var": var}


def diff_ci(a: Sequence[float], b: Sequence[float], z: float = Z95) -> dict:
    """mean(a) - mean(b) with a Welch normal interval."""
    ma, mb = mean_ci(a), mean_ci(b)
    if ma["mean"] is None or mb["mean"] is None:
        return {"diff": None, "lo": None, "hi": None}
    d = ma["mean"] - mb["mean"]
    if ma["var"] is None or mb["var"] is None:
        return {"diff": d, "lo": None, "hi": None}
    h = z * math.sqrt(ma["var"] / ma["n"] + mb["var"] / mb["n"])
    return {"diff": d, "lo": d - h, "hi": d + h}


# ---- cells -----------------------------------------------------------------------------------------------------------

def spread_bucket(s: Optional[float]) -> str:
    if s is None:
        return "spread?"
    c = round(float(s) * 100)
    return "1c" if c <= 1 else "2c" if c == 2 else "3-5c" if c <= 5 else "6c+"


def depth_bucket(d: Optional[float]) -> str:
    if d is None:
        return "depth?"
    return "<100" if d < 100 else "100-999" if d < 1000 else "1000+"


def hours_bucket(h: Optional[float]) -> str:
    if h is None:
        return "hours?"
    return "<1h" if h < 1 else "1-6h" if h < 6 else "6-24h" if h < 24 else "24h+"


def price_bucket(p: Optional[float]) -> str:
    """Which side of the market the order backs: the favourite (price >= 0.5) or the underdog."""
    if p is None:
        return "price?"
    return "favourite" if float(p) >= 0.5 else "underdog"


KEYS: Dict[str, Callable[[dict], str]] = {
    "arm": lambda r: str(r.get("arm")),
    "sport": lambda r: str(r.get("sport") or "?").lower(),
    "placement": lambda r: str(r.get("placement") or "rest_touch"),
    "spread": lambda r: spread_bucket(r.get("spread")),
    "depth": lambda r: depth_bucket(r.get("depth")),
    "hours": lambda r: hours_bucket(r.get("hours")),
    "backs": lambda r: price_bucket(r.get("price")),
    "leaf": lambda r: str(r.get("leaf_id")),
}


def cell_of(r: dict, by: Sequence[str]) -> str:
    return "|".join(KEYS[k](r) for k in by)


def _group(records: Iterable[dict], by: Sequence[str]) -> Dict[str, List[dict]]:
    out: Dict[str, List[dict]] = {}
    for r in records:
        out.setdefault(cell_of(r, by), []).append(r)
    return out


def _r(x: Optional[float], nd: int = 4) -> Optional[float]:
    return None if x is None else round(x, nd)


# ---- the three tables ------------------------------------------------------------------------------------------------

def fill_table(records: Iterable[dict], by: Sequence[str] = ("arm",)) -> Dict[str, dict]:
    """P(fill | cell): n placed, fills, rate, Wilson 95%."""
    out = {}
    for cell, rs in sorted(_group(records, by).items()):
        n, k = len(rs), sum(1 for r in rs if r.get("filled"))
        lo, hi = wilson(k, n)
        out[cell] = {"n": n, "fills": k, "p_fill": _r(k / n), "lo": _r(lo), "hi": _r(hi)}
    return out


def edge(r: dict) -> Optional[float]:
    """won - price: the result of one contract before fees. None until the market resolves."""
    if r.get("won") is None or r.get("price") is None:
        return None
    return (1.0 if r["won"] else 0.0) - float(r["price"])


def selection_table(records: Iterable[dict], by: Sequence[str] = ("arm",), min_n: int = MIN_N) -> Dict[str, dict]:
    """E(won - price | filled) vs E(won - price | not filled) per cell, and the raw win rates (E3)."""
    out = {}
    for cell, rs in sorted(_group(records, by).items()):
        f = [edge(r) for r in rs if r.get("filled") and edge(r) is not None]
        u = [edge(r) for r in rs if not r.get("filled") and edge(r) is not None]
        wf = [1.0 if r["won"] else 0.0 for r in rs if r.get("filled") and r.get("won") is not None]
        wu = [1.0 if r["won"] else 0.0 for r in rs if not r.get("filled") and r.get("won") is not None]
        mf, mu, d = mean_ci(f), mean_ci(u), diff_ci(f, u)
        out[cell] = {"n_filled": len(f), "n_unfilled": len(u),
                     "win_filled": _r(sum(wf) / len(wf)) if wf else None,
                     "win_unfilled": _r(sum(wu) / len(wu)) if wu else None,
                     "edge_filled": _r(mf["mean"]), "edge_filled_ci": [_r(mf["lo"]), _r(mf["hi"])],
                     "edge_unfilled": _r(mu["mean"]), "edge_unfilled_ci": [_r(mu["lo"]), _r(mu["hi"])],
                     "selection": _r(d["diff"]), "selection_ci": [_r(d["lo"]), _r(d["hi"])],
                     "supported": len(f) >= min_n and len(u) >= min_n}
    return out


def _fee(r: dict, price: float, side: str) -> float:
    """Exact per-contract fee at ``price`` (quant/money fee table); 0 when the series is unknown to the table."""
    try:
        return float(money.fee_rate(str(r.get("series") or ""), min(max(price, 0.01), 0.99), side))
    except Exception:  # noqa: BLE001 - an unknown series must not break a read; it is reported as fee 0
        return 0.0


def _spread(r: dict) -> float:
    if r.get("spread") is not None:
        return max(0.0, float(r["spread"]))
    return SPREAD_BY_SPORT.get(str(r.get("sport") or "").lower(), DEFAULT_SPREAD)


def same_cancel_rule(r: dict) -> bool:
    """GG-1943: True for a record placed under the arm path's 60 s cancel (the default for a record that does not say)."""
    return (r.get("cancel_rule") or "cancel_60s") == "cancel_60s"


def option_table(records: Iterable[dict], by: Sequence[str] = ("arm",), min_n: int = MIN_N,
                 strict_spread: bool = True) -> Dict[str, dict]:
    """Expected net per order placed (dollars per contract, after exact fees and selection) for each placement option,
    and the best supported one. ``placement`` must not be in ``by``: the options are compared inside a cell."""
    assert "placement" not in by, "options are compared inside a cell"
    out = {}
    for cell, rs in sorted(_group(records, by).items()):
        row: dict = {"no_place": {"net": 0.0, "n": len(rs)}}
        for opt in ("rest_touch", "rest_inside"):
            ors = [r for r in rs if (r.get("placement") or "rest_touch") == opt and same_cancel_rule(r)]
            # an unresolved filled order has no value yet, so the per-order value is taken on resolved orders only
            v = [(edge(r) - _fee(r, float(r["price"]), "maker")) if r.get("filled") else 0.0
                 for r in ors if edge(r) is not None]
            m = mean_ci(v)
            nf = sum(1 for r in ors if r.get("filled") and edge(r) is not None)
            row[opt] = {"net": _r(m["mean"]), "ci": [_r(m["lo"]), _r(m["hi"])], "n": m["n"], "n_filled": nf,
                        "supported": m["n"] >= min_n and nf >= min_n}
        # crossing: every order in the cell, filled or not, bought at the far touch - the unselected population
        touch = [r for r in rs if (r.get("placement") or "rest_touch") == "rest_touch" and same_cancel_rule(r) and edge(r) is not None]
        if strict_spread:  # W117.1: a crossing cost is valued only where a spread was logged or backfilled, never assumed
            touch = [r for r in touch if r.get("spread") is not None]
        v = []
        for r in touch:
            px = min(0.99, float(r["price"]) + _spread(r))
            v.append((1.0 if r["won"] else 0.0) - px - _fee(r, px, "taker"))
        m = mean_ci(v)
        row["cross"] = {"net": _r(m["mean"]), "ci": [_r(m["lo"]), _r(m["hi"])], "n": m["n"], "supported": m["n"] >= min_n,
                        "spread_logged": sum(1 for r in touch if r.get("spread") is not None)}
        cands = [(row[o]["net"], o) for o in ("rest_touch", "rest_inside", "cross")
                 if row[o].get("supported") and row[o]["net"] is not None]
        best = max(cands + [(0.0, "no_place")])
        row["best"] = best[1] if cands else None           # None: nothing in this cell is supported yet
        row["best_net"] = best[0] if cands else None
        out[cell] = row
    return out


def summary(records: List[dict], by: Sequence[str] = ("arm",), min_n: int = MIN_N) -> dict:
    return {"by": list(by), "min_n": min_n, "fill": fill_table(records, by),
            "selection": selection_table(records, by, min_n),
            "options": option_table(records, [k for k in by if k != "placement"], min_n)}


# ---- game-clustered intervals (W117.1 Part B) --------------------------------------------------------------------------

def game_of(r: dict) -> str:
    """The game an order belongs to: sport + the date-and-teams part of the ticker (KXNBAGAME-26NOV17ABCDEF-ABC -> 26NOV17ABCDEF), so
    the game, spread and total markets of one game share a key. Orders on one game are not independent; this is the cluster."""
    parts = str(r.get("ticker") or "").split("-")
    return str(r.get("sport") or "?").lower() + "|" + (parts[1] if len(parts) > 1 else str(r.get("ticker") or r.get("order_id")))


def t_crit(df: float, z: float = Z95) -> float:
    """Two-sided 95% Student-t critical value by the Cornish-Fisher expansion (df >= 2); the normal value for large df."""
    if df < 2:
        return float("inf")
    return z + (z ** 3 + z) / (4 * df) + (5 * z ** 5 + 16 * z ** 3 + 3 * z) / (96 * df ** 2)


def cluster_mean_ci(vals: Sequence[float], games: Sequence[str]) -> dict:
    """Mean of per-order values with a game-clustered 95% interval: the CR1 sandwich standard error with G games, the t critical
    value on G - 1 degrees of freedom. ``n`` is orders, ``n_games`` is games; fewer than 2 games has no interval."""
    n = len(vals)
    if n == 0:
        return {"n": 0, "n_games": 0, "mean": None, "lo": None, "hi": None}
    m = sum(vals) / n
    g: Dict[str, List[float]] = {}
    for v, k in zip(vals, games):
        g.setdefault(k, []).append(v)
    G = len(g)
    if G < 2:
        return {"n": n, "n_games": G, "mean": m, "lo": None, "hi": None}
    meat = sum((sum(x - m for x in v)) ** 2 for v in g.values())
    se = math.sqrt(G / (G - 1) * meat) / n
    h = t_crit(G - 1) * se
    return {"n": n, "n_games": G, "mean": m, "lo": m - h, "hi": m + h}


def _cl(r: Optional[dict]) -> dict:
    return {"n": r["n"], "n_games": r["n_games"], "net": _r(r["mean"]), "ci": [_r(r["lo"]), _r(r["hi"])]}


def option_net_clustered(records: Iterable[dict], by: Sequence[str] = ("arm",)) -> Dict[str, dict]:
    """Per cell, net per contract after exact fees for each option, with game-clustered intervals and n in orders AND games.

      rest_touch   per order placed, on the orders that have a real spread (the same orders the crossing is valued on)
      cross        won - (price + real spread) - taker fee, per order; ONLY orders with a logged or backfilled spread
      rest_touch_all   rest_touch on every resolved order in the cell, spread or not
    Reads: if ``cross`` has an interval wholly above zero it cleared zero after costs on these games; the comparison with
    rest_touch is on the same orders (``cross_minus_rest``)."""
    assert "placement" not in by
    out = {}
    for cell, rs in sorted(_group(records, by).items()):
        res = [r for r in rs if (r.get("placement") or "rest_touch") == "rest_touch" and same_cancel_rule(r) and edge(r) is not None]
        sp = [r for r in res if r.get("spread") is not None]

        def touch_v(r: dict) -> float:
            return (edge(r) - _fee(r, float(r["price"]), "maker")) if r.get("filled") else 0.0

        def cross_v(r: dict) -> float:
            px = min(0.99, float(r["price"]) + max(0.0, float(r["spread"])))
            return (1.0 if r["won"] else 0.0) - px - _fee(r, px, "taker")
        row = {"rest_touch_all": _cl(cluster_mean_ci([touch_v(r) for r in res], [game_of(r) for r in res])),
               "rest_touch": _cl(cluster_mean_ci([touch_v(r) for r in sp], [game_of(r) for r in sp])),
               "cross": _cl(cluster_mean_ci([cross_v(r) for r in sp], [game_of(r) for r in sp])),
               "cross_minus_rest": _cl(cluster_mean_ci([cross_v(r) - touch_v(r) for r in sp], [game_of(r) for r in sp])),
               "n_spread_logged": sum(1 for r in sp if r.get("spread_src") == "logged"),
               "n_spread_archive": sum(1 for r in sp if r.get("spread_src") == "archive"),
               "n_no_spread": len(res) - len(sp), "no_place": {"net": 0.0}}
        out[cell] = row
    return out
