"""
Tests for game_market_settlement.py (T-527, T-535).

Covers every NFL game-market type (moneyline, spread, game total, team
total) with: a favourite losing outright, a YES/NO on each side, a
moneyline exact tie, and a push on an integer spread/total.

Two tiers of fixture data are used, deliberately:

- The BAL/KC "26SEP07" fixture (27-17) below is entirely synthetic/invented
  -- it does not correspond to a real game. It exists because the push-
  refusal tests need a contrived actual_stat that lands exactly on an
  integer threshold, which live half-point-line NFL data cannot produce
  (see game_market_settlement.py's module docstring: every real Kalshi
  spread/total/team-total strike currently observed is a half-point line).
- The "Real 2025-10-05 games" block further down uses three genuine
  completed 2025-season games, live-fetched via direct `curl` against
  ESPN's real scoreboard endpoint during T-535 (not memory, not an existing
  fixture) and cross-checked against real box scores, including one game
  decided by <=3 points (CAR 27 - MIA 24, margin=3) as required by this
  block's Deliverable 3. These cover derive_actual_stat() for all four
  market types against real, not invented, final scores. The moneyline
  tie test above (DAL 40 - GB 40, 2025-09-28) was independently
  re-verified live against ESPN during T-535 as well and found accurate.
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
# Real 2025-10-05 games (T-535) -- live-verified via direct curl against
# ESPN's real scoreboard endpoint during this session, not memory or an
# existing fixture. All four market types, across three real games,
# including one decided by <=3 points (CAR/MIA, margin=3) per Deliverable 3.
# ---------------------------------------------------------------------------

# Game A: CAR (home) 27 - MIA (away) 24 -- margin=3, the required <=3-point
# game. Combined total = 51.

def test_real_game_moneyline_car_beats_mia_by_3():
    actual_stat, label = derive_actual_stat(
        MarketType.NFL_MONEYLINE,
        "KXNFLGAME-25OCT05CARMIA-CAR",
        home_team_code="CAR",
        away_team_code="MIA",
        home_score=27,
        away_score=24,
    )
    assert actual_stat == 3
    assert label == "point_margin_for_CAR"
    check_settlement_ambiguity(MarketType.NFL_MONEYLINE, actual_stat, threshold=0)


def test_real_game_spread_car_covers_2_5():
    actual_stat, label = derive_actual_stat(
        MarketType.NFL_SPREAD,
        "KXNFLSPREAD-25OCT05CARMIA-CAR25",
        home_team_code="CAR",
        away_team_code="MIA",
        home_score=27,
        away_score=24,
    )
    assert actual_stat == 3
    assert label == "point_margin_for_CAR"
    assert actual_stat >= 2.5  # covers
    check_settlement_ambiguity(MarketType.NFL_SPREAD, actual_stat, threshold=2.5)


def test_real_game_total_car_mia_over_50_5():
    actual_stat, label = derive_actual_stat(
        MarketType.NFL_GAME_TOTAL,
        "KXNFLTOTAL-25OCT05CARMIA-50",
        home_team_code="CAR",
        away_team_code="MIA",
        home_score=27,
        away_score=24,
    )
    assert actual_stat == 51
    assert label == "combined_final_score"
    assert actual_stat >= 50.5  # over
    check_settlement_ambiguity(MarketType.NFL_GAME_TOTAL, actual_stat, threshold=50.5)


def test_real_game_team_total_car_over_24_5():
    actual_stat, label = derive_actual_stat(
        MarketType.NFL_TEAM_TOTAL,
        "KXNFLTEAMTOTAL-25OCT05CARMIA-CAR24",
        home_team_code="CAR",
        away_team_code="MIA",
        home_score=27,
        away_score=24,
    )
    assert actual_stat == 27
    assert label == "team_final_score_CAR"
    assert actual_stat >= 24.5  # over
    check_settlement_ambiguity(MarketType.NFL_TEAM_TOTAL, actual_stat, threshold=24.5)


# Game B: BAL (home) 10 - HOU (away) 44 -- blowout, margin=34. Combined
# total = 54.

def test_real_game_moneyline_hou_beats_bal_by_34():
    actual_stat, label = derive_actual_stat(
        MarketType.NFL_MONEYLINE,
        "KXNFLGAME-25OCT05BALHOU-HOU",
        home_team_code="BAL",
        away_team_code="HOU",
        home_score=10,
        away_score=44,
    )
    assert actual_stat == 34
    assert label == "point_margin_for_HOU"


def test_real_game_spread_hou_covers_20_5():
    actual_stat, _label = derive_actual_stat(
        MarketType.NFL_SPREAD,
        "KXNFLSPREAD-25OCT05BALHOU-HOU20",
        home_team_code="BAL",
        away_team_code="HOU",
        home_score=10,
        away_score=44,
    )
    assert actual_stat == 34
    assert actual_stat >= 20.5  # covers
    check_settlement_ambiguity(MarketType.NFL_SPREAD, actual_stat, threshold=20.5)


def test_real_game_total_bal_hou_over_47_5():
    actual_stat, _label = derive_actual_stat(
        MarketType.NFL_GAME_TOTAL,
        "KXNFLTOTAL-25OCT05BALHOU-47",
        home_team_code="BAL",
        away_team_code="HOU",
        home_score=10,
        away_score=44,
    )
    assert actual_stat == 54
    assert actual_stat >= 47.5  # over
    check_settlement_ambiguity(MarketType.NFL_GAME_TOTAL, actual_stat, threshold=47.5)


def test_real_game_team_total_bal_under_20_5():
    actual_stat, label = derive_actual_stat(
        MarketType.NFL_TEAM_TOTAL,
        "KXNFLTEAMTOTAL-25OCT05BALHOU-BAL20",
        home_team_code="BAL",
        away_team_code="HOU",
        home_score=10,
        away_score=44,
    )
    assert actual_stat == 10
    assert label == "team_final_score_BAL"
    assert actual_stat < 20.5  # under
    check_settlement_ambiguity(MarketType.NFL_TEAM_TOTAL, actual_stat, threshold=20.5)


# Game C: NYJ (home) 22 - DAL (away) 37 -- margin=15. Combined total = 59.

def test_real_game_moneyline_dal_beats_nyj_by_15():
    actual_stat, label = derive_actual_stat(
        MarketType.NFL_MONEYLINE,
        "KXNFLGAME-25OCT05NYJDAL-DAL",
        home_team_code="NYJ",
        away_team_code="DAL",
        home_score=22,
        away_score=37,
    )
    assert actual_stat == 15
    assert label == "point_margin_for_DAL"


def test_real_game_spread_dal_covers_6_5():
    actual_stat, _label = derive_actual_stat(
        MarketType.NFL_SPREAD,
        "KXNFLSPREAD-25OCT05NYJDAL-DAL6",
        home_team_code="NYJ",
        away_team_code="DAL",
        home_score=22,
        away_score=37,
    )
    assert actual_stat == 15
    assert actual_stat >= 6.5  # covers
    check_settlement_ambiguity(MarketType.NFL_SPREAD, actual_stat, threshold=6.5)


def test_real_game_total_nyj_dal_over_55_5():
    actual_stat, _label = derive_actual_stat(
        MarketType.NFL_GAME_TOTAL,
        "KXNFLTOTAL-25OCT05NYJDAL-55",
        home_team_code="NYJ",
        away_team_code="DAL",
        home_score=22,
        away_score=37,
    )
    assert actual_stat == 59
    assert actual_stat >= 55.5  # over
    check_settlement_ambiguity(MarketType.NFL_GAME_TOTAL, actual_stat, threshold=55.5)


def test_real_game_team_total_nyj_under_24_5():
    actual_stat, label = derive_actual_stat(
        MarketType.NFL_TEAM_TOTAL,
        "KXNFLTEAMTOTAL-25OCT05NYJDAL-NYJ24",
        home_team_code="NYJ",
        away_team_code="DAL",
        home_score=22,
        away_score=37,
    )
    assert actual_stat == 22
    assert label == "team_final_score_NYJ"
    assert actual_stat < 24.5  # under
    check_settlement_ambiguity(MarketType.NFL_TEAM_TOTAL, actual_stat, threshold=24.5)


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
