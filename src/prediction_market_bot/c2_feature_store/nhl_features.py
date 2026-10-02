"""C2 — NHL pregame features (T-607 / EXP-036).

Every feature is computed from finished games only, and a game is *available* at
``as_of_utc`` only if ``start_time_utc + RESULT_LAG <= as_of_utc`` (event-time cutoff:
a stored ``fetched_at_utc`` of a backfill is today and cannot gate history). The
largest input timestamp used is returned as ``input_max_ts`` and ``assert_cutoff`` raises
if it ever exceeds ``as_of_utc`` — the cutoff is enforced in code, not by convention.

Starter handling by band: T1 uses the PROJECTED starter (last game's starter, ``starter_source
= "projected_last_start"``); T3 may pass a confirmed id (``"confirmed"``). Unknown -> team
average goalie prior, flagged ``goalie_known = 0``.
"""
from __future__ import annotations

import hashlib
import json
from bisect import bisect_right
from datetime import datetime, timedelta, timezone
from typing import Optional

RESULT_LAG = timedelta(hours=3)  # a game is treated as final 3h after puck drop
HALF_LIFE_GAMES = 12.0
LEAGUE_GF = 3.05          # prior goals/team/game (re-fit from training data in the model)
LEAGUE_SVP = 0.905
GOALIE_PRIOR_SA = 400.0    # shrinkage weight (shots) toward league save%
FEATURE_NAMES = [
    "gf_ew", "ga_ew", "sf_ew", "sa_ew", "pp_ew", "pim_ew", "gf_l10", "ga_l10", "n_games",
    "rest_days", "b2b", "games_7d", "road_streak", "goalie_svp", "goalie_known",
]


def parse_ts(s: str) -> datetime:
    return datetime.fromisoformat(s.replace("Z", "+00:00")).astimezone(timezone.utc)


def assert_cutoff(input_max_ts: Optional[datetime], as_of_utc: datetime) -> None:
    if input_max_ts is not None and input_max_ts > as_of_utc:
        raise ValueError(f"information cutoff violated: input {input_max_ts} > as_of {as_of_utc}")


