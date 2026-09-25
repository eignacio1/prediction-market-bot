"""
Reproduction + fix tests for GG-303 (T-576).

GG-303: 395/731 NOT_RETRIEVABLE T4M-PROJ ledger rows carry a kalshi_order_id
that does not exist at Kalshi. The confirmed write-boundary defect: an HTTP
200/201 response with no resolvable order_id in the body was previously
still treated as a successful, acknowledged order (order.ok=True,
order_id=""), which paper_trader.py then persisted as a confirmed position.

These tests reproduce the defect against the pre-fix code path (by stubbing
_post() to return a Kalshi-shaped 200 response missing order_id) and assert
the post-fix behavior: (a) such a response is refused, not persisted as a
phantom open position; (b) a genuine, well-formed fill still records
correctly; (c) the refusal is visible via the rejected_positions/audit path.
"""
from unittest.mock import MagicMock

import pytest

from prediction_market_bot.c5_execution.kalshi_client import KalshiMarketClient
from prediction_market_bot.c5_execution.paper_trader import PaperTrader
from prediction_market_bot.c6_audit_logger.audit_logger import AuditLogger


def _client() -> KalshiMarketClient:
    # has_signing_key() only requires a non-None private_key; no real RSA
    # material needed since _post() is stubbed directly below submit_order().
    return KalshiMarketClient(api_key_id="x" * 12, private_key="dummy-not-real-key")


class TestGG303SubmitOrderWriteBoundary:
    def test_missing_order_id_in_response_is_refused_not_fabricated(self, monkeypatch):
        """(a) Reproduction: Kalshi 200s with no order_id -> must NOT be ok=True."""
        client = _client()
        # Kalshi-shaped success response with no "order" wrapper and no order_id key.
        monkeypatch.setattr(client, "_post", lambda path, body: (True, {"status": "submitted"}))

        order = client.submit_order(
            ticker="KXMLBHIT-26SEP24TEST-1",
            side="yes",
            size_usd=5.0,
            mid_price=0.55,
        )

        assert order.ok is False
        assert order.order_id == ""
        assert "order_id" in order.error

    def test_empty_string_order_id_is_also_refused(self, monkeypatch):
        """Same defect via the 'order' wrapper form, order_id explicitly empty."""
        client = _client()
        monkeypatch.setattr(
            client, "_post",
            lambda path, body: (True, {"order": {"order_id": "", "status": "resting"}}),
        )

        order = client.submit_order(
            ticker="KXMLBHIT-26SEP24TEST-1",
            side="yes",
            size_usd=5.0,
            mid_price=0.55,
        )

        assert order.ok is False
        assert order.order_id == ""

    def test_genuine_fill_still_records_correctly(self, monkeypatch):
        """(b) A well-formed response with a real order_id is unaffected by the fix."""
        client = _client()
        monkeypatch.setattr(
            client, "_post",
            lambda path, body: (True, {"order": {"order_id": "kalshi-real-abc123", "status": "resting"}}),
        )

        order = client.submit_order(
            ticker="KXMLBHIT-26SEP24TEST-1",
            side="yes",
            size_usd=5.0,
            mid_price=0.55,
        )

        assert order.ok is True
        assert order.order_id == "kalshi-real-abc123"
        assert order.status == "resting"


class TestGG303PaperTraderWriteBoundary:
    """(c) paper_trader.open_position() must route a refused write to
    rejected_positions with an audit-visible log entry, never into
    open_positions."""

    def test_refused_order_never_enters_open_positions(self, monkeypatch, tmp_path):
        portfolio_path = tmp_path / "paper_portfolio_gg303_test.json"
        logger = AuditLogger(log_path=tmp_path / "audit_gg303_test.jsonl")
        trader = PaperTrader(portfolio_path=portfolio_path, logger=logger)

        fake_kalshi = MagicMock()
        fake_kalshi.has_signing_key.return_value = True
        fake_order = MagicMock()
        fake_order.ok = True
        fake_order.order_id = ""  # the defect shape: "ok" but no real id
        fake_order.error = ""
        fake_kalshi.submit_order.return_value = fake_order
        trader._kalshi = fake_kalshi

        approval = {
            "approval_status": "APPROVED",
            "approved_size": 5.0,
            "approved_direction": "YES",
            "edge": 0.05,
            "gross_edge": 0.07,
            "model_p": 0.62,
            "risk_eval_id": "RISK-GG303",
            "forecast_id": "FC-GG303",
        }

        ok_pos, pos = trader.open_position(
            approval=approval,
            player_name="Test Player",
            player_id=1,
            kalshi_ticker="KXMLBHIT-26SEP24TEST-1",
            kalshi_threshold=1,
            mid_price=0.55,
            vig=0.03,
            game_date="2026-09-24",
            session_id="gg303-test-session",
            pool_isolated=True,
            h_so_far_at_entry=0,
            ab_remaining_at_entry=4,
        )

        assert pos == {}
        assert not any(
            p.get("kalshi_ticker") == "KXMLBHIT-26SEP24TEST-1"
            for p in trader._state.get("open_positions", [])
        )
        rejected = trader._state.get("rejected_positions", [])
        assert any(p.get("kalshi_ticker") == "KXMLBHIT-26SEP24TEST-1" for p in rejected)
