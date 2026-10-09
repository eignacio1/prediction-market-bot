"""GG-527 Part B: T4M-PROJ places no paper stake for post-2026 games unless re-enabled."""
import logging
import pathlib

import pytest

from prediction_market_bot import run_t4_mlb_live as m

T26 = "KXMLBHIT-26OCT081700CLECWS-CLEBROCCHIO4-2"   # 2026 postseason
T27 = "KXMLBHIT-27APR021410CINMIL-MILWCONTRERAS24-2"  # 2027


@pytest.fixture(autouse=True)
def _reset(monkeypatch):
    m._stand_down_skips.clear()
    monkeypatch.setattr(m, "T4M_PROJ_POST_2026_REENABLE", False)
    yield
    m._stand_down_skips.clear()


def test_default_is_off():
    assert m.T4M_PROJ_POST_2026_REENABLE is False


def test_2026_postseason_still_stakes():
    assert m.stake_stood_down(T26) is False
    assert not m._stand_down_skips


def test_2027_game_places_no_stake_and_is_counted():
    assert m.stake_stood_down(T27) is True
    assert m._stand_down_skips[T27] == 1


def test_reenable_places_stake(monkeypatch):
    monkeypatch.setattr(m, "T4M_PROJ_POST_2026_REENABLE", True)
    assert m.stake_stood_down(T27) is False


def test_one_log_line_per_ticker_not_per_cycle(caplog):
    with caplog.at_level(logging.WARNING, logger=m.logger.name):
        for _ in range(50):
            assert m.stake_stood_down(T27)
    assert sum("GG-527 stand-down" in r.getMessage() for r in caplog.records) == 1
    assert m._stand_down_skips[T27] == 50


def test_gate_sits_after_cycle_log_write_and_before_placement():
    """Ordering guard: cycle-log row (p_t4/mip) is built before the gate; the gate is
    before the forecast/stake record, so a stood-down game still logs its evaluation."""
    src = pathlib.Path(m.__file__).read_text()
    gate = src.index("if stake_stood_down(ticker)")
    assert src.rindex('"p_t4"', 0, gate) < gate
    assert gate < src.index("fc_record = {", gate)
