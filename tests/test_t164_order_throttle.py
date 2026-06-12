"""
Tests: T-164 — Throttled Order Submission (GG-014 G6 gate)
===========================================================
GG-014: 9/29 = 31% order failure rate at G5 with 0.5s inter-order sleep.
T-164 remediation:
  - Inter-order sleep raised 0.5s → 2.0s (paper_trader.open_position)
  - RETRY_DELAY_S raised 1.0 → 2.0 (kalshi_client._post/_get)
  - MAX_RETRIES raised 3 → 4 (kalshi_client._post/_get)
  - Retry delays: 4s / 8s / 16s / 32s = 60s max window (covers most rate-limit windows)
  - Batch order completion log added to run_paper_trade.py (GG-014 hygiene)

G6 gate: ≤5% order failure rate.
"""

import json
from pathlib import Path
from unittest.mock import MagicMock, patch, call

import pytest

from prediction_market_bot.c5_execution.kalshi_client import (
    MAX_RETRIES,
    RETRY_DELAY_S,
    KalshiMarketClient,
)
from prediction_market_bot.c5_execution.paper_trader import PaperTrader
from prediction_market_bot.c6_audit_logger.audit_logger import AuditLogger


# ---------------------------------------------------------------------------
# kalshi_client constants — T-164 raised values
# ---------------------------------------------------------------------------

class TestRetryConstants:
    def test_max_retries_is_4(self):
        """MAX_RETRIES must be 4 (T-164: raised from 3 to cover 60s rate-limit windows)."""
        assert MAX_RETRIES == 4

    def test_retry_delay_is_2s(self):
        """RETRY_DELAY_S must be 2.0 (T-164: raised from 1.0; delay schedule 4/8/16/32s)."""
        assert RETRY_DELAY_S == pytest.approx(2.0, abs=1e-9)

    def test_post_retry_delay_schedule(self, monkeypatch):
        """_post() retry delays must follow 4s/8s/16s/32s schedule (RETRY_DELAY_S=2.0)."""
        monkeypatch.setenv("BOT_ENV", "paper")
        client = KalshiMarketClient(api_key_id="x" * 20)
        client._private_key = MagicMock()
        sleep_calls = []

        # Return 429 for all attempts to capture full delay schedule
        def fake_post(url, json=None, headers=None, timeout=None):
            resp = MagicMock()
            resp.status_code = 429
            resp.text = "Too Many Requests"
            return resp

        with patch("prediction_market_bot.c5_execution.kalshi_client._auth_headers", return_value={}), \
             patch("prediction_market_bot.c5_execution.kalshi_client.time.sleep",
                   side_effect=lambda s: sleep_calls.append(s)):
            client._session.post = fake_post
            ok, data = client._post("/portfolio/orders", {"type": "limit"})

        assert ok is False
        # 4 attempts: delays 2*(2^1)=4, 2*(2^2)=8, 2*(2^3)=16, 2*(2^4)=32
        assert sleep_calls == [4.0, 8.0, 16.0, 32.0], (
            f"Expected [4.0, 8.0, 16.0, 32.0] but got {sleep_calls}. "
            f"MAX_RETRIES={MAX_RETRIES}, RETRY_DELAY_S={RETRY_DELAY_S}"
        )

    def test_get_retry_delay_schedule(self, monkeypatch):
        """_get() retry delays must match _post(): 4s/8s/16s/32s."""
        monkeypatch.setenv("BOT_ENV", "paper")
        client = KalshiMarketClient(api_key_id="x" * 20)
        sleep_calls = []

        def fake_get(url, params=None, headers=None, timeout=None):
            resp = MagicMock()
            resp.status_code = 503
            resp.text = "Service Unavailable"
            return resp

        with patch("prediction_market_bot.c5_execution.kalshi_client.time.sleep",
                   side_effect=lambda s: sleep_calls.append(s)):
            client._session.get = fake_get
            ok, data = client._get("/markets", authenticated=False)

        assert ok is False
        assert sleep_calls == [4.0, 8.0, 16.0, 32.0]

    def test_total_retry_window_covers_60s(self):
        """Sum of all retry delays must be ≥60s to cover standard rate-limit reset windows."""
        total = sum(RETRY_DELAY_S * (2 ** (i + 1)) for i in range(MAX_RETRIES))
        assert total >= 60.0, f"Total retry window {total}s < 60s minimum"


# ---------------------------------------------------------------------------
# paper_trader inter-order sleep — T-164 raised 0.5→2.0s
# ---------------------------------------------------------------------------

@pytest.fixture
def tmp_trader(tmp_path):
    log_file = tmp_path / "audit.jsonl"
    portfolio_file = tmp_path / "portfolio.json"
    logger = AuditLogger(log_path=log_file)
    return PaperTrader(
        portfolio_path=portfolio_file,
        logger=logger,
        kalshi_client=None,
    )


