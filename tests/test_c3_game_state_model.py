"""
Tests: C3 Game State Model (T4/T5 In-Play Inference Engine)
============================================================
Covers:
    - Poisson CDF correctness (known mathematical values)
    - p_exceeds_threshold edge cases (already hit, impossible, half-points)
    - GameStateModel.update() T4 signal properties
    - T4 materiality gate (ADR-0021: |delta_p_incr| >= max(Z·σ_null, floor))
    - null_delta_sigma structural invariants (tip-off zero, final-horn limit,
      martingale monotonicity, Poisson-additivity mean-zero)
    - T5 eligibility flag (Q4 + ≤3 min)
    - LateGameArithmetic.evaluate() verdict classification
    - Kelly fraction assignment
    - Compute budget (50ms T4, 5ms T5)
"""

import time

import pytest

from prediction_market_bot.c3_forecasting.game_state_model import (
    GAME_MINUTES_TOTAL,
    KELLY_T4,
    KELLY_T5,
    T4_DELTA_SIGMA_Z,
    T4_MIN_DELTA_FLOOR,
    T5_NO_CERTAINTY,
    T5_TIME_THRESHOLD_MIN,
    T5_YES_CERTAINTY,
    GameState,
    GameStateModel,
    LateGameArithmetic,
    _poisson_cdf,
    null_delta_sigma,
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

    def test_is_material_consistent_with_gate(self):
        gs = make_gs(pts_so_far=20.0, time_remaining_min=20.0)
        signal = self.model.update(gs, threshold=22.5, p_t1=0.50)
        gate = max(T4_DELTA_SIGMA_Z * signal.sigma_null, T4_MIN_DELTA_FLOOR)
        assert self.model.is_material(signal) == (abs(signal.delta_p_incr) >= gate)

    def test_not_material_at_tipoff(self):
        # At tip-off the current state IS the null state: delta_p_incr = 0
        # identically, regardless of any calibration gap vs p_t1.
        gs = make_gs(pts_so_far=0.0, time_remaining_min=48.0)
        signal = self.model.update(gs, threshold=22.5, p_t1=0.01)
        assert signal.delta_p_incr == pytest.approx(0.0, abs=1e-12)
        assert self.model.is_material(signal) is False

    def test_not_material_when_on_expectation_midgame(self):
        # Player scoring exactly at pregame pace at halftime → the game has
        # confirmed the prior, not moved it. Must not fire.
        gs = make_gs(pts_so_far=12.0, time_remaining_min=24.0, pace_pts_per_min=0.5)
        signal = self.model.update(gs, threshold=24.5, p_t1=0.50)
        assert self.model.is_material(signal) is False

    def test_material_when_far_above_expectation(self):
        # 20 pts by halftime on a 0.4 pts/min pace (expected ~9.6) chasing a
        # 22.5 threshold: genuine live signal, must fire.
        gs = make_gs(pts_so_far=20.0, time_remaining_min=24.0, pace_pts_per_min=0.4)
        signal = self.model.update(gs, threshold=22.5, p_t1=0.50)
        assert signal.delta_p_incr > 0
        assert self.model.is_material(signal) is True

    def test_baseline_is_stateless_and_restart_safe(self):
        # Baseline depends only on (pace, threshold) — identical regardless of
        # the game state it is computed from (process-restart safety).
        gs_early = make_gs(pts_so_far=2.0, time_remaining_min=44.0)
        gs_late = make_gs(pts_so_far=18.0, time_remaining_min=10.0)
        s1 = self.model.update(gs_early, threshold=22.5, p_t1=0.50)
        s2 = self.model.update(gs_late, threshold=22.5, p_t1=0.50)
        assert s1.p_t4_baseline == pytest.approx(s2.p_t4_baseline, abs=1e-12)

    def test_lambda_correctly_computed(self):
        gs = make_gs(pace_pts_per_min=0.4, time_remaining_min=10.0)
        signal = self.model.update(gs, threshold=22.5, p_t1=0.50)
        assert signal.lambda_remaining == pytest.approx(4.0, abs=1e-9)


# ---------------------------------------------------------------------------
# null_delta_sigma — structural invariants of the ADR-0021 noise envelope
# ---------------------------------------------------------------------------

class TestNullDeltaSigma:
    """
    The materiality gate is only sound if the null envelope obeys the
    mathematical structure it claims. Each test asserts one structural
    invariant — these are the institutional coverage for ADR-0021.
    """

    PACE = 0.5          # 24 expected pts over 48 min
    THRESHOLD = 22.5

    def test_zero_at_tipoff(self):
        # No game information yet → no noise envelope.
        assert null_delta_sigma(self.PACE, self.THRESHOLD, 48.0) == 0.0

    def test_final_horn_limit(self):
        # At t_rem=0 the outcome is fully resolved: delta is a shifted
        # Bernoulli(baseline) → σ = sqrt(b·(1−b)) exactly.
        b = p_exceeds_threshold(0.0, self.THRESHOLD, self.PACE * GAME_MINUTES_TOTAL)
        sigma = null_delta_sigma(self.PACE, self.THRESHOLD, 0.0)
        assert sigma == pytest.approx((b * (1.0 - b)) ** 0.5, abs=1e-6)

    def test_monotone_nondecreasing_in_elapsed_time(self):
        # Martingale variance accumulates: σ_null can only grow as the game
        # progresses. Sweep the full game at 1-minute resolution.
        sigmas = [
            null_delta_sigma(self.PACE, self.THRESHOLD, float(t_rem))
            for t_rem in range(48, -1, -1)
        ]
        for earlier, later in zip(sigmas, sigmas[1:]):
            assert later >= earlier - 1e-9

    def test_null_mean_is_zero_by_poisson_additivity(self):
        # Σ_k pmf(k)·p_t4(k) must equal the baseline exactly — this is the
        # property that makes delta_p_incr calibration-free.
        import math as _math
        t_rem = 24.0
        lam_e = self.PACE * (GAME_MINUTES_TOTAL - t_rem)
        lam_r = self.PACE * t_rem
        baseline = p_exceeds_threshold(0.0, self.THRESHOLD, self.PACE * GAME_MINUTES_TOTAL)
        mean = 0.0
        pmf = _math.exp(-lam_e)
        for k in range(200):
            mean += pmf * p_exceeds_threshold(float(k), self.THRESHOLD, lam_r)
            pmf *= lam_e / (k + 1)
        assert mean == pytest.approx(baseline, abs=1e-9)

    def test_zero_pace_no_crash(self):
        # Scratch player / bad feature data: envelope collapses to zero,
        # economic floor governs the gate.
        assert null_delta_sigma(0.0, self.THRESHOLD, 24.0) == 0.0

    def test_bad_feed_time_beyond_regulation(self):
        # t_rem > 48 clamps elapsed to 0 → σ = 0 (no envelope inflation
        # from a malformed feed).
        assert null_delta_sigma(self.PACE, self.THRESHOLD, 55.0) == 0.0

    def test_negative_time_clamped(self):
        # t_rem < 0 (feed glitch at final horn) behaves as t_rem = 0.
        s_neg = null_delta_sigma(self.PACE, self.THRESHOLD, -2.0)
        s_zero = null_delta_sigma(self.PACE, self.THRESHOLD, 0.0)
        assert s_neg == pytest.approx(s_zero, abs=1e-9)

    def test_envelope_bounded_by_bernoulli_max(self):
        # σ_null can never exceed the final-horn Bernoulli σ — the variance
        # of a bounded martingale is maximal at resolution.
        b = p_exceeds_threshold(0.0, self.THRESHOLD, self.PACE * GAME_MINUTES_TOTAL)
        cap = (b * (1.0 - b)) ** 0.5 + 1e-9
        for t_rem in (40.0, 30.0, 20.0, 10.0, 5.0, 1.0):
            assert null_delta_sigma(self.PACE, self.THRESHOLD, t_rem) <= cap

    def test_high_pace_star_player(self):
        # λ_full = 48·0.9 = 43.2 (Brunson-class load) — enumeration must stay
        # exact and bounded; mean-zero property must still hold.
        import math as _math
        pace, thr, t_rem = 0.9, 30.5, 18.0
        lam_e = pace * (GAME_MINUTES_TOTAL - t_rem)
        lam_r = pace * t_rem
        baseline = p_exceeds_threshold(0.0, thr, pace * GAME_MINUTES_TOTAL)
        mean = 0.0
        pmf = _math.exp(-lam_e)
        for k in range(300):
            mean += pmf * p_exceeds_threshold(float(k), thr, lam_r)
            pmf *= lam_e / (k + 1)
        assert mean == pytest.approx(baseline, abs=1e-8)
        sigma = null_delta_sigma(pace, thr, t_rem)
        assert 0.0 < sigma < 0.5

    def test_compute_budget(self):
        # Full-game sweep across 5 thresholds in well under the 50ms budget.
        start = time.perf_counter()
        for thr in (10.5, 15.5, 20.5, 25.5, 30.5):
            for t_rem in range(0, 49, 4):
                null_delta_sigma(0.7, thr, float(t_rem))
        elapsed_ms = (time.perf_counter() - start) * 1000.0
        assert elapsed_ms < 50.0


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


# ---------------------------------------------------------------------------
# parse_ticker_opponent (ADR-0015)
# ---------------------------------------------------------------------------

from prediction_market_bot.c3_forecasting.game_state_model import (
    LEAGUE_AVG_PTS_ALLOWED,
    OPP_ADJ_MAX,
    OPP_ADJ_MIN,
    opp_adjusted_lambda,
    parse_ticker_opponent,
)


class TestParseTickerOpponent:
    def test_nyk_player_returns_sas(self):
        ticker = "KXNBAPTS-26JUN03NYKSAS-NYKJBRUNSON11-20"
        assert parse_ticker_opponent(ticker) == "SAS"

    def test_sas_player_returns_nyk(self):
        ticker = "KXNBAPTS-26JUN03NYKSAS-SASVWEMBANYAMA1-40"
        assert parse_ticker_opponent(ticker) == "NYK"

    def test_malformed_too_few_parts(self):
        assert parse_ticker_opponent("KXNBAPTS-26JUN03NYKSAS") is None

    def test_malformed_short_segment1(self):
        assert parse_ticker_opponent("KXNBAPTS-26JUN03-NYKBRUNSON-20") is None

    def test_empty_string(self):
        assert parse_ticker_opponent("") is None

    def test_player_team_not_in_matchup(self):
        # OKC player in a NYK-SAS ticker
        ticker = "KXNBAPTS-26JUN03NYKSAS-OKCSGA-20"
        assert parse_ticker_opponent(ticker) is None

    def test_different_matchup(self):
        ticker = "KXNBAPTS-26MAY15BOSGSW-BOSTATUM0-25"
        assert parse_ticker_opponent(ticker) == "GSW"

    def test_away_team_player(self):
        ticker = "KXNBAPTS-26MAY15BOSGSW-GSWCURRY30-30"
        assert parse_ticker_opponent(ticker) == "BOS"


# ---------------------------------------------------------------------------
# opp_adjusted_lambda (ADR-0015)
# ---------------------------------------------------------------------------

class _MockStore:
    """Minimal TeamStatsStore interface for unit testing."""
    def __init__(self, rating):  # float | None
        self._rating = rating

    def get_opp_def_rating(self, opp, as_of_date, **kw):
        return self._rating


class TestOppAdjustedLambda:
    def test_no_store_returns_raw(self):
        result = opp_adjusted_lambda(25.0, "KXNBAPTS-26JUN03NYKSAS-NYKJBRUNSON11-20", None, "2026-06-03")
        assert result == 25.0

    def test_strong_defense_reduces_lambda(self):
        store = _MockStore(90.0)  # well below league avg 113
        result = opp_adjusted_lambda(25.0, "KXNBAPTS-26JUN03NYKSAS-NYKJBRUNSON11-20", store, "2026-06-03")
        assert result < 25.0
        assert result == pytest.approx(25.0 * (90.0 / LEAGUE_AVG_PTS_ALLOWED))

    def test_weak_defense_increases_lambda(self):
        store = _MockStore(130.0)  # above league avg
        result = opp_adjusted_lambda(20.0, "KXNBAPTS-26JUN03NYKSAS-NYKJBRUNSON11-20", store, "2026-06-03")
        assert result > 20.0

    def test_floor_clamps_extreme_defense(self):
        store = _MockStore(50.0)  # very strong D → factor = 50/113 = 0.44 → clamped to 0.70
        result = opp_adjusted_lambda(25.0, "KXNBAPTS-26JUN03NYKSAS-NYKJBRUNSON11-20", store, "2026-06-03")
        assert result == pytest.approx(25.0 * OPP_ADJ_MIN)

    def test_ceiling_clamps_extreme_offense(self):
        store = _MockStore(200.0)  # very weak D → factor = 200/113 = 1.77 → clamped to 1.30
        result = opp_adjusted_lambda(20.0, "KXNBAPTS-26JUN03NYKSAS-NYKJBRUNSON11-20", store, "2026-06-03")
        assert result == pytest.approx(20.0 * OPP_ADJ_MAX)

    def test_league_avg_defense_returns_unchanged(self):
        store = _MockStore(LEAGUE_AVG_PTS_ALLOWED)
        result = opp_adjusted_lambda(22.5, "KXNBAPTS-26JUN03NYKSAS-NYKJBRUNSON11-20", store, "2026-06-03")
        assert result == pytest.approx(22.5)

    def test_unparseable_ticker_returns_raw(self):
        store = _MockStore(90.0)
        result = opp_adjusted_lambda(25.0, "BAD-TICKER", store, "2026-06-03")
        assert result == 25.0

    def test_unknown_opponent_returns_raw(self):
        store = _MockStore(None)  # store returns None for unknown team
        result = opp_adjusted_lambda(25.0, "KXNBAPTS-26JUN03NYKSAS-NYKJBRUNSON11-20", store, "2026-06-03")
        assert result == 25.0
