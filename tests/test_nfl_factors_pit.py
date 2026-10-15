"""Point-in-time + interface checks for the EXPLORATORY NFL factor builder and rate layer (W75.2)."""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "12_EXPLORATORY" / "nfl_engine"))
import factors as F  # noqa: E402
import rate_layer as R  # noqa: E402


def _plays():
    rows = []
    for i in range(200):
        rows.append(dict(season=2024, kickoff=pd.Timestamp("2024-09-08", tz="UTC") + pd.Timedelta(days=7 * (i % 10)),
                         off="A" if i % 2 else "B", dfn="B" if i % 2 else "A", shell="COVER_3" if i % 3 else "COVER_2",
                         pers="11", motion="S", epa=0.1 * (i % 5 - 2), success=float(i % 2), game_idx=i % 10))
    return pd.DataFrame(rows)


def test_pit_excludes_future_and_post_game_lag():
    p = _plays()
    asof = pd.Timestamp("2024-09-15 02:00", tz="UTC")  # first game kicked 09-08 00:00 -> usable; 09-15 00:00 + 4h > asof
    u = F.pit(p, asof)
    assert (u.kickoff + F.POST_GAME_LAG <= asof).all() and len(u) < len(p)


def test_factor_values_unchanged_by_future_rows():
    p = _plays()
    asof = pd.Timestamp("2024-10-01", tz="UTC")
    a = F.factor_values(p, asof, F.COVERAGE_X_PERSONNEL_NOMOTION)
    fut = p.copy()
    fut.loc[fut.kickoff > asof, "epa"] = 99.0
    b = F.factor_values(fut, asof, F.COVERAGE_X_PERSONNEL_NOMOTION)
    assert np.allclose(a.epa_shrunk, b.epa_shrunk) and np.allclose(a.share_shrunk, b.share_shrunk)


class _Z:
    name = "z"

    def points(self, as_of, offense, defense):
        return 1.0 if offense == "H" else None


def test_rate_layer_none_is_league_average_and_beta_scales():
    gi = R.GameInputs(pd.Timestamp("2024-09-01", tz="UTC"), "H", "A", 24.0, 21.0)
    r = R.rates(gi, [_Z()], {"z": 2.0})
    assert r.mu_home == 26.0 and r.mu_away == 21.0 and r.populated["z"] == (1.0, None)
    assert R.rates(gi, [_Z()], {}).mu_home == 24.0
