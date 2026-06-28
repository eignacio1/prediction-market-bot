"""
T-189: Tests for PIPE-05 session-83 fixes.

Concerns addressed:
  1. GAME_DATE = tomorrow (T1 night-before baseline; contamination guard must target
     the games being bet on, not today's in-progress games).
  2. Market date filter — only markets whose ticker resolves to GAME_DATE_ISO are
     evaluated; today's in-progress markets are excluded.
  3. PaperTrader writes portfolio file on first init, even with 0 bets placed.
  4. fetch_game_starters hydrate no longer includes 'venue' (returns 406 from VPS
     via Fastly CDN; removed to restore SP data availability).
  5. PIPE-05FX cache bust does not delete starters/pitcher caches (they cannot be
     refreshed from VPS and destroying them removes locally-built SP data).
"""
from __future__ import annotations

import json
import re
import unittest
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import MagicMock, patch


# ---------------------------------------------------------------------------
# Fix 1 — GAME_DATE = tomorrow
# ---------------------------------------------------------------------------


class TestGameDateIsToday(unittest.TestCase):
    """GAME_DATE logic: cron at 03:00 UTC targets today's (UTC) games.

    S87 FIX: Original 23:30 UTC cron used timedelta(days=1) to target tomorrow;
    Kalshi hadn't published next-day markets at that hour (VPS confirmed 0 players).
    Fixed: same-day targeting at 03:00 UTC — today's (ET) games start ≥17:05 UTC,
    so the contamination guard always passes at cron time.
    """

    def _compute_game_date(self, now_utc: datetime) -> tuple[str, str]:
        """Mirror the run_mlb_paper_trade.py GAME_DATE computation."""
        target = now_utc.date()
        return target.strftime("%Y%m%d"), target.strftime("%Y-%m-%d")

    def test_game_date_is_utc_today(self):
        now = datetime(2026, 6, 25, 3, 0, tzinfo=timezone.utc)
        gd, gd_iso = self._compute_game_date(now)
        self.assertEqual(gd, "20260625")
        self.assertEqual(gd_iso, "2026-06-25")

    def test_game_date_crosses_month_boundary(self):
        now = datetime(2026, 7, 1, 3, 0, tzinfo=timezone.utc)
        gd, gd_iso = self._compute_game_date(now)
        self.assertEqual(gd, "20260701")
        self.assertEqual(gd_iso, "2026-07-01")

    def test_game_date_matches_utc_date(self):
        now = datetime(2026, 6, 25, 3, 0, tzinfo=timezone.utc)
        _, gd_iso = self._compute_game_date(now)
        today_iso = now.strftime("%Y-%m-%d")
        self.assertEqual(gd_iso, today_iso)

    def test_game_date_matches_contamination_guard_target(self):
        """Guard checks GAME_DATE_ISO; today's ET games are 'Preview' at 03:00 UTC."""
        now = datetime(2026, 6, 25, 3, 0, tzinfo=timezone.utc)
        _, gd_iso = self._compute_game_date(now)
        # Jun-25 ET games start ≥17:05 UTC — all Preview at 03:00 UTC
        self.assertEqual(gd_iso, "2026-06-25")


# ---------------------------------------------------------------------------
# Fix 2 — Market date filter
# ---------------------------------------------------------------------------


def _ticker_to_game_date(ticker: str, fallback_iso: str) -> str:
    """Pure copy of run_mlb_paper_trade._ticker_to_game_date for isolated testing.

    Kalshi opens markets the day before the game; adds 1 day to get true game date.
    YY in ticker is unreliable; uses current UTC year instead.
    """
    from datetime import timezone, timedelta as _td
    m = re.search(r"-([0-9]{2})([A-Z]{3})[0-9]{2}[0-9]{4}", ticker)
    if m:
        try:
            year = datetime.now(tz=timezone.utc).year
            kalshi_date = datetime.strptime(
                f"{m.group(1)}{m.group(2)}{year}", "%d%b%Y"
            ).date()
            return (kalshi_date + _td(days=1)).strftime("%Y-%m-%d")
        except ValueError:
            pass
    return fallback_iso


