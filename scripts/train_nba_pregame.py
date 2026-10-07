"""Fit + freeze models/nba_pregame_v1.json (EXP-038 D). Offline only (Hard Rule 4).

Split fixed in the EXP-038 pre-registration BEFORE fitting (seasons labelled by ending year):
  train        2016-2023   (2015-16 .. 2022-23)  ridge means for margin and total (lambda fixed a priori)
  calibration  2024        (2023-24)             probit-Platt (a, b) on the margin; sigma/rho from residuals
  held-out     2025        (2024-25)             reported only; never used for any choice
  extra        2026        (2025-26)             reported only (post-hoc extra check), never used for any choice
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from prediction_market_bot.c1_signal_ingestion import nba_ingest as N  # noqa: E402
from prediction_market_bot.c1_signal_ingestion.nba_pregame_features import (  # noqa: E402
    FEATURE_NAMES, NBAFeatureBuilder, _dt,
)
from prediction_market_bot.pregame_shadow.nba_model import NBAPregameModel  # noqa: E402
from prediction_market_bot.pregame_shadow.nfl_model import _phi, canonical_sha  # noqa: E402

LAMBDA = 100.0
TRAIN, CAL, HELD, EXTRA = range(2016, 2024), 2024, 2025, 2026


def build_frame(games: list[dict]) -> list[dict]:
    fb = NBAFeatureBuilder(games)
    rows = []
    for g in games:
        if not (g["completed"] and g["season_type"] == 2 and g["home_score"] is not None):
            continue
        start = _dt(g["start_time_utc"])
        out = fb.row(g["home"], g["away"], start, start)
        if out is None:
            continue
        rows.append({"season": g["season"], "margin": g["home_score"] - g["away_score"],
                     "total": g["home_score"] + g["away_score"], **out["features"]})
    return rows


def arr(rows, keys):
    return np.array([[r[k] for k in keys] for r in rows], float)


def ridge(X, y):
    mu, sd = X.mean(0), X.std(0)
    sd[sd == 0] = 1.0
    Z = (X - mu) / sd
    w = np.linalg.solve(Z.T @ Z + LAMBDA * np.eye(Z.shape[1]), Z.T @ (y - y.mean()))
    return float(y.mean()), w, mu, sd


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--raw", required=True)
    ap.add_argument("--out", default=str(ROOT / "models" / "nba_pregame_v1.json"))
    args = ap.parse_args()
    games = []
    for s in range(min(TRAIN) - 1, EXTRA + 1):
        games += list(N.load_season(s, Path(args.raw))["games"].values())
    rows = build_frame(games)
    tr = [r for r in rows if r["season"] in TRAIN]
    ca = [r for r in rows if r["season"] == CAL]
    ho = [r for r in rows if r["season"] == HELD]
    ex = [r for r in rows if r["season"] == EXTRA]
    X = arr(tr, FEATURE_NAMES)
    art: dict = {"model_id": "nba_pregame_v1", "feature_names": FEATURE_NAMES, "lambda": LAMBDA,
                 "train_seasons": [min(TRAIN), max(TRAIN)], "cal_season": CAL, "held_out_season": HELD}
    for key in ("margin", "total"):
        b0, w, mu, sd = ridge(X, np.array([r[key] for r in tr], float))
        art[key] = {"intercept": b0, "coef": w.tolist(), "mean": mu.tolist(), "std": sd.tolist()}
    art["platt"] = {"a": 1.0, "b": 0.0}
    art["sigma_margin"], art["sigma_total"], art["rho"] = 12.0, 18.0, 0.0
    art["sha256"] = canonical_sha(art)
    m0 = NBAPregameModel(art)

    def raw(frame, key):
        return np.array([m0._lin(key, r) for r in frame])

    res_m = np.array([r["margin"] for r in ca], float) - raw(ca, "margin")
    res_t = np.array([r["total"] for r in ca], float) - raw(ca, "total")
    sm, st = float(res_m.std(ddof=1)), float(res_t.std(ddof=1))
    rho = float(np.corrcoef(res_m, res_t)[0, 1])
    z = raw(ca, "margin") / sm
    y = np.array([1.0 if r["margin"] > 0 else 0.0 for r in ca])
    a, b = 1.0, 0.0
    for _ in range(50):                                   # Newton on the probit link
        eta = a * z + b
        p = np.clip([_phi(e) for e in eta], 1e-6, 1 - 1e-6)
        pdf = np.exp(-0.5 * eta ** 2) / math.sqrt(2 * math.pi)
        wgt = pdf ** 2 / (p * (1 - p))
        gr = (y - p) * pdf / (p * (1 - p))
        Xd = np.column_stack([z, np.ones_like(z)])
        step = np.linalg.solve(Xd.T @ (Xd * wgt[:, None]) + 1e-9 * np.eye(2), Xd.T @ gr)
        a, b = a + step[0], b + step[1]
    mt = np.array([r["margin"] for r in tr], float)
    tt = np.array([r["total"] for r in tr], float)
    art["platt"] = {"a": float(a), "b": float(b)}
    art["sigma_margin"], art["sigma_total"], art["rho"] = sm, st, rho
    art["climatology"] = {"home_win_rate": float((mt > 0).mean()), "mean_margin": float(mt.mean()),
                          "mean_total": float(tt.mean()), "sd_margin": float(mt.std(ddof=1)),
                          "sd_total": float(tt.std(ddof=1))}
    art["sha256"] = canonical_sha(art)
    model = NBAPregameModel(art)

    def report(frame):
        if not frame:
            return None
        ph = np.array([model.p_home_win(model.distribution(r)) for r in frame])
        yh = np.array([1.0 if r["margin"] > 0 else 0.0 for r in frame])
        clim = art["climatology"]["home_win_rate"]
        d = [model.distribution(r) for r in frame]
        mg = np.array([r["margin"] for r in frame], float)
        tot = np.array([r["total"] for r in frame], float)
        order = np.argsort(ph)
        bins = [{"n": int(len(i)), "mean_p": float(ph[i].mean()), "obs": float(yh[i].mean())}
                for i in np.array_split(order, 5)]
        return {"n_games": len(frame), "brier_model": float(np.mean((ph - yh) ** 2)),
                "brier_climatology": float(np.mean((clim - yh) ** 2)),
                "rmse_margin": float(np.sqrt(np.mean((mg - [x["mu_margin"] for x in d]) ** 2))),
                "rmse_margin_climatology": float(np.sqrt(np.mean((mg - mt.mean()) ** 2))),
                "rmse_total": float(np.sqrt(np.mean((tot - [x["mu_total"] for x in d]) ** 2))),
                "rmse_total_climatology": float(np.sqrt(np.mean((tot - tt.mean()) ** 2))),
                "reliability_5bin": bins}

    rep = {"n_train": len(tr), "n_cal": len(ca), "held_out_2025": report(ho), "extra_2026": report(ex),
           "sha256": art["sha256"], "platt": art["platt"], "sigma_margin": sm, "sigma_total": st, "rho": rho}
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(art, indent=1, sort_keys=True))
    out.with_name("nba_pregame_v1_heldout.json").write_text(json.dumps(rep, indent=1))
    print(json.dumps(rep, indent=1))


if __name__ == "__main__":
    main()
