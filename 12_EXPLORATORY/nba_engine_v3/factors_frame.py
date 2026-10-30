"""W96.1 Part B step 1: game-level v3 candidate factors, point-in-time, from the NBA event store + injury-report history.

Factors (all known before tip; statuses cut at tip_earliest, lead 0; rates fit on seasons 2023-2024 only, as in W93.1):
  d_exp_missing / s_exp_missing  expected missing rotation minutes, home-away / home+away (93.1's one surviving availability lead)
  d_lineup_net / s_lineup_net    rotation-weighted prior-game player ratings (92.3 lineups), home-away / home+away
Officials: NOT built here — the crew is post_game in the archive with no assignment timestamp (GG-1390); a factor not known
before the price is an upper bound, not a pricing input.
Usage: factors_frame.py <NBA_EVENTS root> <out parquet, inside 12_EXPLORATORY/>
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "nba_availability"))
sys.path.insert(0, str(HERE.parent))
import run_w93_1 as W  # noqa: E402  (reuses its loaders; not edited)
from _fence import safe_out  # noqa: E402
from prediction_market_bot.c1_signal_ingestion import nba_availability as A  # noqa: E402
from prediction_market_bot.c1_signal_ingestion import nba_lineups as L  # noqa: E402
from prediction_market_bot.c1_signal_ingestion.nba_data_rules import eligible_games, game_quality  # noqa: E402
from prediction_market_bot.c1_signal_ingestion.nba_injury_reports import norm_name  # noqa: E402
from prediction_market_bot.c1_signal_ingestion.nba_point_in_time import tip_table  # noqa: E402

TRAIN = (2023, 2024)


def main(root: Path, out: Path):
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
    rt = L.player_asof_ratings(pg, tg_t, gm)
    sid = sch.drop_duplicates("game_id").set_index("game_id")
    team_of = pd.concat([pd.DataFrame({"game_id": sid.index, "side": "home", "team_id": sid["home_team_id"].to_numpy()}),
                         pd.DataFrame({"game_id": sid.index, "side": "away", "team_id": sid["away_team_id"].to_numpy()})])
    rot = L.rotation_weights(pg, team_of, gm)
    pb = rd(root, "player_box")
    names = pb.drop_duplicates("person_id").assign(norm_name=lambda d: (d.first_name.fillna("") + " " + d.family_name.fillna("")).map(norm_name))[["person_id", "norm_name"]]
    inj = W.load_inj()
    played = pg[pg.sec >= A.PLAYED_SEC][["game_id", "person_id"]].assign(played=1)
    stt = A.status_table(rot, names, gm, inj, lead_min=0).merge(played, on=["game_id", "person_id"], how="left")
    stt["played"] = stt["played"].fillna(0).astype(int)
    stt["season"] = stt["game_id"].map(gm["season"])
    tr = stt[stt.season.isin(TRAIN) & stt.has_report]
    rates = A.rate_map(A.play_rates(tr), min_n=20)
    rates.setdefault(A.UNREPORTED, 1.0)
    fx = A.expected_lineup_features(stt, rt, rates)[["game_id", "team_id", "exp_missing", "cover"]]
    f_rot = L.team_lineup_features(rot, rt, active=played[["game_id", "person_id"]])[["game_id", "team_id", "lineup_net"]]
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
    g.to_parquet(safe_out(HERE.parent / out))
    print(len(g), g.groupby("season")[["d_exp_missing", "d_lineup_net"]].count().to_dict(), flush=True)


if __name__ == "__main__":
    main(Path(sys.argv[1]), sys.argv[2])
