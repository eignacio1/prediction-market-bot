import math
import random

import pytest

from prediction_market_bot.quant import weather_calib as w
from prediction_market_bot.quant.money import fee_rate


def test_settle_semantics():
    assert w.settle_yes(68, None, 69) == 1 and w.settle_yes(68, None, 68) == 0
    assert w.settle_yes(None, 61, 60) == 1 and w.settle_yes(None, 61, 61) == 0
    assert w.settle_yes(63, 64, 63) == 1 and w.settle_yes(63, 64, 64) == 1 and w.settle_yes(63, 64, 65) == 0


def test_ladder_probs_sum_to_one():
    # tails + 2-wide buckets covering the line: the ladder partitions the integers
    mu, s = 66.3, 2.4
    ladder = [(None, 61)] + [(f, f + 1) for f in range(61, 67 + 1, 2)] + [(68, None)]
    # cap-tail <=60, buckets 61-62,63-64,65-66,67-68 ... then floor tail >=69 : adjust to be an exact partition
    ladder = [(None, 61), (61, 62), (63, 64), (65, 66), (67, 68), (68, None)]
    # 61-62, 63-64... leave 67-68 and >=69 : bucket (67,68) and (68,None) overlap at 68 -> use true partition below
    part = [(None, 61), (61, 62), (63, 64), (65, 66), (67, 68), (68, None)][:5] + [(68, None)]
    total = sum(w.strike_prob(mu, s, f, c) for f, c in [(None, 61), (61, 62), (63, 64), (65, 66), (67, 68)]) \
        + w.strike_prob(mu, s, 68, None)
    assert total == pytest.approx(1.0, abs=1e-12)


def test_strike_prob_matches_simulation_known_truth():
    rnd = random.Random(7)
    mu, s, n = 70.2, 3.0, 200000
    xs = [round(rnd.gauss(mu, s)) for _ in range(n)]
    for f, c in [(72, None), (None, 66), (68, 69), (70, 71)]:
        emp = sum(w.settle_yes(f, c, x) for x in xs) / n
        assert w.strike_prob(mu, s, f, c) == pytest.approx(emp, abs=0.004)


def test_fit_error_known_answer():
    fc = [70.0, 72.0, 68.0, 75.0]
    act = [71.0, 74.0, 69.0, 76.0]  # errors 1,2,1,1 -> bias 1.25
    b, sd = w.fit_error(fc, act)
    assert b == pytest.approx(1.25)
    assert sd == pytest.approx(math.sqrt(((0.25) ** 2 * 3 + 0.75 ** 2) / 3))
    with pytest.raises(ValueError):
        w.fit_error([1.0], [1.0])


def test_trade_toward_and_realised():
    # model says 0.60, price 0.40, half spread 0.01 -> buy YES at 0.41
    r = w.trade_toward(0.60, 0.40, 0.01, "KXHIGHNY")
    assert r["side"] == "yes"
    assert r["edge"] == pytest.approx(0.60 - 0.41 - fee_rate("KXHIGHNY", 0.41))
    r2 = w.trade_toward(0.20, 0.40, 0.01, "KXHIGHNY")
    assert r2["side"] == "no" and r2["ask_no"] == pytest.approx(0.61)
    assert w.realised("yes", 0.41, 0.60, 1, "KXHIGHNY") == pytest.approx(1 - 0.41 - fee_rate("KXHIGHNY", 0.41))
    assert w.realised("no", 0.41, 0.61, 1, "KXHIGHNY") == pytest.approx(0 - 0.61 - fee_rate("KXHIGHNY", 0.61))
