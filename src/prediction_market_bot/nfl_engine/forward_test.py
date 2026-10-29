"""EXP-045: board v2 priced against Kalshi NFL alternate strikes, scored forward from the price archive.

Pure functions only: nothing here places an order, writes a ledger or runs on a schedule. The scoring script
(12_EXPLORATORY/nfl_engine_forward/score_exp045.py) feeds it archive rows and settled scores.

Convention (Kalshi "gt"): a strike suffix N means YES iff value > N, so the threshold is N itself.
"""
from __future__ import annotations

import collections
import math
import random
import re
from statistics import NormalDist
from typing import Iterable, Mapping, Optional

import numpy as np

from prediction_market_bot.nfl_engine.board_v2 import Library, price_board
from prediction_market_bot.quant.inference import benjamini_hochberg, cluster_bootstrap
from prediction_market_bot.quant.money import fee

_N = NormalDist()
FAMILIES = ("spread", "total", "teamtotal")
SERIES_FAMILY = {"KXNFLSPREAD": "spread", "KXNFLTOTAL": "total", "KXNFLTEAMTOTAL": "teamtotal"}
OFF_MIN = 3.0          # spread/total strikes must sit this many points off the main line
SPREAD_CAP = 0.10      # quote-sanity: ask - bid must not exceed this
LINE_STEP = 0.25       # main lines are rounded to this before pricing (board cache key)
_TEAM_N = re.compile(r"([A-Z]+?)(\d+)$")


def centre(points: Mapping[float, float]) -> Optional[float]:
    """0.5 crossing of a ladder {threshold: P(X > threshold)}, linear between neighbours; None if it never crosses."""
    hs = sorted(points)
    for a, b in zip(hs, hs[1:]):
        if points[a] >= 0.5 >= points[b] and points[a] > points[b]:
            return a + (points[a] - 0.5) / (points[a] - points[b]) * (b - a)
    return None


_MON = "JAN FEB MAR APR MAY JUN JUL AUG SEP OCT NOV DEC".split()
_ALIAS = {"LA": "LAR"}


def games_from_schedule(sched, season: int = 2026) -> dict:
    """{Kalshi event suffix: {home, away, ko, hp, ap}} for one regular season of an nflverse schedule frame.
    ko is ISO UTC (gametime is US/Eastern in nflverse); hp/ap are None until the schedule carries a score."""
    import pandas as pd
    out = {}
    for r in sched[(sched.season == season) & (sched.game_type == "REG")].itertuples():
        d = pd.Timestamp(r.gameday)
        h, a = _ALIAS.get(r.home_team, r.home_team), _ALIAS.get(r.away_team, r.away_team)
        ko = pd.Timestamp(f"{r.gameday} {r.gametime}", tz="America/New_York").tz_convert("UTC")
        has = pd.notna(r.home_score) and pd.notna(r.away_score)
        out[f"{d:%y}{_MON[d.month - 1]}{d:%d}{a}{h}"] = dict(
            home=h, away=a, ko=ko.strftime("%Y-%m-%dT%H:%M:%SZ"),
            hp=int(r.home_score) if has else None, ap=int(r.away_score) if has else None)
    return out


def iter_snapshots(rows: Iterable[Mapping]):
    """Group archive rows (file order, i.e. time order) into (run_ts, {event_suffix: {series: {strike: row}}})."""
    cur, byev = None, {}
    for r in rows:
        ser = r.get("series_ticker")
        if ser not in SERIES_FAMILY and ser != "KXNFLGAME":
            continue
        if r["run_ts"] != cur:
            if cur is not None:
                yield cur, byev
            cur, byev = r["run_ts"], {}
        ev = r["event_ticker"].split("-", 1)[1]
        byev.setdefault(ev, {}).setdefault(ser, {})[r["ticker"].rsplit("-", 1)[1]] = r
    if cur is not None:
        yield cur, byev


def _round_line(x: float) -> float:
    return round(x / LINE_STEP) * LINE_STEP


def _split(suf: str) -> Optional[tuple[str, int]]:
    m = _TEAM_N.match(suf)
    return (m.group(1), int(m.group(2))) if m else None