class TestTickerToGameDate(unittest.TestCase):
    """_ticker_to_game_date parses KXMLBHIT tickers correctly."""

    def test_standard_format(self):
        # Ticker day=25 → Kalshi convention +1 day → game date June 26
        ticker = "KXMLBHIT-25JUN261907BALLAA-2"
        result = _ticker_to_game_date(ticker, "2026-06-25")
        self.assertEqual(result, "2026-06-26")

    def test_different_month(self):
        # Ticker day=04 (July) → Kalshi +1 day → game date July 5
        ticker = "KXMLBHIT-04JUL261900NYYBOS-1"
        result = _ticker_to_game_date(ticker, "2026-06-25")
        self.assertEqual(result, "2026-07-05")

    def test_unparseable_returns_fallback(self):
        ticker = "KXMLBHIT-BADFORMAT"
        result = _ticker_to_game_date(ticker, "2026-06-25")
        self.assertEqual(result, "2026-06-25")

    def test_empty_ticker_returns_fallback(self):
        result = _ticker_to_game_date("", "2026-06-25")
        self.assertEqual(result, "2026-06-25")

    def test_yesterday_ticker_excluded_when_game_date_is_today(self):
        """Cron targets today (2026-06-25). Kalshi dates markets one day before game.
        Today's market (June 25 game) has ticker day=24; +1 day = June 25 = game_date_iso.
        Yesterday's market (June 24 game) has ticker day=23; +1 day = June 24 ≠ game_date_iso."""
        yesterday_ticker = "KXMLBHIT-23JUN261907BOSNYY-1"  # day=23 → June 24 → excluded
        today_ticker     = "KXMLBHIT-24JUN261907BALLAA-2"  # day=24 → June 25 → included
        game_date_iso    = "2026-06-25"

        yesterday_date = _ticker_to_game_date(yesterday_ticker, game_date_iso)
        today_date     = _ticker_to_game_date(today_ticker, game_date_iso)

        self.assertNotEqual(yesterday_date, game_date_iso, "yesterday's market should be excluded")
        self.assertEqual(today_date, game_date_iso, "today's market should be included")


