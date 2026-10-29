"""2026-27 NBA team-game table, point-in-time, refreshed daily (W94.1 Part A).

The event store's nba_stats team box file is not published for 2027 (HTTP 404, checked 2026-10-28), but the
nba_stats schedule/results and play-by-play files are, and the ESPN team box is. This module builds the same
shape ``nba_factors.team_game_table`` returns, keyed on nba_stats game and team ids so the engine's ratings
and the pre-2027 history join without a second id space:

    nba_stats schedule (ids, date, teams, final score)
      + ESPN team box (shot/rebound/turnover counts, joined on game date + team abbreviation)
      + nba_stats pbp (periods played -> minutes, so overtime games get the right pace)

A game is returned only if all three agree (score equals the box score, both teams present). Nothing is
imputed. A game's rows exist only once the sources publish it, i.e. after it ends.

Additive: ``NBA_STATS_LAST`` in the event store is left as it was.
Nothing here touches an order, a position, a stake or a ledger row.
"""
from __future__ import annotations

import argparse
import io
import json
import sys
from pathlib import Path
from typing import Optional

import pandas as pd

from prediction_market_bot.c1_signal_ingestion.nba_event_store import RELEASE_BASE
from prediction_market_bot.c1_signal_ingestion.nba_factors import team_game_table
from prediction_market_bot.c1_signal_ingestion.nba_point_in_time import ESPN_TO_NBA_ABBR, tip_table
from prediction_market_bot.c1_signal_ingestion.nfl_event_store import http_get, utc_stamp

SEASON = 2027
DEFAULT_OUT = Path("exp_output/NBA_EVENTS/current")
FILES = {
    "schedule": ("nba_stats_schedules", f"nba_schedule_{SEASON}.parquet"),
    "pbp": ("nba_stats_pbp", f"nba_play_by_play_{SEASON}.parquet"),
    "espn_box": ("espn_nba_team_boxscores", f"team_box_{SEASON}.parquet"),
    "espn_schedule": ("espn_nba_schedules", f"nba_schedule_{SEASON}.parquet"),
}
PLAYED_TYPES = ("regular-season", "playoffs", "nba-cup")
REG_MINUTES, OT_MINUTES = 240.0, 25.0   # five players x 48 min; five-minute overtimes


def fetch(name: str) -> tuple[pd.DataFrame, dict]:
    tag, fname = FILES[name]
    raw, headers = http_get(f"{RELEASE_BASE}/{tag}/{fname}")
    return pd.read_parquet(io.BytesIO(raw)), headers


def game_minutes(pbp: pd.DataFrame) -> pd.Series:
    """Team-minutes played per game id: 240 plus 25 per overtime period."""
    per = pbp.assign(game_id=pbp["game_id"].astype(str)).groupby("game_id")["period"].max()
    return REG_MINUTES + OT_MINUTES * (per.clip(lower=4) - 4)


