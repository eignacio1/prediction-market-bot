"""W85.2: position_gate is pure and unwired. Zero skill means no order; a ladder is one exposure."""
import math
from pathlib import Path

from prediction_market_bot.c5_execution import position_gate as pg


def _c(ts="t1", tk="K-1", band="T1", p=0.60, mid=0.40, bid=0.39, ask=0.41, fee=0.01, game="g", fam="TOTAL", stake=1.0):
    return pg.Candidate(ts, tk, band, game, fam, p, mid, bid, ask, fee, stake)


def test_skill_weight_missing_or_worse_is_zero():
    assert pg.skill_weight(None, 0.25) == 0.0
    assert pg.skill_weight(0.24, None) == 0.0
    assert pg.skill_weight(0.26, 0.25) == 0.0
    assert 0 < pg.skill_weight(0.24, 0.25) < 1


def test_shrink_endpoints():
    assert pg.shrink(0.7, 0.4, 0.0) == 0.4
    assert math.isclose(pg.shrink(0.7, 0.4, 1.0), 0.7)
    assert math.isclose(pg.shrink(0.7, 0.4, 0.5), 0.55)


def test_zero_skill_means_no_order():
    rows = [_c(tk="K-%d" % i, p=0.99) for i in range(10)]
    assert pg.select(rows, weight=0.0, bar=0.0) == []


def test_unmeasured_error_bar_blocks_everything():
    assert pg.error_bar([0.1]) == math.inf
    assert pg.select([_c()], weight=1.0, bar=pg.error_bar([])) == []


def test_clears_only_above_bar():
    assert pg.clears(_c(), 1.0, 0.05) == "yes"
    assert pg.clears(_c(), 1.0, 0.50) is None


def test_no_side_edge():
    c = _c(p=0.10, mid=0.40)
    assert pg.clears(c, 1.0, 0.05) == "no"


def test_one_position_per_market_per_band_first_row_wins():
    rows = [_c(ts="t2", p=0.9), _c(ts="t1", p=0.8), _c(ts="t3", band="T2", p=0.8)]
    kept = pg.select(rows, 1.0, 0.05)
    assert len(kept) == 2
    assert {(c.band, c.ts) for c, _ in kept} == {("T1", "t1"), ("T2", "t3")}


def test_full_ladder_from_one_curve_is_one_exposure():
    rows = [_c(tk="K-%d" % i, ts="t%d" % i, stake=1.0) for i in range(12)]
    kept = pg.select(rows, 1.0, 0.05)
    assert len(kept) == 12
    ex = pg.ladder_exposures(kept)
    assert list(ex) == [("g", "TOTAL", "yes")]
    assert ex[("g", "TOTAL", "yes")] == 1.0


def test_distinct_games_and_sides_are_distinct_exposures():
    rows = [_c(tk="A", game="g1"), _c(tk="B", game="g2"), _c(tk="C", game="g1", p=0.05)]
    assert len(pg.ladder_exposures(pg.select(rows, 1.0, 0.05))) == 3


def test_module_is_pure_and_unwired():
    src = Path(pg.__file__).read_text()
    for banned in ("import os", "import time", "import datetime", "open(", "requests", "urllib"):
        assert banned not in src
    root = Path(pg.__file__).resolve().parents[1]
    importers = [p for p in root.rglob("*.py") if p.name != "position_gate.py" and "position_gate" in p.read_text()]
    assert importers == []
