"""
C1: Signal Ingestion — NBA Data via nba_api
============================================
Component:    C1 (Signal Ingestion)
Phase active: Phase 3+ (Research Build)
Status:       CANONICAL (Phase 3 2026-05-23)
Upstream:     nba_api (NBA.com stats API proxy; free; no auth required)
              DS-01 Player_Attribute_Matrix_v4 (SNAP-001)
Downstream:   C2 Feature Store (IF-C1-C2)
Interfaces:   IF-C1-C2: pd.DataFrame (normalized player/team game logs)
ADR refs:     ADR-0003 (nba_api confirmed Phase 3 proxy; OQ-015 resolved
              2026-05-23). Synergy/Second Spectrum deferred to Phase 4.
Policy refs:  DATA_PROVENANCE.md, DATA_SNAPSHOTS_INDEX.md

Security constraints (NFR-05, NFR-07):
  - ENV-01: No live venue credentials. VENUE_API_KEY must NOT be present.
  - nba_api requires no authentication — no secrets in this component.
  - Player/game data is public. No PII ingested.

nba_api endpoints used (Phase 3):
  - PlayerGameLog    — per-player game-by-game stats (box score)
  - TeamGameLog      — per-team game-by-game stats
  - BoxScoreTraditionalV2 — full box score for a single game
  - PlayerCareerStats    — career and per-season aggregates
  - LeagueDashPlayerStats — league-wide player stat dashboard

Tracking-specific modifiers (M-9, M-10, M-11):
  - Approximated from NBA.com tracking endpoints available via nba_api.
  - If approximations prove insufficient in Phase 3 evidence, Synergy /
    Second Spectrum access is OQ-015 deferred enhancement (Phase 4).

Output schema (IF-C1-C2) — see INTERFACES_CONTRACTS.md IF-C1-C2:
  Each DataFrame row is one player-game observation with normalized columns:
    player_id, player_name, team_id, team_abbreviation,
    game_id, game_date (YYYY-MM-DD), season (YYYY-YY),
    min, pts, reb, ast, stl, blk, tov, pf,
    fgm, fga, fg_pct, fg3m, fg3a, fg3_pct, ftm, fta, ft_pct,
    plus_minus, snapshot_id, ingestion_run_id, ingested_at
"""

from __future__ import annotations

import os
import time
import uuid
from datetime import datetime, timezone
from typing import Any

import pandas as pd
from nba_api.stats.endpoints import (
    BoxScoreTraditionalV2,
    PlayerCareerStats,
    PlayerGameLog,
    TeamGameLog,
)
from nba_api.stats.static import players as nba_players_static
from nba_api.stats.static import teams as nba_teams_static

from prediction_market_bot.c6_audit_logger.audit_logger import AuditLogger

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

COMPONENT = "C1"

# nba_api is a public API scraper — be a good citizen. The NBA.com endpoints
# rate-limit aggressively. 0.6s between requests is the safe floor.
DEFAULT_REQUEST_DELAY_S = 0.6

# Seasons supported for Phase 3 experiments
# Format: "YYYY-YY" (e.g. "2023-24")
SUPPORTED_SEASONS = ("2021-22", "2022-23", "2023-24")

# Season type constants (nba_api uses these strings)
SEASON_TYPE_REGULAR = "Regular Season"
SEASON_TYPE_PLAYOFFS = "Playoffs"

# Columns we normalize to in IF-C1-C2 output
_OUTPUT_COLUMNS = [
    "player_id",
    "player_name",
    "team_id",
    "team_abbreviation",
    "game_id",
    "game_date",
    "season",
    "season_type",
    "matchup",           # Raw MATCHUP string from nba_api (e.g. "OKC vs. SAS")
    "is_home_game",      # 1 = home ("vs."), 0 = away ("@"), null if unparseable
    "opponent_team_abbr",# 3-letter opponent team abbreviation parsed from MATCHUP
    "min",
    "pts",
    "reb",
    "ast",
    "stl",
    "blk",
    "tov",
    "pf",
    "fgm",
    "fga",
    "fg_pct",
    "fg3m",
    "fg3a",
    "fg3_pct",
    "ftm",
    "fta",
    "ft_pct",
    "plus_minus",
    "snapshot_id",
    "ingestion_run_id",
    "ingested_at",
]


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _run_id() -> str:
    return f"C1-RUN-{uuid.uuid4().hex[:10].upper()}"


