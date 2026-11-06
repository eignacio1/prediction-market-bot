"""W105.3 driver: build store, run checks, build PIT tables, fit/evaluate the Part C model. Off-box only.

Usage: PYTHONPATH=src python3 12_EXPLORATORY/mlb_engine/run_w105_3.py STORE [--skip-build] [--skip-box]
Writes <STORE>/tables/{pit_pitcher,pit_batter}.parquet and prints a JSON report.
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

from prediction_market_bot.mlb_engine import checks, model, pit, store


def main() -> None:
    root = Path(sys.argv[1])
    flags = set(sys.argv[2:])
    tdir = root / "tables"
    rep = {}
    if "--skip-build" not in flags:
        rep["build"] = store.build_store(root, [2024, 2025])
    p = pd.read_parquet(tdir / "pitches.parquet")
    pa = pd.read_parquet(tdir / "pa.parquet")
    g = pd.read_parquet(tdir / "games.parquet")
    lu = pd.read_parquet(tdir / "lineups.parquet")
    rep["rows"] = {"pitches": len(p), "pa": len(pa), "games": len(g), "lineups": len(lu)}
    rep["by_year_games"] = g.groupby(pd.to_datetime(g["game_date"]).dt.year).size().to_dict()
    rep["duplicate_pitches"] = checks.duplicate_pitches(p)

    reg = checks.load_register(root / "tables" / "register.parquet")
    rep["unresolved_ids"] = checks.unresolved_ids(p, reg)

    if "--skip-box" not in flags:
        g25 = g[pd.to_datetime(g["game_date"]).dt.year == 2025]
        sample = g25.sample(25, random_state=3)["game_pk"].tolist()
        bx = checks.pitch_counts_vs_box(g, sample)
        rep["box"] = {"n": len(bx), "pitch_diff_abs_mean": float(bx["pitch_diff"].abs().mean()),
                      "pitch_diff_max_abs": int(bx["pitch_diff"].abs().max()),
                      "exact_pitch_match": int((bx["pitch_diff"] == 0).sum()),
                      "score_match": int(bx["score_match"].sum())}

    pp = pit.pitcher_pit(p, pa)
    bp = pit.batter_pit(p, pa)
    pp.to_parquet(tdir / "pit_pitcher.parquet", index=False)
    bp.to_parquet(tdir / "pit_batter.parquet", index=False)
    rep["pit_rows"] = {"pitcher": len(pp), "batter": len(bp)}

    # Part C: train 2024, hold out 2025
    g = g.copy()
    g["game_date"] = pd.to_datetime(g["game_date"])
    yr = g["game_date"].dt.year
    tr_g, te_g = g[yr == 2024], g[yr == 2025]
    tr_pa = pa[pd.to_datetime(pa["game_date"]).dt.year == 2024]
    mu_bat = float(tr_pa["woba_value"].astype(float).sum() / tr_pa["woba_denom"].astype(float).sum())
    mu_pit = mu_bat
    d = model.design(g, lu, bp, pp, mu_bat, mu_pit)
    d_tr = d[d["game_pk"].isin(tr_g["game_pk"])]
    d_te = d[d["game_pk"].isin(te_g["game_pk"])]
    m = model.fit(d_tr)
    rep["coef"] = dict(zip(model.FEATURES, [float(x) for x in m.coef_]))
    rep["intercept"] = float(m.intercept_)
    pred = model.predict(m, te_g, d_te, line=8.5)
    train_pred = model.predict(m, tr_g, d_tr, line=8.5)
    base_home = float(train_pred["home_win"].mean())
    base_over = float(train_pred["over"].mean())
    y_h, y_o = pred["home_win"].to_numpy(), pred["over"].to_numpy()
    out = {"n_test_games": len(pred), "n_train_games": len(train_pred), "base_home": base_home, "base_over": base_over}
    for name, pm, pb, y in (("moneyline", pred["p_home"].to_numpy(), np.full(len(pred), base_home), y_h),
                            ("total_8.5", pred["p_over"].to_numpy(), np.full(len(pred), base_over), y_o)):
        diff, lo, hi = model.boot_diff(pm, pb, y)
        out[name] = {"brier_model": model.brier(pm, y), "brier_baseline": model.brier(pb, y),
                     "improvement": diff, "ci95": [lo, hi]}
    rep["holdout"] = out
    print(json.dumps(rep, indent=2, default=str))


if __name__ == "__main__":
    main()
