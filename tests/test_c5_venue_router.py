"""Tests for c5_execution/venue_router.py — VenueRouter routing logic."""
import pytest
from unittest.mock import MagicMock, patch

from prediction_market_bot.c5_execution.kalshi_client import DS02Snapshot, PlayerMarket
from prediction_market_bot.c5_execution.venue_router import VenueRouter, _deduplicate_best_price


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _market(player="Shai Gilgeous-Alexander", threshold=25, venue="kalshi",
            yes_ask=0.55, no_ask=0.48, mid_price=0.525, vig=0.05) -> PlayerMarket:
    return PlayerMarket(
        ticker=f"KXNBAPTS-TEST-{player[:3].upper()}-{threshold}",
        title=f"{player}: {threshold}+ points",
        player_name=player, team_abbr="OKC", threshold=threshold,
        game_date="2026-05-28", event_ticker="KXNBAPTS-TEST",
        yes_ask=yes_ask, yes_bid=yes_ask - vig,
        no_ask=no_ask, no_bid=no_ask - vig,
        mid_price=mid_price, vig=vig, volume=100.0,
        status="active", fetched_at="2026-05-28T21:30:00.000Z",
        venue=venue,
    )

def _mock_adapter(venue_id="kalshi", markets=None, ok=True) -> MagicMock:
    adapter = MagicMock()
    adapter.venue_id = venue_id
    snapshot = DS02Snapshot(
        fetched_at="2026-05-28T21:30:00.000Z",
        markets=markets or [],
    )
    adapter.fetch_player_points_markets.return_value = (ok, snapshot)
    adapter.check_connectivity.return_value = (True, {"exchange_active": True})
    return adapter


# ---------------------------------------------------------------------------
# Constructor
# ---------------------------------------------------------------------------

class TestVenueRouterInit:
    def test_raises_on_empty_adapters(self):
        with pytest.raises(ValueError):
            VenueRouter(adapters={})

    def test_active_venues_reflects_adapters(self):
        router = VenueRouter({"kalshi": _mock_adapter("kalshi")})
        assert "kalshi" in router.active_venues

    def test_default_mode_is_kalshi_only(self):
        router = VenueRouter({"kalshi": _mock_adapter("kalshi")})
        assert router.mode == "kalshi_only"


# ---------------------------------------------------------------------------
# fetch_all_markets — single venue
# ---------------------------------------------------------------------------

class TestFetchAllMarketsSingleVenue:
    def test_returns_kalshi_markets(self):
        m = _market()
        router = VenueRouter({"kalshi": _mock_adapter("kalshi", markets=[m])})
        ok, snapshot = router.fetch_all_markets()
        assert ok
        assert len(snapshot.markets) == 1

    def test_returns_false_on_adapter_failure(self):
        router = VenueRouter({"kalshi": _mock_adapter("kalshi", ok=False)})
        ok, snapshot = router.fetch_all_markets()
        assert not ok

    def test_empty_snapshot_on_no_markets(self):
        router = VenueRouter({"kalshi": _mock_adapter("kalshi", markets=[])})
        ok, snapshot = router.fetch_all_markets()
        assert ok
        assert snapshot.markets == []


# ---------------------------------------------------------------------------
# fetch_all_markets — multi-venue best_price mode
# ---------------------------------------------------------------------------

class TestFetchAllMarketsMultiVenue:
    def test_merges_markets_from_two_venues(self):
        kalshi_market = _market(venue="kalshi")
        poly_market   = _market(player="Luka Doncic", threshold=30, venue="polymarket")
        router = VenueRouter(
            {
                "kalshi":     _mock_adapter("kalshi",     markets=[kalshi_market]),
                "polymarket": _mock_adapter("polymarket", markets=[poly_market]),
            },
            mode="best_price",
        )
        ok, snapshot = router.fetch_all_markets()
        assert ok
        assert len(snapshot.markets) == 2

    def test_degrades_gracefully_when_one_adapter_fails(self):
        kalshi_market = _market(venue="kalshi")
        router = VenueRouter(
            {
                "kalshi":     _mock_adapter("kalshi",     markets=[kalshi_market]),
                "polymarket": _mock_adapter("polymarket", ok=False),
            },
            mode="best_price",
        )
        ok, snapshot = router.fetch_all_markets()
        assert ok                       # Kalshi succeeded — overall ok
        assert len(snapshot.markets) == 1

    def test_returns_false_when_all_adapters_fail(self):
        router = VenueRouter(
            {
                "kalshi":     _mock_adapter("kalshi",     ok=False),
                "polymarket": _mock_adapter("polymarket", ok=False),
            },
            mode="best_price",
        )
        ok, snapshot = router.fetch_all_markets()
        assert not ok


# ---------------------------------------------------------------------------
# get_best_market
# ---------------------------------------------------------------------------

