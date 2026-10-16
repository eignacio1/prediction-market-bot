"""EXPLORATORY -- W76.2 Part A: aggregate + orthogonality-test F8 unit availability against the rating layer's inputs."""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parent)); sys.path.insert(0, str(HERE.parent.parent / "src"))
from _fence import safe_out  # noqa: E402
import availability as A  # noqa: E402

_sp = importlib.util.spec_from_file_location("v0study", HERE / "study.py")
S = importlib.util.module_from_spec(_sp); _sp.loader.exec_module(S)
W = S.W
ROOT = HERE.parent.parent


def main():
    R = ROOT / "exp_output" / "NFL_EVENTS"
    sched = pd.read_parquet(sorted((R / "raw" / "schedules").glob("*.parquet"))[0])
    stats = pd.read_parquet(R / "aux" / "team_stats.parquet")
    df = W.build(sched, sched, stats)
    flags, tg, pit = A.build_flags(ROOT, sched, list(range(2018, 2026)), W.norm)
    res = {"flag_rows": int(len(flags)), "by_status": flags.groupby("status").agg(n=("share", "size"), mean_share=("share", "mean"), p_absent=("absent", "mean")).to_dict("index"),
           "by_unit": flags.groupby("unit").agg(n=("share", "size")).n.to_dict()}
    res["usable_team_games"] = float((tg.usable & tg.has_report).mean())
    rates = A.absence_rates(flags, 2022)
    res["absence_rates_le2022"] = rates
    lost = A.lost_table(flags, tg, rates)
    X = A.side_matrix(lost, tg)
    # team-point residuals vs engine-v0-style ridge on seasons <=2022 (descriptive fit)
    d = df.copy(); d["total"] = d.game_id.map(sched.set_index("game_id").eval("home_score+away_score")).astype(float)
    c = W.cols("full")
    tr = d[(d.season >= 2018) & (d.season <= 2022)]
    mm, mt = W.ridge(tr[c].to_numpy(float), tr.margin.to_numpy(float), 100.0), W.ridge(tr[c].to_numpy(float), tr.total.to_numpy(float), 100.0)
    pm, pt = W.pred(mm, d[c].to_numpy(float)), W.pred(mt, d[c].to_numpy(float))
    d["mu_h"], d["mu_a"] = (pt + pm) / 2, (pt - pm) / 2
    d["hs"], d["as"] = (d.total + d.margin) / 2, (d.total - d.margin) / 2
    side = pd.concat([pd.DataFrame(dict(game_id=d.game_id, team=d.home, mu=d.mu_h, pts=d.hs, own_off=d.eb_off_epa_h, own_def=d.eb_def_epa_h, opp_off=d.eb_off_epa_a, opp_def=d.eb_def_epa_a,
                                        own_pf=d.eb_pf_h, opp_pa=d.eb_pa_a, qb=d.qb_epa_h, oqb=d.qb_epa_a)),
                      pd.DataFrame(dict(game_id=d.game_id, team=d.away, mu=d.mu_a, pts=d["as"], own_off=d.eb_off_epa_a, own_def=d.eb_def_epa_a, opp_off=d.eb_off_epa_h, opp_def=d.eb_def_epa_h,
                                        own_pf=d.eb_pf_a, opp_pa=d.eb_pa_h, qb=d.qb_epa_a, oqb=d.qb_epa_h))])
    M = X.merge(side, on=["game_id", "team"], how="inner").dropna(subset=list(A.UNITS) + ["mu"])
    M["resid"] = M.pts - M.mu
    inputs = ["own_off", "opp_def", "own_pf", "opp_pa", "qb", "oqb", "own_def", "opp_off"]
    res["n_sides"] = int(len(M))
    res["corr_units_vs_inputs"] = {u: {i: float(np.corrcoef(M[u], M[i])[0, 1]) for i in inputs} for u in A.UNITS}
    res["corr_units_vs_mu"] = {u: float(np.corrcoef(M[u], M.mu)[0, 1]) for u in A.UNITS}
    # orthogonality of the fitted composite (coef fitted on <=2022) to the rating layer inputs
    fit = M[M.season <= 2022]
    coef, center = A.fit_coefs(fit[list(A.UNITS)], fit.resid.to_numpy(float))
    term = sum(coef[u] * (M[u] - center[u]) for u in A.UNITS)
    M["term"] = term
    res["coef_le2022"], res["center_le2022"] = coef, center
    res["term_sd_points"] = float(term.std())
    Z = np.column_stack([np.ones(len(M))] + [M[i].to_numpy(float) for i in inputs + ["mu"]])
    ok = ~np.isnan(Z).any(axis=1)
    b, *_ = np.linalg.lstsq(Z[ok], M.term.to_numpy(float)[ok], rcond=None)
    r2 = 1 - ((M.term.to_numpy(float)[ok] - Z[ok] @ b) ** 2).sum() / ((M.term.to_numpy(float)[ok] - M.term.to_numpy(float)[ok].mean()) ** 2).sum()
    res["R2_term_on_rating_inputs"] = float(r2)
    res["corr_term_resid_oos"] = float(np.corrcoef(M[M.season >= 2023].term, M[M.season >= 2023].resid)[0, 1])
    res["corr_term_mu"] = float(np.corrcoef(M.term, M.mu)[0, 1])
    # per-unit incremental: stand-alone slope of residual on each unit loss (points per expected starter lost), seasons <=2022 and >=2023
    sl = {}
    for u in A.UNITS:
        for lab, sub in (("le2022", M[M.season <= 2022]), ("ge2023", M[M.season >= 2023])):
            x = sub[u] - sub[u].mean(); sl[f"{u}_{lab}"] = float((x * (sub.resid - sub.resid.mean())).sum() / (x * x).sum())
    res["standalone_slope_points_per_starter"] = sl
    res["loss_dist"] = {u: dict(mean=float(M[u].mean()), sd=float(M[u].std()), p_gt0=float((M[u] > 0.05).mean())) for u in A.UNITS}
    # trait-or-noise: team-level season persistence of mean unit loss (corr of team's mean loss season s vs s+1)
    tp = {}
    for u in A.UNITS:
        m = M.groupby(["team", "season"])[u].mean().unstack()
        pairs = [(m[s], m[s + 1]) for s in range(2018, 2025) if s in m and s + 1 in m]
        a = np.concatenate([x.to_numpy() for x, _ in pairs]); b_ = np.concatenate([y.to_numpy() for _, y in pairs]); k = ~(np.isnan(a) | np.isnan(b_))
        tp[u] = float(np.corrcoef(a[k], b_[k])[0, 1])
    res["season_persistence_of_team_mean_loss"] = tp
    safe_out(HERE / "part_a_avail.json").write_text(json.dumps(res, indent=1, default=float))
    print(json.dumps(res, indent=1, default=float))


if __name__ == "__main__":
    main()
