"""W111.4 Part B -- build the NBA granularity index (parts 1-4 per entry; part 5 is Part C).

Run: python3 12_EXPLORATORY/granularity_index_nba/build_index.py [--season 2025]
Reads the NBA event store (NBA_EVENTS_ROOT, default the W78.4 data-layer worktree), builds one ``Situation`` row per
question, and writes entries/<name>.json plus INDEX.md. Every entry is point-in-time: rank and stability read only games
played so far. Lineup types are derived from the PRIOR season's player_box (3PA per 36 and steals+blocks per 36, top third
of players with 500+ minutes), because player_box.position is blank on ~56% of rows (GG-1895).
Applies when: refreshing the index for a season, or adding a Situation row.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

import numpy as np
import pandas as pd

import sys
from pathlib import Path as _P
sys.path.insert(0, str(_P(__file__).resolve().parent.parent))
from _fence import safe_out  # noqa: E402
from prediction_market_bot.nba_engine import situation_splits as ss

ROOT = Path(os.environ.get("NBA_EVENTS_ROOT", "/Users/earlignacio/Documents/Claude/Projects/PM-worktrees/"
                                               "20261016T054636Z-w78-4-nba-data-layer/exp_output/NBA_EVENTS/raw"))
OUT = Path(__file__).parent
YEARS = list(range(2017, 2027))
SAMPLE_POINTS = (20, 40, 82)

TOTAL, TEAMTOT, SPREAD, GAME = "KXNBATOTAL", "KXNBATEAMTOTAL", "KXNBASPREAD", "KXNBAGAME"
PTS, THREES = "player_points_prop", "player_threes_prop"


def rd(kind: str, y: int, cols=None) -> pd.DataFrame:
    return pd.read_parquet(ROOT / kind / f"{kind}_{y}.parquet", columns=cols)


def load_games() -> pd.DataFrame:
    gs = []
    for y in YEARS:
        s = rd("schedule", y)
        s = s[s.season_type == "regular-season"]
        gs.append(pd.DataFrame({"game_id": s.game_id, "season": y, "date": pd.to_datetime(s.game_date),
                                "home_team_id": s.home_team_id, "away_team_id": s.away_team_id}))
    return pd.concat(gs, ignore_index=True)


def player_classes(y: int) -> tuple:
    """(shooters, defenders) player-id sets from season y's player_box: top third by 3PA/36 and by (stl+blk)/36."""
    b = rd("player_box", y, ["person_id", "minutes", "three_pointers_attempted", "steals", "blocks"])
    mm = b.minutes.astype(str).str.extract(r"(\d+):(\d+)").astype(float)
    b["min"] = mm[0] + mm[1] / 60.0
    g = b.groupby("person_id").agg(m=("min", "sum"), t=("three_pointers_attempted", "sum"), s=("steals", "sum"), k=("blocks", "sum"))
    g = g[g.m >= 500]
    t3, dfn = g.t / g.m * 36, (g.s + g.k) / g.m * 36
    return set(g.index[t3 >= t3.quantile(2 / 3)]), set(g.index[dfn >= dfn.quantile(2 / 3)])


def add_types(f: pd.DataFrame, poss: pd.DataFrame) -> pd.DataFrame:
    shoot, defs = {}, {}
    for y in sorted(f.season.unique()):
        shoot[y], defs[y] = player_classes(y - 1)
    key = poss.set_index(["game_id", "start_order_index"])
    out_s, out_d = np.zeros(len(f), dtype=int), np.zeros(len(f), dtype=int)
    for y in sorted(f.season.unique()):
        m = (f.season == y).to_numpy()
        sub = f[m]
        out_s[m] = sum(sub[f"off_player_{i}"].isin(shoot[y]).astype(int) for i in range(1, 6)).to_numpy()
        out_d[m] = sum(sub[f"def_player_{i}"].isin(defs[y]).astype(int) for i in range(1, 6)).to_numpy()
    f["off_shoot_n"], f["dfn_def_n"] = out_s, out_d
    return f


