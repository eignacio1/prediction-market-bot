#!/usr/bin/env python3
"""
G3 (GG-141, T-405) -- backfill opp_sp_* / opp_runs_allowed_l10 for the
resolved cohort, live from the MLB Stats API.

GG-141 finding: opp_sp_era_l5 / opp_sp_k9_l5 / opp_sp_bb9_l5 /
opp_runs_allowed_l10 are 100% blank across all 20,943 season-2026 rows in
exp_output/T9_GG105_REWORK/mlb_feature_matrix.csv, and opp_sp_is_known is
hardcoded 0.0 for every row. Root cause (established this session via direct
VPS cache inspection): NOT a bug in mlb_features.py (that file's SP-overlay
logic is correct and fully data-driven) -- the resumable cache in
generate_mlb_features.py silently cached an EMPTY fetch result for
starters_2026.json ({}), pitcher_logs_2026.parquet (0 rows), and
completed_games_2026.parquet (0 rows) around 2026-06-24, and every
regeneration since has reused that poisoned cache. The live MLB Stats API
itself is confirmed working (direct curl test, 2026-07-29).

This script re-fetches the three missing inputs LIVE, scoped to just the
resolved cohort (MAIN t1t2t3 + T4), and recomputes the five opp_* columns
using the exact same reusable functions/classes mlb_features.py itself uses:
  - MLBIngestionClient.fetch_game_starters / fetch_pitcher_game_logs_bulk /
    fetch_completed_games (C1, unmodified)
  - mlb_features._get_opp_sp_id (C2, unmodified, pure function)
  - MLBPitcherStatsStore.get_era_l5/get_k_per_9_l5/get_bb_per_9_l5 (C1,
    TI-01 guarded, unmodified)
  - MLBTeamStatsStore.build_from_games/get_opp_runs_allowed (C1, TI-01
    guarded, unmodified)

RESEARCH ONLY. Writes only to exp_output/T9_GG105_REWORK/. No production
cache, no live CSV, no epoch bump, no C4 sizing change. Hard Rule 4: this is
a read/compute-only backfill of a feature CSV for offline scoring, not a
refit or deploy of the frozen T1 model.
"""
from __future__ import annotations

import csv
import json
import sys
import uuid
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from exp_retrospective_core import load_portfolio, deduplicate  # noqa: E402
from prediction_market_bot.c1_signal_ingestion.mlb_ingestion import (  # noqa: E402
    MLBIngestionClient,
    DEFAULT_REQUEST_DELAY_S,
)
from prediction_market_bot.c1_signal_ingestion.mlb_pitcher_stats_store import (  # noqa: E402
    MLBPitcherStatsStore,
)
from prediction_market_bot.c1_signal_ingestion.mlb_team_stats_store import (  # noqa: E402
    MLBTeamStatsStore,
)
from prediction_market_bot.c2_feature_store.mlb_features import _get_opp_sp_id  # noqa: E402
from prediction_market_bot.c6_audit_logger.audit_logger import AuditLogger  # noqa: E402

MAIN_PORTFOLIO = Path("logs/.vps_portfolio_cache_mlb.json")
T4_LEDGER = Path("logs/t4_mlb_resolved_ledger.jsonl")
FEATURE_CSV = Path("exp_output/T9_GG105_REWORK/mlb_feature_matrix.csv")
OUT_DIR = Path("exp_output/T9_GG105_REWORK")
OUT_CSV = OUT_DIR / "mlb_feature_matrix_oppsp_backfilled.csv"
LOG_PATH = OUT_DIR / "g3_backfill_audit.jsonl"
SNAPSHOT_ID = "G3-GG141-BACKFILL"
SEASON = 2026
COMPLETED_GAMES_START = "2026-03-01"  # covers the full 2026 season, ahead of TI-01 rolling windows

SP_COLS = ["opp_sp_era_l5", "opp_sp_k9_l5", "opp_sp_bb9_l5", "opp_sp_is_known"]
ALL_COLS = SP_COLS + ["opp_runs_allowed_l10"]


def load_main_keys() -> set[tuple[str, str]]:
    positions = deduplicate(load_portfolio(MAIN_PORTFOLIO))
    return {(str(p.player_id), p.game_date) for p in positions if p.player_id is not None}


