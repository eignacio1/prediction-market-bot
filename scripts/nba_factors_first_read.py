#!/usr/bin/env python3
"""W79.3 Part B: first read of two NBA factor classes (pace+efficiency, rest). Seasons 2016-2025 (label = ending year);
2026 and 2027 are not read. Rules fixed before any result was computed:
  TRAIT  : split-half (first vs second half of a team-season) Pearson r, cluster bootstrap CI over team-seasons;
           a trait iff the CI lower bound >= TRAIT_R_LOW.
  MOVES  : out-of-sample (fit 2016-2020, score 2021-2025) MSE of baseline minus MSE of baseline+factor, paired
           bootstrap over test games; the factor moves the target iff the 95% CI of the gain excludes 0.
Baselines are point-in-time: margin ~ home-minus-away season-to-date net rating; total ~ mean season-to-date game total.
"""
from __future__ import annotations

import glob
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))
from prediction_market_bot.c1_signal_ingestion.nba_data_rules import eligible_games, game_quality  # noqa: E402
from prediction_market_bot.c1_signal_ingestion.nba_factors import game_frame, rest_features, rolling_asof, team_game_table  # noqa: E402
from prediction_market_bot.c1_signal_ingestion.nba_point_in_time import PointInTime, tip_table  # noqa: E402

TRAIT_R_LOW = 0.30
TRAIN, TEST = range(2016, 2021), range(2021, 2026)
BOOT = 1000
rng = np.random.default_rng(79_3)


def load(root: Path, kind: str) -> pd.DataFrame:
    return pd.concat([pd.read_parquet(f) for f in sorted(glob.glob(str(root / "raw" / kind / "*.parquet")))], ignore_index=True)


def ols(X, y):
    A = np.column_stack([np.ones(len(X)), X])
    beta, *_ = np.linalg.lstsq(A, y, rcond=None)
    return beta


def pred(beta, X):
    return np.column_stack([np.ones(len(X)), X]) @ beta


def oos_gain(df, base, extra, target):
    d = df.dropna(subset=base + extra + [target])
    tr, te = d[d.season.isin(list(TRAIN))], d[d.season.isin(list(TEST))]
    e0 = (te[target] - pred(ols(tr[base], tr[target]), te[base])) ** 2
    e1 = (te[target] - pred(ols(tr[base + extra], tr[target]), te[base + extra])) ** 2
    diff = (e0 - e1).to_numpy()
    bs = np.array([diff[rng.integers(0, len(diff), len(diff))].mean() for _ in range(BOOT)])
    return dict(n_train=len(tr), n_test=len(te), mse_base=float(e0.mean()), mse_with=float(e1.mean()),
                gain=float(diff.mean()), gain_ci=[float(np.percentile(bs, 2.5)), float(np.percentile(bs, 97.5))],
                moves=bool(np.percentile(bs, 2.5) > 0))


def coef_ci(df, cols, target, which):
    d = df[df.season.isin(list(range(2016, 2026)))].dropna(subset=cols + [target])
    X, y = d[cols].to_numpy(), d[target].to_numpy()
    est = ols(X, y)[1:]
    bs = np.array([ols(X[i], y[i])[1:] for i in (rng.integers(0, len(d), len(d)) for _ in range(300))])
    return {c: dict(coef=float(est[j]), ci=[float(np.percentile(bs[:, j], 2.5)), float(np.percentile(bs[:, j], 97.5))])
            for j, c in enumerate(cols) if c in which}


def split_half(tg, metric):
    r = tg.sort_values(["team_id", "season", "tip_latest"]).copy()
    r["k"] = r.groupby(["team_id", "season"]).cumcount()
    r["n"] = r.groupby(["team_id", "season"])["k"].transform("size")
    r["half"] = (r["k"] >= r["n"] / 2).astype(int)
    p = r.groupby(["team_id", "season", "half"])[metric].mean().unstack("half").dropna()
    p = p[p.index.get_level_values("season").isin(range(2016, 2026))]
    x, y = p[0].to_numpy(), p[1].to_numpy()
    r0 = float(np.corrcoef(x, y)[0, 1])
    bs = []
    for _ in range(BOOT):
        i = rng.integers(0, len(x), len(x))
        bs.append(np.corrcoef(x[i], y[i])[0, 1])
    lo, hi = float(np.percentile(bs, 2.5)), float(np.percentile(bs, 97.5))
    return dict(n_team_seasons=len(p), r=r0, ci=[lo, hi], spearman_brown=float(2 * r0 / (1 + r0)), trait=bool(lo >= TRAIT_R_LOW))


