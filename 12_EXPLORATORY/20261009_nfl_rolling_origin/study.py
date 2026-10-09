"""EXPLORATORY -- NFL rolling-origin challenger comparison (W61.3 Part C). Not a verdict.

Seasons 2019-2023 only as test seasons; 2024/2025/2026 are never read as outcomes here.
Per test season T: ridge fit on 2015..T-2, probit-Platt fit on T-1, score on T.
Candidates are FIXED before running: base(lam=100, frozen recipe), lam30, lam300, base+dome flag.
Metric: pooled Brier on home win; delta vs base with game bootstrap (B=2000, seed 20261009).
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE.parent.parent / "src"))
from _fence import safe_out  # noqa: E402
from prediction_market_bot.c1_signal_ingestion.nfl_pregame_features import (  # noqa: E402
    FEATURE_NAMES, NFLPregameFeatureBuilder,
)

B, SEED = 2000, 20261009
TESTS = [2019, 2020, 2021, 2022, 2023]
CANDS = {"base": (100.0, False), "lam30": (30.0, False), "lam300": (300.0, False), "dome": (100.0, True)}
DOME = {"dome", "closed"}


def phi(z):
    return 0.5 * (1.0 + np.vectorize(math.erf)(z / math.sqrt(2.0)))


def ridge(X, y, lam):
    mu, sd = X.mean(0), X.std(0)
    sd[sd == 0] = 1.0
    Z = (X - mu) / sd
    w = np.linalg.solve(Z.T @ Z + lam * np.eye(Z.shape[1]), Z.T @ (y - y.mean()))
    return y.mean(), w, mu, sd


def pred(m, X):
    b0, w, mu, sd = m
    return b0 + ((X - mu) / sd) @ w


def platt(z, y):
    a, b = 1.0, 0.0
    for _ in range(50):
        eta = a * z + b
        p = np.clip(phi(eta), 1e-6, 1 - 1e-6)
        pdf = np.exp(-0.5 * eta**2) / math.sqrt(2 * math.pi)
        w = pdf**2 / (p * (1 - p))
        g = (y - p) * pdf / (p * (1 - p))
        X = np.column_stack([z, np.ones_like(z)])
        s = np.linalg.solve(X.T @ (X * w[:, None]) + 1e-9 * np.eye(2), X.T @ g)
        a, b = a + s[0], b + s[1]
    return a, b


def boot(d):
    rng = np.random.default_rng(SEED)
    m = d[rng.integers(0, len(d), (B, len(d)))].mean(1)
    return dict(mean=float(d.mean()), lo95=float(np.percentile(m, 2.5)), hi95=float(np.percentile(m, 97.5)))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--schedule", required=True)
    ap.add_argument("--team-stats", required=True)
    a = ap.parse_args()
    sched, stats = pd.read_parquet(a.schedule), pd.read_parquet(a.team_stats)
    fb = NFLPregameFeatureBuilder(stats, sched)
    reg = sched[(sched.game_type == "REG") & sched.home_score.notna() & (sched.season <= 2023)]
    rows = []
    for r in reg.itertuples():
        as_of = datetime(*map(int, str(r.gameday).split("-")), tzinfo=timezone.utc)
        out = fb.row(r.home_team, r.away_team, as_of, r.home_rest, r.away_rest)
        if out is None:
            continue
        mg = r.home_score - r.away_score
        rows.append({"game_id": r.game_id, "season": r.season, "margin": mg,
                     "dome": 1.0 if str(r.roof).lower() in DOME else 0.0,
                     "y": 1.0 if mg > 0 else (0.5 if mg == 0 else 0.0), **out["features"]})
    df = pd.DataFrame(rows)
    preds = {k: [] for k in CANDS}
    ys, ids, seas = [], [], []
    for T in TESTS:
        tr, ca, te = df[df.season <= T - 2], df[df.season == T - 1], df[df.season == T]
        for k, (lam, dome) in CANDS.items():
            cols = FEATURE_NAMES + (["dome"] if dome else [])
            m = ridge(tr[cols].to_numpy(float), tr.margin.to_numpy(float), lam)
            rc = pred(m, ca[cols].to_numpy(float))
            sm = float(np.std(ca.margin.to_numpy(float) - rc, ddof=1))
            nt = ca.margin != 0
            aa, bb = platt(rc[nt.to_numpy()] / sm, ca.y[nt].to_numpy())
            z = pred(m, te[cols].to_numpy(float)) / sm
            p = phi(aa * z + bb)
            preds[k].append(p)
        ys.append(te.y.to_numpy())
        ids += list(te.game_id)
        seas += [T] * len(te)
    y = np.concatenate(ys)
    P = {k: np.concatenate(v) for k, v in preds.items()}
    seas = np.array(seas)
    res = {"n_games": int(len(y)), "tests": TESTS, "brier": {k: float(((p - y) ** 2).mean()) for k, p in P.items()},
           "delta_vs_base": {}, "per_season_delta": {}}
    for k in CANDS:
        if k == "base":
            continue
        d = (P[k] - y) ** 2 - (P["base"] - y) ** 2
        res["delta_vs_base"][k] = boot(d)
        res["per_season_delta"][k] = {str(T): float(d[seas == T].mean()) for T in TESTS}
    p = safe_out(HERE / "results.json")
    p.write_text(json.dumps(res, indent=1))
    print(json.dumps(res, indent=1))


if __name__ == "__main__":
    main()
