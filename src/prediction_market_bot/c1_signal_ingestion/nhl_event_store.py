"""NHL event store: one reproducible build of the free NHL APIs (W83.3, ADR-0073 stage 1).

Sources (all free, public, unauthenticated, no login):

* ``api-web.nhle.com/v1/schedule/<date>``               weekly schedule with the real start instant of every game
* ``api-web.nhle.com/v1/gamecenter/<id>/play-by-play``  every event (shots with x/y + type, faceoffs, hits, penalties,
  giveaways/takeaways, goals) with the strength state ``situationCode`` and the dressed roster
* ``api-web.nhle.com/v1/gamecenter/<id>/boxscore``      per-player lines (TOI, shots, hits, PIM, goalie saves)
* ``api.nhle.com/stats/rest/en/shiftcharts``            every shift of every skater and goalie (the on-ice record)

Season label = the calendar year the season STARTS (2015 = 2015-16), matching the NHL's own ``YYYYYYYY`` ids
(20152016). Coverage starts at 2015-16 (the first season of the operator's window); play-by-play and shifts reach
back to 2010-11 on the same endpoints, but every season before 2015 is out of scope here.

Layout (git-ignored; ``exp_output/NHL_EVENTS/`` is listed in ``.gitignore``)::

    exp_output/NHL_EVENTS/raw/<kind>/<season>/<game_id>.json.gz   # the fetched payload + fetch stamp (resumable cache)
    exp_output/NHL_EVENTS/raw/schedule/<week_start>.json.gz
    exp_output/NHL_EVENTS/<table>_<season>.parquet                # compiled from the cache, deterministic

The committed artefact is the manifest, ``02_ARCHITECTURE_DESIGN/NHL_ENGINE/event_store_manifest.json``.

Nothing here touches an order, a position, a stake or a ledger row. Public GETs only, rate-limited, 429-backoff.
"""
from __future__ import annotations

import argparse
import datetime as dt
import gzip
import hashlib
import json
import re
import sys
import threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any, Optional

from prediction_market_bot.atomic_io import atomic_write_text
from prediction_market_bot.c1_signal_ingestion.nhl_ingest import NhlHttpError, Throttle, http_get_json

WEB = "https://api-web.nhle.com/v1"
STATS = "https://api.nhle.com/stats/rest/en/shiftcharts?cayenneExp=gameId="
DEFAULT_ROOT = Path("exp_output/NHL_EVENTS")
DEFAULT_MANIFEST = Path("02_ARCHITECTURE_DESIGN/NHL_ENGINE/event_store_manifest.json")
FIRST_SEASON = 2015
KINDS = ("pbp", "box", "shifts")
COUNTING_TYPES = (2, 3)        # regular season, playoffs. 1 = preseason, 4 = all-star, 19 = international: excluded
FINAL_STATES = ("FINAL", "OFF")
TABLES = ("games", "events", "shifts", "box_players", "rosters")


def utc_stamp() -> str:
    return dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def current_season(today: Optional[dt.date] = None) -> int:
    """NHL season in progress or just finished, by START year: the label turns over in September."""
    today = today or dt.datetime.now(dt.timezone.utc).date()
    return today.year if today.month >= 9 else today.year - 1


class LockedThrottle(Throttle):
    """``Throttle`` shared by worker threads: the lock serialises the spacing, so N threads overlap latency but the
    request rate across all of them never exceeds ``1 / interval_s``."""

    def __init__(self, interval_s: float):
        super().__init__(interval_s=interval_s, base_s=interval_s)
        self._lock = threading.Lock()

    def wait(self) -> None:
        with self._lock:
            super().wait()

    def on_429(self) -> None:
        with self._lock:
            super().on_429()

    def on_ok(self) -> None:
        with self._lock:
            super().on_ok()


# ---------------------------------------------------------------- cache
def cache_path(root: Path, kind: str, season: Any, key: Any) -> Path:
    return root / "raw" / kind / str(season) / f"{key}.json.gz"


