"""W98.1 Part C known-answer tests for the rank-vs-history and matchup-cross factors (study code in 12_EXPLORATORY/nba_engine_v3)."""
import importlib.util
import sys
from pathlib import Path

import numpy as np
import pandas as pd

P = Path(__file__).resolve().parents[1] / "12_EXPLORATORY" / "nba_engine_v3" / "study_partc_w98.py"


def _mod():
    for d in (P.parent, P.parent.parent / "nba_board", P.parent.parent / "nba_engine_live", P.parent.parent):
        sys.path.insert(0, str(d))
    spec = importlib.util.spec_from_file_location("study_partc_w98", P)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def _frame(n=400):
    rng = np.random.default_rng(0)
    rows = []
    for s in (2023, 2024):
        v = rng.uniform(0, 1, n)
        rows.append(pd.DataFrame(dict(season=s, h_x=v, a_x=rng.uniform(0, 1, n)), index=[f"{s}{i:04d}" for i in range(n)]))
    return pd.concat(rows)


def test_rank_is_percentile_of_prior_seasons_only():
    m = _mod()
    F = _frame()
    F.loc[F.season == 2024, "h_x"] = 0.5
    r = m.history_rank(F, "h_x", "a_x")
    cur = r[F.season == 2024].h
    assert abs(cur.mean() - 0.5) < 0.05           # known answer: the median of a uniform history ranks at ~0.5
    assert r[F.season == 2023].h.isna().all()     # no history -> NaN, never a same-season (look-ahead) rank


def test_rank_ignores_the_future():
    m = _mod()
    F = _frame()
    base = m.history_rank(F, "h_x", "a_x")
    F2 = F.copy()
    F2.loc[F2.season == 2024, "h_x"] = 99.0       # change the later season's values
    after = m.history_rank(F2, "h_x", "a_x")
    assert base[F.season == 2023].h.isna().all() and after[F.season == 2023].h.isna().all()


def test_cross_term_matches_hand_value():
    m = _mod()
    F = pd.DataFrame(dict(season=[2024], h_exp_missing=[0.2], a_exp_missing=[0.1], h_lineup_net=[0.5], a_lineup_net=[2.0]))
    # rank columns need history, so only the cross is asserted here
    ch, ca = 0.2 * 2.0, 0.1 * 0.5
    out = m.add_factors(F)
    assert abs(out.d_cross_missing_net.iloc[0] - (ch - ca)) < 1e-12 and abs(out.s_cross_missing_net.iloc[0] - (ch + ca)) < 1e-12
