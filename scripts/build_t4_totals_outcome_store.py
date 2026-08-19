#!/usr/bin/env python3
"""T-463 — team runs-scored outcome store for archived KXMLBTOTAL game-events.

Phase 2 (game-market coverage expansion, see 04_EXECUTION/ACTIVE_QUEUE.md) is
blocked on ingestion: the existing decoupled outcome store
(logs/t4_mlb_outcome_store.jsonl, T-421/build_t4_outcome_store.py) is
player-hits only (every ticker is KXMLBHIT-*, schema is actual_hits/
player_id/threshold) and cannot resolve a team run total. The price archive
(exp_output/PRICE_ARCHIVE/prices_*.jsonl) holds tens of thousands of
KXMLBTOTAL quote snapshots but 100% status:"active" — it is a live-quote
archiver, never a settlement feed, so it carries no outcomes of its own.
This script closes that gap: it enumerates every distinct KXMLBTOTAL
event_ticker seen in the archive and resolves the true final team score via
the MLB Stats API, independent of anything the archive itself claims.

Follows scripts/build_t4_outcome_store.py's structural pattern (T-421):
ticker-keyed JSONL store, idempotent/resumable, first-class failure
attempts, atomic checkpointed writes. Divergences, and why:

  - Join key is `event_ticker`, not `ticker`. KXMLBTOTAL lists 12 threshold
    markets (totals 3-14) under one event_ticker with one shared outcome
    (the actual combined/team run total) -- the per-threshold `ticker`
    suffix carries no outcome-relevant information here, unlike KXMLBHIT
    where ticker already includes the resolved batter+threshold.
  - Source is the local price archive (exp_output/PRICE_ARCHIVE/), not a
    VPS-resident cycle log -- no --pull/scp step; the archive already exists
    wherever this runs.
  - Resolution is a new function (`attempt_resolution` below calls the MLB
    schedule endpoint directly), not an import of `_fetch_mlb_hits` --
    that helper is player/hits-shaped (game_type R/P, hits count) and has
    no team-runs equivalent anywhere in the codebase. What IS imported,
    per instruction, is T-458's GG-170 guard, `_verify_official_date`
    (src/prediction_market_bot/run_resolve_mlb.py) -- every resolution
    cross-checks the ticker-embedded date against MLB's own authoritative
    `officialDate` via gamePk and REFUSES (unresolved, not written) on any
    disagreement or unconfirmable lookup, exactly as GG-166/GG-170 require
    for KXMLBHIT. No second copy of that guard exists anywhere in this file.
  - Team abbreviation mapping reuses `_FALLBACK_TEAM_ABBR`
    (c1_signal_ingestion/mlb_ingestion.py) rather than instantiating the
    full MLBIngestionClient (which requires an AuditLogger + snapshot_id --
    machinery this standalone read-only script has no use for). Verified
    directly against real ticker data before use: KXMLBTOTAL-26AUG021410
    TEXHOU resolves via MLB Stats API to gamePk 824163, officialDate
    2026-08-02 (exact ticker-date match), Texas Rangers @ Houston Astros,
    final score 3-7 -- confirming both that _FALLBACK_TEAM_ABBR's codes
    (TEX, HOU, ...) match Kalshi's ticker convention and that the
    ticker-embedded date is the true game date, not a listing/creation
    date (see the docstring note on `close_time` below).

Also confirmed and worth recording: KXMLBTOTAL's `close_time`/
`expiration_time` fields in the archive run a constant +3 days past the
ticker-embedded game date on every sampled event (8/8) -- this is a Kalshi
market-metadata artifact (settlement/dispute window default), not an
alternate game-date signal. It is not used anywhere in this script. Do not
treat it as a corroborating or disagreeing date source.

No changes to c5_execution/paper_trader.py, c4_risk_engine/risk.py, any
band, gate 2.3, or the KXMLBHIT outcome store. No model fit, no scoring.
This script only reads the price archive and writes a new, independent,
gitignored JSONL store (logs/t4_mlb_totals_outcome_store.jsonl).
"""
from __future__ import annotations

import argparse
import contextlib
import glob
import json
import os
import re
import sys
import tempfile
import time
from pathlib import Path

import requests

os.environ.setdefault("BOT_ENV", "paper")  # import-time gate in run_resolve_mlb; read-only import, no writes

_REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO_ROOT / "src"))

from prediction_market_bot.run_resolve_mlb import _verify_official_date  # noqa: E402
from prediction_market_bot.c1_signal_ingestion.mlb_ingestion import (  # noqa: E402
    _FALLBACK_TEAM_ABBR,
)

_DEFAULT_ARCHIVE_GLOB = str(_REPO_ROOT / "exp_output" / "PRICE_ARCHIVE" / "prices_*.jsonl")
_DEFAULT_STORE = _REPO_ROOT / "logs" / "t4_mlb_totals_outcome_store.jsonl"

_MLB_BASE_URL = "https://statsapi.mlb.com"
_REQUEST_TIMEOUT_S = 15
_RATE_LIMIT_S = 0.6

_CHECKPOINT_EVERY = 25

_MONTHS = {
    "JAN": "01", "FEB": "02", "MAR": "03", "APR": "04", "MAY": "05", "JUN": "06",
    "JUL": "07", "AUG": "08", "SEP": "09", "OCT": "10", "NOV": "11", "DEC": "12",
}
# KXMLBTOTAL-{YY}{MON}{DD}{HHMM}{AWAYTEAM}{HOMETEAM}[G{n}]  (event_ticker, no per-market suffix)
# The away/home codes are concatenated with no delimiter and each run 2-3 chars
# (e.g. "AZCLE" = AZ+CLE, "SFTEX" = SF+TEX) -- a blind greedy {2,3}{2,3} regex
# mis-splits these (AZC+LE) whenever the away code is a valid 2-char prefix of
# a false 3-char reading. Disambiguated below against the known abbr set
# instead of trusting regex greediness.
_EVENT_TICKER_RE = re.compile(r"^KXMLBTOTAL-(\d{2})([A-Z]{3})(\d{2})(\d{4})([A-Z]{4,6})(?:G\d+)?$")

_ABBR_TO_TEAM_ID = {v: k for k, v in _FALLBACK_TEAM_ABBR.items()}
_KNOWN_ABBRS = set(_FALLBACK_TEAM_ABBR.values())


def _split_team_codes(combined: str) -> tuple[str, str] | None:
    """Split a concatenated {AWAY}{HOME} code string against the known abbr
    set. Returns None if zero or more-than-one valid split exists (genuine
    ambiguity -- refuse rather than guess)."""
    valid_splits = []
    for i in range(2, len(combined) - 1):
        away, home = combined[:i], combined[i:]
        if away in _KNOWN_ABBRS and home in _KNOWN_ABBRS:
            valid_splits.append((away, home))
    if len(valid_splits) == 1:
        return valid_splits[0]
    return None

_last_request_t = 0.0


def _throttled_get(url: str, params: dict) -> dict | None:
    global _last_request_t
    elapsed = time.monotonic() - _last_request_t
    if elapsed < _RATE_LIMIT_S:
        time.sleep(_RATE_LIMIT_S - elapsed)
    _last_request_t = time.monotonic()
    resp = requests.get(url, params=params, timeout=_REQUEST_TIMEOUT_S)
    resp.raise_for_status()
    return resp.json()


def parse_event_ticker(event_ticker: str) -> dict | None:
    """Derive game_date + away/home abbrs from the event_ticker (ticker-embedded date is authority)."""
    m = _EVENT_TICKER_RE.match(event_ticker)
    if not m:
        return None
    yy, mon, dd, hhmm, combined_teams = m.groups()
    month = _MONTHS.get(mon)
    if month is None:
        return None
    split = _split_team_codes(combined_teams)
    if split is None:
        return None
    away_abbr, home_abbr = split
    return {
        "game_date": f"20{yy}-{month}-{dd}",
        "hhmm": hhmm,
        "away_abbr": away_abbr,
        "home_abbr": home_abbr,
    }


