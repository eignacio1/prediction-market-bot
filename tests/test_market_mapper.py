"""Tests for c5_execution/market_mapper.py — cross-venue player name normalization."""
import pytest

from prediction_market_bot.c5_execution.kalshi_client import PlayerMarket
from prediction_market_bot.c5_execution.market_mapper import (
    PlayerMarketKey,
    group_by_key,
    market_key,
    normalize_player_name,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _market(player: str, threshold: int = 25, venue: str = "kalshi") -> PlayerMarket:
    return PlayerMarket(
        ticker=f"KXNBAPTS-TEST-{player[:4].upper()}-{threshold}",
        title=f"{player}: {threshold}+ points",
        player_name=player,
        team_abbr="OKC",
        threshold=threshold,
        game_date="2026-05-28",
        event_ticker="KXNBAPTS-TEST",
        yes_ask=0.55, yes_bid=0.50, no_ask=0.48, no_bid=0.44,
        mid_price=0.525, vig=0.05, volume=100.0,
        status="active", fetched_at="2026-05-28T21:30:00.000Z",
        venue=venue,
    )


# ---------------------------------------------------------------------------
# normalize_player_name
# ---------------------------------------------------------------------------

class TestNormalizePlayerName:
    def test_lowercase(self):
        assert normalize_player_name("LeBron James") == "lebron james"

    def test_strips_apostrophe(self):
        assert normalize_player_name("De'Aaron Fox") == "deaaron fox"

    def test_strips_period(self):
        assert normalize_player_name("A.J. Green") == "aj green"

    def test_strips_parentheses(self):
        assert normalize_player_name("Joel Embiid (day-to-day)") == "joel embiid day-to-day"

    def test_accent_normalization(self):
        result = normalize_player_name("Luka Dončić")
        assert result == "luka doncic"

    def test_already_clean_name(self):
        assert normalize_player_name("Shai Gilgeous-Alexander") == "shai gilgeous-alexander"

    def test_leading_trailing_whitespace(self):
        assert normalize_player_name("  Kevin Durant  ") == "kevin durant"

    def test_multiple_internal_spaces(self):
        assert normalize_player_name("James  Harden") == "james harden"

    def test_all_caps(self):
        assert normalize_player_name("STEPHEN CURRY") == "stephen curry"

    def test_hyphenated_name_preserved(self):
        result = normalize_player_name("Gilgeous-Alexander")
        assert "-" in result

    def test_empty_string(self):
        assert normalize_player_name("") == ""

    def test_unicode_cedilla(self):
        result = normalize_player_name("Nikola Jokić")
        assert result == "nikola jokic"

    def test_idempotent(self):
        name = "Jayson Tatum"
        assert normalize_player_name(normalize_player_name(name)) == normalize_player_name(name)


# ---------------------------------------------------------------------------
# PlayerMarketKey
# ---------------------------------------------------------------------------

class TestPlayerMarketKey:
    def test_is_named_tuple(self):
        key = PlayerMarketKey("shai gilgeous-alexander", 25)
        assert key.normalized_name == "shai gilgeous-alexander"
        assert key.threshold == 25

    def test_equality_by_value(self):
        k1 = PlayerMarketKey("lebron james", 30)
        k2 = PlayerMarketKey("lebron james", 30)
        assert k1 == k2

    def test_different_threshold_not_equal(self):
        k1 = PlayerMarketKey("lebron james", 25)
        k2 = PlayerMarketKey("lebron james", 30)
        assert k1 != k2

    def test_hashable_for_dict_use(self):
        key = PlayerMarketKey("lebron james", 25)
        d = {key: "value"}
        assert d[key] == "value"


# ---------------------------------------------------------------------------
# market_key
# ---------------------------------------------------------------------------

class TestMarketKey:
    def test_returns_player_market_key(self):
        m = _market("Shai Gilgeous-Alexander", threshold=25)
        key = market_key(m)
        assert isinstance(key, PlayerMarketKey)

    def test_normalizes_player_name(self):
        m = _market("De'Aaron Fox", threshold=20)
        key = market_key(m)
        assert key.normalized_name == "deaaron fox"

    def test_uses_market_threshold(self):
        m = _market("LeBron James", threshold=30)
        key = market_key(m)
        assert key.threshold == 30

    def test_same_player_different_venues_same_key(self):
        k = _market("Shai Gilgeous-Alexander", threshold=25, venue="kalshi")
        p = _market("Shai Gilgeous-Alexander", threshold=25, venue="polymarket")
        assert market_key(k) == market_key(p)

    def test_same_player_different_thresholds_different_key(self):
        m25 = _market("LeBron James", threshold=25)
        m30 = _market("LeBron James", threshold=30)
        assert market_key(m25) != market_key(m30)


# ---------------------------------------------------------------------------
# group_by_key
# ---------------------------------------------------------------------------

class TestGroupByKey:
    def test_single_market_single_group(self):
        m = _market("LeBron James", 25)
        groups = group_by_key([m])
        assert len(groups) == 1

    def test_two_venues_same_player_same_threshold_one_group(self):
        kalshi_m = _market("LeBron James", 25, venue="kalshi")
        poly_m   = _market("LeBron James", 25, venue="polymarket")
        groups = group_by_key([kalshi_m, poly_m])
        assert len(groups) == 1
        key = PlayerMarketKey("lebron james", 25)
        assert len(groups[key]) == 2

    def test_same_player_different_thresholds_two_groups(self):
        m25 = _market("LeBron James", 25)
        m30 = _market("LeBron James", 30)
        groups = group_by_key([m25, m30])
        assert len(groups) == 2

    def test_different_players_different_groups(self):
        m1 = _market("LeBron James", 25)
        m2 = _market("Stephen Curry", 25)
        groups = group_by_key([m1, m2])
        assert len(groups) == 2

    def test_empty_list_empty_dict(self):
        assert group_by_key([]) == {}

    def test_accent_name_same_group_as_ascii(self):
        m_accent = _market("Luka Dončić", 30, venue="polymarket")
        m_ascii  = _market("Luka Doncic", 30, venue="kalshi")
        groups = group_by_key([m_accent, m_ascii])
        assert len(groups) == 1

    def test_all_markets_in_correct_groups(self):
        markets = [
            _market("SGA",         25, venue="kalshi"),
            _market("SGA",         25, venue="polymarket"),
            _market("SGA",         30, venue="kalshi"),
            _market("LeBron James",25, venue="kalshi"),
        ]
        groups = group_by_key(markets)
        assert len(groups) == 3  # (sga,25), (sga,30), (lebron james,25)
