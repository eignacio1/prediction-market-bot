"""EXP-028 runner. Stage 'validation' never reads the holdout rows' labels into any fit or score.
Stage 'holdout' runs once; a lock file refuses a second run."""
import json, sys
from pathlib import Path
import numpy as np
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
from prediction_market_bot.c3_forecasting import pregame_hits_model as m

OUT = Path(__file__).resolve().parent
df = m.load_population(ROOT / "exp_output/MLB/mlb_feature_matrix.csv")
tr, va = m.split(df, m.TRAIN), m.split(df, m.VALIDATION)
stage = sys.argv[1]

def brier(p, y): return float(np.mean((p - y) ** 2))

if stage == "validation":
    res = {"n_train": len(tr), "n_val": len(va), "C": {}}
    for C in m.C_GRID:
        p = m.PregameHitsModel(C).fit(tr).predict(va)
        res["C"][str(C)] = brier(p, va["y"].values)
    best = min(m.C_GRID, key=lambda c: res["C"][str(c)])
    res["chosen_C"] = best
    res["val_brier_climatology"] = brier(np.full(len(va), tr["y"].mean()), va["y"].values)
    # permutation-null control (pipeline-leak check), on TRAIN->VALIDATION only
    trp = tr.copy(); trp["y"] = m.permute_within_date(tr)
    pp = m.PregameHitsModel(best).fit(trp).predict(va)
    pb = np.full(len(va), trp["y"].mean())
    res["permutation_null_val"] = m.paired_delta(pb, pp, va["y"].values, va["game_id"].values)
    (OUT / "validation_results.json").write_text(json.dumps(res, indent=1, default=float))
    print(json.dumps(res, indent=1, default=float))
elif stage == "holdout":
    lock = OUT / "HOLDOUT_TOUCHED.lock"
    if lock.exists(): sys.exit("holdout already touched; refusing")
    lock.write_text("touched\n")
    C = json.loads((OUT / "validation_results.json").read_text())["chosen_C"]
    trva = df[(df.game_date >= m.TRAIN[0]) & (df.game_date <= m.VALIDATION[1])]
    ho = m.split(df, m.HOLDOUT)
    mod = m.PregameHitsModel(C).fit(trva)
    p, y, g = mod.predict(ho), ho["y"].values, ho["game_id"].values
    b0 = np.full(len(ho), trva["y"].mean())
    res = {"chosen_C": C, "n_holdout": len(ho), "n_games": int(ho.game_id.nunique()),
           "holdout_base_rate": float(y.mean()), "train_val_base_rate": float(trva["y"].mean()),
           "brier_model": brier(p, y), "brier_B0": brier(b0, y)}
    res["vs_B0"] = m.paired_delta(b0, p, y, g)
    res["vs_B1"] = m.paired_delta(m.baseline_b1(ho), p, y, g)
    res["B1_vs_B0"] = m.paired_delta(b0, m.baseline_b1(ho), y, g)
    ok = ho["y_backward"].notna().values
    hb = ho[ok]
    res["placebo_backward_vs_B0"] = m.paired_delta(b0[ok], p[ok], hb["y_backward"].values, hb["game_id"].values)
    res["coef"] = dict(zip(m.FEATURES, map(float, mod.lr_.coef_[0])))
    res["B2_market"] = "NOT TESTABLE: priced-and-featured overlap = 0 rows"
    (OUT / "holdout_results.json").write_text(json.dumps(res, indent=1, default=float))
    print(json.dumps(res, indent=1, default=float))
