"""Tests for scripts/mc_forward_projection.py (GG-071/T-223).

Covers: simulation mechanics (compounding, cap engagement, kill-switch
detection), reproduction of GG-071's cited order-of-magnitude findings, and
monotonicity of the T-223 candidate remediation directions (de-rating stake
fraction and lowering the absolute cap should both reduce kill-switch
probability; this is the property ADR-0040's recommendation relies on).
"""

import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from mc_forward_projection import (  # noqa: E402
    SimParams,
    simulate_paths,
    kill_prob_at_horizons,
    build_report,
    sensitivity_report,
    LEDGER_BANDS,
    derive_ledger_stats,
    build_ledger_scenarios,
    bootstrap_kill_ci,
    build_ledger_report,
    load_clean_band_records,
    BETS_PER_DAY,
    t4m_proj_operational_params,
    T4M_PROJ_WIN_RATE,
    T4M_PROJ_WIN_MULT,
    T4M_PROJ_LOSS_MULT,
    T4M_PROJ_STAKE_USD,
    T4M_PROJ_BETS_PER_DAY,
)
from prediction_market_bot.logic_epoch import CURRENT_LOGIC_EPOCH  # noqa: E402


def _mk_recs(n_win, n_loss, win_mult=1.2, loss_mult=1.0, size=10.0,
             span_days=20.0, epoch=None, with_timestamps=True):
    """Synthetic clean_n-shaped records: the exact fields derive_ledger_stats /
    bootstrap_kill_ci read (_win, _pnl, _size, logic_epoch, resolved_at) —
    hermetic, no dependency on live VPS ledger files."""
    if epoch is None:
        epoch = CURRENT_LOGIC_EPOCH
    total = n_win + n_loss
    base = datetime(2026, 7, 1, tzinfo=timezone.utc)
    recs = []
    for i in range(total):
        is_win = i < n_win
        rec = {
            "_win": 1 if is_win else 0,
            "_pnl": size * win_mult if is_win else -size * loss_mult,
            "_size": size,
            "logic_epoch": epoch,
        }
        if with_timestamps and total > 1:
            frac = i / (total - 1)
            ts = base + timedelta(days=frac * span_days)
            rec["resolved_at"] = ts.strftime("%Y-%m-%dT%H:%M:%S") + "Z"
        recs.append(rec)
    return recs


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


class TestDeriveLedgerStats:
    """T-330: derive win_rate/win_mult/loss_mult/stake_frac/cadence from a
    clean_n record set instead of hardcoded module constants."""

    def test_basic_derivation(self):
        recs = _mk_recs(n_win=60, n_loss=40, win_mult=1.2, loss_mult=1.0, size=10.0)
        stats = derive_ledger_stats("T1", recs, starting_bankroll=1000.0)
        assert stats.clean_n == 100
        assert stats.win_rate == pytest.approx(0.60)
        assert stats.win_mult == pytest.approx(1.2)
        assert stats.loss_mult == pytest.approx(1.0)
        assert stats.stake_frac == pytest.approx(10.0 / 1000.0)

    def test_zero_clean_n_raises(self):
        with pytest.raises(ValueError, match="clean_n=0"):
            derive_ledger_stats("T1", [], starting_bankroll=1000.0)

    def test_no_wins_raises(self):
        recs = _mk_recs(n_win=0, n_loss=40)
        with pytest.raises(ValueError, match="win_mult"):
            derive_ledger_stats("T1", recs, starting_bankroll=1000.0)

    def test_no_losses_raises(self):
        recs = _mk_recs(n_win=40, n_loss=0)
        with pytest.raises(ValueError, match="loss_mult"):
            derive_ledger_stats("T1", recs, starting_bankroll=1000.0)

    def test_cadence_immature_flagged_for_short_span(self):
        recs = _mk_recs(n_win=30, n_loss=20, span_days=3.0)
        stats = derive_ledger_stats("T1", recs, starting_bankroll=1000.0)
        assert stats.cadence_span_days == pytest.approx(3.0)
        assert stats.cadence_immature is True

    def test_cadence_mature_not_flagged(self):
        recs = _mk_recs(n_win=30, n_loss=20, span_days=30.0)
        stats = derive_ledger_stats("T1", recs, starting_bankroll=1000.0)
        assert stats.cadence_span_days == pytest.approx(30.0)
        assert stats.cadence_immature is False

    def test_cadence_unmeasurable_falls_back_to_module_default(self):
        recs = _mk_recs(n_win=30, n_loss=20, with_timestamps=False)
        stats = derive_ledger_stats("T1", recs, starting_bankroll=1000.0)
        assert stats.cadence_bets_per_week is None
        assert stats.bets_per_day == BETS_PER_DAY


