"""
C1: Signal Ingestion — MLB via MLB Stats API (api.mlb.com)
===========================================================
Component:    C1 (Signal Ingestion)
Sport:        MLB
Status:       CANONICAL (T-181 2026-06-23)
Upstream:     MLB Stats API (statsapi.mlb.com; free; unauthenticated)
Downstream:   C2 Feature Store (IF-C1-C2 MLB batter/pitcher schemas)
ADR:          ADR-0031 (multi-sport C1 extension)

IF-C1-C2 MLB contract
----------------------
Batter game log   : one row per player-game. Columns: _MLB_BATTER_COLUMNS.
Pitcher game log  : one row per pitcher-game. Columns: _MLB_PITCHER_COLUMNS.
Game starters dict: gamePk (int) → {home_sp_id, home_sp_name, away_sp_id,
                    away_sp_name, venue_id, venue_name, home_team_abbr,
                    away_team_abbr, home_team_id, away_team_id}.
Completed games   : one row per game with {game_id, game_date, home_team_abbr,
                    away_team_abbr, home_team_id, away_team_id, home_runs,
                    away_runs}. Used to populate MLBTeamStatsStore.

All public methods return (ok: bool, data).
ok=False is a terminal failure — caller MUST trigger the kill switch (NFR-03).
"""

from __future__ import annotations

import time
import uuid
from datetime import datetime, timezone

import pandas as pd
import requests

from prediction_market_bot.c6_audit_logger.audit_logger import AuditLogger
from typing import Any

COMPONENT = "C1_MLB"
MLB_BASE_URL = "https://statsapi.mlb.com"

DEFAULT_REQUEST_DELAY_S = 0.6  # respect MLB Stats API rate limits
MAX_RETRIES = 3
RETRY_DELAY_S = 1.0
REQUEST_TIMEOUT_S = 15

# IF-C1-C2 MLB batter schema: one row per player-game.
_MLB_BATTER_COLUMNS: list[str] = [
    "player_id",
    "player_name",
    "team_id",
    "team_abbreviation",
    "game_id",
    "game_date",
    "season",
    "season_type",
    "matchup",
    "is_home_game",
    "opponent_team_abbr",
    "ab",
    "h",
    "doubles",
    "triples",
    "hr",
    "rbi",
    "bb",
    "k",
    "hbp",
    "sf",
    "snapshot_id",
    "ingestion_run_id",
    "ingested_at",
]

# IF-C1-C2 MLB pitcher schema: one row per pitcher-game appearance.
_MLB_PITCHER_COLUMNS: list[str] = [
    "player_id",
    "player_name",
    "team_id",
    "team_abbreviation",
    "game_id",
    "game_date",
    "season",
    "season_type",
    "matchup",
    "is_home_game",
    "opponent_team_abbr",
    "ip",
    "h_allowed",
    "er",
    "bb",
    "k",
    "hr_allowed",
    "is_start",
    "snapshot_id",
    "ingestion_run_id",
    "ingested_at",
]

# Hardcoded fallback team ID → abbreviation map (MLB; correct as of 2026-06-23).
# Used only if the live /api/v1/teams endpoint is unreachable at init.
_FALLBACK_TEAM_ABBR: dict[int, str] = {
    108: "LAA", 109: "AZ",  110: "BAL", 111: "BOS", 112: "CHC",
    113: "CIN", 114: "CLE", 115: "COL", 116: "DET", 117: "HOU",
    118: "KC",  119: "LAD", 120: "WSH", 121: "NYM", 133: "ATH",
    134: "PIT", 135: "SD",  136: "SEA", 137: "SF",  138: "STL",
    139: "TB",  140: "TEX", 141: "TOR", 142: "MIN", 143: "PHI",
    144: "ATL", 145: "CWS", 146: "MIA", 147: "NYY", 158: "MIL",
}