def _mid(r: Mapping) -> float:
    """Quote midpoint; early archive rows carry only yes_bid/yes_ask."""
    return float(r["yes_mid"]) if r.get("yes_mid") is not None else (float(r["yes_bid"]) + float(r["yes_ask"])) / 2


def _sane(r: Mapping) -> bool:
    try:
        bid, ask = float(r["yes_bid"]), float(r["yes_ask"])
    except (KeyError, TypeError, ValueError):
        return False
    return 0.0 < bid <= ask < 1.0 and ask - bid <= SPREAD_CAP + 1e-9


def ladders(rows_by_series: Mapping[str, Mapping[str, Mapping]], home: str, away: str) -> tuple[Optional[float], Optional[float]]:
    """Main spread (home-favoured positive) and main total from one snapshot's ladders (mid-price 0.5 crossings)."""
    hp: dict[float, float] = {}
    for suf, r in rows_by_series.get("KXNFLSPREAD", {}).items():
        s = _split(suf)
        if not s:
            continue
        team, n = s
        if team == home:
            hp[float(n)] = _mid(r)
        elif team == away:
            hp[-float(n)] = 1 - _mid(r)
    tp = {}
    for suf, r in rows_by_series.get("KXNFLTOTAL", {}).items():
        d = re.sub(r"\D", "", suf)
        if d:
            tp[float(int(d))] = _mid(r)
    return centre(hp), centre(tp)


class BoardCache:
    """Prices a board once per (rounded spread, rounded total) against a pinned library."""

    def __init__(self, lib: Library):
        self.lib, self._c = lib, {}

    def get(self, line: float, total: float):
        k = (_round_line(line), _round_line(total))
        if k not in self._c:
            self._c[k] = price_board(self.lib, *k)
        return self._c[k]


def engine_prob(board, fam: str, suf: str, game: Mapping, lc: float, tc: float):
    """(P_engine(YES), distance from the main line) for one strike, or None if the strike is not scoreable."""
    if fam == "spread":
        s = _split(suf)
        if not s:
            return None
        team, th = s[0], float(s[1])
        if team == game["home"]:
            return board.p_margin_ge(int(math.floor(th)) + 1), abs(th - lc)
        if team == game["away"]:
            return float(board.p[board.m < -th].sum()), abs(-th - lc)
        return None
    if fam == "total":
        d = re.sub(r"\D", "", suf)
        if not d:
            return None
        th = float(int(d))
        return board.p_total_ge(int(math.floor(th)) + 1), abs(th - tc)
    s = _split(suf)
    if not s or s[0] not in (game["home"], game["away"]):
        return None
    return board.p_team_ge(s[0] == game["home"], int(math.floor(float(s[1]))) + 1), 99.0


def outcome(fam: str, suf: str, game: Mapping, hp: int, ap: int) -> Optional[int]:
    """1 if the strike's YES side won given the final score, else 0."""
    m, t = hp - ap, hp + ap
    if fam == "spread":
        s = _split(suf)
        if not s:
            return None
        return int(m > s[1]) if s[0] == game["home"] else int(-m > s[1])
    if fam == "total":
        d = re.sub(r"\D", "", suf)
        return int(t > int(d)) if d else None
    s = _split(suf)
    if not s:
        return None
    return int((hp if s[0] == game["home"] else ap) > s[1])


