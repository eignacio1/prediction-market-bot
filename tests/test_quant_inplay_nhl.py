"""Known-answer tests for quant/inplay_nhl.py (W103.3 / B-046)."""
import math

import numpy as np
import pytest

from prediction_market_bot.quant import inplay_nhl as q


def test_classify_state():
    assert q.classify_state(5, 5, 1, 1) == "EV"
    assert q.classify_state(5, 4, 1, 1) == "H_PP"
    assert q.classify_state(4, 5, 1, 1) == "A_PP"
    assert q.classify_state(6, 5, 0, 1) == "H_EN"
    assert q.classify_state(5, 6, 1, 0) == "A_EN"
    assert q.classify_state(6, 5, 0, 1) != "A_PP"


def test_poisson_pmf_known():
    p = q._poisson_pmf(2.0)
    assert p[0] == pytest.approx(math.exp(-2))
    assert p[3] == pytest.approx(math.exp(-2) * 8 / 6)
    assert p.sum() == pytest.approx(1.0, abs=1e-9)
    assert q._poisson_pmf(0.0)[0] == 1.0


def test_skellam_sums_and_mean():
    d, p = q.skellam_pmf(1.7, 1.1)
    assert p.sum() == pytest.approx(1.0, abs=1e-9)
    assert float((d * p).sum()) == pytest.approx(0.6, abs=1e-6)


def test_symmetry_and_sum_to_one():
    o = q.outcome_probs(0, 0, 60.0, 3.0, 3.0)
    assert o["reg_home"] == pytest.approx(o["reg_away"], abs=1e-12)
    assert o["game_home"] == pytest.approx(0.5, abs=1e-9)
    assert o["reg_home"] + o["reg_tie"] + o["reg_away"] == pytest.approx(1.0, abs=1e-9)


def test_ot_formula_closed_form():
    ph, pend = q.p_ot_home(3.0, 3.0, ot_mult=1.0)
    assert pend == pytest.approx(1 - math.exp(-5 * 6 / 60))
    assert ph == pytest.approx(0.5 * pend)
    ph2, pend2 = q.p_ot_home(4.0, 2.0, ot_mult=2.0)
    assert ph2 / pend2 == pytest.approx(4.0 / 6.0)


def test_settlement_exact_tie_at_horn():
    # tied with 0 min left: game_home = P_ot_home + (1 - P_ot_end) * p_so
    o = q.outcome_probs(2, 2, 0.0, 3.4, 2.6, ot_mult=1.5, p_so_home=0.55)
    ph, pend = q.p_ot_home(3.4, 2.6, 1.5)
    assert o["reg_tie"] == 1.0
    assert o["game_home"] == pytest.approx(ph + (1 - pend) * 0.55, abs=1e-12)
    # regulation win/loss at the horn is decided with no OT
    assert q.outcome_probs(3, 2, 0.0, 3.0, 3.0)["game_home"] == pytest.approx(1.0)
    assert q.outcome_probs(1, 2, 0.0, 3.0, 3.0)["game_home"] == pytest.approx(0.0)


def test_total_over_is_poisson_tail():
    # 20 min left each, lam=3 per 60 -> L_h=L_a=1 -> remaining total ~ Poisson(2). 2 scored, line 4.5 -> need >2.5 -> P(K>=3)
    p = q.p_total_over(1, 1, 20.0, 3.0, 3.0, 4.5)
    expect = 1 - sum(math.exp(-2) * 2 ** k / math.factorial(k) for k in range(3))
    assert p == pytest.approx(expect, abs=1e-9)
    assert q.p_total_over(3, 3, 0.0, 3.0, 3.0, 5.5) == 1.0
    assert q.p_total_over(2, 2, 0.0, 3.0, 3.0, 5.5) == 0.0


def test_power_play_and_empty_net_shift_probability():
    st = dict(q.NEUTRAL)
    st["H_PP"] = (1.8, 0.8, 1.0)
    st["A_EN"] = (2.5, 4.0, None)
    base = q.outcome_probs(0, 0, 20.0, 3.0, 3.0)["reg_home"]
    pp = q.outcome_probs(0, 0, 20.0, 3.0, 3.0, "H_PP", st)["reg_home"]
    assert pp > base
    # empty net for the away side (they trail): the home team scores more often into the open net
    en = q.outcome_probs(1, 0, 3.0, 3.0, 3.0, "A_EN", st)
    ev = q.outcome_probs(1, 0, 3.0, 3.0, 3.0)
    assert en["L_h"] > ev["L_h"] and en["L_a"] > ev["L_a"]


def test_monte_carlo_agrees_with_closed_form():
    rng = np.random.default_rng(3)
    lam_h, lam_a, tau = 3.2, 2.8, 25.0
    n = 400_000
    gh = rng.poisson(lam_h * tau / 60, n)
    ga = rng.poisson(lam_a * tau / 60, n)
    d = 1 + gh - ga  # leading by 1 now
    mc_reg_home = float(np.mean(d > 0))
    assert q.outcome_probs(1, 0, tau, lam_h, lam_a)["reg_home"] == pytest.approx(mc_reg_home, abs=0.004)
