"""EXPLORATORY -- W89.3 Part B: NFL venue+weather (N13/N14) on the total. Screen, then anchor+adjustment out of sample.

Term: rolling-origin ridge of (total - mu_t) on [p_indoor, p_turf, wind_eff, cold_eff] fit on seasons < T (forecast weather,
point-in-time), applied to season T. Close is the target; the line never enters the term. Test seasons 2023-2025.
Anchor: P(total > K) ~ Normal(total_line, sd_train). Adjusted: mean = total_line + (1-b_train)*term. b_train from seasons < T.
Outcomes are used only to score (paired Brier, realized net edge), never to pick strikes or weights beyond the ridge fit.
"""
from __future__ import annotations
import json, math, sys
from pathlib import Path
import numpy as np, pandas as pd
from scipy.stats import norm

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent)); sys.path.insert(0, str(HERE.parent / "20261011_nfl_totals_venue_weather")); sys.path.insert(0, str(HERE))
from _fence import safe_out  # noqa: E402
from vw_features import stadium_category, weather_effects  # noqa: E402
from screen import share_priced, unpriced_prob, FEE  # noqa: E402

COLS = ["p_indoor", "p_turf", "wind_eff", "cold_eff"]
OFFS = [-6, -3, 0, 3, 6]


def ridge(X, y, lam=50.0):
    mu, sd = X.mean(0), X.std(0) + 1e-9; Z = (X - mu) / sd; yc = y - y.mean()
    w = np.linalg.solve(Z.T @ Z + lam * np.eye(Z.shape[1]), Z.T @ yc)
    return lambda Xn: ((Xn - mu) / sd) @ w + 0.0


def main(terms, sched, fcst, out):
    t = pd.read_json(terms); S = pd.read_parquet(sched); fc = json.loads(Path(fcst).read_text())
    s = S[["game_id", "gameday", "home_team", "total_line"]]
    d = t.merge(s, on="game_id", how="left").dropna(subset=["total_line"])
    d = d[d.season >= 2021].copy(); rows = []
    ext = S[S.game_type == "REG"]
    for r in d.itertuples():
        c = stadium_category(ext, r.home_team, r.gameday); f = fc.get(r.game_id)
        fx = weather_effects(c["p_indoor"], f["wind_mph"] if f else None, f["temp_f"] if f else None)
        rows.append([c["p_indoor"], c["p_turf"], fx["wind_eff"], fx["cold_eff"]])
    d[COLS] = np.array(rows, float)
    d["resid"] = d.total - d.mu_t
    parts = []
    for T in (2023, 2024, 2025):
        tr, te = d[d.season < T], d[d.season == T].copy()
        f = ridge(tr[COLS].to_numpy(), tr.resid.to_numpy()); te["term"] = f(te[COLS].to_numpy()); tr = tr.copy(); tr["term"] = f(tr[COLS].to_numpy())
        b = share_priced(tr.mu_t.to_numpy(), tr.term.to_numpy(), tr.total_line.to_numpy(), tr.game_id.to_numpy(), B=500)["b"]
        te["sd"] = float((tr.total - tr.total_line).std()); te["b_tr"] = b; parts.append(te)
    te = pd.concat(parts)
    scr = share_priced(te.mu_t.to_numpy(), te.term.to_numpy(), te.total_line.to_numpy(), te.game_id.to_numpy())
    sd_term = float(te.term.std()); scr.update(term_sd=sd_term, unpriced_prob_1sd=unpriced_prob(sd_term, scr["hi"], 0.399 / te.total.std()),
                                            identified=bool(scr["hi"] - scr["lo"] < 1.0), n_games=int(len(te)))
    # anchor + adjustment, paired Brier and net edge over strikes
    rec = []
    for r in te.itertuples():
        adj = r.total_line + max(0.0, 1 - min(r.b_tr, 1.0)) * r.term
        for o in OFFS:
            K = r.total_line + o + 0.5
            pa, pj = 1 - norm.cdf(K, r.total_line, r.sd), 1 - norm.cdf(K, adj, r.sd); y = float(r.total > K)
            rec.append((r.game_id, o, pa, pj, y))
    R = pd.DataFrame(rec, columns=["g", "o", "pa", "pj", "y"])
    R["db"] = (R.pa - R.y) ** 2 - (R.pj - R.y) ** 2   # >0: adjustment better
    R["dp"] = R.pj - R.pa
    def cb(v, B=2000, seed=20261027):
        gi = R.groupby("g").indices; ks = list(gi); rng = np.random.default_rng(seed); m = []
        a = np.asarray(v)
        for _ in range(B):
            ix = np.concatenate([gi[ks[k]] for k in rng.choice(len(ks), len(ks))]); m.append(a[ix].mean())
        return [float(a.mean()), *map(float, np.percentile(m, [2.5, 97.5]))]
    res = {"screen": scr, "dBrier_vs_anchor": cb(R.db.to_numpy()), "n_strike_games": int(len(R)), "fee": FEE}
    # strikes where the adjustment moves price by more than the fee, scored on the side it favours
    big = R[R.dp.abs() > FEE].copy(); res["n_moves_gt_fee"] = int(len(big))
    if len(big):
        big["net"] = np.where(big.dp > 0, big.y - big.pa, big.pa - big.y) - FEE
        gi = big.groupby("g").indices; ks = list(gi); a = big.net.to_numpy(); rng = np.random.default_rng(1)
        m = [a[np.concatenate([gi[ks[k]] for k in rng.choice(len(ks), len(ks))])].mean() for _ in range(2000)]
        res["net_edge_per_contract_after_fee"] = [float(a.mean()), *map(float, np.percentile(m, [2.5, 97.5]))]
        res["strikes_clear"] = int((big.dp.abs() > FEE).sum()) if res["net_edge_per_contract_after_fee"][1] > 0 else 0
    else:
        res["strikes_clear"] = 0
    safe_out(out).write_text(json.dumps(res, indent=1)); print(json.dumps(res, indent=1))


if __name__ == "__main__":
    main(*sys.argv[1:5])
