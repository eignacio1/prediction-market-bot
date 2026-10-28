#!/usr/bin/env python3
"""W93.2 Part A: NBA travel / schedule geometry (B12) - does it move game margin / total beyond B1 + B9 + B2 + prior-season carry?

Rules fixed before any result (same protocol as W92.3): train labels 2017-2024 (season label = ending year), test 2025 and 2026,
regular season only; paired squared-error gain, 1000-rep bootstrap over test games (one row per game = the cluster), seed 93_2;
the factor moves the target iff the 95% CI of the gain excludes 0. Baseline = W92.3's (base_margin, net_dev_diff, rest_diff,
b2b_diff, prior_margin / base_total, pace_mean, eff_mean, pace_dev_mean, b2b_sum, prior_total_mean, prior_pace_mean).
Usage: run_w93_2.py [NBA_EVENTS root] [out json]
"""
from __future__ import annotations

import glob
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from _fence import safe_out  # noqa: E402
from prediction_market_bot.c1_signal_ingestion.nba_data_rules import eligible_games, game_quality  # noqa: E402
from prediction_market_bot.c1_signal_ingestion.nba_factors import game_frame, rest_features, rolling_asof, team_game_table  # noqa: E402
from prediction_market_bot.c1_signal_ingestion.nba_point_in_time import tip_table  # noqa: E402
from prediction_market_bot.c1_signal_ingestion.nba_schedule_geometry import schedule_geometry, venue_table  # noqa: E402

TRAIN, TESTS = range(2017, 2025), (2025, 2026)
BOOT = 1000
ALT_VENUES = ("Denver", "Salt Lake City")
rng = np.random.default_rng(93_2)


def rd(root, kind):
    return pd.concat([pd.read_parquet(f) for f in sorted(glob.glob(str(root / "raw" / kind / "*.parquet")))], ignore_index=True)


def ols(X, y):
    beta, *_ = np.linalg.lstsq(np.column_stack([np.ones(len(X)), X]), y, rcond=None)
    return beta


def pred(b, X):
    return np.column_stack([np.ones(len(X)), X]) @ b


def gain(df, base, extra, target, test_seasons):
    d = df.dropna(subset=base + extra + [target])
    tr, te = d[d.season.isin(list(TRAIN))], d[d.season.isin(list(test_seasons))]
    e0 = (te[target] - pred(ols(tr[base], tr[target]), te[base])) ** 2
    e1 = (te[target] - pred(ols(tr[base + extra], tr[target]), te[base + extra])) ** 2
    diff = (e0 - e1).to_numpy()
    bs = np.array([diff[rng.integers(0, len(diff), len(diff))].mean() for _ in range(BOOT)])
    beta = ols(tr[base + extra], tr[target])[1 + len(base):]
    return dict(n_train=len(tr), n_test=len(te), mse_base=float(e0.mean()), mse_with=float(e1.mean()), gain=float(diff.mean()),
                gain_ci=[float(np.percentile(bs, 2.5)), float(np.percentile(bs, 97.5))], moves=bool(np.percentile(bs, 2.5) > 0),
                extra_coefs=dict(zip(extra, map(float, beta))))


def boot_mean(x, reps=BOOT):
    x = np.asarray(x, float)
    x = x[~np.isnan(x)]
    bs = np.array([x[rng.integers(0, len(x), len(x))].mean() for _ in range(reps)])
    return dict(n=int(len(x)), mean=float(x.mean()), ci=[float(np.percentile(bs, 2.5)), float(np.percentile(bs, 97.5))])


