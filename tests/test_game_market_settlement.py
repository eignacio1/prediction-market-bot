"""
Tests for game_market_settlement.py (T-527).

Covers every NFL game-market type (moneyline, spread, game total, team
total) with: a favourite losing outright, a YES/NO on each side, a
moneyline exact tie, and a push on an integer spread/total. Real ticker
shapes and real completed-game scores are used where practical (see
docs/verification notes in DECISION_LOG / SESSION_CLAIMS for the three
real-game ESPN verification, done separately in
tests/test_nfl_espn_results.py against live network data).
"""
from __future__ import annotations

import pytest

from prediction_market_bot.c5_execution.game_market_settlement import (
    SettlementAmbiguityError,
    check_settlement_ambiguity,
    derive_actual_stat,
)
from prediction_market_bot.c5_execution.market_type_registry import MarketType


# ---------------------------------------------------------------------------
# Moneyline
# ---------------------------------------------------------------------------

def test_moneyline_yes_team_wins_as_home():
    # Real settled market: KXNFLGAME-26AUG29CHITEN-CHI -> Chicago (home) beat
    # Tennessee (away); Kalshi resolved this market YES.
    actual_stat, label = derive_actual_stat(
        MarketType.NFL_MONEYLINE,
        "KXNFLGAME-26AUG29CHITEN-CHI",
        home_team_code="CHI",
        away_team_code="TEN",
        home_score=24,
        away_score=17,
    )
    assert actual_stat == 7
    assert label == "point_margin_for_CHI"
    assert actual_stat >= 0  # threshold for moneyline is 0 -> YES


def test_moneyline_yes_team_is_away_and_loses():
    # KXNFLGAME-26AUG29CHITEN-TEN -> Tennessee (away) lost; Kalshi resolved NO.
    actual_stat, label = derive_actual_stat(
        MarketType.NFL_MONEYLINE,
        "KXNFLGAME-26AUG29CHITEN-TEN",
        home_team_code="CHI",
        away_team_code="TEN",
        home_score=24,
        away_score=17,
    )
    assert actual_stat == -7
    assert label == "point_margin_for_TEN"
    assert actual_stat < 0  # NO


def test_moneyline_favourite_loses_outright():
    # HOU (home) beat TEN (away) 26-0 in the real 2025-09-28 game; a market
    # naming TEN (the loser, presumptively the underdog here) must derive a
    # negative margin regardless of who was favoured pregame -- the
    # derivation module has no notion of "favourite," only final score.
    actual_stat, label = derive_actual_stat(
        MarketType.NFL_MONEYLINE,
        "KXNFLGAME-25SEP28HOUTEN-TEN",
        home_team_code="HOU",
        away_team_code="TEN",
        home_score=26,
        away_score=0,
    )
    assert actual_stat == -26
    assert label == "point_margin_for_TEN"


def test_moneyline_exact_tie_real_game():
    # Real 2025-09-28 game: DAL 40 - GB 40, a genuine NFL tie.
    actual_stat, _label = derive_actual_stat(
        MarketType.NFL_MONEYLINE,
        "KXNFLGAME-25SEP28GBDAL-DAL",
        home_team_code="DAL",
        away_team_code="GB",
        home_score=40,
        away_score=40,
    )
    assert actual_stat == 0
    with pytest.raises(SettlementAmbiguityError, match="Tie"):
        check_settlement_ambiguity(MarketType.NFL_MONEYLINE, actual_stat, threshold=0)


def test_moneyline_no_tie_does_not_raise():
    check_settlement_ambiguity(MarketType.NFL_MONEYLINE, actual_stat=7, threshold=0)
    check_settlement_ambiguity(MarketType.NFL_MONEYLINE, actual_stat=-7, threshold=0)


# ---------------------------------------------------------------------------
# Spread
# ---------------------------------------------------------------------------

def test_spread_yes_team_covers():
    # KXNFLSPREAD-...-BAL42 style suffix; BAL is home, wins by 10.
    actual_stat, label = derive_actual_stat(
        MarketType.NFL_SPREAD,
        "KXNFLSPREAD-26SEP07BALKC-BAL42",
        home_team_code="BAL",
        away_team_code="KC",
        home_score=27,
        away_score=17,
    )
    assert actual_stat == 10
    assert label == "point_margin_for_BAL"


def test_spread_yes_team_is_away_and_does_not_cover():
    actual_stat, label = derive_actual_stat(
        MarketType.NFL_SPREAD,
        "KXNFLSPREAD-26SEP07BALKC-KC7",
        home_team_code="BAL",
        away_team_code="KC",
        home_score=27,
        away_score=17,
    )
    assert actual_stat == -10
    assert label == "point_margin_for_KC"


