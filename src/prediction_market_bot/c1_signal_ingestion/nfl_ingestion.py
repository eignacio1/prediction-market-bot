"""
C1: Signal Ingestion — NFL via nflverse (github.com/nflverse/nflverse-data)
=============================================================================
Component:    C1 (Signal Ingestion)
Sport:        NFL
Status:       NEW (T-526, GG-253)
Upstream:     nflverse-data GitHub Releases (static CSV assets; MIT license)
Downstream:   NFLTeamStatsStore (nfl_team_stats_store.py); C2 feature build (future)

Source selection (GG-253) — nflverse vs. ESPN
-----------------------------------------------
Two candidate sources were evaluated. nflverse was chosen:

  nflverse-data (chosen): MIT-licensed, community-maintained, purpose-built
    NFL analytics data project (feeds nflfastR/nflreadr). Data is distributed
    as static GitHub Release assets (CSV/parquet), updated nightly during
    the season. No auth, no documented rate limit beyond normal GitHub CDN
    fetch behavior, and a permanent/stable URL per release tag.

  ESPN public endpoints (rejected for this use): the "hidden" ESPN API this
    codebase's T4 live-polling code touches (ds02_nba_live.py) actually goes
    through nba_api.live, not ESPN directly, so there was no existing
    ESPN-consumption precedent to follow here in the first place. ESPN's
    own API is unofficial, undocumented, has no published ToS, no published
    rate limit, and was reported publicly discontinued by ESPN in 2018 —
    appropriate only for the low-volume, best-effort live-state polling this
    codebase already does elsewhere, not for a new batch pregame C1 module
    that needs a documented, licensed, stable contract.

Two release tags are consumed:
  schedules   -> games.csv         (one file, ALL seasons incl. unplayed games;
                                     includes pre-computed home_rest/away_rest)
  stats_team  -> stats_team_week_<season>.csv (one file PER SEASON; per-team
                                     per-week EPA stats; does not exist yet
                                     for a season that hasn't started — see
                                     cold-start handling below)

IF-C1-C2 NFL contract
----------------------
Schedule   : one row per scheduled game. Columns: _NFL_SCHEDULE_COLUMNS.
             home_score/away_score are null for unplayed games (by design —
             this is the schedule, not a results feed).
Team stats : one row per team-game. Columns: _NFL_TEAM_STATS_COLUMNS.
             off_epa = passing_epa + rushing_epa (EPA is the standard
             modern NFL offensive-efficiency proxy; directly available from
             nflverse, no derivation risk). Defensive efficiency (EPA
             allowed) is computed downstream in NFLTeamStatsStore by
             joining a team's row to its opponent's row for the same
             game_id — the NFL analogue of MLBTeamStatsStore.build_from_games()
             deriving runs_allowed from the opposing team's runs scored.

Cold start (Week 1, current season has zero completed games)
--------------------------------------------------------------
fetch_team_stats() for a season whose file does not yet exist on nflverse
(confirmed empirically 2026-09-07: stats_team_week_2026.csv 404s, current
season hasn't started) returns (True, empty DataFrame) with a WARNING log —
this is an EXPECTED soft case, not a kill-switch failure: the season simply
has not produced any team-game rows yet. ok=False is reserved for a genuine
fetch failure (network exhaustion, non-404 HTTP error) on a request that
SHOULD have succeeded.

The season-file-missing case is not a cold-start gap by itself, because
NFLTeamStatsStore's queries operate on strict prior-date ordering across
ALL loaded seasons, not scoped to "this season only" — see that module's
docstring for how the Week 1 carryover behavior actually falls out of that
design, without any special-cased branch here.

Rest days / home-away
-----------------------
Both come directly off the schedule fetch (home_rest/away_rest,
home_team/away_team) — nflverse pre-computes rest days, so there is no
derivation step and no cold-start gap for these two features: they are
present even for a fully unplayed future game (confirmed empirically on
2026 Week 1 rows, which have null scores but populated rest values).

Out of scope (explicit, per GG-253 task fence)
-------------------------------------------------
Strength-of-schedule is explicitly NOT built here — noted as a follow-on
only. Model fitting (EXP-026) is not this module's job.

All public methods return (ok: bool, data).
ok=False is a terminal failure — caller MUST trigger the kill switch (NFR-03).
"""