def build_frame(root):
    sch, box, off, espn = rd(root, "schedule"), rd(root, "team_box"), rd(root, "officials"), rd(root, "espn_schedule")
    sch["game_id"] = sch["game_id"].astype(str)
    tips = tip_table(sch, espn)
    q = game_quality(sch, box.assign(game_id=box.game_id.astype(str)), off.assign(game_id=off.game_id.astype(str)), tips)
    elig = eligible_games(q)
    venues = venue_table(sch, espn)
    tg = team_game_table(sch, box, tips)
    tg = tg[tg.game_id.isin(elig) & (tg.season_type == "regular-season") & tg.season.between(2016, 2026)].copy()
    tg["net"] = tg["ortg"] - tg["drtg"]
    tg = rolling_asof(tg, cols=("pace", "ortg", "drtg", "total", "net"))
    tg = rest_features(tg)
    tg["pace_dev_l10"] = tg["pace_l10"] - tg["pace_ytd"]
    tg["net_dev_l10"] = tg["net_l10"] - tg["net_ytd"]
    sm = tg.groupby(["team_id", "season"])[["pace", "total", "net"]].mean().add_prefix("prior_")
    tg = tg.merge(sm.reset_index().assign(season=lambda d: d.season + 1), on=["team_id", "season"], how="left")
    # geometry is computed over ALL of the team's eligible regular-season games (so travel legs are real), then merged
    geo = schedule_geometry(tg[["game_id", "team_id", "side", "season", "date", "tip_earliest", "tip_latest"]], venues)
    gcols = ["travel_mi", "tz_shift", "tz_cross", "east", "alt_m", "alt_gain", "g_last4", "g_last6", "miles_last7", "road_run",
             "home_run", "body_tip_hr", "late_body", "city"]
    tg = tg.merge(geo[["game_id", "team_id"] + gcols], on=["game_id", "team_id"], how="left")
    feats = ["pace_ytd", "ortg_ytd", "drtg_ytd", "total_ytd", "net_ytd", "net_dev_l10", "pace_dev_l10", "rest_days", "b2b",
             "three_in_four", "g_last7", "prior_pace", "prior_total", "prior_net"] + gcols[:-1]
    g = game_frame(tg, feats).reset_index()
    h_city = tg[tg.side == "home"].set_index("game_id")["city"]
    g["city"] = g["game_id"].map(h_city)
    g["base_margin"] = g.h_net_ytd - g.a_net_ytd
    g["net_dev_diff"] = g.h_net_dev_l10 - g.a_net_dev_l10
    g["rest_diff"] = g.h_rest_days.clip(upper=4) - g.a_rest_days.clip(upper=4)
    g["b2b_diff"] = g.h_b2b - g.a_b2b
    g["base_total"] = (g.h_total_ytd + g.a_total_ytd) / 2
    g["pace_mean"] = (g.h_pace_ytd + g.a_pace_ytd) / 2
    g["eff_mean"] = (g.h_ortg_ytd + g.a_ortg_ytd + g.h_drtg_ytd + g.a_drtg_ytd) / 4
    g["pace_dev_mean"] = (g.h_pace_dev_l10 + g.a_pace_dev_l10) / 2
    g["b2b_sum"] = g.h_b2b + g.a_b2b
    g["prior_margin"] = g.h_prior_net - g.a_prior_net
    g["prior_total_mean"] = (g.h_prior_total + g.a_prior_total) / 2
    g["prior_pace_mean"] = (g.h_prior_pace + g.a_prior_pace) / 2
    # geometry features (scaled so coefficients are readable)
    g["d_miles"] = (g.h_travel_mi - g.a_travel_mi) / 1000
    g["d_miles7"] = (g.h_miles_last7 - g.a_miles_last7) / 1000
    g["d_g_last4"] = g.h_g_last4 - g.a_g_last4
    g["d_road_run"] = g.h_road_run - g.a_road_run
    g["h_tz"], g["a_tz"] = g.h_tz_shift, g.a_tz_shift
    g["alt_gain_a"] = g.a_alt_gain / 1000
    g["d_late_body"] = g.h_late_body - g.a_late_body
    g["s_miles"] = (g.h_travel_mi + g.a_travel_mi) / 1000
    g["s_late_body"] = g.h_late_body + g.a_late_body
    g["s_g_last4"] = g.h_g_last4 + g.a_g_last4
    g["s_tz_cross"] = g.h_tz_cross + g.a_tz_cross
    g["venue_alt"] = g.h_alt_m / 1000
    g["altitude"] = g.city.isin(ALT_VENUES).astype(float)
    return g[g.season.isin(list(range(2017, 2027)))].copy(), tg


