"""EXP-037 / T-608 (MLB): pull MLB team-game results + probable starters from the public Stats API.

Read-only public data, <=1 req/s. Writes one parquet of games (all game types kept, with a game_type
column; training uses regular season 'R' only). Also used with --upcoming to refresh scheduled games.

  PYTHONPATH=src:. python3 scripts/fetch_mlb_game_history.py --first 2015 --last 2026
"""
from __future__ import annotations

import argparse
import sys
import time
from datetime import date, timedelta
from pathlib import Path

import pandas as pd
import requests

ROOT = Path(__file__).resolve().parent.parent
CACHE = ROOT / "exp_output" / "MLB_GAME" / "cache_w47"
URL = "https://statsapi.mlb.com/api/v1/schedule"


KEEP_TYPES = frozenset("RFDLW")
RETRY_STATUS = (406, 429, 500, 502, 503, 504)
BACKOFF_S = (5, 15, 45, 90)
MAX_GAP_DAYS = 21                     # refresh window cap: a wider gap means the cache needs a re-seed, not a patch


def _rows(games: list[dict]) -> list[dict]:
    rows = []
    for g in games:
        h, a = g["teams"]["home"], g["teams"]["away"]
        rows.append({
            "game_pk": g["gamePk"], "game_type": g["gameType"], "season": int(g["season"]),
            "game_date": g["officialDate"], "start_utc": g["gameDate"],
            "status": g["status"]["abstractGameState"], "double_header": g.get("doubleHeader", "N"),
            "home": h["team"].get("abbreviation"), "away": a["team"].get("abbreviation"),
            "home_score": h.get("score"), "away_score": a.get("score"),
            "home_sp": (h.get("probablePitcher") or {}).get("id"),
            "away_sp": (a.get("probablePitcher") or {}).get("id"),
        })
    return rows


def fetch_range(start: str, end: str, game_types: str) -> list[dict]:
    r = requests.get(URL, params={"sportId": 1, "startDate": start, "endDate": end,
                                  "gameType": game_types, "hydrate": "probablePitcher,team"}, timeout=60)
    r.raise_for_status()
    return _rows([g for d in r.json().get("dates", []) for g in d.get("games", [])])


def fetch_day(day: str, sleep=time.sleep) -> list[dict]:
    """One date, no gameType param. GG-470: from the VPS the edge answers 406 to gameType= and to range queries
    intermittently (per-IP, flips over minutes); a plain date= query gets through often enough with retry.
    Game types are filtered client-side. Raises after the last retry -- a caller must never proceed on a miss."""
    for wait in (*BACKOFF_S, None):
        r = requests.get(URL, params={"sportId": 1, "date": day, "hydrate": "probablePitcher,team"}, timeout=60)
        if r.status_code not in RETRY_STATUS:
            r.raise_for_status()
            games = [g for d in r.json().get("dates", []) for g in d.get("games", []) if g["gameType"] in KEEP_TYPES]
            return _rows(games)
        if wait is None:
            raise RuntimeError(f"stats api {r.status_code} for date={day} after {len(BACKOFF_S)} retries")
        sleep(wait)
    raise AssertionError("unreachable")


def refresh_recent(out: Path, base: Path, season: int, today: date, back: int = 5, ahead: int = 3,
                   fetch=fetch_day, sleep=time.sleep) -> int:
    """Patch the current season's games from per-date queries: base = existing `out` if present else the
    season rows of `base`. Rows for every refreshed date are replaced wholesale (a game moved by a postponement
    shows up under its new date). Writes a FULL-season frame, since the runner swaps whole seasons."""
    src = out if out.exists() else base
    if not src.exists():
        raise RuntimeError(f"no games cache at {out} or {base} -- seed it first (scripts/fetch_mlb_game_history.py)")
    df = pd.read_parquet(src)
    df = df[df.season == season]
    if df.empty:
        raise RuntimeError(f"no season={season} rows in {src} -- seed it first")
    start = today - timedelta(days=back)              # only used when the cache holds no Final game yet
    final = df[df.status == "Final"]
    if len(final):        # earlier days already hold their results; every extra request is extra 406 exposure
        start = date.fromisoformat(str(final.game_date.max())) - timedelta(days=1)
    if (today - start).days > MAX_GAP_DAYS:
        raise RuntimeError(f"cache last Final {final.game_date.max()} is >{MAX_GAP_DAYS}d behind {today} -- re-seed")
    days = [(start + timedelta(days=i)).isoformat() for i in range((today - start).days + 1 + ahead)]
    new: list[dict] = []
    for d in days:
        new += fetch(d)
        sleep(1.1)
    keep = df[~df.game_date.isin(days)]
    merged = pd.concat([keep, pd.DataFrame(new)], ignore_index=True).drop_duplicates("game_pk", keep="last")
    for c in ("home_score", "away_score", "home_sp", "away_sp"):     # range path yields float64 (nullable ids/scores)
        merged[c] = merged[c].astype("float64")
    merged.to_parquet(out)
    print(f"refreshed {days[0]}..{days[-1]}: {len(new)} games fetched, {len(merged)} season rows -> {out}")
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--first", type=int, default=2015)
    ap.add_argument("--last", type=int, default=date.today().year)
    ap.add_argument("--out", default=str(CACHE / "games.parquet"))
    ap.add_argument("--recent", action="store_true", help="per-date patch of the current season (VPS-safe)")
    ap.add_argument("--base", default=str(CACHE / "games.parquet"))
    ap.add_argument("--season", type=int, default=date.today().year)
    ap.add_argument("--today", default=None, help="YYYY-MM-DD override (testing only)")
    a = ap.parse_args(argv)
    CACHE.mkdir(parents=True, exist_ok=True)
    if a.recent:
        try:
            return refresh_recent(Path(a.out), Path(a.base), a.season,
                                  date.fromisoformat(a.today) if a.today else date.today())
        except (RuntimeError, requests.RequestException) as e:
            print(f"REFRESH FAILED: {e}", file=sys.stderr)
            return 1
    rows: list[dict] = []
    for yr in range(a.first, a.last + 1):
        for lo, hi in ((f"{yr}-03-01", f"{yr}-06-30"), (f"{yr}-07-01", f"{yr}-11-30")):
            rows += fetch_range(lo, hi, "R,F,D,L,W")
            time.sleep(1.1)
        print(yr, len(rows), flush=True)
    df = pd.DataFrame(rows).drop_duplicates("game_pk")
    df.to_parquet(a.out)
    print("wrote", a.out, len(df))
    return 0


if __name__ == "__main__":
    sys.exit(main())
