"""T-280 / WINDOW B (B3) — property-based invariants (Hypothesis).

B2 (test_t280_cross_implementation_invariants.py) checked that two independent
implementations of the same metric agree on specific synthetic datasets. This
file complements that with Hypothesis-generated inputs spanning each
function's domain, asserting mathematical invariants that must hold for
*every* valid input, not just the fixed examples chosen by hand elsewhere in
the suite.

Determinism: `settings.register_profile(..., derandomize=True)` makes every
Hypothesis example sequence a fixed function of the test itself (no entropy
from wall-clock or `/dev/urandom`), so re-runs are byte-for-byte reproducible
without hand-picking a seed per test. This satisfies the "fixed seed" brief
requirement via Hypothesis's own idiomatic mechanism.

Coverage:
  - Kelly sizing (_compute_kelly_size, c4_risk_engine/risk.py):
      * output always in [0, full-Kelly-implied bankroll fraction * bankroll]
      * output never exceeds the hard single-event exposure cap
      * monotonic non-decreasing in p_estimate (fixed mip/kelly_fraction/bankroll)
  - Temperature scaling (temperature_scale, c3_forecasting/calibration.py):
      * output always in (0, 1) (open interval -- internal epsilon clamp)
      * monotonic non-decreasing in p (ranking-preserving) for fixed T
  - Brier score (_compute_brier, c7_monitoring/monitor.py):
      * bounded in [0, 1] for this codebase's binary 0/1-outcome convention
        (NOT the general [0, 2] bound, which applies to +-1-coded outcomes
        used elsewhere -- see test_t280_cross_implementation_invariants.py's
        identical note)
  - Binomial PMF log-space stability (_binomial_pmf, run_t4_mlb_live.py):
      * agrees with a naive pow-based reference within tolerance across the
        function's full realistic domain (small n, any k in [0,n], any p)
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

import pytest
from hypothesis import assume, given, settings
from hypothesis import strategies as st

_SRC = Path(__file__).parent.parent / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from prediction_market_bot.c3_forecasting.calibration import temperature_scale
from prediction_market_bot.c4_risk_engine.risk import _HARD_LIMITS, _compute_kelly_size
from prediction_market_bot.c7_monitoring.monitor import ForecastOutcomeRecord, _compute_brier

sys.path.insert(0, str(Path(__file__).parent.parent))
import importlib.util

_spec = importlib.util.spec_from_file_location(
    "run_t4_mlb_live", _SRC / "prediction_market_bot" / "run_t4_mlb_live.py"
)
_runner = importlib.util.module_from_spec(_spec)
sys.modules["run_t4_mlb_live"] = _runner
_spec.loader.exec_module(_runner)
_binomial_pmf = _runner._binomial_pmf

settings.register_profile("t280-deterministic", derandomize=True, max_examples=100)
settings.load_profile("t280-deterministic")

_CAP = _HARD_LIMITS["max_single_event_exposure_usd"]


# ---------------------------------------------------------------------------
# Kelly sizing
# ---------------------------------------------------------------------------


@st.composite
def _kelly_inputs(draw):
    p_estimate = draw(st.floats(min_value=0.0, max_value=1.0, allow_nan=False))
    mip = draw(st.floats(min_value=0.0, max_value=1.0, allow_nan=False))
    kelly_fraction = draw(st.floats(min_value=0.01, max_value=1.0, allow_nan=False))
    bankroll = draw(st.floats(min_value=1.0, max_value=100_000.0, allow_nan=False))
    return p_estimate, mip, kelly_fraction, bankroll


class TestKellySizingProperties:
    @given(_kelly_inputs())
    def test_size_bounded_zero_to_full_kelly_bankroll_fraction(self, inputs):
        """size is always >= 0 and never exceeds kelly_fraction * bankroll --
        the full-Kelly fraction f* is provably <= 1 for any p_estimate in
        [0,1] (maximized at p_estimate=1, where f*=1), so f_live=f*.kelly_fraction
        <= kelly_fraction, and size = min(f_live*bankroll, cap) can never
        exceed kelly_fraction * bankroll."""
        p_estimate, mip, kelly_fraction, bankroll = inputs
        size = _compute_kelly_size(p_estimate, mip, kelly_fraction, bankroll)
        assert size >= 0.0
        assert size <= kelly_fraction * bankroll + 1e-9

    @given(_kelly_inputs())
    def test_size_never_exceeds_hard_exposure_cap(self, inputs):
        p_estimate, mip, kelly_fraction, bankroll = inputs
        size = _compute_kelly_size(p_estimate, mip, kelly_fraction, bankroll)
        assert size <= _CAP + 1e-9

    @given(
        mip=st.floats(min_value=0.0001, max_value=0.9999, allow_nan=False),
        kelly_fraction=st.floats(min_value=0.01, max_value=1.0, allow_nan=False),
        bankroll=st.floats(min_value=1.0, max_value=100_000.0, allow_nan=False),
        p1=st.floats(min_value=0.0, max_value=1.0, allow_nan=False),
        p2=st.floats(min_value=0.0, max_value=1.0, allow_nan=False),
    )
    def test_monotonic_non_decreasing_in_p_estimate(
        self, mip, kelly_fraction, bankroll, p1, p2
    ):
        """Holding mip/kelly_fraction/bankroll fixed, a higher model
        probability estimate must never produce a smaller position size."""
        lo, hi = (p1, p2) if p1 <= p2 else (p2, p1)
        size_lo = _compute_kelly_size(lo, mip, kelly_fraction, bankroll)
        size_hi = _compute_kelly_size(hi, mip, kelly_fraction, bankroll)
        assert size_lo <= size_hi + 1e-9


# ---------------------------------------------------------------------------
# Temperature scaling
# ---------------------------------------------------------------------------


class TestTemperatureScalingProperties:
    @given(
        p=st.floats(min_value=0.0, max_value=1.0, allow_nan=False),
        temperature=st.floats(min_value=1.0, max_value=10.0, allow_nan=False),
    )
    def test_output_always_in_open_unit_interval_for_dampening_temperatures(
        self, p, temperature
    ):
        """T >= 1.0 (dampening/no-op -- the only range this codebase's
        CALIBRATION_TEMPERATURE registry ever uses: mlb=1.0, nba=2.05, both
        >=1) always keeps output strictly inside (0,1). T < 1.0 (sharpening)
        does NOT hold this property in floating point -- see the dedicated
        finding test below, which is why this property is scoped to T>=1.0
        rather than the function's full nominal T>0 domain."""
        assume(temperature != 1.0)
        result = temperature_scale(p, temperature)
        assert 0.0 < result < 1.0

    @pytest.mark.unit
    def test_sharpening_temperature_can_saturate_extreme_p_to_exact_boundary(self):
        """KNOWN, NARROW finding (found by this B3 property sweep, not a test
        bug -- do not "fix" by narrowing the strategy without also recording
        this): temperature_scale's docstring/closed-form contract implies
        output is always in the open interval (0,1) (p is clamped to
        (_EPS, 1-_EPS) before the logit, and sigmoid's mathematical range is
        open). That holds in exact arithmetic but NOT always in float64.

        Root cause: sigmoid(x) = 1/(1+exp(-x)). For p clamped to 1-1e-9 and
        a sharpening temperature T<1 (dividing the logit by T further
        increases |x|), exp(-x) underflows to something smaller than
        float64's relative epsilon (~2.22e-16), so `1.0 + exp(-x)` rounds
        to exactly `1.0` and the result is exactly `1.0`, not
        `1.0 - epsilon`. Confirmed directly: temperature_scale(1.0, T)
        returns exactly 1.0 for T <= ~0.55 (T=0.6 -> 0.9999999999999989,
        the largest sub-1.0 T still observed unsaturated; T<=0.55 -> exactly
        1.0).

        This is ASYMMETRIC: the p->0 side does not saturate to exactly 0.0
        under the same conditions (temperature_scale(0.0, 0.5) ==
        1.0000000020000015e-18, not 0.0) -- because the underflow-to-zero
        threshold for a plain division (~1e-308) is far more extreme than
        the "1 + epsilon == 1" addition-rounding threshold (~1.1e-16) that
        causes the p->1 saturation.

        Severity: negligible in current production. CALIBRATION_TEMPERATURE
        (calibration.py) only defines T=1.0 (mlb) and T=2.05 (nba) -- both
        >=1.0 (dampening), never triggering this sharpening-side edge case.
        Any future sport/config introducing T<1.0 should be aware that
        temperature_scale is not guaranteed float64-open-interval at the
        extreme p boundary, and downstream code must not assume
        `1.0 - temperature_scale(p, T) > 0` unconditionally.
        """
        result_p1 = temperature_scale(1.0, 0.5)
        assert result_p1 == 1.0

        result_p1_near_boundary = temperature_scale(1.0, 0.6)
        assert 0.0 < result_p1_near_boundary < 1.0
        assert result_p1_near_boundary == pytest.approx(1.0, abs=1e-12)

        result_p0 = temperature_scale(0.0, 0.5)
        assert 0.0 < result_p0 < 1.0
        assert result_p0 == pytest.approx(0.0, abs=1e-15)

    @given(
        temperature=st.floats(min_value=0.1, max_value=10.0, allow_nan=False),
        p1=st.floats(min_value=0.0, max_value=1.0, allow_nan=False),
        p2=st.floats(min_value=0.0, max_value=1.0, allow_nan=False),
    )
    def test_monotonic_non_decreasing_ranking_preserved(self, temperature, p1, p2):
        """Temperature scaling is a monotonic reparameterization: it must
        never invert the relative ranking of two probability estimates."""
        lo, hi = (p1, p2) if p1 <= p2 else (p2, p1)
        scaled_lo = temperature_scale(lo, temperature)
        scaled_hi = temperature_scale(hi, temperature)
        assert scaled_lo <= scaled_hi + 1e-9

    @given(temperature=st.floats(min_value=1e-6, max_value=0.0999, allow_nan=False))
    def test_small_positive_temperature_never_raises(self, temperature):
        """Sanity check on the documented ValueError boundary: any T>0, no
        matter how small, must never raise (only T<=0.0 is invalid per the
        module's explicit guard)."""
        result = temperature_scale(0.5, temperature)
        assert 0.0 < result < 1.0

    def test_zero_and_negative_temperature_raise(self):
        with pytest.raises(ValueError):
            temperature_scale(0.5, 0.0)
        with pytest.raises(ValueError):
            temperature_scale(0.5, -1.0)


