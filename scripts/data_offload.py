#!/usr/bin/env python3
"""W128.5 -- Muse's file / API families as ONE polite server job ($0, no AI per chunk).

What it fetches (public, documented-or-open endpoints only; see 12_EXPLORATORY/data_offload/TRIAGE.md for terms and sizes):
  moneypuck        season summaries (lines, goalies, teams, skaters) + per-team game-by-game CSVs
  nhl_goalie_logs  api.nhle.com stats REST, one row per goalie per game
  nhl_officials    api-web.nhle.com right-rail: referees + linesmen per game
  savant           baseballsavant.mlb.com leaderboard CSVs (expected stats, barrels, percentiles, arsenals, tempo, pop time, ...)
  mlb_boxscore     statsapi.mlb.com boxscore: batting orders + umpire crew per game

Point in time: every stored row / file records its fetch time (`fetched_at_utc`). Past seasons are fetched once (backfill, spread over
nights by a byte AND request cap); the current season is fetched daily and an unchanged snapshot is not stored twice.
Output: exp_output/DATA_OFFLOAD/<family>/..., gzip written as it streams (a whole file is never held in memory), plus a monthly
manifest (`manifest_YYYY-MM.jsonl`) that is both the audit trail and the done-set (idempotent: re-running does nothing new).

Box capacity (operator addendum 2026-11-25, GG-118): 1 GB RAM. One run at a time (flock on /tmp/data_offload.lock), only inside the
09:00-15:00 UTC window, memory-capped by the cron wrapper (systemd-run MemoryMax=150M), peak RSS and runtime logged on every run.

Politeness: honest User-Agent, per-host pause, capped retries, and a refusal (401/403/429, a challenge page, "Access Denied") STOPS that
family for the night. It never retries around, spoofs, or signs in; a source that refuses the server is Muse's.

Usage:
  data_offload.py run [--family F ...] [--out DIR] [--night-cap-mb N] [--max-minutes M] [--no-window]
  data_offload.py probe          # read-only: reachability + one capped sample per family into a temp dir, with peak RSS / runtime
"""
from __future__ import annotations

import argparse
import fcntl
import gzip
import hashlib
import json
import os
import resource
import shutil
import sys
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Callable, Iterator, Optional

ROOT = Path(__file__).resolve().parents[1]
OUT_DEFAULT = ROOT / "exp_output" / "DATA_OFFLOAD"
LOG = ROOT / "logs" / "data_offload.log"
LOCK = "/tmp/data_offload.run.lock"     # distinct from the cron wrapper's own /tmp/data_offload.lock (the same file would self-block)
UA = "prediction-market-bot-research/1.0 (personal non-commercial research; low request rate; honors robots.txt)"
WINDOW_UTC = (9, 15)                    # run only 09:00-15:00 UTC: outside pre-game and live-game hours
CHUNK = 64 * 1024
MAX_FILE_BYTES = 30 * 1024 * 1024       # a single streamed download larger than this is aborted (sanity cap)
RETRIES = 3

# Per-night caps (backfill is spread over nights). Bytes are COMPRESSED bytes written; requests include enumeration requests.
FAMILY_CAPS = {   # family: (max_requests, max_gz_bytes)
    "nhl_goalie_logs": (120, 2_000_000),
    "nhl_officials": (600, 2_000_000),
    "moneypuck": (150, 5_000_000),
    "savant": (150, 1_000_000),
    "mlb_boxscore": (800, 2_000_000),
}
NIGHT_CAP_BYTES = sum(c[1] for c in FAMILY_CAPS.values())   # 12 MB compressed per night, all families
PAUSE_S = {"moneypuck.com": 2.0, "api-web.nhle.com": 1.0, "api.nhle.com": 1.0, "baseballsavant.mlb.com": 3.0, "statsapi.mlb.com": 0.5}
REFUSAL_CODES = (401, 403, 429)
REFUSAL_MARKERS = (b"Access Denied", b"Just a moment", b"cf-chl", b"captcha", b"Attention Required")


class Refused(Exception):
    """The source refused the server (auth / rate / bot check). The family stops for the night; nothing is retried around it."""


