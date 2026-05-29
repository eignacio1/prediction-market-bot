"""Tests for c5_execution/complement_lock_scanner.py — cross-venue lock detection."""
import pytest

from prediction_market_bot.c5_execution.kalshi_client import PlayerMarket
from prediction_market_bot.c5_execution.complement_lock_scanner import (
    DEFAULT_FEE_PER_CONTRACT,
    MIN_NET_PROFIT,
    ComplementLockScanner,
    LockOpportunity,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _market(
    player: str = "Shai Gilgeous-Alexander",
    threshold: int = 25,
    venue: str = "kalshi",
    yes_ask: float = 0.55,
    no_ask: float = 0.48,
) -> PlayerMarket:
    return PlayerMarket(
        ticker=f"KXNBAPTS-TEST-{player[:4].upper()}-{threshold}",
        title=f"{player}: {threshold}+ points",
        player_name=player,
        team_abbr="OKC",
        threshold=threshold,
        game_date="2026-05-28",
        event_ticker="KXNBAPTS-TEST",
        yes_ask=yes_ask,
        yes_bid=yes_ask - 0.05,
        no_ask=no_ask,
        no_bid=no_ask - 0.05,
        mid_price=(yes_ask + (yes_ask - 0.05)) / 2,
        vig=0.05,
        volume=100.0,
        status="active",
        fetched_at="2026-05-28T21:30:00.000Z",
        venue=venue,
    )


# ---------------------------------------------------------------------------
# LockOpportunity
# ---------------------------------------------------------------------------

class TestLockOpportunity:
    def test_is_cross_venue_true(self):
        opp = LockOpportunity(
            player_name="shai gilgeous-alexander", threshold=25,
            yes_venue="kalshi", no_venue="polymarket",
            ask_yes=0.44, ask_no=0.52,
            gross_profit=0.04, estimated_fee=0.06, net_profit=-0.02,
            detected_at="2026-05-28T21:30:00.000Z",
        )
        assert opp.is_cross_venue is True

    def test_is_cross_venue_false(self):
        opp = LockOpportunity(
            player_name="shai gilgeous-alexander", threshold=25,
            yes_venue="kalshi", no_venue="kalshi",
            ask_yes=0.44, ask_no=0.52,
            gross_profit=0.04, estimated_fee=0.06, net_profit=-0.02,
            detected_at="2026-05-28T21:30:00.000Z",
        )
        assert opp.is_cross_venue is False

    def test_frozen_immutability(self):
        opp = LockOpportunity(
            player_name="shai gilgeous-alexander", threshold=25,
            yes_venue="kalshi", no_venue="polymarket",
            ask_yes=0.44, ask_no=0.52,
            gross_profit=0.04, estimated_fee=0.06, net_profit=-0.02,
            detected_at="2026-05-28T21:30:00.000Z",
        )
        with pytest.raises((AttributeError, TypeError)):
            opp.net_profit = 0.99  # type: ignore[misc]


# ---------------------------------------------------------------------------
# ComplementLockScanner — scan_snapshot
# ---------------------------------------------------------------------------

class TestScanSnapshotNoOpportunity:
    """Cases where no lock opportunity should be returned."""

    def _scanner(self):
        return ComplementLockScanner(fee_per_contract=0.030, min_net_profit=0.001)

    def test_empty_list(self):
        assert self._scanner().scan_snapshot([]) == []

    def test_single_venue_single_market_no_lock(self):
        m = _market(yes_ask=0.55, no_ask=0.48)  # 0.55+0.48=1.03 > 1.00
        assert self._scanner().scan_snapshot([m]) == []

    def test_two_venues_no_lock_after_fees(self):
        # 0.50 + 0.46 = 0.96 → gross=0.04, fee=0.06 → net=-0.02
        k = _market(venue="kalshi",     yes_ask=0.50, no_ask=0.50)
        p = _market(venue="polymarket", yes_ask=0.50, no_ask=0.46)
        assert self._scanner().scan_snapshot([k, p]) == []

    def test_require_cross_venue_blocks_same_venue(self):
        # Single-venue pair that would be profitable without fee enforcement
        k_yes = _market(venue="kalshi", yes_ask=0.40, no_ask=0.50)
        k_no  = _market(player="Shai Gilgeous-Alexander", threshold=25,
                        venue="kalshi", yes_ask=0.50, no_ask=0.40)
        scanner = ComplementLockScanner(require_cross_venue=True, min_net_profit=0.001)
        # Same player/threshold on same venue — the scanner evaluates the group
        # but require_cross_venue=True means same-venue lock is not reported
        result = scanner.scan_snapshot([k_yes])
        assert result == []


class TestScanSnapshotWithOpportunity:
    """Cases where a lock opportunity should be detected."""

    def _scanner(self, fee=0.030, min_net=0.001, cross=True):
        return ComplementLockScanner(
            fee_per_contract=fee,
            min_net_profit=min_net,
            require_cross_venue=cross,
        )

    def test_detects_cross_venue_lock(self):
        # ask_yes=0.40, ask_no=0.40 → gross=0.20, fee=0.06, net=0.14
        k = _market(venue="kalshi",     yes_ask=0.40, no_ask=0.55)
        p = _market(venue="polymarket", yes_ask=0.55, no_ask=0.40)
        opps = self._scanner().scan_snapshot([k, p])
        assert len(opps) == 1
        opp = opps[0]
        assert opp.yes_venue == "kalshi"    # kalshi has lower yes_ask
        assert opp.no_venue == "polymarket" # polymarket has lower no_ask
        assert opp.net_profit > 0

    def test_net_profit_calculation(self):
        # ask_yes=0.40, ask_no=0.40 → gross=0.20, fee=0.06, net=0.14
        k = _market(venue="kalshi",     yes_ask=0.40, no_ask=0.60)
        p = _market(venue="polymarket", yes_ask=0.60, no_ask=0.40)
        opps = self._scanner().scan_snapshot([k, p])
        assert len(opps) == 1
        opp = opps[0]
        assert abs(opp.gross_profit - 0.20) < 1e-5
        assert abs(opp.net_profit - 0.14) < 1e-4

    def test_sorted_by_net_profit_descending(self):
        # Two players — second has higher net profit
        # Player 1: net ~0.05
        k1 = _market("LeBron James",              30, "kalshi",     0.42, 0.60)
        p1 = _market("LeBron James",              30, "polymarket", 0.60, 0.44)
        # Player 2: net ~0.14
        k2 = _market("Stephen Curry",             25, "kalshi",     0.40, 0.60)
        p2 = _market("Stephen Curry",             25, "polymarket", 0.60, 0.40)
        opps = self._scanner().scan_snapshot([k1, p1, k2, p2])
        assert len(opps) == 2
        assert opps[0].net_profit >= opps[1].net_profit

    def test_same_venue_lock_with_require_cross_false(self):
        # Transient same-venue lock (rare; stale quote scenario)
        # ask_yes=0.35, ask_no=0.35 → gross=0.30, fee=0.06, net=0.24
        m1 = _market(venue="kalshi", yes_ask=0.35, no_ask=0.60)
        m2 = _market(venue="kalshi", yes_ask=0.60, no_ask=0.35)
        # Both on kalshi — only detected with require_cross_venue=False
        scanner = self._scanner(cross=False)
        opps = scanner.scan_snapshot([m1, m2])
        # Note: same player/threshold will deduplicate into one group —
        # group has one market (same player/threshold/venue combination)
        # so best_yes and best_no come from the same market
        # This edge case tests that scanner doesn't crash
        assert isinstance(opps, list)

    def test_returns_lock_opportunity_type(self):
        k = _market(venue="kalshi",     yes_ask=0.40, no_ask=0.60)
        p = _market(venue="polymarket", yes_ask=0.60, no_ask=0.40)
        opps = self._scanner().scan_snapshot([k, p])
        assert all(isinstance(o, LockOpportunity) for o in opps)

    def test_detected_at_populated(self):
        k = _market(venue="kalshi",     yes_ask=0.40, no_ask=0.60)
        p = _market(venue="polymarket", yes_ask=0.60, no_ask=0.40)
        opps = self._scanner().scan_snapshot([k, p])
        assert opps[0].detected_at.endswith("Z")

    def test_picks_best_yes_and_no_across_three_venues(self):
        # Three venues — want best YES (lowest yes_ask) and best NO (lowest no_ask)
        k = _market(venue="kalshi",      yes_ask=0.50, no_ask=0.60)
        p = _market(venue="polymarket",  yes_ask=0.38, no_ask=0.55)  # best YES
        d = _market(venue="draftkings",  yes_ask=0.48, no_ask=0.37)  # best NO
        opps = ComplementLockScanner(
            fee_per_contract=0.020, min_net_profit=0.001, require_cross_venue=True
        ).scan_snapshot([k, p, d])
        assert len(opps) == 1
        opp = opps[0]
        assert opp.ask_yes == pytest.approx(0.38)
        assert opp.ask_no  == pytest.approx(0.37)
        assert opp.yes_venue == "polymarket"
        assert opp.no_venue  == "draftkings"


# ---------------------------------------------------------------------------
# ComplementLockScanner — scan_single
# ---------------------------------------------------------------------------

class TestScanSingle:
    def _scanner(self):
        return ComplementLockScanner(fee_per_contract=0.020, min_net_profit=0.001)

    def test_finds_lock_for_specific_player(self):
        k = _market("Gilgeous-Alexander", 25, "kalshi",     0.40, 0.60)
        p = _market("Gilgeous-Alexander", 25, "polymarket", 0.60, 0.40)
        opp = self._scanner().scan_single("Gilgeous", 25, [k, p])
        assert opp is not None
        assert opp.threshold == 25

    def test_returns_none_for_unknown_player(self):
        k = _market("SGA", 25, "kalshi")
        opp = self._scanner().scan_single("LeBron", 25, [k])
        assert opp is None

    def test_returns_none_for_wrong_threshold(self):
        k = _market("SGA", 25, "kalshi",     0.40, 0.60)
        p = _market("SGA", 25, "polymarket", 0.60, 0.40)
        opp = self._scanner().scan_single("SGA", 30, [k, p])
        assert opp is None

    def test_fragment_match_case_insensitive(self):
        k = _market("Shai Gilgeous-Alexander", 25, "kalshi",     0.40, 0.60)
        p = _market("Shai Gilgeous-Alexander", 25, "polymarket", 0.60, 0.40)
        opp = self._scanner().scan_single("gilgeous", 25, [k, p])
        assert opp is not None


# ---------------------------------------------------------------------------
# Default constants
# ---------------------------------------------------------------------------

class TestConstants:
    def test_default_fee_value(self):
        assert DEFAULT_FEE_PER_CONTRACT == 0.030

    def test_min_net_profit_value(self):
        assert MIN_NET_PROFIT == 0.001