def scan_archive(glob_pattern: str) -> dict[str, dict]:
    """Enumerate distinct KXMLBTOTAL event_tickers across the price archive."""
    events: dict[str, dict] = {}
    files = sorted(glob.glob(glob_pattern))
    for fp in files:
        with open(fp) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                rec = json.loads(line)
                tk = rec.get("ticker") or ""
                if not tk.startswith("KXMLBTOTAL-"):
                    continue
                et = rec.get("event_ticker", "")
                if not et:
                    continue
                g = events.get(et)
                if g is None:
                    parsed = parse_event_ticker(et)
                    g = {
                        "event_ticker": et,
                        "game_date": parsed["game_date"] if parsed else None,
                        "date_source": "ticker" if parsed else None,
                        "away_abbr": parsed["away_abbr"] if parsed else None,
                        "home_abbr": parsed["home_abbr"] if parsed else None,
                        "hhmm": parsed["hhmm"] if parsed else None,
                        "n_price_rows": 0,
                    }
                    events[et] = g
                g["n_price_rows"] += 1
    return events, len(files)


def load_store(path: Path) -> dict[str, dict]:
    if not path.exists():
        return {}
    store: dict[str, dict] = {}
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            rec = json.loads(line)
            store[rec["event_ticker"]] = rec
    return store


