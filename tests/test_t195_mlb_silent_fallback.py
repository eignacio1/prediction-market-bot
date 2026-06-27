"""
T-195: Silent fallback audit — _is_mlb_game_in_progress and _fetch_live_game_pks

Verifies that API failures in the two MLB schedule-check helpers emit a C6 WARNING
instead of silently swallowing exceptions. Both functions remain permissive on failure
(return False / empty set) so the pipeline continues — but operators now see a log
entry in audit_mlb.jsonl when the MLB Stats API is unreachable.
"""
from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

import requests

_REPO_ROOT = Path(__file__).parent.parent
_SRC_ROOT  = _REPO_ROOT / "src"
if str(_SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(_SRC_ROOT))

os.environ.setdefault("BOT_ENV", "paper")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_logger() -> MagicMock:
    """Return a mock AuditLogger with a tracked .warning() method."""
    logger = MagicMock()
    logger.warning = MagicMock()
    return logger


# ---------------------------------------------------------------------------
# Tests for _is_mlb_game_in_progress (run_mlb_paper_trade.py)
# ---------------------------------------------------------------------------

class TestIsMlbGameInProgress(unittest.TestCase):
    """Tests for the contamination guard in PIPE-05."""

    def _import(self):
        from prediction_market_bot.run_mlb_paper_trade import _is_mlb_game_in_progress
        return _is_mlb_game_in_progress

    # --- happy path ---

    def test_returns_false_when_no_live_games(self):
        fn = self._import()
        payload = {"dates": [{"games": [
            {"status": {"abstractGameState": "Preview"}},
            {"status": {"abstractGameState": "Final"}},
        ]}]}
        with patch("prediction_market_bot.run_mlb_paper_trade.requests.get") as mock_get:
            mock_get.return_value.json.return_value = payload
            mock_get.return_value.raise_for_status = MagicMock()
            result = fn("2026-06-01")
        self.assertFalse(result)

    def test_returns_true_when_live_game_present(self):
        fn = self._import()
        payload = {"dates": [{"games": [
            {"status": {"abstractGameState": "Live"}},
        ]}]}
        with patch("prediction_market_bot.run_mlb_paper_trade.requests.get") as mock_get:
            mock_get.return_value.json.return_value = payload
            mock_get.return_value.raise_for_status = MagicMock()
            result = fn("2026-06-01")
        self.assertTrue(result)

    def test_returns_false_on_empty_dates(self):
        fn = self._import()
        with patch("prediction_market_bot.run_mlb_paper_trade.requests.get") as mock_get:
            mock_get.return_value.json.return_value = {"dates": []}
            mock_get.return_value.raise_for_status = MagicMock()
            result = fn("2026-06-01")
        self.assertFalse(result)

    # --- failure paths ---

    def test_returns_false_on_connection_error_no_logger(self):
        """API failure without logger → return False silently (backward-compat)."""
        fn = self._import()
        with patch("prediction_market_bot.run_mlb_paper_trade.requests.get",
                   side_effect=requests.ConnectionError("timeout")):
            result = fn("2026-06-01")
        self.assertFalse(result)

    def test_logs_warning_on_connection_error_with_logger(self):
        """API failure with logger → return False AND emit C6 WARNING."""
        fn = self._import()
        logger = _make_logger()
        with patch("prediction_market_bot.run_mlb_paper_trade.requests.get",
                   side_effect=requests.ConnectionError("timeout")):
            result = fn("2026-06-01", logger=logger, session_id="SID-TEST")
        self.assertFalse(result)
        logger.warning.assert_called_once()
        call_args = logger.warning.call_args
        self.assertEqual(call_args[0][0], "PIPE-05")
        self.assertEqual(call_args[0][1], "mlb_schedule_api_failed")
        self.assertIn("error", call_args[1]["payload"])
        self.assertEqual(call_args[1]["session_id"], "SID-TEST")

    def test_logs_warning_on_http_error_with_logger(self):
        """HTTP 500 response → return False AND emit C6 WARNING."""
        fn = self._import()
        logger = _make_logger()
        with patch("prediction_market_bot.run_mlb_paper_trade.requests.get") as mock_get:
            mock_get.return_value.raise_for_status.side_effect = requests.HTTPError("500")
            result = fn("2026-06-01", logger=logger, session_id="SID-TEST")
        self.assertFalse(result)
        logger.warning.assert_called_once()
        call_args = logger.warning.call_args
        self.assertEqual(call_args[0][1], "mlb_schedule_api_failed")

    def test_no_warning_when_logger_is_none_and_api_fails(self):
        """No logger provided → exception swallowed, no AttributeError."""
        fn = self._import()
        with patch("prediction_market_bot.run_mlb_paper_trade.requests.get",
                   side_effect=Exception("boom")):
            result = fn("2026-06-01", logger=None)
        self.assertFalse(result)

    def test_game_date_passed_in_warning_payload(self):
        """Payload must include the game_date so operators can identify which API call failed."""
        fn = self._import()
        logger = _make_logger()
        with patch("prediction_market_bot.run_mlb_paper_trade.requests.get",
                   side_effect=requests.ConnectionError("x")):
            fn("2026-07-04", logger=logger, session_id="SID-X")
        payload = logger.warning.call_args[1]["payload"]
        self.assertEqual(payload["game_date"], "2026-07-04")