def load_possession_frame(games: pd.DataFrame) -> pd.DataFrame:
    fs = []
    for y in YEARS:
        p = rd("possessions", y)
        p = p[p.game_id.isin(games[games.season == y].game_id)]
        b = rd("pbp", y, ["game_id", "order_index", "score_home", "score_away"])
        f = ss.possession_frame(p, b, games[games.season == y])
        f["dur"] = (f.start_seconds_remaining - f.end_seconds_remaining).clip(0, 48)
        f["tovx"] = f.tov.clip(0, 1)
        fs.append(add_types(f, p) if y > YEARS[0] else None)
    return pd.concat([x for x in fs if x is not None], ignore_index=True)


def load_shot_frame(games: pd.DataFrame) -> pd.DataFrame:
    fs = []
    for y in YEARS[1:]:
        s = rd("shots", y)
        s = s[s.game_id.isin(games[games.season == y].game_id)]
        s["season"] = y
        fs.append(ss.shot_frame(s, games[games.season == y]))
    return pd.concat(fs, ignore_index=True)


S = ss.Situation
START = lambda t: (lambda f: f.possession_start_type == t)
SITUATIONS = [
    S("clutch_offence_ppp", "points", ss.is_clutch, "team", "off", True, 100, ((GAME, "moneyline", "late"), (SPREAD, "cover", "late"))),
    S("clutch_defence_ppp", "points", ss.is_clutch, "team", "dfn", False, 100, ((GAME, "moneyline", "late"), (SPREAD, "cover", "late"))),
    S("trailing_big_q4_offence_ppp", "points", lambda f: (f.period >= 4) & (f.margin <= -10), "team", "off", True, 100, ((SPREAD, "cover", "comeback"), (TOTAL, "over", "garbage-time"))),
    S("leading_big_q4_defence_ppp", "points", lambda f: (f.period >= 4) & (f.margin <= -10), "team", "dfn", False, 100, ((SPREAD, "cover", "late-lead"), (TOTAL, "under", "garbage-time"))),
    S("pace_seconds_per_possession", "dur", lambda f: f.dur >= 0, "team", "off", False, 300, ((TOTAL, "over", "pace"),)),
    S("pace_after_made_shot", "dur", START("OffMadeShot"), "team", "off", False, 300, ((TOTAL, "over", "pace"),)),
    S("pace_after_missed_shot", "dur", START("OffMissedShot"), "team", "off", False, 300, ((TOTAL, "over", "pace"),)),
    S("ppp_after_live_ball_turnover", "points", START("OffLiveBallTurnover"), "team", "off", True, 100, ((TOTAL, "over", "transition"), (TEAMTOT, "over", "transition"))),
    S("second_chance_ppp", "points", lambda f: f.is_second_chance.astype(bool), "team", "off", True, 100, ((TEAMTOT, "over", "second-chance"),)),
    S("turnover_rate", "tovx", lambda f: f.dur >= 0, "team", "off", False, 300, ((TOTAL, "under", "turnovers"), (TEAMTOT, "under", "turnovers"))),
    S("turnovers_forced_rate", "tovx", lambda f: f.dur >= 0, "team", "dfn", True, 300, ((TOTAL, "under", "turnovers"), (GAME, "moneyline", "defence"))),
    S("three_attempt_rate", "fg3a", lambda f: f.dur >= 0, "team", "off", True, 300, ((THREES, "over", "volume"), (TOTAL, "over", "variance"))),
    S("three_attempt_rate_allowed", "fg3a", lambda f: f.dur >= 0, "team", "dfn", False, 300, ((THREES, "over", "volume"),)),
    S("free_throw_rate", "fta", lambda f: f.dur >= 0, "team", "off", True, 300, ((PTS, "over", "free-throws"), (TOTAL, "over", "stoppages"))),
    S("first_four_minutes_ppp", "points", lambda f: (f.period == 1) & (f.secs >= 480), "team", "off", True, 100, ((TOTAL, "over", "start"), (TEAMTOT, "over", "start"))),
    S("lineup_onfloor_offence_ppp", "points", lambda f: f.dur >= 0, "lineup", "off", True, 150, ((TEAMTOT, "over", "lineup"), (PTS, "over", "lineup"))),
    S("lineup_onfloor_defence_ppp", "points", lambda f: f.dur >= 0, "lineup", "dfn", False, 150, ((GAME, "moneyline", "lineup"), (SPREAD, "cover", "lineup"))),
    S("shooting_lineup_offence_ppp", "points", lambda f: f.off_shoot_n >= 3, "team", "off", True, 150, ((THREES, "over", "lineup-type"), (TEAMTOT, "over", "lineup-type"))),
    S("defensive_lineup_defence_ppp", "points", lambda f: f.dfn_def_n >= 3, "team", "dfn", False, 150, ((TOTAL, "under", "lineup-type"), (SPREAD, "cover", "lineup-type"))),
    S("shooters_vs_defenders_offence_ppp", "points", lambda f: (f.off_shoot_n >= 3) & (f.dfn_def_n >= 3), "team", "off", True, 100, ((TOTAL, "under", "lineup-matchup"), (THREES, "under", "lineup-matchup"))),
]
ZONE = [
    S("rim_fg_allowed", "make", lambda f: f.zone == "rim", "team", "dfn", False, 200, ((PTS, "under", "rim"), (TOTAL, "under", "rim"))),
    S("corner_three_make_rate", "make", lambda f: f.zone == "corner3", "team", "off", True, 100, ((THREES, "over", "corner"),)),
    S("above_break_three_make_rate", "make", lambda f: f.zone == "above_break3", "team", "off", True, 200, ((THREES, "over", "above-break"),)),
    S("midrange_make_rate", "make", lambda f: f.zone == "midrange", "team", "off", True, 150, ((PTS, "over", "midrange"),)),
]


