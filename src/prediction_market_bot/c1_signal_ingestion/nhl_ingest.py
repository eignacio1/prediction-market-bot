"""C1 — NHL ingestion (T-607 / EXP-036).

Source: the public NHL web API (``api-web.nhle.com/v1``), reachable from Mac and VPS
(verified 2026-10-02, HTTP 200 on both). Read-only, no credentials.

Every stored payload carries ``fetched_at_utc`` so the information cutoff can be audited.
Raw payloads live under ``data/raw/nhl/`` (gitignored). Throttle: <= 1 request/s,
halved on any 429 (operator rule for this wave).

Pure parsing functions (``parse_game_row``) take dicts so tests need no network.
"""
from __future__ import annotations

import json
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Iterable, Optional
from prediction_market_bot.atomic_io import atomic_write_text

BASE = "https://api-web.nhle.com/v1"
RAW_DIR = Path("data/raw/nhl")
REG_SEASON = 2  # gameType: 1 preseason, 2 regular, 3 playoffs

TEAMS = [
    "ANA", "BOS", "BUF", "CAR", "CBJ", "CGY", "CHI", "COL", "DAL", "DET", "EDM", "FLA",
    "LAK", "MIN", "MTL", "NJD", "NSH", "NYI", "NYR", "OTT", "PHI", "PIT", "SEA", "SJS",
    "STL", "TBL", "TOR", "UTA", "VAN", "VGK", "WPG", "WSH",
]
# Franchise relocation: ARI -> UTA from 2024-25; 2021-23 seasons use ARI.
SEASON_TEAM_OVERRIDES = {2021: {"UTA": "ARI"}, 2022: {"UTA": "ARI"}, 2023: {"UTA": "ARI"}}
# SEA began 2021-22; all five target seasons have 32 clubs (UTA/ARI swap).


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


@dataclass
class Throttle:
    """<=1 req/s; interval doubles (rate halves) on every 429, relaxes slowly after."""
    interval_s: float = 1.0
    _last: float = 0.0
    base_s: float = 1.0

    def wait(self) -> None:
        dt = time.monotonic() - self._last
        if dt < self.interval_s:
            time.sleep(self.interval_s - dt)
        self._last = time.monotonic()

    def on_429(self) -> None:
        self.interval_s = min(self.interval_s * 2.0, 60.0)

    def on_ok(self) -> None:
        self.interval_s = max(self.base_s, self.interval_s * 0.98)


class NhlHttpError(RuntimeError):
    def __init__(self, url: str, status: int, body: str = ""):
        super().__init__(f"{status} for {url}: {body[:200]}")
        self.url, self.status = url, status


def http_get_json(url: str, throttle: Throttle, retries: int = 4,
                  opener: Optional[Callable[[str], tuple[int, bytes]]] = None) -> dict:
    """GET JSON with throttle + 429 backoff. ``opener`` is the test seam."""
    last: Optional[Exception] = None
    for attempt in range(retries):
        throttle.wait()
        try:
            if opener is not None:
                status, body = opener(url)
            else:
                req = urllib.request.Request(url, headers={"User-Agent": "pmbot-nhl-shadow/1"})
                with urllib.request.urlopen(req, timeout=25) as r:
                    status, body = r.status, r.read()
        except urllib.error.HTTPError as e:
            status, body = e.code, e.read() or b""
        except Exception as e:  # network error
            last = e
            time.sleep(2 ** attempt)
            continue
        if status == 429:
            throttle.on_429()
            continue
        if status == 200:
            throttle.on_ok()
            return json.loads(body)
        if status in (404,):
            raise NhlHttpError(url, status, body.decode("utf8", "replace"))
        last = NhlHttpError(url, status, body.decode("utf8", "replace"))
        time.sleep(2 ** attempt)
    raise last if last else NhlHttpError(url, 0, "exhausted retries")


# ---------------------------------------------------------------- parsing (pure)
def season_start_year(season: int) -> int:
    """20252026 -> 2025"""
    return season // 10000


