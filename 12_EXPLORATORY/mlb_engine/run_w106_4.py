"""W106.4 Part B driver: train season 1, test season 2, ablations vs naive. PYTHONPATH=src.

usage: python 12_EXPLORATORY/mlb_engine/run_w106_4.py [store_root] -> writes RESULTS_W106_4.json next to this file.
"""
import json
import sys
from pathlib import Path

import pandas as pd

from prediction_market_bot.mlb_engine import lineup_aware as la
from prediction_market_bot.mlb_engine import model_lineup as ml

ROOT = Path(sys.argv[1]) if len(sys.argv) > 1 else Path.home() / "mlb_store"
T = ROOT / "tables"
ARMS = {
    "base(W105.3)": la.BASE_FEATURES,
    "+platoon": ["lineup_woba_vsH", "starter_woba_vs_lineup", "is_home"],
    "+bullpen": la.BASE_FEATURES + ["pen_woba_allowed", "pen_fatigue", "starter_share"],
    "+park": la.BASE_FEATURES + ["park_logf"],
    "all": la.LINEUP_FEATURES,
}


def load():
    return {k: pd.read_parquet(T / f"{k}.parquet") for k in ("pitches", "pa", "games", "lineups")}


def main():
    t = load()
    pa = t["pa"]
    tr_mask = pa["game_date"] < "2025-01-01"
    mu = float(pa[tr_mask].woba_value.sum() / pa[tr_mask].woba_denom.sum())
    d = la.design_lineup(t["games"], t["lineups"], pa, t["pitches"], mu)
    train, test = d[d.game_date < "2025-01-01"], d[d.game_date >= "2025-01-01"]
    # base rates from TRAIN games
    trp = ml.price(ml.RunModel(["is_home"]).fit(train), train)
    base = {c: float(trp[c].mean()) for c in ("home_win", "over", "home_rl")}
    out = {"mu": mu, "n_train_rows": len(train), "n_test_rows": len(test), "base": base, "arms": {}}
    for name, feats in ARMS.items():
        m = ml.RunModel(feats).fit(train)
        pr = ml.price(m, test)
        out["arms"][name] = {"k": m.k, "coef": dict(zip(feats, map(float, m.coef))), **ml.score(pr, base)}
        r = out["arms"][name]
        print(f"{name:14s} n={r['moneyline']['n']} k={m.k:.1f} " + " | ".join(
            f"{mk}: B {r[mk]['brier']:.5f} (naive {r[mk]['brier_naive']:.5f}) gain {r[mk]['gain_brier'][0]:+.5f} "
            f"[{r[mk]['gain_brier'][1]:+.5f},{r[mk]['gain_brier'][2]:+.5f}]" for mk in ("moneyline", "total", "runline")))
    (Path(__file__).parent / "RESULTS_W106_4.json").write_text(json.dumps(out, indent=1, default=float))


if __name__ == "__main__":
    main()
