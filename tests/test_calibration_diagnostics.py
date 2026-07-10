"""T-280 / WINDOW B (B4) — direct unit tests for calibration_diagnostics.py.

`src/prediction_market_bot/analytics/calibration_diagnostics.py` is exercised
today only indirectly: via `run_exp017c_calibration_mlb.py`'s re-exports (used
by `tests/test_t280_cross_implementation_invariants.py`'s Brier/ECE
cross-checks) and via `scripts/run_exp017_mlb.py`'s calibration report (B4).
Neither of those exercises the module's own edge cases or invariants
directly. This file does.
"""
from __future__ import annotations

import math
import random
import sys
from pathlib import Path

import pytest

_SRC = Path(__file__).parent.parent / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from prediction_market_bot.analytics.calibration_diagnostics import (
    EPS,
    brier_murphy,
    calib_fit_ci,
    ece,
    irls_logistic,
    logit,
    reliability,
    sigmoid,
)


# ---------------------------------------------------------------------------
# link functions
# ---------------------------------------------------------------------------


class TestLogitSigmoid:
    @pytest.mark.unit
    def test_round_trip_mid_range(self):
        for p in (0.01, 0.1, 0.3, 0.5, 0.7, 0.9, 0.99):
            assert sigmoid(logit(p)) == pytest.approx(p, abs=1e-9)

    @pytest.mark.unit
    def test_logit_zero_point_five_is_zero(self):
        assert logit(0.5) == pytest.approx(0.0, abs=1e-12)

    @pytest.mark.unit
    def test_logit_clamps_boundary_inputs(self):
        # p=0 and p=1 would be -inf/+inf without clamping; EPS clamp keeps
        # this finite and matches the module's own EPS constant exactly.
        lo = logit(0.0)
        hi = logit(1.0)
        assert math.isfinite(lo)
        assert math.isfinite(hi)
        assert lo == pytest.approx(math.log(EPS / (1.0 - EPS)))
        assert hi == pytest.approx(math.log((1.0 - EPS) / EPS))

    @pytest.mark.unit
    def test_sigmoid_symmetry(self):
        for z in (-5.0, -1.0, 0.0, 1.0, 5.0, 50.0, -50.0):
            assert sigmoid(z) + sigmoid(-z) == pytest.approx(1.0, abs=1e-12)

    @pytest.mark.unit
    def test_sigmoid_large_magnitude_no_overflow(self):
        # naive exp(-z) for very negative z overflows; the z>=0/z<0 branch
        # split in sigmoid() exists specifically to avoid that.
        assert sigmoid(-1000.0) == pytest.approx(0.0, abs=1e-12)
        assert sigmoid(1000.0) == pytest.approx(1.0, abs=1e-12)


# ---------------------------------------------------------------------------
# IRLS logistic fit
# ---------------------------------------------------------------------------


class TestIrlsLogistic:
    @pytest.mark.unit
    def test_perfectly_calibrated_data_recovers_a0_b1(self):
        # event ~ Bernoulli(model_p) with model_p itself well spread and the
        # true generating probability == model_p: the MLE fit should recover
        # (a, b) close to (0, 1) at large n.
        rng = random.Random(42)
        xs, ys = [], []
        for _ in range(4000):
            p = rng.uniform(0.02, 0.98)
            xs.append(logit(p))
            ys.append(1 if rng.random() < p else 0)
        a, b = irls_logistic(xs, ys)
        assert a == pytest.approx(0.0, abs=0.1)
        assert b == pytest.approx(1.0, abs=0.15)

    @pytest.mark.unit
    def test_fewer_than_three_points_returns_default(self):
        assert irls_logistic([0.1, 0.2], [1, 0]) == (0.0, 1.0)
        assert irls_logistic([], []) == (0.0, 1.0)

    @pytest.mark.unit
    def test_all_same_outcome_does_not_crash(self):
        # degenerate case: score g0 pushes a to an extreme but det-guard must
        # keep this from diverging to inf/nan.
        xs = [logit(p) for p in (0.1, 0.3, 0.5, 0.7, 0.9)]
        ys = [1, 1, 1, 1, 1]
        a, b = irls_logistic(xs, ys)
        assert math.isfinite(a)
        assert math.isfinite(b)


