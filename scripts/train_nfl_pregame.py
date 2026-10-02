"""Fit + freeze models/nfl_pregame_v1.json (EXP-037 / T-608, D3). Offline only.

Split (fixed before fitting, no tuning on the held-out season):
  train        seasons 2015-2023   ridge means for margin and total (lambda=100, fixed a priori)
  calibration  season  2024        probit-Platt (a, b) on the margin; sigma/rho from 2024 residuals
  held-out     season  2025        reported only; never used for any choice

Features use as_of = 00:00 UTC on the game's gameday, so only games on earlier
dates inform a row (TI-01).
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

from prediction_market_bot.c1_signal_ingestion.nfl_pregame_features import (  # noqa: E402
    FEATURE_NAMES, NFLPregameFeatureBuilder,
)
from prediction_market_bot.pregame_shadow.nfl_model import (  # noqa: E402
    NFLPregameModel, canonical_sha, _phi,
)

LAMBDA = 100.0
TRAIN = range(2015, 2024)
CAL, HELD = 2024, 2025


def build_frame(sched: pd.DataFrame, stats: pd.DataFrame) -> pd.DataFrame:
    fb = NFLPregameFeatureBuilder(stats, sched)
    rows = []
    reg = sched[(sched.game_type == "REG") & sched.home_score.notna()]
    for r in reg.itertuples():
        as_of = datetime.fromisoformat(str(r.gameday)).replace(tzinfo=timezone.utc)
        out = fb.row(r.home_team, r.away_team, as_of, r.home_rest, r.away_rest)
        if out is None:
            continue
        rows.append({"game_id": r.game_id, "season": r.season, "week": r.week,
                     "margin": r.home_score - r.away_score,
                     "total": r.home_score + r.away_score, **out["features"]})
    return pd.DataFrame(rows)


def ridge(X: np.ndarray, y: np.ndarray) -> tuple[float, np.ndarray, np.ndarray, np.ndarray]:
    mu, sd = X.mean(0), X.std(0)
    sd[sd == 0] = 1.0
    Z = (X - mu) / sd
    w = np.linalg.solve(Z.T @ Z + LAMBDA * np.eye(Z.shape[1]), Z.T @ (y - y.mean()))
    return float(y.mean()), w, mu, sd


def brier(p, y):
    return float(np.mean((np.asarray(p) - np.asarray(y)) ** 2))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--schedule", required=True)
    ap.add_argument("--team-stats", required=True)
    ap.add_argument("--out", default=str(ROOT / "models" / "nfl_pregame_v1.json"))
    args = ap.parse_args()
    sched = pd.read_parquet(args.schedule)
    stats = pd.read_parquet(args.team_stats)
    df = build_frame(sched, stats)
    tr, ca, ho = (df[df.season.isin(TRAIN)], df[df.season == CAL], df[df.season == HELD])
    X = tr[FEATURE_NAMES].to_numpy(float)
    art: dict = {"model_id": "nfl_pregame_v1", "feature_names": FEATURE_NAMES, "lambda": LAMBDA,
                 "train_seasons": [min(TRAIN), max(TRAIN)], "cal_season": CAL, "held_out_season": HELD}
    for key in ("margin", "total"):
        b0, w, mu, sd = ridge(X, tr[key].to_numpy(float))
        art[key] = {"intercept": b0, "coef": w.tolist(), "mean": mu.tolist(), "std": sd.tolist()}
    art["platt"] = {"a": 1.0, "b": 0.0}
    art["sigma_margin"], art["sigma_total"], art["rho"] = 13.0, 13.0, 0.0
    art["sha256"] = canonical_sha(art)
    m0 = NFLPregameModel(art)

    def raw(frame, key):
        return np.array([m0._lin(key, r) for r in frame[FEATURE_NAMES].to_dict("records")])

    # sigma / rho from calibration-season residuals (never held-out)
    res_m = ca["margin"].to_numpy(float) - raw(ca, "margin")
    res_t = ca["total"].to_numpy(float) - raw(ca, "total")
    sm, st = float(res_m.std(ddof=1)), float(res_t.std(ddof=1))
    rho = float(np.corrcoef(res_m, res_t)[0, 1])
    # probit-Platt on 2024: P(home win) = Phi(a * mu/sm + b); ties excluded
    nt = ca[ca.margin != 0]
    z = raw(nt, "margin") / sm
    y = (nt.margin > 0).astype(float).to_numpy()
    from sklearn.linear_model import LogisticRegression
    # logistic on z as a stable surrogate to initialise, then a few Newton steps on the probit link
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
        "home_win_rate_ex_ties": float((tr[tr.margin != 0].margin > 0).mean()),
        "mean_margin": float(tr.margin.mean()), "mean_total": float(tr.total.mean()),
        "sd_margin": float(tr.margin.std()), "sd_total": float(tr.total.std()),
        "tie_rate": float((tr.margin == 0).mean()),
    }
    art["sha256"] = canonical_sha(art)
    model = NFLPregameModel(art)

    # held-out report
    ph = np.array([model.p_moneyline_home(model.distribution(r)) for r in ho[FEATURE_NAMES].to_dict("records")])
    yh = np.where(ho.margin > 0, 1.0, np.where(ho.margin == 0, 0.5, 0.0))
    clim = art["climatology"]["home_win_rate_ex_ties"]
    rep = {"n_games": len(ho), "brier_model": brier(ph, yh), "brier_climatology": brier([clim] * len(ho), yh),
           "n_train": len(tr), "n_cal": len(ca)}
    q = pd.qcut(ph, 5, duplicates="drop")
    rep["reliability_5bin"] = [
        {"bin": str(k), "n": int(len(g)), "mean_p": float(ph[g.index.map(lambda i: ho.index.get_loc(i))].mean()),
         "obs": float(yh[g.index.map(lambda i: ho.index.get_loc(i))].mean())}
        for k, g in pd.Series(range(len(ho)), index=ho.index).groupby(q, observed=True)
    ]
    # margin / total error on held-out
    dm = np.array([model.distribution(r)["mu_margin"] for r in ho[FEATURE_NAMES].to_dict("records")])
    dt = np.array([model.distribution(r)["mu_total"] for r in ho[FEATURE_NAMES].to_dict("records")])
    rep["rmse_margin"] = float(np.sqrt(np.mean((ho.margin.to_numpy() - dm) ** 2)))
    rep["rmse_total"] = float(np.sqrt(np.mean((ho.total.to_numpy() - dt) ** 2)))
    rep["rmse_margin_climatology"] = float(np.sqrt(np.mean((ho.margin.to_numpy() - tr.margin.mean()) ** 2)))
    rep["rmse_total_climatology"] = float(np.sqrt(np.mean((ho.total.to_numpy() - tr.total.mean()) ** 2)))
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(art, indent=1, sort_keys=True))
    out.with_name("nfl_pregame_v1_heldout_2025.json").write_text(json.dumps(rep, indent=1))
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        pts = rep["reliability_5bin"]
        plt.figure(figsize=(4, 4))
        plt.plot([0, 1], [0, 1], "k--", lw=0.8)
        plt.plot([p["mean_p"] for p in pts], [p["obs"] for p in pts], "o-")
        plt.xlabel("predicted P(home win)"); plt.ylabel("observed"); plt.title("NFL pregame v1, 2025 held-out")
        plt.tight_layout(); plt.savefig(out.with_name("nfl_pregame_v1_calibration_2025.png"), dpi=110)
    except Exception as exc:  # plot is a convenience; table is the record
        print("plot skipped:", exc)
    print(json.dumps(rep, indent=1))
    print("sha256", art["sha256"], "platt", art["platt"], "sigma", sm, st, "rho", rho)


if __name__ == "__main__":
    main()
