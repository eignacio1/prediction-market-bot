"""W113.4 Part B: grade NBA archive table families by recompute from the bot's event store.

Usage: python3 grade_nba.py <archive_checkout> <archive_sha>   (NBA_EVENTS_ROOT env for the store)
Writes grades_nba.json next to this file.
"""
import json, os, re, sys
from pathlib import Path
import numpy as np, pandas as pd
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
from prediction_market_bot.archive_intake import Archive

R = Path(os.environ.get("NBA_EVENTS_ROOT", "exp_output/NBA_EVENTS/raw"))
BINS = [("less than 5 ft", 0, 5), ("5-9 ft", 5, 10), ("10-14 ft", 10, 15), ("15-19 ft", 15, 20), ("20-24 ft", 20, 25), ("25-29 ft", 25, 30)]
TOL = {"fgm": 0.15, "fga": 0.15, "pct": 1.0}   # per-game counts: rounding .05 + 0.10 slack; FG%: 1.0 pt


def reg_games():
    sc = pd.read_parquet(R / "schedule/schedule_2026.parquet")
    sc = sc[sc.season_type.str.lower().str.contains("regular")]
    return sc


def grade_opp_shooting(arc, loc="all"):
    sc = reg_games()
    shots = pd.read_parquet(R / "shots/shots_2026.parquet")
    shots = shots[shots.game_id.isin(sc.game_id)]
    home = sc.set_index("game_id")[["home_team_id", "away_team_id"]]
    # NBA.com bins use exact distance from court x/y (tenths of ft), not the store's rounded shot_distance
    shots["dist"] = np.hypot(shots.x_legacy, shots.y_legacy) / 10
    shots = shots.join(home, on="game_id")
    shots["opp_id"] = np.where(shots.team_id == shots.home_team_id, shots.away_team_id, shots.home_team_id)
    names = pd.concat([sc[["home_team_id", "home_team_name"]].set_axis(["id", "name"], axis=1),
                       sc[["away_team_id", "away_team_name"]].set_axis(["id", "name"], axis=1)]).drop_duplicates().set_index("id").name
    if loc == "home":   # defending team is the home team
        shots = shots[shots.opp_id == shots.home_team_id]
        games = sc.groupby("home_team_id").size()
    elif loc == "road":
        shots = shots[shots.opp_id == shots.away_team_id]
        games = sc.groupby("away_team_id").size()
    else:
        games = pd.concat([sc[["game_id", "home_team_id"]].rename(columns={"home_team_id": "id"}),
                           sc[["game_id", "away_team_id"]].rename(columns={"away_team_id": "id"})]).groupby("id").size()
    arch = arc.split_frame("nba", family="NBA.com Teams Opponent Shooting", season=2025)
    arch = arch[arch.split == loc]
    out = []
    for lab, lo, hi in BINS:
        sub = shots[(shots.dist >= lo) & (shots.dist < hi)]
        g = sub.groupby("opp_id")
        fga = g.size() / games
        fgm = sub.assign(m=sub.shot_result == "Made").groupby("opp_id").m.sum() / games
        pct = 100 * fgm / fga
        for kind, ser in (("fgm", fgm), ("fga", fga), ("pct", pct)):
            word = {"fgm": "field goals made", "fga": "field goals attempted", "pct": "field goal percentage"}[kind]
            a = arch[arch.metric.str.startswith(f"opponent {word}, {lab},")]
            for _, r in a.iterrows():
                tid = names[names == r.subject].index
                if len(tid) == 0 or tid[0] not in ser.index:
                    continue
                out.append(dict(kind=kind, bin=lab, team=r.subject, archive=r.value_num, recomputed=round(float(ser[tid[0]]), 3)))
    d = pd.DataFrame(out)
    d["diff"] = (d.archive - d.recomputed).abs()
    d["ok"] = d.apply(lambda r: r["diff"] <= TOL[r.kind], axis=1)
    return d, int(games.median()), len(arch)


