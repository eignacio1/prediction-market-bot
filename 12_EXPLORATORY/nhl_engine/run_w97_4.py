"""W97.4 Parts B+C (held-out): walk-forward fit of the NHL engine, Poisson vs shared-factor NB, scored vs results.

Exploratory. Input: the frame from w97_4_build.py. Test seasons 2023-2025 (regular season); every fit uses seasons
BEFORE the test season only. Output: predictions long table (parquet) + summary json. No orders, no registry cells.
Usage: python3 run_w97_4.py <frame.parquet> <out_dir>
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
from prediction_market_bot.nhl_engine import model  # noqa: E402

TEST = [2023, 2024, 2025]
LEVEL = True   # point-in-time in-season level recalibration (model.level_adjust)
FAM = {"ML": [None], "SPREAD_HOME": [1.5, 2.5], "TOTAL": [4.5, 5.5, 6.5], "TEAMTOTAL_HOME": [2.5, 3.5], "TEAMTOTAL_AWAY": [2.5, 3.5]}


def outcomes(fr: pd.DataFrame) -> dict:
    d = (fr["home_score"] - fr["away_score"]).to_numpy(); t = (fr["home_score"] + fr["away_score"]).to_numpy()
    o = {("ML", None): (d > 0).astype(float)}
    for x in FAM["SPREAD_HOME"]: o[("SPREAD_HOME", x)] = (d > x).astype(float)
    for x in FAM["TOTAL"]: o[("TOTAL", x)] = (t > x).astype(float)
    for x in FAM["TEAMTOTAL_HOME"]: o[("TEAMTOTAL_HOME", x)] = (fr["home_score"].to_numpy() > x).astype(float)
    for x in FAM["TEAMTOTAL_AWAY"]: o[("TEAMTOTAL_AWAY", x)] = (fr["away_score"].to_numpy() > x).astype(float)
    return o


def probs(b: list) -> dict:
    p = {("ML", None): np.array([r["moneyline_home"] for r in b])}
    for x in FAM["SPREAD_HOME"]: p[("SPREAD_HOME", x)] = np.array([r["home_wins_by_over"][x] for r in b])
    for x in FAM["TOTAL"]: p[("TOTAL", x)] = np.array([r["total_over"][x] for r in b])
    for x in FAM["TEAMTOTAL_HOME"]: p[("TEAMTOTAL_HOME", x)] = np.array([r["home_goals_over"][x] for r in b])
    for x in FAM["TEAMTOTAL_AWAY"]: p[("TEAMTOTAL_AWAY", x)] = np.array([r["away_goals_over"][x] for r in b])
    return p


def main(frame: str, out: str) -> None:
    out_d = Path(out); out_d.mkdir(parents=True, exist_ok=True)
    fr = pd.read_parquet(frame)
    fr = fr[(fr["game_type"] == 2) & fr["reg_h"].notna() & fr["home_score"].notna()].reset_index(drop=True)
    rows, summ = [], {}
    for S in TEST:
        tr = fr[fr["season"] < S].reset_index(drop=True); te = fr[fr["season"] == S].reset_index(drop=True)
        hw = (tr["home_score"] > tr["away_score"]).to_numpy()
        fits = {"poisson": model.fit(tr, tr["reg_h"].to_numpy(), tr["reg_a"].to_numpy(), hw, force_poisson=True),
                "nb": model.fit(tr, tr["reg_h"].to_numpy(), tr["reg_a"].to_numpy(), hw)}
        ot = outcomes(te); otr = outcomes(tr)
        summ[S] = {"n_train": len(tr), "n_test": len(te), "k_nb": fits["nb"].k, "p_home_ot": fits["nb"].p_home_ot,
                   "coef": [float(c) for c in fits["nb"].coef]}
        for name, m in fits.items():
            lh, la = model.level_adjust(te, *m.rates(te), te["reg_h"].to_numpy(), te["reg_a"].to_numpy()) if LEVEL else m.rates(te)
            pr = probs(model.price_games(m, te, n_sim=20000, seed=S, rates=(lh, la)))
            for key, p in pr.items():
                y = ot[key]; clim = float(otr[key].mean())
                e = np.clip(p, 1e-4, 1 - 1e-4)
                summ[S].setdefault(name, {})[f"{key[0]}|{key[1]}"] = {
                    "brier": float(np.mean((p - y) ** 2)), "brier_clim": float(np.mean((clim - y) ** 2)),
                    "logloss": float(-np.mean(y * np.log(e) + (1 - y) * np.log(1 - e))), "base_rate": float(y.mean()), "mean_p": float(p.mean())}
                if name == "nb":
                    rows.append(pd.DataFrame({"game_id": te["game_id"], "season": S, "family": key[0], "strike": key[1] if key[1] is not None else np.nan,
                                              "p": p, "y": y, "start": te["start"], "home": te["home"], "away": te["away"]}))
    pd.concat(rows).to_parquet(out_d / "heldout_predictions.parquet")
    json.dump(summ, open(out_d / "heldout_summary.json", "w"), indent=1)
    for S in TEST:
        print(S, summ[S]["n_test"], "k=%.1f" % summ[S]["k_nb"], "pOT=%.3f" % summ[S]["p_home_ot"])
        for key in summ[S]["nb"]:
            a, b = summ[S]["poisson"][key], summ[S]["nb"][key]
            print("  %-18s brier pois %.4f nb %.4f clim %.4f | ll pois %.4f nb %.4f" % (key, a["brier"], b["brier"], b["brier_clim"], a["logloss"], b["logloss"]))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
