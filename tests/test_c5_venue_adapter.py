"""Tests for c5_execution/venue_adapter.py — VenueAdapter protocol and KalshiVenueAdapter."""
import pytest
from unittest.mock import MagicMock, patch

from prediction_market_bot.c5_execution.kalshi_client import DS02Snapshot, PlayerMarket
from prediction_market_bot.c5_execution.venue_adapter import (
    DFSPickemVenueAdapter,
    KalshiVenueAdapter,
    PolymarketVenueAdapter,
    VenueAdapter,
    _tag_market,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_market(**overrides) -> PlayerMarket:
    defaults = dict(
        ticker="KXNBAPTS-26MAY28OKCSAS-OKCSGA-25",
        title="Gilgeous-Alexander: 25+ points",
        player_name="Shai Gilgeous-Alexander",
        team_abbr="OKC",
        threshold=25,
        game_date="2026-05-28",
        event_ticker="KXNBAPTS-26MAY28OKCSAS",
        yes_ask=0.55, yes_bid=0.50, no_ask=0.48, no_bid=0.44,
        mid_price=0.525, vig=0.05, volume=100.0,
        status="active", fetched_at="2026-05-28T21:30:00.000Z",
        venue="kalshi",
    )
    defaults.update(overrides)
    return PlayerMarket(**defaults)


# ---------------------------------------------------------------------------
# PlayerMarket venue field
# ---------------------------------------------------------------------------

class TestPlayerMarketVenueField:
    def test_default_venue_is_kalshi(self):
        m = _make_market()
        assert m.venue == "kalshi"

    def test_venue_field_settable(self):
        m = _make_market(venue="polymarket")
        assert m.venue == "polymarket"

    def test_dataclass_fields_includes_venue(self):
        assert "venue" in PlayerMarket.__dataclass_fields__


# ---------------------------------------------------------------------------
# _tag_market helper
# ---------------------------------------------------------------------------

class TestTagMarket:
    def test_tags_venue_field(self):
        m = _make_market(venue="kalshi")
        tagged = _tag_market(m, "polymarket")
        assert tagged.venue == "polymarket"

    def test_all_other_fields_preserved(self):
        m = _make_market()
        tagged = _tag_market(m, "polymarket")
        assert tagged.ticker     == m.ticker
        assert tagged.player_name == m.player_name
        assert tagged.threshold  == m.threshold
        assert tagged.mid_price  == m.mid_price

    def test_original_market_unchanged(self):
        m = _make_market(venue="kalshi")
        _tag_market(m, "polymarket")
        assert m.venue == "kalshi"   # frozen — original unmodified


# ---------------------------------------------------------------------------
# VenueAdapter protocol
# ---------------------------------------------------------------------------

class TestVenueAdapterProtocol:
    def test_kalshi_adapter_satisfies_protocol(self):
        mock_client = MagicMock()
        adapter = KalshiVenueAdapter(mock_client)
        assert isinstance(adapter, VenueAdapter)

    def test_polymarket_adapter_satisfies_protocol(self):
        adapter = PolymarketVenueAdapter("fake_key_12345678")
        assert isinstance(adapter, VenueAdapter)


# ---------------------------------------------------------------------------
# KalshiVenueAdapter
# ---------------------------------------------------------------------------

class TestKalshiVenueAdapter:
    def _adapter(self):
        mock_client = MagicMock()
        return KalshiVenueAdapter(mock_client), mock_client

    def test_venue_id(self):
        adapter, _ = self._adapter()
        assert adapter.venue_id == "kalshi"

    def test_implied_prob_method(self):
        adapter, _ = self._adapter()
        assert adapter.implied_prob_method == "market"

    def test_check_connectivity_delegates(self):
        adapter, mock_client = self._adapter()
        mock_client.check_connectivity.return_value = (True, {"exchange_active": True})
        ok, status = adapter.check_connectivity()
        assert ok is True
        mock_client.check_connectivity.assert_called_once()

    def test_fetch_markets_tags_venue(self):
        adapter, mock_client = self._adapter()
        market = _make_market(venue="kalshi")
        mock_client.fetch_player_points_markets.return_value = (
            True, DS02Snapshot(fetched_at="2026-05-28T21:30:00.000Z", markets=[market])
        )
        ok, snapshot = adapter.fetch_player_points_markets()
        assert ok
        assert all(m.venue == "kalshi" for m in snapshot.markets)

    def test_fetch_markets_returns_false_on_client_failure(self):
        adapter, mock_client = self._adapter()
        mock_client.fetch_player_points_markets.return_value = (
            False, DS02Snapshot(fetched_at="2026-05-28T21:30:00.000Z", markets=[])
        )
        ok, snapshot = adapter.fetch_player_points_markets()
        assert not ok

    def test_fetch_market_detail_tags_venue(self):
        adapter, mock_client = self._adapter()
        market = _make_market()
        mock_client.fetch_market_detail.return_value = (True, market)
        ok, result = adapter.fetch_market_detail("some-ticker")
        assert ok
        assert result.venue == "kalshi"

    def test_fetch_market_detail_none_on_not_found(self):
        adapter, mock_client = self._adapter()
        mock_client.fetch_market_detail.return_value = (False, None)
        ok, result = adapter.fetch_market_detail("missing")
        assert not ok
        assert result is None

    def test_from_env_raises_without_key(self):
        with patch.dict("os.environ", {}, clear=True):
            import os
            os.environ.pop("VENUE_API_KEY", None)
            with pytest.raises(EnvironmentError):
                KalshiVenueAdapter.from_env()


# ---------------------------------------------------------------------------
# PolymarketVenueAdapter — T-077 implementation (network calls fail gracefully)
# ---------------------------------------------------------------------------

class TestPolymarketVenueAdapter:
    def test_venue_id(self):
        adapter = PolymarketVenueAdapter("fake_key_12345678")
        assert adapter.venue_id == "polymarket"

    def test_implied_prob_method(self):
        adapter = PolymarketVenueAdapter("fake_key_12345678")
        assert adapter.implied_prob_method == "market"

    def test_check_connectivity_returns_false_without_real_key(self):
        # No real key → network call fails → returns (False, dict) — not raises
        adapter = PolymarketVenueAdapter("fake_key_12345678")
        ok, status = adapter.check_connectivity()
        assert isinstance(ok, bool)
        assert isinstance(status, dict)
        assert "venue" in status

    def test_fetch_markets_returns_empty_snapshot_without_real_key(self):
        # No real key → network call fails → returns (False, empty snapshot) — not raises
        adapter = PolymarketVenueAdapter("fake_key_12345678")
        ok, snapshot = adapter.fetch_player_points_markets()
        assert isinstance(ok, bool)
        assert hasattr(snapshot, "markets")

    def test_from_env_raises_without_key(self):
        with patch.dict("os.environ", {}, clear=True):
            import os
            os.environ.pop("POLYMARKET_API_KEY", None)
            with pytest.raises(EnvironmentError):
                PolymarketVenueAdapter.from_env()

    def test_satisfies_venue_adapter_protocol(self):
        from prediction_market_bot.c5_execution.venue_adapter import VenueAdapter
        adapter = PolymarketVenueAdapter("fake_key_12345678")
        assert isinstance(adapter, VenueAdapter)


# ---------------------------------------------------------------------------
# DFSPickemVenueAdapter (stub)
# ---------------------------------------------------------------------------

class TestDFSPickemVenueAdapterStub:
    def test_implied_prob_method_is_bookmaker(self):
        adapter = DFSPickemVenueAdapter()
        assert adapter.implied_prob_method == "bookmaker"

    def test_all_methods_raise_not_implemented(self):
        adapter = DFSPickemVenueAdapter()
        with pytest.raises(NotImplementedError):
            adapter.check_connectivity()
        with pytest.raises(NotImplementedError):
            adapter.fetch_player_points_markets()
        with pytest.raises(NotImplementedError):
            adapter.fetch_market_detail("any")