TRAD = {  # archive metric prefix -> (team_box column, scale); pct rows are x100
    "points per game": "points", "field goals made per game": "field_goals_made", "field goals attempted per game": "field_goals_attempted",
    "three-pointers made per game": "three_pointers_made", "three-pointers attempted per game": "three_pointers_attempted",
    "free throws made per game": "free_throws_made", "free throws attempted per game": "free_throws_attempted",
    "offensive rebounds per game": "rebounds_offensive", "defensive rebounds per game": "rebounds_defensive", "rebounds per game": "rebounds_total",
    "assists per game": "assists", "turnovers per game": "turnovers", "steals per game": "steals", "blocks per game": "blocks",
    "personal fouls per game": "fouls_personal", "plus/minus per game": "plus_minus_points",
}


def grade_traditional(arc, loc):
    """Teams Traditional, Location=Home|Road, recomputed from team_box. Tolerance 0.06 (published to 0.1 dp)."""
    sc = reg_games()
    tb = pd.read_parquet(R / "team_box/team_box_2026.parquet")
    tb = tb[tb.game_id.isin(sc.game_id)]
    opp = tb[["game_id", "side", "blocks", "fouls_personal"]].assign(side=lambda d: d.side.map({"home": "away", "away": "home"}))
    tb = tb.merge(opp, on=["game_id", "side"], suffixes=("", "_opp"))
    sub = tb[tb.side == ("home" if loc == "Home" else "away")]
    name = (tb.team_city + " " + tb.team_name).str.replace("LA Clippers", "LA Clippers")
    sub = sub.assign(team=(sub.team_city + " " + sub.team_name))
    g = sub.groupby("team")
    rec = {k: g[c].mean() for k, c in TRAD.items()}
    rec["blocks against per game"] = g["blocks_opp"].mean()
    rec["personal fouls drawn per game"] = g["fouls_personal_opp"].mean()
    rec["field goal percentage"] = 100 * g.field_goals_made.sum() / g.field_goals_attempted.sum()
    rec["three-point percentage"] = 100 * g.three_pointers_made.sum() / g.three_pointers_attempted.sum()
    rec["free throw percentage"] = 100 * g.free_throws_made.sum() / g.free_throws_attempted.sum()
    rec["home games played" if loc == "Home" else "road games played"] = g.size()
    df = arc.split_frame("nba", season=2025, contains=f"Teams Traditional table (2025-26, Location={loc})")
    out = []
    for _, r in df.iterrows():
        k = r.metric.split(" (NBA.com")[0]
        if k in rec:
            team = r.subject.replace("Los Angeles Clippers", "LA Clippers")
            if team in rec[k].index:
                out.append(dict(table=f"traditional_{loc.lower()}", metric=k, team=r.subject, archive=r.value_num, recomputed=round(float(rec[k][team]), 3)))
    d = pd.DataFrame(out)
    d["diff"] = (d.archive - d.recomputed).abs()
    d["ok"] = d["diff"] <= 0.06
    return d


if __name__ == "__main__":
    arc = Archive(sys.argv[1], sys.argv[2])
    for _loc in ("all", "home", "road"):
      d, gp, n = grade_opp_shooting(arc, _loc)
      print("OPP SHOOTING", _loc, "n", len(d), "within", round(d.ok.mean(), 3), "max diff", d["diff"].max())
      d.to_csv(Path(__file__).with_name(f"opp_shooting_{_loc}_recompute.csv"), index=False)
    d, gp, n = grade_opp_shooting(arc, "all")
    summ = d.groupby(["kind"]).agg(n=("ok", "size"), within=("ok", "mean"), mad=("diff", "mean"), max=("diff", "max")).round(3)
    print("games/team (regular season, store):", gp, "archive rows:", n)
    print(summ)
    print(d.groupby("bin").agg(within=("ok", "mean"), mad=("diff", "mean")).round(3))
    d.to_csv(Path(__file__).with_name("opp_shooting_recompute.csv"), index=False)
    for loc in ("Home", "Road"):
        td = grade_traditional(arc, loc)
        print(loc, "n", len(td), "within", round(td.ok.mean(), 3), "max diff", td["diff"].max())
        print(td[~td.ok].groupby("metric").agg(n=("ok", "size"), mx=("diff", "max")))
        td.to_csv(Path(__file__).with_name(f"traditional_{loc.lower()}_recompute.csv"), index=False)