class TestBuildLedgerScenarios:
    def test_floor_is_zero_edge_breakeven(self):
        recs = _mk_recs(n_win=60, n_loss=40, win_mult=1.2, loss_mult=1.0, size=10.0)
        stats = derive_ledger_stats("T1", recs, starting_bankroll=1000.0)
        scenarios = build_ledger_scenarios(stats)
        expected_p0 = stats.loss_mult / (stats.win_mult + stats.loss_mult)
        assert scenarios["floor"].win_rate == pytest.approx(expected_p0)
        assert scenarios["floor"].win_mult == pytest.approx(stats.win_mult)
        assert scenarios["floor"].loss_mult == pytest.approx(stats.loss_mult)

    def test_operational_is_frozen_default_unaffected_by_ledger(self):
        recs = _mk_recs(n_win=95, n_loss=5, win_mult=3.0, loss_mult=1.0, size=999.0)
        stats = derive_ledger_stats("T1", recs, starting_bankroll=1000.0)
        scenarios = build_ledger_scenarios(stats)
        default = SimParams()
        op = scenarios["operational"]
        assert op.win_rate == default.win_rate
        assert op.win_mult == default.win_mult
        assert op.loss_mult == default.loss_mult
        assert op.stake_frac == default.stake_frac
        assert op.bets_per_day == default.bets_per_day

    def test_ceiling_uses_fully_observed_stats(self):
        recs = _mk_recs(n_win=60, n_loss=40, win_mult=1.2, loss_mult=1.0, size=10.0)
        stats = derive_ledger_stats("T1", recs, starting_bankroll=1000.0)
        scenarios = build_ledger_scenarios(stats)
        assert scenarios["ceiling"].win_rate == pytest.approx(stats.win_rate)
        assert scenarios["ceiling"].stake_frac == pytest.approx(stats.stake_frac)

    def test_ceiling_less_risky_than_floor_when_real_edge_present(self):
        """floor assumes the edge is illusory (breakeven win_rate); ceiling uses
        the real observed (positive) edge — ceiling must show lower or equal
        ruin risk at every horizon when the ledger reflects a genuine edge."""
        recs = _mk_recs(n_win=65, n_loss=35, win_mult=1.15, loss_mult=1.0, size=10.0, span_days=30.0)
        stats = derive_ledger_stats("T1", recs, starting_bankroll=1000.0)
        scenarios = build_ledger_scenarios(stats)
        p_floor, _ = kill_prob_at_horizons(scenarios["floor"], [365], n_sims=2000, seed=5)
        p_ceiling, _ = kill_prob_at_horizons(scenarios["ceiling"], [365], n_sims=2000, seed=5)
        assert p_ceiling[365] <= p_floor[365]


class TestLoadCleanBandRecords:
    def test_unknown_band_raises(self):
        with pytest.raises(ValueError):
            load_clean_band_records("NOT-A-BAND")

    def test_ledger_bands_covers_book_bands_and_t4(self):
        assert "T1" in LEDGER_BANDS
        assert "T2" in LEDGER_BANDS
        assert "T3" in LEDGER_BANDS
        assert "T4M-PROJ" in LEDGER_BANDS


class TestBootstrapKillCI:
    def test_invalid_scenario_name_raises(self):
        recs = _mk_recs(n_win=60, n_loss=40)
        with pytest.raises(ValueError):
            bootstrap_kill_ci("T1", recs, "operational", starting_bankroll=1000.0,
                               cap_usd=500.0, kill_switch_dd=0.20, horizons=[365],
                               n_boot=5, boot_sims=200)

    def test_ci_ordering_lo_le_point_le_hi(self):
        recs = _mk_recs(n_win=60, n_loss=40, win_mult=1.2, loss_mult=1.0, size=10.0, span_days=30.0)
        result = bootstrap_kill_ci("T1", recs, "ceiling", starting_bankroll=1000.0,
                                    cap_usd=500.0, kill_switch_dd=0.20, horizons=[30, 365],
                                    n_boot=15, boot_sims=300, seed=42)
        for h in (30, 365):
            entry = result[h]
            assert entry is not None
            assert entry["lo"] <= entry["point"] <= entry["hi"]
            assert entry["n_boot_valid"] <= 15

    def test_deterministic_with_fixed_seed(self):
        recs = _mk_recs(n_win=60, n_loss=40, win_mult=1.2, loss_mult=1.0, size=10.0, span_days=30.0)
        r1 = bootstrap_kill_ci("T1", recs, "floor", starting_bankroll=1000.0,
                                cap_usd=500.0, kill_switch_dd=0.20, horizons=[365],
                                n_boot=10, boot_sims=200, seed=7)
        r2 = bootstrap_kill_ci("T1", recs, "floor", starting_bankroll=1000.0,
                                cap_usd=500.0, kill_switch_dd=0.20, horizons=[365],
                                n_boot=10, boot_sims=200, seed=7)
        assert r1[365] == r2[365]

    def test_tractable_with_small_boot_params(self):
        """Sanity check that a small n_boot/boot_sims configuration (as used for
        quick CLI/test invocations) actually completes and returns a well-formed
        result, without asserting a specific runtime."""
        recs = _mk_recs(n_win=30, n_loss=20, span_days=10.0)
        result = bootstrap_kill_ci("T1", recs, "ceiling", starting_bankroll=1000.0,
                                    cap_usd=500.0, kill_switch_dd=0.20, horizons=[30],
                                    n_boot=5, boot_sims=100, seed=1)
        assert result[30] is not None
        assert result[30]["n_boot_valid"] > 0


