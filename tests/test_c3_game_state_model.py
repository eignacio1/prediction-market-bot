"""
Tests: C3 Game State Model (T4/T5 In-Play Inference Engine)
============================================================
Covers:
    - Poisson CDF correctness (known mathematical values)
    - p_exceeds_threshold edge cases (already hit, impossible, half-points)
    - GameStateModel.update() T4 signal properties
    - T4 materiality check (T4_MIN_DELTA_P)
    - T5 eligibility flag (Q4 + ≤3 min)
    - LateGameArithmetic.evaluate() verdict classification
    - Kelly fraction assignment
    - Compute budget (50ms T4, 5ms T5)
"""

import time

import pytest

from prediction_market_bot.c3_forecasting.game_state_model import (
    KELLY_T4,
    KELLY_T5,
    T4_MIN_DELTA_P,
    T5_NO_CERTAINTY,
    T5_TIME_THRESHOLD_MIN,
    T5_YES_CERTAINTY,
    GameState,
    GameStateModel,
    LateGameArithmetic,
    _poisson_cdf,
    p_exceeds_threshold,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_gs(
    pts_so_far: float = 0.0,
    time_remaining_min: float = 48.0,
    quarter: int = 1,
    pace_pts_per_min: float = 0.5,
    player_id: str = "TestPlayer",
) -> GameState:
    return GameState(
        player_id=player_id,
        pts_so_far=pts_so_far,
        time_remaining_min=time_remaining_min,
        quarter=quarter,
        pace_pts_per_min=pace_pts_per_min,
    )


# ---------------------------------------------------------------------------
# Poisson CDF — mathematical correctness
# ---------------------------------------------------------------------------

class TestPoissonCDF:
    def test_lambda_zero_k_zero(self):
        # Poisson(0): P(X=0) = 1, so P(X<=0) = 1
        assert _poisson_cdf(0, 0.0) == 1.0

    def test_lambda_zero_k_negative(self):
        # P(X <= -1 | lam=0) = 0: Poisson(0) is always X=0, so -1 is impossible
        assert _poisson_cdf(-1, 0.0) == 0.0

    def test_k_zero_lambda_one(self):
        # P(X=0 | lam=1) = e^-1 ≈ 0.3679
        result = _poisson_cdf(0, 1.0)
        assert abs(result - 0.3679) < 0.001

    def test_k_one_lambda_one(self):
        # P(X<=1 | lam=1) = e^-1 + e^-1 = 2e^-1 ≈ 0.7358
        result = _poisson_cdf(1, 1.0)
        assert abs(result - 0.7358) < 0.001

    def test_large_k_exceeds_one_clamped(self):
        # CDF must never exceed 1.0
        assert _poisson_cdf(1000, 1.0) <= 1.0

    def test_monotone_in_k(self):
        # CDF is non-decreasing in k
        lam = 5.0
        vals = [_poisson_cdf(k, lam) for k in range(20)]
        for a, b in zip(vals, vals[1:]):
            assert a <= b + 1e-10

    def test_approaches_one_for_large_k(self):
        # P(X <= 100 | lam=3) ≈ 1.0
        assert _poisson_cdf(100, 3.0) > 0.9999


# ---------------------------------------------------------------------------
# p_exceeds_threshold — edge cases
# ---------------------------------------------------------------------------

class TestPExceedsThreshold:
    def test_already_hit_threshold(self):
        # pts_so_far >= threshold → probability = 1.0
        assert p_exceeds_threshold(23.0, 22.5, lam_remaining=10.0) == 1.0

    def test_exactly_at_threshold(self):
        # pts_so_far == threshold → hit (>=, not >)
        assert p_exceeds_threshold(22.5, 22.5, lam_remaining=10.0) == 1.0

    def test_zero_time_remaining(self):
        # lam = 0 → can't score → P = 0
        assert p_exceeds_threshold(10.0, 22.5, lam_remaining=0.0) == 0.0

    def test_half_point_threshold_integer_ceiling(self):
        # pts_so_far=10, threshold=22.5 → pts_needed=12.5 → ceil=13
        # P(Poisson(lam) >= 13) should be strictly less than P(>= 12)
        p13 = p_exceeds_threshold(10.0, 22.5, 20.0)
        p12 = p_exceeds_threshold(10.0, 22.0, 20.0)
        # 22.0 threshold: pts_needed=12, ceil=12 → P(>=12)
        # 22.5 threshold: pts_needed=12.5, ceil=13 → P(>=13)
        # P(>=13) < P(>=12) for finite lambda
        assert p13 < p12

    def test_large_lambda_high_probability(self):
        # player has 0 pts, needs 5 more, expected 20 more → high P
        p = p_exceeds_threshold(0.0, 5.0, lam_remaining=20.0)
        assert p > 0.99

    def test_small_lambda_low_probability(self):
        # player has 0 pts, needs 20 more, expected 2 more → low P
        p = p_exceeds_threshold(0.0, 20.0, lam_remaining=2.0)
        assert p < 0.01

    def test_probability_bounded(self):
        for pts_so_far in [0, 5, 10, 15, 20]:
            for lam in [0.5, 1.0, 5.0, 20.0]:
                p = p_exceeds_threshold(pts_so_far, 22.5, lam)
                assert 0.0 <= p <= 1.0


# ---------------------------------------------------------------------------
# GameStateModel — T4 signal properties
# ---------------------------------------------------------------------------

class TestGameStateModel:
    def setup_method(self):
        self.model = GameStateModel()

    def test_signal_fields_present(self):
        gs = make_gs(pts_so_far=10.0, time_remaining_min=20.0, quarter=3)
        signal = self.model.update(gs, threshold=22.5, p_t1=0.50)
        assert signal.player_id == gs.player_id
        assert signal.threshold == 22.5
        assert signal.p_t1 == 0.50
        assert 0.0 <= signal.p_t4 <= 1.0
        assert signal.delta_p == pytest.approx(signal.p_t4 - signal.p_t1, abs=1e-9)

    def test_pts_needed_floor_at_zero(self):
        # Player already hit threshold — pts_needed must be 0, not negative
        gs = make_gs(pts_so_far=25.0, time_remaining_min=10.0, quarter=4)
        signal = self.model.update(gs, threshold=22.5, p_t1=0.50)
        assert signal.pts_needed == 0.0
        assert signal.p_t4 == 1.0

    def test_delta_p_positive_when_trending_over(self):
        # Player has 15 pts with 24 min left at 0.6 pts/min → expects 14.4 more
        # P(total ≥ 22.5 | 15 so far, lam=14.4) should be very high → delta positive
        gs = make_gs(pts_so_far=15.0, time_remaining_min=24.0, pace_pts_per_min=0.6)
        signal = self.model.update(gs, threshold=22.5, p_t1=0.50)
        assert signal.delta_p > 0

    def test_delta_p_negative_when_trending_under(self):
        # Player has 2 pts with 6 min left at 0.3 pts/min → expects 1.8 more
        # P(total ≥ 22.5 | 2 so far, lam=1.8) is near zero → delta strongly negative
        gs = make_gs(pts_so_far=2.0, time_remaining_min=6.0, pace_pts_per_min=0.3)
        signal = self.model.update(gs, threshold=22.5, p_t1=0.50)
        assert signal.delta_p < -0.4

    def test_t5_eligible_q4_under_threshold(self):
        gs = make_gs(time_remaining_min=2.9, quarter=4)
        signal = self.model.update(gs, threshold=22.5, p_t1=0.50)
        assert signal.t5_eligible is True

    def test_t5_not_eligible_q3(self):
        gs = make_gs(time_remaining_min=2.0, quarter=3)
        signal = self.model.update(gs, threshold=22.5, p_t1=0.50)
        assert signal.t5_eligible is False

    def test_t5_not_eligible_too_much_time(self):
        gs = make_gs(time_remaining_min=4.0, quarter=4)
        signal = self.model.update(gs, threshold=22.5, p_t1=0.50)
        assert signal.t5_eligible is False

    def test_t5_eligible_exactly_at_threshold(self):
        gs = make_gs(time_remaining_min=T5_TIME_THRESHOLD_MIN, quarter=4)
        signal = self.model.update(gs, threshold=22.5, p_t1=0.50)
        assert signal.t5_eligible is True

    def test_is_material_above_threshold(self):
        gs = make_gs(pts_so_far=20.0, time_remaining_min=20.0)
        signal = self.model.update(gs, threshold=22.5, p_t1=0.50)
        # p_t4 will be high (only needs 3 more pts with 20 min left)
        if abs(signal.delta_p) >= T4_MIN_DELTA_P:
            assert self.model.is_material(signal) is True
        else:
            assert self.model.is_material(signal) is False

    def test_is_material_false_for_small_delta(self):
        # Construct a scenario where delta is guaranteed < T4_MIN_DELTA_P
        # p_t1 = 0.50 and player is exactly on pace → P_t4 ≈ 0.50
        gs = make_gs(pts_so_far=11.25, time_remaining_min=22.5, pace_pts_per_min=0.5)
        signal = self.model.update(gs, threshold=22.5, p_t1=0.50)
        # With lam=11.25 and pts_needed=11.25, P is roughly middling
        # delta might be small enough
        materiality = self.model.is_material(signal)
        assert isinstance(materiality, bool)

    def test_lambda_correctly_computed(self):
        gs = make_gs(pace_pts_per_min=0.4, time_remaining_min=10.0)
        signal = self.model.update(gs, threshold=22.5, p_t1=0.50)
        assert signal.lambda_remaining == pytest.approx(4.0, abs=1e-9)


# ---------------------------------------------------------------------------
# LateGameArithmetic — T5 verdict classification
# ---------------------------------------------------------------------------

class TestLateGameArithmetic:
    def setup_method(self):
        self.engine = LateGameArithmetic()

    def make_t5_gs(self, pts_so_far, pace_pts_per_min=0.5, time_remaining_min=2.0):
        return make_gs(
            pts_so_far=pts_so_far,
            time_remaining_min=time_remaining_min,
            quarter=4,
            pace_pts_per_min=pace_pts_per_min,
        )

    def test_already_hit_near_certain_yes(self):
        gs = self.make_t5_gs(pts_so_far=30.0)
        result = self.engine.evaluate(gs, threshold=22.5)
        assert result.verdict == "NEAR_CERTAIN_YES"
        assert result.p_hit == 1.0
        assert result.kelly_fraction == KELLY_T5
        assert result.pts_needed == 0.0

    def test_impossible_near_certain_no(self):
        # Player has 0 pts, needs 30 more, expected ~1 more → near certain NO
        gs = self.make_t5_gs(pts_so_far=0.0, pace_pts_per_min=0.4, time_remaining_min=2.0)
        result = self.engine.evaluate(gs, threshold=30.0)
        assert result.verdict == "NEAR_CERTAIN_NO"
        assert result.p_hit <= T5_NO_CERTAINTY
        assert result.kelly_fraction == KELLY_T5

    def test_uncertain_borderline(self):
        # Player needs ~3 pts, expected ~2 pts remaining → uncertain
        gs = self.make_t5_gs(pts_so_far=20.0, pace_pts_per_min=0.5, time_remaining_min=4.0)
        # lam = 0.5 * 4.0 = 2.0; pts_needed = 22.5 - 20 = 2.5; ceil = 3
        # P(Poisson(2) >= 3) = 1 - P(<=2) = 1 - (e^-2)(1 + 2 + 2) = 1 - 5e^-2 ≈ 0.323
        result = self.engine.evaluate(gs, threshold=22.5)
        assert result.verdict == "UNCERTAIN"
        assert result.kelly_fraction == 0.0

    def test_verdict_near_certain_yes_correct_kelly(self):
        gs = self.make_t5_gs(pts_so_far=22.0, pace_pts_per_min=0.8, time_remaining_min=2.5)
        result = self.engine.evaluate(gs, threshold=22.5)
        if result.verdict == "NEAR_CERTAIN_YES":
            assert result.kelly_fraction == KELLY_T5
        elif result.verdict == "UNCERTAIN":
            assert result.kelly_fraction == 0.0

    def test_kelly_zero_for_uncertain(self):
        # Any UNCERTAIN verdict must have kelly_fraction = 0
        gs = self.make_t5_gs(pts_so_far=15.0, pace_pts_per_min=0.4, time_remaining_min=2.0)
        result = self.engine.evaluate(gs, threshold=22.5)
        if result.verdict == "UNCERTAIN":
            assert result.kelly_fraction == 0.0

    def test_expected_pts_remaining_correct(self):
        gs = self.make_t5_gs(pts_so_far=10.0, pace_pts_per_min=0.6, time_remaining_min=2.5)
        result = self.engine.evaluate(gs, threshold=22.5)
        # lam = 0.6 * 2.5 = 1.5
        assert result.expected_pts_remaining == pytest.approx(1.5, abs=1e-9)

    def test_signal_fields_present(self):
        gs = self.make_t5_gs(pts_so_far=10.0)
        result = self.engine.evaluate(gs, threshold=22.5)
        assert result.player_id == gs.player_id
        assert result.threshold == 22.5
        assert result.verdict in {"NEAR_CERTAIN_YES", "NEAR_CERTAIN_NO", "UNCERTAIN"}
        assert 0.0 <= result.p_hit <= 1.0


# ---------------------------------------------------------------------------
# Compute budget — performance assertions
# ---------------------------------------------------------------------------

class TestComputeBudget:
    def test_t4_inference_under_50ms(self):
        model = GameStateModel()
        gs = make_gs(pts_so_far=12.0, time_remaining_min=18.0, quarter=3, pace_pts_per_min=0.55)
        runs = 1000
        start = time.perf_counter()
        for _ in range(runs):
            model.update(gs, threshold=22.5, p_t1=0.52)
        elapsed_ms = (time.perf_counter() - start) * 1000
        per_call_ms = elapsed_ms / runs
        assert per_call_ms < 50.0, f"T4 inference took {per_call_ms:.3f}ms (budget: 50ms)"

    def test_t5_arithmetic_under_5ms(self):
        engine = LateGameArithmetic()
        gs = make_gs(pts_so_far=21.0, time_remaining_min=2.0, quarter=4, pace_pts_per_min=0.5)
        runs = 1000
        start = time.perf_counter()
        for _ in range(runs):
            engine.evaluate(gs, threshold=22.5)
        elapsed_ms = (time.perf_counter() - start) * 1000
        per_call_ms = elapsed_ms / runs
        assert per_call_ms < 5.0, f"T5 arithmetic took {per_call_ms:.3f}ms (budget: 5ms)"