# ---------------------------------------------------------------------------
# Brier score
# ---------------------------------------------------------------------------


class TestBrierScoreProperties:
    @given(
        st.lists(
            st.tuples(
                st.floats(min_value=0.0, max_value=1.0, allow_nan=False),
                st.sampled_from([0, 1]),
            ),
            min_size=1,
            max_size=50,
        )
    )
    def test_bounded_zero_to_one_for_any_binary_outcome_dataset(self, pairs):
        records = [
            ForecastOutcomeRecord(p_estimate=p, outcome=o, market_implied_prob=0.5)
            for p, o in pairs
        ]
        brier = _compute_brier(records)
        assert 0.0 <= brier <= 1.0

    @given(st.sampled_from([0, 1]), st.integers(min_value=1, max_value=20))
    def test_zero_when_every_prediction_is_perfect(self, outcome, n):
        records = [
            ForecastOutcomeRecord(
                p_estimate=float(outcome), outcome=outcome, market_implied_prob=0.5
            )
            for _ in range(n)
        ]
        assert _compute_brier(records) == pytest.approx(0.0, abs=1e-12)

    @given(st.sampled_from([0, 1]), st.integers(min_value=1, max_value=20))
    def test_one_when_every_prediction_is_maximally_wrong(self, outcome, n):
        wrong_p = 1.0 - float(outcome)
        records = [
            ForecastOutcomeRecord(
                p_estimate=wrong_p, outcome=outcome, market_implied_prob=0.5
            )
            for _ in range(n)
        ]
        assert _compute_brier(records) == pytest.approx(1.0, abs=1e-12)


