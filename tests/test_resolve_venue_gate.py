"""T-656 / GG-440 / GG-450: a Kalshi-cancelled market is never booked as WIN/LOSS.

The resolver books a position only when Kalshi reports the market settled yes/no;
cancelled, not-final and unreadable markets are skipped and reported, never settled
and never tagged aged_open. --dry-run classifies and writes nothing.
"""
from __future__ import annotations

import os
from unittest.mock import MagicMock

import pytest

os.environ.setdefault("BOT_ENV", "paper")

import prediction_market_bot.run_resolve_mlb as rm  # noqa: E402

TICKER = "KXMLBHIT-26JUL191910KCDET-KCBWITTJR7-1"


@pytest.mark.parametrize("raw,state", [
    ({"result": "yes"}, rm.VENUE_SETTLED),
    ({"result": "NO"}, rm.VENUE_SETTLED),
    ({"result": "scalar", "expiration_value": "Cancelled"}, rm.VENUE_CANCELLED),
    ({"result": "scalar", "expiration_value": ""}, rm.VENUE_CANCELLED),
    ({"result": "", "expiration_value": "Cancelled"}, rm.VENUE_CANCELLED),
    ({"result": "", "status": "canceled"}, rm.VENUE_CANCELLED),
    ({"result": "", "status": "open"}, rm.VENUE_NOT_FINAL),
    ({}, rm.VENUE_NOT_FINAL),
])
def test_classify_venue_market(raw, state):
    assert rm._classify_venue_market(raw) == state


def _pool(state, raw, hits=2.0, dry_run=False, monkeypatch=None, logger=None):
    pos = {"position_id": "P1", "player_id": 677951, "player_name": "Bobby Witt Jr.",
           "game_date": "2026-07-19", "kalshi_threshold": 1, "direction": "YES", "kalshi_ticker": TICKER}
    trader = MagicMock()
    trader.get_state.return_value = {"open_positions": [pos], "closed_positions": [], "rejected_positions": []}
    trader.settle_position_from_venue.return_value = (True, {"pnl": 1.0, "outcome": "WIN", "cancelled": False})
    monkeypatch.setattr(rm, "_ticker_to_game_date", lambda t: "2026-07-19")
    monkeypatch.setattr(rm, "_venue_market_state", lambda t: (state, raw))
    fetch = MagicMock(return_value=hits)
    monkeypatch.setattr(rm, "fetch_actual_hits", fetch)
    rm._resolve_pool("T1/T2", trader, logger or MagicMock(), "S", MagicMock(), dry_run=dry_run)
    return trader, fetch


@pytest.mark.parametrize("state,raw", [
    (rm.VENUE_NOT_FINAL, {"result": ""}),
    (rm.VENUE_UNKNOWN, {}),
    (rm.VENUE_CANCELLED, {"result": "scalar", "expiration_value": "Cancelled"}),  # no settlement value
])
def test_unbookable_market_is_never_booked_or_aged(state, raw, monkeypatch):
    trader, fetch = _pool(state, raw, monkeypatch=monkeypatch)
    trader.settle_position_from_venue.assert_not_called()
    trader.settle_position.assert_not_called()
    trader.mark_aged_open.assert_not_called()


def test_settled_market_books_on_kalshi_result_not_stat_feed(monkeypatch):
    # ADR-0071: stat feed says 0 hits (NO) but Kalshi says yes -> booked on Kalshi's result.
    trader, fetch = _pool(rm.VENUE_SETTLED, {"result": "yes"}, hits=0.0, monkeypatch=monkeypatch)
    trader.settle_position.assert_not_called()
    trader.settle_position_from_venue.assert_called_once()
    assert trader.settle_position_from_venue.call_args.kwargs["venue_result"] == "yes"


def test_cancelled_market_booked_at_settlement_value(monkeypatch):
    raw = {"result": "scalar", "expiration_value": "Cancelled", "settlement_value_dollars": "0.3400"}
    trader, _ = _pool(rm.VENUE_CANCELLED, raw, monkeypatch=monkeypatch)
    kw = trader.settle_position_from_venue.call_args.kwargs
    assert kw["venue_result"] == "scalar" and kw["settlement_value"] == 0.34


