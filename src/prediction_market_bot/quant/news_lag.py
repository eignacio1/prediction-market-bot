"""News-lag event study (W107.2 / B-060): does Kalshi's line lag public news?

Pure functions, no I/O against live ledgers. Three layers:

1. ``parse_injury_text`` -- NBA official injury-report PDF text (pypdf *plain* mode, one token per line) into rows
   (game_date, tip_et, matchup, side, team, player, status, g_league).  Plain mode keeps matchup -> team -> players in
   reading order, which the layout mode scrambles.
2. ``report_events`` -- diff two consecutive reports into news events per (game, team): a status change that moves a
   team's availability.  ``sign`` is -1 for worse-for-the-team news, +1 for better.
3. ``signed_profile`` -- the event study: signed price move (in the news direction) over fixed horizons after the news,
   plus the pre-news window (leak check) and a cluster-by-game bootstrap interval.

When it applies: price snapshots at a fixed cadence (the archive's is ~20 min); it can show a lag of tens of minutes
and nothing shorter.  When it does not: news that is not in the official report (beat-writer tweets, warm-up
scratches), and any lag under one snapshot interval -- that is invisible here by construction.
"""
from __future__ import annotations

import bisect
import random
import re
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Optional, Sequence
from zoneinfo import ZoneInfo

ET = ZoneInfo("America/New_York")
STATUSES = ("Out", "Doubtful", "Questionable", "Probable", "Available")
# availability cost of a status: how much worse the team is for a player carrying it (0 = fully available)
SEVERITY = {"Out": 1.0, "Doubtful": 0.75, "Questionable": 0.4, "Probable": 0.1, "Available": 0.0}
SUFFIX = {"Jr.", "Sr.", "II", "III", "IV", "V"}
TEAMS = [
    "Atlanta Hawks", "Boston Celtics", "Brooklyn Nets", "Charlotte Hornets", "Chicago Bulls", "Cleveland Cavaliers",
    "Dallas Mavericks", "Denver Nuggets", "Detroit Pistons", "Golden State Warriors", "Houston Rockets",
    "Indiana Pacers", "LA Clippers", "Los Angeles Clippers", "Los Angeles Lakers", "Memphis Grizzlies", "Miami Heat",
    "Milwaukee Bucks", "Minnesota Timberwolves", "New Orleans Pelicans", "New York Knicks", "Oklahoma City Thunder",
    "Orlando Magic", "Philadelphia 76ers", "Phoenix Suns", "Portland Trail Blazers", "Sacramento Kings",
    "San Antonio Spurs", "Toronto Raptors", "Utah Jazz", "Washington Wizards",
]
_TEAM_TOK = {tuple(t.split()): t for t in TEAMS}
_MAXTEAM = max(len(k) for k in _TEAM_TOK)
_MATCHUP = re.compile(r"^[A-Z]{2,4}@[A-Z]{2,4}$")
_DATE = re.compile(r"^\d{2}/\d{2}/\d{4}$")
_TIME = re.compile(r"^\d{2}:\d{2}$")


@dataclass(frozen=True)
class Row:
    game_date: str          # ISO date of the game (ET)
    tip_et: str             # "HH:MM" 24h ET
    matchup: str            # AWAY@HOME
    side: str               # "away" | "home"
    team: str
    player: str
    status: str
    g_league: bool          # two-way / G League assignment -- not news about the NBA rotation


def _team_at(toks, i):
    for L in range(_MAXTEAM, 1, -1):
        key = tuple(toks[i:i + L])
        if key in _TEAM_TOK:
            return L, _TEAM_TOK[key]
    return None


def _players(block: list) -> list:
    """Segment a team block into (player, status, reason).  Anchor = a token ending in ',' followed within 3 tokens by
    a status word ("Last, First [Suffix] Status").  Reasons may contain commas ("Lower Back, Injury Management"); those
    commas are not followed by a status within 3 tokens, so they are not anchors."""
    anchors = []
    for c, t in enumerate(block):
        if t.endswith(",") and len(t) > 1:
            for k in (1, 2, 3):
                if c + k < len(block) and block[c + k] in STATUSES:
                    anchors.append((c, c + k))
                    break
    out = []
    for n, (c, st) in enumerate(anchors):
        last = block[c - 1] + " " + block[c] if block[c] in {x + "," for x in SUFFIX} and c > 0 else block[c]
        name = last + " " + " ".join(block[c + 1:st])
        end = anchors[n + 1][0] if n + 1 < len(anchors) else len(block)
        if n + 1 < len(anchors) and block[anchors[n + 1][0]] in {x + "," for x in SUFFIX}:
            end -= 1
        out.append((name, block[st], " ".join(block[st + 1:end])))
    return out


