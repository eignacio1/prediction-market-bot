"""EXPLORATORY -- NFL totals venue+weather challenger vs frozen EXP-037 (W68.3). Not a verdict. Plan: README.md (frozen before fitting).

Reads public nflverse copies + free Open-Meteo previous-day forecasts. Pre-2026 only. Writes only via safe_out().
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
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parent)); sys.path.insert(0, str(HERE.parent.parent / "src"))
from _fence import safe_out  # noqa: E402
from prediction_market_bot.c1_signal_ingestion.nfl_pregame_features import FEATURE_NAMES, NFLPregameFeatureBuilder  # noqa: E402
from vw_features import stadium_category, weather_effects  # noqa: E402

B, SEED, M = 20000, 20261009, 14
ALPHA = 0.05 / M
TESTS = [2023, 2024, 2025]
TOT_LADDER = [37.5, 40.5, 43.5, 46.5, 49.5, 52.5]
TT_LADDER = [14.5, 17.5, 20.5, 23.5, 26.5, 29.5]
VENUE = ["p_indoor", "p_turf"]
ARMS = {  # name -> (extra cols, first train season)
    "frozen": ([], 2015), "frozen_w21": ([], 2021),
    "venue": (VENUE, 2021), "venue_fcst": (VENUE + ["f_wind_eff", "f_cold_eff"], 2021),
    "venue_obs": (VENUE + ["o_wind_eff", "o_cold_eff"], 2021),
}


def phi(z):
    return 0.5 * (1.0 + np.vectorize(math.erf)(np.asarray(z, float) / math.sqrt(2.0)))


def ridge(X, y, lam=100.0):
    mu, sd = X.mean(0), X.std(0)
    sd[sd == 0] = 1.0
    Z = (X - mu) / sd
    w = np.linalg.solve(Z.T @ Z + lam * np.eye(Z.shape[1]), Z.T @ (y - y.mean()))
    return y.mean(), w, mu, sd


def pred(m, X):
    b0, w, mu, sd = m
    return b0 + ((X - mu) / sd) @ w


def boot(d, level=0.95, seed=SEED):
    rng = np.random.default_rng(seed)
    n = len(d)
    m = d[rng.integers(0, n, (B, n))].mean(1)
    lo, hi = (1 - level) / 2 * 100, (1 + level) / 2 * 100
    return dict(mean=float(d.mean()), lo=float(np.percentile(m, lo)), hi=float(np.percentile(m, hi)), level=level)


def build(sched, ext, stats, fc):
    fb = NFLPregameFeatureBuilder(stats, sched)
    exq = ext.set_index("game_id")
    reg = sched[(sched.game_type == "REG") & sched.home_score.notna() & (sched.season >= 2015) & (sched.season <= 2025)]
    rows = []
    for r in reg.itertuples():
        as_of = datetime(*map(int, str(r.gameday).split("-")), tzinfo=timezone.utc)
        out = fb.row(r.home_team, r.away_team, as_of, r.home_rest, r.away_rest)
        if out is None:
            continue
        row = {"game_id": r.game_id, "season": r.season, "week": r.week, "hs": r.home_score, "as": r.away_score}
        row.update(out["features"])
        row.update({k: v for k, v in stadium_category(ext, r.home_team, r.gameday).items() if k != "n_prior"})
        # FCST-ARM-BEGIN
        f = fc.get(r.game_id)
        fx = weather_effects(row["p_indoor"], f["wind_mph"] if f else None, f["temp_f"] if f else None)
        row["f_wind_eff"], row["f_cold_eff"] = fx["wind_eff"], fx["cold_eff"]
        # FCST-ARM-END
        if r.game_id in exq.index:  # observed: flagged upper bound only
            ox = weather_effects(row["p_indoor"], exq.wind.get(r.game_id), exq.temp.get(r.game_id))
        else:
            ox = weather_effects(row["p_indoor"], None, None)
        row["o_wind_eff"], row["o_cold_eff"] = ox["wind_eff"], ox["cold_eff"]
        rows.append(row)
    return pd.DataFrame(rows)


def contracts(mu_t, sd_t, mu_m, sd_m, rho):
    """Per-game over-probabilities: total ladder, then home/away team-total ladders."""
    out = [1 - phi((k - mu_t) / sd_t) for k in TOT_LADDER]
    for sgn in (+1, -1):
        mean = (mu_t + sgn * mu_m) / 2
        sd = math.sqrt((sd_t**2 + sd_m**2 + sgn * 2 * rho * sd_t * sd_m) / 4)
        out += [1 - phi((k - mean) / sd) for k in TT_LADDER]
    return out


def main():
    ap = argparse.ArgumentParser()
    for k in ("schedule", "schedule-ext", "team-stats", "forecasts"):
        ap.add_argument("--" + k, required=True)
    a = ap.parse_args()
    sched, ext, stats = pd.read_parquet(a.schedule), pd.read_parquet(a.schedule_ext), pd.read_parquet(a.team_stats)
    fc = json.loads(Path(a.forecasts).read_text())
    df = build(sched, ext, stats, fc)
    df["total"] = df.hs + df["as"]; df["margin"] = df.hs - df["as"]
    print("rows", len(df), "fcst coverage 2023-25", float(df[df.season >= 2023].game_id.isin(fc).mean()), file=sys.stderr)
    P = {k: [] for k in ARMS}
    meta = []
    for T in TESTS:
        te = df[df.season == T]
        ca = df[df.season == T - 1]
        for k, (extra, s0) in ARMS.items():
            tr = df[(df.season >= s0) & (df.season <= T - 2)]
            c = FEATURE_NAMES + extra
            mt = ridge(tr[c].to_numpy(float), tr.total.to_numpy(float))
            mm = ridge(tr[FEATURE_NAMES].to_numpy(float), tr.margin.to_numpy(float))
            rt = ca.total.to_numpy(float) - pred(mt, ca[c].to_numpy(float))
            rm = ca.margin.to_numpy(float) - pred(mm, ca[FEATURE_NAMES].to_numpy(float))
            sdt, sdm, rho = rt.std(ddof=1), rm.std(ddof=1), float(np.corrcoef(rt, rm)[0, 1])
            pt, pm = pred(mt, te[c].to_numpy(float)), pred(mm, te[FEATURE_NAMES].to_numpy(float))
            P[k].append(np.array([contracts(x, sdt, y, sdm, rho) for x, y in zip(pt, pm)]))
        meta.append(te)
    te = pd.concat(meta)
    seas = te.season.to_numpy()
    Y = np.column_stack([(te.total.to_numpy()[:, None] > np.array(TOT_LADDER)).astype(float),
                         (te.hs.to_numpy()[:, None] > np.array(TT_LADDER)).astype(float),
                         (te["as"].to_numpy()[:, None] > np.array(TT_LADDER)).astype(float)])
    Pa = {k: np.vstack(v) for k, v in P.items()}
    fam = {"game_total": slice(0, 6), "team_total": slice(6, 18)}
    br = {k: {f: ((Pa[k][:, s] - Y[:, s]) ** 2).mean(1) for f, s in fam.items()} for k in ARMS}
    res = {"n_games": int(len(te)), "tests": TESTS, "m": M, "alpha": ALPHA, "B": B,
           "brier": {k: {f: float(v.mean()) for f, v in br[k].items()} for k in ARMS}, "arms": {}}
    for k in ("frozen_w21", "venue", "venue_fcst", "venue_obs"):
        res["arms"][k] = {}
        for f in fam:
            d = br[k][f] - br["frozen"][f]
            ps = {str(T): float(d[seas == T].mean()) for T in TESTS}
            e = {"vs_frozen_ci95": boot(d), "vs_frozen_ci_corrected": boot(d, 1 - ALPHA), "per_season": ps,
                 "seasons_better": int(sum(v < 0 for v in ps.values()))}
            if k != "frozen_w21":
                d2 = br[k][f] - br["frozen_w21"][f]
                e["vs_frozen_w21_ci_corrected"] = boot(d2, 1 - ALPHA)
                e["beats_frozen"] = bool(e["vs_frozen_ci_corrected"]["hi"] < 0 and e["seasons_better"] >= 2
                                         and e["vs_frozen_w21_ci_corrected"]["hi"] < 0)
            res["arms"][k][f] = e
    safe_out(HERE / "results.json").write_text(json.dumps(res, indent=1, default=float))
    print(json.dumps(res, indent=1, default=float))


if __name__ == "__main__":
    main()