def parse_game_row(box: dict, fetched_at_utc: str) -> Optional[dict]:
    """One finished-game record from a boxscore payload; None if not FINAL/OFF.

    Records: scores split into regulation/OT/SO, outcome type, shots, starter and
    goalies used, special-teams goals, PIM. ``end_period_type`` in {REG, OT, SO}.
    """
    if box.get("gameState") not in ("FINAL", "OFF"):
        return None
    if box.get("gameType") != REG_SEASON:
        return None
    home, away = box["homeTeam"], box["awayTeam"]
    end = (box.get("gameOutcome") or {}).get("lastPeriodType") or box["periodDescriptor"]["periodType"]
    out: dict[str, Any] = {
        "game_id": box["id"], "season": box["season"], "game_date": box["gameDate"],
        "start_time_utc": box["startTimeUTC"], "venue": (box.get("venue") or {}).get("default"),
        "neutral_site": bool(box.get("neutralSite", False)),
        "home": home["abbrev"], "away": away["abbrev"],
        "home_score": home["score"], "away_score": away["score"],
        "home_sog": home.get("sog"), "away_sog": away.get("sog"),
        "end_period_type": end, "fetched_at_utc": fetched_at_utc,
    }
    for side, team in (("home", home), ("away", away)):
        pbg = (box.get("playerByGameStats") or {}).get(f"{side}Team") or {}
        goalies = pbg.get("goalies") or []
        starter = next((g for g in goalies if g.get("starter")), None)
        out[f"{side}_starter_id"] = starter["playerId"] if starter else None
        out[f"{side}_goalies_used"] = [g["playerId"] for g in goalies if _toi_s(g.get("toi")) > 0]
        out[f"{side}_pp_goals_against_by_goalie"] = sum(int(g.get("powerPlayGoalsAgainst") or 0) for g in goalies)
        out[f"{side}_pim"] = sum(int(p.get("pim") or 0) for k in ("forwards", "defense", "goalies") for p in pbg.get(k, []))
        skaters = pbg.get("forwards", []) + pbg.get("defense", [])
        out[f"{side}_pp_goals"] = sum(int(p.get("powerPlayGoals") or 0) for p in skaters)
        out[f"{side}_goalie_sa"] = sum(int(g.get("shotsAgainst") or 0) for g in goalies)
        out[f"{side}_goalie_saves"] = sum(int(g.get("saves") or 0) for g in goalies)
    # Regulation+OT goal totals as Kalshi totals them: SO adds ONE goal to the winner.
    # NHL boxscore scores already include the SO winner's +1; keep a clean split anyway.
    if end == "SO":
        winner_home = out["home_score"] > out["away_score"]
        out["home_score_ex_so"] = out["home_score"] - (1 if winner_home else 0)
        out["away_score_ex_so"] = out["away_score"] - (0 if winner_home else 1)
    else:
        out["home_score_ex_so"], out["away_score_ex_so"] = out["home_score"], out["away_score"]
    return out


def _toi_s(toi: Optional[str]) -> int:
    if not toi or ":" not in toi:
        return 0
    m, s = toi.split(":")[:2]
    return int(m) * 60 + int(s)


def parse_schedule_game(g: dict) -> dict:
    """Schedule-level record (works for future, postponed and final games)."""
    return {
        "game_id": g["id"], "season": g["season"], "game_type": g["gameType"],
        "game_date": g["gameDate"], "start_time_utc": g["startTimeUTC"],
        "state": g["gameState"], "schedule_state": g.get("gameScheduleState", "OK"),
        "home": g["homeTeam"]["abbrev"], "away": g["awayTeam"]["abbrev"],
        "neutral_site": bool(g.get("neutralSite", False)),
        "venue": (g.get("venue") or {}).get("default"),
    }


def is_postponed(sched: dict) -> bool:
    return sched.get("schedule_state") in ("PPD", "CNCL", "SUSP") or sched.get("state") in ("PPD", "CNCL")


# ---------------------------------------------------------------- fetching / store
def club_season_url(team: str, season: int) -> str:
    return f"{BASE}/club-schedule-season/{team}/{season}{season + 1}"


def fetch_season_schedule(season: int, throttle: Throttle,
                          opener: Optional[Callable] = None,
                          teams: Optional[Iterable[str]] = None) -> dict[int, dict]:
    """All regular-season games of a season keyed by game_id (deduped across clubs)."""
    games: dict[int, dict] = {}
    overrides = SEASON_TEAM_OVERRIDES.get(season, {})
    for t in (teams or TEAMS):
        t = overrides.get(t, t)
        try:
            d = http_get_json(club_season_url(t, season), throttle, opener=opener)
        except NhlHttpError as e:
            if e.status == 404:
                continue
            raise
        for g in d.get("games", []):
            if g.get("gameType") == REG_SEASON:
                games[g["id"]] = parse_schedule_game(g)
    return games


def box_path(game_id: int, root: Path = RAW_DIR) -> Path:
    return root / "boxscore" / f"{game_id}.json"


def fetch_boxscore(game_id: int, throttle: Throttle, root: Path = RAW_DIR,
                   opener: Optional[Callable] = None, refresh: bool = False) -> Optional[dict]:
    """Fetch+store a boxscore wrapper {fetched_at_utc, payload}. Returns None on 404."""
    p = box_path(game_id, root)
    if p.exists() and not refresh:
        return json.loads(p.read_text())
    try:
        payload = http_get_json(f"{BASE}/gamecenter/{game_id}/boxscore", throttle, opener=opener)
    except NhlHttpError as e:
        if e.status == 404:
            return None
        raise
    wrapper = {"fetched_at_utc": utcnow().isoformat(), "payload": payload}
    p.parent.mkdir(parents=True, exist_ok=True)
    atomic_write_text(p, json.dumps(wrapper))
    return wrapper


def load_games(root: Path = RAW_DIR) -> list[dict]:
    """All parsed finished-game rows from the local raw store, sorted by start time."""
    rows = []
    for p in (root / "boxscore").glob("*.json"):
        w = json.loads(p.read_text())
        r = parse_game_row(w["payload"], w["fetched_at_utc"])
        if r:
            rows.append(r)
    rows.sort(key=lambda r: (r["start_time_utc"], r["game_id"]))
    return rows


def save_schedule(season: int, games: dict[int, dict], root: Path = RAW_DIR) -> Path:
    p = root / "schedule" / f"{season}.json"
    p.parent.mkdir(parents=True, exist_ok=True)
    atomic_write_text(p, json.dumps({"fetched_at_utc": utcnow().isoformat(), "games": list(games.values())}))
    return p


def load_schedule(season: int, root: Path = RAW_DIR) -> list[dict]:
    p = root / "schedule" / f"{season}.json"
    return json.loads(p.read_text())["games"] if p.exists() else []
