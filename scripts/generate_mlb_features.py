"""
T-187A — MLB Feature Matrix Generation
=======================================

Script ID:    T-187A
ADR:          ADR-0031 (multi-sport C1/C2 extension)
Status:       CANONICAL
Upstream:     MLB Stats API (statsapi.mlb.com; unauthenticated)
Downstream:   scripts/train_mlb_model.py (T-183)
Output:       exp_output/MLB/mlb_feature_matrix.csv

Purpose
-------
Offline orchestration: MLBIngestionClient → MLBFeatureStore → CSV.
Must be run once before training (T-183) and periodically thereafter
to capture new games (recommended: daily during the season, before
run_mlb_paper_trade.py fires).

Data scope
----------
Fetches Regular Season (gameType="R") batter game logs for all active
MLB position players (primaryPosition.type != "Pitcher") across the
configured SEASONS. Starting pitcher game logs are fetched for all SPs
encountered in game_starters. Completed game scores populate
MLBTeamStatsStore for the opp_runs_allowed_l10 context feature.

Resumable caching
-----------------
Intermediate outputs are cached under CACHE_DIR so that interrupted
runs can resume without re-fetching already-completed API calls:

  cache/players_{season}.json          — list of (player_id, name) tuples
  cache/batter_logs_{season}.parquet   — concatenated batter game logs
  cache/pitcher_logs_{season}.parquet  — concatenated pitcher game logs
  cache/completed_games_{season}.parquet
  cache/starters_{season}.json         — {gamePk: starters_dict}

Delete a cache file to force re-fetch for that data type/season.

Performance
-----------
MLB Stats API at 0.6 s/call:
  Players endpoint:    3 calls (~2 s)
  Batter game logs:    ~700 position players × 3 seasons = ~2,100 calls (~21 min)
  Pitcher game logs:   ~120 unique SPs × 3 seasons = ~360 calls (~4 min)
  Starters:            ~500 unique dates = ~300 s = ~5 min
  Completed games:     6 range calls (~4 s)
Total first run:       ~30 min; subsequent runs (cache hit): <1 min

How to run:
  PYTHONPATH=src python3 scripts/generate_mlb_features.py
  PYTHONPATH=src python3 scripts/generate_mlb_features.py --seasons 2025 2026
  PYTHONPATH=src python3 scripts/generate_mlb_features.py --dry-run

Security:
  No BOT_C4_ACTIVE, no venue API calls, no hardcoded secrets.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import uuid
from datetime import date, datetime, timezone
from pathlib import Path

import pandas as pd
import requests

_SRC_ROOT = Path(__file__).parent.parent / "src"
if str(_SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(_SRC_ROOT))

from prediction_market_bot.c1_signal_ingestion.data_contracts import (
    MLB_BATTER_CONTRACT,
    MLB_PITCHER_CONTRACT,
)
from prediction_market_bot.c1_signal_ingestion.mlb_ingestion import (
    DEFAULT_REQUEST_DELAY_S,
    MLB_BASE_URL,
    REQUEST_TIMEOUT_S,
    MLBIngestionClient,
)
from prediction_market_bot.c1_signal_ingestion.mlb_pitcher_stats_store import MLBPitcherStatsStore
from prediction_market_bot.c1_signal_ingestion.mlb_team_stats_store import MLBTeamStatsStore
from prediction_market_bot.c1_signal_ingestion.validators import (
    DataContractViolation,
    assert_contract,
)
from prediction_market_bot.c2_feature_store.mlb_features import MLBFeatureStore
from prediction_market_bot.c6_audit_logger.audit_logger import AuditLogger

sys.path.insert(0, str(Path(__file__).parent))
from check_feature_column_health import print_report, scan_columns  # noqa: E402

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

CACHE_DIR = Path("exp_output/MLB/cache")
OUTPUT_CSV = Path("exp_output/MLB/mlb_feature_matrix.csv")
LOG_PATH = Path("exp_output/MLB/generate_features.jsonl")

DEFAULT_SEASONS: list[int] = [2024, 2025, 2026]
TRAIN_END_DATE = "2025-09-30"
VAL_END_DATE = "2025-12-31"

SNAPSHOT_ID = "SNAP-T187A"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _utc_now() -> str:
    return datetime.now(tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"


def _today_iso() -> str:
    return date.today().isoformat()


def _players_cache_path(season: int) -> Path:
    return CACHE_DIR / f"players_{season}.json"


def _batter_cache_path(season: int) -> Path:
    return CACHE_DIR / f"batter_logs_{season}.parquet"


def _pitcher_cache_path(season: int) -> Path:
    return CACHE_DIR / f"pitcher_logs_{season}.parquet"


POSTSEASON_GAME_TYPES = "F,D,L,W"  # wild card, division, league champ., world series


def _batter_post_cache_path(season: int) -> Path:
    return CACHE_DIR / f"batter_logs_{season}_post.parquet"


def _games_post_cache_path(season: int) -> Path:
    return CACHE_DIR / f"completed_games_{season}_post.parquet"


def _postseason_date_range(season: int) -> tuple[str, str]:
    end = f"{season}-11-15"
    if season == 2026:
        end = min(end, _today_iso())
    return f"{season}-09-25", end


def _games_cache_path(season: int) -> Path:
    return CACHE_DIR / f"completed_games_{season}.parquet"


def _starters_cache_path(season: int) -> Path:
    return CACHE_DIR / f"starters_{season}.json"


def _fetch_position_players(season: int) -> list[dict]:
    """Return list of {player_id, full_name} for position players (non-pitchers)."""
    try:
        resp = requests.get(
            f"{MLB_BASE_URL}/api/v1/sports/1/players",
            params={"season": str(season), "gameType": "R"},
            timeout=REQUEST_TIMEOUT_S,
        )
        resp.raise_for_status()
        data = resp.json()
    except Exception as exc:
        print(f"  [ERROR] Could not fetch player roster for {season}: {exc}")
        return []

    players = []
    for p in data.get("people", []):
        pos_type = p.get("primaryPosition", {}).get("type", "")
        pos_abbr = p.get("primaryPosition", {}).get("abbreviation", "")
        pid = p.get("id")
        name = p.get("fullName", f"player_{pid}")
        if pid is None:
            continue
        # Exclude pure pitchers (P). Two-way players (TP) can bat.
        if pos_abbr == "P" or pos_type.lower() in ("pitcher",):
            continue
        players.append({"player_id": int(pid), "full_name": name})
    return players


def _season_date_range(season: int) -> tuple[str, str]:
    """Return (start_date, end_date) for a Regular Season."""
    if season == 2026:
        return f"{season}-03-26", _today_iso()
    return f"{season}-03-20", f"{season}-10-01"


# ---------------------------------------------------------------------------
# Per-season fetch routines (with cache)
# ---------------------------------------------------------------------------


def _load_or_fetch_players(season: int) -> list[dict]:
    cache = _players_cache_path(season)
    if cache.exists():
        print(f"  [CACHE] Players {season}: hit")
        return json.loads(cache.read_text())
    print(f"  [FETCH] Players {season}...")
    players = _fetch_position_players(season)
    cache.write_text(json.dumps(players))
    print(f"    {len(players)} position players")
    return players


def _load_or_fetch_batter_logs(
    season: int,
    players: list[dict],
    client: MLBIngestionClient,
    session_id: str,
) -> pd.DataFrame:
    cache = _batter_cache_path(season)
    if cache.exists():
        print(f"  [CACHE] Batter logs {season}: hit")
        return pd.read_parquet(cache)

    print(f"  [FETCH] Batter logs {season} ({len(players)} players)...")
    player_ids = [p["player_id"] for p in players]
    ok, df = client.fetch_batter_game_logs_bulk(
        player_ids=player_ids,
        season=str(season),
        session_id=session_id,
    )
    if not ok:
        print(f"    [WARN] Some player fetches failed for season {season}.")
    if df.empty:
        df = pd.DataFrame()
    else:
        df = df[df["season_type"] == "Regular Season"].copy()
    df.to_parquet(cache, index=False)
    print(f"    {len(df)} game rows cached")
    return df


def _postseason_player_ids(season: int, client: MLBIngestionClient) -> set[int] | None:
    """IDs of every player listed in a postseason game's boxscore (W66.1, Actions minutes at $0).

    Fetching a postseason gameLog for every regular-season position player (~650 requests) returns
    rows only for players who actually appeared in a postseason game. The boxscore roster of each
    postseason game is a SUPERSET of those players (it includes bench players who never appeared,
    whose gameLog would be empty), so restricting the fetch to it yields identical rows.
    Returns None on any doubt (schedule failure, boxscore failure, no games) so the caller falls
    back to the full player list -- the pre-W66.1 behaviour.
    """
    start, end = _postseason_date_range(season)
    sched = client._get(
        f"{MLB_BASE_URL}/api/v1/schedule",
        params={"sportId": 1, "startDate": start, "endDate": end, "gameType": POSTSEASON_GAME_TYPES},
    )
    if sched is None:
        return None
    game_pks = [
        g["gamePk"]
        for block in sched.get("dates", [])
        for g in block.get("games", [])
        if g.get("gamePk") is not None
    ]
    if not game_pks:
        return None
    ids: set[int] = set()
    for pk in game_pks:
        box = client._get(f"{MLB_BASE_URL}/api/v1/game/{pk}/boxscore")
        if box is None:
            return None
        for side in ("home", "away"):
            for key in (box.get("teams", {}).get(side, {}).get("players") or {}):
                if key.startswith("ID") and key[2:].isdigit():
                    ids.add(int(key[2:]))
    return ids


def _load_or_fetch_batter_logs_post(
    season: int,
    players: list[dict],
    client: MLBIngestionClient,
    session_id: str,
) -> pd.DataFrame:
    """Postseason batter logs (opt-in, D6(b)). Separate cache; never touches the R cache."""
    cache = _batter_post_cache_path(season)
    if cache.exists():
        print(f"  [CACHE] Postseason batter logs {season}: hit")
        return pd.read_parquet(cache)
    post_ids = _postseason_player_ids(season, client)
    if post_ids is not None:
        # Same order as the full list, so the concatenated frame is row-for-row what it was before.
        fetch_players = [p for p in players if p["player_id"] in post_ids]
        print(
            f"  [FETCH] Postseason batter logs {season} "
            f"({len(fetch_players)} of {len(players)} players appear in a postseason game)..."
        )
    else:
        fetch_players = players
        print(f"  [FETCH] Postseason batter logs {season} ({len(players)} players; boxscore filter unavailable)...")
    ok, df = client.fetch_batter_game_logs_bulk(
        player_ids=[p["player_id"] for p in fetch_players],
        season=str(season),
        season_type=POSTSEASON_GAME_TYPES,
        session_id=session_id,
    )
    if not ok:
        print(f"    [WARN] Some postseason fetches failed for season {season}.")
    if df.empty:
        df = pd.DataFrame()
    else:
        df = df.copy()
        df["season_type"] = "Postseason"
    df.to_parquet(cache, index=False)
    print(f"    {len(df)} postseason game rows cached")
    return df


def _load_or_fetch_completed_games_post(
    season: int,
    client: MLBIngestionClient,
    session_id: str,
) -> pd.DataFrame:
    cache = _games_post_cache_path(season)
    if cache.exists():
        print(f"  [CACHE] Postseason games {season}: hit")
        return pd.read_parquet(cache)
    start, end = _postseason_date_range(season)
    ok, df = client.fetch_completed_games(
        start, end, session_id=session_id, game_types=POSTSEASON_GAME_TYPES
    )
    if not ok or df.empty:
        df = pd.DataFrame()
    df.to_parquet(cache, index=False)
    return df


def _load_or_fetch_completed_games(
    season: int,
    client: MLBIngestionClient,
    session_id: str,
) -> pd.DataFrame:
    cache = _games_cache_path(season)
    if cache.exists():
        print(f"  [CACHE] Completed games {season}: hit")
        return pd.read_parquet(cache)

    start, end = _season_date_range(season)
    print(f"  [FETCH] Completed games {season} ({start} to {end})...")
    ok, df = client.fetch_completed_games(start, end, session_id=session_id)
    if not ok or df.empty:
        print(f"    [WARN] No completed games for {season}.")
        df = pd.DataFrame()
    df.to_parquet(cache, index=False)
    print(f"    {len(df)} games cached")
    return df


def _load_or_fetch_starters(
    season: int,
    game_dates: list[str],
    client: MLBIngestionClient,
    session_id: str,
) -> dict[int, dict]:
    cache = _starters_cache_path(season)
    if cache.exists():
        print(f"  [CACHE] Game starters {season}: hit ({len(game_dates)} dates in batter logs)")
        raw = json.loads(cache.read_text())
        return {int(k): v for k, v in raw.items()}

    print(f"  [FETCH] Game starters {season} ({len(game_dates)} dates)...")
    all_starters: dict[int, dict] = {}
    for i, gd in enumerate(sorted(set(game_dates))):
        ok, starters = client.fetch_game_starters(str(gd), session_id=session_id)
        if ok and starters:
            all_starters.update(starters)
        if (i + 1) % 50 == 0:
            print(f"    ...{i + 1}/{len(game_dates)} dates fetched")

    cache.write_text(json.dumps({str(k): v for k, v in all_starters.items()}))
    print(f"    {len(all_starters)} games in starters dict")
    return all_starters


def _load_or_fetch_pitcher_logs(
    season: int,
    sp_ids: list[int],
    client: MLBIngestionClient,
    session_id: str,
) -> pd.DataFrame:
    cache = _pitcher_cache_path(season)
    if cache.exists():
        print(f"  [CACHE] Pitcher logs {season}: hit")
        return pd.read_parquet(cache)

    if not sp_ids:
        print(f"  [SKIP] No SP IDs for {season}")
        pd.DataFrame().to_parquet(cache, index=False)
        return pd.DataFrame()

    print(f"  [FETCH] Pitcher logs {season} ({len(sp_ids)} unique SPs)...")
    ok, df = client.fetch_pitcher_game_logs_bulk(
        player_ids=sp_ids,
        season=str(season),
        session_id=session_id,
    )
    if not ok:
        print(f"    [WARN] Some pitcher fetches failed for season {season}.")
    if df.empty:
        df = pd.DataFrame()
    df.to_parquet(cache, index=False)
    print(f"    {len(df)} pitcher game rows cached")
    return df


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main(
    seasons: list[int] = DEFAULT_SEASONS,
    dry_run: bool = False,
    include_postseason: bool = False,
) -> None:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)

    if os.environ.get("BOT_C4_ACTIVE"):
        print("FATAL: BOT_C4_ACTIVE is set — offline script must not run inside C4.", file=sys.stderr)
        sys.exit(1)

    session_id = f"T187A-{uuid.uuid4().hex[:8].upper()}"
    logger = AuditLogger(str(LOG_PATH), min_severity="INFO")

    print(f"\n{'='*65}")
    print("T-187A — MLB Feature Matrix Generation")
    print(f"Session:  {session_id}")
    print(f"Seasons:  {seasons}")
    print(f"Output:   {OUTPUT_CSV}")
    if dry_run:
        print("MODE: DRY RUN — no output files written")
    print(f"{'='*65}\n")

    logger.log(
        "T187A",
        "generate_mlb_features_start",
        payload={"session_id": session_id, "seasons": seasons, "dry_run": dry_run},
        session_id=session_id,
        snapshot_id=SNAPSHOT_ID,
    )

    client = MLBIngestionClient(
        logger=logger,
        snapshot_id=SNAPSHOT_ID,
        request_delay=DEFAULT_REQUEST_DELAY_S,
    )
    feature_store = MLBFeatureStore(logger=logger, snapshot_id=SNAPSHOT_ID)

    all_feature_dfs: list[pd.DataFrame] = []

    for season in seasons:
        print(f"\n[SEASON {season}]")

        # 1. Position players
        players = _load_or_fetch_players(season)
        if not players:
            print(f"  [SKIP] No players found for {season}.")
            continue

        # 2. Batter game logs
        batter_df = _load_or_fetch_batter_logs(season, players, client, session_id)
        if include_postseason:
            post_df = _load_or_fetch_batter_logs_post(season, players, client, session_id)
            if not post_df.empty:
                batter_df = pd.concat([batter_df, post_df], ignore_index=True)
        if batter_df.empty:
            print(f"  [SKIP] No batter game logs for {season}.")
            continue

        try:
            assert_contract(
                batter_df,
                MLB_BATTER_CONTRACT,
                audit=logger,
                pipeline_id="T187A",
                session_id=session_id,
                snapshot_id=SNAPSHOT_ID,
            )
        except DataContractViolation as exc:
            print(f"  [SKIP] Batter log data contract violated for {season}: {exc}")
            continue

        # 3. Completed games → team store
        completed_df = _load_or_fetch_completed_games(season, client, session_id)
        if include_postseason:
            post_games = _load_or_fetch_completed_games_post(season, client, session_id)
            if not post_games.empty:
                completed_df = pd.concat([completed_df, post_games], ignore_index=True)
        team_store = MLBTeamStatsStore.build_from_games(completed_df) if not completed_df.empty else MLBTeamStatsStore()
        print(f"  [TSS] {len(team_store)} teams in store")

        # 4. Game starters (using unique dates from batter_df)
        game_dates = batter_df["game_date"].dropna().astype(str).unique().tolist()
        starters = _load_or_fetch_starters(season, game_dates, client, session_id)

        # 5. SP IDs from starters → pitcher logs
        sp_ids: list[int] = []
        for info in starters.values():
            for key in ("home_sp_id", "away_sp_id"):
                sid = info.get(key)
                if sid is not None:
                    sp_ids.append(int(sid))
        sp_ids = sorted(set(sp_ids))

        pitcher_df = _load_or_fetch_pitcher_logs(season, sp_ids, client, session_id)
        if not pitcher_df.empty:
            try:
                assert_contract(
                    pitcher_df,
                    MLB_PITCHER_CONTRACT,
                    audit=logger,
                    pipeline_id="T187A",
                    session_id=session_id,
                    snapshot_id=SNAPSHOT_ID,
                )
            except DataContractViolation as exc:
                # Non-fatal: pitcher fetch errors are already tolerated elsewhere
                # in this script (see _load_or_fetch_pitcher_logs's [WARN] path).
                print(f"  [WARN] Pitcher log data contract violated for {season}: {exc}")
        pitcher_store = MLBPitcherStatsStore()
        if not pitcher_df.empty and "player_id" in pitcher_df.columns:
            for sp_id, sp_group in pitcher_df.groupby("player_id"):
                pitcher_store.add_pitcher_log(int(sp_id), sp_group)
        print(f"  [PSS] {len(pitcher_store)} pitchers in store")

        # 6. Compute features
        print(f"  [C2] Computing features ({len(batter_df)} game rows)...")
        ok, feature_df = feature_store.compute_features_bulk(
            batter_game_log_df=batter_df,
            game_starters=starters,
            pitcher_store=pitcher_store,
            team_store=team_store,
            session_id=session_id,
        )
        if not ok:
            print(f"  [ERROR] Feature computation encountered errors for {season}.")
        if feature_df.empty:
            print(f"  [SKIP] Empty feature output for {season}.")
            continue

        print(f"    {len(feature_df)} feature rows ({feature_df['player_id'].nunique() if 'player_id' in feature_df.columns else '?'} players)")

        # 7. Assign train/test labels
        ok2, feature_df = feature_store.assign_train_test_labels(
            feature_df,
            train_end_date=TRAIN_END_DATE,
            val_end_date=VAL_END_DATE,
            session_id=session_id,
        )
        if not ok2:
            print(f"  [WARN] Label assignment log write failed for {season}.")

        all_feature_dfs.append(feature_df)

    if not all_feature_dfs:
        print("\n[FATAL] No feature data produced across any season.", file=sys.stderr)
        sys.exit(1)

    combined = pd.concat(all_feature_dfs, ignore_index=True)

    # Ensure game_date is serializable (date objects → str)
    if "game_date" in combined.columns:
        combined["game_date"] = combined["game_date"].astype(str)
    if "temporal_cutoff" in combined.columns:
        combined["temporal_cutoff"] = combined["temporal_cutoff"].astype(str)

    print(f"\n[COMBINED] {len(combined)} total rows | {combined['player_id'].nunique()} players")

    # GG-141 preventive check (T-405): a blank or hardcoded-constant feature
    # column is syntactically valid data and produces no exception -- this is
    # the only point in the pipeline where it's caught same-day instead of
    # weeks later. Non-fatal: a real, sparse-but-legitimate column (e.g.
    # early-season small-n) should not block the day's feature generation,
    # but it must be loud in the cron log so Step 4 (or a human) can see it.
    column_health_findings = scan_columns(combined)
    print_report(column_health_findings, str(OUTPUT_CSV))
    if column_health_findings:
        logger.log(
            "T187A",
            "column_health_findings",
            payload={
                "session_id": session_id,
                "findings": column_health_findings,
            },
            session_id=session_id,
            snapshot_id=SNAPSHOT_ID,
            severity="WARNING",
        )

    if not dry_run:
        combined.to_csv(OUTPUT_CSV, index=False)
        print(f"[DONE] Wrote {OUTPUT_CSV}")
        logger.log(
            "T187A",
            "generate_mlb_features_complete",
            payload={
                "output_csv": str(OUTPUT_CSV),
                "total_rows": len(combined),
                "player_count": int(combined["player_id"].nunique()),
                "seasons": seasons,
                "session_id": session_id,
            },
            session_id=session_id,
            snapshot_id=SNAPSHOT_ID,
        )
    else:
        print("[DRY RUN] Feature matrix not written.")

    print(f"\n{'='*65}")
    print("T-187A COMPLETE" if not dry_run else "T-187A DRY RUN COMPLETE")
    print(f"{'='*65}\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate MLB C2 feature matrix (T-187A)")
    parser.add_argument(
        "--seasons",
        type=int,
        nargs="+",
        default=DEFAULT_SEASONS,
        help=f"MLB seasons to fetch (default: {DEFAULT_SEASONS})",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Run without writing output files (cache writes still happen)",
    )
    parser.add_argument(
        "--include-postseason",
        action="store_true",
        help="Also fetch and include postseason games (default off: regular season only)",
    )
    args = parser.parse_args()
    main(seasons=args.seasons, dry_run=args.dry_run, include_postseason=args.include_postseason)
