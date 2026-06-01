"""
Tests for kalshi_client.py — URL routing and core logic.

Coverage:
  - _price_discovery_url() always returns production regardless of BOT_ENV (T-114)
  - _kalshi_base_url() follows BOT_ENV for order/portfolio endpoints
  - _get() uses production URL for unauthenticated calls
  - _get() uses BOT_ENV URL for authenticated calls
  - _parse_market() parses valid and invalid market dicts
  - KalshiMarketClient construction guards
"""
import os
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest

from prediction_market_bot.c5_execution.kalshi_client import (
    _KALSHI_DEMO_BASE_URL,
    _KALSHI_LIVE_BASE_URL,
    _kalshi_base_url,
    _price_discovery_url,
    DS02Snapshot,
    KalshiMarketClient,
    KalshiOrder,
    PlayerMarket,
)


# ---------------------------------------------------------------------------
# T-114: URL routing invariants
# ---------------------------------------------------------------------------


class TestPriceDiscoveryUrl:
    """_price_discovery_url() must always return production regardless of BOT_ENV."""

    def test_returns_live_url_when_bot_env_paper(self, monkeypatch):
        monkeypatch.setenv("BOT_ENV", "paper")
        assert _price_discovery_url() == _KALSHI_LIVE_BASE_URL

    def test_returns_live_url_when_bot_env_live(self, monkeypatch):
        monkeypatch.setenv("BOT_ENV", "live")
        assert _price_discovery_url() == _KALSHI_LIVE_BASE_URL

    def test_returns_live_url_when_bot_env_missing(self, monkeypatch):
        monkeypatch.delenv("BOT_ENV", raising=False)
        assert _price_discovery_url() == _KALSHI_LIVE_BASE_URL

    def test_returns_live_url_when_bot_env_test(self, monkeypatch):
        monkeypatch.setenv("BOT_ENV", "test")
        assert _price_discovery_url() == _KALSHI_LIVE_BASE_URL

    def test_is_not_demo_url(self, monkeypatch):
        monkeypatch.setenv("BOT_ENV", "paper")
        assert _price_discovery_url() != _KALSHI_DEMO_BASE_URL


class TestKalshiBaseUrl:
    """_kalshi_base_url() follows BOT_ENV for authenticated/order endpoints."""

    def test_paper_returns_demo(self, monkeypatch):
        monkeypatch.setenv("BOT_ENV", "paper")
        assert _kalshi_base_url() == _KALSHI_DEMO_BASE_URL

    def test_live_returns_live(self, monkeypatch):
        monkeypatch.setenv("BOT_ENV", "live")
        assert _kalshi_base_url() == _KALSHI_LIVE_BASE_URL

    def test_missing_defaults_to_demo(self, monkeypatch):
        monkeypatch.delenv("BOT_ENV", raising=False)
        assert _kalshi_base_url() == _KALSHI_DEMO_BASE_URL

    def test_unknown_env_defaults_to_demo(self, monkeypatch):
        monkeypatch.setenv("BOT_ENV", "staging")
        assert _kalshi_base_url() == _KALSHI_DEMO_BASE_URL


class TestGetUrlRouting:
    """_get() must use production for market data and BOT_ENV for authenticated calls."""

    def _make_client(self):
        return KalshiMarketClient(api_key_id="x" * 20)

    def test_unauthenticated_get_uses_production_url_in_paper_mode(self, monkeypatch):
        """Market data must always hit production — T-114 core assertion."""
        monkeypatch.setenv("BOT_ENV", "paper")
        client = self._make_client()

        captured_urls = []

        def fake_get(url, params=None, headers=None, timeout=None):
            captured_urls.append(url)
            resp = MagicMock()
            resp.status_code = 200
            resp.json.return_value = {"markets": []}
            return resp

        client._session.get = fake_get
        client._get("/markets", params={"series_ticker": "KXNBAPTS"}, authenticated=False)

        assert len(captured_urls) == 1
        assert captured_urls[0].startswith(_KALSHI_LIVE_BASE_URL), (
            f"Market data should use production URL, got: {captured_urls[0]}"
        )
        assert _KALSHI_DEMO_BASE_URL not in captured_urls[0]

    def test_authenticated_get_uses_demo_url_in_paper_mode(self, monkeypatch):
        """Portfolio/balance endpoints should use demo sandbox in paper mode."""
        monkeypatch.setenv("BOT_ENV", "paper")
        client = self._make_client()

        # Inject a dummy private key so auth headers are built
        mock_key = MagicMock()
        mock_key.sign.return_value = b"fakesig"
        client._private_key = mock_key

        captured_urls = []

        def fake_get(url, params=None, headers=None, timeout=None):
            captured_urls.append(url)
            resp = MagicMock()
            resp.status_code = 200
            resp.json.return_value = {"balance": 100000, "portfolio_value": 0}
            return resp

        client._session.get = fake_get
        client._get("/portfolio/balance", authenticated=True)

        assert len(captured_urls) == 1
        assert captured_urls[0].startswith(_KALSHI_DEMO_BASE_URL), (
            f"Authenticated endpoint should use demo URL in paper mode, got: {captured_urls[0]}"
        )

    def test_unauthenticated_get_uses_production_url_in_live_mode(self, monkeypatch):
        """Production mode: market data should also use production (same result)."""
        monkeypatch.setenv("BOT_ENV", "live")
        client = self._make_client()

        captured_urls = []

        def fake_get(url, params=None, headers=None, timeout=None):
            captured_urls.append(url)
            resp = MagicMock()
            resp.status_code = 200
            resp.json.return_value = {"markets": []}
            return resp

        client._session.get = fake_get
        client._get("/markets", authenticated=False)

        assert captured_urls[0].startswith(_KALSHI_LIVE_BASE_URL)


