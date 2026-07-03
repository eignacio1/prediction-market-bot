"""Tests for scripts/mc_forward_projection.py (GG-071/T-223).

Covers: simulation mechanics (compounding, cap engagement, kill-switch
detection), reproduction of GG-071's cited order-of-magnitude findings, and
monotonicity of the T-223 candidate remediation directions (de-rating stake
fraction and lowering the absolute cap should both reduce kill-switch
probability; this is the property ADR-0040's recommendation relies on).
"""

import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from mc_forward_projection import (  # noqa: E402
    SimParams,
    simulate_paths,
    kill_prob_at_horizons,
    build_report,
    sensitivity_report,
)


class TestSimulatePaths:
    def test_zero_win_rate_always_kills(self):
        params = SimParams(win_rate=0.0, bets_per_day=26, starting_bankroll=1000.0)
        result = simulate_paths(params, n_days=30, n_sims=200, seed=1)
        assert result["killed"].all()

    def test_win_rate_one_never_kills(self):
        params = SimParams(win_rate=1.0, bets_per_day=26, starting_bankroll=1000.0)
        result = simulate_paths(params, n_days=30, n_sims=200, seed=1)
        assert not result["killed"].any()
        # every bet wins -> bankroll strictly grows, never drawn down
        assert (result["ending_bankroll"] > 1000.0).all()

    def test_kill_day_never_exceeds_n_days_plus_one_when_not_killed(self):
        params = SimParams()
        result = simulate_paths(params, n_days=30, n_sims=500, seed=2)
        not_killed = ~result["killed"]
        assert (result["kill_day"][not_killed] == 31).all()

    def test_kill_day_within_range_when_killed(self):
        params = SimParams(win_rate=0.3)  # low win rate -> most paths killed
        result = simulate_paths(params, n_days=30, n_sims=500, seed=3)
        killed_days = result["kill_day"][result["killed"]]
        assert len(killed_days) > 0
        assert (killed_days >= 1).all()
        assert (killed_days <= 30).all()

    def test_cap_binds_at_high_bankroll(self):
        """Once bankroll exceeds cap/stake_frac, per-bet stake should be capped,
        not a growing percentage — verify indirectly via a single deterministic
        all-win path."""
        params = SimParams(win_rate=1.0, stake_frac=0.5, cap_usd=100.0, starting_bankroll=1000.0,
                            bets_per_day=1)
        # first bet: stake = min(0.5*1000, 100) = 100 -> bankroll += 100*win_mult
        result = simulate_paths(params, n_days=1, n_sims=1, seed=1)
        expected = 1000.0 + 100.0 * params.win_mult
        assert result["ending_bankroll"][0] == pytest.approx(expected)


class TestGG071Reproduction:
    def test_baseline_reproduces_elevated_ruin_risk_order_of_magnitude(self):
        """GG-071 (SESSION 113, 2026-07-02) cited 17.05%/43.5%/46.45% at
        1mo/6mo/1yr. This recreated script does not share the original's
        exact source (mc_forward_projection.py did not survive in the repo),
        so exact reproduction is not expected — but the same real T1 MLB
        parameters must produce the same *order of magnitude* and the same
        qualitative finding: a real, positive edge still carries material
        (double-digit percent) permanent kill-switch risk under proportional
        compounding at this cadence."""
        params = SimParams()
        probs, _ = kill_prob_at_horizons(params, [30, 182, 365], n_sims=5000, seed=42)
        assert 10.0 < probs[30] < 30.0
        assert 30.0 < probs[182] < 65.0
        assert 30.0 < probs[365] < 65.0
        # monotonic non-decreasing with horizon
        assert probs[30] <= probs[182] <= probs[365] + 1e-9

    def test_higher_win_rate_reduces_kill_probability(self):
        low = SimParams(win_rate=0.50)
        high = SimParams(win_rate=0.58)
        p_low, _ = kill_prob_at_horizons(low, [365], n_sims=3000, seed=7)
        p_high, _ = kill_prob_at_horizons(high, [365], n_sims=3000, seed=7)
        assert p_high[365] < p_low[365]


class TestRemediationMonotonicity:
    """These properties are what ADR-0040's recommendation depends on —
    verify them directly rather than trusting the sensitivity report output."""

    def test_derating_stake_fraction_reduces_kill_probability(self):
        base = SimParams()
        derated = SimParams(stake_frac=base.stake_frac / 3.0)
        p_base, _ = kill_prob_at_horizons(base, [365], n_sims=3000, seed=11)
        p_derated, _ = kill_prob_at_horizons(derated, [365], n_sims=3000, seed=11)
        assert p_derated[365] < p_base[365]

    def test_extreme_derating_approaches_zero_kill_probability(self):
        tiny = SimParams(stake_frac=0.0005)
        probs, _ = kill_prob_at_horizons(tiny, [365], n_sims=2000, seed=13)
        assert probs[365] < 5.0

    def test_lowering_cap_has_zero_effect_on_near_term_horizon(self):
        """At the real starting bankroll ($1,000), the cap only binds once
        bankroll compounds past cap/stake_frac. At 30 days essentially no
        path has grown that far yet, so lowering the cap should not move
        the 30-day kill probability at all — unlike de-rating stake_frac,
        which acts on every bet from day 1. This is the basis for ADR-0040
        preferring (a)/(b) over (c) alone."""
        base = SimParams()
        lower_cap = SimParams(cap_usd=50.0)
        p_base, _ = kill_prob_at_horizons(base, [30], n_sims=4000, seed=17)
        p_lower, _ = kill_prob_at_horizons(lower_cap, [30], n_sims=4000, seed=17)
        assert abs(p_lower[30] - p_base[30]) < 3.0

    def test_lowering_cap_reduces_longer_horizon_kill_probability(self):
        """Unlike the 30-day horizon, a lower cap does meaningfully reduce
        kill probability at 6mo/1yr once some paths have compounded past the
        (lower) engagement bankroll."""
        base = SimParams()
        lower_cap = SimParams(cap_usd=50.0)
        p_base, _ = kill_prob_at_horizons(base, [365], n_sims=4000, seed=17)
        p_lower, _ = kill_prob_at_horizons(lower_cap, [365], n_sims=4000, seed=17)
        assert p_lower[365] < p_base[365]


class TestReportGeneration:
    def test_build_report_contains_expected_sections(self):
        report = build_report(SimParams(), [30, 182, 365], n_sims=500)
        assert "KILL-SWITCH BREACH PROBABILITY" in report
        assert "PARAMETERS" in report
        assert "GOVERNANCE" in report
        assert "GG-071" in report

    def test_sensitivity_report_contains_all_three_directions(self):
        report = sensitivity_report(n_sims=500)
        assert "(a) CADENCE-AWARE KELLY DE-RATING" in report
        assert "(b) FORMAL MAX-P(KILL-SWITCH) TARGET" in report
        assert "(c) LOWERING THE $500/BET HARD CAP" in report