def test_stat_feed_failure_cannot_block_booking(monkeypatch):
    trader, fetch = _pool(rm.VENUE_SETTLED, {"result": "no"}, hits=None, monkeypatch=monkeypatch)
    trader.settle_position_from_venue.assert_called_once()
    trader.mark_aged_open.assert_not_called()


def test_crosscheck_disagreement_is_logged_not_acted_on(monkeypatch):
    logger = MagicMock()
    trader, _ = _pool(rm.VENUE_SETTLED, {"result": "yes"}, hits=0.0, monkeypatch=monkeypatch, logger=logger)
    events = [c.args[1] for c in logger.warning.call_args_list]
    assert "kalshi_stat_crosscheck_disagree" in events
    trader.settle_position_from_venue.assert_called_once()


def test_dry_run_writes_nothing(monkeypatch, capsys):
    trader, _ = _pool(rm.VENUE_SETTLED, {"result": "yes"}, dry_run=True, monkeypatch=monkeypatch)
    trader.settle_position_from_venue.assert_not_called()
    trader.settle_position.assert_not_called()
    trader.mark_aged_open.assert_not_called()
    assert "DRY-RUN settles" in capsys.readouterr().out


def test_venue_lookup_uses_historical_then_live_and_fails_closed(monkeypatch):
    calls = []

    class R:
        def __init__(self, code, body):
            self.status_code, self._b = code, body

        def raise_for_status(self):
            if self.status_code >= 400:
                raise RuntimeError(self.status_code)

        def json(self):
            return self._b

    def fake_get(url, timeout):
        calls.append(url)
        if "/historical/" in url:
            return R(404, {})
        return R(200, {"market": {"result": "scalar", "expiration_value": "Cancelled"}})

    monkeypatch.setattr(rm.requests, "get", fake_get)
    assert rm._venue_market_state(TICKER)[0] == rm.VENUE_CANCELLED
    assert "/historical/markets/" in calls[0] and "/markets/" in calls[1]
    assert all(u.startswith("https://external-api.kalshi.com/") for u in calls)

    def boom(url, timeout):
        raise OSError("blocked")

    monkeypatch.setattr(rm.requests, "get", boom)
    assert rm._venue_market_state(TICKER)[0] == rm.VENUE_UNKNOWN
    assert rm._venue_market_state("")[0] == rm.VENUE_UNKNOWN


def test_espn_not_found_is_logged(monkeypatch, capsys):
    monkeypatch.setattr(rm, "_espn_game_ids_for_date", lambda d: [])
    assert rm._espn_fetch_hits("Bobby Witt Jr.", "2026-07-19") is None
    assert "not found in any final ESPN boxscore" in capsys.readouterr().err


def _espn_summary(status, athletes=()):
    return {"header": {"competitions": [{"status": {"type": {"name": status}}}]},
            "boxscore": {"players": [{"statistics": [{"labels": ["AB", "H"], "athletes": list(athletes)}]}]}}


def _espn_fetch(monkeypatch, status, capsys):
    monkeypatch.setattr(rm, "_espn_game_ids_for_date", lambda d: ["G1"])
    resp = MagicMock()
    resp.json.return_value = _espn_summary(status)
    monkeypatch.setattr(rm.requests, "get", lambda *a, **k: resp)
    assert rm._espn_fetch_hits("Gunnar Henderson", "2026-07-21") is None
    return capsys.readouterr().err


def test_espn_not_found_log_names_postponed_game(monkeypatch, capsys):
    """W53.1: a POSTPONED game's empty boxscore must not be logged as plain 'did not play'."""
    err = _espn_fetch(monkeypatch, rm._ESPN_STATUS_POSTPONED, capsys)
    assert "POSTPONED" in err and "G1" in err


def test_espn_not_found_log_final_game_unchanged(monkeypatch, capsys):
    err = _espn_fetch(monkeypatch, rm._ESPN_STATUS_FINAL, capsys)
    assert "did not play, or name mismatch" in err and "POSTPONED" not in err
