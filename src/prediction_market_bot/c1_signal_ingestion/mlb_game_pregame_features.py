"""Point-in-time MLB team/starter feature builder for the EXP-037 game-market shadow (T-608).

Information cutoff: a row for a game on ``as_of_utc`` uses only games whose ``game_date`` is strictly
earlier than ``as_of_utc.date()`` and in the same season (TI-01). Short history -> None.

The confirmed starting pitcher is the T1-vs-T3 difference: the starter feature is the shrunk mean of
runs allowed by the pitcher's team in his prior starts (a schedule-derived proxy; no box scores). When
the schedule shows no probable pitcher at ``as_of`` the feature falls back to the team's own runs
allowed (full shrinkage) and ``sp_known`` records that in the row.
"""
from __future__ import annotations

import hashlib
import json
from bisect import bisect_left
from collections import defaultdict
from datetime import datetime
from typing import Optional

import pandas as pd

WINDOW = 20
DECAY = 0.95
MIN_PERIODS = 10
SP_STARTS = 8
SP_PRIOR_STARTS = 4.0
FEATURE_NAMES = ["home_rs", "home_ra", "away_rs", "away_ra", "home_wp", "away_wp",
                 "home_sp_ra", "away_sp_ra", "league_rpg"]

# Stats API abbreviation / historical code -> canonical code (Kalshi codes verified live in the runner).
CANON = {"OAK": "ATH", "ARI": "AZ", "CHW": "CWS", "WAS": "WSH", "TBR": "TB", "KCR": "KC", "SDP": "SD",
         "SFG": "SF", "LA": "LAD"}


def canon(code: Optional[str]) -> Optional[str]:
    return CANON.get(code, code) if code else code


def feature_sha(feats: dict[str, float], as_of: datetime) -> str:
    body = {k: round(float(v), 6) for k, v in sorted(feats.items())}
    body["as_of"] = as_of.isoformat()
    return hashlib.sha256(json.dumps(body, sort_keys=True).encode()).hexdigest()


class MLBGameFeatureBuilder:
    def __init__(self, games: pd.DataFrame) -> None:
        g = games[games.home_score.notna() & games.away_score.notna() & (games.status == "Final")]
        g = g.sort_values(["game_date", "start_utc"])
        self._team: dict[tuple[int, str], list] = defaultdict(list)   # (season, team) -> [(date, rs, ra, win)]
        self._sp: dict[tuple[int, int], list] = defaultdict(list)     # (season, pitcher) -> [(date, runs allowed)]
        self._league: dict[int, list] = defaultdict(list)             # season -> [(date, runs in game)]
        for r in g.itertuples():
            h, a = canon(r.home), canon(r.away)
            hs, as_ = float(r.home_score), float(r.away_score)
            self._team[(r.season, h)].append((r.game_date, hs, as_, 1.0 if hs > as_ else 0.0))
            self._team[(r.season, a)].append((r.game_date, as_, hs, 1.0 if as_ > hs else 0.0))
            self._league[r.season].append((r.game_date, hs + as_))
            if pd.notna(r.home_sp):
                self._sp[(r.season, int(r.home_sp))].append((r.game_date, as_))
            if pd.notna(r.away_sp):
                self._sp[(r.season, int(r.away_sp))].append((r.game_date, hs))
        self._dates: dict = {}

    def _prior(self, rows: list, as_of_date: str) -> list:
        key = id(rows)
        ds = self._dates.get(key)
        if ds is None:
            ds = self._dates[key] = [x[0] for x in rows]
        return rows[:bisect_left(ds, as_of_date)]

    def _team_form(self, season: int, team: str, d: str):
        hist = self._prior(self._team.get((season, team), []), d)[-WINDOW:]
        if len(hist) < MIN_PERIODS:
            return None
        w = [DECAY ** (len(hist) - 1 - i) for i in range(len(hist))]
        sw = sum(w)
        return tuple(sum(wi * h[k] for wi, h in zip(w, hist)) / sw for k in (1, 2, 3))

    def _sp_ra(self, season: int, sp: Optional[int], d: str, team_ra: float) -> float:
        if sp is None:
            return team_ra
        hist = self._prior(self._sp.get((season, int(sp)), []), d)[-SP_STARTS:]
        n = len(hist)
        return (sum(h[1] for h in hist) + SP_PRIOR_STARTS * team_ra) / (n + SP_PRIOR_STARTS)

    def row(self, home: str, away: str, as_of: datetime, home_sp: Optional[int] = None,
            away_sp: Optional[int] = None) -> Optional[dict]:
        d = as_of.date().isoformat()
        season = as_of.year
        home, away = canon(home), canon(away)
        hf, af = self._team_form(season, home, d), self._team_form(season, away, d)
        lg = self._prior(self._league.get(season, []), d)
        if hf is None or af is None or len(lg) < 50:
            return None
        feats = {"home_rs": hf[0], "home_ra": hf[1], "home_wp": hf[2],
                 "away_rs": af[0], "away_ra": af[1], "away_wp": af[2],
                 "home_sp_ra": self._sp_ra(season, home_sp, d, hf[1]),
                 "away_sp_ra": self._sp_ra(season, away_sp, d, af[1]),
                 "league_rpg": sum(x[1] for x in lg) / len(lg)}
        return {"features": feats, "sha256": feature_sha(feats, as_of),
                "sp_known": bool(home_sp is not None and away_sp is not None)}