def _ip_to_decimal(ip_raw: str | float) -> float:
    """Convert MLB Stats API inningsPitched to decimal innings.

    The API uses baseball notation: "5.2" = 5 innings + 2 outs = 5⅔ = 5.667.
    Decimal digits 0/1/2 represent 0, 1/3, 2/3 of an inning respectively.
    Any other decimal digit (should not occur) is treated as 0 outs.
    """
    try:
        s = str(ip_raw).strip()
        if "." in s:
            whole_s, frac_s = s.split(".", 1)
            whole = int(whole_s) if whole_s else 0
            outs = int(frac_s[0]) if frac_s else 0  # only first digit is outs (0, 1, 2)
            return float(whole) + outs / 3.0
        return float(s)
    except (ValueError, TypeError):
        return 0.0


_GAME_TYPE_LABELS: dict[str, str] = {
    "R": "Regular Season",
    "P": "Postseason",
    "D": "Postseason",
    "L": "Postseason",
    "W": "Postseason",
    "F": "Postseason",
    "S": "Spring Training",
    "E": "Exhibition",
}


class MLBIngestionClient:
    """Fetch MLB player game log data from the MLB Stats API.

    All public methods return (ok: bool, data) where ok=False signals a terminal
    failure. Callers must check ok and trigger the kill switch on False (NFR-03).

    Parameters
    ----------
    logger:
        AuditLogger instance (C6).
    snapshot_id:
        DS snapshot anchor for the ingestion run (e.g. "SNAP-001").
    request_delay:
        Minimum seconds between successive HTTP requests (rate-limit floor).
    _team_abbr_map:
        If provided, skips the live /api/v1/teams lookup. For testing only.
    """

    def __init__(
        self,
        logger: AuditLogger,
        snapshot_id: str,
        request_delay: float = DEFAULT_REQUEST_DELAY_S,
        _team_abbr_map: dict[int, str] | None = None,
    ) -> None:
        self._logger = logger
        self._snapshot_id = snapshot_id
        self._delay = request_delay
        self._last_request_ts: float | None = None
        if _team_abbr_map is not None:
            self._team_abbr_map: dict[int, str] = _team_abbr_map
        else:
            self._team_abbr_map = self._build_team_abbr_map()

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
        return f"C1MLB-{uuid.uuid4().hex[:8]}"

    def _utc_now_iso(self) -> str:
        return datetime.now(timezone.utc).isoformat()

    def _build_team_abbr_map(self) -> dict[int, str]:
        """Fetch live team abbreviations; fall back to static map on any failure."""
        try:
            resp = requests.get(
                f"{MLB_BASE_URL}/api/v1/teams",
                params={"sportId": 1},
                timeout=REQUEST_TIMEOUT_S,
            )
            resp.raise_for_status()
            data = resp.json()
            result: dict[int, str] = {}
            for team in data.get("teams", []):
                team_id = team.get("id")
                abbr = team.get("abbreviation")
                if team_id and abbr:
                    result[int(team_id)] = str(abbr)
            if result:
                return result
        except Exception:
            pass
        return dict(_FALLBACK_TEAM_ABBR)

    def _get(self, url: str, params: dict[str, Any] | None = None) -> dict[str, Any] | None:
        """HTTP GET with throttle and linear retry. Returns parsed JSON or None."""
        for attempt in range(MAX_RETRIES):
            self._throttle()
            try:
                resp = requests.get(url, params=params, timeout=REQUEST_TIMEOUT_S)
                resp.raise_for_status()
                return resp.json()  # type: ignore[no-any-return]
            except requests.HTTPError as exc:
                if exc.response is not None and exc.response.status_code < 500:
                    return None  # 4xx — no retry
                if attempt < MAX_RETRIES - 1:
                    time.sleep(RETRY_DELAY_S * (attempt + 1))
            except requests.RequestException:
                if attempt < MAX_RETRIES - 1:
                    time.sleep(RETRY_DELAY_S * (attempt + 1))
        return None

    def _team_abbr(self, team_id: int) -> str:
        """Return abbreviation for team_id; fallback to 'T{id}' if unmapped."""
        return self._team_abbr_map.get(int(team_id), f"T{team_id}")

    def _norm_season_type(self, api_code: str) -> str:
        return _GAME_TYPE_LABELS.get(api_code, api_code)

    # ------------------------------------------------------------------
    # Normalization
    # ------------------------------------------------------------------

    def _normalize_batter_df(
        self,
        splits: list[dict[str, Any]],
        player_id: int,
        player_name: str,
        run_id: str,
    ) -> pd.DataFrame:
        rows = []
        now_iso = self._utc_now_iso()
        for split in splits:
            stat = split.get("stat", {})
            team = split.get("team", {})
            opp = split.get("opponent", {})
            game = split.get("game", {})
            is_home = bool(split.get("isHome", False))
            team_id = team.get("id")
            opp_id = opp.get("id")
            team_abbr = self._team_abbr(team_id) if team_id is not None else ""
            opp_abbr = self._team_abbr(opp_id) if opp_id is not None else ""
            game_type = split.get("gameType", "R")
            matchup = (
                f"{team_abbr} vs. {opp_abbr}" if is_home
                else f"{team_abbr} @ {opp_abbr}"
            )
            rows.append({
                "player_id": player_id,
                "player_name": player_name,
                "team_id": team_id,
                "team_abbreviation": team_abbr,
                "game_id": game.get("gamePk"),
                "game_date": split.get("date") or None,
                "season": split.get("season", ""),
                "season_type": self._norm_season_type(game_type),
                "matchup": matchup,
                "is_home_game": 1 if is_home else 0,
                "opponent_team_abbr": opp_abbr,
                "ab": stat.get("atBats", 0),
                "h": stat.get("hits", 0),
                "doubles": stat.get("doubles", 0),
                "triples": stat.get("triples", 0),
                "hr": stat.get("homeRuns", 0),
                "rbi": stat.get("rbi", 0),
                "bb": stat.get("baseOnBalls", 0),
                "k": stat.get("strikeOuts", 0),
                "hbp": stat.get("hitByPitch", 0),
                "sf": stat.get("sacFlies", 0),
                "snapshot_id": self._snapshot_id,
                "ingestion_run_id": run_id,
                "ingested_at": now_iso,
            })
        if not rows:
            return pd.DataFrame(columns=_MLB_BATTER_COLUMNS)
        df = pd.DataFrame(rows)
        df["game_date"] = pd.to_datetime(df["game_date"], errors="coerce").dt.date
        return df[_MLB_BATTER_COLUMNS]

    def _normalize_pitcher_df(
        self,
        splits: list[dict[str, Any]],
        player_id: int,
        player_name: str,
        run_id: str,
    ) -> pd.DataFrame:
        rows = []
        now_iso = self._utc_now_iso()
        for split in splits:
            stat = split.get("stat", {})
            team = split.get("team", {})
            opp = split.get("opponent", {})
            game = split.get("game", {})
            is_home = bool(split.get("isHome", False))
            team_id = team.get("id")
            opp_id = opp.get("id")
            team_abbr = self._team_abbr(team_id) if team_id is not None else ""
            opp_abbr = self._team_abbr(opp_id) if opp_id is not None else ""
            game_type = split.get("gameType", "R")
            matchup = (
                f"{team_abbr} vs. {opp_abbr}" if is_home
                else f"{team_abbr} @ {opp_abbr}"
            )
            ip = _ip_to_decimal(stat.get("inningsPitched", "0.0"))
            rows.append({
                "player_id": player_id,
                "player_name": player_name,
                "team_id": team_id,
                "team_abbreviation": team_abbr,
                "game_id": game.get("gamePk"),
                "game_date": split.get("date") or None,
                "season": split.get("season", ""),
                "season_type": self._norm_season_type(game_type),
                "matchup": matchup,
                "is_home_game": 1 if is_home else 0,
                "opponent_team_abbr": opp_abbr,
                "ip": ip,
                "h_allowed": stat.get("hits", 0),
                "er": stat.get("earnedRuns", 0),
                "bb": stat.get("baseOnBalls", 0),
                "k": stat.get("strikeOuts", 0),
                "hr_allowed": stat.get("homeRuns", 0),
                "is_start": 1 if stat.get("gamesStarted", 0) >= 1 else 0,
                "snapshot_id": self._snapshot_id,
                "ingestion_run_id": run_id,
                "ingested_at": now_iso,
            })
        if not rows:
            return pd.DataFrame(columns=_MLB_PITCHER_COLUMNS)
        df = pd.DataFrame(rows)
        df["game_date"] = pd.to_datetime(df["game_date"], errors="coerce").dt.date
        return df[_MLB_PITCHER_COLUMNS]

    # ------------------------------------------------------------------
    # Public API — batter game log
    # ------------------------------------------------------------------

    def fetch_batter_game_log(
        self,
        player_id: int,
        season: int | str,
        season_type: str = "R",
        session_id: str | None = None,
    ) -> tuple[bool, pd.DataFrame]:
        """Fetch hitting game log for one batter.

        Returns (True, DataFrame) on success (empty DataFrame if no games).
        Returns (False, empty DataFrame) on HTTP failure — caller triggers kill switch.
        """
        run_id = self._run_id()
        self._logger.log(
            COMPONENT,
            "batter_game_log_fetch_start",
            payload={"player_id": player_id, "season": str(season), "season_type": season_type},
            session_id=session_id,
            snapshot_id=self._snapshot_id,
            severity="INFO",
        )
        data = self._get(
            f"{MLB_BASE_URL}/api/v1/people/{player_id}/stats",
            params={"stats": "gameLog", "group": "hitting", "season": str(season), "gameType": season_type},
        )
        if data is None:
            self._logger.log(
                COMPONENT,
                "batter_game_log_fetch_error",
                payload={"player_id": player_id, "season": str(season)},
                session_id=session_id,
                snapshot_id=self._snapshot_id,
                severity="ERROR",
            )
            return False, pd.DataFrame(columns=_MLB_BATTER_COLUMNS)

        raw_stats = data.get("stats", [])
        splits = raw_stats[0].get("splits", []) if raw_stats else []

        if not splits:
            self._logger.log(
                COMPONENT,
                "batter_game_log_empty",
                payload={"player_id": player_id, "season": str(season)},
                session_id=session_id,
                snapshot_id=self._snapshot_id,
                severity="WARNING",
            )
            return True, pd.DataFrame(columns=_MLB_BATTER_COLUMNS)

        player_name = splits[0].get("player", {}).get("fullName", f"player_{player_id}")
        df = self._normalize_batter_df(splits, player_id, player_name, run_id)
        self._logger.log(
            COMPONENT,
            "batter_game_log_fetch_complete",
            payload={"player_id": player_id, "season": str(season), "n_games": len(df)},
            session_id=session_id,
            snapshot_id=self._snapshot_id,
            severity="INFO",
        )
        return True, df

    def fetch_batter_game_logs_bulk(
        self,
        player_ids: list[int],
        season: int | str,
        season_type: str = "R",
        session_id: str | None = None,
    ) -> tuple[bool, pd.DataFrame]:
        """Fetch hitting game logs for multiple batters and concatenate.

        Returns (False, data) if ANY individual fetch fails (partial data is still
        returned so callers can inspect; the False signals a kill-switch condition).
        """
        frames: list[pd.DataFrame] = []
        any_error = False
        for pid in player_ids:
            ok, df = self.fetch_batter_game_log(pid, season, season_type, session_id)
            if not ok:
                any_error = True
            elif not df.empty:
                frames.append(df)
        if not frames:
            return not any_error, pd.DataFrame(columns=_MLB_BATTER_COLUMNS)
        return not any_error, pd.concat(frames, ignore_index=True)

    # ------------------------------------------------------------------
    # Public API — pitcher game log
    # ------------------------------------------------------------------

    def fetch_pitcher_game_log(
        self,
        player_id: int,
        season: int | str,
        season_type: str = "R",
        session_id: str | None = None,
    ) -> tuple[bool, pd.DataFrame]:
        """Fetch pitching game log for one pitcher.

        is_start==1 rows are starting appearances; is_start==0 are relief.
        """
        run_id = self._run_id()
        self._logger.log(
            COMPONENT,
            "pitcher_game_log_fetch_start",
            payload={"player_id": player_id, "season": str(season), "season_type": season_type},
            session_id=session_id,
            snapshot_id=self._snapshot_id,
            severity="INFO",
        )
        data = self._get(
            f"{MLB_BASE_URL}/api/v1/people/{player_id}/stats",
            params={"stats": "gameLog", "group": "pitching", "season": str(season), "gameType": season_type},
        )
        if data is None:
            self._logger.log(
                COMPONENT,
                "pitcher_game_log_fetch_error",
                payload={"player_id": player_id, "season": str(season)},
                session_id=session_id,
                snapshot_id=self._snapshot_id,
                severity="ERROR",
            )
            return False, pd.DataFrame(columns=_MLB_PITCHER_COLUMNS)

        raw_stats = data.get("stats", [])
        splits = raw_stats[0].get("splits", []) if raw_stats else []

        if not splits:
            self._logger.log(
                COMPONENT,
                "pitcher_game_log_empty",
                payload={"player_id": player_id, "season": str(season)},
                session_id=session_id,
                snapshot_id=self._snapshot_id,
                severity="WARNING",
            )
            return True, pd.DataFrame(columns=_MLB_PITCHER_COLUMNS)

        player_name = splits[0].get("player", {}).get("fullName", f"pitcher_{player_id}")
        df = self._normalize_pitcher_df(splits, player_id, player_name, run_id)
        self._logger.log(
            COMPONENT,
            "pitcher_game_log_fetch_complete",
            payload={"player_id": player_id, "season": str(season), "n_games": len(df)},
            session_id=session_id,
            snapshot_id=self._snapshot_id,
            severity="INFO",
        )
        return True, df

    def fetch_pitcher_game_logs_bulk(
        self,
        player_ids: list[int],
        season: int | str,
        season_type: str = "R",
        session_id: str | None = None,
    ) -> tuple[bool, pd.DataFrame]:
        """Fetch pitching game logs for multiple pitchers and concatenate."""
        frames: list[pd.DataFrame] = []
        any_error = False
        for pid in player_ids:
            ok, df = self.fetch_pitcher_game_log(pid, season, season_type, session_id)
            if not ok:
                any_error = True
            elif not df.empty:
                frames.append(df)
        if not frames:
            return not any_error, pd.DataFrame(columns=_MLB_PITCHER_COLUMNS)
        return not any_error, pd.concat(frames, ignore_index=True)

    # ------------------------------------------------------------------
    # Public API — game starters (for C2 pitcher feature join)
    # ------------------------------------------------------------------

    def fetch_game_starters(
        self,
        game_date: str,
        session_id: str | None = None,
    ) -> tuple[bool, dict[int, dict[str, Any]]]:
        """Return probable starting pitchers for all games on game_date.

        Returns (ok, {gamePk: {home_sp_id, home_sp_name, away_sp_id, away_sp_name,
                                venue_id, venue_name, home_team_id, home_team_abbr,
                                away_team_id, away_team_abbr}}).

        Probable pitchers may be None before lineups are posted. C2 must handle
        None sp_id gracefully (fall back to league-average pitcher features).
        ok=False on HTTP failure; ok=True with empty dict if no games scheduled.
        """
        self._logger.log(
            COMPONENT,
            "game_starters_fetch_start",
            payload={"game_date": game_date},
            session_id=session_id,
            snapshot_id=self._snapshot_id,
            severity="INFO",
        )
        data = self._get(
            f"{MLB_BASE_URL}/api/v1/schedule",
            # Note: "venue" hydrate returns 406 from DigitalOcean/Fastly CDN.
            # venue_id/venue_name will be absent; park_factor_hits uses team abbr
            # from static lookup so venue data is not needed at inference time.
            params={"sportId": 1, "date": game_date, "hydrate": "probablePitcher,team"},
        )
        if data is None:
            self._logger.log(
                COMPONENT,
                "game_starters_fetch_error",
                payload={"game_date": game_date},
                session_id=session_id,
                snapshot_id=self._snapshot_id,
                severity="ERROR",
            )
            return False, {}

        result: dict[int, dict[str, Any]] = {}
        for date_block in data.get("dates", []):
            for game in date_block.get("games", []):
                game_pk = game.get("gamePk")
                if game_pk is None:
                    continue
                teams = game.get("teams", {})
                home = teams.get("home", {})
                away = teams.get("away", {})
                home_sp = home.get("probablePitcher") or {}
                away_sp = away.get("probablePitcher") or {}
                venue = game.get("venue") or {}
                home_team = home.get("team") or {}
                away_team = away.get("team") or {}
                home_team_id = home_team.get("id")
                away_team_id = away_team.get("id")
                result[int(game_pk)] = {
                    "home_sp_id": home_sp.get("id"),
                    "home_sp_name": home_sp.get("fullName"),
                    "away_sp_id": away_sp.get("id"),
                    "away_sp_name": away_sp.get("fullName"),
                    "venue_id": venue.get("id"),
                    "venue_name": venue.get("name"),
                    "home_team_id": home_team_id,
                    "home_team_abbr": self._team_abbr(home_team_id) if home_team_id is not None else "",
                    "away_team_id": away_team_id,
                    "away_team_abbr": self._team_abbr(away_team_id) if away_team_id is not None else "",
                }

        self._logger.log(
            COMPONENT,
            "game_starters_fetch_complete",
            payload={"game_date": game_date, "n_games": len(result)},
            session_id=session_id,
            snapshot_id=self._snapshot_id,
            severity="INFO",
        )
        return True, result

    # ------------------------------------------------------------------
    # Public API — confirmed batting lineups (for T2 same-day overlay)
    # ------------------------------------------------------------------

    def fetch_lineups(
        self,
        game_date: str,
        session_id: str | None = None,
    ) -> tuple[bool, dict[int, dict[str, Any]]]:
        """Return confirmed batting lineups for all games on game_date.

        Returns (ok, {player_id: {"batting_slot": N, "game_pk": N, "team_id": N}}).
        batting_slot is 1-indexed (1 = leadoff, 9 = last batter).
        Returns empty dict if lineups not yet posted (typically posted
        3–4h before first pitch; safe to call and get empty result).
        ok=False on HTTP failure; ok=True with empty dict if none available.
        """
        self._logger.log(
            COMPONENT,
            "lineups_fetch_start",
            payload={"game_date": game_date},
            session_id=session_id,
            snapshot_id=self._snapshot_id,
            severity="INFO",
        )
        data = self._get(
            f"{MLB_BASE_URL}/api/v1/schedule",
            params={"sportId": 1, "date": game_date, "hydrate": "lineups,team"},
        )
        if data is None:
            self._logger.log(
                COMPONENT,
                "lineups_fetch_error",
                payload={"game_date": game_date},
                session_id=session_id,
                snapshot_id=self._snapshot_id,
                severity="ERROR",
            )
            return False, {}

        result: dict[int, dict[str, Any]] = {}
        for date_block in data.get("dates", []):
            for game in date_block.get("games", []):
                game_pk = game.get("gamePk")
                if game_pk is None:
                    continue
                teams = game.get("teams", {})
                home_team_id = (teams.get("home", {}).get("team") or {}).get("id")
                away_team_id = (teams.get("away", {}).get("team") or {}).get("id")

                lineups = game.get("lineups") or {}
                for side, team_id in (("homePlayers", home_team_id), ("awayPlayers", away_team_id)):
                    for slot_idx, player in enumerate(lineups.get(side, []), start=1):
                        pid = player.get("id")
                        if pid is not None:
                            result[int(pid)] = {
                                "batting_slot": slot_idx,
                                "game_pk": int(game_pk),
                                "team_id": team_id,
                            }

        self._logger.log(
            COMPONENT,
            "lineups_fetch_complete",
            payload={"game_date": game_date, "n_players": len(result)},
            session_id=session_id,
            snapshot_id=self._snapshot_id,
            severity="INFO",
        )
        return True, result

    # ------------------------------------------------------------------
    # Public API — completed game scores (for MLBTeamStatsStore population)
    # ------------------------------------------------------------------

    def fetch_completed_games(
        self,
        start_date: str,
        end_date: str,
        session_id: str | None = None,
    ) -> tuple[bool, pd.DataFrame]:
        """Return final scores for all completed games in [start_date, end_date].

        Output columns: game_id, game_date, home_team_id, home_team_abbr,
        away_team_id, away_team_abbr, home_runs, away_runs.

        Used by C1 run scripts to populate MLBTeamStatsStore with per-team
        runs scored / runs allowed history.
        """
        self._logger.log(
            COMPONENT,
            "completed_games_fetch_start",
            payload={"start_date": start_date, "end_date": end_date},
            session_id=session_id,
            snapshot_id=self._snapshot_id,
            severity="INFO",
        )
        data = self._get(
            f"{MLB_BASE_URL}/api/v1/schedule",
            params={
                "sportId": 1,
                "startDate": start_date,
                "endDate": end_date,
                "hydrate": "linescore,team",
                "gameType": "R",
            },
        )
        if data is None:
            self._logger.log(
                COMPONENT,
                "completed_games_fetch_error",
                payload={"start_date": start_date, "end_date": end_date},
                session_id=session_id,
                snapshot_id=self._snapshot_id,
                severity="ERROR",
            )
            return False, pd.DataFrame()

        rows = []
        for date_block in data.get("dates", []):
            game_date = date_block.get("date", "")
            for game in date_block.get("games", []):
                status = game.get("status", {}).get("abstractGameState", "")
                if status != "Final":
                    continue
                game_pk = game.get("gamePk")
                teams = game.get("teams", {})
                home = teams.get("home", {})
                away = teams.get("away", {})
                home_team = home.get("team") or {}
                away_team = away.get("team") or {}
                home_team_id = home_team.get("id")
                away_team_id = away_team.get("id")
                rows.append({
                    "game_id": game_pk,
                    "game_date": game_date,
                    "home_team_id": home_team_id,
                    "home_team_abbr": self._team_abbr(home_team_id) if home_team_id is not None else "",
                    "away_team_id": away_team_id,
                    "away_team_abbr": self._team_abbr(away_team_id) if away_team_id is not None else "",
                    "home_runs": home.get("score"),
                    "away_runs": away.get("score"),
                })

        if not rows:
            return True, pd.DataFrame()

        df = pd.DataFrame(rows)
        df["game_date"] = pd.to_datetime(df["game_date"], errors="coerce").dt.date
        self._logger.log(
            COMPONENT,
            "completed_games_fetch_complete",
            payload={"start_date": start_date, "end_date": end_date, "n_games": len(df)},
            session_id=session_id,
            snapshot_id=self._snapshot_id,
            severity="INFO",
        )
        return True, df
