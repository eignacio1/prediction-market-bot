"""EXP-047 (W109.3, B-070): NBA player rebounds / assists / threes priced from the NBA engine's own game draws.

Ticker -> game + player -> engine_v2 draws (fixed league constants, walk-forward shrunk team ratings) ->
``nba_engine.props`` split -> P(stat >= n). EVALUATE-AND-LOG only; nothing here can place an order. A player not in
the team's prior rotation, an unknown/ambiguous name, or an unscheduled game yields no forecast -- never a guess.
Frozen constants (hashed into ``model_sha256``): any change is a new challenger with its own pre-registration."""
from __future__ import annotations

import collections
import hashlib
import json
import re
from datetime import datetime
from typing import Any, Mapping, Optional

import numpy as np

from prediction_market_bot.c1_signal_ingestion.nba_ingest import kalshi_code
from prediction_market_bot.nba_engine import engine_v2 as E2
from prediction_market_bot.nba_engine import props as P
from prediction_market_bot.pregame_shadow.contract import PregameForecast
from prediction_market_bot.pregame_shadow.nba_forecaster import _MON, KALSHI_CODES
from prediction_market_bot.pregame_shadow.nba_player_points_forecaster import _PLAYER, _initial, _norm_surname

SPORT = "NBAENG"
SERIES = {"KXNBAREB": ("NBA_PLAYER_REBOUNDS", "rebounds"), "KXNBAAST": ("NBA_PLAYER_ASSISTS", "assists"),
          "KXNBA3PT": ("NBA_PLAYER_THREES", "threes")}
LEAGUE = 114.0
PRIOR_GAMES, MIN_PRIOR_GAMES, MIN_MPG, ROTATION, DRAWS = 8, 4, 10.0, 10, 4000
PARAMS = E2.V2Params(hca=2.0, tbias=0.0, sd_margin=13.0, sd_total=19.0)
MODEL_ID = "nba_engine_v2_props_w109_3"
_CONSTANTS = dict(params=[2.0, 0.0, 13.0, 19.0], league=LEAGUE, prior_games=PRIOR_GAMES, min_prior=MIN_PRIOR_GAMES,
                  min_mpg=MIN_MPG, rotation=ROTATION, draws=DRAWS, beta=P.DEFAULT_BETA, r=P.DEFAULT_R,
                  rest=P.DEFAULT_REST, conc=P.DEFAULT_CONC)
MODEL_SHA256 = hashlib.sha256(json.dumps(_CONSTANTS, sort_keys=True).encode()).hexdigest()
_EVENT = re.compile(r"^(KXNBA(?:REB|AST|3PT))-(\d{2})([A-Z]{3})(\d{2})([A-Z]{6})$")


def parse_market_ticker(t: str) -> Optional[dict]:
    """KXNBAREB-26NOV09NOPGSW-NOPDQUEEN22-10 -> series, game date, away/home, player (team, initial, surname), n."""
    parts = t.split("-")
    if len(parts) != 4 or not parts[3].isdigit():
        return None
    m = _EVENT.match("-".join(parts[:2]))
    pm = _PLAYER.match(parts[2])
    if not m or pm is None or m.group(3) not in _MON:
        return None
    away, home = m.group(5)[:3], m.group(5)[3:]
    if away not in KALSHI_CODES or home not in KALSHI_CODES or pm.group(1) not in (away, home):
        return None
    mt, stat = SERIES[m.group(1)]
    return {"series": m.group(1), "market_type": mt, "stat": stat, "event_ticker": "-".join(parts[:2]),
            "game_date": f"20{m.group(2)}-{_MON[m.group(3)]:02d}-{m.group(4)}", "away": away, "home": home,
            "team": pm.group(1), "initial": pm.group(2), "surname": pm.group(3), "n": int(parts[3])}


def parse_box(raw: Mapping[str, Any]):
    """ESPN {event_id: {date, box (summary boxscore), hdr ['ABR:home|away:score']}} -> (games, player_rows)."""
    games, pl = {}, collections.defaultdict(list)
    for gid, g in raw.items():
        teams = {}
        for t in g["box"]["players"]:
            code = kalshi_code(t["team"]["abbreviation"])
            ks = t["statistics"][0]["keys"]
            ix = {k: i for i, k in enumerate(ks)}
            rows = []
            for a in t["statistics"][0]["athletes"]:
                st = a.get("stats") or []
                if not st or a.get("didNotPlay"):
                    continue
                try:
                    mins = float(st[ix["minutes"]])
                except ValueError:
                    continue
                if mins <= 0:
                    continue
                rows.append(dict(name=a["athlete"]["displayName"], min=mins, points=float(st[ix["points"]]),
                                 rebounds=float(st[ix["rebounds"]]), assists=float(st[ix["assists"]]),
                                 threes=float(st[ix["threePointFieldGoalsMade-threePointFieldGoalsAttempted"]].split("-")[0])))
            teams[code] = rows
        hdr = {h.split(":")[0]: (h.split(":")[1], float(h.split(":")[2])) for h in g["hdr"]}
        pts = {kalshi_code(k): v[1] for k, v in hdr.items()}
        home = [kalshi_code(k) for k, v in hdr.items() if v[0] == "home"][0]
        games[gid] = dict(date=g["date"], home=home, away=[c for c in teams if c != home][0], pts=pts, teams=teams)
        for code, rows in teams.items():
            for r in rows:
                pl[(code, r["name"])].append((g["date"], r))
    return games, pl