def find_triggers(snapshots: Iterable[tuple[str, dict]], games: Mapping[str, Mapping], cache: BoardCache,
                  freeze_ts: str) -> list[dict]:
    """First-trigger-per-market positions.

    snapshots: iterable of (run_ts, {event_suffix: {series: {strike_suffix: archive_row}}}) in run_ts order.
    games: {event_suffix: {home, away, ko (ISO UTC)}}. Only snapshots at/after ``freeze_ts`` and before the game's
    kickoff are read, and only for games whose kickoff is itself after the freeze. YES is bought at the ask when
    P_engine - ask > exact taker fee; NO at 1 - bid when bid - P_engine > exact taker fee (the same as
    P_engine - mid > fee + half-spread). One position per market; later snapshots are ignored.
    """
    taken: set[tuple[str, str]] = set()
    out = []
    for run_ts, byev in snapshots:
        if run_ts < freeze_ts:
            continue
        for ev, fam_rows in byev.items():
            g = games.get(ev)
            if not g or g["ko"] <= freeze_ts or run_ts >= g["ko"]:
                continue
            lc, tc = ladders(fam_rows, g["home"], g["away"])
            if lc is None or tc is None:
                continue
            try:
                board = cache.get(lc, tc)
            except ValueError:
                continue
            for ser, fam in SERIES_FAMILY.items():
                for suf, r in fam_rows.get(ser, {}).items():
                    if (ev, r["ticker"]) in taken or not _sane(r):
                        continue
                    ep = engine_prob(board, fam, suf, g, lc, tc)
                    if ep is None or (fam != "teamtotal" and ep[1] < OFF_MIN):
                        continue
                    eng, bid, ask = ep[0], float(r["yes_bid"]), float(r["yes_ask"])
                    fy, fn = fee(ser, ask, 1), fee(ser, 1 - bid, 1)
                    if eng - ask > fy:
                        side, entry, f = "YES", ask, fy
                    elif bid - eng > fn:
                        side, entry, f = "NO", 1 - bid, fn
                    else:
                        continue
                    taken.add((ev, r["ticker"]))
                    out.append(dict(event=ev, fam=fam, ticker=r["ticker"], strike=suf, series=ser, side=side,
                                    entry=entry, fee=f, eng=eng, run_ts=run_ts))
    return out


def settle(positions: list[dict], games: Mapping[str, Mapping], results: Mapping[str, tuple[int, int]]) -> list[dict]:
    """Attach net P&L per contract (settlement 1 or 0, entry and exact fee) to positions whose game has a final score."""
    out = []
    for p in positions:
        res = results.get(p["event"])
        if res is None:
            continue
        y = outcome(p["fam"], p["strike"], games[p["event"]], int(res[0]), int(res[1]))
        if y is None:
            continue
        won = y if p["side"] == "YES" else 1 - y
        out.append({**p, "y": y, "pnl": won - p["entry"] - p["fee"]})
    return out


def power_n(sd_game: float, delta: float, alpha: float = 0.05, power: float = 0.8) -> int:
    """Games needed for a one-sided z-test of mean game-level net P&L > 0 to detect true mean ``delta``.
    Applies to independent games with a roughly normal mean; sd_game is the SD of per-game mean P&L."""
    return int(math.ceil(((_N.inv_cdf(1 - alpha) + _N.inv_cdf(power)) * sd_game / delta) ** 2))


def p_one_sided(by_game: Mapping[str, float], b: int = 4000, seed: int = 20261029) -> float:
    """Bootstrap p for H0: mean game-level P&L <= 0 (centred game resampling; floor 1/(b+1))."""
    v = list(by_game.values())
    n = len(v)
    if n < 2:
        return 1.0
    mean = sum(v) / n
    c = [x - mean for x in v]
    rng = random.Random(seed)
    hit = sum(1 for _ in range(b) if sum(c[rng.randrange(n)] for _ in range(n)) / n >= mean)
    return (hit + 1) / (b + 1)


def score(settled: list[dict], bh_q: float = 0.10) -> dict:
    """Per-family net P&L per contract with a game-clustered interval, one-sided p, BH across families.

    The unit of inference is the game: each game's P&L is its fired positions' mean, so a game with many strikes
    does not outweigh one with few. The headline interval is the row-weighted game-clustered bootstrap.
    """
    fams = {}
    for f in FAMILIES:
        x = [p for p in settled if p["fam"] == f]
        pc = collections.defaultdict(list)
        for p in x:
            pc[p["event"]].append(p["pnl"])
        gm = {e: sum(v) / len(v) for e, v in pc.items()}
        if x:
            m, lo, hi = cluster_bootstrap(pc, b=2000)
        else:
            m = lo = hi = float("nan")
        sd = float(np.std(list(gm.values()), ddof=1)) if len(gm) > 1 else float("nan")
        fams[f] = dict(positions=len(x), games=len(gm), mean=m, lo=lo, hi=hi, sd_game=sd,
                       p=p_one_sided(gm) if len(gm) > 1 else 1.0)
    rej = benjamini_hochberg([fams[f]["p"] for f in FAMILIES], q=bh_q)
    for f, r in zip(FAMILIES, rej):
        fams[f]["bh_reject"] = bool(r)
        fams[f]["pass"] = bool(r and fams[f]["lo"] > 0)
    return fams