class TestBuildLedgerReport:
    def _stats_and_scenarios(self):
        recs = _mk_recs(n_win=60, n_loss=40, win_mult=1.2, loss_mult=1.0, size=10.0, span_days=20.0)
        stats = derive_ledger_stats("T1", recs, starting_bankroll=1000.0)
        scenarios = build_ledger_scenarios(stats)
        return stats, scenarios

    def test_contains_expected_sections(self):
        stats, scenarios = self._stats_and_scenarios()
        report = build_ledger_report("T1", stats, scenarios, [30, 182, 365], n_sims=500)
        assert "FLOOR" in report
        assert "OPERATIONAL" in report
        assert "CEILING" in report
        assert "clean_n" in report
        assert "band=T1" in report

    def test_contains_ci_band_when_boot_ci_provided(self):
        stats, scenarios = self._stats_and_scenarios()
        fake_ci = {
            "floor": {30: {"point": 5.0, "lo": 0.2, "hi": 41.0, "n_boot_valid": 20, "n_boot_skipped": 0},
                      182: None, 365: None},
            "ceiling": {30: None, 182: None, 365: None},
        }
        report = build_ledger_report("T1", stats, scenarios, [30, 182, 365], n_sims=500, boot_ci=fake_ci)
        assert "90% CI: 0.20% - 41.00%" in report

    def test_cadence_immature_caveat_appears(self):
        recs = _mk_recs(n_win=30, n_loss=20, span_days=3.0)
        stats = derive_ledger_stats("T1", recs, starting_bankroll=1000.0)
        scenarios = build_ledger_scenarios(stats)
        report = build_ledger_report("T1", stats, scenarios, [30, 182, 365], n_sims=500)
        assert "CAVEAT" in report
        assert "maturity floor" in report


class TestSimParamsStakeModeValidation:
    """T-342: stake_mode is validated at construction and at every entry point
    that accepts it explicitly, not just deep inside simulate_paths."""

    def test_invalid_stake_mode_rejected_by_simparams(self):
        with pytest.raises(ValueError, match="stake_mode"):
            SimParams(stake_mode="bogus")

    def test_invalid_stake_mode_rejected_by_build_ledger_scenarios(self):
        recs = _mk_recs(n_win=60, n_loss=40, span_days=20.0)
        stats = derive_ledger_stats("T1", recs, starting_bankroll=1000.0)
        with pytest.raises(ValueError, match="stake_mode"):
            build_ledger_scenarios(stats, stake_mode="bogus")

    def test_invalid_stake_mode_rejected_by_bootstrap_kill_ci(self):
        recs = _mk_recs(n_win=60, n_loss=40, span_days=20.0)
        with pytest.raises(ValueError, match="stake_mode"):
            bootstrap_kill_ci("T1", recs, "ceiling", starting_bankroll=1000.0,
                               cap_usd=500.0, kill_switch_dd=0.20, horizons=[365],
                               n_boot=5, boot_sims=200, stake_mode="bogus")