class NBAEngineProps:
    """Holds settled-game history; prices one scheduled game at a time (draws cached per game)."""
    sport = SPORT

    def __init__(self, games: dict, player_rows: dict, tips: Mapping[tuple, datetime]) -> None:
        self.games, self.pl, self.tips = games, player_rows, tips      # tips: (ET date, frozenset{a,b}) -> tip UTC
        self._draws: dict = {}
        self._split: dict = {}

    def tip_for(self, parsed: dict) -> Optional[datetime]:
        return self.tips.get((parsed["game_date"], frozenset((parsed["home"], parsed["away"]))))

    def kickoff_for_event(self, event_ticker: str):
        m = _EVENT.match(event_ticker)
        if not m or m.group(3) not in _MON:
            return None
        away, home = m.group(5)[:3], m.group(5)[3:]
        t = self.tips.get((f"20{m.group(2)}-{_MON[m.group(3)]:02d}-{m.group(4)}", frozenset((home, away))))
        return (t, "espn_scoreboard_start_time") if t else None

    def _ratings(self, before: str):
        f, a = collections.defaultdict(list), collections.defaultdict(list)
        for g in self.games.values():
            if g["date"] < before:
                for t in (g["home"], g["away"]):
                    o = g["away"] if t == g["home"] else g["home"]
                    f[t].append(g["pts"][t]); a[t].append(g["pts"][o])
        sh = lambda v: (sum(v) + PRIOR_GAMES * LEAGUE) / (len(v) + PRIOR_GAMES)
        return (lambda t: sh(f[t])), (lambda t: sh(a[t]))

    def roster(self, team: str, before: str) -> list:
        out = []
        for (tm, name), rows in self.pl.items():
            prior = [r for d, r in rows if d < before]
            if tm == team and len(prior) >= MIN_PRIOR_GAMES and np.mean([r["min"] for r in prior]) >= MIN_MPG:
                out.append((float(np.mean([r["min"] for r in prior])), name,
                            {s: float(np.mean([r[s] for r in prior])) for s in P.STATS}))
        out.sort(key=lambda x: (-x[0], x[1]))
        return out[:ROTATION]

    def _game_draws(self, p: dict):
        key = (p["game_date"], p["home"], p["away"])
        if key not in self._draws:
            af, aa = self._ratings(p["game_date"])
            mu_h, mu_a = (af(p["home"]) + aa(p["away"])) / 2, (af(p["away"]) + aa(p["home"])) / 2
            mm, tt = E2.game_means(PARAMS, mu_h, mu_a)
            seed = int(hashlib.sha256("|".join(key).encode()).hexdigest()[:8], 16) % 100003
            self._draws[key] = E2.simulate(PARAMS, mm, tt, DRAWS, seed=seed)
        return self._draws[key]

    def forecast(self, market_ticker: str, as_of_utc: datetime) -> Optional[PregameForecast]:
        p = parse_market_ticker(market_ticker)
        if p is None or self.tip_for(p) is None:
            return None
        ros = self.roster(p["team"], p["game_date"])
        hits = [i for i, (_, n, _) in enumerate(ros) if _initial(n) == p["initial"] and _norm_surname(n) == p["surname"]]
        if len(hits) != 1:
            return None
        h, a = self._game_draws(p)
        pts = h if p["team"] == p["home"] else a
        names = [n for _, n, _ in ros]
        key = (p["game_date"], p["home"], p["away"], p["team"], p["stat"])
        if key not in self._split:
            R = P.TeamRoster(tuple(names), {s: [r[2][s] for r in ros] for s in P.STATS}, float(pts.mean()))
            seed = int(hashlib.sha256("|".join(key).encode()).hexdigest()[:8], 16) % 99991
            self._split[key] = P.player_draws(pts, R, p["stat"], np.random.default_rng(seed))[0]
        d = self._split[key]
        py = P.strike_probs(d[:, hits[0]], [p["n"]])[p["n"]]
        py = min(max(py, 1e-4), 1 - 1e-4)
        row_sha = hashlib.sha256(json.dumps([ros[hits[0]][2], p["game_date"], len(self.games)], sort_keys=True).encode()).hexdigest()
        return PregameForecast(SPORT, p["market_type"], p["event_ticker"], market_ticker, py, as_of_utc,
                               MODEL_ID, MODEL_SHA256, row_sha)
