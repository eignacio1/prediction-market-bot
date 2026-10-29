"""EXP-044b live entry (W94.1 Part C): side symmetry, strike rule and parameter-hash stability for the v2 challenger."""
import numpy as np

from prediction_market_bot.nba_engine import engine_v2 as V, live_v2 as L2

PARSED = dict(event_ticker="KXNBAGAME-26OCT28OKCDAL", game_date="2026-10-28", away="OKC", home="DAL", subject="DAL", strike=None)


def _p():
    p = V.V2Params(hca=2.0, tbias=0.0, sd_margin=14.0, sd_total=19.0)
    return V.with_platt(p, {"ml": (-0.2, 1.9), "spread": (0.0, 1.0), "total": (0.0, 1.0), "team_total": (0.0, 1.0)})


def test_moneyline_sides_sum_to_one():
    p = _p()
    a = L2.engine_p(p, 3.0, 224.0, dict(PARSED, market_type="NBA_MONEYLINE", subject="DAL"))
    b = L2.engine_p(p, 3.0, 224.0, dict(PARSED, market_type="NBA_MONEYLINE", subject="OKC"))
    assert abs(a + b - 1.0) < 1e-12 and a > 0.5


def test_strike_rule_known_answer():
    p = V.V2Params(hca=0.0, tbias=0.0, sd_margin=14.0, sd_total=19.0)   # no Platt: identity
    # suffix 220 -> strike 219.5 -> P(total >= 220) = 1 - Phi((219.5 - 224) / 19)
    q = L2.engine_p(p, 0.0, 224.0, dict(PARSED, market_type="NBA_GAME_TOTAL", subject="", strike=219.5))
    assert abs(q - (1.0 - V.ND.cdf((219.5 - 224.0) / 19.0))) < 1e-12


def test_away_team_total_uses_away_mean_and_spread_monotone():
    p = _p()
    home = L2.engine_p(p, 6.0, 224.0, dict(PARSED, market_type="NBA_TEAM_TOTAL", subject="DAL", strike=114.5))
    away = L2.engine_p(p, 6.0, 224.0, dict(PARSED, market_type="NBA_TEAM_TOTAL", subject="OKC", strike=114.5))
    assert home > away   # home is the favourite: mean 115 vs 109
    a = L2.engine_p(p, 2.0, 224.0, dict(PARSED, market_type="NBA_SPREAD", subject="DAL", strike=2.5))
    b = L2.engine_p(p, 2.0, 224.0, dict(PARSED, market_type="NBA_SPREAD", subject="DAL", strike=8.5))
    assert a > b
    assert L2.engine_p(p, 2.0, 224.0, dict(PARSED, market_type="NBA_SPREAD", subject="XXX", strike=2.5)) is None


def test_params_hash_stable_and_sensitive():
    p = _p()
    assert L2.params_hash(p) == L2.params_hash(_p())
    q = V.with_platt(p, {**p.platt, "ml": (-0.2, 1.8)})
    assert L2.params_hash(q) != L2.params_hash(p)


def test_train_rows_are_probabilities():
    import pandas as pd
    g = pd.DataFrame(dict(mu_poss=[99.0, 100.0], ppp_h=[114.0, 112.0], ppp_a=[113.0, 115.0], home_pts=[110.0, 120.0], away_pts=[105.0, 118.0]))
    d = L2._train_rows(_p(), g)
    assert d["raw"].between(0, 1).all() and set(d.family) == {"ml", "spread", "total", "team_total"}
    assert np.isfinite(d["raw"]).all()
