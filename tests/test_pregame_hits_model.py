"""EXP-028 (T-594) unit tests. Synthetic data only; no matrix required."""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from prediction_market_bot.c3_forecasting import pregame_hits_model as m

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import ab_harness_t4 as h  # noqa: E402


def test_sha_mismatch_refuses(tmp_path):
    p = tmp_path / "x.csv"
    p.write_text("a,b\n1,2\n")
    with pytest.raises(RuntimeError):
        m.load_population(p)


def test_run_gate_refuses_matrix_only_rows():
    rows = [{"game_id": "1", "game_date": "2026-01-02", "outcome": 1, "player_id": 7}]
    with pytest.raises(h.T4HarnessRefusal):
        h.run_gate(rows, lambda tr: (lambda r: 0.5), cutoff="2026-01-01", hypothesis="x")


def test_verdict_rule():
    up = {"ci_low": 0.001, "ci_high": 0.01, "mean": 0.005}
    assert m.verdict(up, {"mean": 0.01}) == "DEFENSIBLE_IMPROVEMENT"
    assert m.verdict(up, {"mean": -0.01}) == "NO DETECTABLE DIFFERENCE"
    span = {"ci_low": -0.001, "ci_high": 0.01, "mean": 0.004}
    assert m.verdict(span, {"mean": 0.01}) == "NO DETECTABLE DIFFERENCE"
    assert m.verdict({"ci_low": -0.02, "ci_high": -0.001, "mean": -0.01}, {"mean": -1}) == "HARMFUL"


def test_permutation_preserves_within_date_counts():
    d = pd.DataFrame({"game_date": ["a"] * 6 + ["b"] * 4, "y": [1, 1, 0, 0, 0, 1, 1, 0, 0, 0]})
    yp = m.permute_within_date(d)
    for dt in ("a", "b"):
        assert yp[(d.game_date == dt).values].sum() == d.y[d.game_date == dt].sum()


def test_paired_delta_zero_for_identical_predictions():
    rng = np.random.default_rng(0)
    y = rng.integers(0, 2, 400)
    p = np.full(400, 0.5)
    r = m.paired_delta(p, p, y, [str(i // 4) for i in range(400)], n_boot=200)
    assert r["delta_brier"]["mean"] == 0 and r["verdict"] == "NO DETECTABLE DIFFERENCE"


def test_model_fit_predict_shapes_and_bounds():
    rng = np.random.default_rng(1)
    n = 300
    d = pd.DataFrame({f: rng.normal(size=n) for f in m.FEATURES})
    d.loc[:20, "opp_sp_era_l5"] = np.nan
    d["y"] = (rng.random(n) < 0.58).astype(int)
    p = m.PregameHitsModel(1.0).fit(d).predict(d)
    assert p.shape == (n,) and ((p > 0) & (p < 1)).all()


def test_b1_bounded():
    d = pd.DataFrame({"ba_l10_shrunk": [0.25, np.nan], "ab_l10_mean": [3.9, 4.0], "ba_l10": [0.2, 0.3]})
    b = m.baseline_b1(d)
    assert ((b > 0) & (b < 1)).all()