def parse_injury_text(text: str) -> list[Row]:
    """Parse one report's plain-mode text (one token per line or whitespace-separated)."""
    toks = text.split()
    rows: list[Row] = []
    date = tip = matchup = team = side = None
    teams_seen = 0
    block: list = []

    def flush():
        nonlocal block
        if team and matchup and block:
            for name, status, reason in _players(block):
                rows.append(Row(date, tip, matchup, side, team, name, status, "League" in reason and "G" in reason.split()))
        block = []

    i, n = 0, len(toks)
    while i < n:
        t = toks[i]
        if t == "Injury" and i + 1 < n and toks[i + 1] == "Report:":
            j = i
            while j < n and toks[j] != "of":
                j += 1
            i = j + 2
            continue
        if toks[i:i + 10] == ["Game", "Date", "Game", "Time", "Matchup", "Team", "Player", "Name", "Current", "Status"]:
            i += 11 if toks[i + 10:i + 11] == ["Reason"] else 10
            continue
        if _DATE.match(t):
            flush(); team = None
            date = f"{t[6:]}-{t[:2]}-{t[3:5]}"; i += 1; continue
        if _TIME.match(t) and i + 1 < n and toks[i + 1] == "(ET)":
            flush(); tip = t; i += 2; continue
        if _MATCHUP.match(t):
            flush(); matchup, team, side, teams_seen = t, None, None, 0; i += 1; continue
        hit = _team_at(toks, i)
        if hit:
            flush()
            team = hit[1]; side = "away" if teams_seen == 0 else "home"; teams_seen += 1
            i += hit[0]; continue
        if toks[i:i + 3] == ["NOT", "YET", "SUBMITTED"]:
            flush(); i += 3; continue
        block.append(t); i += 1
    flush()
    return rows


# --------------------------------------------------------------------------------------------------------------- events
@dataclass(frozen=True)
class Event:
    report_utc: datetime        # nominal stamp of the report that carried the news
    game_date: str
    matchup: str
    team: str
    side: str
    tip_utc: datetime
    kind: str                   # to_out | to_questionable | q_to_active | out_to_active
    sign: int                   # -1 worse for the team, +1 better
    player: str


def tip_utc(game_date: str, tip_et: str) -> datetime:
    h, m = tip_et.split(":")
    d = datetime.fromisoformat(game_date).replace(hour=int(h), minute=int(m), tzinfo=ET)
    if d.hour < 12 and int(h) < 12:       # report prints 12-hour clock without AM/PM: games are evening ET
        d = d.replace(hour=int(h) + 12)
    return d.astimezone(timezone.utc)


def _kind(old: Optional[str], new: str) -> Optional[tuple[str, int]]:
    so, sn = SEVERITY.get(old, None) if old else None, SEVERITY[new]
    if old is None:
        return None
    if so == sn:
        return None
    if sn > so:
        return ("to_out", -1) if new in ("Out", "Doubtful") else ("to_questionable", -1)
    return ("out_to_active", +1) if old in ("Out", "Doubtful") else ("q_to_active", +1)


def report_events(prev: Sequence[Row], cur: Sequence[Row], report_utc: datetime) -> list[Event]:
    """News = a player's status moved between two consecutive reports for a game both reports carry.

    A player absent from ``prev`` is not an event (the team block may simply not have been submitted yet); the first
    submission of a team's list is therefore not scored here -- it is a different, bigger event class."""
    base = {(r.game_date, r.matchup, r.team, r.player): r for r in prev if not r.g_league}
    out = []
    for r in cur:
        if r.g_league:
            continue
        old = base.get((r.game_date, r.matchup, r.team, r.player))
        if old is None:
            continue
        k = _kind(old.status, r.status)
        if k:
            out.append(Event(report_utc, r.game_date, r.matchup, r.team, r.side, tip_utc(r.game_date, r.tip_et),
                             k[0], k[1], r.player))
    return out


