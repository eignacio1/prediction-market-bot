"""C1 -- NBA ingestion (W58.2 / EXP-038).

Source: ESPN public NBA scoreboard (``site.api.espn.com``), reachable from Mac and VPS
(HTTP 200 both, 2026-10-06; stats.nba.com / cdn.nba.com 403 from the VPS). One request per
game date: the endpoint rejects date ranges. Read-only, no credentials, <= 2 requests/s.

Raw per-season files live under ``data/raw/nba/`` (gitignored). Every file carries the
``fetched_at_utc`` of each date so the information cutoff can be audited. All team codes are
normalised to Kalshi's 3-letter spelling; an unknown ESPN abbreviation raises, never drops
(the NHL 2-letter-code drop, GG-403, must not recur).
"""
from __future__ import annotations

import json
import time
import urllib.error
import urllib.request
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Callable, Optional

BASE = "https://site.api.espn.com/apis/site/v2/sports/basketball/nba/scoreboard"
RAW_DIR = Path("data/raw/nba")
PRESEASON, REGULAR = 1, 2  # ESPN season.type; 3 = playoffs, 5 = play-in

KALSHI_TEAMS = (
    "ATL BOS BKN CHA CHI CLE DAL DEN DET GSW HOU IND LAC LAL MEM MIA MIL MIN NOP NYK OKC "
    "ORL PHI PHX POR SAC SAS TOR UTA WAS").split()

# ESPN abbreviation -> Kalshi code (identity where they agree).
ESPN_TO_KALSHI = {c: c for c in KALSHI_TEAMS}
ESPN_TO_KALSHI.update({"GS": "GSW", "NY": "NYK", "NO": "NOP", "SA": "SAS", "UTAH": "UTA", "WSH": "WAS"})


class UnknownTeam(ValueError):
    pass


def kalshi_code(espn_abbr: str) -> str:
    try:
        return ESPN_TO_KALSHI[espn_abbr]
    except KeyError:
        raise UnknownTeam(f"unmapped ESPN team abbreviation {espn_abbr!r}") from None


def parse_event(ev: dict[str, Any]) -> Optional[dict[str, Any]]:
    """One ESPN event -> flat game row, or None when it has no two-team competition."""
    comp = (ev.get("competitions") or [{}])[0]
    teams = {c["homeAway"]: c for c in comp.get("competitors", [])}
    if "home" not in teams or "away" not in teams:
        return None
    st = ev["status"]["type"]
    # Exhibitions against non-NBA clubs and all-star games carry no NBA code: skip them. A regular-season
    # game with an unmapped code is a mapping bug and raises (never silently dropped).
    mapped = [c["team"].get("abbreviation", "") in ESPN_TO_KALSHI for c in teams.values()]
    if not all(mapped) and (ev["season"]["type"] != REGULAR or not any(mapped)):
        return None
    done = bool(st.get("completed"))

    def score(c: dict[str, Any]) -> Optional[int]:
        return int(c["score"]) if done and c.get("score") not in (None, "") else None

    return {
        "game_id": str(ev["id"]),
        "start_time_utc": ev["date"],
        "season": ev["season"]["year"],       # ending year: 2024 == 2023-24
        "season_type": ev["season"]["type"],
        "state": st["name"],
        "completed": done,
        "neutral_site": bool(comp.get("neutralSite")),
        "home": kalshi_code(teams["home"]["team"].get("abbreviation", "")),
        "away": kalshi_code(teams["away"]["team"].get("abbreviation", "")),
        "home_score": score(teams["home"]),
        "away_score": score(teams["away"]),
    }


class Throttle:
    def __init__(self, interval_s: float = 0.5) -> None:
        self.interval_s, self._last = interval_s, 0.0

    def wait(self) -> None:
        d = self.interval_s - (time.monotonic() - self._last)
        if d > 0:
            time.sleep(d)
        self._last = time.monotonic()

    def slow_down(self) -> None:
        self.interval_s = min(self.interval_s * 2, 8.0)


def fetch_date(d: date, th: Throttle, opener: Callable = urllib.request.urlopen, retries: int = 4) -> list[dict]:
    url = f"{BASE}?dates={d:%Y%m%d}&limit=300"
    for attempt in range(retries):
        th.wait()
        try:
            with opener(urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"}), timeout=30) as r:
                payload = json.loads(r.read())
            return [g for g in (parse_event(e) for e in payload.get("events", [])) if g]
        except urllib.error.HTTPError as e:
            if e.code == 429:
                th.slow_down()
            if attempt == retries - 1:
                raise
        except (urllib.error.URLError, TimeoutError):
            if attempt == retries - 1:
                raise
        time.sleep(1 + attempt)
    return []


def season_path(season: int, root: Path = RAW_DIR) -> Path:
    return root / f"games_{season}.json"


def load_season(season: int, root: Path = RAW_DIR) -> dict[str, Any]:
    p = season_path(season, root)
    return json.loads(p.read_text()) if p.exists() else {"season": season, "dates": {}, "games": {}}


def save_season(store: dict[str, Any], root: Path = RAW_DIR) -> None:
    root.mkdir(parents=True, exist_ok=True)
    p = season_path(store["season"], root)
    tmp = p.with_suffix(".tmp")
    tmp.write_text(json.dumps(store, sort_keys=True))
    tmp.replace(p)


def season_dates(season: int) -> list[date]:
    """Oct 1 of the season's starting year through Jun 30 of its ending year."""
    d, end = date(season - 1, 10, 1), date(season, 6, 30)
    return [d + timedelta(days=i) for i in range((end - d).days + 1)]


def backfill_season(season: int, th: Throttle, root: Path = RAW_DIR, today: Optional[date] = None,
                    refresh_days: int = 3, fetch: Callable = fetch_date) -> int:
    """Fetch every missing date; re-fetch the trailing ``refresh_days`` so late finals land. Returns dates fetched."""
    today = today or datetime.now(timezone.utc).date()
    store = load_season(season, root)
    n = 0
    for d in season_dates(season):
        if d > today:
            break
        key = d.isoformat()
        if key in store["dates"] and (today - d).days > refresh_days:
            continue
        for g in fetch(d, th):
            store["games"][g["game_id"]] = g
        store["dates"][key] = datetime.now(timezone.utc).isoformat()
        n += 1
        if n % 25 == 0:
            save_season(store, root)
    save_season(store, root)
    return n


def completed_regular(store: dict[str, Any]) -> list[dict[str, Any]]:
    rows = [g for g in store["games"].values() if g["completed"] and g["season_type"] == REGULAR
            and g["home_score"] is not None]
    return sorted(rows, key=lambda g: (g["start_time_utc"], g["game_id"]))
