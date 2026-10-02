"""Fit + freeze models/mlb_game_pregame_v1.json (EXP-037 / T-608, MLB). Offline only.

Split (fixed before fitting, no tuning on the held-out season; regular season 'R' games only):
  train        seasons 2015-2023   ridge means for margin and total (lambda=100, fixed a priori)
  calibration  season  2024        probit-Platt (a, b) on the margin; sigma/rho from 2024 residuals
  held-out     season  2025        reported only; never used for any choice
Features use as_of = 00:00 UTC on the game's date (strictly earlier games only, same season).
Probable starters in the historical schedule are the pitchers who actually started (a stated weakness).
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

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from prediction_market_bot.c1_signal_ingestion.mlb_game_pregame_features import (  # noqa: E402
    FEATURE_NAMES, MLBGameFeatureBuilder)
from prediction_market_bot.pregame_shadow.mlb_model import MLBPregameModel, _phi, canonical_sha  # noqa: E402

LAMBDA = 100.0
TRAIN = range(2015, 2024)
CAL, HELD = 2024, 2025


def build_frame(games: pd.DataFrame) -> pd.DataFrame:
    fb = MLBGameFeatureBuilder(games)
    reg = games[(games.game_type == "R") & (games.status == "Final") & games.home_score.notna()]
    rows = []
    for r in reg.itertuples():
        as_of = datetime.fromisoformat(r.game_date).replace(tzinfo=timezone.utc)
        out = fb.row(r.home, r.away, as_of,
                     None if pd.isna(r.home_sp) else int(r.home_sp),
                     None if pd.isna(r.away_sp) else int(r.away_sp))
        if out is None:
            continue
        rows.append({"game_pk": r.game_pk, "season": r.season, "margin": r.home_score - r.away_score,
                     "total": r.home_score + r.away_score, **out["features"]})
    return pd.DataFrame(rows)


def ridge(X, y):
    mu, sd = X.mean(0), X.std(0)
    sd[sd == 0] = 1.0
    Z = (X - mu) / sd
    w = np.linalg.solve(Z.T @ Z + LAMBDA * np.eye(Z.shape[1]), Z.T @ (y - y.mean()))
    return float(y.mean()), w, mu, sd


def brier(p, y):
    return float(np.mean((np.asarray(p) - np.asarray(y)) ** 2))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--games", required=True)
    ap.add_argument("--out", default=str(ROOT / "models" / "mlb_game_pregame_v1.json"))
    args = ap.parse_args()
    df = build_frame(pd.read_parquet(args.games))
    tr, ca, ho = df[df.season.isin(TRAIN)], df[df.season == CAL], df[df.season == HELD]
    X = tr[FEATURE_NAMES].to_numpy(float)
    art: dict = {"model_id": "mlb_game_pregame_v1", "feature_names": FEATURE_NAMES, "lambda": LAMBDA,
                 "train_seasons": [min(TRAIN), max(TRAIN)], "cal_season": CAL, "held_out_season": HELD,
                 "game_type": "R"}
    for key in ("margin", "total"):
        b0, w, mu, sd = ridge(X, tr[key].to_numpy(float))
        art[key] = {"intercept": b0, "coef": w.tolist(), "mean": mu.tolist(), "std": sd.tolist()}
    art["platt"] = {"a": 1.0, "b": 0.0}
    art["sigma_margin"], art["sigma_total"], art["rho"] = 4.4, 4.4, 0.0
    art["sha256"] = canonical_sha(art)
    m0 = MLBPregameModel(art)

    def raw(frame, key):
        return np.array([m0._lin(key, r) for r in frame[FEATURE_NAMES].to_dict("records")])

    res_m = ca["margin"].to_numpy(float) - raw(ca, "margin")
    res_t = ca["total"].to_numpy(float) - raw(ca, "total")
    sm, st = float(res_m.std(ddof=1)), float(res_t.std(ddof=1))
    rho = float(np.corrcoef(res_m, res_t)[0, 1])
    z = raw(ca, "margin") / sm
    y = (ca.margin > 0).astype(float).to_numpy()   # no ties in MLB
    from sklearn.linear_model import LogisticRegression
    lr = LogisticRegression(C=1e6).fit(z.reshape(-1, 1), y)
    a, b = float(lr.coef_[0, 0]) / 1.702, float(lr.intercept_[0]) / 1.702
    for _ in range(25):
        eta = a * z + b
        p = np.clip([_phi(e) for e in eta], 1e-6, 1 - 1e-6)
        pdf = np.exp(-0.5 * eta**2) / math.sqrt(2 * math.pi)
        wgt = pdf**2 / (p * (1 - p))
        gr = (y - p) * pdf / (p * (1 - p))
        Xd = np.column_stack([z, np.ones_like(z)])
        H = Xd.T @ (Xd * wgt[:, None]) + 1e-9 * np.eye(2)
        step = np.linalg.solve(H, Xd.T @ gr)
        a, b = a + step[0], b + step[1]
    art["platt"] = {"a": float(a), "b": float(b)}
    art["sigma_margin"], art["sigma_total"], art["rho"] = sm, st, rho
    art["climatology"] = {
        "home_win_rate": float((tr.margin > 0).mean()),
        "mean_margin": float(tr.margin.mean()), "mean_total": float(tr.total.mean()),
        "sd_margin": float(tr.margin.std()), "sd_total": float(tr.total.std()),
    }
    art["sha256"] = canonical_sha(art)
    model = MLBPregameModel(art)

    recs = ho[FEATURE_NAMES].to_dict("records")
    ph = np.array([model.p_moneyline_home(model.distribution(r)) for r in recs])
    yh = (ho.margin > 0).astype(float).to_numpy()
    clim = art["climatology"]["home_win_rate"]
    rep = {"n_games": len(ho), "brier_model": brier(ph, yh), "brier_climatology": brier([clim] * len(ho), yh),
           "n_train": len(tr), "n_cal": len(ca)}
    q = pd.qcut(ph, 5, duplicates="drop")
    rep["reliability_5bin"] = [
        {"bin": str(k), "n": int(len(ix)), "mean_p": float(ph[ix].mean()), "obs": float(yh[ix].mean())}
        for k, ix in pd.Series(np.arange(len(ho))).groupby(q, observed=True)
        for ix in [ix.to_numpy()]]
    dm = np.array([model.distribution(r)["mu_margin"] for r in recs])
    dt = np.array([model.distribution(r)["mu_total"] for r in recs])
    rep["rmse_margin"] = float(np.sqrt(np.mean((ho.margin.to_numpy() - dm) ** 2)))
    rep["rmse_total"] = float(np.sqrt(np.mean((ho.total.to_numpy() - dt) ** 2)))
    rep["rmse_margin_climatology"] = float(np.sqrt(np.mean((ho.margin.to_numpy() - tr.margin.mean()) ** 2)))
    rep["rmse_total_climatology"] = float(np.sqrt(np.mean((ho.total.to_numpy() - tr.total.mean()) ** 2)))
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(art, indent=1, sort_keys=True))
    out.with_name("mlb_game_pregame_v1_heldout_2025.json").write_text(json.dumps(rep, indent=1))
    print(json.dumps(rep, indent=1))
    print("sha256", art["sha256"], "platt", art["platt"], "sigma", sm, st, "rho", rho)


if __name__ == "__main__":
    main()
