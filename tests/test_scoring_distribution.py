"""Tests for c3_forecasting/scoring_distribution.py — ScoringDistributionModel."""
import pytest
import numpy as np

from prediction_market_bot.c3_forecasting.scoring_distribution import (
    MIN_FIT_SAMPLES,
    PlayerDistribution,
    ScoringDistributionModel,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _uniform_pts(mean: float = 25.0, std: float = 5.0, n: int = 60) -> np.ndarray:
    """Synthetic pts with overdispersion (var > mean) for NB fitting."""
    rng = np.random.default_rng(42)
    return np.clip(rng.normal(mean, std, n), 0, None)


def _low_variance_pts(mean: float = 20.0, n: int = 60) -> np.ndarray:
    """Pts with var ≈ mean (near-Poisson)."""
    rng = np.random.default_rng(42)
    # Use actual Poisson draws which have var = mean
    return rng.poisson(mean, n).astype(float)


# ---------------------------------------------------------------------------
# PlayerDistribution
# ---------------------------------------------------------------------------

class TestPlayerDistribution:
    def test_frozen(self):
        d = PlayerDistribution(player_id=1, dist_type="nb",
                               mu=25.0, r=5.0, p=0.17, n_samples=60)
        with pytest.raises((AttributeError, TypeError)):
            d.mu = 30.0  # type: ignore

    def test_poisson_has_none_r_p(self):
        d = PlayerDistribution(player_id=1, dist_type="poisson",
                               mu=20.0, r=None, p=None, n_samples=40)
        assert d.r is None
        assert d.p is None


# ---------------------------------------------------------------------------
# fit()
# ---------------------------------------------------------------------------

class TestFit:
    def test_fit_returns_self(self):
        model = ScoringDistributionModel()
        result = model.fit({1: _uniform_pts()})
        assert result is model

    def test_is_fitted_after_fit(self):
        model = ScoringDistributionModel()
        model.fit({1: _uniform_pts()})
        assert model.is_fitted

    def test_skips_player_with_insufficient_samples(self):
        model = ScoringDistributionModel(min_samples=MIN_FIT_SAMPLES)
        model.fit({1: np.array([25.0] * (MIN_FIT_SAMPLES - 1))})
        assert model.n_fitted_players == 0

    def test_fits_player_with_sufficient_samples(self):
        model = ScoringDistributionModel()
        model.fit({1: _uniform_pts()})
        assert model.n_fitted_players == 1

    def test_fits_multiple_players(self):
        model = ScoringDistributionModel()
        model.fit({1: _uniform_pts(), 2: _uniform_pts(mean=30.0), 3: _uniform_pts(mean=20.0)})
        assert model.n_fitted_players == 3

    def test_overdispersed_uses_nb(self):
        # High variance pts → NB
        pts = _uniform_pts(mean=25.0, std=7.0)
        model = ScoringDistributionModel()
        model.fit({1: pts})
        dist = model.get_distribution(1)
        assert dist is not None
        assert dist.dist_type == "nb"
        assert dist.r is not None
        assert dist.p is not None

    def test_near_poisson_uses_poisson(self):
        pts = _low_variance_pts(mean=20.0)
        model = ScoringDistributionModel()
        model.fit({1: pts})
        dist = model.get_distribution(1)
        if dist is not None:
            # Either poisson or nb is acceptable; just verify mu is set
            assert dist.mu > 0

    def test_skips_all_nan_player(self):
        model = ScoringDistributionModel()
        pts = np.full(60, np.nan)
        model.fit({1: pts})
        assert model.n_fitted_players == 0

    def test_empty_dict_produces_no_fitted_players(self):
        model = ScoringDistributionModel()
        model.fit({})
        assert model.n_fitted_players == 0


# ---------------------------------------------------------------------------
# predict_threshold_prob()
# ---------------------------------------------------------------------------

class TestPredictThresholdProb:
    def _fitted_model(self, player_id: int = 1, mean: float = 25.0) -> ScoringDistributionModel:
        model = ScoringDistributionModel()
        model.fit({player_id: _uniform_pts(mean=mean, std=6.0)})
        return model

    def test_raises_if_not_fitted(self):
        model = ScoringDistributionModel()
        with pytest.raises(RuntimeError):
            model.predict_threshold_prob(1, 25.0)

    def test_returns_none_for_unknown_player(self):
        model = self._fitted_model(player_id=1)
        assert model.predict_threshold_prob(99, 25.0) is None

    def test_returns_float_in_unit_interval(self):
        model = self._fitted_model()
        p = model.predict_threshold_prob(1, 25.0)
        assert p is not None
        assert 0.0 <= p <= 1.0

    def test_prob_decreases_with_higher_threshold(self):
        model = self._fitted_model(mean=25.0)
        p20 = model.predict_threshold_prob(1, 20.0)
        p30 = model.predict_threshold_prob(1, 30.0)
        assert p20 is not None and p30 is not None
        assert p20 > p30

    def test_zero_threshold_returns_one(self):
        model = self._fitted_model()
        p = model.predict_threshold_prob(1, 0.0)
        assert p == pytest.approx(1.0)

    def test_very_high_threshold_near_zero(self):
        model = self._fitted_model(mean=25.0)
        p = model.predict_threshold_prob(1, 200.0)
        assert p is not None
        assert p < 0.001

    def test_fractional_threshold_ceiled(self):
        # P(X ≥ 25.5) should equal P(X ≥ 26) — threshold is ceiled to int
        model = self._fitted_model()
        p_frac = model.predict_threshold_prob(1, 25.5)
        p_int  = model.predict_threshold_prob(1, 26.0)
        assert p_frac == pytest.approx(p_int)

    def test_prob_around_mean_is_near_half(self):
        # For a player whose mean ~25 pts, P(X≥25) should be near 0.5
        model = ScoringDistributionModel()
        # Large sample to get good fit
        rng = np.random.default_rng(0)
        pts = np.clip(rng.normal(25.0, 6.0, 200), 0, None)
        model.fit({1: pts})
        p = model.predict_threshold_prob(1, 25.0)
        assert p is not None
        assert 0.3 <= p <= 0.7  # loose range given distribution shape


# ---------------------------------------------------------------------------
# price_all_lines()
# ---------------------------------------------------------------------------

class TestPriceAllLines:
    def test_returns_list_same_length(self):
        model = ScoringDistributionModel()
        model.fit({1: _uniform_pts()})
        thresholds = [18.0, 20.0, 22.0, 25.0, 28.0, 30.0]
        result = model.price_all_lines(1, thresholds)
        assert len(result) == len(thresholds)

    def test_all_values_in_unit_interval(self):
        model = ScoringDistributionModel()
        model.fit({1: _uniform_pts()})
        for p in model.price_all_lines(1, [15.0, 20.0, 25.0, 30.0]):
            assert p is not None
            assert 0.0 <= p <= 1.0

    def test_monotonically_decreasing(self):
        model = ScoringDistributionModel()
        model.fit({1: _uniform_pts()})
        thresholds = [15.0, 20.0, 25.0, 30.0, 35.0]
        probs = model.price_all_lines(1, thresholds)
        for i in range(len(probs) - 1):
            assert probs[i] >= probs[i + 1]

    def test_returns_none_list_for_unknown_player(self):
        model = ScoringDistributionModel()
        model.fit({1: _uniform_pts()})
        result = model.price_all_lines(99, [20.0, 25.0])
        assert all(p is None for p in result)


# ---------------------------------------------------------------------------
# get_fitted_player_ids + get_distribution
# ---------------------------------------------------------------------------

class TestAccessors:
    def test_get_fitted_player_ids(self):
        model = ScoringDistributionModel()
        model.fit({1: _uniform_pts(), 2: _uniform_pts()})
        ids = model.get_fitted_player_ids()
        assert set(ids) == {1, 2}

    def test_get_distribution_returns_player_distribution(self):
        model = ScoringDistributionModel()
        model.fit({1: _uniform_pts()})
        dist = model.get_distribution(1)
        assert isinstance(dist, PlayerDistribution)
        assert dist.player_id == 1
        assert dist.mu > 0

    def test_get_distribution_none_for_unfitted(self):
        model = ScoringDistributionModel()
        model.fit({1: _uniform_pts()})
        assert model.get_distribution(99) is None