class TestSimulatePathsFlatMode:
    """T-342: flat stake_mode uses a fixed $ stake per bet that does not
    compound with bankroll — the defining structural difference from
    proportional/Kelly-style sizing."""

    def test_flat_stake_grows_bankroll_linearly_not_exponentially(self):
        """win_rate=1.0 makes every path deterministic regardless of seed —
        exact linear growth (bankroll += bets_per_day * stake_usd * win_mult
        per day) is the signature of a non-compounding fixed stake."""
        params = SimParams(win_rate=1.0, win_mult=1.0, stake_mode="flat",
                            stake_usd=5.0, cap_usd=500.0, bets_per_day=10,
                            starting_bankroll=1000.0, kill_switch_dd=0.99)
        result = simulate_paths(params, n_days=4, n_sims=3, seed=1)
        expected = 1000.0 + 4 * 10 * 5.0 * 1.0
        assert np.allclose(result["ending_bankroll"], expected)

    def test_flat_stake_ignores_bankroll_level_unlike_proportional(self):
        """Same win/loss mechanics, only stake_mode differs: proportional
        stake must change as bankroll compounds away from its starting value;
        flat stake must not."""
        base_kwargs = dict(win_rate=1.0, win_mult=0.5, loss_mult=1.0,
                            bets_per_day=5, cap_usd=100000.0, kill_switch_dd=0.99,
                            starting_bankroll=1000.0)
        flat = SimParams(stake_mode="flat", stake_usd=10.0, **base_kwargs)
        prop = SimParams(stake_mode="proportional", stake_frac=0.01, **base_kwargs)
        r_flat = simulate_paths(flat, n_days=10, n_sims=1, seed=2)
        r_prop = simulate_paths(prop, n_days=10, n_sims=1, seed=2)
        # flat: fixed $10/bet regardless of day -> exact linear closed form
        assert np.allclose(r_flat["ending_bankroll"], 1000.0 + 10 * 5 * 10.0 * 0.5)
        # proportional: stake grows with bankroll each day -> compounds strictly
        # above the flat (linear) trajectory once bankroll has grown past start
        assert r_prop["ending_bankroll"][0] > r_flat["ending_bankroll"][0]

    def test_flat_stake_capped_at_cap_usd(self):
        params = SimParams(win_rate=0.0, stake_mode="flat", stake_usd=1000.0,
                            cap_usd=50.0, bets_per_day=1, starting_bankroll=10000.0,
                            kill_switch_dd=0.99)
        result = simulate_paths(params, n_days=1, n_sims=1, seed=3)
        # one loss capped at $50, not the requested $1000 stake_usd
        assert result["ending_bankroll"][0] == pytest.approx(10000.0 - 50.0)

    def test_flat_and_proportional_both_report_valid_kill_probabilities(self):
        """Sanity check both modes produce well-formed, bounded output —
        not asserting a specific magnitude relationship (that is an empirical,
        regime-specific finding documented in DECISION_LOG.md, not a general
        mathematical property to pin in a unit test)."""
        flat = SimParams(win_rate=0.5, stake_mode="flat", stake_usd=1.0,
                          bets_per_day=20, starting_bankroll=1000.0)
        prop = SimParams(win_rate=0.5, stake_mode="proportional", stake_frac=0.01,
                          bets_per_day=20, starting_bankroll=1000.0)
        for params in (flat, prop):
            probs, _ = kill_prob_at_horizons(params, [30, 365], n_sims=1000, seed=9)
            for h in (30, 365):
                assert 0.0 <= probs[h] <= 100.0
            assert probs[365] >= probs[30]


class TestT4mProjOperationalParams:
    """T-342: T4M-PROJ's frozen operational scenario — the flat-stake analogue
    of SimParams() (T1's GG-071 defaults) for the new band."""

    def test_uses_flat_stake_mode(self):
        params = t4m_proj_operational_params()
        assert params.stake_mode == "flat"

    def test_matches_frozen_module_constants(self):
        params = t4m_proj_operational_params()
        assert params.win_rate == pytest.approx(T4M_PROJ_WIN_RATE)
        assert params.win_mult == pytest.approx(T4M_PROJ_WIN_MULT)
        assert params.loss_mult == pytest.approx(T4M_PROJ_LOSS_MULT)
        assert params.stake_usd == pytest.approx(T4M_PROJ_STAKE_USD)
        assert params.bets_per_day == T4M_PROJ_BETS_PER_DAY


