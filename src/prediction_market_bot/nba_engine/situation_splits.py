"""NBA situation splits -- the granularity index as a generic machine (W111.4 Part A, directive D-06).

A split is (metric, situation filter, unit). One definition yields the five parts of a GRANULARITY_INDEX entry except the
application: the value point-in-time, its rank against every unit-season at the same games-played point, split-half
stability at that sample, the matchup cross (offense side x the opponent's defence side), and how often the situation occurs.
The sport-agnostic rank / stability / cross come from ``nfl_engine.granularity_index``; this module is the NBA possession
layer in front of them. Nothing here is specific to one question: clutch, lineup type, shot zone, pace-by-situation are all
``Situation`` rows (data), and a new one is a new row, not new code.

Input possession frame (one row per possession, built by ``possession_frame``): season, game_id, off, dfn, off_week, dfn_week
(each team's game number in the season), points, margin (offence minus defence at possession start), period, secs (seconds
left in the period), off_lineup / dfn_lineup (sorted five-id strings), plus any derived columns a filter reads.
Point in time: ``games=g`` reads each unit's first g games only; every situation column is known at possession start.
Applies when: asking whether a team/lineup does something unusually well or badly in a stated situation, whether that is a
stable trait at the games played so far, and whether tonight's opponent makes the situation likely and exploitable.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Mapping, Optional, Sequence

import numpy as np
import pandas as pd

from prediction_market_bot.nfl_engine import granularity_index as gi

CLUTCH_SECS = 300.0     # last five minutes of the fourth quarter or overtime
CLUTCH_MARGIN = 5.0     # within five points


@dataclass(frozen=True)
class Situation:
    """One split definition. ``where`` maps the possession frame to a boolean mask (the situation filter); ``metric`` is a
    column of the frame (0/1 or numeric, per possession); ``unit`` is team or lineup; ``side`` is which side of the ball the
    unit is on. ``tag``/``markets`` is the market map (family, line, direction), data not code."""
    name: str
    metric: str
    where: Callable[[pd.DataFrame], pd.Series]
    unit: str = "team"                  # "team" | "lineup"
    side: str = "off"                   # "off" | "dfn"
    higher_is_better: bool = True       # better FOR THE UNIT on its side (a defence wants a low points-allowed value)
    min_n: int = 100                    # possessions below which an entry is not ranked
    markets: tuple = ()                 # ((family, line, direction), ...)


def is_clutch(f: pd.DataFrame) -> pd.Series:
    return (f.period >= 4) & (f.secs <= CLUTCH_SECS) & (f.margin.abs() <= CLUTCH_MARGIN)


def shot_zone(distance: float, value: int, x: float) -> str:
    """rim <= 4 ft; paint <= 8 ft; mid-range (two, beyond 8 ft); corner three (|x| >= 220 tenths of a foot, i.e. the 22 ft
    line); above-the-break three. Legacy coordinates: x lateral, tenths of a foot from the basket."""
    if value == 3:
        return "corner3" if abs(x) >= 220 else "above_break3"
    if distance <= 4:
        return "rim"
    return "paint" if distance <= 8 else "midrange"


def possession_frame(poss: pd.DataFrame, scores: pd.DataFrame, games: pd.DataFrame) -> pd.DataFrame:
    """Join possessions to the score at their start (pbp ``score_home/score_away`` at ``start_order_index``) and to each
    team's game number. ``games``: game_id, season, date, home_team_id, away_team_id. Columns out are the module contract."""
    p = poss[poss.count_as_possession].copy()
    s = scores[["game_id", "order_index", "score_home", "score_away"]].copy()
    for c in ("score_home", "score_away"):
        s[c] = pd.to_numeric(s[c].replace("", np.nan), errors="coerce")
    s = s.sort_values(["game_id", "order_index"], kind="stable")
    # pbp fills the score only on scoring events; the score at a possession's start is the latest one at or before it.
    s[["score_home", "score_away"]] = s.groupby("game_id")[["score_home", "score_away"]].ffill().fillna(0)
    s = s.rename(columns={"order_index": "start_order_index"})
    p = p.merge(s, on=["game_id", "start_order_index"], how="inner")
    g = games[["game_id", "date", "home_team_id", "away_team_id"]]
    p = p.merge(g, on="game_id", how="inner")
    home_off = p.offense_team_id == p.home_team_id
    p["margin"] = np.where(home_off, p.score_home - p.score_away, p.score_away - p.score_home)
    p["secs"] = p.start_seconds_remaining
    p["off"] = p.offense_team_id
    p["dfn"] = p.defense_team_id
    long = pd.concat([games.assign(team=games.home_team_id), games.assign(team=games.away_team_id)])
    long = long.sort_values(["season", "team", "date", "game_id"], kind="stable")
    long["week"] = long.groupby(["season", "team"]).cumcount() + 1
    wk = long.set_index(["game_id", "team"]).week
    p["off_week"] = wk.reindex(list(zip(p.game_id, p.off))).to_numpy()
    p["dfn_week"] = wk.reindex(list(zip(p.game_id, p.dfn))).to_numpy()
    for side, pre in (("off", "off_player_"), ("dfn", "def_player_")):
        cols = [f"{pre}{i}" for i in range(1, 6)]
        p[f"{side}_lineup"] = p[cols].astype("Int64").astype(str).agg(lambda r: "-".join(sorted(r)), axis=1) \
            if len(p) else pd.Series(dtype=str)
    p["season"] = p["season"].astype(int)
    return p.drop(columns=["home_team_id", "away_team_id"])


