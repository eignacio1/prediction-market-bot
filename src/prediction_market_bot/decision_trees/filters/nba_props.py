"""NBA player-prop splits (W121.2, EXP-NBAPROPS-001; PREREG 12_EXPLORATORY/nba_props_splits/PREREG.md).

Four layer-2 splits tag a prop row with categorical leaves before routing it to an arm:
  P1 ``minutes_trend@player`` -- last-10 vs season-to-date minutes per game, from games strictly BEFORE the row's game date.
  P2 ``zone_defence@player``  -- opponent's allowed FG% in the shot zones the stat uses (2025-26 profile); points and threes only.
  P3 ``pace@total``           -- both teams' 2025-26 pace percentile (same leaf as nba_depth S1).
  P4 ``rest@player``          -- the player's team days of rest (back-to-back / normal / rested) from its previous game date.
Point-in-time: profile values are PRIOR COMPLETED season only (``assert_prior_season``); minutes and rest use only games dated
before the row's game date (a prior date on or after it raises ``PITViolation``). Unjoined inputs give ``unknown``, never scored.
Applies when: tagging an NBA player-prop row with leaves before routing. Interface: ``prop_filters(...)`` -> {filter_name: leaf}.
"""
from __future__ import annotations

from datetime import date
from typing import Optional, Sequence

from prediction_market_bot.decision_trees.filters.nba_depth import (
    PITViolation, ZONES, _pct_rank, _team_pcts, _tercile, assert_prior_season)

SPLIT_NAMES = ("minutes_trend@player", "zone_defence@player", "pace@total", "rest@player")
TREND_BAND = 0.10
MIN_PRIOR_GAMES = 5
THREE_ZONES = ("corner 3", "above the break 3")


def minutes_trend(prior_minutes: Sequence[float]) -> str:
    """``prior_minutes`` = minutes of games dated before the row's game, oldest first (caller filters by date)."""
    m = [x for x in prior_minutes if x is not None]
    if len(m) < MIN_PRIOR_GAMES:
        return "unknown"
    season = sum(m) / len(m)
    last = m[-10:]
    r = (sum(last) / len(last)) / season - 1.0 if season > 0 else 0.0
    return "up" if r >= TREND_BAND else "down" if r <= -TREND_BAND else "flat"


def rest_leaf(prev_game: Optional[date], game_day: date) -> str:
    if prev_game is None:
        return "unknown"
    if prev_game >= game_day:
        raise PITViolation(f"previous game {prev_game} is not before the row's game day {game_day}")
    d = (game_day - prev_game).days
    return "b2b" if d <= 1 else "rested" if d >= 3 else "normal"


def _fg(v):
    return v / 100.0 if v is not None and v > 1.0 else v


def zone_leaf(prof: dict, team: str, opp: str, stat: str) -> str:
    """soft / mid / tough: opponent's allowed FG% in the stat's zones, weighted by ``team``'s zone mix, ranked among all 30 defences."""
    if stat not in ("points", "threes"):
        return "unknown"
    T = prof["teams"]
    share = (T.get(team) or {}).get("zone_off_share")
    zones = ZONES if stat == "points" else THREE_ZONES
    if not share or any(z not in share for z in zones):
        return "unknown"
    w = {z: share[z] for z in zones}
    tot = sum(w.values())
    if tot <= 0:
        return "unknown"

    def score(d):
        fg = (d or {}).get("zone_def_fg")
        if not fg or any(fg.get(z) is None for z in zones):
            return None
        return sum(w[z] * _fg(fg[z]) for z in zones) / tot

    vals = {ab: score(d) for ab, d in T.items()}
    vals = {k: v for k, v in vals.items() if v is not None}
    if opp not in vals:
        return "unknown"
    p = _pct_rank(list(vals.values()), vals[opp])
    return "soft" if p > 2 / 3 else "tough" if p < 1 / 3 else "mid"


def prop_filters(*, prof: dict, row_season: int, team: str, opp: str, home: str, away: str, stat: str,
                 prior_minutes: Sequence[float], prev_game: Optional[date], game_day: date) -> dict:
    assert_prior_season(prof["season"], row_season)
    pace = _team_pcts(prof, "pace")
    return {
        "minutes_trend@player": minutes_trend(prior_minutes),
        "zone_defence@player": zone_leaf(prof, team, opp, stat),
        "pace@total": _tercile(None if home not in pace or away not in pace else (pace[home] + pace[away]) / 2),
        "rest@player": rest_leaf(prev_game, game_day),
    }


def _norm(s: str) -> str:
    return "".join(c for c in s.upper() if c.isalpha())


def make_props_supply(games: dict, player_rows: dict, prof: dict):
    """W121.2: ``props_for_row(row) -> {filter_name: leaf} | None`` for the live prop shadow run.

    games / player_rows are the forecaster's stores (parse_box output: games[gid] = {date, home, away, ...},
    player_rows[(team, name)] = [(date_str, {"min": ..})]). Only games dated STRICTLY BEFORE the row's game date feed
    minutes and rest. Never raises: any failure is None so the row is logged without prop leaves."""
    from prediction_market_bot.decision_trees.filter_supply import nba_season_of
    from prediction_market_bot.pregame_shadow.nba_engine_props_forecaster import parse_market_ticker

    def props_for_row(row: dict) -> Optional[dict]:
        try:
            p = parse_market_ticker(str(row.get("market_ticker", "")))
            if p is None:
                return None
            day = date.fromisoformat(p["game_date"])
            team, opp = p["team"], (p["home"] if p["team"] == p["away"] else p["away"])
            ds = day.isoformat()
            tdates = [date.fromisoformat(g["date"]) for g in games.values()
                      if g["date"] < ds and team in (g["home"], g["away"])]
            cand = [rows for (tm, name), rows in player_rows.items()
                    if tm == team and _norm(name).startswith(p["initial"].upper()) and _norm(name).endswith(_norm(p["surname"]))]
            prior = [r["min"] for d, r in sorted(cand[0], key=lambda x: x[0]) if d < ds] if len(cand) == 1 else []
            return prop_filters(prof=prof, row_season=nba_season_of(row["ts_utc"]), team=team, opp=opp, home=p["home"],
                                away=p["away"], stat=p["stat"], prior_minutes=prior,
                                prev_game=max(tdates) if tdates else None, game_day=day)
        except Exception:  # noqa: BLE001 - prop leaves never block a shadow row
            return None
    return props_for_row