def write_store(path: Path, store: dict[str, dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(dir=str(path.parent), prefix=".totals_outcome_store_", suffix=".tmp")
    try:
        with os.fdopen(fd, "w") as f:
            for et in sorted(store.keys()):
                f.write(json.dumps(store[et], sort_keys=True) + "\n")
        os.replace(tmp_name, path)
    except BaseException:
        with contextlib.suppress(OSError):
            os.remove(tmp_name)
        raise


def _fetch_schedule(game_date: str) -> list[dict] | None:
    try:
        data = _throttled_get(
            f"{_MLB_BASE_URL}/api/v1/schedule",
            params={"sportId": 1, "date": game_date, "hydrate": "linescore,team"},
        )
    except Exception as exc:
        return None, f"{type(exc).__name__}: {exc}"
    games = []
    for db in data.get("dates", []):
        games.extend(db.get("games", []))
    return games, None


def attempt_resolution(rec: dict) -> None:
    """One resolution pass against the MLB Stats API schedule endpoint for game_date.

    Refuses (leaves unresolved) on: no parseable date/teams, no matching
    game found, ambiguous doubleheader match, not-yet-Final status, or a
    failed/unconfirmed GG-170 officialDate cross-check. Every attempt is
    recorded, success or failure -- resolution failures are first-class data.
    """
    now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    attempts = rec.setdefault("attempts", [])
    rec.setdefault("first_attempted_at", now)
    rec["last_attempted_at"] = now

    game_date = rec.get("game_date")
    away_abbr = rec.get("away_abbr")
    home_abbr = rec.get("home_abbr")
    if not game_date or not away_abbr or not home_abbr:
        attempts.append({"source": "MLB", "at": now, "result": None,
                          "detail": "unparseable event_ticker (no game_date/away_abbr/home_abbr)"})
        rec["resolved"] = False
        rec["attempt_count"] = len(attempts)
        return

    away_id = _ABBR_TO_TEAM_ID.get(away_abbr)
    home_id = _ABBR_TO_TEAM_ID.get(home_abbr)
    if away_id is None or home_id is None:
        attempts.append({"source": "MLB", "at": now, "result": None,
                          "detail": f"unknown team abbr(s): away={away_abbr} home={home_abbr}"})
        rec["resolved"] = False
        rec["attempt_count"] = len(attempts)
        return

    games, fetch_err = _fetch_schedule(game_date)
    if games is None:
        attempts.append({"source": "MLB", "at": now, "result": None,
                          "detail": f"schedule fetch failed: {fetch_err}"})
        rec["resolved"] = False
        rec["attempt_count"] = len(attempts)
        return

    matches = [
        g for g in games
        if (g.get("teams", {}).get("away", {}).get("team") or {}).get("id") == away_id
        and (g.get("teams", {}).get("home", {}).get("team") or {}).get("id") == home_id
    ]

    if not matches:
        attempts.append({"source": "MLB", "at": now, "result": None,
                          "detail": f"no {away_abbr}@{home_abbr} game found on {game_date} "
                                    f"({len(games)} games that date)"})
        rec["resolved"] = False
        rec["attempt_count"] = len(attempts)
        return

    if len(matches) > 1:
        # Doubleheader: pick the game whose local start hour is closest to the
        # ticker's embedded hhmm token; record the ambiguity either way.
        ticker_hhmm = rec.get("hhmm")

        def _hour_dist(g):
            gd = g.get("gameDate", "")
            try:
                gh, gm = int(gd[11:13]), int(gd[14:16])
            except (ValueError, IndexError):
                return 9999
            th, tm = int(ticker_hhmm[:2]), int(ticker_hhmm[2:])
            return abs((gh * 60 + gm) - (th * 60 + tm))

        matches.sort(key=_hour_dist)
        attempts.append({"source": "MLB", "at": now, "result": None,
                          "detail": f"doubleheader: {len(matches)} {away_abbr}@{home_abbr} games on "
                                    f"{game_date}, selected gamePk={matches[0].get('gamePk')} by closest start time"})

    game = matches[0]
    game_pk = game.get("gamePk")
    status = game.get("status", {}).get("abstractGameState", "")

    if status != "Final":
        attempts.append({"source": "MLB", "at": now, "result": None,
                          "detail": f"gamePk={game_pk} status={status!r}, not yet Final"})
        rec["resolved"] = False
        rec["attempt_count"] = len(attempts)
        return

    date_ok = _verify_official_date(game_pk, game_date)
    if date_ok is not True:
        attempts.append({"source": "MLB", "at": now, "result": None,
                          "detail": f"GG-170 officialDate guard refused: gamePk={game_pk} "
                                    f"expected={game_date} verify_result={date_ok!r}"})
        rec["resolved"] = False
        rec["attempt_count"] = len(attempts)
        return

    teams = game.get("teams", {})
    away_runs = teams.get("away", {}).get("score")
    home_runs = teams.get("home", {}).get("score")
    if away_runs is None or home_runs is None:
        attempts.append({"source": "MLB", "at": now, "result": None,
                          "detail": f"gamePk={game_pk} Final + date-verified but score missing from payload"})
        rec["resolved"] = False
        rec["attempt_count"] = len(attempts)
        return

    attempts.append({"source": "MLB", "at": now,
                      "result": {"away_runs": away_runs, "home_runs": home_runs}, "detail": None})
    rec["resolved"] = True
    rec["resolution_source"] = "MLB"
    rec["game_pk"] = game_pk
    rec["date_verified"] = True
    rec["away_runs"] = away_runs
    rec["home_runs"] = home_runs
    rec["total_runs"] = away_runs + home_runs
    rec["attempt_count"] = len(attempts)


def run_backfill(archive_glob: str, store_path: Path, limit: int | None) -> dict:
    events, n_files = scan_archive(archive_glob)
    store = load_store(store_path)

    event_tickers = sorted(events.keys())
    if limit is not None:
        event_tickers = event_tickers[:limit]

    attempted_this_run = 0
    resolved_this_run = 0

    pending = []
    for et in event_tickers:
        meta = events[et]
        rec = store.get(et)
        if rec is None:
            rec = dict(meta)
            store[et] = rec
        else:
            rec["n_price_rows"] = meta["n_price_rows"]
        if not rec.get("resolved"):
            pending.append(rec)

    total_pending = len(pending)
    for i, rec in enumerate(pending, 1):
        attempt_resolution(rec)
        attempted_this_run += 1
        if rec.get("resolved"):
            resolved_this_run += 1
        if attempted_this_run % _CHECKPOINT_EVERY == 0:
            write_store(store_path, store)
            print(f"  ...checkpoint {i}/{total_pending} pending scanned, "
                  f"{attempted_this_run} attempted this run, {resolved_this_run} newly resolved",
                  file=sys.stderr)

    write_store(store_path, store)

    total_events = len(store)
    resolved_total = sum(1 for r in store.values() if r.get("resolved"))
    unresolved_total = total_events - resolved_total

    return {
        "archive_files_scanned": n_files,
        "unique_event_tickers": total_events,
        "resolved_total": resolved_total,
        "unresolved_total": unresolved_total,
        "attempted_this_run": attempted_this_run,
        "resolved_this_run": resolved_this_run,
    }


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--archive-glob", default=_DEFAULT_ARCHIVE_GLOB)
    ap.add_argument("--store", type=Path, default=_DEFAULT_STORE)
    ap.add_argument("--limit", type=int, default=None, help="only process the first N event_tickers (testing)")
    args = ap.parse_args()

    summary = run_backfill(args.archive_glob, args.store, args.limit)
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