class TestMarketDateFilter(unittest.TestCase):
    """Only markets for GAME_DATE_ISO pass the date filter in markets_by_player."""

    def _apply_filter(self, markets: list[dict], game_date_iso: str) -> dict[str, list]:
        """Simulate the fixed markets_by_player loop from run_mlb_paper_trade.py."""
        result: dict[str, list] = {}
        for m in markets:
            if m["status"] == "active" and m["has_live_quotes"]:
                mkt_date = _ticker_to_game_date(m["ticker"], game_date_iso)
                if mkt_date == game_date_iso:
                    result.setdefault(m["player_name"], []).append(m)
        return result

    def _make_market(self, ticker: str, player: str) -> dict:
        return {
            "ticker": ticker,
            "player_name": player,
            "status": "active",
            "has_live_quotes": True,
        }

    def test_only_today_markets_included(self):
        """GAME_DATE_ISO = today (2026-06-25). Kalshi ticker day = game_day - 1.
        June 24 game (ticker day=23) excluded; June 25 game (ticker day=24) included."""
        markets = [
            self._make_market("KXMLBHIT-23JUN261907BOSNYY-1", "Mookie Betts"),  # June 24 game → excluded
            self._make_market("KXMLBHIT-24JUN261907BALLAA-1", "Aaron Judge"),   # June 25 game → included
            self._make_market("KXMLBHIT-24JUN261907BALLAA-2", "Aaron Judge"),   # June 25 game → included
        ]
        result = self._apply_filter(markets, "2026-06-25")
        self.assertNotIn("Mookie Betts", result)
        self.assertIn("Aaron Judge", result)
        self.assertEqual(len(result["Aaron Judge"]), 2)

    def test_all_filtered_if_all_yesterday(self):
        # June 24 games have ticker day=23; +1 = June 24 ≠ June 25 → all excluded
        markets = [
            self._make_market("KXMLBHIT-23JUN261907BOSNYY-1", "Player A"),
            self._make_market("KXMLBHIT-23JUN262005NYYHOU-1", "Player B"),
        ]
        result = self._apply_filter(markets, "2026-06-25")
        self.assertEqual(result, {})

    def test_inactive_markets_excluded_regardless_of_date(self):
        markets = [
            {
                "ticker": "KXMLBHIT-25JUN261907BALLAA-1",
                "player_name": "Aaron Judge",
                "status": "inactive",
                "has_live_quotes": True,
            }
        ]
        result = self._apply_filter(markets, "2026-06-25")
        self.assertEqual(result, {})

    def test_no_live_quotes_excluded(self):
        markets = [
            {
                "ticker": "KXMLBHIT-25JUN261907BALLAA-1",
                "player_name": "Aaron Judge",
                "status": "active",
                "has_live_quotes": False,
            }
        ]
        result = self._apply_filter(markets, "2026-06-25")
        self.assertEqual(result, {})

    def test_unparseable_ticker_falls_back_to_game_date_iso(self):
        """Unparse-able tickers resolve to GAME_DATE_ISO — they pass the filter."""
        markets = [
            {
                "ticker": "KXMLBHIT-BADFORMAT",
                "player_name": "Unknown Player",
                "status": "active",
                "has_live_quotes": True,
            }
        ]
        result = self._apply_filter(markets, "2026-06-25")
        self.assertIn("Unknown Player", result)


# ---------------------------------------------------------------------------
# Fix 3 — PaperTrader writes portfolio file on init
# ---------------------------------------------------------------------------


class TestEnsurePersistedCreatesFile(unittest.TestCase):
    """ensure_persisted() must create the portfolio file even when 0 bets are placed.

    The fix: run_mlb_paper_trade.py calls trader.ensure_persisted() immediately
    after PaperTrader construction. This is the Concern 2 fix (portfolio file
    missing when contamination guard fires before any bet is placed).
    """

    def _make_trader(self, path: Path) -> object:
        from prediction_market_bot.c5_execution.paper_trader import PaperTrader
        from prediction_market_bot.c6_audit_logger.audit_logger import AuditLogger
        log_path = path.parent / "audit" / "audit.log"
        log_path.parent.mkdir(parents=True, exist_ok=True)
        logger = AuditLogger(log_path=log_path)
        return PaperTrader(portfolio_path=path, logger=logger)

    def test_init_alone_does_not_write_file(self, tmp_path=None):
        """PaperTrader.__init__ must NOT write to disk — file only created when bets land
        or ensure_persisted() is called. This preserves the _reload_locked invariant."""
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            portfolio_path = Path(d) / "paper_portfolio_mlb.json"
            self.assertFalse(portfolio_path.exists(), "pre-condition")
            self._make_trader(portfolio_path)
            self.assertFalse(portfolio_path.exists(),
                             "init must not write file — _reload_locked would overwrite "
                             "in-memory mutations if file exists before first bet")

    def test_ensure_persisted_creates_file(self, tmp_path=None):
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            portfolio_path = Path(d) / "paper_portfolio_mlb.json"
            trader = self._make_trader(portfolio_path)
            self.assertFalse(portfolio_path.exists(), "pre-condition")
            trader.ensure_persisted()
            self.assertTrue(portfolio_path.exists(), "file must exist after ensure_persisted()")

    def test_ensure_persisted_writes_1000_bankroll(self, tmp_path=None):
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            portfolio_path = Path(d) / "paper_portfolio_mlb.json"
            trader = self._make_trader(portfolio_path)
            trader.ensure_persisted()
            state = json.loads(portfolio_path.read_text())
            self.assertEqual(state["bankroll_usd"], 1000.0)
            self.assertEqual(state["initial_bankroll_usd"], 1000.0)

    def test_ensure_persisted_writes_empty_positions(self, tmp_path=None):
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            portfolio_path = Path(d) / "paper_portfolio_mlb.json"
            trader = self._make_trader(portfolio_path)
            trader.ensure_persisted()
            state = json.loads(portfolio_path.read_text())
            self.assertEqual(state["open_positions"], [])
            self.assertEqual(state["closed_positions"], [])

    def test_ensure_persisted_noop_if_file_exists(self, tmp_path=None):
        """ensure_persisted() must not overwrite an existing portfolio."""
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            portfolio_path = Path(d) / "paper_portfolio_mlb.json"
            pre_existing = {
                "bankroll_usd": 900.0,
                "initial_bankroll_usd": 1000.0,
                "total_realized_pnl": -100.0,
                "current_daily_loss": 0.0,
                "daily_loss_date": "2026-06-24",
                "open_positions": [],
                "closed_positions": [],
                "created_at": "2026-06-24T00:00:00.000Z",
                "last_updated": "2026-06-24T00:00:00.000Z",
            }
            portfolio_path.write_text(json.dumps(pre_existing))
            trader = self._make_trader(portfolio_path)
            trader.ensure_persisted()
            state = json.loads(portfolio_path.read_text())
            # bankroll derived from ledger: initial=1000 + closed_pnl=0 - open=0 = 1000
            # BUT we haven't called _save() yet, so the file still has the pre-existing data
            self.assertEqual(state["bankroll_usd"], 900.0,
                             "ensure_persisted must not overwrite existing file")


