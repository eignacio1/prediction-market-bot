"""W113.2 Part A: committed snapshots the NFL provider reads (no network on the shadow path).

  filter_data/nfl_team_games.csv  -- matchup_cross.build_team_games over pbp 2022..now (one offence row per team-game)
  filter_data/nfl_schedule.csv    -- season, week, gameday, kickoff_utc, home, away, stadium_id, roof, spread_line, total_line
  filter_data/nfl_snapshot_meta.json -- data_through_utc (latest completed game in the pbp) for the PIT check

usage: python3 -E nfl_build_snapshots.py <pbp_dir_old> <pbp_2026.parquet> <games.csv>
Inputs are untrusted downloaded data: read only, never executed.
"""
import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from prediction_market_bot.nfl_engine.matchup_cross import build_team_games  # noqa: E402

OUT = ROOT / "src/prediction_market_bot/decision_trees/filter_data"
COLS = ["season", "season_type", "week", "game_id", "game_date", "posteam", "defteam", "play_type", "epa", "success", "sack", "qb_hit"]


def main(old_dir, new_pbp, games_csv):
    parts = [pd.read_parquet(p, columns=COLS) for p in sorted(Path(old_dir).glob("pbp_202[2-5].parquet"))]
    parts.append(pd.read_parquet(new_pbp, columns=COLS))
    pbp = pd.concat(parts, ignore_index=True)
    tg = build_team_games(pbp)
    gd = pbp.groupby("game_id").game_date.max().rename("game_date")
    tg = tg.merge(gd, on="game_id", how="left")
    tg.to_csv(OUT / "nfl_team_games.csv", index=False)
    through = pd.to_datetime(pbp.game_date.max()) + pd.Timedelta(hours=30)   # end of the last game day (ET evening)
    g = pd.read_csv(games_csv)
    g = g[(g.season >= 2022) & (g.game_type == "REG")].copy()
    ko = pd.to_datetime(g.gameday + " " + g.gametime.fillna("13:00")).dt.tz_localize("America/New_York", ambiguous="NaT", nonexistent="shift_forward")
    g["kickoff_utc"] = ko.dt.tz_convert("UTC").dt.strftime("%Y-%m-%dT%H:%M:%SZ")
    keep = ["season", "week", "gameday", "kickoff_utc", "home_team", "away_team", "stadium_id", "roof", "spread_line", "total_line"]
    g[keep].rename(columns={"home_team": "home", "away_team": "away"}).to_csv(OUT / "nfl_schedule.csv", index=False)
    (OUT / "nfl_snapshot_meta.json").write_text(json.dumps({"data_through_utc": through.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "pbp_last_game_date": str(pbp.game_date.max()), "team_game_rows": int(len(tg)), "schedule_rows": int(len(g))}, indent=1))
    print("team_games", len(tg), "schedule", len(g), "through", through)


if __name__ == "__main__":
    main(*sys.argv[1:4])
