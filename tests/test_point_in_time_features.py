"""Point-in-time proofs (W72.3 Part B item 5): a game's features never include that game or later ones.

Method (perturbation, not code reading): compute features, then corrupt every source row at/after the
as-of date with extreme values and assert the features are bit-identical. A positive control corrupts a
PRIOR row and asserts the features DO move, so the test cannot pass vacuously.
"""
from datetime import date

import numpy as np
import pandas as pd
import pytest

from prediction_market_bot.c1_signal_ingestion.nfl_qb_features import ChallengerFeatures
from prediction_market_bot.c2_feature_store.mlb_features import _compute_rolling_batter_features

ROLL_COLS = ["ba_l10", "ba_l10_shrunk", "slg_l10", "obp_l10", "ops_l10", "h_l10_mean",
             "k_rate_l10", "bb_rate_l10", "hr_rate_l10", "days_rest", "b2b_flag"]


def _batter_log(n=25, seed=0):
    rng = np.random.default_rng(seed)
    ab = rng.integers(2, 6, n)
    h = np.minimum(rng.integers(0, 4, n), ab)
    return pd.DataFrame({
        "game_date": pd.date_range("2026-04-01", periods=n, freq="D").astype(str),
        "ab": ab, "h": h, "doubles": 0, "triples": 0, "hr": rng.integers(0, 2, n),
        "bb": rng.integers(0, 2, n), "k": rng.integers(0, 3, n), "hbp": 0, "sf": 0, "rbi": 0,
        "is_home_game": 1,
    })


@pytest.mark.parametrize("i", [3, 10, 24])
def test_mlb_rolling_excludes_own_and_later_games(i):
    base = _batter_log()
    ref = _compute_rolling_batter_features(base, window=10, min_periods=3)
    pert = base.copy()
    for c in ("ab", "h", "doubles", "triples", "hr", "bb", "k", "hbp", "sf"):
        pert.loc[i:, c] = 999  # corrupt game i (its own box score) and everything after
    got = _compute_rolling_batter_features(pert, window=10, min_periods=3)
    pd.testing.assert_series_equal(ref.loc[i, ROLL_COLS], got.loc[i, ROLL_COLS], check_names=False)
    # every earlier row is also untouched
    pd.testing.assert_frame_equal(ref.loc[:i, ROLL_COLS], got.loc[:i, ROLL_COLS])


def test_mlb_positive_control_prior_game_moves_features():
    base = _batter_log()
    ref = _compute_rolling_batter_features(base, window=10, min_periods=3)
    pert = base.copy()
    pert.loc[9, ["ab", "h"]] = [50, 50]
    got = _compute_rolling_batter_features(pert, window=10, min_periods=3)
    assert ref.loc[10, "ba_l10"] != got.loc[10, "ba_l10"]


def test_mlb_unsorted_input_is_sorted_not_leaked():
    base = _batter_log()
    ref = _compute_rolling_batter_features(base, window=10, min_periods=3)
    shuffled = base.sample(frac=1, random_state=1)
    got = _compute_rolling_batter_features(shuffled, window=10, min_periods=3)
    pd.testing.assert_frame_equal(ref[ROLL_COLS].reset_index(drop=True), got[ROLL_COLS].reset_index(drop=True))


# ---------------------------------------------------------------- NFL QB challenger
TEAMS = ["AAA", "BBB", "CCC", "DDD"]


def _nfl(weeks=10):
    rng = np.random.default_rng(1)
    sch, ts = [], []
    gid = 0
    for w in range(weeks):
        d = (pd.Timestamp("2026-09-06") + pd.Timedelta(days=7 * w)).strftime("%Y-%m-%d")
        order = TEAMS[w % 2:] + TEAMS[:w % 2]
        for h, a in ((order[0], order[1]), (order[2], order[3])):
            gid += 1
            g = f"g{gid}"
            sch.append({"game_id": g, "gameday": d, "home_team": h, "away_team": a,
                        "home_score": int(rng.integers(10, 35)), "away_score": int(rng.integers(10, 35)),
                        "home_qb_id": f"qb_{h}_{w % 3}", "away_qb_id": f"qb_{a}_{w % 3}"})
            ts.append({"game_id": g, "team": h, "opponent_team": a, "off_epa": float(rng.normal(0, .2))})
            ts.append({"game_id": g, "team": a, "opponent_team": h, "off_epa": float(rng.normal(0, .2))})
    return pd.DataFrame(ts), pd.DataFrame(sch)


def _probe(cf, d):
    out = {}
    for t in TEAMS:
        out[t] = (cf.team_rates(t, d, 2.0), cf.projected_starter(t, d),
                  cf.qb_epa(cf.projected_starter(t, d), d), cf._lm_epa.before(d), cf._lm_pts.before(d))
    return out


def test_nfl_features_ignore_rows_on_or_after_asof():
    ts, sch = _nfl()
    asof = date(2026, 10, 25)  # week 7 game day
    ref = _probe(ChallengerFeatures(ts, sch, sch), asof)
    assert ref["AAA"][0] is not None  # enough history, so the test is meaningful

    sch2, ts2 = sch.copy(), ts.copy()
    late = pd.to_datetime(sch2.gameday).dt.date >= asof
    sch2.loc[late, ["home_score", "away_score"]] = 999
    sch2.loc[late, ["home_qb_id", "away_qb_id"]] = "qb_LEAK"
    late_ids = set(sch2.loc[late, "game_id"])
    ts2.loc[ts2.game_id.isin(late_ids), "off_epa"] = 99.0
    got = _probe(ChallengerFeatures(ts2, sch2, sch2), asof)
    assert got == ref


def test_nfl_positive_control_prior_row_moves_features():
    ts, sch = _nfl()
    asof = date(2026, 10, 25)
    ref = _probe(ChallengerFeatures(ts, sch, sch), asof)
    ts2 = ts.copy()
    ts2.loc[ts2.game_id == "g1", "off_epa"] = 50.0
    got = _probe(ChallengerFeatures(ts2, sch, sch), asof)
    assert got != ref