def jsonable(o):
    if isinstance(o, (np.integer,)):
        return int(o)
    if isinstance(o, (np.floating,)):
        return None if np.isnan(o) else float(o)
    if isinstance(o, float) and o != o:
        return None
    raise TypeError(type(o))


def pick_units(frame, sit, season, games):
    """Best-ranked unit at ``games`` and the strongest opposing-side unit for the cross (team units)."""
    from prediction_market_bot.nfl_engine import granularity_index as gi
    plays, spec = ss.plays_for(frame, sit), ss.spec_for(sit)
    t = gi.game_table(plays, spec)
    me = gi.split(plays, spec, season=season, games=games, table=t)
    me = me[me.n >= sit.min_n]
    if me.empty:
        return None, None
    best = me.sort_values("value", ascending=not sit.higher_is_better).iloc[0].unit
    opp = None
    if sit.unit == "team":
        other = ss.Situation(**{**sit.__dict__, "side": "dfn" if sit.side == "off" else "off"})
        op = gi.split(ss.plays_for(frame, other), ss.spec_for(other), season=season, games=games)
        op = op[op.n >= sit.min_n]
        if len(op):
            opp = op.sort_values("value", ascending=other.higher_is_better).iloc[0].unit
    return best, opp


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--season", type=int, default=2025)
    a = ap.parse_args()
    games = load_games()
    frames = {"poss": load_possession_frame(games), "shot": load_shot_frame(games)}
    (OUT / "entries").mkdir(exist_ok=True)
    rows = []
    for sit, kind in [(s, "poss") for s in SITUATIONS] + [(s, "shot") for s in ZONE]:
        fr = frames[kind]
        best, opp = pick_units(fr, sit, a.season, 82)
        if best is None:
            rows.append({"name": sit.name, "ok": False, "reason": "no unit reaches min_n"})
            continue
        e = {"points": {}}
        for g in SAMPLE_POINTS:
            e["points"][str(g)] = ss.build_entry(fr, sit, best, a.season, g, opp=opp, opp_games=g)
        e.update({"name": sit.name, "season": a.season, "unit_shown": best, "opp_shown": opp, "frame": kind,
                  "metric": sit.metric, "side": sit.side, "unit_kind": sit.unit,
                  "markets": [{"family": f, "line": l, "direction": d} for f, l, d in sit.markets],
                  "application": "pending Part C (filters.py + per-leaf scoring)"})
        safe_out(OUT / "entries" / f"{sit.name}.json").write_text(json.dumps(e, indent=1, default=jsonable))
        p82 = e["points"]["82"]
        rows.append({"name": sit.name, "ok": p82.get("ok", False), "unit": best, "value": p82.get("value"), "rank_history": p82.get("rank_history"),
                     "of_history": p82.get("of_history"), "trait": (p82.get("stability") or {}).get("trait"),
                     "split_half_r": (p82.get("stability") or {}).get("r_spearman_brown"), "markets": len(sit.markets)})
    safe_out(OUT / "index.json").write_text(json.dumps(rows, indent=1, default=jsonable))
    print(json.dumps(rows, indent=1, default=jsonable))


if __name__ == "__main__":
    main()
