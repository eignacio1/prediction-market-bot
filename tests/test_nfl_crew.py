"""Known-answer tests for nfl_engine/crew.py (W99.1)."""
import json
import numpy as np
import pandas as pd

from prediction_market_bot.nfl_engine.crew import SHRINK_K, fit_beta, load_crew_table, prior_feature


def _tab():
    return pd.DataFrame([
        dict(ref="A", season=2020, games=16, pen=320.0, yds=2800.0),
        dict(ref="B", season=2020, games=16, pen=160.0, yds=1400.0),
        dict(ref="A", season=2021, games=16, pen=0.0, yds=0.0),
    ])


def test_no_leakage_same_season_ignored():
    # 2021 record for A (0 penalties) must not move the 2021 feature; only 2020 counts
    f = prior_feature(_tab(), "A", 2021)
    league = (320 + 160) / 32
    assert abs(f - ((320 + SHRINK_K * league) / (16 + SHRINK_K) - league)) < 1e-9
    assert f > 0


def test_unknown_or_first_season_is_zero():
    assert prior_feature(_tab(), "Z", 2021) == 0.0
    assert prior_feature(_tab(), "A", 2020) == 0.0
    assert prior_feature(_tab(), None, 2021) == 0.0


def test_shrinkage_toward_league_with_k():
    t = pd.DataFrame([dict(ref="A", season=2020, games=16, pen=320.0, yds=1.0), dict(ref="B", season=2020, games=16, pen=160.0, yds=1.0)])
    raw = 20 - 15
    f = prior_feature(t, "A", 2021)
    assert 0 < f < raw
    assert abs(f - raw * 16 / (16 + SHRINK_K)) < 1e-9


def test_fit_beta_recovers_planted_slope():
    rng = np.random.default_rng(0)
    x = rng.normal(0, 1, 5000)
    y = 0.8 * x + rng.normal(0, 5, 5000)
    assert abs(fit_beta(x, y) - 0.8) < 0.15


def test_loader_reads_season_total_only(tmp_path):
    d = tmp_path / "L3-split" / "nfl"
    d.mkdir(parents=True)
    rows = [
        dict(subject="Pete Morelli", season=2016, metric="penalties logged (count)", split="season total", value=200, population_n=16),
        dict(subject="Pete Morelli", season=2016, metric="penalty yardage (yards)", split="season total", value=1700, population_n=16),
        dict(subject="Pete Morelli", season=2016, metric="penalties logged (count)", split="season total to date", value=5, population_n=1),
    ]
    (d / "crew-penalties-2016.claims.jsonl").write_text("\n".join(json.dumps(r) for r in rows))
    t = load_crew_table(str(tmp_path))
    assert len(t) == 1 and t.ref[0] == "Peter Morelli" and t.pen[0] == 200 and t.yds[0] == 1700