from __future__ import annotations

import io
import time
import uuid
from datetime import datetime, timezone

import pandas as pd
import requests

from prediction_market_bot.c6_audit_logger.audit_logger import AuditLogger
from typing import Any

COMPONENT = "C1_NFL"

NFLVERSE_GAMES_URL = (
    "https://github.com/nflverse/nflverse-data/releases/download/schedules/games.csv"
)
NFLVERSE_TEAM_STATS_URL_TEMPLATE = (
    "https://github.com/nflverse/nflverse-data/releases/download/stats_team/"
    "stats_team_week_{season}.csv"
)

# nflverse-data assets are static GitHub Release files (CDN-backed), not a
# live API — no documented per-request rate limit exists, but a modest
# throttle is kept for politeness and to match this codebase's existing
# convention (MLB Stats API uses DEFAULT_REQUEST_DELAY_S = 0.6).
DEFAULT_REQUEST_DELAY_S = 0.5
MAX_RETRIES = 3
RETRY_DELAY_S = 1.0
REQUEST_TIMEOUT_S = 20

# IF-C1-C2 NFL schedule schema: one row per scheduled game (all seasons).
_NFL_SCHEDULE_COLUMNS: list[str] = [
    "game_id",
    "season",
    "game_type",
    "week",
    "gameday",
    "home_team",
    "away_team",
    "home_score",
    "away_score",
    "home_rest",
    "away_rest",
]

# IF-C1-C2 NFL team-game stats schema: one row per team-game.
_NFL_TEAM_STATS_COLUMNS: list[str] = [
    "season",
    "week",
    "season_type",
    "game_id",
    "team",
    "opponent_team",
    "off_epa",
]

# T-581 (EXP-027 EPA-splits candidate): opt-in schema that additionally RETAINS
# the raw passing_epa / rushing_epa columns instead of collapsing them into
# off_epa alone. Default fetch behaviour is unchanged (include_splits=False)
# -- the incumbent EXP-027 path never sees these columns.
_NFL_TEAM_STATS_SPLIT_COLUMNS: list[str] = _NFL_TEAM_STATS_COLUMNS + [
    "passing_epa",
    "rushing_epa",
]

_NFL_RAW_TEAM_STATS_SOURCE_COLUMNS = [
    "season", "week", "season_type", "game_id", "team", "opponent_team",
    "passing_epa", "rushing_epa",
]