def test_spread_push_on_integer_line_is_refused():
    actual_stat, _label = derive_actual_stat(
        MarketType.NFL_SPREAD,
        "KXNFLSPREAD-26SEP07BALKC-BAL10",
        home_team_code="BAL",
        away_team_code="KC",
        home_score=27,
        away_score=17,
    )
    assert actual_stat == 10
    with pytest.raises(SettlementAmbiguityError, match="push"):
        check_settlement_ambiguity(MarketType.NFL_SPREAD, actual_stat, threshold=10)


def test_spread_no_push_does_not_raise():
    check_settlement_ambiguity(MarketType.NFL_SPREAD, actual_stat=10, threshold=7)


# ---------------------------------------------------------------------------
# Game total
# ---------------------------------------------------------------------------

def test_game_total_over():
    actual_stat, label = derive_actual_stat(
        MarketType.NFL_GAME_TOTAL,
        "KXNFLTOTAL-26SEP07BALKC-40",
        home_team_code="BAL",
        away_team_code="KC",
        home_score=27,
        away_score=17,
    )
    assert actual_stat == 44
    assert label == "combined_final_score"
    assert actual_stat >= 40  # over the 40 line -> YES


def test_game_total_under():
    actual_stat, _label = derive_actual_stat(
        MarketType.NFL_GAME_TOTAL,
        "KXNFLTOTAL-26SEP07BALKC-50",
        home_team_code="BAL",
        away_team_code="KC",
        home_score=27,
        away_score=17,
    )
    assert actual_stat == 44
    assert actual_stat < 50  # under -> NO


def test_game_total_push_on_integer_line_is_refused():
    actual_stat, _label = derive_actual_stat(
        MarketType.NFL_GAME_TOTAL,
        "KXNFLTOTAL-26SEP07BALKC-44",
        home_team_code="BAL",
        away_team_code="KC",
        home_score=27,
        away_score=17,
    )
    with pytest.raises(SettlementAmbiguityError, match="push"):
        check_settlement_ambiguity(MarketType.NFL_GAME_TOTAL, actual_stat, threshold=44)


# ---------------------------------------------------------------------------
# Team total
# ---------------------------------------------------------------------------

def test_team_total_home_team_named():
    actual_stat, label = derive_actual_stat(
        MarketType.NFL_TEAM_TOTAL,
        "KXNFLTEAMTOTAL-26SEP07BALKC-BAL24",
        home_team_code="BAL",
        away_team_code="KC",
        home_score=27,
        away_score=17,
    )
    assert actual_stat == 27
    assert label == "team_final_score_BAL"
    assert actual_stat >= 24  # over -> YES


def test_team_total_away_team_named():
    actual_stat, label = derive_actual_stat(
        MarketType.NFL_TEAM_TOTAL,
        "KXNFLTEAMTOTAL-26SEP07BALKC-KC20",
        home_team_code="BAL",
        away_team_code="KC",
        home_score=27,
        away_score=17,
    )
    assert actual_stat == 17
    assert label == "team_final_score_KC"
    assert actual_stat < 20  # under -> NO


def test_team_total_push_on_integer_line_is_refused():
    actual_stat, _label = derive_actual_stat(
        MarketType.NFL_TEAM_TOTAL,
        "KXNFLTEAMTOTAL-26SEP07BALKC-BAL27",
        home_team_code="BAL",
        away_team_code="KC",
        home_score=27,
        away_score=17,
    )
    with pytest.raises(SettlementAmbiguityError, match="push"):
        check_settlement_ambiguity(MarketType.NFL_TEAM_TOTAL, actual_stat, threshold=27)


# ---------------------------------------------------------------------------
# Error paths
# ---------------------------------------------------------------------------

def test_unsupported_market_type_raises_value_error():
    with pytest.raises(ValueError, match="unsupported market_type"):
        derive_actual_stat(
            MarketType.MLB_PLAYER_PROP_HITS,
            "KXMLBHIT-260907-JUDGE",
            home_team_code="NYY",
            away_team_code="BOS",
            home_score=5,
            away_score=3,
        )


def test_strike_team_matching_neither_side_raises_value_error():
    with pytest.raises(ValueError, match="matches neither"):
        derive_actual_stat(
            MarketType.NFL_MONEYLINE,
            "KXNFLGAME-26SEP07BALKC-NYJ",
            home_team_code="BAL",
            away_team_code="KC",
            home_score=27,
            away_score=17,
        )


def test_ticker_with_no_strike_suffix_raises_value_error():
    with pytest.raises(ValueError, match="no strike suffix"):
        derive_actual_stat(
            MarketType.NFL_MONEYLINE,
            "KXNFLGAME",
            home_team_code="BAL",
            away_team_code="KC",
            home_score=27,
            away_score=17,
        )


def test_check_settlement_ambiguity_rejects_unsupported_market_type():
    with pytest.raises(ValueError, match="unsupported market_type"):
        check_settlement_ambiguity(MarketType.MLB_PLAYER_PROP_HITS, 5, 3)