# --------------------------------------------------------------------------------------------------- event-study maths
Series = Sequence[tuple[datetime, float]]      # sorted (ts, price) with price in [0, 1]


def price_at(series: Series, t: datetime, side: str = "le", tol: timedelta = timedelta(minutes=25)):
    """Nearest snapshot at-or-before ('le') / at-or-after ('ge') t within tol.  Returns (ts, price) or None."""
    ts = [s[0] for s in series]
    if side == "le":
        k = bisect.bisect_right(ts, t) - 1
        if k >= 0 and t - ts[k] <= tol:
            return series[k]
    else:
        k = bisect.bisect_left(ts, t)
        if k < len(ts) and ts[k] - t <= tol:
            return series[k]
    return None


def signed_profile(events: Sequence[Event], series_for: dict, horizons_min: Sequence[int],
                   pre_min: int = 20) -> dict:
    """Mean signed move (price units, in the NEWS direction) from the last snapshot at/before the news to the first
    snapshot at/after news + h, for each horizon; plus the pre-news move (t-pre -> t).  ``series_for(event)`` returns the
    team's win-price Series.  Events without both endpoints, or whose horizon passes the tip, are dropped (counted)."""
    res = {"n_events": len(events), "horizons": {}, "pre": None}
    pre_rows = []
    for h in horizons_min:
        rows = []
        for e in events:
            s = series_for(e)
            if not s:
                continue
            t0 = price_at(s, e.report_utc, "le")
            t1 = price_at(s, e.report_utc + timedelta(minutes=h), "ge")
            if not t0 or not t1 or t1[0] >= e.tip_utc or t1[0] <= t0[0]:
                continue
            rows.append((e.matchup + e.game_date, e.sign * (t1[1] - t0[1]), abs(t1[1] - t0[1])))
        res["horizons"][h] = _summ(rows)
    for e in events:
        s = series_for(e)
        if not s:
            continue
        a = price_at(s, e.report_utc - timedelta(minutes=pre_min), "le")
        b = price_at(s, e.report_utc, "le")
        if a and b and b[0] > a[0] and b[0] < e.tip_utc:
            pre_rows.append((e.matchup + e.game_date, e.sign * (b[1] - a[1]), abs(b[1] - a[1])))
    res["pre"] = _summ(pre_rows)
    return res


def _summ(rows, boots: int = 2000, seed: int = 7) -> dict:
    n = len(rows)
    if n == 0:
        return {"n": 0, "games": 0}
    mean = sum(r[1] for r in rows) / n
    mabs = sum(r[2] for r in rows) / n
    by_game: dict = {}
    for g, v, _ in rows:
        by_game.setdefault(g, []).append(v)
    keys = list(by_game)
    rng = random.Random(seed)
    bm = []
    for _ in range(boots):
        tot = cnt = 0
        for _k in keys:
            vs = by_game[keys[rng.randrange(len(keys))]]
            tot += sum(vs)
            cnt += len(vs)
        bm.append(tot / cnt)
    bm.sort()
    return {"n": n, "games": len(keys), "mean_signed": mean, "mean_abs": mabs,
            "lo": bm[int(0.025 * boots)], "hi": bm[int(0.975 * boots) - 1]}


def increment(series_for, events: Sequence[Event], h1: int, h2: int, boots: int = 2000) -> dict:
    """Move still to come after the first post-news snapshot: signed (price at news+h2) - (price at news+h1).
    This is the part of the move a trader entering at the h1 snapshot could still have captured."""
    rows = []
    for e in events:
        s = series_for(e)
        if not s:
            continue
        a = price_at(s, e.report_utc + timedelta(minutes=h1), "ge")
        b = price_at(s, e.report_utc + timedelta(minutes=h2), "ge")
        if a and b and b[0] > a[0] and b[0] < e.tip_utc:
            rows.append((e.matchup + e.game_date, e.sign * (b[1] - a[1]), abs(b[1] - a[1])))
    return _summ(rows, boots)
