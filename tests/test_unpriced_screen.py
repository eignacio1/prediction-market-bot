"""W89.3 known-answer tests for the unpriced-share screen (EXPLORATORY)."""
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "12_EXPLORATORY" / "unpriced_screen"))
import screen as S  # noqa: E402


def test_recovers_known_share():
    r = S._simulate_check()
    assert r["lo"] < 0.6 < r["hi"] and abs(r["b"] - 0.6) < 0.05


def test_fully_priced_term_has_no_unpriced_part():
    rng = np.random.default_rng(2); n = 1500
    e, t = rng.normal(0, 6, n), rng.normal(0, 2, n)
    r = S.share_priced(e, t, 0.8 * e + 1.0 * t + rng.normal(0, 1, n), np.arange(n), B=300)
    assert r["lo"] < 1.0 < r["hi"] and S.unpriced_prob(2.0, r["hi"], 0.03) == 0.0


def test_bh_known():
    assert S.bh([0.001, 0.2, 0.9]).tolist() == [True, False, False]


def test_part_b_ridge_recovers_known_signal():
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "12_EXPLORATORY" / "unpriced_screen"))
    import part_b_weather as P
    rng = np.random.default_rng(3); X = rng.normal(0, 1, (4000, 4)); y = 2.0 * X[:, 2] + rng.normal(0, 1, 4000)
    f = P.ridge(X, y); pred = f(X)
    assert np.corrcoef(pred, 2.0 * X[:, 2])[0, 1] > 0.98
