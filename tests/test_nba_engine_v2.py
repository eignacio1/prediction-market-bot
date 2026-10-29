"""Known-answer tests for engine_v2 (W94.1 Part C)."""
import numpy as np

from prediction_market_bot.nba_engine import engine_v2 as V


def _truth(n=200000, rho=0.20, sd=11.0, seed=3):
    rng = np.random.default_rng(seed)
    z = rng.standard_normal((2, n))
    eh = sd * z[0]
    ea = sd * (rho * z[0] + np.sqrt(1 - rho ** 2) * z[1])
    return 110 + eh, 108 + ea


def test_fit_recovers_sd_and_rho():
    h, a = _truth()
    p = V.fit_params(np.full(len(h), 110.0), np.full(len(h), 108.0), h, a)
    assert abs(p.sd_team - 11.0) < 0.1
    assert abs(p.rho - 0.20) < 0.01
    assert abs(p.hca) < 0.1 and abs(p.tbias) < 0.2


def test_closed_form_matches_simulation():
    p = V.V2Params(hca=2.0, tbias=0.0, sd_margin=13.0, sd_total=19.0)
    m, t = V.game_means(p, 112.0, 110.0)
    h, a = V.simulate(p, m, t, n=400000, seed=1)
    for fam, n, emp in (("ml", 1, np.mean(h - a >= 1)), ("spread", 5, np.mean(h - a >= 5)),
                        ("total", 225, np.mean(h + a >= 225)), ("team_total", 114, np.mean(h >= 114))):
        assert abs(V.raw_prob(p, fam, m, t, n) - emp) < 0.006, fam


def test_factor_shift_recovered_and_applied():
    rng = np.random.default_rng(5)
    n = 50000
    x = rng.integers(0, 2, n).astype(float)
    h = 110 + 1.5 * x + 10 * rng.standard_normal(n)
    a = 108 + 1.5 * x + 10 * rng.standard_normal(n)
    p = V.fit_params(np.full(n, 110.0), np.full(n, 108.0), h, a, {"alt": x}, total_factors=["alt"])
    assert abs(p.shift_total["alt"] - 3.0) < 0.3
    m0, t0 = V.game_means(p, 110.0, 108.0, {"alt": 0.0})
    m1, t1 = V.game_means(p, 110.0, 108.0, {"alt": 1.0})
    assert abs((t1 - t0) - p.shift_total["alt"]) < 1e-9 and m1 == m0


def test_platt_fixes_known_miscalibration():
    rng = np.random.default_rng(2)
    q = rng.uniform(0.05, 0.95, 80000)
    true = 1 / (1 + np.exp(-1.8 * np.log(q / (1 - q))))   # the stated probs under-state: true slope 1.8
    y = (rng.random(len(q)) < true).astype(float)
    a, b = V.fit_platt(q, y)
    assert abs(b - 1.8) < 0.08 and abs(a) < 0.05
    p = V.with_platt(V.V2Params(0, 0, 13, 19), {"ml": (a, b)})
    assert abs(V.calibrated(p, "ml", 0.7) - 1 / (1 + np.exp(-1.8 * np.log(0.7 / 0.3)))) < 0.01
    assert V.calibrated(p, "total", 0.7) == np.float64(0.7) or abs(V.calibrated(p, "total", 0.7) - 0.7) < 1e-9
