"""
Targeted player roster pull — append new players to the active feature matrix.
================================================================================
Purpose:  Add players who were missing from the EXP-005 feature matrix.
          Used when the cohort scope needs to expand (e.g., new playoff participants).

Usage:
  PYTHONPATH=src python3 src/prediction_market_bot/run_add_players.py

Output:   Appends new player rows to exp_output/EXP-005/EXP-005_feature_matrix.csv
          Prints a summary of players added and their most recent feature date.

Governance:
  - Run locally only (VPS 403s on nba_api — KI-020)
  - After running: SCP the updated matrix to VPS:
      scp exp_output/EXP-005/EXP-005_feature_matrix.csv \\
          root@157.230.91.33:/opt/prediction-market-bot/exp_output/EXP-005/EXP-005_feature_matrix.csv
  - Commit this script + note in DECISION_LOG; matrix itself is gitignored
"""

from __future__ import annotations

import sys
import uuid
from pathlib import Path

import pandas as pd

_SRC_ROOT = Path(__file__).parent.parent.parent
if str(_SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(_SRC_ROOT))

from prediction_market_bot.c1_signal_ingestion.ingestion import (
    NBAIngestionClient,
    SEASON_TYPE_REGULAR,
    SEASON_TYPE_PLAYOFFS,
)
from prediction_market_bot.c2_feature_store.features import FeatureStore
from prediction_market_bot.c6_audit_logger.audit_logger import AuditLogger

# ---------------------------------------------------------------------------
# Players to add — Finals 2026 coverage gap (LL-013)
# ---------------------------------------------------------------------------
NEW_PLAYERS: dict[int, str] = {
    # SAS Finals participants
    1641705: "Victor Wembanyama",
    1630170: "Devin Vassell",
    1642264: "Stephon Castle",
    1631110: "Jeremy Sochan",
    # NYK Finals participants (missing from v1 matrix)
    1628404: "Josh Hart",
}

# Seasons to pull — enough history for reliable rolling windows
SEASONS = ["2023-24", "2024-25", "2025-26"]
SEASON_TYPES = [SEASON_TYPE_REGULAR, SEASON_TYPE_PLAYOFFS]

FEATURE_CSV = Path("exp_output/EXP-005/EXP-005_feature_matrix.csv")
LOG_DIR = Path("logs")
SNAPSHOT_ID = "SNAP-2026-05-31-FINALS-ROSTER"
SESSION_ID = f"AR-{uuid.uuid4().hex[:8].upper()}"

COMPONENT = "run_add_players"


def main() -> None:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    logger = AuditLogger(LOG_DIR / "audit.jsonl", min_severity="INFO")

    if not FEATURE_CSV.exists():
        print(f"ERROR: {FEATURE_CSV} not found. Run from project root.", file=sys.stderr)
        sys.exit(1)

    existing_df = pd.read_csv(FEATURE_CSV)
    existing_pids = set(existing_df["player_id"].unique())
    players_to_pull = {pid: name for pid, name in NEW_PLAYERS.items()
                       if pid not in existing_pids}

    if not players_to_pull:
        print("All target players already in feature matrix. Nothing to do.")
        return

    print(f"\n[ADD_PLAYERS] Session: {SESSION_ID}")
    print(f"Target players: {list(players_to_pull.values())}")
    print(f"Seasons: {SEASONS} × {SEASON_TYPES}\n")

    client = NBAIngestionClient(logger=logger, snapshot_id=SNAPSHOT_ID)
    store = FeatureStore(logger=logger, snapshot_id=SNAPSHOT_ID)

    player_ids = list(players_to_pull.keys())
    all_logs: list[pd.DataFrame] = []

    for season in SEASONS:
        for stype in SEASON_TYPES:
            print(f"  Pulling {season} {stype}...")
            ok, df = client.fetch_player_game_logs_bulk(
                player_ids=player_ids,
                season=season,
                season_type=stype,
                session_id=SESSION_ID,
            )
            if not df.empty:
                all_logs.append(df)
                print(f"    {len(df)} rows ({df['player_id'].nunique()} players)")
            else:
                print(f"    No data.")

    if not all_logs:
        print("\nERROR: No game log data retrieved. Check nba_api connectivity.")
        sys.exit(1)

    combined = pd.concat(all_logs, ignore_index=True)
    print(f"\n[C2] Computing features for {combined['player_id'].nunique()} players "
          f"({len(combined)} rows total)...")

    ok, feature_df = store.compute_features_bulk(combined, session_id=SESSION_ID)
    if not ok or feature_df.empty:
        print("ERROR: Feature computation failed.", file=sys.stderr)
        sys.exit(1)

    # Get the most recent feature row per player (what pregame uses)
    feature_df["game_date_dt"] = pd.to_datetime(feature_df["game_date"], errors="coerce")
    latest = feature_df.sort_values("game_date_dt").groupby("player_id").last().reset_index()

    print(f"\n[RESULTS] Latest feature rows per player:")
    for _, row in latest.iterrows():
        pid = int(row["player_id"])
        name = players_to_pull.get(pid, str(pid))
        gdate = row.get("game_date", "?")
        pts_mean = row.get("pts_l10_mean", float("nan"))
        print(f"  {name:<28} last_game={gdate}  pts_l10_mean={pts_mean:.1f}")

    # Append all feature rows (not just latest) so rolling windows stay accurate
    new_rows = feature_df[feature_df["player_id"].isin(players_to_pull)]
    updated = pd.concat([existing_df, new_rows], ignore_index=True)
    updated.to_csv(FEATURE_CSV, index=False)

    print(f"\n[DONE] Added {len(new_rows)} rows for {latest['player_id'].nunique()} players.")
    print(f"Updated matrix: {FEATURE_CSV} ({len(updated)} total rows)")
    print(f"\nNext step — copy to VPS:")
    print(f"  scp {FEATURE_CSV} root@157.230.91.33:/opt/prediction-market-bot/{FEATURE_CSV}")


if __name__ == "__main__":
    main()