class TestBuildLedgerScenariosFlatMode:
    def test_floor_and_ceiling_use_stake_usd_flat_not_stake_frac(self):
        recs = _mk_recs(n_win=60, n_loss=40, win_mult=1.2, loss_mult=1.0, size=10.0, span_days=20.0)
        stats = derive_ledger_stats("T4M-PROJ", recs, starting_bankroll=1000.0)
        scenarios = build_ledger_scenarios(stats, stake_mode="flat")
        assert scenarios["floor"].stake_mode == "flat"
        assert scenarios["floor"].stake_usd == pytest.approx(stats.stake_usd_flat)
        assert scenarios["ceiling"].stake_mode == "flat"
        assert scenarios["ceiling"].stake_usd == pytest.approx(stats.stake_usd_flat)

    def test_operational_override_used_when_supplied(self):
        recs = _mk_recs(n_win=60, n_loss=40, span_days=20.0)
        stats = derive_ledger_stats("T4M-PROJ", recs, starting_bankroll=1000.0)
        override = t4m_proj_operational_params()
        scenarios = build_ledger_scenarios(stats, stake_mode="flat", operational=override)
        assert scenarios["operational"] is override
        assert scenarios["operational"].stake_mode == "flat"

    def test_ceiling_less_risky_than_floor_when_real_edge_present_flat_mode(self):
        recs = _mk_recs(n_win=65, n_loss=35, win_mult=1.15, loss_mult=1.0, size=10.0, span_days=30.0)
        stats = derive_ledger_stats("T4M-PROJ", recs, starting_bankroll=1000.0)
        scenarios = build_ledger_scenarios(stats, stake_mode="flat")
        p_floor, _ = kill_prob_at_horizons(scenarios["floor"], [365], n_sims=2000, seed=5)
        p_ceiling, _ = kill_prob_at_horizons(scenarios["ceiling"], [365], n_sims=2000, seed=5)
        assert p_ceiling[365] <= p_floor[365]


class TestBootstrapKillCIFlatMode:
    def test_flat_mode_ci_well_formed(self):
        recs = _mk_recs(n_win=60, n_loss=40, win_mult=1.2, loss_mult=1.0, size=10.0, span_days=30.0)
        result = bootstrap_kill_ci("T4M-PROJ", recs, "ceiling", starting_bankroll=1000.0,
                                    cap_usd=500.0, kill_switch_dd=0.20, horizons=[30, 365],
                                    n_boot=10, boot_sims=200, seed=11, stake_mode="flat")
        for h in (30, 365):
            entry = result[h]
            assert entry is not None
            assert entry["lo"] <= entry["point"] <= entry["hi"]

    def test_flat_mode_deterministic_with_fixed_seed(self):
        recs = _mk_recs(n_win=60, n_loss=40, win_mult=1.2, loss_mult=1.0, size=10.0, span_days=30.0)
        r1 = bootstrap_kill_ci("T4M-PROJ", recs, "floor", starting_bankroll=1000.0,
                                cap_usd=500.0, kill_switch_dd=0.20, horizons=[365],
                                n_boot=8, boot_sims=200, seed=13, stake_mode="flat")
        r2 = bootstrap_kill_ci("T4M-PROJ", recs, "floor", starting_bankroll=1000.0,
                                cap_usd=500.0, kill_switch_dd=0.20, horizons=[365],
                                n_boot=8, boot_sims=200, seed=13, stake_mode="flat")
        assert r1[365] == r2[365]


class TestBuildLedgerReportFlatMode:
    def _t4_stats_and_scenarios(self):
        recs = _mk_recs(n_win=60, n_loss=40, win_mult=1.2, loss_mult=1.0, size=0.55, span_days=20.0)
        stats = derive_ledger_stats("T4M-PROJ", recs, starting_bankroll=1000.0)
        scenarios = build_ledger_scenarios(stats, stake_mode="flat", operational=t4m_proj_operational_params())
        return stats, scenarios

    def test_flat_stake_line_appears_not_stake_frac(self):
        stats, scenarios = self._t4_stats_and_scenarios()
        report = build_ledger_report("T4M-PROJ", stats, scenarios, [30, 182, 365], n_sims=500)
        assert "flat" in report
        assert "does not scale with bankroll" in report

    def test_gg105_caveat_appears_for_t4m_proj_band(self):
        stats, scenarios = self._t4_stats_and_scenarios()
        report = build_ledger_report("T4M-PROJ", stats, scenarios, [30, 182, 365], n_sims=500)
        assert "GG-105" in report
        assert "ANTI_PREDICTIVE" in report

    def test_gg105_caveat_absent_for_other_bands(self):
        recs = _mk_recs(n_win=60, n_loss=40, win_mult=1.2, loss_mult=1.0, size=10.0, span_days=20.0)
        stats = derive_ledger_stats("T1", recs, starting_bankroll=1000.0)
        scenarios = build_ledger_scenarios(stats)
        report = build_ledger_report("T1", stats, scenarios, [30, 182, 365], n_sims=500)
        assert "GG-105" not in report
