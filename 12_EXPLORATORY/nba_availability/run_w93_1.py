#!/usr/bin/env python3
"""W93.1: NBA availability known before tip (B5/B6). Part A: point-in-time status table + P(played | status) by season.
Part B (interpreted): does expected availability (statuses published before tip) predict margin beyond B1/B9 + prior-season
carry, and how much of 92.3's who-actually-played upper bound survives?

Rules fixed before any result: report cutoff = tip_earliest (lead 0; sensitivity lead 240 min); played = >= 60 s floor time;
status->p rates estimated on TRAIN seasons only (2023-2024); train 2023-2024 (injury reports exist from 2022-23 only),
test 2025 and 2026; paired MSE gain, 1000-rep bootstrap over test games, seed 93_1; moves iff 95% CI of gain excludes 0.
Usage: run_w93_1.py [NBA_EVENTS root] [out json]
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
from prediction_market_bot.c1_signal_ingestion import nba_availability as A  # noqa: E402
from prediction_market_bot.c1_signal_ingestion import nba_lineups as L  # noqa: E402
from prediction_market_bot.c1_signal_ingestion.nba_data_rules import eligible_games, game_quality  # noqa: E402
from prediction_market_bot.c1_signal_ingestion.nba_factors import game_frame, rest_features, rolling_asof, team_game_table  # noqa: E402
from prediction_market_bot.c1_signal_ingestion.nba_injury_reports import norm_name  # noqa: E402
from prediction_market_bot.c1_signal_ingestion.nba_point_in_time import tip_table  # noqa: E402

SEASONS = range(2021, 2027)
TRAIN, TESTS = (2023, 2024), (2025, 2026)
BOOT = 1000
rng = np.random.default_rng(93_1)
INJ_DIRS = [REPO / "12_EXPLORATORY/20261012_nba_points_minutes/inj", REPO / "12_EXPLORATORY/20261013_nba_games_availability/inj2026"]


def rd(root, kind, s=None):
    if s is None:
        return pd.concat([pd.read_parquet(f) for f in sorted(glob.glob(str(root / "raw" / kind / "*.parquet")))], ignore_index=True)
    return pd.read_parquet(root / "raw" / kind / f"{kind}_{s}.parquet")


def load_inj():
    """{ET date: {slot: {name: status}}}; later dirs override (the 2025-12-22+ URL-v2 re-fetch is complete)."""
    out = {}
    for d in INJ_DIRS:
        for f in sorted(glob.glob(str(d / "inj_*.json"))):
            day = pd.Timestamp(Path(f).stem.split("_")[1]).date()
            data = json.load(open(f))
            if data:
                out[day] = {k: v for k, v in data.items() if v is not None}
    return out


def ols(X, y):
    return np.linalg.lstsq(np.column_stack([np.ones(len(X)), X]), y, rcond=None)[0]


def pred(b, X):
    return np.column_stack([np.ones(len(X)), X]) @ b


def gain(df, base, extra, target, test_seasons, train=TRAIN):
    d = df.dropna(subset=base + extra + [target])
    tr, te = d[d.season.isin(list(train))], d[d.season.isin(list(test_seasons))]
    e0 = (te[target] - pred(ols(tr[base], tr[target]), te[base])) ** 2
    e1 = (te[target] - pred(ols(tr[base + extra], tr[target]), te[base + extra])) ** 2
    diff = (e0 - e1).to_numpy()
    bs = np.array([diff[rng.integers(0, len(diff), len(diff))].mean() for _ in range(BOOT)])
    beta = ols(tr[base + extra], tr[target])[1 + len(base):]
    return dict(n_train=len(tr), n_test=len(te), mse_base=float(e0.mean()), mse_with=float(e1.mean()), gain=float(diff.mean()),
                gain_ci=[float(np.percentile(bs, 2.5)), float(np.percentile(bs, 97.5))], moves=bool(np.percentile(bs, 2.5) > 0),
                extra_coefs=dict(zip(extra, map(float, beta))))


def main(root: Path, out: Path):
    t0 = time.time()
    sch, box, off, espn = rd(root, "schedule"), rd(root, "team_box"), rd(root, "officials"), rd(root, "espn_schedule")
    sch["game_id"] = sch["game_id"].astype(str)
    tips = tip_table(sch, espn)
    q = game_quality(sch, box.assign(game_id=box.game_id.astype(str)), off.assign(game_id=off.game_id.astype(str)), tips)
    elig = eligible_games(q)
    pgs, tgs = [], []
    for s in SEASONS:
        st = L.build_stints(rd(root, "pbp", s), rd(root, "lineups", s), rd(root, "schedule", s).assign(game_id=lambda d: d.game_id.astype(str)))
        kept, _ = L.clean_games(st)
        st = st[st.game_id.isin(kept & elig)]
        pgs.append(L.player_game_table(st))
        tgs.append(L.team_game_totals(st))
        print("season", s, round(time.time() - t0), "s", flush=True)
    pg, tg_t = pd.concat(pgs, ignore_index=True), pd.concat(tgs, ignore_index=True)
    gm = tips.loc[tips.index.isin(set(pg.game_id)), ["season", "tip_earliest", "tip_latest"]].copy()
    gm["day"] = [t.tz_convert(A.ET).date() for t in gm["tip_earliest"]]
    rt = L.player_asof_ratings(pg, tg_t, gm)
    sid = sch.drop_duplicates("game_id").set_index("game_id")
    team_of = pd.concat([pd.DataFrame({"game_id": sid.index, "side": "home", "team_id": sid["home_team_id"].to_numpy()}),
                         pd.DataFrame({"game_id": sid.index, "side": "away", "team_id": sid["away_team_id"].to_numpy()})])
    rot = L.rotation_weights(pg, team_of, gm)
    pb = rd(root, "player_box")
    names = pb.drop_duplicates("person_id").assign(norm_name=lambda d: (d.first_name.fillna("") + " " + d.family_name.fillna("")).map(norm_name))[["person_id", "norm_name"]]
    inj = load_inj()
    print("inj days", len(inj), "rot rows", len(rot), round(time.time() - t0), "s", flush=True)
    played = pg[pg.sec >= A.PLAYED_SEC][["game_id", "person_id"]].assign(played=1)
    res = {"partA": {}, "partB": {}}
    tables = {}
    for lead in (0, 240):
        stt = A.status_table(rot, names, gm, inj, lead_min=lead).merge(played, on=["game_id", "person_id"], how="left")
        stt["played"] = stt["played"].fillna(0).astype(int)
        stt["season"] = stt["game_id"].map(gm["season"])
        tables[lead] = stt
    st0 = tables[0]
    in_scope = st0[st0.season >= 2023]
    res["partA"]["team_games_with_report_by_season"] = (in_scope.groupby(["season", "game_id", "team_id"])["has_report"].max()
                                                        .groupby("season").agg(share="mean", team_games="size").to_dict("index"))
    listed = in_scope[in_scope.has_report].assign(l=lambda d: d.w * (d.status != A.UNREPORTED))
    res["partA"]["rotation_minutes_listed_share_by_season"] = (listed.groupby("season")["l"].sum() / listed.groupby("season")["w"].sum()).to_dict()
    obs = in_scope[in_scope.has_report]
    for lead, stt in tables.items():
        o = stt[(stt.season >= 2023) & stt.has_report]
        res["partA"][f"p_played_by_status_lead{lead}"] = A.play_rates(o).to_dict("records")
        res["partA"][f"p_played_by_season_status_lead{lead}"] = A.play_rates(o, by="season").to_dict("records")
    print("partA", json.dumps(res["partA"]["p_played_by_status_lead0"], default=float), round(time.time() - t0), "s", flush=True)
    # ---- Part B frame
    tg = team_game_table(sch, box, tips)
    tg = tg[tg.game_id.isin(elig) & (tg.season_type == "regular-season") & tg.season.between(2016, 2026)].copy()
    tg["net"] = tg["ortg"] - tg["drtg"]
    tg = rolling_asof(tg, cols=("pace", "ortg", "drtg", "total", "net"))
    tg = rest_features(tg)
    tg["net_dev_l10"] = tg["net_l10"] - tg["net_ytd"]
    sm = tg.groupby(["team_id", "season"])[["net"]].mean().add_prefix("prior_").reset_index().assign(season=lambda d: d.season + 1)
    tg = tg.merge(sm, on=["team_id", "season"], how="left")
    f_rot = L.team_lineup_features(rot, rt, active=played[["game_id", "person_id"]])
    tg = tg.merge(f_rot[["game_id", "team_id", "lineup_net", "lineup_net_act"]], on=["game_id", "team_id"], how="left")
    exp_cols = []
    for lead in (0, 240):
        stt = tables[lead]
        tr_obs = stt[stt.season.isin(TRAIN) & stt.has_report]
        rates = A.rate_map(A.play_rates(tr_obs), min_n=20)
        rates.setdefault(A.UNREPORTED, 1.0)
        res["partA"][f"rates_used_lead{lead}"] = rates
        fx = A.expected_lineup_features(stt, rt, rates)[["game_id", "team_id", "lineup_net_exp", "exp_missing", "cover"]]
        fx.columns = [{"lineup_net_exp": f"lineup_net_exp{lead}", "exp_missing": f"exp_missing{lead}", "cover": f"cover{lead}"}.get(c, c) for c in fx.columns]
        tg = tg.merge(fx, on=["game_id", "team_id"], how="left")
        exp_cols += [f"lineup_net_exp{lead}", f"exp_missing{lead}"]
    feats = ["net_ytd", "net_dev_l10", "rest_days", "b2b", "prior_net", "lineup_net", "lineup_net_act"] + exp_cols
    g = game_frame(tg, feats).reset_index()
    g["base_margin"] = g.h_net_ytd - g.a_net_ytd
    g["net_dev_diff"] = g.h_net_dev_l10 - g.a_net_dev_l10
    g["rest_diff"] = g.h_rest_days.clip(upper=4) - g.a_rest_days.clip(upper=4)
    g["b2b_diff"] = g.h_b2b - g.a_b2b
    g["prior_margin"] = g.h_prior_net - g.a_prior_net
    for c in ("lineup_net", "lineup_net_act", "lineup_net_exp0", "lineup_net_exp240", "exp_missing0", "exp_missing240"):
        g[f"d_{c}"] = g[f"h_{c}"] - g[f"a_{c}"]
    g["d_exp_delta"] = g.d_lineup_net_exp0 - g.d_lineup_net
    g["d_act_delta"] = g.d_lineup_net_act - g.d_lineup_net
    g["d_exp240_delta"] = g.d_lineup_net_exp240 - g.d_lineup_net
    g = g[g.season.isin([2023, 2024, 2025, 2026])]
    gmf = g.dropna(subset=["base_margin", "d_lineup_net_exp0", "d_lineup_net_act"])
    bm = ["base_margin", "net_dev_diff", "rest_diff", "b2b_diff"]
    bmp = bm + ["prior_margin"]
    specs = {
        "margin | rot + exp availability (lead0) | over baseline+prior": (bmp + ["d_lineup_net"], ["d_exp_delta"]),
        "margin | rot + exp availability (lead240) | over baseline+prior": (bmp + ["d_lineup_net"], ["d_exp240_delta"]),
        "margin | rot + act (upper bound) | over baseline+prior": (bmp + ["d_lineup_net"], ["d_act_delta"]),
        "margin | rot | over baseline+prior": (bmp, ["d_lineup_net"]),
        "margin | exp level (lead0) | over baseline+prior": (bmp, ["d_lineup_net_exp0"]),
        "margin | act level (upper bound) | over baseline+prior": (bmp, ["d_lineup_net_act"]),
        "margin | exp missing minutes (lead0) | over baseline+prior": (bmp, ["d_exp_missing0"]),
    }
    for name, (b, e) in specs.items():
        res["partB"][name] = {str(ts): gain(gmf, b, e, "margin", [ts]) for ts in TESTS}
        res["partB"][name]["pooled_2025_26"] = gain(gmf, b, e, "margin", list(TESTS))
        print(name, {k: (round(v["gain"], 3), [round(x, 3) for x in v["gain_ci"]], v["n_test"]) for k, v in res["partB"][name].items()}, flush=True)
    res["partB"]["frame_games"] = int(len(gmf))
    safe_out(out).write_text(json.dumps(res, indent=2, default=float))
    print("done", round(time.time() - t0), "s")


if __name__ == "__main__":
    root = Path(sys.argv[1]) if len(sys.argv) > 1 else REPO / "exp_output" / "NBA_EVENTS"
    out = Path(sys.argv[2]) if len(sys.argv) > 2 else Path(__file__).with_name("results_W93_1.json")
    main(root, out)