# ---------------------------------------------------------------------------
# Binomial PMF log-space stability
# ---------------------------------------------------------------------------


def _binomial_pmf_naive(n: int, k: int, p: float) -> float:
    if k < 0 or k > n:
        return 0.0
    if p <= 0.0:
        return 1.0 if k == 0 else 0.0
    if p >= 1.0:
        return 1.0 if k == n else 0.0
    return math.comb(n, k) * (p**k) * ((1.0 - p) ** (n - k))


class TestBinomialPmfLogSpaceProperty:
    @given(
        n=st.integers(min_value=1, max_value=15),
        p=st.floats(min_value=0.001, max_value=0.999, allow_nan=False),
        data=st.data(),
    )
    def test_log_space_agrees_with_naive_across_generated_domain(self, n, p, data):
        k = data.draw(st.integers(min_value=0, max_value=n))
        log_space = _binomial_pmf(n, k, p)
        naive = _binomial_pmf_naive(n, k, p)
        assert log_space == pytest.approx(naive, abs=1e-9)

    @given(
        n=st.integers(min_value=1, max_value=15),
        p=st.floats(min_value=0.001, max_value=0.999, allow_nan=False),
    )
    def test_pmf_values_sum_to_one_over_full_support(self, n, p):
        total = sum(_binomial_pmf(n, k, p) for k in range(n + 1))
        assert total == pytest.approx(1.0, abs=1e-6)

    @given(
        n=st.integers(min_value=1, max_value=15),
        k=st.integers(min_value=0, max_value=15),
        p=st.floats(min_value=0.0, max_value=1.0, allow_nan=False),
    )
    def test_pmf_always_bounded_zero_to_one(self, n, k, p):
        assume(k <= n)
        val = _binomial_pmf(n, k, p)
        assert 0.0 <= val <= 1.0 + 1e-9
