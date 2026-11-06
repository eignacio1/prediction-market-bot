"""Known-answer tests for quant/price_dynamics.py: simulated series with planted reversion, momentum and none."""
import math
import random

from prediction_market_bot.quant.price_dynamics import (
    big_move_events, hourly_regimes, lagged_regime, move_sigma, moves, price_at,
    regime_transitions, reversion_fraction, settle_proxy)

STEP = 60.0           # 1-minute grid
HOR = 900.0           # 15 min
J = 0.02              # planted jump
NOISE = 0.002


def make_game(rng, rho, n=600, jumps=(100, 250, 400, 520), start=0.5):
    """Random walk (sd NOISE) with planted jumps of +/-J; over the next 15 steps the price moves by -rho*J*sign
    in total (rho>0 reversion, rho<0 momentum, rho=0 none)."""
    p = start
    ser = [(0.0, p)]
    drift = [0.0] * (n + 20)
    for j in jumps:
        sgn = rng.choice([-1.0, 1.0])
        drift[j] += sgn * J
        for q in range(j + 1, j + 16):
            drift[q] += -sgn * rho * J / 15.0
    for i in range(1, n):
        p += rng.gauss(0, NOISE) + drift[i]
        ser.append((i * STEP, p))
    return ser


def run(rho, games=60, seed=1):
    rng = random.Random(seed)
    series = {"g%d" % i: make_game(rng, rho) for i in range(games)}
    sigma = move_sigma([d for s in series.values() for _, d, _ in moves(s, 2 * STEP)])
    ev = {g: big_move_events(s, 4.0, sigma, 2 * STEP, HOR, [300.0, HOR], tol_s=1.0, settle=False) for g, s in series.items()}
    return ev, reversion_fraction(ev, HOR, b=500)


def test_planted_reversion_recovered():
    ev, r = run(0.6)
    assert r["n_events"] >= 200
    assert abs(r["R"] - 0.6) < 0.08
    assert r["lo"] > 0.4 and r["p_two_sided"] < 0.01


def test_planted_momentum_recovered():
    _, r = run(-0.5)
    assert abs(r["R"] - (-0.5)) < 0.08
    assert r["hi"] < -0.3


def test_no_effect_interval_covers_zero():
    _, r = run(0.0)
    assert abs(r["R"]) < 0.08
    assert r["lo"] < 0 < r["hi"]
    assert r["p_two_sided"] > 0.05


def test_refractory_blocks_double_counting():
    # two jumps 5 minutes apart in the same direction: only the first counts with a 15-minute refractory
    s = [(i * STEP, 0.5) for i in range(40)]
    s = [(t, p + (0.03 if 10 <= i < 15 else 0.0) + (0.03 if i >= 15 else 0.0)) for i, (t, p) in enumerate(s)]
    ev = big_move_events(s, 3.0, 0.002, 2 * STEP, HOR, [300.0], tol_s=1.0, settle=False)
    assert len(ev) == 1


def test_gap_longer_than_max_is_not_a_move():
    s = [(0.0, 0.5), (60.0, 0.5), (7200.0, 0.9)]
    assert moves(s, 120.0) == [(60.0, 0.0, 60.0)]


def test_price_at_no_interpolation():
    s = [(0.0, 0.4), (600.0, 0.6)]
    assert price_at(s, 300.0, 100.0) is None
    assert price_at(s, 300.0, 400.0) == 0.6


def test_settle_proxy_only_when_resolved():
    assert settle_proxy([(0, 0.5), (1, 0.99)]) == 0.99
    assert settle_proxy([(0, 0.5), (1, 0.01)]) == 0.01
    assert settle_proxy([(0, 0.5), (1, 0.6)]) is None
    assert settle_proxy([]) is None


def test_move_sigma_known():
    assert math.isclose(move_sigma([3.0, -3.0, 3.0, -3.0]), 3.0)
    assert math.isnan(move_sigma([1.0]))


def test_regimes_labels_and_stability():
    # hour 0 jumpy, hour 1 calm, hour 2 jumpy, hour 3 calm (alternating) -> P(jumpy|jumpy)=0, P(jumpy|calm)=1
    pts, p = [], 0.5
    for h in range(4):
        for m in range(6):
            t = h * 3600 + m * 600
            if h % 2 == 0 and m == 2:
                p += 0.05
            pts.append((float(t), p))
    lab = hourly_regimes(pts, 3.0, 0.005, 1200.0)
    assert [lab[h] for h in range(4)] == ["jumpy", "calm", "jumpy", "calm"]
    tr = regime_transitions(lab)
    assert tr["p_jumpy_given_jumpy"] == 0.0 and tr["p_jumpy_given_calm"] == 1.0
    assert lagged_regime(lab, 3600.0 * 2 + 5) == "calm"      # hour 1 is the hour before hour 2
    assert lagged_regime(lab, 5.0) is None


def test_persistent_regime_detected():
    # every hour jumpy -> p_jumpy_given_jumpy == 1
    pts, p = [], 0.5
    for h in range(4):
        for m in range(6):
            if m == 2:
                p += 0.05
            pts.append((float(h * 3600 + m * 600), p))
    tr = regime_transitions(hourly_regimes(pts, 3.0, 0.005, 1200.0))
    assert tr["p_jumpy_given_jumpy"] == 1.0 and math.isnan(tr["p_jumpy_given_calm"])
