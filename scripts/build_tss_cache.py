#!/usr/bin/env python3
"""
Build TeamStatsStore cache from LeagueGameLog endpoint.

Called by GitHub Actions tss_daily_sync workflow (GG-013 fix).
GitHub's servers are not blocked by Akamai; the VPS DigitalOcean IP is.

Writes team_stats_cache_{GAME_DATE}.json to the working directory.
The workflow SCPs this file to the VPS before PIPE-02 fires.
"""
from datetime import datetime, timezone
import json
import sys

import pandas as pd
from nba_api.stats.endpoints import LeagueGameLog


GAME_DATE = datetime.now(tz=timezone.utc).strftime("%Y%m%d")
SEASON = "2025-26"
OUT_FILE = f"team_stats_cache_{GAME_DATE}.json"


def fetch_league_game_log(season_type: str) -> pd.DataFrame:
    lg = LeagueGameLog(
        season=SEASON,
        season_type_all_star=season_type,
        player_or_team_abbreviation="T",
        sorter="DATE",
        direction="DESC",
    )
    df = lg.get_data_frames()[0]
    df.columns = [c.lower() for c in df.columns]
    return df


def main() -> None:
    data: dict[str, list[dict]] = {}

    for season_type in ["Regular Season", "Playoffs"]:
        print(f"Fetching {season_type}...")
        try:
            df = fetch_league_game_log(season_type)
        except Exception as e:
            print(f"ERROR fetching {season_type}: {e}", file=sys.stderr)
            continue

        if "team_abbreviation" not in df.columns or "plus_minus" not in df.columns:
            print(f"WARNING: unexpected columns: {list(df.columns)}", file=sys.stderr)
            continue

        df["pts"] = pd.to_numeric(df["pts"], errors="coerce")
        df["plus_minus"] = pd.to_numeric(df["plus_minus"], errors="coerce")
        df["pts_allowed"] = df["pts"] - df["plus_minus"]
        df["game_date"] = pd.to_datetime(df["game_date"]).dt.strftime("%Y-%m-%d")

        for abbr, team_df in df.groupby("team_abbreviation"):
            records = (
                team_df[["game_date", "pts", "plus_minus", "pts_allowed"]]
                .to_dict(orient="records")
            )
            if abbr not in data:
                data[abbr] = []
            data[abbr].extend(records)

    if not data:
        print("ERROR: no data fetched — not writing cache", file=sys.stderr)
        sys.exit(1)

    # De-duplicate by game_date per team, keep sorted ascending
    for abbr in data:
        seen: dict[str, dict] = {}
        for rec in sorted(data[abbr], key=lambda r: r["game_date"]):
            seen[rec["game_date"]] = rec
        data[abbr] = list(seen.values())

    with open(OUT_FILE, "w") as f:
        json.dump(data, f)

    total_games = sum(len(v) for v in data.values())
    print(f"Written {OUT_FILE}: {len(data)} teams, {total_games} game-records, GAME_DATE={GAME_DATE}")


if __name__ == "__main__":
    main()
