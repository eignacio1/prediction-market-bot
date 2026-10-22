"""W84.3 runner. Part A: build the three factor classes point-in-time and write the granularity-index tables.
Part B: does the best factor add to the Kalshi KXNHLGAME pre-game price beyond the frozen nhl_pregame_v1 p?

Exploratory: reads the event store and the Kalshi history store; writes only under 12_EXPLORATORY/nhl_engine/results.
Rule fixed BEFORE the 2025 look (stated in results_W84.md): ``adds`` = the factor coefficient's 95% CI (stacked on
logit(market)) excludes 0 AND the cross-validated blend beats the market on Brier with the 95% CI of the paired
difference below 0; ``does not add`` = the coefficient CI includes 0 and its upper end is under 0.5 (half a unit of
weight on the factor); otherwise ``too few to tell``.
"""
from __future__ import annotations

import json
import sys
from datetime import timedelta
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parent))
from _fence import safe_out  # noqa: E402
import factors as F  # noqa: E402

ROOT = F.ROOT
OUT = HERE / "results"
SEASONS = [2021, 2022, 2023, 2024, 2025]
XG_FIRST = 2022                 # xG for season t is fit on seasons < t; 2021 is the burn-in
FACTOR_TRAIN = [2022, 2023, 2024]
HOLDOUT = 2025
KALSHI = ROOT / "exp_output" / "KALSHI_HISTORY_NHL"


def logit(p):
    p = np.clip(np.asarray(p, float), 1e-4, 1 - 1e-4)
    return np.log(p / (1 - p))


def fit_lr(X, y, l2=1e-6, iters=100):
    X = np.column_stack([np.ones(len(X)), X]); b = np.zeros(X.shape[1])
    for _ in range(iters):
        p = 1 / (1 + np.exp(-X @ b)); w = p * (1 - p) + 1e-9
        H = X.T @ (X * w[:, None]) + l2 * np.eye(len(b)); step = np.linalg.solve(H, X.T @ (y - p) - l2 * b)
        b += step
        if np.abs(step).max() < 1e-9:
            break
    return b


def predict(b, X):
    return 1 / (1 + np.exp(-(np.column_stack([np.ones(len(X)), X]) @ b)))


def build_frame():
    g, ev, bx = F.load(SEASONS)
    g = g[g["has_pbp"] & g["has_box"] & g["game_type"].isin([2, 3])].copy()
    g["game_id"] = g["game_id"].astype("int64")
    sx = F.xg_by_season(F.shots(ev), XG_FIRST)
    tg = F.rolling(F.team_games(g[g["season"] >= XG_FIRST], sx, ev))
    gw = F.goalie_workload(g[g["season"] >= XG_FIRST], bx, sx)
    n_pit = F.assert_pit(g, tg)
    h = tg[tg.is_home].set_index("game_id"); a = tg[~tg.is_home].set_index("game_id")
    cols = ["xg_share5", "xgd5_60", "pp_xg60", "pk_xga60", "st_net60", "n_prior"]
    fr = pd.DataFrame({f"h_{c}": h[c] for c in cols}).join(pd.DataFrame({f"a_{c}": a[c] for c in cols}), how="inner")
    gh = gw.merge(g[["game_id", "home_team_id", "away_team_id"]], on="game_id")
    gh_h = gh[gh.team_id == gh.home_team_id].set_index("game_id"); gh_a = gh[gh.team_id == gh.away_team_id].set_index("game_id")
    for c in ("days_since_prev", "prev_goalie_starts7", "prev_goalie_gsax10", "prev_goalie_b2b"):
        fr[f"h_{c}"] = gh_h[c]; fr[f"a_{c}"] = gh_a[c]
    meta = g.set_index("game_id")[["season", "game_type", "start_time_utc", "home", "away", "game_date_et"]
                                 + [c for c in ("home_score", "away_score") if c in g.columns]]
    fr = fr.join(meta, how="inner")
    return g, fr.reset_index(), n_pit


def main():
    OUT.mkdir(exist_ok=True)
    g, fr, n_pit = build_frame()
    print("frame", fr.shape, "pit-checked", n_pit)
    fr.to_parquet(safe_out(OUT / "factor_frame.parquet"))
    json.dump({"rows": len(fr), "pit_games_checked": n_pit}, open(safe_out(OUT / "part_a_meta.json"), "w"))


if __name__ == "__main__":
    main()