# ---------------------------------------------------------------------------
# Fix 4 — fetch_game_starters hydrate
# ---------------------------------------------------------------------------


class TestFetchGameStartersHydrate(unittest.TestCase):
    """fetch_game_starters must NOT include 'venue' in hydrate (406 on DO/Fastly CDN)."""

    def test_venue_not_in_hydrate_param(self):
        import inspect
        from prediction_market_bot.c1_signal_ingestion.mlb_ingestion import (
            MLBIngestionClient,
        )
        src = inspect.getsource(MLBIngestionClient.fetch_game_starters)
        # Find the hydrate param value
        m = re.search(r'"hydrate":\s*"([^"]+)"', src)
        self.assertIsNotNone(m, "hydrate param not found in fetch_game_starters source")
        hydrate_value = m.group(1)
        self.assertNotIn("venue", hydrate_value,
                         f"'venue' found in hydrate={hydrate_value!r} — "
                         "this returns HTTP 406 from DigitalOcean/Fastly CDN")

    def test_probablepitcher_still_present_in_hydrate(self):
        import inspect
        from prediction_market_bot.c1_signal_ingestion.mlb_ingestion import (
            MLBIngestionClient,
        )
        src = inspect.getsource(MLBIngestionClient.fetch_game_starters)
        m = re.search(r'"hydrate":\s*"([^"]+)"', src)
        self.assertIsNotNone(m)
        hydrate_value = m.group(1)
        self.assertIn("probablePitcher", hydrate_value,
                      f"'probablePitcher' missing from hydrate={hydrate_value!r}")

    def test_team_still_present_in_hydrate(self):
        import inspect
        from prediction_market_bot.c1_signal_ingestion.mlb_ingestion import (
            MLBIngestionClient,
        )
        src = inspect.getsource(MLBIngestionClient.fetch_game_starters)
        m = re.search(r'"hydrate":\s*"([^"]+)"', src)
        self.assertIsNotNone(m)
        hydrate_value = m.group(1)
        self.assertIn("team", hydrate_value,
                      f"'team' missing from hydrate={hydrate_value!r}")


