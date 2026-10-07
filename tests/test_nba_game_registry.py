"""W58.2 Part B: NBA game MarketTypes, series map, ticker grammar, T1/T2/T3 cells.

Tickers are real Kalshi samples captured 2026-10-06 (exp_output/NBA/discovery.json).
Every one of the 30 team codes is exercised (the NHL 2-letter-code drop, GG-403, must not recur).
"""
import pytest

from prediction_market_bot.c5_execution.market_type_registry import (
    CellStatus, ExecutionBand, MarketType, derive_game_date, get_cell,
    market_type_for_ticker, parse_ticker_date, series_ticker_for, sport_for)

NBA_CODES = (
    "ATL BOS BKN CHA CHI CLE DAL DEN DET GSW HOU IND LAC LAL MEM MIA MIL MIN NOP NYK OKC "
    "ORL PHI PHX POR SAC SAS TOR UTA WAS").split()

SERIES = {
    MarketType.NBA_MONEYLINE: "KXNBAGAME",
    MarketType.NBA_SPREAD: "KXNBASPREAD",
    MarketType.NBA_GAME_TOTAL: "KXNBATOTAL",
    MarketType.NBA_TEAM_TOTAL: "KXNBATEAMTOTAL",
}

REAL = [
    ("KXNBAGAME-26OCT13INDOKC-OKC", MarketType.NBA_MONEYLINE, "2026-10-13", "INDOKC"),
    ("KXNBASPREAD-26OCT06BKNCHA-BKN38", MarketType.NBA_SPREAD, "2026-10-06", "BKNCHA"),
    ("KXNBATOTAL-26OCT07MININD-256", MarketType.NBA_GAME_TOTAL, "2026-10-07", "MININD"),
]


def test_thirty_codes():
    assert len(NBA_CODES) == 30 == len(set(NBA_CODES))


@pytest.mark.parametrize("ticker,mt,date,teams", REAL)
def test_real_tickers_parse(ticker, mt, date, teams):
    assert market_type_for_ticker(ticker) is mt
    p = parse_ticker_date(ticker)
    assert (p.game_date, p.teams_raw) == (date, teams)
    assert derive_game_date(ticker) == date


def test_every_team_code_parses_in_both_positions():
    for i, code in enumerate(NBA_CODES):
        other = NBA_CODES[(i + 1) % 30]
        for mt, series in SERIES.items():
            ticker = f"{series}-26OCT20{code}{other}-{code}"
            assert market_type_for_ticker(ticker) is mt
            p = parse_ticker_date(ticker)
            assert p.teams_raw == code + other
            assert p.teams_raw[:3] in NBA_CODES and p.teams_raw[3:] in NBA_CODES


def test_series_and_sport():
    for mt, series in SERIES.items():
        assert series_ticker_for(mt) == series
        assert sport_for(mt) == "nba"


@pytest.mark.parametrize("mt", list(SERIES))
def test_pregame_cells_not_implemented_until_logging(mt):
    for b in (ExecutionBand.T1_MULTI_DAY, ExecutionBand.T2_SAME_DAY, ExecutionBand.T3_PRE_TIP):
        assert get_cell(mt, b).status in (CellStatus.NOT_IMPLEMENTED, CellStatus.SHADOW)
