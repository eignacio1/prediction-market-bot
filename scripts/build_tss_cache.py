#!/usr/bin/env python3
"""
Build TeamStatsStore cache using ESPN scoreboard API (GG-013 fix).

nba_api stats.nba.com is blocked from both VPS (DigitalOcean) and GitHub Actions
(Azure) IPs by Akamai WAF. ESPN scoreboard API is not blocked from either.

Called by GitHub Actions tss_daily_sync workflow.
Writes team_stats_cache_{GAME_DATE}.json to the working directory.
The workflow SCPs this file to VPS before PIPE-02 fires.

Data: ESPN scoreboard per date, 60-day lookback. Covers L10 for all active teams.
pts_allowed = opponent score per game (mathematically equivalent to pts - plus_minus).
"""
from datetime import datetime, timedelta, timezone
import json
import sys
import time

import requests

GAME_DATE = datetime.now(tz=timezone.utc).strftime("%Y%m%d")
LOOKBACK_DAYS = 60  # L10 for Finals-paced teams needs ~20 days; 60 gives margin
OUT_FILE = f"team_stats_cache_{GAME_DATE}.json"
ESPN_SCOREBOARD = "https://site.api.espn.com/apis/site/v2/sports/basketball/nba/scoreboard"

# ESPN uses shortened abbreviations for some teams; normalize to NBA standard (used everywhere else).
ESPN_TO_NBA: dict[str, str] = {
    "GS": "GSW",
    "NY": "NYK",
    "SA": "SAS",
    "NO": "NOP",
    "UTAH": "UTA",
    "WSH": "WAS",
}


def fetch_scoreboard(date_str: str) -> list[dict]:
    """Return completed game records for one UTC date (YYYYMMDD)."""
    try:
        r = requests.get(ESPN_SCOREBOARD, params={"dates": date_str}, timeout=10)
        if r.status_code != 200:
            return []
        data = r.json()
    except Exception:
        return []

    records = []
    for event in data.get("events", []):
        comp = event.get("competitions", [{}])[0]
        comps = comp.get("competitors", [])
        if len(comps) != 2:
            continue
        if not event.get("status", {}).get("type", {}).get("completed", False):
            continue
        game_date = event.get("date", "")[:10]  # YYYY-MM-DD
        c0, c1 = comps[0], comps[1]
        abbr0 = c0.get("team", {}).get("abbreviation", "")
        abbr1 = c1.get("team", {}).get("abbreviation", "")
        try:
            pts0 = int(c0.get("score") or 0)
            pts1 = int(c1.get("score") or 0)
        except (ValueError, TypeError):
            continue
        if not (abbr0 and abbr1 and pts0 and pts1):
            continue
        abbr0 = ESPN_TO_NBA.get(abbr0.upper(), abbr0.upper())
        abbr1 = ESPN_TO_NBA.get(abbr1.upper(), abbr1.upper())
        records.append({
            "abbr": abbr0, "game_date": game_date,
            "pts": pts0, "pts_allowed": pts1, "plus_minus": pts0 - pts1,
        })
        records.append({
            "abbr": abbr1, "game_date": game_date,
            "pts": pts1, "pts_allowed": pts0, "plus_minus": pts1 - pts0,
        })
    return records


def main() -> None:
    today_utc = datetime.now(tz=timezone.utc)
    raw: dict[str, dict[str, dict]] = {}  # abbr → {game_date → record}

    fetched, nonempty = 0, 0
    for days_back in range(LOOKBACK_DAYS):
        date_str = (today_utc - timedelta(days=days_back)).strftime("%Y%m%d")
        records = fetch_scoreboard(date_str)
        fetched += 1
        if records:
            nonempty += 1
        for rec in records:
            abbr = rec["abbr"]
            gd = rec["game_date"]
            raw.setdefault(abbr, {})[gd] = rec
        time.sleep(0.05)  # gentle rate limit

    print(f"Fetched {fetched} dates, {nonempty} with game data")

    if not raw:
        print("ERROR: no game records found", file=sys.stderr)
        sys.exit(1)

    out: dict[str, list[dict]] = {}
    for abbr, games_by_date in raw.items():
        sorted_games = sorted(games_by_date.values(), key=lambda r: r["game_date"])
        out[abbr] = [
            {
                "game_date": g["game_date"],
                "pts": g["pts"],
                "plus_minus": g["plus_minus"],
                "pts_allowed": g["pts_allowed"],
            }
            for g in sorted_games
        ]

    with open(OUT_FILE, "w") as f:
        json.dump(out, f)

    total_games = sum(len(v) for v in out.values())
    print(f"Written {OUT_FILE}: {len(out)} teams, {total_games} game-records, GAME_DATE={GAME_DATE}")


if __name__ == "__main__":
    main()