def build_team_box(schedule: pd.DataFrame, espn_box: pd.DataFrame, pbp: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """Rows in the nba_stats team-box schema (game_id, team_id, side, points, minutes, ...) plus a drop report."""
    s = schedule[schedule["home_pts"].notna() & schedule["season_type"].isin(PLAYED_TYPES)].copy()
    s["game_id"] = s["game_id"].astype(str)
    s["game_date"] = pd.to_datetime(s["game_date"].astype(str)).dt.strftime("%Y-%m-%d")
    e = espn_box.copy()
    e["abbr"] = e["team_abbreviation"].replace(ESPN_TO_NBA_ABBR)
    e["day"] = pd.to_datetime(e["game_date"].astype(str)).dt.strftime("%Y-%m-%d")
    mins = game_minutes(pbp)
    rows, drops = [], {"no_espn_box": 0, "score_mismatch": 0, "no_pbp": 0}
    for side in ("home", "away"):
        t = s.rename(columns={f"{side}_team_id": "team_id", f"{side}_team_abbreviation": "abbr",
                              f"{side}_pts": "points"})[["game_id", "game_date", "team_id", "abbr", "points"]]
        t["side"] = side
        rows.append(t)
    t = pd.concat(rows, ignore_index=True)
    keep = ["day", "abbr", "team_score", "field_goals_attempted", "free_throws_attempted", "offensive_rebounds",
            "turnovers", "total_turnovers", "team_turnovers"]
    m = t.merge(e[keep], how="left", left_on=["game_date", "abbr"], right_on=["day", "abbr"])
    bad_box = m["team_score"].isna()
    bad_score = ~bad_box & (m["team_score"].astype(float) != m["points"].astype(float))
    bad_pbp = ~m["game_id"].isin(mins.index)
    bad_game = set(m.loc[bad_box | bad_score | bad_pbp, "game_id"])
    drops["no_espn_box"] = int(m.loc[bad_box, "game_id"].nunique())
    drops["score_mismatch"] = int(m.loc[bad_score, "game_id"].nunique())
    drops["no_pbp"] = int(m.loc[bad_pbp, "game_id"].nunique())
    m = m[~m["game_id"].isin(bad_game)].copy()
    m["rebounds_offensive"] = m["offensive_rebounds"].astype(float)
    m["minutes"] = m["game_id"].map(mins).astype(int).astype(str)
    m["points"] = m["points"].astype(float)
    out = m[["game_id", "team_id", "side", "points", "minutes", "field_goals_attempted", "free_throws_attempted",
             "rebounds_offensive", "turnovers"]].reset_index(drop=True)
    drops["games_kept"] = int(out["game_id"].nunique())
    return out, drops


def build(schedule: pd.DataFrame, espn_box: pd.DataFrame, pbp: pd.DataFrame,
          espn_schedule: Optional[pd.DataFrame] = None) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    """(team_game_table, tips, drop report). The table carries rolling-ready columns; tips bound each game's tip-off."""
    box, drops = build_team_box(schedule, espn_box, pbp)
    sch = schedule[schedule["game_id"].astype(str).isin(set(box["game_id"]))].copy()
    sch["game_date"] = pd.to_datetime(sch["game_date"].astype(str)).dt.strftime("%Y-%m-%d")
    tips = tip_table(sch, espn_schedule)
    return team_game_table(sch, box, tips), tips, drops


def known_answer_check(tg: pd.DataFrame, espn_box: pd.DataFrame, schedule: pd.DataFrame, pbp: pd.DataFrame,
                       sample: int = 10) -> dict:
    """Compare ``tg`` with the raw ESPN box for an evenly spaced sample of games: game total and pace.

    Pace is recomputed here from the raw counts (possessions = FGA + 0.44 FTA - OREB + TOV, team average,
    scaled to 240 team-minutes) rather than by calling the builder again."""
    e = espn_box.copy()
    e["abbr"] = e["team_abbreviation"].replace(ESPN_TO_NBA_ABBR)
    e["day"] = pd.to_datetime(e["game_date"].astype(str)).dt.strftime("%Y-%m-%d")
    e["poss"] = e["field_goals_attempted"] + 0.44 * e["free_throws_attempted"] - e["offensive_rebounds"] + e["turnovers"]
    sch = schedule.assign(game_id=schedule["game_id"].astype(str)).set_index("game_id")
    mins = game_minutes(pbp)
    games = sorted(tg["game_id"].unique())
    ids = games[:: max(1, len(games) // sample)][:sample]
    worst_total = worst_pace = 0.0
    for gid in ids:
        g = tg[tg["game_id"] == gid]
        sg = sch.loc[gid]
        raw = e[(e["day"] == str(sg["game_date"])[:10])
                & (e["abbr"].isin([sg["home_team_abbreviation"], sg["away_team_abbreviation"]]))]
        worst_total = max(worst_total, abs(float(raw["team_score"].sum()) - float(g["total"].iloc[0])))
        worst_pace = max(worst_pace, abs(float(raw["poss"].mean()) * 240.0 / mins[gid] - float(g["pace"].iloc[0])))
    return {"games_checked": len(ids), "max_abs_total_diff": worst_total, "max_abs_pace_diff": worst_pace}


def refresh(out_dir: Path = DEFAULT_OUT, now: Optional[str] = None) -> dict:
    """Download, rebuild, write ``team_game_2027.parquet`` and ``status.json``; return the status record."""
    as_of = now or utc_stamp()
    sch, h1 = fetch("schedule")
    pbp, h2 = fetch("pbp")
    box, h3 = fetch("espn_box")
    esch, _ = fetch("espn_schedule")
    tg, tips, drops = build(sch, box, pbp, esch)
    out_dir.mkdir(parents=True, exist_ok=True)
    tg.assign(_as_of=as_of).to_parquet(out_dir / f"team_game_{SEASON}.parquet", index=False)
    kat = known_answer_check(tg, box, sch, pbp)
    status = {
        "as_of": as_of, "season": SEASON, "games_ingested": int(tg["game_id"].nunique()),
        "last_game_date": str(tg["game_date"].max()) if len(tg) else None,
        "source_last_modified": {"schedule": h1.get("last-modified"), "pbp": h2.get("last-modified"),
                                 "espn_box": h3.get("last-modified")},
        "dropped": drops, "known_answer": kat,
    }
    (out_dir / "status.json").write_text(json.dumps(status, indent=2) + "\n")
    return status


def main(argv: Optional[list] = None) -> int:
    ap = argparse.ArgumentParser(description="Refresh the 2026-27 NBA team-game table (free sources, point-in-time).")
    ap.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = ap.parse_args(argv)
    print(json.dumps(refresh(args.out), indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
