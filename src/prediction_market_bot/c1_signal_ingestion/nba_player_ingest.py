"""C1 -- NBA player box-score ingestion (W65.1 / EXP-039).

Source: ESPN public ``summary?event=<game_id>`` (site.api.espn.com; reachable from Mac and VPS, stats.nba.com
is 403 from the VPS). One request per completed game, <= 2 requests/s, read-only, no credentials. Game ids come
from the scoreboard store written by ``nba_ingest`` (``data/raw/nba/games_<season>.json``).

Raw per-season files: ``data/raw/nba/players_<season>.json`` (gitignored) ->
``{"season": s, "games": {game_id: {"fetched_at_utc", "start_time_utc", "rows": [...]}}}``.
A row is one player-game: ``player_id, name, team (Kalshi code), home (bool), minutes, points, fga, dnp``.
"""
from __future__ import annotations

import json
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable
from prediction_market_bot.atomic_io import atomic_write_text

from prediction_market_bot.c1_signal_ingestion import nba_ingest as N

SUMMARY = "https://site.api.espn.com/apis/site/v2/sports/basketball/nba/summary?event={gid}"


def _num(x: Any) -> float:
    try:
        return float(x)
    except (TypeError, ValueError):
        return 0.0


def parse_summary(payload: dict[str, Any], home_code: str, away_code: str) -> list[dict[str, Any]]:
    """ESPN summary -> player-game rows. DNP / zero-minute players are kept with ``dnp=True`` (never dropped
    silently) so the feature builder decides what counts as a prior game."""
    rows: list[dict[str, Any]] = []
    for t in payload.get("boxscore", {}).get("players", []):
        code = N.kalshi_code(t["team"].get("abbreviation", ""))
        for block in t.get("statistics", []):
            keys = block.get("keys", [])
            ix = {k: i for i, k in enumerate(keys)}
            for a in block.get("athletes", []):
                if not (a.get("athlete") or {}).get("id"):
                    continue                     # ESPN occasionally lists an athlete entry with no id (unmatchable)
                st = a.get("stats") or []
                dnp = bool(a.get("didNotPlay")) or not st
                fga = 0.0
                if "fieldGoalsMade-fieldGoalsAttempted" in ix and len(st) > ix["fieldGoalsMade-fieldGoalsAttempted"]:
                    fga = _num(st[ix["fieldGoalsMade-fieldGoalsAttempted"]].split("-")[-1])
                mins = _num(st[ix["minutes"]]) if "minutes" in ix and len(st) > ix["minutes"] else 0.0
                pts = _num(st[ix["points"]]) if "points" in ix and len(st) > ix["points"] else 0.0
                rows.append({"player_id": str(a["athlete"]["id"]), "name": a["athlete"].get("displayName", ""),
                             "jersey": str(a["athlete"].get("jersey", "")), "team": code, "home": code == home_code, "minutes": mins, "points": pts,
                             "fga": fga, "dnp": dnp or mins <= 0})
    return rows


def fetch_summary(gid: str, th: N.Throttle, opener: Callable = urllib.request.urlopen, retries: int = 4) -> dict:
    url = SUMMARY.format(gid=gid)
    for attempt in range(retries):
        th.wait()
        try:
            with opener(urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"}), timeout=30) as r:
                return json.loads(r.read())
        except urllib.error.HTTPError as e:
            if e.code == 429:
                th.slow_down()
            if attempt == retries - 1:
                raise
        except (urllib.error.URLError, TimeoutError, OSError):
            if attempt == retries - 1:
                raise
        time.sleep(1 + attempt)
    return {}


def players_path(season: int, root: Path = N.RAW_DIR) -> Path:
    return root / f"players_{season}.json"


def load_players(season: int, root: Path = N.RAW_DIR) -> dict[str, Any]:
    p = players_path(season, root)
    return json.loads(p.read_text()) if p.exists() else {"season": season, "games": {}}


def save_players(store: dict[str, Any], root: Path = N.RAW_DIR) -> None:
    root.mkdir(parents=True, exist_ok=True)
    p = players_path(store["season"], root)
    atomic_write_text(p, json.dumps(store, sort_keys=True))


def backfill_players(season: int, th: N.Throttle, root: Path = N.RAW_DIR, fetch: Callable = fetch_summary,
                     season_types: tuple[int, ...] = (N.REGULAR,)) -> int:
    """Fetch the box score of every completed game in the scoreboard store that is not yet stored.
    Resumable (saves every 50 games). Returns games fetched."""
    games = N.load_season(season, root)["games"]
    store = load_players(season, root)
    n = 0
    for g in sorted(games.values(), key=lambda x: x["start_time_utc"]):
        if not g["completed"] or g["season_type"] not in season_types or g["game_id"] in store["games"]:
            continue
        rows = parse_summary(fetch(g["game_id"], th), g["home"], g["away"])
        store["games"][g["game_id"]] = {"fetched_at_utc": datetime.now(timezone.utc).isoformat(),
                                        "start_time_utc": g["start_time_utc"], "rows": rows}
        n += 1
        if n % 50 == 0:
            save_players(store, root)
    save_players(store, root)
    return n
