"""EXP-040 live feature row: EXP-039's 10 box-score features + minutes (min30, min_rank) + injury-report terms.
Port of 12_EXPLORATORY/20261012_nba_points_minutes/features.py (``minutes_inj`` arm), restricted to what a single
live (player, game) evaluation needs. Feature order is taken from the frozen artifact, not from this module."""
from __future__ import annotations

import bisect
from datetime import datetime
from typing import Any, Optional

from prediction_market_bot.c1_signal_ingestion.nba_injury_reports import norm_name
from prediction_market_bot.c1_signal_ingestion.nba_player_features import PlayerFeatureBuilder
from prediction_market_bot.c1_signal_ingestion.nba_pregame_features import et_date, et_midnight_utc

ACTIVE_DAYS = 21     # a teammate is "rotation" only if he played within this many days


def status_of(snap: dict, name: str) -> Optional[str]:
    """Exact normalized match, else unique first+last token subset (the parser can leak a team name mid-entry)."""
    n = norm_name(name)
    if n in snap:
        return snap[n]
    toks = n.split()
    if len(toks) < 2:
        return None
    hits = [v for k, v in snap.items() if toks[0] in k.split() and toks[-1] in k.split()]
    return hits[0] if len(hits) == 1 else None


class MinutesFeatureBuilder:
    def __init__(self, base: PlayerFeatureBuilder) -> None:
        self.fb = base

    def _recent(self, pid: str, team: str, cutoff: datetime):
        seq, starts = self.fb._by_player.get(pid, []), self.fb._pstarts.get(pid, [])
        hist = seq[:bisect.bisect_left(starts, cutoff)]
        if len(hist) < 10 or hist[-1][2]["team"] != team or (cutoff - hist[-1][0]).days > ACTIVE_DAYS:
            return None
        s10 = [r for _, _, r in hist[-10:]]
        return {"min10": sum(r["minutes"] for r in s10) / len(s10), "fga10": sum(r["fga"] for r in s10) / len(s10),
                "min30": sum(r["minutes"] for _, _, r in hist[-30:]) / len(hist[-30:])}

    def _mates(self, team: str, cutoff: datetime) -> dict[str, tuple[str, dict]]:
        out = {}
        for pid, starts in self.fb._pstarts.items():
            j = bisect.bisect_left(starts, cutoff)
            if j:
                t, _, r = self.fb._by_player[pid][j - 1]
                if r["team"] == team and (cutoff - t).days <= ACTIVE_DAYS:
                    st = self._recent(pid, team, cutoff)
                    if st:
                        out[pid] = (r["name"], st)
        return out

    def row(self, pid: str, name: str, team: str, opp: str, home: bool, season: int, game_start: datetime,
            as_of: datetime, snap: Optional[dict]) -> Optional[dict[str, Any]]:
        base = self.fb.row(pid, team, opp, home, season, game_start, as_of)
        if base is None:
            return None
        f = dict(base["features"])
        cutoff = min(as_of, et_midnight_utc(et_date(game_start)))
        mates = self._mates(team, cutoff)
        me = self._recent(pid, team, cutoff)
        f["min30"] = me["min30"] if me else f["min10"]
        f["min_rank"] = float(1 + sum(1 for _, st in mates.values() if st["min10"] > f["min10"]))
        f["inj_missing"] = 1.0 if snap is None else 0.0
        f["out_min"] = f["out_fga"] = f["own_quest"] = f["own_prob"] = 0.0
        if snap is not None:
            for mid, (nm, st) in mates.items():
                if mid != pid and status_of(snap, nm) in ("Out", "Doubtful"):
                    f["out_min"] += st["min10"]
                    f["out_fga"] += st["fga10"]
            s_me = status_of(snap, name)
            f["own_quest"] = 1.0 if s_me in ("Questionable", "Doubtful") else 0.0
            f["own_prob"] = 1.0 if s_me == "Probable" else 0.0
        return f
