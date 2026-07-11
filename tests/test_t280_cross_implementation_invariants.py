"""T-280 / WINDOW B (B2) — cross-implementation invariants.

Each metric below has at least two independently-written implementations
somewhere in this codebase (production `src/` code and/or standalone
experiment scripts under `scripts/`). This file asserts they agree, so a
regression in either one is caught even though nothing calls both from the
same production code path.

Coverage:
  - Brier score:        c7_monitoring.monitor._compute_brier
                         vs scripts/run_exp017c_calibration_mlb.py::brier_murphy
  - Temperature scaling ("Platt" in the original WINDOW B brief -- the actual
                         C3 calibration mechanism is temperature scaling per
                         ADR-0027, not sklearn Platt scaling; see
                         c3_forecasting/calibration.py module docstring):
                         c3_forecasting.calibration.temperature_scale
                         vs the algebraically-equivalent power-mean closed form
                         p_cal = p^(1/T) / (p^(1/T) + (1-p)^(1/T))
  - ECE:                 c7_monitoring.monitor._compute_ece
                         vs scripts/run_exp017c_calibration_mlb.py::ece
  - Kelly:               already covered by
                         tests/test_c4_risk.py::TestComputeKellySize::
                         test_direct_formula_agrees_with_algebraic_simplification
                         (direct f*=(p*b-q)/b vs simplified f*=p-q*mip/(1-mip)) --
                         not duplicated here.
"""
from __future__ import annotations

import random
import sys
from pathlib import Path

import pytest

# GG-109/B4 (WINDOW B, 2026-07-09): explicit worktree-local src guard, matching
# tests/test_c4_risk.py's established pattern. Without this, `prediction_market_bot`
# binds via the shared Python env's static .pth file (main tree's src/) whenever
# this file is collected/run before any test that inserts its own worktree src
# first -- silently validating the wrong tree's code. See GG-109.
_SRC = Path(__file__).parent.parent / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from prediction_market_bot.c3_forecasting.calibration import temperature_scale
from prediction_market_bot.c7_monitoring.monitor import (
    ForecastOutcomeRecord,
    _compute_brier,
    _compute_ece,
)

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
from run_exp017c_calibration_mlb import brier_murphy, ece as script_ece  # noqa: E402

_CAL_EPS = 1e-9


def _synthetic_records(n: int = 200, seed: int = 280) -> list[ForecastOutcomeRecord]:
    """Deterministic synthetic (p_estimate, outcome) pairs spanning [0,1]."""
    rng = random.Random(seed)
    records = []
    for _ in range(n):
        p = rng.uniform(0.01, 0.99)
        # Outcome correlated with p (not pure noise) so bins aren't degenerate.
        outcome = 1 if rng.random() < p else 0
        records.append(
            ForecastOutcomeRecord(
                p_estimate=p, outcome=outcome, market_implied_prob=0.5
            )
        )
    return records


def _as_script_dicts(records: list[ForecastOutcomeRecord]) -> list[dict]:
    return [{"_model_p": r.p_estimate, "_event": r.outcome} for r in records]


# ---------------------------------------------------------------------------
# Brier score
# ---------------------------------------------------------------------------


class TestBrierCrossImplementation:
    @pytest.mark.unit
    def test_monitor_and_exp017c_agree_on_synthetic_data(self):
        records = _synthetic_records()
        dicts = _as_script_dicts(records)

        brier_monitor = _compute_brier(records)
        brier_script = brier_murphy(dicts, bins=10)["brier_full"]

        assert brier_monitor == pytest.approx(brier_script, abs=1e-9)

    @pytest.mark.unit
    @pytest.mark.parametrize("seed", [1, 2, 3, 4, 5])
    def test_agreement_holds_across_multiple_datasets(self, seed):
        records = _synthetic_records(n=50, seed=seed)
        dicts = _as_script_dicts(records)

        assert _compute_brier(records) == pytest.approx(
            brier_murphy(dicts, bins=10)["brier_full"], abs=1e-9
        )

    @pytest.mark.unit
    def test_murphy_decomposition_recomposes_exactly(self):
        """The reliability-resolution-uncertainty identity must hold on its
        own terms (recompose_ok), independent of the monitor cross-check --
        a defense-in-depth invariant on the decomposition itself."""
        records = _synthetic_records(n=300, seed=42)
        result = brier_murphy(_as_script_dicts(records), bins=10)
        assert result["recompose_ok"] is True

    @pytest.mark.unit
    def test_brier_score_bounded_zero_to_one_for_binary_outcomes(self):
        """Brier in [0,1] here specifically (binary 0/1 outcome, p in [0,1] --
        the general prediction-market bound of [0,2] applies to +-1-coded
        outcomes elsewhere in the codebase, not this 0/1 outcome convention)."""
        records = _synthetic_records(n=100, seed=7)
        b = _compute_brier(records)
        assert 0.0 <= b <= 1.0