# ---------------------------------------------------------------------------
# Tests for _fetch_live_game_pks (run_t2_mlb_sameday.py)
# ---------------------------------------------------------------------------

class TestFetchLiveGamePks(unittest.TestCase):
    """Tests for the per-game contamination guard in PIPE-05.5."""

    def _import(self):
        from prediction_market_bot.run_t2_mlb_sameday import _fetch_live_game_pks
        return _fetch_live_game_pks

    # --- happy path ---

    def test_returns_empty_set_when_no_live_games(self):
        fn = self._import()
        payload = {"dates": [{"games": [
            {"status": {"abstractGameState": "Preview"}, "gamePk": 111},
            {"status": {"abstractGameState": "Final"}, "gamePk": 222},
        ]}]}
        with patch("prediction_market_bot.run_t2_mlb_sameday.requests.get") as mock_get:
            mock_get.return_value.json.return_value = payload
            mock_get.return_value.raise_for_status = MagicMock()
            result = fn("2026-06-01")
        self.assertEqual(result, set())

    def test_returns_pks_for_live_games(self):
        fn = self._import()
        payload = {"dates": [{"games": [
            {"status": {"abstractGameState": "Live"}, "gamePk": 745488},
            {"status": {"abstractGameState": "Preview"}, "gamePk": 745489},
            {"status": {"abstractGameState": "Live"}, "gamePk": 745490},
        ]}]}
        with patch("prediction_market_bot.run_t2_mlb_sameday.requests.get") as mock_get:
            mock_get.return_value.json.return_value = payload
            mock_get.return_value.raise_for_status = MagicMock()
            result = fn("2026-06-01")
        self.assertEqual(result, {745488, 745490})

    def test_returns_empty_set_on_empty_response(self):
        fn = self._import()
        with patch("prediction_market_bot.run_t2_mlb_sameday.requests.get") as mock_get:
            mock_get.return_value.json.return_value = {"dates": []}
            mock_get.return_value.raise_for_status = MagicMock()
            result = fn("2026-06-01")
        self.assertEqual(result, set())

    # --- failure paths ---

    def test_returns_empty_set_on_connection_error_no_logger(self):
        """API failure without logger → return empty set silently (backward-compat)."""
        fn = self._import()
        with patch("prediction_market_bot.run_t2_mlb_sameday.requests.get",
                   side_effect=requests.ConnectionError("timeout")):
            result = fn("2026-06-01")
        self.assertEqual(result, set())

    def test_logs_warning_on_connection_error_with_logger(self):
        """API failure with logger → return empty set AND emit C6 WARNING."""
        fn = self._import()
        logger = _make_logger()
        with patch("prediction_market_bot.run_t2_mlb_sameday.requests.get",
                   side_effect=requests.ConnectionError("timeout")):
            result = fn("2026-06-01", logger=logger, session_id="SID-TEST")
        self.assertEqual(result, set())
        logger.warning.assert_called_once()
        call_args = logger.warning.call_args
        self.assertEqual(call_args[0][0], "PIPE-05.5-MLB")
        self.assertEqual(call_args[0][1], "mlb_schedule_api_failed")
        self.assertIn("error", call_args[1]["payload"])
        self.assertEqual(call_args[1]["session_id"], "SID-TEST")

    def test_logs_warning_on_http_error_with_logger(self):
        """HTTP error → return empty set AND emit C6 WARNING."""
        fn = self._import()
        logger = _make_logger()
        with patch("prediction_market_bot.run_t2_mlb_sameday.requests.get") as mock_get:
            mock_get.return_value.raise_for_status.side_effect = requests.HTTPError("503")
            result = fn("2026-06-01", logger=logger, session_id="SID-T2")
        self.assertEqual(result, set())
        logger.warning.assert_called_once()
        self.assertEqual(logger.warning.call_args[0][1], "mlb_schedule_api_failed")

    def test_no_warning_when_logger_is_none_and_api_fails(self):
        """No logger → exception swallowed, no AttributeError raised."""
        fn = self._import()
        with patch("prediction_market_bot.run_t2_mlb_sameday.requests.get",
                   side_effect=Exception("boom")):
            result = fn("2026-06-01", logger=None)
        self.assertEqual(result, set())

    def test_game_date_passed_in_warning_payload(self):
        """Payload must include game_date for operator diagnostics."""
        fn = self._import()
        logger = _make_logger()
        with patch("prediction_market_bot.run_t2_mlb_sameday.requests.get",
                   side_effect=requests.ConnectionError("x")):
            fn("2026-08-15", logger=logger, session_id="SID-X")
        payload = logger.warning.call_args[1]["payload"]
        self.assertEqual(payload["game_date"], "2026-08-15")

    def test_null_gamepk_skipped(self):
        """Games with gamePk=None must not raise — should not appear in result set."""
        fn = self._import()
        payload = {"dates": [{"games": [
            {"status": {"abstractGameState": "Live"}, "gamePk": None},
            {"status": {"abstractGameState": "Live"}, "gamePk": 12345},
        ]}]}
        with patch("prediction_market_bot.run_t2_mlb_sameday.requests.get") as mock_get:
            mock_get.return_value.json.return_value = payload
            mock_get.return_value.raise_for_status = MagicMock()
            result = fn("2026-06-01")
        self.assertEqual(result, {12345})


if __name__ == "__main__":
    unittest.main()