class NotFound(Exception):
    pass


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def iso(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def peak_rss_mb() -> float:
    r = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss      # KB on Linux, bytes on macOS
    return round(r / (1024.0 * 1024.0 if sys.platform == "darwin" else 1024.0), 1)


# ------------------------------------------------------------------ http
class Http:
    def __init__(self, pause=None, sleep=time.sleep, opener=None):
        self.pause = dict(PAUSE_S if pause is None else pause)
        self.sleep = sleep
        self.last: dict = {}
        self.requests = 0
        self.opener = opener or urllib.request.urlopen

    def _wait(self, url: str) -> None:
        host = urllib.parse.urlsplit(url).netloc
        gap = self.pause.get(host, 1.0)
        wait = self.last.get(host, 0.0) + gap - time.monotonic()
        if wait > 0:
            self.sleep(wait)
        self.last[host] = time.monotonic()

    def open(self, url: str):
        """Open with capped retries. 5xx / network errors retry (2 s, 6 s); a refusal raises Refused at once; 404 raises NotFound."""
        err: Optional[Exception] = None
        for attempt in range(RETRIES):
            self._wait(url)
            self.requests += 1
            req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept-Encoding": "identity"})
            try:
                return self.opener(req, timeout=40)
            except urllib.error.HTTPError as e:
                if e.code in REFUSAL_CODES:
                    raise Refused("HTTP %d from %s" % (e.code, urllib.parse.urlsplit(url).netloc))
                if e.code == 404:
                    raise NotFound(url)
                err = e
            except (urllib.error.URLError, TimeoutError, OSError) as e:
                err = e
            self.sleep((2, 6, 6)[attempt])
        raise RuntimeError("giving up after %d tries: %s: %s" % (RETRIES, url, err))

    def json(self, url: str):
        with self.open(url) as r:
            raw = r.read(MAX_FILE_BYTES + 1)
        if len(raw) > MAX_FILE_BYTES:
            raise RuntimeError("response over the %d MB sanity cap: %s" % (MAX_FILE_BYTES >> 20, url))
        if any(m in raw[:2000] for m in REFUSAL_MARKERS):
            raise Refused("bot-check / access-denied page from %s" % urllib.parse.urlsplit(url).netloc)
        return json.loads(raw)

    def stream_gz(self, url: str, dest: Path, expect_header: Optional[bytes] = None) -> tuple:
        """Stream `url` into gzip at `dest` (atomic rename). Returns (raw_bytes, gz_bytes, sha256_of_raw). Never holds the file in memory."""
        dest.parent.mkdir(parents=True, exist_ok=True)
        tmp = dest.with_name(dest.name + ".part")
        h = hashlib.sha256()
        raw_n = 0
        with self.open(url) as r, gzip.open(tmp, "wb", compresslevel=6) as out:
            first = True
            while True:
                b = r.read(CHUNK)
                if not b:
                    break
                if first:
                    first = False
                    if any(m in b[:2000] for m in REFUSAL_MARKERS) or b.lstrip()[:15].lower().startswith((b"<!doctype html", b"<html")):
                        tmp.unlink(missing_ok=True)
                        raise Refused("HTML / bot-check page where a data file was expected: %s" % url)
                raw_n += len(b)
                if raw_n > MAX_FILE_BYTES:
                    tmp.unlink(missing_ok=True)
                    raise RuntimeError("download over the %d MB sanity cap: %s" % (MAX_FILE_BYTES >> 20, url))
                h.update(b)
                out.write(b)
        if raw_n == 0:
            tmp.unlink(missing_ok=True)
            raise RuntimeError("empty body: %s" % url)
        os.replace(tmp, dest)
        return raw_n, dest.stat().st_size, h.hexdigest()


# ------------------------------------------------------------------ manifest = audit trail + done set
class Manifest:
    def __init__(self, family_dir: Path):
        self.dir = family_dir
        self.done: set = set()
        self.last_sha: dict = {}
        for p in sorted(family_dir.glob("manifest_????-??.jsonl*")) if family_dir.exists() else []:
            op = gzip.open if p.suffix == ".gz" else open
            with op(p, "rt") as fh:
                for line in fh:
                    try:
                        r = json.loads(line)
                    except ValueError:
                        continue
                    if r.get("done", True):
                        self.done.add(r["key"])
                    if r.get("sha256") and r.get("base"):
                        self.last_sha[r["base"]] = r["sha256"]

    def add(self, row: dict) -> None:
        self.dir.mkdir(parents=True, exist_ok=True)
        row = {"fetched_at_utc": iso(now_utc()), **row}
        with open(self.dir / ("manifest_%s.jsonl" % now_utc().strftime("%Y-%m")), "a") as fh:
            fh.write(json.dumps(row, sort_keys=True) + "\n")
        if row.get("done", True):
            self.done.add(row["key"])
        if row.get("sha256") and row.get("base"):
            self.last_sha[row["base"]] = row["sha256"]


def append_gz_jsonl(path: Path, rows: list) -> int:
    """Append rows as one more gzip member (a multi-member .gz reads as one stream). Returns compressed bytes added."""
    path.parent.mkdir(parents=True, exist_ok=True)
    before = path.stat().st_size if path.exists() else 0
    with gzip.open(path, "ab", compresslevel=6) as fh:
        for r in rows:
            fh.write((json.dumps(r, sort_keys=True, separators=(",", ":")) + "\n").encode())
    return path.stat().st_size - before


@dataclass
class Budget:
    max_requests: int
    max_bytes: int
    deadline: float                     # time.monotonic() deadline
    requests0: int = 0
    bytes_written: int = 0
    stop: str = ""

    def exhausted(self, http: Http) -> bool:
        if http.requests - self.requests0 >= self.max_requests:
            self.stop = "request cap"
        elif self.bytes_written >= self.max_bytes:
            self.stop = "byte cap"
        elif time.monotonic() >= self.deadline:
            self.stop = "time cap"
        return bool(self.stop)


@dataclass
class Ctx:
    http: Http
    out: Path
    budget: Budget
    today: date
    stats: dict = field(default_factory=lambda: {"items": 0, "unchanged": 0, "missing": 0, "bytes": 0})


# ------------------------------------------------------------------ seasons
def nhl_season_start_year(today: date) -> int:
    return today.year if today.month >= 9 else today.year - 1


def nhl_in_season(today: date) -> bool:
    return today.month >= 10 or today.month <= 6


def mlb_in_season(today: date) -> bool:
    return (3, 15) <= (today.month, today.day) <= (11, 5)


# ------------------------------------------------------------------ family: moneypuck
MP_BASE = "https://moneypuck.com/moneypuck/playerData"
MP_KINDS = ("lines", "goalies", "teams", "skaters")
MP_TEAMS = ("ANA", "ARI", "ATL", "BOS", "BUF", "CAR", "CBJ", "CGY", "CHI", "COL", "DAL", "DET", "EDM", "FLA", "LAK", "MIN", "MTL", "NJD",
            "NSH", "NYI", "NYR", "OTT", "PHI", "PIT", "SEA", "SJS", "STL", "T.B", "TBL", "TOR", "UTA", "VAN", "VGK", "WPG", "WSH")
MP_FIRST_SEASON = 2014


def mp_items(today: date) -> Iterator[dict]:
    cur = nhl_season_start_year(today)
    live = nhl_in_season(today)
    stamp = today.isoformat()
    for kind in MP_KINDS:                                        # current season first: daily point-in-time snapshots in season
        base = "moneypuck|summary|%d|%s" % (cur, kind)
        key = base + "@" + stamp if live else base
        yield {"key": key, "base": base, "url": "%s/seasonSummary/%d/regular/%s.csv" % (MP_BASE, cur, kind),
               "dest": "moneypuck/seasonSummary/%d/%s%s.csv.gz" % (cur, kind, "_" + stamp if live else "")}
    for season in range(cur - 1, MP_FIRST_SEASON - 1, -1):       # finished seasons: once
        for kind in MP_KINDS:
            base = "moneypuck|summary|%d|%s" % (season, kind)
            yield {"key": base, "base": base, "url": "%s/seasonSummary/%d/regular/%s.csv" % (MP_BASE, season, kind),
                   "dest": "moneypuck/seasonSummary/%d/%s.csv.gz" % (season, kind), "past": True}
    for season in range(cur, MP_FIRST_SEASON - 1, -1):
        cur_live = live and season == cur
        if cur_live and today.weekday() != 0:
            continue                                             # the in-season team game files refresh Mondays
        for team in MP_TEAMS:
            base = "moneypuck|teamgame|%d|%s" % (season, team)
            key = base + "@" + stamp if cur_live else base
            yield {"key": key, "base": base, "url": "%s/teamGameByGame/%d/regular/%s.csv" % (MP_BASE, season, team),
                   "dest": "moneypuck/teamGameByGame/%d/%s%s.csv.gz" % (season, team, "_" + stamp if cur_live else ""), "past": not cur_live}


def run_csv_item(ctx: Ctx, man: Manifest, it: dict) -> None:
    dest = ctx.out / it["dest"]
    try:
        raw_n, gz_n, sha = ctx.http.stream_gz(it["url"], dest)
    except NotFound:
        man.add({"key": it["key"], "base": it.get("base"), "url": it["url"], "status": 404, "ok": False})
        ctx.stats["missing"] += 1
        return
    if man.last_sha.get(it.get("base")) == sha and not it.get("past"):
        dest.unlink(missing_ok=True)                             # unchanged since the last snapshot: record it, store it once
        man.add({"key": it["key"], "base": it.get("base"), "url": it["url"], "status": 200, "ok": True, "unchanged": True, "sha256": sha})
        ctx.stats["unchanged"] += 1
        return
    ctx.budget.bytes_written += gz_n
    ctx.stats["bytes"] += gz_n
    man.add({"key": it["key"], "base": it.get("base"), "url": it["url"], "status": 200, "ok": True, "raw_bytes": raw_n,
             "gz_bytes": gz_n, "sha256": sha, "path": it["dest"]})


# ------------------------------------------------------------------ family: savant
SV = "https://baseballsavant.mlb.com/leaderboard"
SV_BOARDS = (   # name, url template ({y} year), validated 2026-11-25 to return text/csv
    ("expected_batter", SV + "/expected_statistics?type=batter&year={y}&position=&team=&min=q&csv=true"),
    ("expected_pitcher", SV + "/expected_statistics?type=pitcher&year={y}&position=&team=&min=q&csv=true"),
    ("barrels_batter", SV + "/statcast?type=batter&year={y}&position=&team=&min=q&csv=true"),
    ("barrels_pitcher", SV + "/statcast?type=pitcher&year={y}&position=&team=&min=q&csv=true"),
    ("percentile_batter", SV + "/percentile-rankings?type=batter&year={y}&csv=true"),
    ("percentile_pitcher", SV + "/percentile-rankings?type=pitcher&year={y}&csv=true"),
    ("pitch_arsenals", SV + "/pitch-arsenals?year={y}&min=100&type=pitcher&hand=&csv=true"),
    ("pitch_tempo", SV + "/pitch-tempo?year={y}&min=q&csv=true"),
    ("pop_time", SV + "/poptime?year={y}&min2b=5&min3b=0&csv=true"),
    ("sprint_speed", SV + "/sprint_speed?year={y}&position=&team=&min=10&csv=true"),
    ("running_splits", SV + "/running_splits?type=Batter&year={y}&min=10&csv=true"),
    ("baserunning_run_value", SV + "/baserunning-run-value?game_type=Regular&year={y}&csv=true"),
)
SV_FIRST_YEAR = 2015


def sv_items(today: date) -> Iterator[dict]:
    live = mlb_in_season(today)
    stamp = today.isoformat()
    last_complete = today.year if (today.month, today.day) > (11, 5) else today.year - 1
    if live:                                                     # in season: today's snapshot of this year's boards
        for name, tpl in SV_BOARDS:
            base = "savant|%s|%d" % (name, today.year)
            yield {"key": base + "@" + stamp, "base": base, "url": tpl.format(y=today.year),
                   "dest": "savant/%s/%d_%s.csv.gz" % (name, today.year, stamp)}
    for y in range(last_complete, SV_FIRST_YEAR - 1, -1):        # finished seasons: once
        for name, tpl in SV_BOARDS:
            base = "savant|%s|%d" % (name, y)
            yield {"key": base, "base": base, "url": tpl.format(y=y), "dest": "savant/%s/%d.csv.gz" % (name, y), "past": True}


# ------------------------------------------------------------------ family: nhl_goalie_logs
NHL_STATS = "https://api.nhle.com/stats/rest/en"
NHL_WEB = "https://api-web.nhle.com/v1"


def goalie_rows(data: dict, fetched: str) -> list:
    keep = ("gameId", "gameDate", "playerId", "goalieFullName", "teamAbbrev", "opponentTeamAbbrev", "homeRoad", "gamesStarted",
            "decision", "saves", "shotsAgainst", "goalsAgainst", "savePct", "timeOnIce", "shutouts", "wins", "losses", "otLosses")
    return [{**{k: r.get(k) for k in keep}, "fetched_at_utc": fetched} for r in data.get("data", [])]


def goalie_season_ids(today: date) -> list:
    cur = nhl_season_start_year(today)
    return list(range(cur, MP_FIRST_SEASON - 1, -1))


def run_goalie_logs(ctx: Ctx, man: Manifest) -> None:
    today = ctx.today
    cur = nhl_season_start_year(today)
    # current season: one request per finished calendar day (immutable rows, fetch time recorded), from Oct 1 to yesterday
    d = date(cur, 10, 1)
    while d < today and nhl_in_season(today):
        key = "nhl_goalie_logs|day|%s" % d.isoformat()
        if key not in man.done:
            if ctx.budget.exhausted(ctx.http):
                return
            q = urllib.parse.urlencode({"isGame": "true", "limit": 100, "sort": "playerId",
                                        "cayenneExp": "gameDate>='%s' and gameDate<='%s' and gameTypeId in (2,3)" % (d, d)})
            data = ctx.http.json("%s/goalie/summary?%s" % (NHL_STATS, q))
            rows = goalie_rows(data, iso(now_utc()))
            n = append_gz_jsonl(ctx.out / "nhl_goalie_logs" / ("season_%d.jsonl.gz" % cur), rows) if rows else 0
            ctx.budget.bytes_written += n
            ctx.stats["bytes"] += n
            ctx.stats["items"] += 1
            man.add({"key": key, "rows": len(rows), "gz_bytes": n, "ok": True})
        d += timedelta(days=1)
    for season in goalie_season_ids(today):                      # past seasons: paginated once
        if season == cur and nhl_in_season(today):
            continue
        sid = "%d%d" % (season, season + 1)
        start = 0
        while True:
            key = "nhl_goalie_logs|season|%s|start|%d" % (sid, start)
            if key in man.done:
                start += 100
                continue
            if ctx.budget.exhausted(ctx.http):
                return
            q = urllib.parse.urlencode({"isGame": "true", "limit": 100, "start": start, "sort": "gameId,playerId",
                                        "cayenneExp": "seasonId=%s and gameTypeId in (2,3)" % sid})
            data = ctx.http.json("%s/goalie/summary?%s" % (NHL_STATS, q))
            rows = goalie_rows(data, iso(now_utc()))
            n = append_gz_jsonl(ctx.out / "nhl_goalie_logs" / ("season_%s.jsonl.gz" % season), rows) if rows else 0
            ctx.budget.bytes_written += n
            ctx.stats["bytes"] += n
            ctx.stats["items"] += 1
            man.add({"key": key, "rows": len(rows), "gz_bytes": n, "ok": True})
            if len(rows) < 100:
                break
            start += 100


# ------------------------------------------------------------------ family: nhl_officials
def officials_row(game: dict, rr: dict, fetched: str) -> dict:
    gi = (rr or {}).get("gameInfo") or {}
    names = lambda k: [o.get("fullName", {}).get("default") for o in gi.get(k, [])]  # noqa: E731
    return {"game_id": game["id"], "game_date": game.get("gameDate"), "season": game.get("season"), "game_type": game.get("gameType"),
            "referees": names("referees"), "linesmen": names("linesmen"), "has_officials": bool(gi.get("referees") or gi.get("linesmen")),
            "fetched_at_utc": fetched}


def run_officials(ctx: Ctx, man: Manifest) -> None:
    cur = nhl_season_start_year(ctx.today)
    for season in range(cur, MP_FIRST_SEASON - 1, -1):
        skey = "nhl_officials|season_complete|%d" % season
        if skey in man.done:
            continue
        if ctx.budget.exhausted(ctx.http):
            return
        q = urllib.parse.urlencode({"cayenneExp": "season=%d%d and gameType in (2,3)" % (season, season + 1)})
        games = ctx.http.json("%s/game?%s" % (NHL_STATS, q)).get("data", [])
        todo = [g for g in games if g.get("gameDate") and g["gameDate"] < ctx.today.isoformat()]
        pending = False
        for g in sorted(todo, key=lambda g: g["id"]):
            key = "nhl_officials|%d" % g["id"]
            if key in man.done:
                continue
            if ctx.budget.exhausted(ctx.http):
                pending = True
                break
            try:
                rr = ctx.http.json("%s/gamecenter/%d/right-rail" % (NHL_WEB, g["id"]))
            except NotFound:
                rr = None
            row = officials_row(g, rr, iso(now_utc()))
            n = append_gz_jsonl(ctx.out / "nhl_officials" / ("season_%d.jsonl.gz" % season), [row])
            ctx.budget.bytes_written += n
            ctx.stats["bytes"] += n
            ctx.stats["items"] += 1
            man.add({"key": key, "ok": True, "has_officials": row["has_officials"], "gz_bytes": n})
        if not pending and season < cur:
            man.add({"key": skey, "ok": True, "games": len(todo)})


# ------------------------------------------------------------------ family: mlb_boxscore
MLB = "https://statsapi.mlb.com/api/v1"


def boxscore_row(game: dict, box: dict, fetched: str) -> dict:
    def side(s):
        t = (box.get("teams") or {}).get(s) or {}
        return {"team_id": (t.get("team") or {}).get("id"), "batting_order": t.get("battingOrder") or []}
    return {"game_pk": game["gamePk"], "date": game.get("officialDate"), "game_type": game.get("gameType"),
            "away": side("away"), "home": side("home"),
            "umpires": [{"id": (o.get("official") or {}).get("id"), "name": (o.get("official") or {}).get("fullName"),
                         "type": o.get("officialType")} for o in box.get("officials", [])], "fetched_at_utc": fetched}


def month_ranges(year: int) -> Iterator[tuple]:
    for m in range(3, 12):
        first = date(year, m, 1)
        last = (date(year + (m == 12), m % 12 + 1, 1) - timedelta(days=1))
        yield first, last


def run_mlb_boxscore(ctx: Ctx, man: Manifest) -> None:
    last_year = ctx.today.year if (ctx.today.month, ctx.today.day) > (11, 5) or mlb_in_season(ctx.today) else ctx.today.year - 1
    for year in range(last_year, 2014, -1):
        ykey = "mlb_boxscore|year_complete|%d" % year
        if ykey in man.done:
            continue
        year_pending = False
        for first, last in month_ranges(year):
            if first >= ctx.today:
                continue
            mkey = "mlb_boxscore|month_complete|%d-%02d" % (year, first.month)
            if mkey in man.done:
                continue
            if ctx.budget.exhausted(ctx.http):
                return
            q = urllib.parse.urlencode({"sportId": 1, "startDate": first.isoformat(), "endDate": min(last, ctx.today - timedelta(days=1)).isoformat(),
                                        "gameType": "R,F,D,L,W"})
            games = [g for d in ctx.http.json("%s/schedule?%s" % (MLB, q)).get("dates", []) for g in d.get("games", [])
                     if g.get("status", {}).get("abstractGameState") == "Final"]
            month_pending = False
            for g in sorted(games, key=lambda g: g["gamePk"]):
                key = "mlb_boxscore|%d" % g["gamePk"]
                if key in man.done:
                    continue
                if ctx.budget.exhausted(ctx.http):
                    month_pending = year_pending = True
                    break
                try:
                    box = ctx.http.json("%s/game/%d/boxscore" % (MLB, g["gamePk"]))
                except NotFound:
                    box = {}
                row = boxscore_row(g, box, iso(now_utc()))
                n = append_gz_jsonl(ctx.out / "mlb_boxscore" / ("season_%d.jsonl.gz" % year), [row])
                ctx.budget.bytes_written += n
                ctx.stats["bytes"] += n
                ctx.stats["items"] += 1
                man.add({"key": key, "ok": True, "gz_bytes": n})
            if month_pending:
                return
            if last < ctx.today - timedelta(days=1):
                man.add({"key": mkey, "ok": True, "games": len(games)})
        if not year_pending and year < ctx.today.year:
            man.add({"key": ykey, "ok": True})


# ------------------------------------------------------------------ runner
def run_csv_family(ctx: Ctx, man: Manifest, items: Iterator[dict]) -> None:
    for it in items:
        if it["key"] in man.done:
            continue
        if ctx.budget.exhausted(ctx.http):
            return
        run_csv_item(ctx, man, it)
        ctx.stats["items"] += 1


FAMILIES: dict = {
    "nhl_goalie_logs": lambda c, m: run_goalie_logs(c, m),
    "nhl_officials": lambda c, m: run_officials(c, m),
    "moneypuck": lambda c, m: run_csv_family(c, m, mp_items(c.today)),
    "savant": lambda c, m: run_csv_family(c, m, sv_items(c.today)),
    "mlb_boxscore": lambda c, m: run_mlb_boxscore(c, m),
}


def in_window(now: datetime) -> bool:
    return WINDOW_UTC[0] <= now.hour < WINDOW_UTC[1]


def run_family(name: str, out: Path, http: Http, today: date, caps: tuple, max_minutes: float) -> dict:
    budget = Budget(max_requests=caps[0], max_bytes=caps[1], deadline=time.monotonic() + max_minutes * 60, requests0=http.requests)
    ctx = Ctx(http=http, out=out, budget=budget, today=today)
    man = Manifest(out / name)
    t0 = time.monotonic()
    err = ""
    try:
        FAMILIES[name](ctx, man)
    except Refused as e:
        err = "REFUSED: %s (family stopped for the night)" % e
    except Exception as e:  # noqa: BLE001 -- one family failing must not stop the others
        err = "%s: %s" % (type(e).__name__, e)
    return {"family": name, **ctx.stats, "requests": http.requests - budget.requests0, "stop": budget.stop or ("error" if err else "done"),
            "error": err, "seconds": round(time.monotonic() - t0, 1), "peak_rss_mb": peak_rss_mb()}


def cmd_run(args) -> int:
    now = now_utc()
    if not args.no_window and not in_window(now):
        print(json.dumps({"ts": iso(now), "skipped": "outside the %02d:00-%02d:00 UTC window" % WINDOW_UTC}))
        return 0
    lock = open(LOCK, "w")
    try:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        print(json.dumps({"ts": iso(now), "skipped": "another data_offload run holds the lock"}))
        return 0
    out = Path(args.out) if args.out else OUT_DEFAULT
    fams = args.family or list(FAMILIES)
    http = Http()
    t0 = time.monotonic()
    results = []
    night_bytes = args.night_cap_mb * 1_000_000
    for f in fams:
        if sum(r["bytes"] for r in results) >= night_bytes:
            results.append({"family": f, "stop": "night byte cap reached before start"})
            continue
        reqs, byts = FAMILY_CAPS[f]
        if args.max_requests:
            reqs = min(reqs, args.max_requests)
        left = max(args.max_minutes * 60 - (time.monotonic() - t0), 0) / 60.0
        results.append(run_family(f, out, http, now.date(), (reqs, min(byts, night_bytes - sum(r.get("bytes", 0) for r in results))), left))
    line = {"ts": iso(now), "families": results, "total_gz_bytes": sum(r.get("bytes", 0) for r in results), "requests": http.requests,
            "seconds": round(time.monotonic() - t0, 1), "peak_rss_mb": peak_rss_mb()}
    print(json.dumps(line, sort_keys=True))
    if not args.out:
        LOG.parent.mkdir(parents=True, exist_ok=True)
        with open(LOG, "a") as fh:
            fh.write(json.dumps(line, sort_keys=True) + "\n")
    return 0


REACH = (   # name, url -- reachability only (status + size), never past a bot check
    ("nba_stats", "https://stats.nba.com/stats/leaguedashteamstats?Season=2025-26&SeasonType=Regular+Season&MeasureType=Base&PerMode=PerGame"),
    ("nba_cdn", "https://cdn.nba.com/static/json/liveData/boxscore/boxscore_0022500001.json"),
    ("pfr", "https://www.pro-football-reference.com/years/2025/opp.htm"),
    ("umpscorecards", "https://umpscorecards.com/api/games?startDate=2025-06-01&endDate=2025-06-02"),
    ("kofsports", "https://kofsports.com/"),
)


def cmd_probe(args) -> int:
    """Read-only: reachability per family and per MUSE candidate, and one capped sample run per family in a temp dir, each in its own
    process so peak RSS and runtime are per scraper. Writes nothing under the project."""
    import subprocess
    res = {"ts": iso(now_utc()), "reach": [], "families": []}
    for name, url in REACH:
        req = urllib.request.Request(url, headers={"User-Agent": UA})
        t0 = time.monotonic()
        try:
            with urllib.request.urlopen(req, timeout=15) as r:
                body = r.read(4096)
                res["reach"].append({"name": name, "status": r.status, "bytes_first_read": len(body),
                                     "challenge": any(m in body for m in REFUSAL_MARKERS), "seconds": round(time.monotonic() - t0, 1)})
        except urllib.error.HTTPError as e:
            res["reach"].append({"name": name, "status": e.code, "seconds": round(time.monotonic() - t0, 1)})
        except Exception as e:  # noqa: BLE001
            res["reach"].append({"name": name, "error": type(e).__name__, "seconds": round(time.monotonic() - t0, 1)})
    tmp = tempfile.mkdtemp(prefix="data_offload_probe_")
    try:
        for fam in FAMILIES:
            cmd = [sys.executable, str(Path(__file__).resolve()), "run", "--family", fam, "--out", os.path.join(tmp, fam), "--no-window",
                   "--max-requests", str(args.sample_requests), "--max-minutes", "6"]
            t0 = time.monotonic()
            p = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
            try:
                line = json.loads(p.stdout.strip().splitlines()[-1])
                fr = line["families"][0]
                res["families"].append({k: fr.get(k) for k in ("family", "requests", "items", "bytes", "stop", "error", "seconds", "peak_rss_mb")})
            except Exception:  # noqa: BLE001
                res["families"].append({"family": fam, "error": "probe run failed: " + (p.stderr or p.stdout)[-300:]})
            res["families"][-1]["wall_seconds"] = round(time.monotonic() - t0, 1)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    print(json.dumps(res, indent=1, sort_keys=True))
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run")
    r.add_argument("--family", action="append", choices=list(FAMILIES))
    r.add_argument("--out")
    r.add_argument("--night-cap-mb", type=float, default=NIGHT_CAP_BYTES / 1e6)
    r.add_argument("--max-minutes", type=float, default=240)
    r.add_argument("--max-requests", type=int, default=0)
    r.add_argument("--no-window", action="store_true")
    r.set_defaults(fn=cmd_run)
    p = sub.add_parser("probe")
    p.add_argument("--sample-requests", type=int, default=25)
    p.set_defaults(fn=cmd_probe)
    a = ap.parse_args(argv)
    return a.fn(a)


if __name__ == "__main__":
    sys.exit(main())