# ---------------------------------------------------------------------------
# Temperature scaling ("Platt" in the original brief)
# ---------------------------------------------------------------------------


def _power_mean_reference(p: float, temperature: float) -> float:
    """Algebraic closed form equivalent to sigmoid(logit(p)/T):

        p_cal = p^(1/T) / (p^(1/T) + (1-p)^(1/T))

    Derivation: sigmoid(logit(p)/T) = 1 / (1 + exp(-logit(p)/T))
    exp(-logit(p)/T) = (p/(1-p))^(-1/T) = ((1-p)/p)^(1/T)
    => p_cal = 1 / (1 + ((1-p)/p)^(1/T)) = p^(1/T) / (p^(1/T) + (1-p)^(1/T))

    Clamped identically to temperature_scale's own internal clamp so the two
    formulas are compared on the same effective input, not divergent at the
    p->0/1 boundary where temperature_scale clamps internally.
    """
    p_c = min(1.0 - _CAL_EPS, max(_CAL_EPS, float(p)))
    if temperature == 1.0:
        return p_c
    inv_t = 1.0 / temperature
    num = p_c**inv_t
    den = num + (1.0 - p_c) ** inv_t
    return num / den


class TestTemperatureScalingCrossImplementation:
    @pytest.mark.unit
    @pytest.mark.parametrize("temperature", [0.5, 1.0, 1.5, 2.05, 3.10, 5.0])
    @pytest.mark.parametrize(
        "p", [0.01, 0.05, 0.1, 0.25, 0.5, 0.6, 0.75, 0.9, 0.95, 0.99]
    )
    def test_sigmoid_form_agrees_with_power_mean_form(self, p, temperature):
        sigmoid_result = temperature_scale(p, temperature)
        power_mean_result = _power_mean_reference(p, temperature)
        assert sigmoid_result == pytest.approx(power_mean_result, abs=1e-9)

    @pytest.mark.unit
    def test_identity_at_t_equals_one_exact(self):
        """T==1.0 must be an exact identity (no clamp applied) per
        temperature_scale's explicit fast-path -- not just approximately 1:1."""
        for p in (0.0001, 0.3, 0.5, 0.7, 0.9999):
            assert temperature_scale(p, 1.0) == p

    @pytest.mark.unit
    def test_frame_symmetry(self):
        """calibrate(1-p) == 1 - calibrate(p) (module docstring's frame-symmetry
        claim) for both the sigmoid form and the power-mean reference."""
        for p in (0.05, 0.2, 0.4, 0.6, 0.8, 0.95):
            for T in (0.5, 2.05, 4.0):
                assert temperature_scale(p, T) == pytest.approx(
                    1.0 - temperature_scale(1.0 - p, T), abs=1e-9
                )
                assert _power_mean_reference(p, T) == pytest.approx(
                    1.0 - _power_mean_reference(1.0 - p, T), abs=1e-9
                )


# ---------------------------------------------------------------------------
# ECE
# ---------------------------------------------------------------------------


