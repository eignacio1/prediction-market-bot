"""Invariants for the EXPLORATORY NFL engine scaffold (no look-ahead concern: engine takes means only)."""
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "12_EXPLORATORY" / "nfl_engine"))
import engine as E  # noqa: E402


def _s(mu_h=24.0, mu_a=21.0, n=60_000, seed=1, r=0.6, s_n=1.0):
    return E.simulate(mu_h, mu_a, n, seed, r, s_n)


def test_deterministic():
    a, b = _s(), _s()
    assert (a.home_pts == b.home_pts).all() and (a.away_pts == b.away_pts).all()


def test_total_is_sum_exactly():
    s = _s()
    assert (s.total == s.home_pts + s.away_pts).all() and (s.margin == s.home_pts - s.away_pts).all()


def test_ladders_monotone_and_ml_identity():
    s = _s()
    ks = [-10.5, -6.5, -3.5, -0.5, 0.5, 3.5, 6.5, 10.5]
    ps = [E.p_spread_home_covers(s, k) for k in ks]
    assert all(a >= b for a, b in zip(ps, ps[1:]))
    tot = [E.p_total_over(s, k) for k in (35.5, 41.5, 47.5, 53.5)]
    assert all(a >= b for a, b in zip(tot, tot[1:]))
    tie = float((s.margin == 0).mean())
    assert abs(E.p_moneyline_home(s) - (E.p_spread_home_covers(s, -0.5) - 0.5 * tie)) < 1e-12


def test_team_totals_pair_sums_to_game_total():
    s = _s()
    assert (s.home_pts + s.away_pts == s.total).all()
    assert abs(s.home_pts.mean() + s.away_pts.mean() - s.total.mean()) < 1e-9


def test_means_recovered_after_ot_correction():
    d = E.ot_delta(n=200_000)
    s = E.simulate(24.0, 21.0, 200_000, 7, 0.6, 1.0, delta=d)
    assert abs(s.home_pts.mean() - 24.0) < 0.25 and abs(s.away_pts.mean() - 21.0) < 0.25


def test_scores_are_integers_and_key_numbers_exist():
    s = _s()
    assert s.home_pts.dtype.kind == "i"
    pm = np.bincount(np.abs(s.margin))[:11] / len(s.margin)
    assert pm[3] > pm[2] and pm[7] > pm[6]   # key numbers emerge from 3/7 scoring


def test_joint_from_same_draws_is_bounded_by_marginals():
    s = _s()
    a, b = (lambda x: x.margin > 2.5), (lambda x: x.total > 44.5)
    j = E.p_joint(s, a, b)
    assert j <= min(E.p_spread_home_covers(s, 2.5), E.p_total_over(s, 44.5)) + 1e-12