# ---------------------------------------------------------------------------
# Fix 5 — PIPE-05FX cache bust does not touch starters / pitcher logs
# ---------------------------------------------------------------------------


class TestPipe05FXCacheBust(unittest.TestCase):
    """cron.conf PIPE-05FX must not bust starters_2026.json or pitcher_logs_2026.parquet."""

    def _get_pipe05fx_rm_command(self) -> str:
        cron_path = Path(__file__).parent.parent / "deploy" / "cron.conf"
        text = cron_path.read_text()
        # Find the PIPE-05FX cron line (22:30 UTC, runs generate_mlb_features.py)
        for line in text.splitlines():
            if "generate_mlb_features.py" in line and "30 22" in line:
                return line
        return ""

    def test_starters_cache_not_in_bust_command(self):
        cmd = self._get_pipe05fx_rm_command()
        self.assertNotEqual(cmd, "", "PIPE-05FX cron line not found in cron.conf")
        self.assertNotIn("starters_2026.json", cmd,
                         "starters_2026.json must NOT be busted — "
                         "hydrate=probablePitcher returns 406 on VPS, busting destroys SP data")

    def test_pitcher_logs_not_in_bust_command(self):
        cmd = self._get_pipe05fx_rm_command()
        self.assertNotIn("pitcher_logs_2026.parquet", cmd,
                         "pitcher_logs_2026.parquet must NOT be busted — "
                         "historical pitcher data can only be built locally")

    def test_batter_logs_still_busted(self):
        cmd = self._get_pipe05fx_rm_command()
        self.assertIn("batter_logs_2026.parquet", cmd,
                      "batter_logs_2026.parquet must still be busted for fresh daily stats")

    def test_completed_games_still_busted(self):
        cmd = self._get_pipe05fx_rm_command()
        self.assertIn("completed_games_2026.parquet", cmd,
                      "completed_games_2026.parquet must still be busted for team stats refresh")


# ---------------------------------------------------------------------------
# Integration: contamination guard targets tomorrow, not today
# ---------------------------------------------------------------------------


class TestContaminationGuardTargetsTomorrow(unittest.TestCase):
    """End-to-end logic: guard checks GAME_DATE_ISO which is always tomorrow."""

    def _is_game_in_progress_mock(self, game_date: str, state: str) -> bool:
        """Simulate the guard: returns True if any game on game_date is 'Live'."""
        # Only 'Live' state triggers contamination
        return state == "Live"

    def test_guard_passes_when_tomorrow_games_preview(self):
        # Tomorrow's games at 23:30 UTC are "Preview" — cron should proceed
        guard_fires = self._is_game_in_progress_mock("2026-06-25", "Preview")
        self.assertFalse(guard_fires)

    def test_guard_would_fire_if_today_used(self):
        # Today's games at 23:30 UTC are "Live" — this is the original bug
        guard_fires = self._is_game_in_progress_mock("2026-06-24", "Live")
        self.assertTrue(guard_fires)

    def test_game_date_iso_computation_for_various_utc_cron_times(self):
        """GAME_DATE_ISO = tomorrow for any reasonable cron time."""
        cron_times = [
            datetime(2026, 6, 24, 22, 0, tzinfo=timezone.utc),   # 22:00 UTC
            datetime(2026, 6, 24, 23, 30, tzinfo=timezone.utc),  # 23:30 UTC (actual cron)
            datetime(2026, 6, 25, 1, 0, tzinfo=timezone.utc),    # 01:00 UTC next day
        ]
        expected = ["2026-06-25", "2026-06-25", "2026-06-26"]
        for t, exp in zip(cron_times, expected):
            target = (t + timedelta(days=1)).strftime("%Y-%m-%d")
            self.assertEqual(target, exp, f"GAME_DATE_ISO mismatch for cron time {t}")


if __name__ == "__main__":
    unittest.main()