class TestECECrossImplementation:
    @pytest.mark.unit
    def test_monitor_and_exp017c_agree_on_synthetic_data(self):
        records = _synthetic_records()
        dicts = _as_script_dicts(records)

        ece_monitor = _compute_ece(records, n_bins=10)
        ece_script = script_ece(dicts, bins=10)

        assert ece_monitor == pytest.approx(ece_script, abs=1e-9)

    @pytest.mark.unit
    @pytest.mark.parametrize("n_bins", [5, 10, 20])
    @pytest.mark.parametrize("seed", [11, 12, 13])
    def test_agreement_holds_across_bin_counts_and_datasets(self, n_bins, seed):
        records = _synthetic_records(n=80, seed=seed)
        dicts = _as_script_dicts(records)

        assert _compute_ece(records, n_bins=n_bins) == pytest.approx(
            script_ece(dicts, bins=n_bins), abs=1e-9
        )

    @pytest.mark.unit
    def test_ece_bounded_zero_to_one(self):
        records = _synthetic_records(n=150, seed=99)
        e = _compute_ece(records, n_bins=10)
        assert 0.0 <= e <= 1.0

    @pytest.mark.unit
    def test_bin_boundary_points_away_from_the_float_grid_agree(self):
        """Both implementations use the same [lo, hi) convention with the
        final bin closed on both ends -- probabilities landing just off an
        interior bin edge (e.g. 0.5 +/- a small offset, with 10 equal-width
        bins) must agree between implementations rather than being silently
        double- or un-counted by one side. (Exact-decile inputs are covered,
        and shown to legitimately diverge, by the dedicated test below.)"""
        records = [
            ForecastOutcomeRecord(p_estimate=p, outcome=o, market_implied_prob=0.5)
            for p, o in [
                (0.001, 0), (0.099, 1), (0.201, 0), (0.299, 1), (0.401, 0),
                (0.5, 1), (0.599, 0), (0.701, 1), (0.799, 0), (0.901, 1), (0.999, 1),
            ]
        ]
        dicts = _as_script_dicts(records)
        assert _compute_ece(records, n_bins=10) == pytest.approx(
            script_ece(dicts, bins=10), abs=1e-9
        )

    @pytest.mark.unit
    def test_exact_decile_inputs_can_legitimately_diverge_between_implementations(self):
        """KNOWN, NARROW divergence (found by this B2 cross-check, not a test
        bug -- do not "fix" by picking different data without also fixing the
        root cause described here):

        monitor.py builds bin edges via `np.linspace(0.0, 1.0, n_bins+1)`
        (cumulative multiplication under the hood); run_exp017c_calibration_mlb.py
        builds them via pure division `i / bins` in a Python list comprehension.
        These are NOT always the same float: np.linspace(0,1,11)[3] evaluates to
        0.30000000000000004, while 3/10 evaluates to 0.3 exactly (confirmed
        directly: 3 of the 10 interior edges drift, at i=3,6,7). A p_estimate
        landing exactly on one of the drifted edges (e.g. p=0.3) is assigned to
        bin 2 by monitor.py's `[lo, hi)` mask but bin 3 by the script's -- a
        real, reproducible cross-implementation disagreement, not floating-point
        noise within a single bin.

        Severity: negligible in practice. Real model p_estimate values come from
        continuous statistical computations (Poisson survival, logistic sigmoid,
        temperature scaling) and are essentially never exact decimal literals
        like 0.3 or 0.6 -- landing on the affected float grid points is a
        measure-zero event for live data. Registered as a documented, accepted,
        low-severity finding (not a blocking defect) rather than silently
        avoided by choosing friendlier test data.
        """
        import numpy as np

        linspace_edges = np.linspace(0.0, 1.0, 11)
        division_edges = [i / 10 for i in range(11)]
        drifted = [
            i for i in range(11) if linspace_edges[i] != division_edges[i]
        ]
        assert drifted == [3, 6, 7]  # locks in the exact drifted indices found

        records = [
            ForecastOutcomeRecord(p_estimate=p, outcome=o, market_implied_prob=0.5)
            for p, o in [
                (0.0, 0), (0.1, 1), (0.2, 0), (0.3, 1), (0.4, 0),
                (0.5, 1), (0.6, 0), (0.7, 1), (0.8, 0), (0.9, 1), (1.0, 1),
            ]
        ]
        dicts = _as_script_dicts(records)
        ece_monitor = _compute_ece(records, n_bins=10)
        ece_script = script_ece(dicts, bins=10)
        # Documents the divergence exists (and its exact magnitude on this
        # fixture) rather than asserting the two agree -- they provably do not
        # for this specific exact-decile input.
        assert ece_monitor != pytest.approx(ece_script, abs=1e-9)
        assert ece_monitor == pytest.approx(0.28181818181818186, abs=1e-9)
        assert ece_script == pytest.approx(0.40909090909090917, abs=1e-9)
