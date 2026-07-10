"""T-280 / WINDOW B (B5) — golden tests with hand-derived analytic answers.

Every prior WINDOW B test file checks *relative* properties: two
implementations agreeing (B2), an invariant holding across generated inputs
(B3), a module's own internal consistency (B4). None of them assert that a
function returns a specific number computed independently, by hand, from the
documented formula. This file closes that gap: each case below is derived
from the closed-form math (not from running the code and copying the output),
then checked against the real implementation.

Determinism for this file specifically is trivial (no RNG involved anywhere
below) -- the values here are exact rational/closed-form numbers. The global
seeding/Hypothesis-profile machinery lives in `tests/conftest.py` (B5) and
covers the *other* files in this suite that do use randomness.
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

import pytest

_SRC = Path(__file__).parent.parent / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from prediction_market_bot.analytics.calibration_diagnostics import brier_murphy, ece
from prediction_market_bot.c3_forecasting.calibration import temperature_scale
from prediction_market_bot.c4_risk_engine.risk import _compute_kelly_size
from prediction_market_bot.c7_monitoring.monitor import ForecastOutcomeRecord, _compute_brier, _compute_ece

import importlib.util

_spec = importlib.util.spec_from_file_location(
    "run_t4_mlb_live", _SRC / "prediction_market_bot" / "run_t4_mlb_live.py"
)
_runner = importlib.util.module_from_spec(_spec)
sys.modules["run_t4_mlb_live"] = _runner
_spec.loader.exec_module(_runner)
_binomial_pmf = _runner._binomial_pmf
p_hits_gte_threshold = _runner.p_hits_gte_threshold


# ---------------------------------------------------------------------------
# Kelly sizing (c4_risk_engine/risk.py::_compute_kelly_size)
#
# b = (1-mip)/mip; f* = (p*b - (1-p))/b; f_live = f* * kelly_fraction;
# size = min(f_live * bankroll, cap).
# ---------------------------------------------------------------------------


class TestKellyGolden:
    @pytest.mark.unit
    def test_case_even_odds_half_kelly_of_full_edge(self):
        # mip=0.5 -> b=1.0 -> f* = p - (1-p) = 2p-1 = 0.2 at p=0.6.
        # f_live = 0.2 * 0.25 = 0.05 -> $50 on a $1000 bankroll.
        size = _compute_kelly_size(
            p_estimate=0.6, market_implied_prob=0.5, kelly_fraction=0.25, bankroll=1000.0
        )
        assert size == pytest.approx(50.0, abs=1e-9)

    @pytest.mark.unit
    def test_case_favorable_odds_larger_stake(self):
        # mip=0.4 -> b=1.5; p=0.7 -> f* = (0.7*1.5 - 0.3)/1.5 = 0.5.
        # f_live = 0.5 * 0.25 = 0.125 -> $125 on a $1000 bankroll (below the $500 cap).
        size = _compute_kelly_size(
            p_estimate=0.7, market_implied_prob=0.4, kelly_fraction=0.25, bankroll=1000.0
        )
        assert size == pytest.approx(125.0, abs=1e-9)

    @pytest.mark.unit
    def test_case_negative_edge_returns_zero(self):
        # mip=0.6 -> b=(0.4/0.6)=0.6667; p=0.5 -> f* = (0.5*0.6667-0.5)/0.6667 < 0.
        size = _compute_kelly_size(
            p_estimate=0.5, market_implied_prob=0.6, kelly_fraction=0.25, bankroll=1000.0
        )
        assert size == 0.0


# ---------------------------------------------------------------------------
# Temperature scaling (c3_forecasting/calibration.py::temperature_scale)
#
# T=1.0 -> identity. Else sigmoid(logit(p)/T).
# ---------------------------------------------------------------------------


class TestTemperatureScaleGolden:
    @pytest.mark.unit
    def test_identity_at_t_equals_one(self):
        for p in (0.01, 0.3, 0.5, 0.7, 0.99):
            assert temperature_scale(p, 1.0) == pytest.approx(p, abs=1e-12)

    @pytest.mark.unit
    def test_half_is_a_fixed_point_for_any_temperature(self):
        # logit(0.5) == 0 regardless of T, so sigmoid(0/T) == 0.5 always.
        for t in (0.5, 2.0, 5.0):
            assert temperature_scale(0.5, t) == pytest.approx(0.5, abs=1e-9)

    @pytest.mark.unit
    def test_known_sigmoid_value(self):
        # p = sigmoid(1.0) = 1/(1+e^-1) => logit(p) = 1.0 exactly.
        # At T=2.0: logit(p)/T = 0.5 => temperature_scale(p, 2.0) == sigmoid(0.5).
        p = 1.0 / (1.0 + math.exp(-1.0))
        expected = 1.0 / (1.0 + math.exp(-0.5))
        assert temperature_scale(p, 2.0) == pytest.approx(expected, abs=1e-9)
        assert expected == pytest.approx(0.6224593312018546, abs=1e-9)


# ---------------------------------------------------------------------------
# Brier / ECE (c7_monitoring/monitor.py -- distinct implementation+bin
# convention from calibration_diagnostics.py, see T-281)
# ---------------------------------------------------------------------------


class TestMonitorBrierEceGolden:
    @pytest.mark.unit
    def test_brier_golden_one_tenth(self):
        # 9 perfect predictions (error^2 = 0) + 1 maximally-wrong prediction
        # (p=0.0, outcome=1 -> error^2 = 1.0) -> mean = 1.0/10 = 0.1 exactly.
        records = [ForecastOutcomeRecord(p_estimate=0.0, outcome=0, market_implied_prob=0.5)
                   for _ in range(9)]
        records.append(ForecastOutcomeRecord(p_estimate=0.0, outcome=1, market_implied_prob=0.5))
        assert _compute_brier(records) == pytest.approx(0.1, abs=1e-12)

    @pytest.mark.unit
    def test_ece_golden_two_bins(self):
        # n_bins=2 -> edges [0.0, 0.5, 1.0].
        # bin0 [0,0.5): preds {0.1,0.4} mean=0.25, outcomes {0,1} frac_pos=0.5, gap=0.25
        # bin1 [0.5,1.0]: preds {0.6,0.9} mean=0.75, outcomes {0,1} frac_pos=0.5, gap=0.25
        # ECE = 0.5*0.25 + 0.5*0.25 = 0.25 exactly.
        records = [
            ForecastOutcomeRecord(p_estimate=0.1, outcome=0, market_implied_prob=0.5),
            ForecastOutcomeRecord(p_estimate=0.4, outcome=1, market_implied_prob=0.5),
            ForecastOutcomeRecord(p_estimate=0.6, outcome=0, market_implied_prob=0.5),
            ForecastOutcomeRecord(p_estimate=0.9, outcome=1, market_implied_prob=0.5),
        ]
        assert _compute_ece(records, n_bins=2) == pytest.approx(0.25, abs=1e-12)


# ---------------------------------------------------------------------------
# Binomial PMF + Bayesian hit-threshold update (run_t4_mlb_live.py)
# ---------------------------------------------------------------------------


class TestBinomialPmfGolden:
    @pytest.mark.unit
    def test_symmetric_case(self):
        # C(5,2) * 0.5^2 * 0.5^3 = 10 * 0.25 * 0.125 = 0.3125
        assert _binomial_pmf(5, 2, 0.5) == pytest.approx(0.3125, abs=1e-12)

    @pytest.mark.unit
    def test_single_success_case(self):
        # C(3,1) * 0.5^1 * 0.5^2 = 3 * 0.5 * 0.25 = 0.375
        assert _binomial_pmf(3, 1, 0.5) == pytest.approx(0.375, abs=1e-12)

    @pytest.mark.unit
    def test_all_failures_edge_case(self):
        # C(4,0) * 0.3^0 * 0.7^4 = 1 * 1 * 0.2401 = 0.2401
        assert _binomial_pmf(4, 0, 0.3) == pytest.approx(0.2401, abs=1e-12)

    @pytest.mark.unit
    def test_all_successes_edge_case(self):
        # C(4,4) * 0.3^4 * 0.7^0 = 1 * 0.0081 * 1 = 0.0081
        assert _binomial_pmf(4, 4, 0.3) == pytest.approx(0.0081, abs=1e-9)


class TestPHitsGteThresholdGolden:
    @pytest.mark.unit
    def test_golden_probability_at_least_two_of_four_at_p_half(self):
        # n=4, p=0.5: P(X=0..4) = 1,4,6,4,1 / 16.
        # P(X>=2) = (6+4+1)/16 = 11/16 = 0.6875 exactly.
        result = p_hits_gte_threshold(h_so_far=0, threshold=2, ba_l10=0.5, ab_remaining=4)
        assert result == pytest.approx(0.6875, abs=1e-12)

    @pytest.mark.unit
    def test_already_achieved_returns_one(self):
        assert p_hits_gte_threshold(h_so_far=3, threshold=2, ba_l10=0.3, ab_remaining=2) == 1.0

    @pytest.mark.unit
    def test_mathematically_impossible_returns_zero(self):
        assert p_hits_gte_threshold(h_so_far=0, threshold=5, ba_l10=0.5, ab_remaining=2) == 0.0


# ---------------------------------------------------------------------------
# Murphy decomposition (analytics/calibration_diagnostics.py)
#
# n=4, bins=2, model_p=[0.2,0.2,0.7,0.7], event=[0,1,1,0] -- every field
# hand-traced against the real bin_of()/reliability() code path (not just the
# textbook formula) so this doubles as a worked example of the module's exact
# binning semantics.
# ---------------------------------------------------------------------------


class TestMurphyDecompositionGolden:
    _RECS = [
        {"_model_p": 0.2, "_event": 0},
        {"_model_p": 0.2, "_event": 1},
        {"_model_p": 0.7, "_event": 1},
        {"_model_p": 0.7, "_event": 0},
    ]

    @pytest.mark.unit
    def test_all_nine_fields_exact(self):
        result = brier_murphy(self._RECS, bins=2)
        assert result["brier_full"] == pytest.approx(0.315, abs=1e-12)
        assert result["brier_binned"] == pytest.approx(0.315, abs=1e-12)
        assert result["reliability"] == pytest.approx(0.065, abs=1e-12)
        assert result["resolution"] == pytest.approx(0.0, abs=1e-12)
        assert result["uncertainty"] == pytest.approx(0.25, abs=1e-12)
        assert result["decomposition_(rel-res+unc)"] == pytest.approx(0.315, abs=1e-12)
        assert result["binning_gap_(full-binned)"] == pytest.approx(0.0, abs=1e-12)
        assert result["base_rate"] == pytest.approx(0.5, abs=1e-12)
        assert result["recompose_ok"] is True

    @pytest.mark.unit
    def test_ece_on_same_golden_dataset(self):
        # bin0 gap |0.2-0.5|=0.3 weight 0.5; bin1 gap |0.7-0.5|=0.2 weight 0.5
        # ECE = 0.5*0.3 + 0.5*0.2 = 0.25 exactly.
        assert ece(self._RECS, bins=2) == pytest.approx(0.25, abs=1e-12)