def write_cache(path: Path, url: str, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    body = json.dumps({"_url": url, "_fetched_at_utc": utc_stamp(), "payload": payload}, separators=(",", ":"))
    tmp = path.with_suffix(".tmp")
    with gzip.open(tmp, "wt", encoding="utf8", compresslevel=6) as fh:
        fh.write(body)
    tmp.replace(path)


def read_cache(path: Path) -> dict:
    with gzip.open(path, "rt", encoding="utf8") as fh:
        return json.load(fh)


def game_url(kind: str, game_id: int) -> str:
    return {"pbp": f"{WEB}/gamecenter/{game_id}/play-by-play",
            "box": f"{WEB}/gamecenter/{game_id}/boxscore",
            "shifts": f"{STATS}{game_id}"}[kind]


# ---------------------------------------------------------------- schedule
def parse_schedule_week(payload: dict) -> list[dict]:
    """Counting games (regular season + playoffs) from one ``schedule/<date>`` payload."""
    out = []
    for day in payload.get("gameWeek", []):
        for g in day.get("games", []):
            if g.get("gameType") not in COUNTING_TYPES:
                continue
            h, a = g["homeTeam"], g["awayTeam"]
            out.append({
                "game_id": int(g["id"]), "season": int(g["season"]) // 10000, "game_type": int(g["gameType"]),
                "start_time_utc": g["startTimeUTC"], "game_date_et": day.get("date"),
                "venue": (g.get("venue") or {}).get("default"), "neutral_site": bool(g.get("neutralSite", False)),
                "game_state": g.get("gameState"), "schedule_state": g.get("gameScheduleState"),
                "home_team_id": h.get("id"), "home": h.get("abbrev"), "home_score": h.get("score"),
                "away_team_id": a.get("id"), "away": a.get("abbrev"), "away_score": a.get("score"),
                "last_period_type": (g.get("gameOutcome") or {}).get("lastPeriodType"),
            })
    return out


def fetch_schedule(root: Path, throttle: Throttle, first: dt.date, last: dt.date,
                   today: Optional[dt.date] = None) -> list[dict]:
    """Walk ``nextStartDate`` week by week from ``first`` to ``last``. A week still in play (ends within a day of
    ``today``) is never cached, so a later run sees its final scores."""
    today = today or dt.datetime.now(dt.timezone.utc).date()
    games: dict[int, dict] = {}
    day = first
    while day <= last:
        p = cache_path(root, "schedule", "weeks", day.isoformat())
        if p.exists():
            payload = read_cache(p)["payload"]
        else:
            url = f"{WEB}/schedule/{day.isoformat()}"
            payload = http_get_json(url, throttle)
            wk_end = max((d["date"] for d in payload.get("gameWeek", [])), default=day.isoformat())
            if dt.date.fromisoformat(wk_end) < today - dt.timedelta(days=2):
                write_cache(p, url, payload)
        for g in parse_schedule_week(payload):
            games[g["game_id"]] = g
        nxt = payload.get("nextStartDate")
        if not nxt:
            break
        nd = dt.date.fromisoformat(nxt)
        day = nd if nd > day else day + dt.timedelta(days=7)
    return sorted(games.values(), key=lambda g: (g["start_time_utc"], g["game_id"]))


# ---------------------------------------------------------------- per-game fetch
def fetch_game(root: Path, throttle: Throttle, game: dict, failures: list) -> int:
    """Fetch the three payloads for one finished game; skip any already cached. Returns new files written."""
    wrote = 0
    for kind in KINDS:
        p = cache_path(root, kind, game["season"], game["game_id"])
        if p.exists():
            continue
        url = game_url(kind, game["game_id"])
        try:
            payload = http_get_json(url, throttle)
        except NhlHttpError as e:
            failures.append({"game_id": game["game_id"], "kind": kind, "status": e.status, "at": utc_stamp()})
            continue
        except Exception as e:  # network exhaustion: leave uncached so a rerun resumes it
            failures.append({"game_id": game["game_id"], "kind": kind, "status": 0, "error": str(e)[:120],
                             "at": utc_stamp()})
            continue
        if kind == "shifts" and not payload.get("data"):
            failures.append({"game_id": game["game_id"], "kind": kind, "status": 200, "error": "empty", "at": utc_stamp()})
            continue
        write_cache(p, url, payload)
        wrote += 1
    return wrote


def build_fetch(root: Path, seasons: list[int], rps: float, threads: int, limit: Optional[int] = None) -> dict:
    throttle = LockedThrottle(1.0 / rps)
    root.mkdir(parents=True, exist_ok=True)
    first = dt.date(min(seasons), 9, 20)
    last = dt.date(max(seasons) + 1, 7, 15)
    sched = fetch_schedule(root, throttle, first, last)
    atomic_write_text(root / "schedule_games.json", json.dumps(sched))
    now = dt.datetime.now(dt.timezone.utc).isoformat()
    todo = [g for g in sched if g["season"] in seasons and g["game_state"] in FINAL_STATES
            and g["start_time_utc"].replace("Z", "+00:00") < now]
    pending = [g for g in todo if not all(cache_path(root, k, g["season"], g["game_id"]).exists() for k in KINDS)]
    if limit:
        pending = pending[:limit]
    print(f"schedule: {len(sched)} counting games, {len(todo)} finished, {len(pending)} to fetch", flush=True)
    failures: list = []
    done = 0
    with ThreadPoolExecutor(max_workers=threads) as ex:
        for n in ex.map(lambda g: fetch_game(root, throttle, g, failures), pending):
            done += 1
            if done % 200 == 0:
                print(f"  {done}/{len(pending)} games, interval={throttle.interval_s:.2f}s, "
                      f"failures={len(failures)}", flush=True)
    atomic_write_text(root / "fetch_failures.json", json.dumps(failures))
    return {"schedule_games": len(sched), "finished": len(todo), "fetched": len(pending), "failures": len(failures)}


# ---------------------------------------------------------------- parse (pure functions; no I/O)
def mmss(txt: Optional[str]) -> Optional[int]:
    """'12:34' -> seconds; None for missing/odd values."""
    if not txt or not re.fullmatch(r"\d+:\d{2}", txt):
        return None
    m, sec = txt.split(":")
    return int(m) * 60 + int(sec)


def parse_situation(code: Any) -> dict:
    """``situationCode`` = away_goalie, away_skaters, home_skaters, home_goalie (e.g. 1551 = 5v5, both nets in)."""
    c = str(code or "")
    if not re.fullmatch(r"\d{4}", c):
        return {"away_goalie": None, "away_skaters": None, "home_skaters": None, "home_goalie": None}
    return {"away_goalie": int(c[0]), "away_skaters": int(c[1]), "home_skaters": int(c[2]), "home_goalie": int(c[3])}


def parse_events(game_id: int, season: int, payload: dict) -> list[dict]:
    home_id = (payload.get("homeTeam") or {}).get("id")
    rows = []
    for pl in payload.get("plays", []):
        d = pl.get("details") or {}
        per = pl.get("periodDescriptor") or {}
        owner = d.get("eventOwnerTeamId")
        row = {
            "game_id": game_id, "season": season, "event_id": pl.get("eventId"), "sort_order": pl.get("sortOrder"),
            "period": per.get("number"), "period_type": per.get("periodType"),
            "time_in_period_s": mmss(pl.get("timeInPeriod")), "time_remaining_s": mmss(pl.get("timeRemaining")),
            "type_code": pl.get("typeCode"), "type": pl.get("typeDescKey"),
            "owner_team_id": owner, "owner_is_home": (owner == home_id) if owner is not None else None,
            "x": d.get("xCoord"), "y": d.get("yCoord"), "zone": d.get("zoneCode"),
            "shot_type": d.get("shotType"), "shooter_id": d.get("shootingPlayerId") or d.get("scoringPlayerId"),
            "goalie_id": d.get("goalieInNetId"), "blocker_id": d.get("blockingPlayerId"),
            "player_id": d.get("playerId"), "hitter_id": d.get("hittingPlayerId"), "hittee_id": d.get("hitteePlayerId"),
            "winner_id": d.get("winningPlayerId"), "loser_id": d.get("losingPlayerId"),
            "penalty_player_id": d.get("committedByPlayerId"), "penalty_type": d.get("descKey"),
            "penalty_minutes": d.get("duration"), "miss_reason": d.get("reason") if pl.get("typeDescKey") == "missed-shot" else None,
            "home_defending_side": pl.get("homeTeamDefendingSide"),
            "away_sog": d.get("awaySOG"), "home_sog": d.get("homeSOG"),
            "away_score": d.get("awayScore"), "home_score": d.get("homeScore"),
        }
        row.update(parse_situation(pl.get("situationCode")))
        rows.append(row)
    return rows


def parse_rosters(game_id: int, season: int, payload: dict) -> list[dict]:
    home_id = (payload.get("homeTeam") or {}).get("id")
    return [{"game_id": game_id, "season": season, "player_id": r.get("playerId"), "team_id": r.get("teamId"),
             "is_home": r.get("teamId") == home_id, "position": r.get("positionCode"),
             "sweater": r.get("sweaterNumber"),
             "first": (r.get("firstName") or {}).get("default"), "last": (r.get("lastName") or {}).get("default")}
            for r in payload.get("rosterSpots", [])]


def parse_shifts(game_id: int, season: int, payload: dict) -> list[dict]:
    rows = []
    for r in payload.get("data", []):
        if r.get("typeCode") != 517:   # 517 = a shift; other typeCodes are goal/penalty markers in the same feed
            continue
        rows.append({"game_id": game_id, "season": season, "player_id": r.get("playerId"), "team_id": r.get("teamId"),
                     "period": r.get("period"), "shift_number": r.get("shiftNumber"),
                     "start_s": mmss(r.get("startTime")), "end_s": mmss(r.get("endTime")),
                     "duration_s": mmss(r.get("duration"))})
    return rows


def _num(x: Any) -> Any:
    return x if isinstance(x, (int, float)) else None


def parse_box_players(game_id: int, season: int, payload: dict) -> list[dict]:
    rows = []
    pg = payload.get("playerByGameStats") or {}
    for side in ("homeTeam", "awayTeam"):
        team = (payload.get(side) or {}).get("id")
        for grp in ("forwards", "defense", "goalies"):
            for p in (pg.get(side) or {}).get(grp, []):
                rows.append({
                    "game_id": game_id, "season": season, "team_id": team, "is_home": side == "homeTeam",
                    "player_id": p.get("playerId"), "group": grp, "position": p.get("position"),
                    "toi_s": mmss(p.get("toi")), "goals": _num(p.get("goals")), "assists": _num(p.get("assists")),
                    "sog": _num(p.get("sog")), "hits": _num(p.get("hits")), "pim": _num(p.get("pim")),
                    "blocked": _num(p.get("blockedShots")), "shifts": _num(p.get("shifts")),
                    "giveaways": _num(p.get("giveaways")), "takeaways": _num(p.get("takeaways")),
                    "pp_goals": _num(p.get("powerPlayGoals")), "plus_minus": _num(p.get("plusMinus")),
                    "shots_against": _num(p.get("shotsAgainst")), "saves": _num(p.get("saves")),
                    "goals_against": _num(p.get("goalsAgainst")), "starter": p.get("starter"),
                })
    return rows


def parse_box_team(payload: dict) -> dict:
    return {"home_sog": (payload.get("homeTeam") or {}).get("sog"), "away_sog": (payload.get("awayTeam") or {}).get("sog"),
            "home_score": (payload.get("homeTeam") or {}).get("score"), "away_score": (payload.get("awayTeam") or {}).get("score")}


# ---------------------------------------------------------------- compile (raw cache -> parquet)
def compile_store(root: Path) -> dict:
    """Parse the whole raw cache into one parquet per (table, season). Deterministic: rows are sorted, files are
    rewritten whole. Returns {table: {season: rows}} plus per-game box reconciliation facts for the checks."""
    import pandas as pd
    sched = json.loads((root / "schedule_games.json").read_text())
    by_season: dict[int, list[dict]] = {}
    for g in sched:
        by_season.setdefault(g["season"], []).append(g)
    counts: dict = {t: {} for t in TABLES}
    recon: list[dict] = []
    for season, games in sorted(by_season.items()):
        ev, sh, bx, ro, gm = [], [], [], [], []
        for g in games:
            gid = g["game_id"]
            have = {k: cache_path(root, k, season, gid).exists() for k in KINDS}
            row = dict(g, has_pbp=have["pbp"], has_box=have["box"], has_shifts=have["shifts"])
            gm.append(row)
            facts = {"game_id": gid, "season": season}
            if have["pbp"]:
                pb = read_cache(cache_path(root, "pbp", season, gid))["payload"]
                e = parse_events(gid, season, pb)
                ev += e
                ro += parse_rosters(gid, season, pb)
                facts["pbp_goals_home"] = sum(1 for x in e if x["type"] == "goal" and x["owner_is_home"] is True and x["period_type"] != "SO")
                facts["pbp_goals_away"] = sum(1 for x in e if x["type"] == "goal" and x["owner_is_home"] is False and x["period_type"] != "SO")
                for side, flag in (("home", True), ("away", False)):
                    facts[f"pbp_sog_{side}"] = sum(1 for x in e if x["type"] in ("shot-on-goal", "goal")
                                                   and x["owner_is_home"] is flag and x["period_type"] != "SO")
                facts["pbp_n_events"] = len(e)
            if have["box"]:
                b = read_cache(cache_path(root, "box", season, gid))["payload"]
                bx += parse_box_players(gid, season, b)
                facts.update({"box_" + k: v for k, v in parse_box_team(b).items()})
            if have["shifts"]:
                sh += parse_shifts(gid, season, read_cache(cache_path(root, "shifts", season, gid))["payload"])
            recon.append(facts)
        for name, rows in (("games", gm), ("events", ev), ("shifts", sh), ("box_players", bx), ("rosters", ro)):
            df = pd.DataFrame(rows)
            df.to_parquet(root / f"{name}_{season}.parquet", index=False)
            counts[name][season] = len(df)
    (root / "recon.json").write_text(json.dumps(recon))
    return counts


def main(argv: Optional[list] = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    f = sub.add_parser("fetch", help="schedule + per-game payloads into the raw cache (resumable)")
    f.add_argument("--root", type=Path, default=DEFAULT_ROOT)
    f.add_argument("--from-season", type=int, default=FIRST_SEASON)
    f.add_argument("--to-season", type=int, default=None)
    f.add_argument("--rps", type=float, default=4.0)
    f.add_argument("--threads", type=int, default=4)
    f.add_argument("--limit", type=int, default=None)
    c = sub.add_parser("compile", help="raw cache -> parquet tables")
    c.add_argument("--root", type=Path, default=DEFAULT_ROOT)
    a = ap.parse_args(argv)
    if a.cmd == "compile":
        print(json.dumps(compile_store(a.root)))
    if a.cmd == "fetch":
        seasons = list(range(a.from_season, (a.to_season or current_season()) + 1))
        print(json.dumps(build_fetch(a.root, seasons, a.rps, a.threads, a.limit)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
