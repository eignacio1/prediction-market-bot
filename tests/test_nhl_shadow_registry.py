"""EXP-036 / T-654 (Wave 52.A): the nine NHL pre-game cells that log shadow rows are SHADOW.

Mirrors T-608's NFL flip test (tests/test_pregame_shadow_framework.py). SHADOW is
evaluate-and-log only; in-play NHL bands stay NOT_IMPLEMENTED.
"""
from prediction_market_bot.c5_execution.market_type_registry import (
    CellStatus, ExecutionBand, MarketType, get_cell)

_NHL = (MarketType.NHL_MONEYLINE, MarketType.NHL_PUCK_LINE, MarketType.NHL_GAME_TOTAL)
_PREGAME = (ExecutionBand.T1_MULTI_DAY, ExecutionBand.T2_SAME_DAY, ExecutionBand.T3_PRE_TIP)


def test_nhl_pregame_cells_shadow_cite_exp036():
    for mt in _NHL:
        for b in _PREGAME:
            c = get_cell(mt, b)
            assert c.status is CellStatus.SHADOW and c.citing_decision == "EXP-036", (mt, b)


def test_nhl_non_pregame_bands_untouched():
    for mt in _NHL:
        for b in ExecutionBand:
            if b in _PREGAME:
                continue
            try:
                c = get_cell(mt, b)
            except KeyError:
                continue
            assert c.status is not CellStatus.SHADOW, (mt, b)
