"""
T-186 Step 1 — Pull Playoff TeamGameLog + Build TeamStatsStore Cache
======================================================================

Script ID:    T-186-PULL
Purpose:      Pull 2024-25 and 2025-26 playoff TeamGameLog for all 30 NBA teams
              via nba_api; build a TeamStatsStore; serialize to JSON cache.
Output:       data/playoff_teamgamelog_cache.json
Usage:        PYTHONPATH=src .venv/bin/python3 scripts/pull_playoff_teamgamelog.py

Cache structure: one key per team abbreviation ("LAL", "BOS", ...) holding
all playoff games from BOTH seasons combined in chronological order. This
lets get_opp_def_rating(opp_abbr, as_of_date) correctly look up prior
playoff defensive context across both the 2024-25 and 2025-26 seasons.

pts_allowed derivation:
  nba_api TeamGameLog does NOT return PLUS_MINUS for any season type.
  Instead: after all team logs are collected, we build a lookup
  (game_date, team_abbr) → pts_scored, then for each team's game we
  parse the opponent from the MATCHUP column ("BOS vs. PHI" / "BOS @ PHI")
  and set plus_minus = pts - opponent_pts so that add_team_log computes
  pts_allowed = pts - plus_minus = opponent_pts.
  Games whose opponent is not in the cache get pts_allowed = NaN.

Throttling: 0.65s between each API call (30 teams × 2 seasons = 60 calls,
~40-60 seconds total). Same rate as C1 ingestion (ingestion.py).

Security:
  - No hardcoded secrets.
  - BOT_C4_ACTIVE must NOT be set.
  - No venue API calls.
"""

from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

_SRC_ROOT = Path(__file__).parent.parent / "src"
if str(_SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(_SRC_ROOT))

from prediction_market_bot.c1_signal_ingestion.ingestion import NBAIngestionClient
from prediction_market_bot.c1_signal_ingestion.team_stats_store import TeamStatsStore
from prediction_market_bot.c6_audit_logger.audit_logger import AuditLogger

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

SEASONS = ["2024-25", "2025-26"]
SEASON_TYPE = "Playoffs"
OUTPUT_PATH = Path("data/playoff_teamgamelog_cache.json")
THROTTLE_S = 0.65  # seconds between API calls

# ---------------------------------------------------------------------------


def _parse_opponent_abbr(matchup: str, my_abbr: str) -> str | None:
    """Extract opponent abbreviation from matchup string.

    Examples: "BOS vs. PHI" → "PHI", "BOS @ PHI" → "PHI"
    The queried team is always first; opponent is always last word.
    """
    if not isinstance(matchup, str):
        return None
    parts = matchup.strip().split()
    if len(parts) >= 3:
        return parts[-1].upper()
    return None


def _fill_pts_allowed_via_crossref(
    logs_by_abbr: dict[str, pd.DataFrame],
) -> dict[str, pd.DataFrame]:
    """Fill pts_allowed for each team's log by cross-referencing opponent PTS.

    nba_api TeamGameLog omits PLUS_MINUS, so pts_allowed cannot be computed
    directly. This function builds a (game_date, abbr) → pts lookup from all
    collected logs, then derives plus_minus = pts - opponent_pts so that
    TeamStatsStore.add_team_log() computes pts_allowed = opponent_pts.

    Games whose opponent is not in the cache are left with NaN plus_minus.
    """
    # Build pts lookup: (game_date, abbr) → pts
    pts_lookup: dict[tuple[str, str], float] = {}
    for abbr, df in logs_by_abbr.items():
        for _, row in df.iterrows():
            gdate = str(row.get("game_date", ""))[:10]
            pts = pd.to_numeric(row.get("pts"), errors="coerce")
            if gdate and not np.isnan(pts):
                pts_lookup[(gdate, abbr.upper())] = float(pts)

    filled: dict[str, pd.DataFrame] = {}
    for abbr, df in logs_by_abbr.items():
        df = df.copy()
        plus_minus_vals: list[float] = []
        for _, row in df.iterrows():
            gdate = str(row.get("game_date", ""))[:10]
            matchup = str(row.get("matchup", ""))
            my_pts = pd.to_numeric(row.get("pts"), errors="coerce")
            opp_abbr = _parse_opponent_abbr(matchup, abbr)
            if opp_abbr and not np.isnan(my_pts):
                opp_pts = pts_lookup.get((gdate, opp_abbr))
                if opp_pts is not None:
                    plus_minus_vals.append(float(my_pts) - float(opp_pts))
                else:
                    plus_minus_vals.append(np.nan)
            else:
                plus_minus_vals.append(np.nan)
        df["plus_minus"] = plus_minus_vals
        filled[abbr] = df
    return filled


