"""W97.1 Part A: build the frozen v3 artifact the live_v3 runner reads (EXP-044c).

Why off-box: the box store holds schedule / espn_schedule / team_box only. The v3 factors need player-level data (pbp, lineups), so
the rotation weights, player ratings, status -> play rates and the fitted v3 parameters are built here from the free sportsdataverse
store and shipped as one hashed JSON file.

Differences from W96.1's factors_frame.py, all on purpose:
  * ``--lead-min`` (default 60): injury statuses are cut at tip - 60 min, the instant the live arm prices, not at tip (W96.1: lead 0).
  * the 2027 snapshot: rotation = each team's last ROT_GAMES completed 2025-26 games; player ratings = as of the start of 2027 (season-gap
    decay applied, via zero-minute pseudo-games). The store has no 2027 player-level rows, so the snapshot is stale for roster changes.
Usage: build_frozen_v3.py <store root holding raw/> <out dir inside 12_EXPLORATORY/> [--lead-min 60]
Writes <out>/v3_factors_lead<N>.parquet (game-level factors, 2021-2026), <out>/frozen/v3_frozen_2027.json.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "nba_availability"))
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE))
import run_w93_1 as W  # noqa: E402
from _fence import safe_out  # noqa: E402
from prediction_market_bot.c1_signal_ingestion import nba_availability as A  # noqa: E402
from prediction_market_bot.c1_signal_ingestion import nba_lineups as L  # noqa: E402
from prediction_market_bot.c1_signal_ingestion.nba_data_rules import eligible_games, game_quality  # noqa: E402
from prediction_market_bot.c1_signal_ingestion.nba_injury_reports import norm_name  # noqa: E402
from prediction_market_bot.c1_signal_ingestion.nba_point_in_time import tip_table  # noqa: E402

TRAIN_RATES = (2023, 2024)   # play rates fit on these seasons only, as W93.1 / W96.1
SNAP_SEASON = 2027
PSEUDO = "PSEUDO_{}"


def build(root: Path, lead_min: float):
    rd = W.rd
    sch, box, off, espn = rd(root, "schedule"), rd(root, "team_box"), rd(root, "officials"), rd(root, "espn_schedule")
    sch["game_id"] = sch["game_id"].astype(str)
    tips = tip_table(sch, espn)
    q = game_quality(sch, box.assign(game_id=box.game_id.astype(str)), off.assign(game_id=off.game_id.astype(str)), tips)
    elig = eligible_games(q)
    pgs, tgs = [], []
    for s in W.SEASONS:
        st = L.build_stints(rd(root, "pbp", s), rd(root, "lineups", s), rd(root, "schedule", s).assign(game_id=lambda d: d.game_id.astype(str)))
        kept, _ = L.clean_games(st)
        st = st[st.game_id.isin(kept & elig)]
        pgs.append(L.player_game_table(st))
        tgs.append(L.team_game_totals(st))
        print("season", s, flush=True)
    pg, tg_t = pd.concat(pgs, ignore_index=True), pd.concat(tgs, ignore_index=True)
    gm = tips.loc[tips.index.isin(set(pg.game_id)), ["season", "tip_earliest", "tip_latest"]].copy()
    gm["day"] = [t.tz_convert(A.ET).date() for t in gm["tip_earliest"]]
    sid = sch.drop_duplicates("game_id").set_index("game_id")
    team_of = pd.concat([pd.DataFrame({"game_id": sid.index, "side": "home", "team_id": sid["home_team_id"].to_numpy()}),
                         pd.DataFrame({"game_id": sid.index, "side": "away", "team_id": sid["away_team_id"].to_numpy()})])
    return dict(sch=sch, sid=sid, tips=tips, pg=pg, tg_t=tg_t, gm=gm, team_of=team_of, pb=rd(root, "player_box"))


def factor_frame(b: dict, lead_min: float):
    pg, tg_t, gm, sid, team_of = b["pg"], b["tg_t"], b["gm"], b["sid"], b["team_of"]
    rt = L.player_asof_ratings(pg, tg_t, gm)
    rot = L.rotation_weights(pg, team_of, gm)
    pb = b["pb"]
    names = pb.drop_duplicates("person_id").assign(norm_name=lambda d: (d.first_name.fillna("") + " " + d.family_name.fillna("")).map(norm_name))[["person_id", "norm_name"]]
    inj = W.load_inj()
    played = pg[pg.sec >= A.PLAYED_SEC][["game_id", "person_id"]].assign(played=1)
    stt = A.status_table(rot, names, gm, inj, lead_min=lead_min).merge(played, on=["game_id", "person_id"], how="left")
    stt["played"] = stt["played"].fillna(0).astype(int)
    stt["season"] = stt["game_id"].map(gm["season"])
    tr = stt[stt.season.isin(TRAIN_RATES) & stt.has_report]
    rates_df = A.play_rates(tr)
    rates = A.rate_map(rates_df, min_n=20)
    rates.setdefault(A.UNREPORTED, 1.0)
    fx = A.expected_lineup_features(stt, rt, rates)[["game_id", "team_id", "exp_missing", "cover"]]
    f_rot = L.team_lineup_features(rot, rt)[["game_id", "team_id", "lineup_net"]]  # rotation-weighted, no `active` (post-game) argument
    t = fx.merge(f_rot, on=["game_id", "team_id"], how="outer")
    home = sid["home_team_id"].astype(str)
    t["is_home"] = t.team_id.astype(str).to_numpy() == t.game_id.map(home).astype(str).to_numpy()
    h, a = t[t.is_home].set_index("game_id"), t[~t.is_home].set_index("game_id")
    g = pd.DataFrame(index=h.index.union(a.index))
    for c in ("exp_missing", "lineup_net", "cover"):
        g["h_" + c], g["a_" + c] = h[c].reindex(g.index), a[c].reindex(g.index)
    g["d_exp_missing"], g["s_exp_missing"] = g.h_exp_missing - g.a_exp_missing, g.h_exp_missing + g.a_exp_missing
    g["d_lineup_net"], g["s_lineup_net"] = g.h_lineup_net - g.a_lineup_net, g.h_lineup_net + g.a_lineup_net
    g["season"] = g.index.map(gm["season"])
    g.index = g.index.astype(str)
    g.index.name = "game_id"
    return g, rates, rates_df, names


def snapshot_2027(b: dict, names: pd.DataFrame) -> dict:
    """Per team: rotation weights from the last ROT_GAMES completed 2025-26 games, and each rotation player's rating as of 2027 start."""
    pg, tg_t, gm, team_of = b["pg"], b["tg_t"], b["gm"], b["team_of"]
    last = gm.season.max()
    after = gm.tip_latest.max() + pd.Timedelta(days=30)
    teams = sorted(team_of.team_id.unique())
    # 1) rotation: a pseudo-game per team in the last real season, after every real game -> rotation_weights reads the last ROT_GAMES games.
    pg_cols = list(pg.columns)
    add_pg, add_tof, add_gm, add_tg = [], [], {}, []
    any_pid = pg.person_id.iloc[0]
    for tid in teams:
        gid = PSEUDO.format(tid)
        row = {c: 0 for c in pg_cols}
        row.update(game_id=gid, side="home", person_id=any_pid)
        add_pg.append(row)
        add_tof.append({"game_id": gid, "side": "home", "team_id": tid})
        add_gm[gid] = dict(season=last, tip_earliest=after, tip_latest=after + pd.Timedelta(hours=3), day=after.date())
        add_tg.append({"game_id": gid, "side": "home", **{c: 0.0 for c in tg_t.columns if c not in ("game_id", "side")}})
    pg2 = pd.concat([pg, pd.DataFrame(add_pg)], ignore_index=True)
    tof2 = pd.concat([team_of, pd.DataFrame(add_tof)], ignore_index=True)
    gm2 = pd.concat([gm, pd.DataFrame.from_dict(add_gm, orient="index").rename_axis("game_id")])
    rot_all = L.rotation_weights(pg2, tof2, gm2)
    rot = rot_all[rot_all.game_id.str.startswith("PSEUDO_")].copy()
    # 2) ratings as of the start of the next season: zero-minute rows for every rotation player in a pseudo-game of season last+1.
    nxt = last + 1
    add_pg2, add_tg2, add_gm2 = [], [], {}
    for tid, grp in rot.groupby("team_id"):
        gid = "PSEUDOR_{}".format(tid)
        for p in grp.person_id:
            row = {c: 0 for c in pg_cols}
            row.update(game_id=gid, side="home", person_id=p)
            add_pg2.append(row)
        add_tg2.append({"game_id": gid, "side": "home", **{c: 0.0 for c in tg_t.columns if c not in ("game_id", "side")}})
        add_gm2[gid] = dict(season=nxt, tip_earliest=after, tip_latest=after + pd.Timedelta(hours=3), day=after.date())
    pg3 = pd.concat([pg, pd.DataFrame(add_pg2)], ignore_index=True)
    tg3 = pd.concat([tg_t, pd.DataFrame(add_tg2)], ignore_index=True)
    gm3 = pd.concat([gm, pd.DataFrame.from_dict(add_gm2, orient="index").rename_axis("game_id")])
    rt = L.player_asof_ratings(pg3, tg3, gm3)
    rt = rt[rt.game_id.str.startswith("PSEUDOR_")][["person_id", "rel_net"]].drop_duplicates("person_id").set_index("person_id")["rel_net"]
    nm = names.drop_duplicates("person_id").set_index("person_id")["norm_name"]
    out = {}
    for tid, grp in rot.groupby("team_id"):
        out[str(tid)] = [dict(person_id=str(p), norm_name=str(nm.get(p, "")), w=round(float(w), 6),
                              rel_net=round(float(rt.get(p, 0.0)), 6)) for p, w in zip(grp.person_id, grp.w)]
    return out


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("root", type=Path)
    ap.add_argument("out", help="directory under 12_EXPLORATORY/")
    ap.add_argument("--lead-min", type=float, default=60.0)
    a = ap.parse_args(argv)
    b = build(a.root, a.lead_min)
    g, rates, rates_df, names = factor_frame(b, a.lead_min)
    out_dir = HERE.parent / a.out
    g.to_parquet(safe_out(out_dir / "v3_factors_lead{}.parquet".format(int(a.lead_min))))
    print("factor frame", len(g), g.groupby("season")[["d_exp_missing", "d_lineup_net"]].count().to_dict(), flush=True)
    snap = snapshot_2027(b, names)
    tid_abbr = {}
    sch = b["sch"]
    for side in ("home", "away"):
        for _, r in sch.drop_duplicates(f"{side}_team_id").iterrows():
            tid_abbr[str(r[f"{side}_team_id"])] = r[f"{side}_team_abbreviation"]
    safe_out(out_dir / "snapshot_2027.json").write_text(json.dumps(dict(rotation=snap, abbr=tid_abbr, rates=rates,
                                                                 rates_table=rates_df.astype(object).where(rates_df.notna(), None).to_dict("records")), indent=1, default=float))
    print("teams in snapshot", len(snap), "players", sum(len(v) for v in snap.values()), flush=True)


if __name__ == "__main__":
    main()