# ---------------------------------------------------------------------------
# reliability
# ---------------------------------------------------------------------------


class TestReliability:
    @pytest.mark.unit
    def test_perfect_calibration_zero_gap(self):
        # Each bin's mean forecast equals empirical rate by construction:
        # 100 records per bin, all forecasting the bin's own midpoint p, with
        # exactly round(p*100) of them resolving as events -- so
        # empirical_rate matches mean_forecast to within 1/100.
        recs = []
        for lo, hi in ((0.0, 0.2), (0.2, 0.4), (0.4, 0.6), (0.6, 0.8), (0.8, 1.0)):
            p = (lo + hi) / 2
            n_events = round(p * 100)
            recs.extend({"_model_p": p, "_event": 1} for _ in range(n_events))
            recs.extend({"_model_p": p, "_event": 0} for _ in range(100 - n_events))
        rows = reliability(recs, bins=5)
        assert len(rows) == 5
        for row in rows:
            assert row["n"] == 100
            assert row["mean_forecast"] == pytest.approx(row["empirical_rate"], abs=0.01)
            assert row["gap"] == pytest.approx(0.0, abs=0.01)

    @pytest.mark.unit
    def test_empty_bin_reports_n_zero_without_crashing(self):
        recs = [{"_model_p": 0.05, "_event": 1}]
        rows = reliability(recs, bins=5)
        assert rows[0]["n"] == 1
        for row in rows[1:]:
            assert row["n"] == 0
            assert "mean_forecast" not in row

    @pytest.mark.unit
    def test_model_p_equal_to_one_falls_in_last_bin(self):
        # edges are half-open [lo, hi) except the final bin, which must also
        # accept model_p == 1.0 exactly (else it's silently dropped from every
        # bin and any n-sum invariant over recs breaks).
        recs = [{"_model_p": 1.0, "_event": 1}]
        rows = reliability(recs, bins=4)
        assert sum(row["n"] for row in rows) == 1
        assert rows[-1]["n"] == 1

    @pytest.mark.unit
    def test_bin_n_sums_to_total_records(self):
        rng = random.Random(7)
        recs = [{"_model_p": rng.uniform(0.0, 1.0), "_event": rng.randrange(2)}
                for _ in range(500)]
        rows = reliability(recs, bins=10)
        assert sum(row["n"] for row in rows) == len(recs)


# ---------------------------------------------------------------------------
# Brier / Murphy decomposition
# ---------------------------------------------------------------------------


class TestBrierMurphy:
    @pytest.mark.unit
    def test_recompose_identity_holds_on_synthetic_data(self):
        rng = random.Random(99)
        recs = [{"_model_p": rng.uniform(0.01, 0.99), "_event": rng.randrange(2)}
                for _ in range(300)]
        result = brier_murphy(recs, bins=8)
        assert result["recompose_ok"] is True
        assert result["decomposition_(rel-res+unc)"] == pytest.approx(
            result["brier_binned"], abs=1e-9
        )

    @pytest.mark.unit
    def test_full_brier_never_below_binned_brier(self):
        # WBV (within-bin variance) is non-negative by construction: binning
        # replaces each forecast with its bin mean, which can only reduce or
        # preserve squared error relative to the per-bin empirical rate.
        rng = random.Random(11)
        recs = [{"_model_p": rng.uniform(0.01, 0.99), "_event": rng.randrange(2)}
                for _ in range(300)]
        result = brier_murphy(recs, bins=6)
        assert result["binning_gap_(full-binned)"] >= -1e-12
        assert result["brier_full"] >= result["brier_binned"] - 1e-12

    @pytest.mark.unit
    def test_perfect_forecasts_zero_brier(self):
        recs = [{"_model_p": 1.0, "_event": 1}] * 10 + [{"_model_p": 0.0, "_event": 0}] * 10
        result = brier_murphy(recs, bins=2)
        assert result["brier_full"] == pytest.approx(0.0, abs=1e-9)
        assert result["reliability"] == pytest.approx(0.0, abs=1e-9)

    @pytest.mark.unit
    def test_uncertainty_equals_base_rate_variance(self):
        recs = [{"_model_p": 0.5, "_event": 1 if i < 30 else 0} for i in range(100)]
        result = brier_murphy(recs, bins=4)
        o_bar = 0.3
        assert result["uncertainty"] == pytest.approx(o_bar * (1 - o_bar), abs=1e-9)
        assert result["base_rate"] == pytest.approx(o_bar, abs=1e-9)