def descriptive(g):
    """The splits (granularity-index part 1): home margin / total by geometry bucket, all 2017-26 regular-season games."""
    d = {}
    g = g.dropna(subset=["margin"])
    base_m, base_t = g.margin.mean(), g.total.mean()
    d["league"] = dict(n=int(len(g)), home_margin=float(base_m), total=float(base_t))
    def split(name, mask, col, ref=None):
        sub, rest = g[mask], g[~mask]
        r = dict(bucket=boot_mean(sub[col]), rest=boot_mean(rest[col]))
        r["diff"] = r["bucket"]["mean"] - r["rest"]["mean"]
        d[name] = r
    split("altitude venue (DEN/UTA) - home margin", g.altitude == 1, "margin")
    split("altitude venue (DEN/UTA) - total", g.altitude == 1, "total")
    split("visitor crossed >=2 zones east - home margin", g.a_tz_shift >= 2, "margin")
    split("visitor crossed >=2 zones west - home margin", g.a_tz_shift <= -2, "margin")
    split("visitor travel >=1500 mi - home margin", g.a_travel_mi >= 1500, "margin")
    split("host travel >=1500 mi - home margin", g.h_travel_mi >= 1500, "margin")
    split("visitor played >=4 of the prior 6 nights - home margin", g.a_g_last6 >= 4, "margin")
    split("visitor on 4th+ road game - home margin", g.a_road_run >= 4, "margin")
    split("host late body-clock start (<12 or >=22) - total", g.h_late_body == 1, "total")
    split("visitor late body-clock start - total", g.a_late_body == 1, "total")
    # stability over time: altitude home edge by season (rank against history at the same point)
    per = {}
    for s, sg in g.groupby("season"):
        a, o = sg[sg.altitude == 1].margin, sg[sg.altitude == 0].margin
        per[str(s)] = dict(n_alt=int(len(a)), edge=float(a.mean() - o.mean()))
    d["altitude_edge_by_season"] = per
    return d


def main(root: Path, out: Path):
    t0 = time.time()
    g, tg = build_frame(root)
    print("frame", len(g), "games", round(time.time() - t0), "s", flush=True)
    res = {"frame_games": int(len(g)), "unmatched_city_games": int(g.city.isna().sum()), "partA": {"gain": {}, "descriptive": descriptive(g)}}
    gmf = g.dropna(subset=["base_margin", "base_total"])
    bm, bt = ["base_margin", "net_dev_diff", "rest_diff", "b2b_diff"], ["base_total", "pace_mean", "eff_mean", "pace_dev_mean", "b2b_sum"]
    bmp, btp = bm + ["prior_margin"], bt + ["prior_total_mean", "prior_pace_mean"]
    specs = {
        "margin | travel + tz + altitude over baseline + prior": (bmp, ["d_miles", "h_tz", "a_tz", "alt_gain_a"], "margin"),
        "margin | schedule density over baseline + prior": (bmp, ["d_g_last4", "d_miles7", "d_road_run"], "margin"),
        "margin | all geometry over baseline + prior": (bmp, ["d_miles", "h_tz", "a_tz", "alt_gain_a", "d_g_last4", "d_miles7", "d_road_run", "d_late_body"], "margin"),
        "margin | all geometry over baseline (no prior)": (bm, ["d_miles", "h_tz", "a_tz", "alt_gain_a", "d_g_last4", "d_miles7", "d_road_run", "d_late_body"], "margin"),
        "total | geometry over baseline + prior": (btp, ["s_miles", "s_late_body", "s_g_last4", "s_tz_cross", "venue_alt"], "total"),
        "total | altitude only over baseline + prior": (btp, ["venue_alt"], "total"),
        "total | geometry over baseline (no prior)": (bt, ["s_miles", "s_late_body", "s_g_last4", "s_tz_cross", "venue_alt"], "total"),
    }
    for name, (b, e, t) in specs.items():
        r = {str(ts): gain(gmf, b, e, t, [ts]) for ts in TESTS}
        r["pooled_2025_26"] = gain(gmf, b, e, t, list(TESTS))
        res["partA"]["gain"][name] = r
        print(name, {k: (round(v["gain"], 3), [round(x, 3) for x in v["gain_ci"]], v["n_test"]) for k, v in r.items()}, flush=True)
    safe_out(out).write_text(json.dumps(res, indent=2, default=float))
    print("done", round(time.time() - t0), "s")


if __name__ == "__main__":
    root = Path(sys.argv[1]) if len(sys.argv) > 1 else REPO / "exp_output" / "NBA_EVENTS"
    out = Path(sys.argv[2]) if len(sys.argv) > 2 else Path(__file__).with_name("results_W93_2.json")
    main(root, out)