def main() -> None:
    if os.environ.get("BOT_C4_ACTIVE"):
        print("FATAL: BOT_C4_ACTIVE is set — refusing to run.", file=sys.stderr)
        sys.exit(1)

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    Path("logs").mkdir(exist_ok=True)
    logger = AuditLogger("logs/pull_playoff_teamgamelog.jsonl", min_severity="WARNING")
    client = NBAIngestionClient(logger=logger, snapshot_id="T186-PULL")
    store = TeamStatsStore()

    teams = NBAIngestionClient.get_all_teams()
    ok = bool(teams)
    if not ok or not teams:
        print("ERROR: get_all_teams() failed.", file=sys.stderr)
        sys.exit(1)

    print(f"\nPulling playoff TeamGameLog: {len(teams)} teams × {len(SEASONS)} seasons "
          f"= {len(teams) * len(SEASONS)} API calls")
    print(f"Throttle: {THROTTLE_S}s / call\n")

    # Accumulate per team abbreviation across both seasons before adding to store.
    # This ensures get_opp_def_rating uses all available playoff history sorted
    # chronologically, with the as_of_date correctly distinguishing seasons.
    logs_by_abbr: dict[str, list[pd.DataFrame]] = {}

    total_calls = 0
    errors = 0

    for season in SEASONS:
        print(f"--- Season: {season} ---")
        for team in teams:
            team_id = team["id"]
            abbr = team["abbreviation"].upper()
            time.sleep(THROTTLE_S)
            total_calls += 1

            ok_pull, log_df = client.fetch_team_game_log(
                team_id, season=season, season_type=SEASON_TYPE
            )

            if not ok_pull:
                print(f"  WARN: {abbr} {season} — fetch failed")
                errors += 1
                continue

            if log_df.empty:
                continue  # did not reach playoffs this season

            logs_by_abbr.setdefault(abbr, []).append(log_df)
            print(f"  OK:   {abbr} {season} — {len(log_df)} playoff games")

        print()

    # Merge per-team frames into one DataFrame per abbreviation
    merged: dict[str, pd.DataFrame] = {}
    for abbr, frames in logs_by_abbr.items():
        merged[abbr] = pd.concat(frames, ignore_index=True)

    # Fill pts_allowed via opponent PTS cross-reference (PLUS_MINUS not in API)
    print("Computing pts_allowed via opponent PTS cross-reference...")
    filled = _fill_pts_allowed_via_crossref(merged)

    # Load into store
    loaded = 0
    pts_allowed_non_nan = 0
    for abbr, df in filled.items():
        store.add_team_log(abbr, df)
        loaded += 1

    # Count non-NaN pts_allowed in cache
    for abbr in filled:
        team_df = store._logs.get(abbr.upper(), pd.DataFrame())
        if not team_df.empty and "pts_allowed" in team_df.columns:
            pts_allowed_non_nan += team_df["pts_allowed"].notna().sum()

    print(f"{'='*55}")
    print(f"Pull complete: {total_calls} API calls, {errors} errors")
    print(f"Teams in store: {loaded}")
    print(f"Games with pts_allowed populated: {pts_allowed_non_nan}")

    cache = store.to_cache_dict()
    OUTPUT_PATH.write_text(json.dumps(cache, indent=2))
    size_kb = OUTPUT_PATH.stat().st_size / 1024
    print(f"Cache written: {OUTPUT_PATH}  ({size_kb:.0f} KB)")
    print(f"\nNext: PYTHONPATH=src .venv/bin/python3 scripts/train_model_v2b.py")


if __name__ == "__main__":
    main()
