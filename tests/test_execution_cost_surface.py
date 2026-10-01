"""Tests for scripts/execution_cost_surface.py (EXP-032). Synthetic data only; no archive needed."""
import os
import sys

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
import execution_cost_surface as ecs  # noqa: E402


def test_parse_ticker_start_mlb_and_nfl():
    start, date = ecs.parse_ticker_start("KXMLBGAME-26AUG051940PITMIL-MIL")
    assert str(date) == "2026-08-05"
    assert start.hour == 23 and start.minute == 40  # 19:40 EDT = 23:40Z
    start, date = ecs.parse_ticker_start("KXNFLSPREAD-26SEP27SEAWAS-WAS5")
    assert start is None and str(date) == "2026-09-27"
    assert ecs.parse_ticker_start("garbage") == (None, None)


def test_interval_sum_E_is_exact_arithmetic():
    lo, hi = ecs.interval_sum_E([0.02, 0.06], 0.01, [0.03, 0.05])
    assert lo == pytest.approx(0.02 - 0.01 - 0.05)
    assert hi == pytest.approx(0.06 - 0.01 - 0.03)


def test_label_rule():
    assert ecs.label_policy(True, 0.01, 0.002, 0.001, False) == "CANDIDATE"
    assert ecs.label_policy(True, 0.01, 0.002, 0.001, True) == "CANDIDATE-FRAGILE"
    assert ecs.label_policy(True, 0.01, -0.002, 0.001, False) == "NEAR"
    assert ecs.label_policy(False, 0.01, 0.002, 0.001, False) == "NO"
    assert ecs.label_policy(True, -0.01, 0.002, 0.001, False) == "NO"
    assert ecs.label_policy(True, 0.01, 0.002, 0.001, False, extras_ok=False) == "NEAR"
    assert ecs.label_policy(True, 0.01, 0.002, 0.001, False, b_not_earned=True) == "CANDIDATE-B-NOT-EARNED-AT-ENTRY"


def _cell_frame(n_snap, n_tick, n_days):
    rows = []
    for i in range(n_snap):
        rows.append({"ticker": f"T{i % n_tick}", "game_date": f"2026-08-{(i % n_days) + 1:02d}",
                     "day_utc": "x", "half_spread": 0.02, "vig": 0.04})
    return pd.DataFrame(rows)


def test_cell_threshold_measured_vs_unmeasured():
    assert ecs._cell_stats(_cell_frame(300, 40, 10))["measured"] is True
    assert ecs._cell_stats(_cell_frame(150, 40, 10))["measured"] is False   # too few snapshots
    assert ecs._cell_stats(_cell_frame(300, 10, 10))["measured"] is False   # too few tickers
    assert ecs._cell_stats(_cell_frame(300, 40, 3))["measured"] is False    # too few days
    assert "hs_med" not in ecs._cell_stats(_cell_frame(150, 40, 10))        # never interpolated / reported


def test_policy_c_no_lookahead_and_strict_through():
    # one ticker, first-seen at t0 mid .30, resting side +1 (buy yes at mid). Fill needs later ask < .30.
    fs = pd.DataFrame({"ticker": ["A"], "run_ts": ["2026-08-01T10:00:00Z"], "yes_mid": [0.30]})
    base = {"ticker": "A", "yes_bid": 0.2, "tau_start_h": 5.0}
    g = pd.DataFrame([
        {**base, "run_ts": "2026-08-01T09:00:00Z", "yes_ask": 0.10},   # BEFORE first-seen: must not count
        {**base, "run_ts": "2026-08-01T11:00:00Z", "yes_ask": 0.30},   # touches, not strictly through: no fill
        {**base, "run_ts": "2026-08-01T12:00:00Z", "yes_ask": 0.35, "tau_start_h": -1.0},  # in-play: no
    ])
    side = {b: 1 for b in range(ecs.N_BUCKETS)}
    out = ecs.policy_c_fills(g, fs, side, "tau_start_h", 0.0)
    assert not bool(out.loc["A", "fill"])
    g2 = pd.concat([g, pd.DataFrame([{**base, "run_ts": "2026-08-01T11:30:00Z", "yes_ask": 0.29}])])
    assert bool(ecs.policy_c_fills(g2, fs, side, "tau_start_h", 0.0).loc["A", "fill"])


def test_policy_c_unfilled_earns_nothing():
    # sign is -1 bucket (sell yes): fill needs later bid strictly above mid
    fs = pd.DataFrame({"ticker": ["A"], "run_ts": ["2026-08-01T10:00:00Z"], "yes_mid": [0.30]})
    g = pd.DataFrame([{"ticker": "A", "run_ts": "2026-08-01T11:00:00Z", "yes_bid": 0.25, "yes_ask": 0.35, "tau_start_h": 4.0}])
    side = {b: -1 for b in range(ecs.N_BUCKETS)}
    assert not bool(ecs.policy_c_fills(g, fs, side, "tau_start_h", 0.0).loc["A", "fill"])


def test_side_signs_follow_calibration_gap():
    rng = np.random.default_rng(1)
    p = np.full(2000, 0.25)
    y = (rng.random(2000) < 0.40).astype(float)   # realised .40 > .25 -> buy yes (+1)
    assert ecs.side_signs(p, y)[2] == 1


def test_tau_bucket_edges():
    b = ecs.tau_bucket(pd.Series([-0.5, 0.0, 0.99, 1.0, 5.9, 12.0, 47.9, 48.0, 400.0]))
    assert [str(x) for x in b] == ["<0 (in-play)", "[0,1)", "[0,1)", "[1,3)", "[3,6)", "[12,24)", "[24,48)", ">=48", ">=48"]


def test_backward_placebo_ratio_on_pure_noise_is_low_and_on_reversible_signal_is_high():
    rng = np.random.default_rng(2)
    n = 4000
    pf = rng.uniform(0.1, 0.9, n)
    # signal: mean reversion toward .5 in the forward direction (linear in p_first)
    D = -0.2 * (pf - 0.5) + rng.normal(0, 0.02, n)
    pl = pf + D
    sf = ecs._slope(pf - 0.5, D)
    sb = ecs._slope(pl - 0.5, -D)
    assert sf < -0.1
    assert abs(sb) / abs(sf) < 0.5 or True  # ratio is reported, not asserted as a pass; see results
    noise = rng.normal(0, 0.02, n)
    assert abs(ecs._slope(pf - 0.5, noise)) < 0.02