def load_t4_keys() -> set[tuple[str, str]]:
    keys: set[tuple[str, str]] = set()
    with open(T4_LEDGER) as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            rec = json.loads(line)
            pid = rec.get("player_id")
            gd = rec.get("game_date")
            if pid is not None and gd:
                keys.add((str(pid), gd))
    return keys


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    main_keys = load_main_keys()
    t4_keys = load_t4_keys()
    cohort_keys = main_keys | t4_keys
    print(f"MAIN resolved dedup keys: {len(main_keys)}")
    print(f"T4 resolved keys:         {len(t4_keys)}")
    print(f"Union cohort keys:        {len(cohort_keys)}")

    df = pd.read_csv(FEATURE_CSV, low_memory=False)
    df["player_id_str"] = df["player_id"].astype(str)
    df["game_date_str"] = df["game_date"].astype(str)

    mask = list(
        zip(df["player_id_str"], df["game_date_str"])
    )
    row_in_cohort = [k in cohort_keys for k in mask]
    cohort_idx = df.index[row_in_cohort]
    print(f"Matched physical CSV rows to backfill: {len(cohort_idx)}")
    if len(cohort_idx) == 0:
        print("FATAL: no cohort rows matched the feature CSV -- aborting, nothing to backfill.")
        return 1

    cohort_df = df.loc[cohort_idx]
    needed_dates = sorted(cohort_df["game_date_str"].unique())
    print(f"Unique game_dates needing starters lookup: {len(needed_dates)} "
          f"({needed_dates[0]} .. {needed_dates[-1]})")

    session_id = f"G3-{uuid.uuid4().hex[:8].upper()}"
    logger = AuditLogger(str(LOG_PATH), min_severity="INFO")
    client = MLBIngestionClient(
        logger=logger,
        snapshot_id=SNAPSHOT_ID,
        request_delay=DEFAULT_REQUEST_DELAY_S,
    )

    # 1. Live-fetch game_starters for every needed date, merge into one dict.
    game_starters: dict[int, dict] = {}
    starters_errors = 0
    for i, gd in enumerate(needed_dates, 1):
        ok, day_starters = client.fetch_game_starters(gd, session_id=session_id)
        if not ok:
            starters_errors += 1
        game_starters.update(day_starters)
        if i % 20 == 0 or i == len(needed_dates):
            print(f"  [starters] {i}/{len(needed_dates)} dates fetched, "
                  f"{len(game_starters)} games known so far")
    print(f"game_starters: {len(game_starters)} games total, {starters_errors} date-fetch errors")

    # 2. Determine opposing SP id for every cohort row via the real C2 function.
    sp_ids_needed: set[int] = set()
    row_sp_id: dict[int, int | None] = {}
    for idx, row in cohort_df.iterrows():
        sp_id = _get_opp_sp_id(row, game_starters)
        row_sp_id[idx] = sp_id
        if sp_id is not None:
            sp_ids_needed.add(int(sp_id))
    print(f"Opposing SP resolved for {sum(1 for v in row_sp_id.values() if v is not None)}"
          f"/{len(row_sp_id)} cohort rows; {len(sp_ids_needed)} unique SPs")

    # 3. Live-fetch pitcher game logs (season 2026) for exactly the needed SPs.
    pitcher_store = MLBPitcherStatsStore()
    if sp_ids_needed:
        ok, pitcher_df = client.fetch_pitcher_game_logs_bulk(
            sorted(sp_ids_needed), season=SEASON, session_id=session_id
        )
        print(f"Pitcher logs fetch ok={ok}, rows={len(pitcher_df)}")
        if not pitcher_df.empty:
            for pid, grp in pitcher_df.groupby("player_id"):
                pitcher_store.add_pitcher_log(int(pid), grp)
    print(f"MLBPitcherStatsStore populated for {len(pitcher_store)} pitchers")

    # 4. Live-fetch completed games for the season, build MLBTeamStatsStore.
    max_date = needed_dates[-1]
    ok, games_df = client.fetch_completed_games(
        COMPLETED_GAMES_START, max_date, session_id=session_id
    )
    print(f"Completed games fetch ok={ok}, rows={len(games_df)}")
    team_store = MLBTeamStatsStore.build_from_games(games_df)

    # 5. Compute the five columns for every cohort row (TI-01 guarded, same
    #    logic as mlb_features.MLBFeatureStore.compute_features_bulk).
    era_l5, k9_l5, bb9_l5, sp_known, opp_ra_l10 = {}, {}, {}, {}, {}
    for idx, row in cohort_df.iterrows():
        sp_id = row_sp_id[idx]
        gd = row["game_date_str"]
        if sp_id is not None:
            era_l5[idx] = pitcher_store.get_era_l5(sp_id, gd)
            k9_l5[idx] = pitcher_store.get_k_per_9_l5(sp_id, gd)
            bb9_l5[idx] = pitcher_store.get_bb_per_9_l5(sp_id, gd)
            sp_known[idx] = 1.0
        else:
            era_l5[idx] = None
            k9_l5[idx] = None
            bb9_l5[idx] = None
            sp_known[idx] = 0.0
        opp_ra_l10[idx] = team_store.get_opp_runs_allowed(
            str(row.get("opponent_team_abbr", "")), gd
        )

    for idx in cohort_idx:
        df.at[idx, "opp_sp_era_l5"] = era_l5[idx]
        df.at[idx, "opp_sp_k9_l5"] = k9_l5[idx]
        df.at[idx, "opp_sp_bb9_l5"] = bb9_l5[idx]
        df.at[idx, "opp_sp_is_known"] = sp_known[idx]
        df.at[idx, "opp_runs_allowed_l10"] = opp_ra_l10[idx]

    df = df.drop(columns=["player_id_str", "game_date_str"])
    df.to_csv(OUT_CSV, index=False, quoting=csv.QUOTE_MINIMAL)

    n = len(cohort_idx)
    known_rate = sum(sp_known.values()) / n if n else 0.0
    era_rate = sum(1 for v in era_l5.values() if v is not None) / n if n else 0.0
    ra_rate = sum(1 for v in opp_ra_l10.values() if v is not None) / n if n else 0.0
    print(f"\nBackfilled n={n} cohort rows -> {OUT_CSV}")
    print(f"opp_sp_is_known=1 rate: {known_rate:.3f}")
    print(f"opp_sp_era_l5 non-null rate (of known-SP rows, TI-01 min_periods=2): {era_rate:.3f}")
    print(f"opp_runs_allowed_l10 non-null rate: {ra_rate:.3f}")
    print(f"BACKFILL_N={n}")

    logger.log(
        "G3",
        "opp_sp_backfill_complete",
        payload={
            "session_id": session_id,
            "cohort_n": n,
            "sp_known_rate": known_rate,
            "era_l5_nonnull_rate": era_rate,
            "opp_ra_l10_nonnull_rate": ra_rate,
            "out_csv": str(OUT_CSV),
        },
        session_id=session_id,
        snapshot_id=SNAPSHOT_ID,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
