"""NBA pregame feature rows (EXP-038). Scores-only, point-in-time (TI-01).

History = completed regular-season games with start < cutoff, where
cutoff = min(as_of, 00:00 US/Eastern of the game's ET date). Rest / back-to-back come from the SCHEDULE
(known in advance), not from outcomes. Windows cross season boundaries so early-season rows still carry
information; a team needs >= MIN_GAMES prior games or no row is produced.
"""
from __future__ import annotations

import bisect
import hashlib
import json
from datetime import datetime, timedelta, timezone
from typing import Any, Optional
from zoneinfo import ZoneInfo

ET = ZoneInfo("America/New_York")
MIN_GAMES = 10
W_SHORT, W_LONG = 10, 30
FEATURE_NAMES = [
    "h_pf10", "h_pa10", "a_pf10", "a_pa10", "h_pf30", "h_pa30", "a_pf30", "a_pa30",
    "h_rest", "a_rest", "h_b2b", "a_b2b", "h_3in4", "a_3in4",
]


def _dt(s: str) -> datetime:
    return datetime.fromisoformat(s.replace("Z", "+00:00"))


def et_date(start_utc: datetime):
    return start_utc.astimezone(ET).date()


def et_midnight_utc(d) -> datetime:
    return datetime(d.year, d.month, d.day, tzinfo=ET).astimezone(timezone.utc)


class NBAFeatureBuilder:
    def __init__(self, games: list[dict[str, Any]]) -> None:
        """``games``: every known regular-season game (completed or scheduled) from nba_ingest."""
        self._by_team: dict[str, list[tuple[datetime, dict]]] = {}
        for g in sorted(games, key=lambda g: (g["start_time_utc"], g["game_id"])):
            if g["season_type"] != 2:
                continue
            t = _dt(g["start_time_utc"])
            for side in ("home", "away"):
                self._by_team.setdefault(g[side], []).append((t, g))
        self._starts = {k: [t for t, _ in v] for k, v in self._by_team.items()}

    def _team(self, team: str, game_start: datetime, cutoff: datetime) -> Optional[dict[str, float]]:
        seq, starts = self._by_team.get(team, []), self._starts.get(team, [])
        i = bisect.bisect_left(starts, game_start)            # schedule: games strictly before this one
        sched_prev = [t for t in starts[max(0, i - 3):i]]
        hist = [(t, g) for t, g in seq[:i] if t < cutoff and g["completed"] and g["home_score"] is not None]
        if len(hist) < MIN_GAMES:
            return None

        def pfpa(rows):
            pf = [g["home_score"] if g["home"] == team else g["away_score"] for _, g in rows]
            pa = [g["away_score"] if g["home"] == team else g["home_score"] for _, g in rows]
            return sum(pf) / len(pf), sum(pa) / len(pa)

        pf10, pa10 = pfpa(hist[-W_SHORT:])
        pf30, pa30 = pfpa(hist[-W_LONG:])
        gd = et_date(game_start)
        days = [(gd - et_date(t)).days for t in sched_prev]    # most recent last
        rest = min(days[-1], 7) if days else 7
        return {"pf10": pf10, "pa10": pa10, "pf30": pf30, "pa30": pa30, "rest": float(rest),
                "b2b": float(bool(days) and days[-1] == 1),
                "g3in4": float(len(days) >= 2 and days[-2] <= 3)}

    def row(self, home: str, away: str, game_start: datetime, as_of: datetime) -> Optional[dict]:
        cutoff = min(as_of, et_midnight_utc(et_date(game_start)))
        h, a = self._team(home, game_start, cutoff), self._team(away, game_start, cutoff)
        if h is None or a is None:
            return None
        f = {"h_pf10": h["pf10"], "h_pa10": h["pa10"], "a_pf10": a["pf10"], "a_pa10": a["pa10"],
             "h_pf30": h["pf30"], "h_pa30": h["pa30"], "a_pf30": a["pf30"], "a_pa30": a["pa30"],
             "h_rest": h["rest"], "a_rest": a["rest"], "h_b2b": h["b2b"], "a_b2b": a["b2b"],
             "h_3in4": h["g3in4"], "a_3in4": a["g3in4"]}
        sha = hashlib.sha256(json.dumps(f, sort_keys=True).encode()).hexdigest()
        return {"features": f, "sha256": sha}