def _utc_now_iso() -> str:
    return datetime.now(tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"


def _throttle(delay: float = DEFAULT_REQUEST_DELAY_S) -> None:
    """Sleep between nba_api calls to respect rate limits."""
    time.sleep(delay)


def _normalize_game_log_df(
    raw_df: pd.DataFrame,
    player_id: int,
    player_name: str,
    season: str,
    season_type: str,
    snapshot_id: str,
    run_id: str,
) -> pd.DataFrame:
    """
    Normalize a raw PlayerGameLog DataFrame to the IF-C1-C2 schema.

    nba_api column names vary slightly by endpoint version — this function
    is the single source of truth for the normalization mapping.
    """
    col_map = {
        # nba_api PlayerGameLog column → IF-C1-C2 column
        "GAME_ID": "game_id",
        "GAME_DATE": "game_date",
        "MATCHUP": "matchup",   # retained in output schema (v1.3.0+)
        "WL": "_wl",
        "MIN": "min",
        "FGM": "fgm",
        "FGA": "fga",
        "FG_PCT": "fg_pct",
        "FG3M": "fg3m",
        "FG3A": "fg3a",
        "FG3_PCT": "fg3_pct",
        "FTM": "ftm",
        "FTA": "fta",
        "FT_PCT": "ft_pct",
        "OREB": "_oreb",
        "DREB": "_dreb",
        "REB": "reb",
        "AST": "ast",
        "STL": "stl",
        "BLK": "blk",
        "TOV": "tov",
        "PF": "pf",
        "PTS": "pts",
        "PLUS_MINUS": "plus_minus",
        "TEAM_ID": "team_id",
        "TEAM_ABBREVIATION": "team_abbreviation",
    }

    df = raw_df.rename(columns=col_map).copy()
    df["player_id"] = player_id
    df["player_name"] = player_name
    df["season"] = season
    df["season_type"] = season_type
    df["snapshot_id"] = snapshot_id
    df["ingestion_run_id"] = run_id
    df["ingested_at"] = _utc_now_iso()

    # Normalize game_date to YYYY-MM-DD string
    df["game_date"] = pd.to_datetime(df["game_date"], format="mixed").dt.strftime("%Y-%m-%d")

    # Derive home/away and opponent abbreviation from MATCHUP string.
    # Formats: "TEAM vs. OPP" (home) or "TEAM @ OPP" (away).
    if "matchup" in df.columns:
        df["is_home_game"] = (
            df["matchup"].str.contains(r"\bvs\.", na=False, regex=True)
            .astype("Int8")
        )
        df["opponent_team_abbr"] = df["matchup"].str.extract(
            r"(?:vs\.\s*|@\s*)([A-Z]{2,4})", expand=False
        )
    else:
        df["is_home_game"] = pd.array([pd.NA] * len(df), dtype="Int8")
        df["opponent_team_abbr"] = None

    # Keep only output schema columns (drop internal _* and any surplus cols)
    present = [c for c in _OUTPUT_COLUMNS if c in df.columns]
    missing = [c for c in _OUTPUT_COLUMNS if c not in df.columns]
    df = df[present].copy()
    for col in missing:
        df[col] = None  # fill any schema gaps with None

    return df[_OUTPUT_COLUMNS]


# ---------------------------------------------------------------------------
# Public ingestion API
# ---------------------------------------------------------------------------


class NBAIngestionClient:
    """
    C1 Signal Ingestion client for NBA game log data.

    Wraps nba_api endpoints with:
      - Rate-limit throttling
      - Full C6 audit trail on every operation
      - Normalized DataFrame output (IF-C1-C2 schema)
      - Kill switch integration (all methods return success flag + DataFrame)

    Usage::

        logger = AuditLogger.from_env()
        client = NBAIngestionClient(logger=logger, snapshot_id="SNAP-001")
        session_id = "SESSION-001"

        ok, df = client.fetch_player_game_log(
            player_id=2544,        # LeBron James
            season="2023-24",
            season_type="Regular Season",
            session_id=session_id,
        )
        if not ok:
            # trigger kill switch
            raise RuntimeError("C1 ingestion failure — kill switch required")
    """

    def __init__(
        self,
        logger: AuditLogger,
        snapshot_id: str,
        request_delay: float = DEFAULT_REQUEST_DELAY_S,
    ) -> None:
        self._logger = logger
        self._snapshot_id = snapshot_id
        self._delay = request_delay

    # ------------------------------------------------------------------
    # Player game log
    # ------------------------------------------------------------------

    def fetch_player_game_log(
        self,
        player_id: int,
        season: str,
        season_type: str = SEASON_TYPE_REGULAR,
        session_id: str | None = None,
    ) -> tuple[bool, pd.DataFrame]:
        """
        Fetch a single player's game log for a given season.

        Parameters
        ----------
        player_id:
            NBA player ID (e.g. 2544 for LeBron James).
        season:
            Season string in "YYYY-YY" format (e.g. "2023-24").
        season_type:
            "Regular Season" or "Playoffs".
        session_id:
            Current bot run session ID (for audit chain).

        Returns
        -------
        (success: bool, df: pd.DataFrame)
            success=False means write failure or API error.
            On failure, df is empty. Caller must trigger kill switch on False.
        """
        run_id = _run_id()
        player_name = self._resolve_player_name(player_id)

        ok = self._logger.info(
            COMPONENT,
            "player_game_log_fetch_start",
            payload={
                "player_id": player_id,
                "player_name": player_name,
                "season": season,
                "season_type": season_type,
            },
            session_id=session_id,
            snapshot_id=self._snapshot_id,
            feature_run_id=run_id,
        )
        if not ok:
            return False, pd.DataFrame(columns=_OUTPUT_COLUMNS)

        try:
            _throttle(self._delay)
            game_log = PlayerGameLog(
                player_id=player_id,
                season=season,
                season_type_all_star=season_type,
            )
            raw_df = game_log.get_data_frames()[0]

            if raw_df.empty:
                ok = self._logger.warning(
                    COMPONENT,
                    "player_game_log_empty",
                    payload={
                        "player_id": player_id,
                        "player_name": player_name,
                        "season": season,
                        "season_type": season_type,
                        "rows": 0,
                    },
                    session_id=session_id,
                    snapshot_id=self._snapshot_id,
                    feature_run_id=run_id,
                )
                return ok, pd.DataFrame(columns=_OUTPUT_COLUMNS)

            df = _normalize_game_log_df(
                raw_df=raw_df,
                player_id=player_id,
                player_name=player_name,
                season=season,
                season_type=season_type,
                snapshot_id=self._snapshot_id,
                run_id=run_id,
            )

            ok = self._logger.info(
                COMPONENT,
                "player_game_log_fetch_complete",
                payload={
                    "player_id": player_id,
                    "player_name": player_name,
                    "season": season,
                    "season_type": season_type,
                    "rows": len(df),
                    "date_range": (
                        f"{df['game_date'].min()} → {df['game_date'].max()}"
                        if not df.empty
                        else "empty"
                    ),
                },
                session_id=session_id,
                snapshot_id=self._snapshot_id,
                feature_run_id=run_id,
            )
            return ok, df

        except Exception as exc:
            ok = self._logger.error(
                COMPONENT,
                "player_game_log_fetch_error",
                payload={
                    "player_id": player_id,
                    "player_name": player_name,
                    "season": season,
                    "error": str(exc),
                    "error_type": type(exc).__name__,
                },
                session_id=session_id,
                snapshot_id=self._snapshot_id,
                feature_run_id=run_id,
            )
            # API errors: ok=True (logger worked), but return failure so caller
            # can decide whether to retry or halt
            return False, pd.DataFrame(columns=_OUTPUT_COLUMNS)

    # ------------------------------------------------------------------
    # Multi-player bulk fetch
    # ------------------------------------------------------------------

    def fetch_player_game_logs_bulk(
        self,
        player_ids: list[int],
        season: str,
        season_type: str = SEASON_TYPE_REGULAR,
        session_id: str | None = None,
    ) -> tuple[bool, pd.DataFrame]:
        """
        Fetch game logs for multiple players, concatenated into a single
        DataFrame. Throttled between requests.

        Returns (all_succeeded: bool, combined_df: pd.DataFrame).
        all_succeeded=False if ANY individual fetch failed.
        """
        frames: list[pd.DataFrame] = []
        all_ok = True

        ok = self._logger.info(
            COMPONENT,
            "bulk_fetch_start",
            payload={
                "player_count": len(player_ids),
                "season": season,
                "season_type": season_type,
            },
            session_id=session_id,
            snapshot_id=self._snapshot_id,
        )
        if not ok:
            return False, pd.DataFrame(columns=_OUTPUT_COLUMNS)

        for player_id in player_ids:
            success, df = self.fetch_player_game_log(
                player_id=player_id,
                season=season,
                season_type=season_type,
                session_id=session_id,
            )
            if not success:
                all_ok = False
                # Continue fetching remaining players — don't halt on single failure
            if not df.empty:
                frames.append(df)

        combined = (
            pd.concat(frames, ignore_index=True) if frames else pd.DataFrame(columns=_OUTPUT_COLUMNS)
        )

        ok = self._logger.info(
            COMPONENT,
            "bulk_fetch_complete",
            payload={
                "player_count": len(player_ids),
                "season": season,
                "total_rows": len(combined),
                "all_succeeded": all_ok,
            },
            session_id=session_id,
            snapshot_id=self._snapshot_id,
        )
        return (all_ok and ok), combined

    # ------------------------------------------------------------------
    # Team game log
    # ------------------------------------------------------------------

    def fetch_team_game_log(
        self,
        team_id: int,
        season: str,
        season_type: str = SEASON_TYPE_REGULAR,
        session_id: str | None = None,
    ) -> tuple[bool, pd.DataFrame]:
        """
        Fetch a single team's game log for a given season.
        Normalized to a subset of IF-C1-C2 schema (team-level fields).
        """
        run_id = _run_id()
        team_name = self._resolve_team_name(team_id)

        ok = self._logger.info(
            COMPONENT,
            "team_game_log_fetch_start",
            payload={
                "team_id": team_id,
                "team_name": team_name,
                "season": season,
                "season_type": season_type,
            },
            session_id=session_id,
            snapshot_id=self._snapshot_id,
            feature_run_id=run_id,
        )
        if not ok:
            return False, pd.DataFrame()

        try:
            _throttle(self._delay)
            game_log = TeamGameLog(
                team_id=team_id,
                season=season,
                season_type_all_star=season_type,
            )
            raw_df = game_log.get_data_frames()[0]

            if raw_df.empty:
                self._logger.warning(
                    COMPONENT,
                    "team_game_log_empty",
                    payload={"team_id": team_id, "season": season},
                    session_id=session_id,
                    snapshot_id=self._snapshot_id,
                )
                return True, pd.DataFrame()

            # Normalize team log columns
            col_map = {
                "GAME_ID": "game_id",
                "GAME_DATE": "game_date",
                "MATCHUP": "matchup",
                "WL": "wl",
                "MIN": "min",
                "FGM": "fgm",
                "FGA": "fga",
                "FG_PCT": "fg_pct",
                "FG3M": "fg3m",
                "FG3A": "fg3a",
                "FG3_PCT": "fg3_pct",
                "FTM": "ftm",
                "FTA": "fta",
                "FT_PCT": "ft_pct",
                "REB": "reb",
                "AST": "ast",
                "STL": "stl",
                "BLK": "blk",
                "TOV": "tov",
                "PF": "pf",
                "PTS": "pts",
                "PLUS_MINUS": "plus_minus",
            }
            df = raw_df.rename(columns=col_map).copy()
            df["team_id"] = team_id
            df["team_name"] = team_name
            df["season"] = season
            df["season_type"] = season_type
            df["snapshot_id"] = self._snapshot_id
            df["ingestion_run_id"] = run_id
            df["ingested_at"] = _utc_now_iso()
            df["game_date"] = pd.to_datetime(df["game_date"], format="mixed").dt.strftime("%Y-%m-%d")

            ok = self._logger.info(
                COMPONENT,
                "team_game_log_fetch_complete",
                payload={
                    "team_id": team_id,
                    "team_name": team_name,
                    "season": season,
                    "rows": len(df),
                },
                session_id=session_id,
                snapshot_id=self._snapshot_id,
                feature_run_id=run_id,
            )
            return ok, df

        except Exception as exc:
            self._logger.error(
                COMPONENT,
                "team_game_log_fetch_error",
                payload={
                    "team_id": team_id,
                    "team_name": team_name,
                    "season": season,
                    "error": str(exc),
                    "error_type": type(exc).__name__,
                },
                session_id=session_id,
                snapshot_id=self._snapshot_id,
            )
            return False, pd.DataFrame()

    # ------------------------------------------------------------------
    # Static roster helpers
    # ------------------------------------------------------------------

    @staticmethod
    def get_all_active_players() -> list[dict[str, Any]]:
        """
        Return a list of all active NBA players as dicts with keys:
        id, full_name, first_name, last_name, is_active.
        """
        return nba_players_static.get_active_players()

    @staticmethod
    def get_player_id_by_name(full_name: str) -> int | None:
        """
        Resolve a player's full name to their NBA player ID.
        Returns None if not found.
        Case-insensitive match.
        """
        matches = nba_players_static.find_players_by_full_name(full_name)
        if not matches:
            return None
        # Return the most recently active player if multiple matches
        active = [p for p in matches if p.get("is_active")]
        target = active[0] if active else matches[0]
        return target["id"]

    @staticmethod
    def get_all_teams() -> list[dict[str, Any]]:
        """
        Return a list of all NBA teams as dicts with keys:
        id, full_name, abbreviation, nickname, city, state, year_founded.
        """
        return nba_teams_static.get_teams()

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _resolve_player_name(self, player_id: int) -> str:
        """Resolve player ID to full name for logging. Returns ID string on failure."""
        try:
            all_players = nba_players_static.get_active_players()
            for p in all_players:
                if p["id"] == player_id:
                    return p["full_name"]
            # Check inactive players too
            all_players_inc = nba_players_static.get_inactive_players()
            for p in all_players_inc:
                if p["id"] == player_id:
                    return p["full_name"]
        except Exception:
            pass
        return str(player_id)

    def _resolve_team_name(self, team_id: int) -> str:
        """Resolve team ID to full name for logging. Returns ID string on failure."""
        try:
            all_teams = nba_teams_static.get_teams()
            for t in all_teams:
                if t["id"] == team_id:
                    return t["full_name"]
        except Exception:
            pass
        return str(team_id)