def plays_for(frame: pd.DataFrame, sit: Situation) -> pd.DataFrame:
    """Reshape the situation's possessions into the generic machine's input: season, week, game_id, unit, bucket, metric.
    Bucket is the constant "in" (the situation); possessions outside it are dropped, so the unit's value is its rate INSIDE."""
    m = sit.where(frame)
    d = frame[m.fillna(False).to_numpy()]
    unit = d[f"{sit.side}_lineup"] if sit.unit == "lineup" else d[sit.side]
    return pd.DataFrame({"season": d.season.to_numpy(), "week": d[f"{sit.side}_week"].to_numpy(),
                         "game_id": d.game_id.to_numpy(), "unit": unit.to_numpy(), "bucket": "in",
                         "metric": d[sit.metric].astype(float).to_numpy()})


def spec_for(sit: Situation) -> gi.SplitSpec:
    return gi.SplitSpec(unit="unit", by="bucket", metric="metric", higher_is_better=sit.higher_is_better, min_n=sit.min_n)


def frequency(frame: pd.DataFrame, sit: Situation, unit, season: int, games: int) -> dict:
    """How often the situation occurs for ``unit`` through ``games`` games: own share of possessions, and the league share."""
    wk, col = f"{sit.side}_week", (f"{sit.side}_lineup" if sit.unit == "lineup" else sit.side)
    d = frame[(frame.season == season) & (frame[wk] <= games)]
    m = sit.where(d).fillna(False)
    mine = d[col] == unit
    own = float(m[mine].mean()) if mine.any() else float("nan")
    return {"own_share": own, "league_share": float(m.mean()) if len(d) else float("nan"),
            "own_possessions": int(mine.sum()), "own_in_situation": int(m[mine].sum())}


def build_entry(frame: pd.DataFrame, sit: Situation, unit, season: int, games: int,
                opp=None, opp_games: Optional[int] = None) -> dict:
    """One index entry (parts 1-4) for ``unit`` through ``games`` games. ``opp``: the opposing team, for the matchup cross
    -- the unit's own value in the situation against what ``opp`` yields at the same point (team units only)."""
    plays = plays_for(frame, sit)
    spec = spec_for(sit)
    t = gi.game_table(plays, spec)
    r = gi.rank(plays, spec, unit, "in", season, games, table=t)
    base = {"name": sit.name, "metric": sit.metric, "unit_kind": sit.unit, "side": sit.side, "unit": unit,
            "markets": [{"family": f, "line": l, "direction": d} for f, l, d in sit.markets]}
    if not r["ok"]:
        return {**base, "ok": False, "reason": r["reason"]}
    st = gi.stability(plays, spec, "in", games, table=t)
    e = {**base, **r, "stability": st, "frequency": frequency(frame, sit, unit, season, games)}
    if opp is not None and sit.unit == "team":
        other = Situation(**{**sit.__dict__, "side": "dfn" if sit.side == "off" else "off"})
        op = plays_for(frame, other)
        ot = gi.game_table(op, spec_for(other))
        og = opp_games if opp_games is not None else games
        o = gi.split(op, spec_for(other), season=season, games=og, table=ot)
        o = o[o.unit == opp]
        me = gi.split(plays, spec, season=season, games=games, table=t)
        me = me[me.unit == unit]
        lg = float(plays[plays.season == season].metric.mean())
        k = gi.estimate_k(gi.split(plays, spec, season=season, games=games, table=t))
        if len(o) and len(me):
            res = gi.cross({"in": (float(me.n.iloc[0]), float(me.s.iloc[0]))}, {"in": (float(o.n.iloc[0]), float(o.s.iloc[0]))},
                           {"in": lg}, {"in": 1.0}, {"in": k})
            e["cross"] = {"opp": opp, "expected": res.expected, "league": lg, "delta_vs_league": res.expected - lg,
                          "opp_value": float(o.value.iloc[0]), "opp_n": int(o.n.iloc[0])}
    return e


def filter_entries(entries: Sequence[Mapping], tail: float = 0.10, min_n: int = 100, require_trait: bool = True,
                   mismatch_min: Optional[float] = None) -> list:
    """Extremes and mismatches pass; the median fails loudly. Reads ``cross.delta_vs_league`` as the mismatch."""
    es = [{**e, "cross_delta": (e.get("cross") or {}).get("delta_vs_league", 0.0)} for e in entries]
    return gi.filter_entries(es, tail=tail, min_n=min_n, require_trait=require_trait, mismatch_min=mismatch_min)
