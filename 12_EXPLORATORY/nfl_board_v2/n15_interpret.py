"""W93.4 Part B: does N15 geometry move margin or total beyond the closing line? Rolling-origin ridge on market residuals."""
import json, sys
import numpy as np, pandas as pd
sys.path.insert(0, "src")
sys.path.insert(0, "12_EXPLORATORY")
from _fence import safe_out
from prediction_market_bot.c1_signal_ingestion.nfl_schedule_geometry import schedule_features
from prediction_market_bot.quant.inference import cluster_bootstrap
s = pd.read_parquet("exp_output/NFL_EVENTS/raw/schedules/schedules_20261020T001136Z.parquet")
s = s[s.home_score.notna() & s.spread_line.notna() & s.total_line.notna()].reset_index(drop=True)
f = schedule_features(s)
s["res_m"] = (s.home_score - s.away_score) - s.spread_line
s["res_t"] = (s.home_score + s.away_score) - s.total_line
X = pd.DataFrame({
    "away_miles_k": f.a_miles / 1000, "away_tz_east": f.a_tz_shift.clip(lower=0), "away_tz_west": (-f.a_tz_shift).clip(lower=0),
    "short_diff": f.a_short_week.astype(float) - f.h_short_week.astype(float), "bye_diff": f.a_post_bye.astype(float) - f.h_post_bye.astype(float),
    "neutral": f.h_neutral.astype(float), "intl": f.h_international.astype(float),
    "away_early_body": (f.a_body_clock_hour < 11).astype(float), "home_late_body": (f.h_body_clock_hour >= 20).astype(float),
}).fillna(0.0)
X["pid"] = s.index
def ridge(Xt, y, lam=50.0):
    Xm = Xt.mean(0); Xc = Xt - Xm; ym = y.mean()
    b = np.linalg.solve(Xc.T @ Xc + lam * np.eye(Xt.shape[1]), Xc.T @ (y - ym)); return b, ym - Xm @ b
cols = [c for c in X.columns if c != "pid"]
out = {"features": cols}
for tgt in ("res_m", "res_t"):
    gains = collections = {}
    diffs = {}
    for S in range(2012, 2026):
        tr, te = s.season < S, s.season == S
        b, a = ridge(X.loc[tr, cols].to_numpy(), s.loc[tr, tgt].to_numpy())
        pred = X.loc[te, cols].to_numpy() @ b + a
        base = (s.loc[te, tgt] - s.loc[tr, tgt].mean()).to_numpy() ** 2     # intercept-only baseline
        mod = (s.loc[te, tgt].to_numpy() - pred) ** 2
        for i, d in zip(s.index[te], base - mod): diffs[str(i)] = [float(d)]
    m, lo, hi = cluster_bootstrap(diffs, b=2000)
    full_b, _ = ridge(X[cols].to_numpy(), s[tgt].to_numpy())
    # OLS SEs on the full sample for the headline coefficients
    Xo = np.column_stack([np.ones(len(s)), X[cols].to_numpy()]); y = s[tgt].to_numpy()
    beta = np.linalg.lstsq(Xo, y, rcond=None)[0]; r = y - Xo @ beta
    se = np.sqrt(np.diag(np.linalg.inv(Xo.T @ Xo)) * (r @ r) / (len(y) - Xo.shape[1]))
    out[tgt] = dict(n_games_scored=len(diffs), mse_gain=[round(m, 3), round(lo, 3), round(hi, 3)],
                    ols={c: [round(float(beta[i + 1]), 3), round(float(se[i + 1]), 3)] for i, c in enumerate(cols)})
    print(tgt, out[tgt]["n_games_scored"], out[tgt]["mse_gain"])
    for c in cols: print("  ", c, out[tgt]["ols"][c])
json.dump(out, open(safe_out("nfl_board_v2/n15_interpret.json"), "w"), indent=1)