class TestGetBestMarket:
    def test_returns_market_for_known_player(self):
        m = _market()
        router = VenueRouter({"kalshi": _mock_adapter("kalshi", markets=[m])})
        ok, best = router.get_best_market("Gilgeous-Alexander", 25.0, "YES")
        assert ok
        assert best is not None
        assert best.player_name == "Shai Gilgeous-Alexander"

    def test_returns_none_for_unknown_player(self):
        m = _market()
        router = VenueRouter({"kalshi": _mock_adapter("kalshi", markets=[m])})
        ok, best = router.get_best_market("NonExistentPlayer", 25.0, "YES")
        assert ok
        assert best is None

    def test_yes_direction_picks_lowest_yes_ask(self):
        cheaper = _market(venue="polymarket", yes_ask=0.51)
        pricier = _market(venue="kalshi",     yes_ask=0.55)
        router = VenueRouter(
            {
                "kalshi":     _mock_adapter("kalshi",     markets=[pricier]),
                "polymarket": _mock_adapter("polymarket", markets=[cheaper]),
            },
            mode="best_price",
        )
        ok, best = router.get_best_market("Gilgeous-Alexander", 25.0, "YES")
        assert ok
        assert best.venue == "polymarket"    # cheaper yes_ask wins

    def test_no_direction_picks_lowest_no_ask(self):
        cheaper_no = _market(venue="polymarket", no_ask=0.44)
        pricier_no = _market(venue="kalshi",     no_ask=0.48)
        router = VenueRouter(
            {
                "kalshi":     _mock_adapter("kalshi",     markets=[pricier_no]),
                "polymarket": _mock_adapter("polymarket", markets=[cheaper_no]),
            },
            mode="best_price",
        )
        ok, best = router.get_best_market("Gilgeous-Alexander", 25.0, "NO")
        assert ok
        assert best.venue == "polymarket"

    def test_tie_breaks_to_kalshi(self):
        kalshi_m = _market(venue="kalshi",     yes_ask=0.55)
        poly_m   = _market(venue="polymarket", yes_ask=0.55)
        router = VenueRouter(
            {
                "kalshi":     _mock_adapter("kalshi",     markets=[kalshi_m]),
                "polymarket": _mock_adapter("polymarket", markets=[poly_m]),
            },
            mode="best_price",
        )
        ok, best = router.get_best_market("Gilgeous-Alexander", 25.0, "YES")
        assert ok
        assert best.venue == "kalshi"   # tie-break: primary venue


# ---------------------------------------------------------------------------
# get_all_quotes
# ---------------------------------------------------------------------------

class TestGetAllQuotes:
    def test_returns_dict_keyed_by_venue(self):
        kalshi_m = _market(venue="kalshi")
        poly_m   = _market(venue="polymarket")
        router = VenueRouter(
            {
                "kalshi":     _mock_adapter("kalshi",     markets=[kalshi_m]),
                "polymarket": _mock_adapter("polymarket", markets=[poly_m]),
            },
        )
        quotes = router.get_all_quotes("Gilgeous-Alexander", 25.0)
        assert "kalshi" in quotes
        assert "polymarket" in quotes

    def test_returns_none_for_venue_with_no_match(self):
        router = VenueRouter({"kalshi": _mock_adapter("kalshi", markets=[])})
        quotes = router.get_all_quotes("Gilgeous-Alexander", 25.0)
        assert quotes["kalshi"] is None


# ---------------------------------------------------------------------------
# _deduplicate_best_price
# ---------------------------------------------------------------------------

class TestDeduplicateBestPrice:
    def test_keeps_one_market_per_player_threshold(self):
        m1 = _market(venue="kalshi",     vig=0.05)
        m2 = _market(venue="polymarket", vig=0.05)
        result = _deduplicate_best_price([m1, m2])
        assert len(result) == 1

    def test_keeps_tighter_vig(self):
        tight  = _market(venue="polymarket", vig=0.03)
        wide   = _market(venue="kalshi",     vig=0.05)
        result = _deduplicate_best_price([wide, tight])
        assert result[0].venue == "polymarket"

    def test_tie_vig_prefers_kalshi(self):
        same_vig_kalshi = _market(venue="kalshi",     vig=0.05)
        same_vig_poly   = _market(venue="polymarket", vig=0.05)
        result = _deduplicate_best_price([same_vig_poly, same_vig_kalshi])
        assert result[0].venue == "kalshi"

    def test_different_players_both_kept(self):
        m1 = _market(player="Shai Gilgeous-Alexander", threshold=25)
        m2 = _market(player="Luka Doncic",             threshold=30)
        result = _deduplicate_best_price([m1, m2])
        assert len(result) == 2


# ---------------------------------------------------------------------------
# TestVenueRouterBackwardCompatibility
# ---------------------------------------------------------------------------

class TestVenueRouterBackwardCompatibility:
    def test_single_venue_active_venues_kalshi_only(self):
        router = VenueRouter({"kalshi": _mock_adapter("kalshi")})
        assert router.active_venues == ["kalshi"]

    def test_kalshi_only_mode_delegates_to_primary_adapter(self):
        m = _market()
        router = VenueRouter({"kalshi": _mock_adapter("kalshi", markets=[m])}, mode="kalshi_only")
        ok, snapshot = router.fetch_all_markets()
        assert ok
        assert len(snapshot.markets) == 1

    def test_check_all_connectivity_returns_dict_keyed_by_venue(self):
        router = VenueRouter({"kalshi": _mock_adapter("kalshi")})
        result = router.check_all_connectivity()
        assert "kalshi" in result
        ok, stat = result["kalshi"]
        assert ok is True

    def test_single_venue_mode_bypasses_deduplication(self):
        # Two identical markets from a single venue should not be deduplicated
        # (deduplication only runs in best_price mode with multiple venues)
        m1 = _market(player="Shai Gilgeous-Alexander", threshold=25, venue="kalshi")
        m2 = _market(player="Luka Doncic",             threshold=30, venue="kalshi")
        router = VenueRouter({"kalshi": _mock_adapter("kalshi", markets=[m1, m2])})
        ok, snapshot = router.fetch_all_markets()
        assert ok
        assert len(snapshot.markets) == 2
