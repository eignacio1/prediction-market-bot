"""EXP-037 / T-608 (MLB): pull MLB team-game results + probable starters from the public Stats API.

Read-only public data, <=1 req/s. Writes one parquet of games (all game types kept, with a game_type
column; training uses regular season 'R' only). Also used with --upcoming to refresh scheduled games.

  PYTHONPATH=src:. python3 scripts/fetch_mlb_game_history.py --first 2015 --last 2026
"""
from __future__ import annotations

import argparse
import sys
import time
from datetime import date
from pathlib import Path

import pandas as pd
import requests

ROOT = Path(__file__).resolve().parent.parent
CACHE = ROOT / "exp_output" / "MLB_GAME" / "cache_w47"
URL = "https://statsapi.mlb.com/api/v1/schedule"


def fetch_range(start: str, end: str, game_types: str) -> list[dict]:
    r = requests.get(URL, params={"sportId": 1, "startDate": start, "endDate": end,
                                  "gameType": game_types, "hydrate": "probablePitcher,team"}, timeout=60)
    r.raise_for_status()
    rows = []
    for d in r.json().get("dates", []):
        for g in d.get("games", []):
            h, a = g["teams"]["home"], g["teams"]["away"]
            rows.append({
                "game_pk": g["gamePk"], "game_type": g["gameType"], "season": int(g["season"]),
                "game_date": g["officialDate"], "start_utc": g["gameDate"],
                "status": g["status"]["abstractGameState"], "double_header": g.get("doubleHeader", "N"),
                "home": h["team"].get("abbreviation"), "away": a["team"].get("abbreviation"),
                "home_score": h.get("score"), "away_score": a.get("score"),
                "home_sp": (h.get("probablePitcher") or {}).get("id"),
                "away_sp": (a.get("probablePitcher") or {}).get("id"),
            })
    return rows


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--first", type=int, default=2015)
    ap.add_argument("--last", type=int, default=date.today().year)
    ap.add_argument("--out", default=str(CACHE / "games.parquet"))
    a = ap.parse_args()
    CACHE.mkdir(parents=True, exist_ok=True)
    rows: list[dict] = []
    for yr in range(a.first, a.last + 1):
        for lo, hi in ((f"{yr}-03-01", f"{yr}-06-30"), (f"{yr}-07-01", f"{yr}-11-30")):
            rows += fetch_range(lo, hi, "R,F,D,L,W")
            time.sleep(1.1)
        print(yr, len(rows), flush=True)
    df = pd.DataFrame(rows).drop_duplicates("game_pk")
    df.to_parquet(a.out)
    print("wrote", a.out, len(df))
    return 0


if __name__ == "__main__":
    sys.exit(main())