def main(root: Path, out: Path) -> dict:
    sch, box, off = load(root, "schedule"), load(root, "team_box"), load(root, "officials")
    espn = load(root, "espn_schedule")
    tips = tip_table(sch, espn)
    q = game_quality(sch.assign(game_id=sch.game_id.astype(str)), box.assign(game_id=box.game_id.astype(str)),
                     off.assign(game_id=off.game_id.astype(str)), tips)
    elig = eligible_games(q)
    tg = team_game_table(sch, box, tips)
    tg = tg[tg.game_id.isin(elig) & (tg.season_type == "regular-season") & tg.season.between(2016, 2025)].copy()
    tg["net"] = tg["ortg"] - tg["drtg"]
    tg["mov"] = tg["pts"] - tg["opp_pts"]
    tg = rolling_asof(tg, cols=("pace", "ortg", "drtg", "total", "net"))
    # independent PIT cross-check on a sample against the contract's own predicate
    pit = PointInTime(tips)
    chk = tg.sample(300, random_state=1)
    for _, r in chk.iterrows():
        done = pit.completed_before(r.game_id)
        want = tg[(tg.team_id == r.team_id) & (tg.season == r.season) & tg.game_id.isin(done)].shape[0]
        assert want == r.n_prior, (r.game_id, want, r.n_prior)
    tg = rest_features(tg)
    tg["pace_dev_l10"] = tg["pace_l10"] - tg["pace_ytd"]
    tg["net_dev_l10"] = tg["net_l10"] - tg["net_ytd"]
    feats = ["pace_ytd", "ortg_ytd", "drtg_ytd", "total_ytd", "net_ytd", "net_dev_l10", "pace_dev_l10",
             "rest_days", "b2b", "three_in_four", "g_last7"]
    g = game_frame(tg, feats).reset_index()
    g["base_margin"] = g.h_net_ytd - g.a_net_ytd
    g["base_total"] = (g.h_total_ytd + g.a_total_ytd) / 2
    g["pace_mean"] = (g.h_pace_ytd + g.a_pace_ytd) / 2
    g["eff_mean"] = (g.h_ortg_ytd + g.a_ortg_ytd + g.h_drtg_ytd + g.a_drtg_ytd) / 4
    g["net_dev_diff"] = g.h_net_dev_l10 - g.a_net_dev_l10
    g["pace_dev_mean"] = (g.h_pace_dev_l10 + g.a_pace_dev_l10) / 2
    g["rest_diff"] = g.h_rest_days.clip(upper=4) - g.a_rest_days.clip(upper=4)
    for c in ("b2b", "three_in_four"):
        g[f"{c}_diff"] = g[f"h_{c}"] - g[f"a_{c}"]
    g["load7_diff"] = g.h_g_last7 - g.a_g_last7
    g["b2b_sum"] = g.h_b2b + g.a_b2b
    g["load7_sum"] = g.h_g_last7 + g.a_g_last7
    gm = g.dropna(subset=["base_margin", "base_total"])
    res = {"games_modelled": int(len(gm)), "pit_crosscheck_games": 300, "seasons": "2016-2025 regular season",
           "trait_rule_r_ci_lower_ge": TRAIT_R_LOW, "stability": {}, "moves": {}, "coefficients": {}}
    for m in ("pace", "ortg", "drtg", "net"):
        res["stability"][m] = split_half(tg, m)
    tgr = tg.dropna(subset=["rest_days"]).copy()
    for m in ("b2b", "three_in_four"):
        res["stability"][f"{m}_rate"] = split_half(tgr, m)
    res["moves"]["pace_eff_vs_total"] = oos_gain(gm, ["base_total"], ["pace_mean", "eff_mean", "pace_dev_mean"], "total")
    res["moves"]["recent_eff_vs_margin"] = oos_gain(gm, ["base_margin"], ["net_dev_diff"], "margin")
    gr = gm.dropna(subset=["rest_diff"])
    res["moves"]["rest_vs_margin"] = oos_gain(gr, ["base_margin"], ["rest_diff", "b2b_diff", "three_in_four_diff", "load7_diff"], "margin")
    res["moves"]["rest_vs_total"] = oos_gain(gr, ["base_total"], ["b2b_sum", "load7_sum"], "total")
    res["coefficients"]["margin_on_rest"] = coef_ci(gr, ["base_margin", "rest_diff", "b2b_diff", "three_in_four_diff", "load7_diff"],
                                                    "margin", {"rest_diff", "b2b_diff", "three_in_four_diff", "load7_diff"})
    res["coefficients"]["total_on_rest"] = coef_ci(gr, ["base_total", "b2b_sum", "load7_sum"], "total", {"b2b_sum", "load7_sum"})
    res["coefficients"]["margin_on_recent_eff"] = coef_ci(gm, ["base_margin", "net_dev_diff"], "margin", {"net_dev_diff"})
    odd = gr[gr.season % 2 == 1]
    even = gr[gr.season % 2 == 0]
    res["rest_effect_stability_odd_vs_even_seasons"] = {
        k: {"odd": coef_ci(odd, ["base_margin", "b2b_diff"], "margin", {"b2b_diff"})["b2b_diff"],
            "even": coef_ci(even, ["base_margin", "b2b_diff"], "margin", {"b2b_diff"})["b2b_diff"]} for k in ("b2b_diff",)}
    res["tip_imputed_share_in_universe"] = float(tips.loc[tips.index.isin(elig) & tips.season_type.eq("regular-season"), "tip_imputed"].mean())
    out.write_text(json.dumps(res, indent=2))
    return res


if __name__ == "__main__":
    root = Path(sys.argv[1]) if len(sys.argv) > 1 else REPO / "exp_output" / "NBA_EVENTS"
    out = Path(sys.argv[2]) if len(sys.argv) > 2 else REPO / "02_ARCHITECTURE_DESIGN" / "NBA_ENGINE" / "factors_first_read.json"
    print(json.dumps(main(root, out), indent=1))
