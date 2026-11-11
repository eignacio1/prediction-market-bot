import pytest

from prediction_market_bot.nba_engine import decision_tree as D
from prediction_market_bot.nba_engine import engine_v2 as V

P = V.V2Params(hca=2.5, tbias=0.0, sd_margin=12.0, sd_total=18.0,
               shift_margin={"exp_missing": -1.5, "rest_diff": 0.5}, shift_total={"exp_missing": -0.8})


def test_band_by_horizon():
    assert [D.band_for(h) for h in (30, 12, 6, 3, 1, -0.1)] == ["T1", "T1", "T2", "T2", "T3", "T4"]


def test_deeper_horizon_permits_more_classes():
    assert set(D.permitted_classes("T3")) < set(D.permitted_classes("T2")) < set(D.permitted_classes("T1"))


def test_lineup_factor_not_used_before_it_exists():
    x = {"exp_missing": 3.0, "rest_diff": 1.0}
    early = D.price(P, "ml", 112, 110, x, hours_to_tip=20)
    assert "exp_missing" in early.skipped and early.used == ["rest_diff"]
    late = D.price(P, "ml", 112, 110, x, hours_to_tip=1.0)
    assert "exp_missing" in late.used and "rest_diff" in late.skipped   # rest not permitted at T3
    assert late.p < early.p   # star out lowers the home price once it is known


def test_known_answer_no_factors_is_ratings_only():
    r = D.price(P, "ml", 112, 110, {}, 20, calibrate=False)
    assert r.m == pytest.approx(112 - 110 + 2.5) and r.p == pytest.approx(V.raw_prob(P, "ml", r.m, r.t, 1))


def test_inplay_converges_to_the_score():
    up = D.price_inplay(P, "ml", 4.5, 224.0, frac_played=0.97, margin_now=15, total_now=210)
    dn = D.price_inplay(P, "ml", 4.5, 224.0, frac_played=0.97, margin_now=-15, total_now=210)
    assert up.p > 0.999 and dn.p < 0.001
    pre = D.price_inplay(P, "ml", 4.5, 224.0, frac_played=0.0, margin_now=0, total_now=0)
    assert pre.p == pytest.approx(V.raw_prob(P, "ml", 4.5, 224.0, 1))


def test_pregame_price_refuses_in_play():
    with pytest.raises(ValueError):
        D.price(P, "ml", 112, 110, {}, -1)