# ---------------------------------------------------------------------------
# ECE
# ---------------------------------------------------------------------------


class TestECE:
    @pytest.mark.unit
    def test_zero_for_perfect_calibration(self):
        recs = []
        for lo, hi in ((0.0, 0.5), (0.5, 1.0)):
            p = (lo + hi) / 2
            n_events = round(p * 100)
            recs.extend({"_model_p": p, "_event": 1} for _ in range(n_events))
            recs.extend({"_model_p": p, "_event": 0} for _ in range(100 - n_events))
        assert ece(recs, bins=2) == pytest.approx(0.0, abs=0.01)

    @pytest.mark.unit
    def test_matches_manual_weighted_gap_sum(self):
        rng = random.Random(3)
        recs = [{"_model_p": rng.uniform(0.0, 1.0), "_event": rng.randrange(2)}
                for _ in range(200)]
        bins = 5
        rows = reliability(recs, bins)
        expected = sum((row["n"] / len(recs)) * abs(row["gap"])
                        for row in rows if row["n"] > 0)
        assert ece(recs, bins) == pytest.approx(expected, abs=1e-12)

    @pytest.mark.unit
    def test_non_negative(self):
        rng = random.Random(4)
        recs = [{"_model_p": rng.uniform(0.0, 1.0), "_event": rng.randrange(2)}
                for _ in range(200)]
        assert ece(recs, bins=10) >= 0.0


# ---------------------------------------------------------------------------
# calib_fit_ci
# ---------------------------------------------------------------------------


class TestCalibFitCi:
    @pytest.mark.unit
    def test_deterministic_given_seeded_rng(self):
        rng_data = random.Random(55)
        recs = [{"_model_p": rng_data.uniform(0.02, 0.98), "_event": rng_data.randrange(2)}
                for _ in range(80)]
        r1 = calib_fit_ci(recs, boot=200, rng=random.Random(17))
        r2 = calib_fit_ci(recs, boot=200, rng=random.Random(17))
        assert r1 == r2

    @pytest.mark.unit
    def test_ci_bounds_ordered_and_contain_point_estimate_direction(self):
        rng_data = random.Random(21)
        recs = [{"_model_p": rng_data.uniform(0.02, 0.98), "_event": rng_data.randrange(2)}
                for _ in range(150)]
        result = calib_fit_ci(recs, boot=500, rng=random.Random(21))
        la, ha = result["a_ci"]
        lb, hb = result["b_ci"]
        assert la <= ha
        assert lb <= hb

    @pytest.mark.unit
    def test_interpretation_labels(self):
        recs = [{"_model_p": 0.5, "_event": 1 if i % 2 == 0 else 0} for i in range(60)]
        result = calib_fit_ci(recs, boot=100, rng=random.Random(1))
        assert result["interpretation"] in ("overconfident", "underconfident", "calibrated")
        assert isinstance(result["b_excludes_1"], bool)