def _make_approval(size: float = 5.0, direction: str = "YES") -> dict:
    return {
        "approval_status": "APPROVED",
        "approved_size": size,
        "approved_direction": direction,
        "model_p": 0.65,
        "edge": 0.10,
        "gross_edge": 0.11,
        "fee_net_edge": 0.10,
    }


class TestInterOrderSleep:
    def test_sleep_2s_when_kalshi_client_present(self, tmp_path):
        """open_position() must sleep 2.0s after Kalshi order when client is present (T-164)."""
        log_file = tmp_path / "audit.jsonl"
        portfolio_file = tmp_path / "portfolio.json"
        logger = AuditLogger(log_path=log_file)

        mock_kalshi = MagicMock()
        mock_kalshi.has_signing_key.return_value = True
        mock_order = MagicMock()
        mock_order.ok = True
        mock_order.order_id = "order-001"
        mock_order.status = "executed"
        mock_order.contracts = 10
        mock_kalshi.submit_order.return_value = mock_order

        trader = PaperTrader(
            portfolio_path=portfolio_file,
            logger=logger,
            kalshi_client=mock_kalshi,
        )

        sleep_calls = []
        with patch("prediction_market_bot.c5_execution.paper_trader.time.sleep",
                   side_effect=lambda s: sleep_calls.append(s)):
            trader.open_position(
                approval=_make_approval(),
                player_name="Test Player",
                player_id=1,
                kalshi_ticker="KXNBAPTS-001",
                kalshi_threshold=20,
                mid_price=0.55,
                vig=0.02,
                game_date="2026-06-13",
            )

        assert 2.0 in sleep_calls, (
            f"Expected time.sleep(2.0) after Kalshi order submission but got: {sleep_calls}"
        )

    def test_no_sleep_without_kalshi_client(self, tmp_trader):
        """open_position() must NOT sleep when kalshi_client is None (local-only mode)."""
        sleep_calls = []
        with patch("prediction_market_bot.c5_execution.paper_trader.time.sleep",
                   side_effect=lambda s: sleep_calls.append(s)):
            tmp_trader.open_position(
                approval=_make_approval(),
                player_name="Test Player",
                player_id=2,
                kalshi_ticker="KXNBAPTS-002",
                kalshi_threshold=25,
                mid_price=0.50,
                vig=0.02,
                game_date="2026-06-13",
            )

        assert sleep_calls == [], (
            f"Expected no sleep with no Kalshi client but got: {sleep_calls}"
        )

    def test_no_sleep_when_key_not_loaded(self, tmp_path):
        """open_position() must NOT sleep when has_signing_key() is False."""
        log_file = tmp_path / "audit.jsonl"
        portfolio_file = tmp_path / "portfolio.json"
        logger = AuditLogger(log_path=log_file)

        mock_kalshi = MagicMock()
        mock_kalshi.has_signing_key.return_value = False

        trader = PaperTrader(
            portfolio_path=portfolio_file,
            logger=logger,
            kalshi_client=mock_kalshi,
        )

        sleep_calls = []
        with patch("prediction_market_bot.c5_execution.paper_trader.time.sleep",
                   side_effect=lambda s: sleep_calls.append(s)):
            trader.open_position(
                approval=_make_approval(),
                player_name="Test Player",
                player_id=3,
                kalshi_ticker="KXNBAPTS-003",
                kalshi_threshold=30,
                mid_price=0.45,
                vig=0.02,
                game_date="2026-06-13",
            )

        assert sleep_calls == [], (
            f"Expected no sleep without signing key but got: {sleep_calls}"
        )

    def test_sleep_value_is_exactly_2s(self, tmp_path):
        """Inter-order sleep must be exactly 2.0s — not 0.5s (old), not 1.0s."""
        log_file = tmp_path / "audit.jsonl"
        portfolio_file = tmp_path / "portfolio.json"
        logger = AuditLogger(log_path=log_file)

        mock_kalshi = MagicMock()
        mock_kalshi.has_signing_key.return_value = True
        mock_order = MagicMock()
        mock_order.ok = False
        mock_order.error = "test_error"
        mock_kalshi.submit_order.return_value = mock_order

        trader = PaperTrader(
            portfolio_path=portfolio_file,
            logger=logger,
            kalshi_client=mock_kalshi,
        )

        sleep_calls = []
        with patch("prediction_market_bot.c5_execution.paper_trader.time.sleep",
                   side_effect=lambda s: sleep_calls.append(s)):
            trader.open_position(
                approval=_make_approval(),
                player_name="Test Player",
                player_id=4,
                kalshi_ticker="KXNBAPTS-004",
                kalshi_threshold=15,
                mid_price=0.60,
                vig=0.02,
                game_date="2026-06-13",
            )

        assert len(sleep_calls) == 1
        assert sleep_calls[0] == pytest.approx(2.0), (
            f"Inter-order sleep must be 2.0s (T-164), got {sleep_calls[0]}"
        )
