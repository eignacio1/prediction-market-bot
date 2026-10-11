"""Fit + freeze models/nba_player_points_v1.json (EXP-039). Offline only (Hard Rule 4); run ONCE.

Split fixed in the EXP-039 pre-registration BEFORE fitting (seasons labelled by ending year):
  train        <= 2024  (through 2023-24)  ridge mean of points (lambda 100 fixed a priori)
  calibration  2025     (2024-25)            NB dispersion (MLE) + Platt (a, b) on the logit, strikes 10/15/20/25
  held-out     2026     (2025-26)            reported only; never used for any choice
Seasons 2023 and 2024 supply the training rows (2023 early-season rows are dropped by the >=10 prior-games rule).
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
from prediction_market_bot.c1_signal_ingestion import nba_player_ingest as P  # noqa: E402
from prediction_market_bot.c1_signal_ingestion.nba_player_features import (  # noqa: E402
    FEATURE_NAMES, QUALITATIVE_FEATURES, PlayerFeatureBuilder,
)
from prediction_market_bot.c1_signal_ingestion.nba_pregame_features import _dt  # noqa: E402
from prediction_market_bot.pregame_shadow.nba_player_points_model import (  # noqa: E402
    NBAPlayerPointsModel, logit, nb_sf,
)
from prediction_market_bot.pregame_shadow.nfl_model import canonical_sha  # noqa: E402

LAMBDA = 100.0
STRIKES = (10, 15, 20, 25)
TRAIN, CAL, HELD = (2023, 2024), 2025, 2026


def build_frame(raw: Path) -> list[dict]:
    games, stores = [], []
    for s in (*TRAIN, CAL, HELD):
        games += list(N.load_season(s, raw)["games"].values())
        stores.append(P.load_players(s, raw))
    fb = PlayerFeatureBuilder(games, stores)
    gmap = {g["game_id"]: g for g in games}
    rows = []
    for store in stores:
        for gid, rec in store["games"].items():
            g = gmap[gid]
            start = _dt(rec["start_time_utc"])
            for r in rec["rows"]:
                if r["dnp"]:
                    continue
                opp = g["away"] if r["team"] == g["home"] else g["home"]
                out = fb.row(r["player_id"], r["team"], opp, r["home"], g["season"], start, start)
                if out is None:
                    continue
                rows.append({"season": g["season"], "points": r["points"], "game_id": gid, **out["features"]})
    return rows


def arr(rows, keys):
    return np.array([[r[k] for k in keys] for r in rows], float)


def ridge(X, y):
    mu, sd = X.mean(0), X.std(0)
    sd[sd == 0] = 1.0
    Z = (X - mu) / sd
    w = np.linalg.solve(Z.T @ Z + LAMBDA * np.eye(Z.shape[1]), Z.T @ (y - y.mean()))
    return float(y.mean()), w, mu, sd


def nb_loglik(y, mu, r):
    from math import lgamma
    lg = np.frompyfunc(lgamma, 1, 1)
    p = r / (r + mu)
    return float(np.sum(lg(y + r).astype(float) - lgamma(r) - lg(y + 1).astype(float)
                        + r * np.log(p) + y * np.log1p(-p)))


def platt(x, y):
    a, b = 1.0, 0.0
    for _ in range(50):
        eta = a * x + b
        p = 1 / (1 + np.exp(-eta))
        w = p * (1 - p)
        Xd = np.column_stack([x, np.ones_like(x)])
        step = np.linalg.solve(Xd.T @ (Xd * w[:, None]) + 1e-9 * np.eye(2), Xd.T @ (y - p))
        a, b = a + step[0], b + step[1]
    return float(a), float(b)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--raw", required=True)
    ap.add_argument("--out", default=str(ROOT / "models" / "nba_player_points_v1.json"))
    args = ap.parse_args()
    rows = build_frame(Path(args.raw))
    tr = [r for r in rows if r["season"] in TRAIN]
    ca = [r for r in rows if r["season"] == CAL]
    ho = [r for r in rows if r["season"] == HELD]
    b0, w, mu, sd = ridge(arr(tr, FEATURE_NAMES), np.array([r["points"] for r in tr], float))
    art: dict = {"model_id": "nba_player_points_v1", "feature_names": FEATURE_NAMES, "lambda": LAMBDA,
                 "quantitative_features": len(FEATURE_NAMES), "qualitative_features": QUALITATIVE_FEATURES,
                 "train_seasons": list(TRAIN), "cal_season": CAL, "held_out_season": HELD,
                 "calibration_method": "NB dispersion MLE + logit Platt on strikes 10/15/20/25, calibration season",
                 "mean_model": {"intercept": b0, "coef": w.tolist(), "mean": mu.tolist(), "std": sd.tolist()},
                 "dispersion_r": 10.0, "platt": {"a": 1.0, "b": 0.0}}
    m0 = NBAPlayerPointsModel({**art, "sha256": canonical_sha(art)})
    mc = np.array([m0.mean_points(r) for r in ca])
    yc = np.array([r["points"] for r in ca], float)
    grid = np.exp(np.linspace(math.log(0.5), math.log(200), 60))
    r_hat = float(grid[int(np.argmax([nb_loglik(yc, mc, r) for r in grid]))])
    art["dispersion_r"] = r_hat
    xs, ys = [], []
    for k in STRIKES:
        xs += [logit(nb_sf(k, m, r_hat)) for m in mc]
        ys += [1.0 if p >= k else 0.0 for p in yc]
    a, bb = platt(np.array(xs), np.array(ys))
    art["platt"] = {"a": a, "b": bb}
    pt = np.array([r["points"] for r in tr], float)
    art["climatology"] = {str(k): float((pt >= k).mean()) for k in STRIKES}
    art["n_train"], art["n_cal"] = len(tr), len(ca)
    art["sha256"] = canonical_sha(art)
    model = NBAPlayerPointsModel(art)

    def report(frame, label):
        if not frame:
            return None
        out = {"n_player_games": len(frame), "n_games": len({r["game_id"] for r in frame}), "per_strike": {}}
        for sub, rs in (("all", frame), ("pts10>=15", [r for r in frame if r["pts10"] >= 15])):
            if not rs:
                continue
            tot_m = tot_c = n = 0.0
            for k in STRIKES:
                p = np.array([model.p_at_least(r, k) for r in rs])
                y = np.array([1.0 if r["points"] >= k else 0.0 for r in rs])
                bm, bc = float(np.mean((p - y) ** 2)), float(np.mean((art["climatology"][str(k)] - y) ** 2))
                out["per_strike"][f"{sub}:{k}"] = {"n": len(rs), "brier_model": bm, "brier_climatology": bc,
                                                   "mean_p": float(p.mean()), "obs": float(y.mean())}
                tot_m, tot_c, n = tot_m + bm * len(rs), tot_c + bc * len(rs), n + len(rs)
            out[f"brier_model_{sub}"], out[f"brier_climatology_{sub}"] = tot_m / n, tot_c / n
        out["rmse_points"] = float(np.sqrt(np.mean([(model.mean_points(r) - r["points"]) ** 2 for r in frame])))
        out["rmse_points_climatology"] = float(np.sqrt(np.mean((pt.mean() - np.array([r["points"] for r in frame])) ** 2)))
        out["label"] = label
        return out

    rep = {"n_train": len(tr), "n_cal": len(ca), "dispersion_r": r_hat, "platt": art["platt"],
           "sha256": art["sha256"], "feature_count": len(FEATURE_NAMES), "qualitative_features": QUALITATIVE_FEATURES,
           "train_seasons": list(TRAIN), "calibration_season": CAL,
           "calibration_in_sample": report(ca, "2024-25 (in-sample for Platt/dispersion)"),
           "held_out_2026": report(ho, "2025-26 (held out; reported only)")}
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(art, indent=1, sort_keys=True))
    out.with_name("nba_player_points_v1_heldout.json").write_text(json.dumps(rep, indent=1))
    print(json.dumps(rep, indent=1))


if __name__ == "__main__":
    main()