class NhlFeatureStore:
    def __init__(self, games: list[dict]):
        """``games``: finished-game rows from ``nhl_ingest.parse_game_row``."""
        self._by_team: dict[str, list[tuple[datetime, dict, bool]]] = {}
        self._goalie: dict[int, list[tuple[datetime, int, int]]] = {}
        for g in sorted(games, key=lambda r: (r["start_time_utc"], r["game_id"])):
            t = parse_ts(g["start_time_utc"])
            self._by_team.setdefault(g["home"], []).append((t, g, True))
            self._by_team.setdefault(g["away"], []).append((t, g, False))
            for side in ("home", "away"):
                for gid in g[f"{side}_goalies_used"]:
                    pass
                sid = g.get(f"{side}_starter_id")
                if sid is not None:
                    self._goalie.setdefault(sid, []).append(
                        (t, int(g[f"{side}_goalie_saves"]), int(g[f"{side}_goalie_sa"])))
        self._times = {k: [x[0] for x in v] for k, v in self._by_team.items()}
        self._gtimes = {k: [x[0] for x in v] for k, v in self._goalie.items()}

    # --------------------------------------------------------------- helpers
    def _prior(self, team: str, as_of: datetime):
        v = self._by_team.get(team, [])
        i = bisect_right(self._times.get(team, []), as_of - RESULT_LAG)
        return v[:i]

    def last_starter(self, team: str, as_of_utc: datetime) -> Optional[int]:
        for _, g, is_home in reversed(self._prior(team, as_of_utc)):
            sid = g["home_starter_id" if is_home else "away_starter_id"]
            if sid is not None:
                return sid
        return None

    def goalie_svp(self, goalie_id: Optional[int], as_of_utc: datetime) -> tuple[float, int, Optional[datetime]]:
        if goalie_id is None or goalie_id not in self._goalie:
            return LEAGUE_SVP, 0, None
        i = bisect_right(self._gtimes[goalie_id], as_of_utc - RESULT_LAG)
        rows = self._goalie[goalie_id][:i]
        if not rows:
            return LEAGUE_SVP, 0, None
        sv = sum(r[1] for r in rows[-60:])
        sa = sum(r[2] for r in rows[-60:])
        svp = (sv + LEAGUE_SVP * GOALIE_PRIOR_SA) / (sa + GOALIE_PRIOR_SA)
        return svp, 1, rows[-1][0]

    # --------------------------------------------------------------- features
    def team_features(self, team: str, as_of_utc: datetime, game_start_utc: datetime,
                      goalie_id: Optional[int] = None) -> tuple[dict, Optional[datetime]]:
        prior = self._prior(team, as_of_utc)
        decay = 0.5 ** (1.0 / HALF_LIFE_GAMES)
        w = tot = 0.0
        acc = {k: 0.0 for k in ("gf", "ga", "sf", "sa", "pp", "pim")}
        for age, (t, g, is_home) in enumerate(reversed(prior[-60:])):
            me, op = ("home", "away") if is_home else ("away", "home")
            wt = decay ** age
            w += wt
            acc["gf"] += wt * g[f"{me}_score_ex_so"]
            acc["ga"] += wt * g[f"{op}_score_ex_so"]
            acc["sf"] += wt * (g.get(f"{me}_sog") or 0)
            acc["sa"] += wt * (g.get(f"{op}_sog") or 0)
            acc["pp"] += wt * g[f"{me}_pp_goals"]
            acc["pim"] += wt * g[f"{me}_pim"]
        n = len(prior)
        # shrink toward league prior with 5 pseudo-games
        k0 = 5.0
        def sh(x, prior_val):
            return (x + k0 * prior_val) / (w + k0)
        l10 = prior[-10:]
        gf10 = [g[("home" if h else "away") + "_score_ex_so"] for _, g, h in l10]
        ga10 = [g[("away" if h else "home") + "_score_ex_so"] for _, g, h in l10]
        last_t = prior[-1][0] if prior else None
        rest = (game_start_utc - last_t).total_seconds() / 86400.0 if last_t else 7.0
        road = 0
        for _, _g, h in reversed(prior):
            if h:
                break
            road += 1
        svp, known, gts = self.goalie_svp(goalie_id, as_of_utc)
        f = {
            "gf_ew": sh(acc["gf"], LEAGUE_GF), "ga_ew": sh(acc["ga"], LEAGUE_GF),
            "sf_ew": sh(acc["sf"], 30.0), "sa_ew": sh(acc["sa"], 30.0),
            "pp_ew": sh(acc["pp"], 0.55), "pim_ew": sh(acc["pim"], 8.0),
            "gf_l10": (sum(gf10) + 2 * LEAGUE_GF) / (len(gf10) + 2),
            "ga_l10": (sum(ga10) + 2 * LEAGUE_GF) / (len(ga10) + 2),
            "n_games": float(min(n, 60)), "rest_days": min(rest, 7.0),
            "b2b": 1.0 if rest < 1.5 else 0.0,
            "games_7d": float(sum(1 for t, _, _ in prior if game_start_utc - t <= timedelta(days=7))),
            "road_streak": float(min(road, 6)), "goalie_svp": svp, "goalie_known": float(known),
        }
        ts = [t for t in (last_t, gts) if t is not None]
        return f, (max(ts) + RESULT_LAG if ts else None)

    def game_features(self, home: str, away: str, game_start_utc: datetime, as_of_utc: datetime,
                      home_goalie: Optional[int] = None, away_goalie: Optional[int] = None,
                      confirmed: bool = False) -> dict:
        """Feature row for one game. ``input_max_ts`` is the latest *availability* time used."""
        if home_goalie is None:
            home_goalie = self.last_starter(home, as_of_utc)
        if away_goalie is None:
            away_goalie = self.last_starter(away, as_of_utc)
        hf, ht = self.team_features(home, as_of_utc, game_start_utc, home_goalie)
        af, at = self.team_features(away, as_of_utc, game_start_utc, away_goalie)
        mx = max([t for t in (ht, at) if t is not None], default=None)
        assert_cutoff(mx, as_of_utc)
        row = {"home": home, "away": away, "start_time_utc": game_start_utc.isoformat(),
               "as_of_utc": as_of_utc.isoformat(),
               "starter_source": "confirmed" if confirmed else "projected_last_start",
               "home_goalie_id": home_goalie, "away_goalie_id": away_goalie,
               "input_max_ts": mx.isoformat() if mx else None,
               **{f"h_{k}": hf[k] for k in FEATURE_NAMES}, **{f"a_{k}": af[k] for k in FEATURE_NAMES}}
        return row


def feature_row_sha256(row: dict) -> str:
    return hashlib.sha256(json.dumps(row, sort_keys=True, default=str).encode()).hexdigest()