class NFLIngestionClient:
    """Fetch NFL schedule and team-efficiency data from nflverse-data.

    All public methods return (ok: bool, data) where ok=False signals a
    terminal fetch failure. Callers must check ok and trigger the kill
    switch on False (NFR-03) — EXCEPT fetch_team_stats()'s documented
    404/cold-start case, which returns ok=True with an empty DataFrame
    (see module docstring).

    Parameters
    ----------
    logger:
        AuditLogger instance (C6).
    snapshot_id:
        DS snapshot anchor for the ingestion run (e.g. "SNAP-001").
    request_delay:
        Minimum seconds between successive HTTP requests (rate-limit floor).
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
        self._last_request_ts: float | None = None

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _throttle(self) -> None:
        if self._last_request_ts is not None:
            elapsed = time.monotonic() - self._last_request_ts
            gap = self._delay - elapsed
            if gap > 0:
                time.sleep(gap)
        self._last_request_ts = time.monotonic()

    def _run_id(self) -> str:
        return f"C1NFL-{uuid.uuid4().hex[:8]}"

    def _utc_now_iso(self) -> str:
        return datetime.now(timezone.utc).isoformat()

    def _get_csv(self, url: str) -> tuple[int | None, pd.DataFrame | None]:
        """HTTP GET a CSV asset with throttle + linear retry.

        Returns (status_code, df). status_code is None only if every retry
        was exhausted on a network-level exception with no response at all.
        df is None whenever status_code != 200. 404 is returned as-is
        (not retried) so callers can distinguish "not found yet" (an
        expected pre-season condition for the per-season team-stats file)
        from a genuine fetch failure.
        """
        for attempt in range(MAX_RETRIES):
            self._throttle()
            try:
                resp = requests.get(url, timeout=REQUEST_TIMEOUT_S)
                if resp.status_code == 404:
                    return 404, None
                resp.raise_for_status()
                df = pd.read_csv(io.StringIO(resp.text), low_memory=False)
                return 200, df
            except requests.HTTPError as exc:
                code = exc.response.status_code if exc.response is not None else None
                if code is not None and code < 500:
                    return code, None  # 4xx (non-404) — no retry
                if attempt < MAX_RETRIES - 1:
                    time.sleep(RETRY_DELAY_S * (attempt + 1))
            except requests.RequestException:
                if attempt < MAX_RETRIES - 1:
                    time.sleep(RETRY_DELAY_S * (attempt + 1))
        return None, None

    # ------------------------------------------------------------------
    # Normalization
    # ------------------------------------------------------------------

    def _normalize_schedule_df(self, raw: pd.DataFrame) -> pd.DataFrame:
        missing = [c for c in _NFL_SCHEDULE_COLUMNS if c not in raw.columns]
        if missing:
            raise ValueError(f"nflverse games.csv missing expected columns: {missing}")
        df = raw[_NFL_SCHEDULE_COLUMNS].copy()
        df["gameday"] = pd.to_datetime(df["gameday"], errors="coerce").dt.date
        return df

    def _normalize_team_stats_df(
        self, raw: pd.DataFrame, include_splits: bool = False,
    ) -> pd.DataFrame:
        missing = [c for c in _NFL_RAW_TEAM_STATS_SOURCE_COLUMNS if c not in raw.columns]
        if missing:
            raise ValueError(f"nflverse stats_team_week CSV missing expected columns: {missing}")
        df = raw[_NFL_RAW_TEAM_STATS_SOURCE_COLUMNS].copy()
        df["off_epa"] = df["passing_epa"] + df["rushing_epa"]
        return df[_NFL_TEAM_STATS_SPLIT_COLUMNS if include_splits else _NFL_TEAM_STATS_COLUMNS]

    # ------------------------------------------------------------------
    # Public API — schedule (rest days + home/away live here)
    # ------------------------------------------------------------------

    def fetch_schedule(
        self,
        seasons: list[int] | None = None,
        session_id: str | None = None,
    ) -> tuple[bool, pd.DataFrame]:
        """Fetch the full nflverse schedule (games.csv), one row per game.

        Includes home_rest/away_rest and home_team/away_team — nflverse
        pre-computes rest days for every scheduled game including unplayed
        future games, so no additional derivation is needed for those two
        minimum-feature-set items.

        seasons, if given, filters the result to those season years
        (the source file always contains all seasons; filtering is local).
        home_score/away_score are null for games not yet played.

        Returns (True, DataFrame) on success. Returns (False, empty
        DataFrame) on fetch failure — caller triggers kill switch. This
        file is expected to always exist (unlike the per-season team-stats
        file), so any non-200 status here is treated as a real failure,
        not a cold-start case.
        """
        run_id = self._run_id()
        self._logger.log(
            COMPONENT, "schedule_fetch_start",
            payload={"seasons": seasons},
            session_id=session_id, snapshot_id=self._snapshot_id, severity="INFO",
        )
        status, raw = self._get_csv(NFLVERSE_GAMES_URL)
        if status != 200 or raw is None:
            self._logger.log(
                COMPONENT, "schedule_fetch_error",
                payload={"status": status},
                session_id=session_id, snapshot_id=self._snapshot_id, severity="ERROR",
            )
            return False, pd.DataFrame(columns=_NFL_SCHEDULE_COLUMNS)

        try:
            df = self._normalize_schedule_df(raw)
        except ValueError as exc:
            self._logger.log(
                COMPONENT, "schedule_fetch_error",
                payload={"error": str(exc)},
                session_id=session_id, snapshot_id=self._snapshot_id, severity="ERROR",
            )
            return False, pd.DataFrame(columns=_NFL_SCHEDULE_COLUMNS)

        if seasons is not None:
            df = df[df["season"].isin(seasons)].reset_index(drop=True)

        self._logger.log(
            COMPONENT, "schedule_fetch_complete",
            payload={"seasons": seasons, "n_games": len(df), "run_id": run_id},
            session_id=session_id, snapshot_id=self._snapshot_id, severity="INFO",
        )
        return True, df

    # ------------------------------------------------------------------
    # Public API — team efficiency stats (offense/defense EPA source)
    # ------------------------------------------------------------------

    def fetch_team_stats(
        self,
        season: int,
        session_id: str | None = None,
        include_splits: bool = False,
    ) -> tuple[bool, pd.DataFrame]:
        """Fetch per-team-game EPA stats for one season.

        include_splits=True (T-581) additionally retains passing_epa /
        rushing_epa; default False keeps the original IF-C1-C2 schema.

        off_epa = passing_epa + rushing_epa (standard modern NFL offensive
        efficiency proxy). Defensive EPA-allowed is NOT computed here — it
        requires joining a team's row to its opponent's row for the same
        game, which NFLTeamStatsStore does when building its store.

        Cold start: if the season's file does not exist yet on nflverse
        (HTTP 404 — confirmed empirically for the not-yet-started current
        season), this is an EXPECTED condition, not a failure: returns
        (True, empty DataFrame) with a WARNING log. Any other non-200
        status is a genuine fetch failure: returns (False, empty DataFrame).
        """
        run_id = self._run_id()
        self._logger.log(
            COMPONENT, "team_stats_fetch_start",
            payload={"season": season},
            session_id=session_id, snapshot_id=self._snapshot_id, severity="INFO",
        )
        url = NFLVERSE_TEAM_STATS_URL_TEMPLATE.format(season=season)
        status, raw = self._get_csv(url)

        if status == 404:
            self._logger.log(
                COMPONENT, "team_stats_not_yet_available",
                payload={"season": season, "note": "season has not started / no games completed yet"},
                session_id=session_id, snapshot_id=self._snapshot_id, severity="WARNING",
            )
            return True, pd.DataFrame(columns=_NFL_TEAM_STATS_COLUMNS)

        if status != 200 or raw is None:
            self._logger.log(
                COMPONENT, "team_stats_fetch_error",
                payload={"season": season, "status": status},
                session_id=session_id, snapshot_id=self._snapshot_id, severity="ERROR",
            )
            return False, pd.DataFrame(columns=_NFL_TEAM_STATS_COLUMNS)

        try:
            df = self._normalize_team_stats_df(raw, include_splits=include_splits)
        except ValueError as exc:
            self._logger.log(
                COMPONENT, "team_stats_fetch_error",
                payload={"season": season, "error": str(exc)},
                session_id=session_id, snapshot_id=self._snapshot_id, severity="ERROR",
            )
            return False, pd.DataFrame(columns=_NFL_TEAM_STATS_COLUMNS)

        self._logger.log(
            COMPONENT, "team_stats_fetch_complete",
            payload={"season": season, "n_rows": len(df), "run_id": run_id},
            session_id=session_id, snapshot_id=self._snapshot_id, severity="INFO",
        )
        return True, df

    def fetch_team_stats_bulk(
        self,
        seasons: list[int],
        session_id: str | None = None,
        include_splits: bool = False,
    ) -> tuple[bool, pd.DataFrame]:
        """Fetch team-game EPA stats for multiple seasons and concatenate.

        include_splits (T-581): forwarded to fetch_team_stats(); default False.

        Returns (False, data) if ANY individual fetch fails for a reason
        OTHER than the documented 404/cold-start case (partial data is
        still returned so callers can inspect; the False signals a
        kill-switch condition). A 404 for one season among several does
        NOT flip this to False — it is folded in as an empty frame for
        that season, per fetch_team_stats()'s own contract.
        """
        frames: list[pd.DataFrame] = []
        any_error = False
        for season in seasons:
            ok, df = self.fetch_team_stats(season, session_id, include_splits=include_splits)
            if not ok:
                any_error = True
            elif not df.empty:
                frames.append(df)
        if not frames:
            return not any_error, pd.DataFrame(
                columns=_NFL_TEAM_STATS_SPLIT_COLUMNS if include_splits else _NFL_TEAM_STATS_COLUMNS
            )
        return not any_error, pd.concat(frames, ignore_index=True)
