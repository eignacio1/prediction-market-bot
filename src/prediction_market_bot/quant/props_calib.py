"""W106.3 -- retail-flow calibration helpers: held-out net-of-cost cells for prop and game-line families.

Measures the MARKET only. No order, sizing or model is touched.

* net_pnl_side(side, y, bid, ask)  -- per-contract P&L after the k007 taker fee, entered at the quote (YES at the
  ask, NO at 1 - bid). Applies to taker entries held to settlement; maker fills and exits differ.
* time_split(rows, frac)           -- earlier `frac` of rows by start time -> (fit, holdout), never splitting a game.
  Applies when rows carry a game id and a time; a game straddling the cut goes wholly to the fit side.
* pick_side(fit_rows)              -- the side (yes/no) with the higher FIT-period mean net. Chosen on fit only so the
  holdout number is not selected on.
* holdout_cell(fit, hold)          -- fit-chosen side's net per contract on holdout with a game-clustered 95%
  interval and a one-sided cluster z p-value for net > 0. Applies when the holdout has >= MIN_GAMES games;
  otherwise p is None (DESCRIPTIVE).
"""
from __future__ import annotations

import math
import random
from collections import defaultdict
from statistics import NormalDist

from .inference import cluster_bootstrap
from .money import fee_k007

_N = NormalDist()
MIN_GAMES = 30


def net_pnl_side(side: str, y: float, bid: float, ask: float) -> float:
    if side == "yes":
        return y - ask - fee_k007(ask)
    q = 1.0 - bid
    return (1.0 - y) - q - fee_k007(q)


def time_split(rows: list[dict], frac: float = 0.7) -> tuple[list[dict], list[dict]]:
    """rows: dicts with 'game' and 'ts'. Games are ordered by their earliest ts; the first `frac` of GAMES go to fit."""
    first: dict = {}
    for r in rows:
        g = r["game"]
        if g not in first or r["ts"] < first[g]:
            first[g] = r["ts"]
    order = sorted(first, key=lambda g: (first[g], str(g)))
    cut = int(len(order) * frac)
    fit_games = set(order[:cut])
    return [r for r in rows if r["game"] in fit_games], [r for r in rows if r["game"] not in fit_games]


def _mean(rows, side):
    return sum(net_pnl_side(side, r["y"], r["bid"], r["ask"]) for r in rows) / len(rows) if rows else float("nan")


def pick_side(fit: list[dict]) -> str:
    return "yes" if _mean(fit, "yes") >= _mean(fit, "no") else "no"


def holdout_cell(fit: list[dict], hold: list[dict], boot: int = 1000, seed: int = 20261110) -> dict:
    side = pick_side(fit) if fit else "yes"
    out = {"side": side, "n_fit": len(fit), "n_hold": len(hold), "fit_net": _mean(fit, side) if fit else None}
    games = defaultdict(list)
    for r in hold:
        games[r["game"]].append(net_pnl_side(side, r["y"], r["bid"], r["ask"]))
    out["games_hold"] = len(games)
    if not games:
        out.update(net=None, lo=None, hi=None, p_pos=None)
        return out
    mean, lo, hi = cluster_bootstrap(games, b=boot, seed=seed)
    out.update(net=mean, lo=lo, hi=hi, p_pos=None)
    n = len(hold)
    if len(games) >= MIN_GAMES:
        s2 = sum((sum(v) - len(v) * mean) ** 2 for v in games.values())
        se = math.sqrt(s2) / n
        if se > 0:
            out["p_pos"] = 1.0 - _N.cdf(mean / se)  # one-sided: net > 0
    return out


def simulate_market(n_games: int, per_game: int, bias: float, spread: float = 0.02, seed: int = 1) -> list[dict]:
    """Synthetic market with KNOWN answer: true P(yes) = clamp(mid + bias). Prices uniform on [0.05, 0.95]; the quote
    is mid +/- spread. A bias of 0 has no edge before costs, so net must be negative; a large positive bias on YES
    has net ~ bias - spread - fee."""
    rng = random.Random(seed)
    rows = []
    for g in range(n_games):
        for _ in range(per_game):
            mid = rng.uniform(0.05, 0.95)
            pt = min(0.99, max(0.01, mid + bias))
            rows.append({"game": f"g{g}", "ts": float(g), "y": 1.0 if rng.random() < pt else 0.0,
                         "bid": mid - spread, "ask": mid + spread})
    return rows