# ---------------------------------------------------------------------------
# _parse_market() — field parsing
# ---------------------------------------------------------------------------


class TestParseMarket:
    """Verify _parse_market() extracts fields from raw API dicts."""

    def _raw(self, **overrides) -> dict:
        base = {
            "ticker": "KXNBAPTS-26JUN03OKCSAS-OKCSGILGEOUSALEXANDER2-25",
            "title": "Shai Gilgeous-Alexander: 25+ Points",
            "event_ticker": "KXNBAPTS-26JUN03OKCSAS",
            "yes_ask": 0.55,
            "yes_bid": 0.50,
            "no_ask": 0.50,
            "no_bid": 0.45,
            "volume_fp": 1500.0,
            "status": "open",
        }
        base.update(overrides)
        return base

    def test_parses_threshold(self):
        m = KalshiMarketClient._parse_market(self._raw())
        assert m is not None
        assert m.threshold == 25

    def test_parses_mid_price(self):
        m = KalshiMarketClient._parse_market(self._raw(yes_ask=0.60, yes_bid=0.50))
        assert m.mid_price == pytest.approx(0.55)

    def test_parses_vig(self):
        m = KalshiMarketClient._parse_market(self._raw(yes_ask=0.60, yes_bid=0.50))
        assert m.vig == pytest.approx(0.10)

    def test_parses_game_date(self):
        m = KalshiMarketClient._parse_market(self._raw())
        assert m.game_date == "2026-06-03"

    def test_parses_player_name_from_title(self):
        m = KalshiMarketClient._parse_market(self._raw(title="LeBron James: 30+ Points"))
        assert m.player_name == "LeBron James"

    def test_parses_team_abbr(self):
        m = KalshiMarketClient._parse_market(self._raw())
        assert m.team_abbr == "OKC"

    def test_returns_none_on_nonnumeric_threshold(self):
        m = KalshiMarketClient._parse_market(self._raw(
            ticker="KXNBAPTS-26JUN03OKCSAS-OKCSGA-NOTANUMBER"
        ))
        assert m is None

    def test_has_live_quotes_true_when_both_prices_set(self):
        m = KalshiMarketClient._parse_market(self._raw(yes_ask=0.55, yes_bid=0.50))
        assert m.has_live_quotes is True

    def test_has_live_quotes_false_when_prices_zero(self):
        m = KalshiMarketClient._parse_market(self._raw(yes_ask=0.0, yes_bid=0.0))
        assert m.has_live_quotes is False

    def test_uses_yes_ask_dollars_fallback(self):
        raw = self._raw()
        del raw["yes_ask"]
        raw["yes_ask_dollars"] = 0.65
        m = KalshiMarketClient._parse_market(raw)
        assert m is not None
        assert m.yes_ask == pytest.approx(0.65)


# ---------------------------------------------------------------------------
# KalshiMarketClient construction guards
# ---------------------------------------------------------------------------


class TestClientConstruction:
    def test_raises_on_missing_api_key(self):
        with pytest.raises(ValueError, match="VENUE_API_KEY"):
            KalshiMarketClient(api_key_id="")

    def test_raises_on_short_api_key(self):
        with pytest.raises(ValueError, match="VENUE_API_KEY"):
            KalshiMarketClient(api_key_id="tooshort")

    def test_has_signing_key_false_without_private_key(self):
        client = KalshiMarketClient(api_key_id="x" * 20)
        assert client.has_signing_key() is False

    def test_has_signing_key_true_with_private_key(self):
        client = KalshiMarketClient(api_key_id="x" * 20, private_key=MagicMock())
        assert client.has_signing_key() is True

    def test_from_env_raises_without_api_key(self, monkeypatch):
        monkeypatch.delenv("VENUE_API_KEY", raising=False)
        with pytest.raises(EnvironmentError, match="VENUE_API_KEY"):
            KalshiMarketClient.from_env()


# ---------------------------------------------------------------------------
# DS02Snapshot helpers
# ---------------------------------------------------------------------------


class TestDS02Snapshot:
    def _market(self, player_name: str, threshold: int) -> PlayerMarket:
        return PlayerMarket(
            ticker=f"KXNBAPTS-26JUN03-TST-{threshold}",
            title=f"{player_name}: {threshold}+ Points",
            player_name=player_name,
            team_abbr="TST",
            threshold=threshold,
            game_date="2026-06-03",
            event_ticker="KXNBAPTS-26JUN03TST",
            yes_ask=0.55, yes_bid=0.50,
            no_ask=0.50, no_bid=0.45,
            mid_price=0.525, vig=0.05,
            volume=1000.0, status="open",
            fetched_at=datetime.now(tz=timezone.utc).isoformat(),
        )

    def test_for_player_returns_matching_markets(self):
        snap = DS02Snapshot(
            fetched_at="2026-06-03T00:00:00Z",
            markets=[self._market("LeBron James", 25), self._market("LeBron James", 30),
                     self._market("Stephen Curry", 25)],
        )
        result = snap.for_player("LeBron")
        assert len(result) == 2
        assert all("LEBRON" in m.player_name.upper() for m in result)

    def test_closest_to_threshold(self):
        snap = DS02Snapshot(
            fetched_at="2026-06-03T00:00:00Z",
            markets=[self._market("LeBron James", 20), self._market("LeBron James", 25),
                     self._market("LeBron James", 30)],
        )
        result = snap.closest_to_threshold("LeBron", 27)
        assert result is not None
        assert result.threshold == 25

    def test_closest_to_threshold_returns_none_on_unknown_player(self):
        snap = DS02Snapshot(fetched_at="2026-06-03T00:00:00Z", markets=[])
        assert snap.closest_to_threshold("UnknownPlayer", 25) is None
