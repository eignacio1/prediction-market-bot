"""NBA player-points feature rows (EXP-039). Box-score-only, point-in-time (TI-01).

History = a player's non-DNP regular-season games with start < cutoff, where
cutoff = min(as_of, 00:00 US/Eastern of the game's ET date) -- the same rule as ``nba_pregame_features``.
Windows cross season boundaries; a player needs >= MIN_GAMES prior played games or no row is produced.
Rest / back-to-back come from the team SCHEDULE (known in advance). Opponent defence = mean points the
opponent allowed over its last 10 completed games before the cutoff (team points = sum of box-score points).
"""
from __future__ import annotations

import bisect
import hashlib
import json
from datetime import datetime
from typing import Any, Optional

from prediction_market_bot.c1_signal_ingestion.nba_pregame_features import _dt, et_date, et_midnight_utc

MIN_GAMES = 10
W_SHORT, W_LONG = 10, 30
FEATURE_NAMES = ["pts10", "pts30", "min10", "fga10", "pts_season", "gp_prior", "home", "rest", "b2b", "opp_def10"]
QUALITATIVE_FEATURES = 0


def _mean(xs: list[float]) -> float:
    return sum(xs) / len(xs)


class PlayerFeatureBuilder:
    def __init__(self, games: list[dict[str, Any]], player_stores: list[dict[str, Any]]) -> None:
        """``games``: scoreboard-store games (all seasons, completed or scheduled). ``player_stores``: the
        ``players_<season>.json`` stores. Regular season only (season_type 2)."""
        gmap = {g["game_id"]: g for g in games if g["season_type"] == 2}
        self._sched: dict[str, list[datetime]] = {}
        for g in sorted(gmap.values(), key=lambda x: (x["start_time_utc"], x["game_id"])):
            t = _dt(g["start_time_utc"])
            for side in ("home", "away"):
                self._sched.setdefault(g[side], []).append(t)
        self._by_player: dict[str, list[tuple[datetime, int, dict]]] = {}
        self._team_allowed: dict[str, list[tuple[datetime, float]]] = {}
        for store in player_stores:
            for gid, rec in sorted(store["games"].items(), key=lambda kv: (kv[1]["start_time_utc"], kv[0])):
                g = gmap.get(gid)
                if g is None:
                    continue
                t = _dt(rec["start_time_utc"])
                tot: dict[str, float] = {}
                for r in rec["rows"]:
                    tot[r["team"]] = tot.get(r["team"], 0.0) + r["points"]
                    if not r["dnp"]:
                        self._by_player.setdefault(r["player_id"], []).append((t, g["season"], r))
                for team, pts in tot.items():
                    for opp, opp_pts in tot.items():
                        if opp != team:
                            self._team_allowed.setdefault(opp, []).append((t, pts))
        for v in self._by_player.values():
            v.sort(key=lambda x: x[0])
        for v in self._team_allowed.values():
            v.sort(key=lambda x: x[0])
        self._pstarts = {k: [t for t, _, _ in v] for k, v in self._by_player.items()}
        self._tstarts = {k: [t for t, _ in v] for k, v in self._team_allowed.items()}
        # roster directory for ticker resolution: latest appearance per (team, player)
        seen: dict[tuple[str, str], tuple[datetime, dict]] = {}
        for pid, seq in self._by_player.items():
            for t, _, r in seq:
                k = (r["team"], pid)
                if k not in seen or t > seen[k][0]:
                    seen[k] = (t, r)
        self.roster: dict[str, list[dict[str, Any]]] = {}
        for (team, pid), (t, r) in seen.items():
            self.roster.setdefault(team, []).append({"player_id": pid, "name": r["name"],
                                                     "jersey": r.get("jersey", ""), "last_seen": t})

    def _rest(self, team: str, game_start: datetime) -> tuple[float, float]:
        starts = self._sched.get(team, [])
        i = bisect.bisect_left(starts, game_start)
        if i == 0:
            return 7.0, 0.0
        prev = starts[i - 1]
        rest = min((game_start - prev).total_seconds() / 86400.0, 7.0)
        return rest, 1.0 if (et_date(game_start) - et_date(prev)).days == 1 else 0.0

    def row(self, player_id: str, team: str, opp: str, home: bool, season: int, game_start: datetime,
            as_of: datetime) -> Optional[dict[str, Any]]:
        cutoff = min(as_of, et_midnight_utc(et_date(game_start)))
        seq, starts = self._by_player.get(player_id, []), self._pstarts.get(player_id, [])
        j = bisect.bisect_left(starts, min(cutoff, game_start))
        hist = seq[:j]
        if len(hist) < MIN_GAMES:
            return None
        tail = hist[-W_LONG:]
        s10 = [r for _, _, r in hist[-W_SHORT:]]
        in_season = [r["points"] for _, s, r in hist if s == season]
        pts10 = _mean([r["points"] for r in s10])
        oseq, ostarts = self._team_allowed.get(opp, []), self._tstarts.get(opp, [])
        k = bisect.bisect_left(ostarts, min(cutoff, game_start))
        allowed = [p for _, p in oseq[max(0, k - 10):k]]
        if len(allowed) < MIN_GAMES:
            return None
        rest, b2b = self._rest(team, game_start)
        feats = {"pts10": pts10, "pts30": _mean([r["points"] for _, _, r in tail]),
                 "min10": _mean([r["minutes"] for r in s10]), "fga10": _mean([r["fga"] for r in s10]),
                 "pts_season": _mean(in_season) if in_season else pts10, "gp_prior": float(len(hist)),
                 "home": 1.0 if home else 0.0, "rest": rest, "b2b": b2b, "opp_def10": _mean(allowed)}
        sha = hashlib.sha256(json.dumps(feats, sort_keys=True).encode()).hexdigest()
        return {"features": feats, "sha256": sha}
