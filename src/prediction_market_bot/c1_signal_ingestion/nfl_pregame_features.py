"""NFL pregame feature row (EXP-037 / T-608, D3).

One row per game, built strictly from information dated before the as_of date
(TI-01: source game date < as_of date). No feature timestamped after
``as_of_utc`` is ever used -- enforced here by construction and by
``tests/test_nfl_pregame_features.py``.

Features (home perspective, all recency-weighted, shrunk by the model not here):
  off_epa_h/a, def_epa_h/a   -- NFLTeamStatsStore (reused, strict game_date < as_of)
  pf_h/a, pa_h/a             -- rolling points for / against, same decay window
  rest_diff                  -- (home_rest - away_rest), clipped to [-7, 7]; a
                                schedule fact, known weeks ahead
  rest_short_h/a             -- rest < 6 days indicator

NOT used, deliberately:
  weather, roof, QB/personnel  -- nflverse extended fields are mutable rolling
                                  snapshots (look-ahead risk for history); no
                                  point-in-time source exists. Gap, not a silent drop.
  travel                       -- no venue-coordinate table built; gap.

Band effect on the row: the row is identical at T1/T2/T3 except ``as_of``.
Everything in the row is fixed by the prior week's final game, so a 48h and a
30-min as_of see the same values unless a game finished in between (a
Thursday-night result enters a Sunday row at every band). The depth the long
horizon buys here is therefore *unused* until a point-in-time injury/weather/QB
source exists; see results summary GAPS.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Optional

import pandas as pd

from prediction_market_bot.c1_signal_ingestion.nfl_team_stats_store import (
    NFLTeamStatsStore,
)

FEATURE_NAMES = [
    "off_epa_h", "def_epa_h", "off_epa_a", "def_epa_a",
    "pf_h", "pa_h", "pf_a", "pa_a",
    "rest_diff", "rest_short_h", "rest_short_a",
]
WINDOW = 8
DECAY = 0.85
MIN_PERIODS = 3


class PointsLog:
    """Per-team points for/against from completed games, strictly before as_of date."""

    def __init__(self, schedule_df: pd.DataFrame) -> None:
        done = schedule_df.dropna(subset=["home_score", "away_score"]).copy()
        done["d"] = pd.to_datetime(done["gameday"]).dt.date
        rows = []
        for r in done.itertuples():
            rows.append((r.home_team, r.d, r.home_score, r.away_score))
            rows.append((r.away_team, r.d, r.away_score, r.home_score))
        df = pd.DataFrame(rows, columns=["team", "d", "pf", "pa"]).sort_values(["team", "d"])
        self._by_team = {t: g.reset_index(drop=True) for t, g in df.groupby("team")}

    def get(self, team: str, as_of_date) -> Optional[tuple[float, float]]:
        g = self._by_team.get(team)
        if g is None:
            return None
        prior = g[g["d"] < as_of_date].tail(WINDOW)
        if len(prior) < MIN_PERIODS:
            return None
        n = len(prior)
        w = pd.Series([DECAY ** (n - 1 - i) for i in range(n)], index=prior.index)
        return (
            float((prior["pf"] * w).sum() / w.sum()),
            float((prior["pa"] * w).sum() / w.sum()),
        )


class NFLPregameFeatureBuilder:
    def __init__(self, team_stats_df: pd.DataFrame, schedule_df: pd.DataFrame) -> None:
        self.store = NFLTeamStatsStore.build_from_team_stats(team_stats_df, schedule_df)
        self.points = PointsLog(schedule_df)

    def row(
        self,
        home: str,
        away: str,
        as_of_utc: datetime,
        home_rest: Optional[float] = None,
        away_rest: Optional[float] = None,
    ) -> Optional[dict]:
        """Feature dict (+ sha) or None if any team lacks history before as_of."""
        if as_of_utc.tzinfo is None:
            raise ValueError("as_of_utc must be timezone-aware")
        as_of_date = as_of_utc.astimezone(timezone.utc).date()
        d = as_of_date.isoformat()
        vals: dict[str, float] = {}
        for side, team in (("h", home), ("a", away)):
            oe = self.store.get_off_epa(team, d, WINDOW, MIN_PERIODS, DECAY)
            de = self.store.get_def_epa_allowed(team, d, WINDOW, MIN_PERIODS, DECAY)
            pts = self.points.get(team, as_of_date)
            if oe is None or de is None or pts is None:
                return None
            vals[f"off_epa_{side}"], vals[f"def_epa_{side}"] = oe, de
            vals[f"pf_{side}"], vals[f"pa_{side}"] = pts
        hr = 7.0 if home_rest is None or pd.isna(home_rest) else float(home_rest)
        ar = 7.0 if away_rest is None or pd.isna(away_rest) else float(away_rest)
        vals["rest_diff"] = max(-7.0, min(7.0, hr - ar))
        vals["rest_short_h"] = 1.0 if hr < 6 else 0.0
        vals["rest_short_a"] = 1.0 if ar < 6 else 0.0
        return {"features": vals, "sha256": feature_sha(vals, as_of_utc)}


def feature_sha(vals: dict[str, float], as_of_utc: datetime) -> str:
    payload = json.dumps(
        {k: round(float(vals[k]), 9) for k in FEATURE_NAMES} | {"as_of": as_of_utc.isoformat()},
        sort_keys=True,
    )
    return hashlib.sha256(payload.encode()).hexdigest()
