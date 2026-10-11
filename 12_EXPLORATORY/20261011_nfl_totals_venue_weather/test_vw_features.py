"""Look-ahead tests for the W68.3 venue + weather features."""
import json
import sys
from pathlib import Path

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from vw_features import (FCST_VARS, assert_forecast_legal, forecast_lead_hours, kickoff_utc,  # noqa: E402
                         stadium_category, weather_effects)


def _ext():
    rows = [("2022-09-11", "closed"), ("2022-09-25", "open"), ("2022-10-09", "closed"), ("2022-10-30", "outdoors")]
    return pd.DataFrame({"home_team": "ATL", "gameday": [r[0] for r in rows], "roof": [r[1] for r in rows],
                         "surface": "fieldturf"})


def test_stadium_category_ignores_target_and_future_games():
    a = stadium_category(_ext(), "ATL", "2022-10-09")
    e2 = _ext(); e2.loc[e2.gameday >= "2022-10-09", "roof"] = "outdoors"
    assert stadium_category(e2, "ATL", "2022-10-09") == a
    assert a["n_prior"] == 2 and a["p_indoor"] == 0.5


def test_forecast_guard_rejects_observed_and_short_lead():
    with pytest.raises(ValueError):
        assert_forecast_legal("wind", 48)
    with pytest.raises(ValueError):
        assert_forecast_legal(FCST_VARS[0], 6)
    assert_forecast_legal(FCST_VARS[1], 24)


def test_lead_is_at_least_t1_horizon():
    for g, t in (("2023-09-10", "13:00"), ("2023-12-25", "20:15"), ("2024-01-07", "16:25")):
        assert forecast_lead_hours(kickoff_utc(g, t)) >= 24.0


def test_fetched_forecasts_all_legal_leads():
    p = Path(__file__).resolve().parent / "forecast_kickoff.json"
    if p.exists():
        assert min(v["lead_h"] for v in json.loads(p.read_text()).values()) >= 24.0


def test_weather_scaled_by_exposure_and_missing_is_zero():
    assert weather_effects(1.0, 25, 20)["wind_eff"] == 0.0
    assert weather_effects(0.0, 20, 35) == {"wind_eff": 20.0, "cold_eff": 20.0, "has_wx": 1.0}
    assert weather_effects(0.0, None, None)["wind_eff"] == 0.0


def test_forecast_arm_source_never_reads_observed():
    src = (Path(__file__).resolve().parent / "study.py")
    if src.exists():
        t = src.read_text()
        seg = t[t.index("# FCST-ARM-BEGIN"):t.index("# FCST-ARM-END")]
        assert "r.temp" not in seg and "r.wind" not in seg and ".temp" not in seg
