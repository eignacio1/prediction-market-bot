"""Known-answer tests for the W93.4 NFL board (nfl_engine/board_v2.py)."""
import numpy as np
import pandas as pd

from prediction_market_bot.nfl_engine.board_v2 import (
    Library, build_library, price_board, _median_gap,
)


def _planted(n=4000, seed=1, spike=0.15):
    """Library with a planted spike: margin==3 with prob `spike`, else a discretised normal; total ~ N(45, 9)."""
    rng = np.random.default_rng(seed)
    m = np.round(rng.normal(0, 13, n)).astype(int)
    hit = rng.random(n) < spike
    m[hit] = 3
    t = np.round(rng.normal(45, 9, n)).astype(int).clip(10, 90)
    t = t + (t - m) % 2   # a real final has total and margin of the same parity
    line = np.zeros(n)
    tline = np.full(n, 45.0)
    return Library(m, t, line, tline, np.zeros(n, int))


def test_median_anchor_is_exact():
    lib = _planted()
    b = price_board(lib, line=2.5, total=47.5)
    assert abs(_median_gap(b.m, b.p, 2.5)) < 1e-3
    assert abs(_median_gap(b.t, b.p, 47.5)) < 1e-3


def test_planted_spike_survives_the_move():
    lib = _planted(spike=0.15)
    b0 = price_board(lib, line=0.0, total=45.0)
    b1 = price_board(lib, line=3.0, total=45.0)
    assert 0.12 < b0.p_margin_eq(3) < 0.22
    # moving the centre must not smear the spike away
    assert b1.p_margin_eq(3) > 0.10


def test_probabilities_sum_and_ladders_are_coherent():
    b = price_board(_planted(), line=-3.5, total=41.5)
    assert abs(b.p.sum() - 1) < 1e-9
    ge = [b.p_margin_ge(k) for k in range(-20, 21)]
    assert all(x >= y - 1e-12 for x, y in zip(ge, ge[1:]))          # spread ladder monotone
    tg = [b.p_total_ge(k) for k in range(20, 70)]
    assert all(x >= y - 1e-12 for x, y in zip(tg, tg[1:]))          # total ladder monotone
    # home wins + away wins (+ ties) partition: ML = P(m>0) + 0.5 P(m=0); symmetric complement
    away = float(b.p[b.m < 0].sum() + 0.5 * b.p[b.m == 0].sum())
    assert abs(b.p_home_win() + away - 1) < 1e-9
    # team totals: home pts + away pts = total, so mean of the two team means equals mean total
    pts_h = (b.t + b.m) // 2
    pts_a = (b.t - b.m) // 2
    assert abs((b.p * (pts_h + pts_a)).sum() - b.mean_total()) < 1e-9


def test_favourite_wins_more_when_line_is_larger():
    lib = _planted()
    lo = price_board(lib, line=1.5, total=45.0).p_home_win()
    hi = price_board(lib, line=7.5, total=45.0).p_home_win()
    assert hi > lo > 0.5


def test_build_library_rolling_origin():
    sched = pd.DataFrame({
        "season": [2000, 2001, 2002], "home_score": [20, 24, 17], "away_score": [10, 27, 17],
        "spread_line": [3.0, -1.0, 0.0], "total_line": [40.0, 44.0, 38.0],
    })
    lib = build_library(sched, before_season=2002)
    assert list(lib.m) == [10, -3] and list(lib.t) == [30, 51]
