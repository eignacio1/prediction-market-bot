"""Per-cell scoring + game-cluster bootstrap (EXP-037 / D2c). Pure functions; reads only.

Scoring unit: the FIRST ledger row per (market_ticker, band) -- fixed in advance so that
repeated evaluations of one market cannot be cherry-picked. Inference clusters on game
(all strikes of one game share a cluster; they are not independent).
"""
from __future__ import annotations

import math
from typing import Iterable

from prediction_market_bot.pregame_shadow.fees import fee_k007, fee_kmult
from prediction_market_bot.quant import inference as _Q

BOOT_B = 2000
BOOT_SEED = 20261002


def first_row_per_market(rows: Iterable[dict]) -> list[dict]:
    seen: dict[tuple[str, str], dict] = {}
    for r in sorted(rows, key=lambda r: r["ts_utc"]):
        seen.setdefault((r["market_ticker"], r["band"]), r)
    return list(seen.values())


def brier(p: float, y: float) -> float:
    return (p - y) ** 2


def logloss(p: float, y: float) -> float:
    p = min(max(p, 1e-6), 1 - 1e-6)
    return -(y * math.log(p) + (1 - y) * math.log(1 - p))


def _best_side_e_net(r: dict, y: float, fee) -> float:
    """Realised $ per contract on the side the model prefers at entry (ask side), net of fee."""
    if r["p_yes"] - r["yes_ask"] >= (1 - r["p_yes"]) - (1 - r["yes_bid"]):
        q = r["yes_ask"]
        return y - q - fee(q)
    q = 1.0 - r["yes_bid"]
    return (1.0 - y) - q - fee(q)


def expected_e_net_entry(r: dict, fee) -> float:
    """MODEL-expected E_net at entry on the preferred side (what the cell would claim ex ante)."""
    ey = r["p_yes"] - r["yes_ask"] - fee(r["yes_ask"])
    q = 1.0 - r["yes_bid"]
    en = (1.0 - r["p_yes"]) - q - fee(q)
    return max(ey, en)


def cluster_bootstrap_ci(vals_by_cluster: dict[str, list[float]], b: int = BOOT_B,
                         seed: int = BOOT_SEED) -> tuple[float, float, float]:
    """Mean of per-row values with game-cluster resampling -> (mean, lo95, hi95)."""
    return _Q.cluster_bootstrap(vals_by_cluster, b=b, seed=seed)  # W87.1: one definition, in the quant core


def score_cell(rows: list[dict], b: int = BOOT_B, seed: int = BOOT_SEED, per_game_mean: bool = False) -> dict:
    """rows: ledger rows already joined with y (0/0.5/1), p_clim, game_key.

    SIGN CONVENTION (fixed by the EXP-037 brief, pre-registered): delta_brier_vs_X =
    Brier(X) - Brier(model). POSITIVE means the model is better than X.
    """
    rows = [r for r in rows if r.get("y") is not None]
    if not rows:
        return {"n_rows": 0, "n_games": 0}
    by_game_vs_mkt: dict[str, list[float]] = {}
    by_game_vs_clim: dict[str, list[float]] = {}
    by_game_enet: dict[str, dict[str, list[float]]] = {}
    for r in rows:
        y, g = r["y"], r["game_key"]
        bm, bk, bc = brier(r["p_yes"], y), brier(r["mid"], y), brier(r["p_clim"], y)
        by_game_vs_mkt.setdefault(g, []).append(bk - bm)
        by_game_vs_clim.setdefault(g, []).append(bc - bm)
        for name, fee in (("k007", fee_k007), ("kmult", fee_kmult)):
            by_game_enet.setdefault(name, {}).setdefault(g, []).append(expected_e_net_entry(r, fee))
    n = len(rows)
    out = {
        "n_rows": n, "n_games": len(by_game_vs_mkt),
        "brier_model": sum(brier(r["p_yes"], r["y"]) for r in rows) / n,
        "brier_market": sum(brier(r["mid"], r["y"]) for r in rows) / n,
        "brier_climatology": sum(brier(r["p_clim"], r["y"]) for r in rows) / n,
        "logloss_model": sum(logloss(r["p_yes"], r["y"]) for r in rows) / n,
        "logloss_market": sum(logloss(r["mid"], r["y"]) for r in rows) / n,
    }
    if per_game_mean:       # EXP-036: the per-game score is the mean over that game's strikes
        _collapse = lambda d: {g: [sum(v) / len(v)] for g, v in d.items()}   # noqa: E731
        by_game_vs_mkt, by_game_vs_clim = _collapse(by_game_vs_mkt), _collapse(by_game_vs_clim)
        by_game_enet = {k: _collapse(v) for k, v in by_game_enet.items()}
    for key, d in (("delta_brier_vs_market", by_game_vs_mkt), ("delta_brier_vs_climatology", by_game_vs_clim)):
        m, lo, hi = cluster_bootstrap_ci(d, b, seed)
        out[key] = {"mean": m, "ci95": [lo, hi]}
    for name in ("k007", "kmult"):
        m, lo, hi = cluster_bootstrap_ci(by_game_enet[name], b, seed)
        out[f"e_net_entry_expected_{name}"] = {"mean": m, "ci95": [lo, hi]}
    out["bootstrap"] = {"B": b, "seed": seed, "unit": "game-mean" if per_game_mean else "game-cluster"}
    out["e_net_realised_best_side"] = {
        "k007": sum(_best_side_e_net(r, r["y"], fee_k007) for r in rows) / n,
        "kmult": sum(_best_side_e_net(r, r["y"], fee_kmult) for r in rows) / n,
    }
    return out
