"""W110.2 step 1: game-level candidate factors for the NBA applied path, point-in-time.

geometry   W93.2 build_frame columns (schedule only)                        class venue
officials  shrunk crew deviations, strictly earlier dates (nba_officials)   class officials (crew time UNVERIFIED, GG-1390 -> upper bound)
usage      expected missing usage share + creator-out cross                 class lineup (statuses cut at tip_earliest, rates fit 2023-24)
pam        PAM creator weight / modifier count x rotation x P(play)         class qualitative; HINDSIGHT: every PAM record has recorded_at 2026-05-28
Usage: build_frame.py <NBA_EVENTS root> <PAM records.jsonl> <out parquet, inside 12_EXPLORATORY/>
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "nba_availability"))
sys.path.insert(0, str(HERE.parent / "nba_geometry"))
sys.path.insert(0, str(HERE.parent))
import run_w93_1 as W  # noqa: E402
import run_w93_2 as G  # noqa: E402
from _fence import safe_out  # noqa: E402
from prediction_market_bot.c1_signal_ingestion import nba_availability as A  # noqa: E402
from prediction_market_bot.c1_signal_ingestion import nba_lineups as L  # noqa: E402
from prediction_market_bot.c1_signal_ingestion import nba_officials as O  # noqa: E402
from prediction_market_bot.c1_signal_ingestion.nba_injury_reports import norm_name  # noqa: E402
from prediction_market_bot.c1_signal_ingestion.nba_point_in_time import tip_table  # noqa: E402
from prediction_market_bot.nba_engine import factors_applied as FA  # noqa: E402

TRAIN = (2023, 2024)


def minutes(s):
    def one(v):
        if isinstance(v, str) and ":" in v:
            a, b = v.split(":")[:2]
            return float(a) + float(b) / 60
        try:
            return float(v)
        except Exception:
            return np.nan
    return s.map(one)


def main(root, pam_path, out):
    root = Path(root)
    rd = W.rd
    sch, espn, box, off, pb = rd(root, "schedule"), rd(root, "espn_schedule"), rd(root, "team_box"), rd(root, "officials"), rd(root, "player_box")
    sch["game_id"] = sch["game_id"].astype(str)
    tips = tip_table(sch, espn)
    sid = sch.drop_duplicates("game_id").set_index("game_id")
    home_team = sid["home_team_id"].astype(str).to_dict()
    # --- geometry
    gf, _ = G.build_frame(root)
    gf["game_id"] = gf["game_id"].astype(str)
    geo = gf.set_index("game_id")[[c for c in FA.GROUPS["geometry"] if c in gf.columns]]
    # --- officials
    tb = box.assign(game_id=box.game_id.astype(str))
    q = O.game_quantities(tb)
    poss = (tb.assign(p=tb.field_goals_attempted + 0.44 * tb.free_throws_attempted + tb.turnovers - tb.rebounds_offensive)
            .groupby("game_id")["p"].mean())  # possessions per team-game ~ pace proxy (same for any official; deviations are what matter)
    q["pace"] = poss.reindex(q.index)
    q = q.copy(); q.index = q.index.astype(str)
    q["date"] = pd.to_datetime(tips.reindex(q.index)["tip_earliest"]).dt.tz_convert("America/New_York").dt.tz_localize(None).dt.normalize()
    q = q.dropna(subset=["date"])
    cr = O.official_rates(off.assign(game_id=off.game_id.astype(str))[["game_id", "official_id"]], q)
    ofc = pd.DataFrame({"s_crew_pace": cr["crew_dev_pace"], "s_crew_fta": cr["crew_dev_fta"], "s_crew_fouls": cr["crew_dev_fouls"]})
    ofc.index = ofc.index.astype(str)
    # --- usage / PAM: surrogate player-game table from player_box (sec = minutes x 60)
    pb = pb.assign(game_id=pb.game_id.astype(str), person_id=pb.person_id.astype(str))
    pb["minutes_f"] = minutes(pb["minutes"])
    pb = pb[pb.minutes_f.fillna(0) > 0]
    pg = pb[["game_id", "side", "person_id", "team_id"]].assign(sec=pb.minutes_f * 60.0)
    gm = tips.loc[tips.index.isin(set(pg.game_id)), ["season", "tip_earliest", "tip_latest"]].copy()
    gm["day"] = [t.tz_convert(A.ET).date() for t in gm["tip_earliest"]]
    team_of = pd.concat([pd.DataFrame({"game_id": sid.index, "side": "home", "team_id": sid["home_team_id"].to_numpy()}),
                         pd.DataFrame({"game_id": sid.index, "side": "away", "team_id": sid["away_team_id"].to_numpy()})])
    rot = L.rotation_weights(pg[["game_id", "side", "person_id", "sec"]], team_of, gm)
    rot["person_id"] = rot["person_id"].astype(str)
    names = pb.drop_duplicates("person_id").assign(norm_name=lambda d: (d.first_name.fillna("") + " " + d.family_name.fillna("")).map(norm_name))[["person_id", "norm_name"]]
    inj = W.load_inj()
    played = pg[pg.sec >= A.PLAYED_SEC][["game_id", "person_id"]].assign(played=1)
    stt = A.status_table(rot, names, gm, inj, lead_min=0).merge(played, on=["game_id", "person_id"], how="left")
    stt["played"] = stt["played"].fillna(0).astype(int)
    stt["season"] = stt["game_id"].map(gm["season"])
    tr = stt[stt.season.isin(TRAIN) & stt.has_report]
    rates = A.rate_map(A.play_rates(tr), min_n=20)
    rates.setdefault(A.UNREPORTED, 1.0)
    stt["p_play"] = stt["status"].map(rates).fillna(rates[A.UNREPORTED])
    # as-of usage share (previous 10 team games, same season, strictly earlier)
    u = pb.assign(ue=FA.usage_events(pb.field_goals_attempted.fillna(0), pb.free_throws_attempted.fillna(0), pb.turnovers.fillna(0)))
    u["season"] = u["game_id"].map(gm["season"])
    u["order"] = u["game_id"].map(gm["tip_earliest"].rank(method="first"))
    u = u.dropna(subset=["season", "order"])[["game_id", "team_id", "person_id", "season", "order", "ue"]]
    sh = FA.usage_shares_asof(u)
    for d_ in (sh, stt):
        d_["team_id"] = d_["team_id"].astype(str)
    j = stt.merge(sh, on=["game_id", "team_id", "person_id"], how="left")
    um = FA.usage_missing(j[["game_id", "team_id", "share", "p_play"]])
    usg = FA.home_away_columns(um, home_team, ["usage_missing", "creator_out"])
    # --- PAM (hindsight: ignore recorded_at)
    recs = [json.loads(x) for x in open(pam_path) if x.strip()]
    pam = FA.pam_player_table(recs)
    gdate = {g: pd.Timestamp(d) for g, d in gm["day"].items()}
    pf = FA.pam_flags(rot.assign(p_play=rot["person_id"].map(dict(zip(stt.person_id, stt.p_play))).fillna(1.0))[["game_id", "team_id", "person_id", "w", "p_play"]]
                      .assign(team_id=lambda d: d.team_id.astype(str)), pam, gdate, point_in_time=False)
    pf["team_id"] = pf["team_id"].astype(str)
    pm = FA.home_away_columns(pf, home_team, ["pam_creator", "pam_mod"])
    F = geo.join(ofc, how="outer").join(usg, how="outer").join(pm, how="outer")
    F["season"] = F.index.map(gm["season"])
    F.index.name = "game_id"
    F.to_parquet(safe_out(HERE.parent / out))
    print(len(F), F.drop(columns="season").notna().sum().to_dict(), flush=True)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], sys.argv[3])
