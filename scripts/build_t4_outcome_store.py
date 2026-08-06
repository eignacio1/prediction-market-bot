#!/usr/bin/env python3
"""T-421 — decoupled outcome-measurement store for T4 MLB.

Reads t4_mlb_cycle_log.jsonl (the forecast leg) and, per unique ticker,
resolves the true outcome (actual hits in that game) via the read-only
resolution helpers already in run_resolve_mlb.py — imported, never edited,
per T-421's hard scope fence:

    NO changes to c5_execution/paper_trader.py
    NO changes to c4_risk_engine/risk.py
    NO changes to run_t4_mlb_live.py's write path
    NO epoch bump, NO sizing change, NO ADR accepted

This script only reads the cycle log and writes a NEW, independent,
gitignored JSONL store (logs/t4_mlb_outcome_store.jsonl) — it never touches
the ledger or the portfolio file.

Join key: ticker (not the raw (player_id, game_date, threshold) tuple —
see 05_RESEARCH_EXPERIMENTS/DECOUPLED_MEASUREMENT_STORE_2026-08-05.md for the
uniqueness verification that motivated this choice: the raw tuple collides
194/2,132 times because the cycle log's own `game_date` field is wrong on
70.2% of rows, GG-164 — it is stamped from UTC wall-clock date-at-write-time,
not the game's true date. `ticker` uniquely encodes date+time+teams+player+
threshold, including doubleheader disambiguation via an embedded start-time/
game-number token, and is used both as the store's primary key and as the
source of the corrected game_date passed to the resolution functions.

Resolution failures are first-class data (requirement 4): every unresolved
ticker's record carries an `attempts` list — one entry per source tried
(MLB_R, MLB_P, ESPN), each with its result and any captured stderr detail
(e.g. an HTTP 403) — plus an `attempt_count`. Nothing is silently dropped.

Idempotent/resumable (requirement 3): tickers already `resolved: true` are
never re-fetched. Unresolved tickers are retried on every run and gain a new
attempts entry each time. The store is checkpointed to disk periodically so
an interrupted run does not lose completed work.
"""
from __future__ import annotations

import argparse
import contextlib
import io
import json
import os
import re
import subprocess
import sys
import tempfile
import time
from pathlib import Path

os.environ.setdefault("BOT_ENV", "paper")  # import-time gate in run_resolve_mlb; read-only import, no writes

_REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO_ROOT / "src"))

from prediction_market_bot.run_resolve_mlb import (  # noqa: E402
    _espn_fetch_hits,
    _fetch_mlb_hits,
)

_DEFAULT_CYCLE_LOG = _REPO_ROOT / "logs" / ".vps_t4_mlb_cycle_log_cache.jsonl"
_DEFAULT_STORE = _REPO_ROOT / "logs" / "t4_mlb_outcome_store.jsonl"
_VPS_ALIAS = "prediction-market-vps"
_VPS_CYCLE_LOG_PATH = "/opt/prediction-market-bot/logs/t4_mlb_cycle_log.jsonl"

_CHECKPOINT_EVERY = 25  # tickers attempted, not just resolved

# KXMLBHIT-{YY}{MON}{DD}{HHMM}{AWAYTEAM}{HOMETEAM}[G{n}]-{TEAM}{PLAYERCODE}-{THRESHOLD}
_MONTHS = {
    "JAN": "01", "FEB": "02", "MAR": "03", "APR": "04", "MAY": "05", "JUN": "06",
    "JUL": "07", "AUG": "08", "SEP": "09", "OCT": "10", "NOV": "11", "DEC": "12",
}
_TICKER_DATE_RE = re.compile(r"^KXMLBHIT-(\d{2})([A-Z]{3})(\d{2})(\d{4})")


def ticker_game_date(ticker: str) -> str | None:
    """Derive the true game date from a ticker's embedded date token (GG-164 fix)."""
    m = _TICKER_DATE_RE.match(ticker)
    if not m:
        return None
    yy, mon, dd, _hhmm = m.groups()
    month = _MONTHS.get(mon)
    if month is None:
        return None
    return f"20{yy}-{month}-{dd}"


def pull_vps_cycle_log(dest: Path) -> None:
    tmp = dest.with_suffix(dest.suffix + ".tmp")
    subprocess.run(
        ["scp", "-q", f"{_VPS_ALIAS}:{_VPS_CYCLE_LOG_PATH}", str(tmp)],
        check=True,
        timeout=120,
    )
    tmp.replace(dest)


def load_cycle_log(path: Path) -> list[dict]:
    rows = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            rows.append(json.loads(line))
    return rows


def group_by_ticker(rows: list[dict]) -> dict[str, dict]:
    """One record per unique ticker; many cycle-log rows fold into one ticker."""
    grouped: dict[str, dict] = {}
    for row in rows:
        ticker = row.get("ticker")
        if not ticker:
            continue
        g = grouped.get(ticker)
        if g is None:
            derived_date = ticker_game_date(ticker)
            g = {
                "ticker": ticker,
                "player_id": row.get("player_id"),
                "player_name": row.get("player_name"),
                "threshold": row.get("threshold"),
                "game_date": derived_date if derived_date else row.get("game_date"),
                "date_source": "ticker" if derived_date else "raw_fallback",
                "n_cycle_rows": 0,
                "has_forecast": False,
            }
            grouped[ticker] = g
        g["n_cycle_rows"] += 1
        if row.get("p_t4") is not None:
            g["has_forecast"] = True
    return grouped


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
            store[rec["ticker"]] = rec
    return store


def write_store(path: Path, store: dict[str, dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(dir=str(path.parent), prefix=".outcome_store_", suffix=".tmp")
    try:
        with os.fdopen(fd, "w") as f:
            for ticker in sorted(store.keys()):
                f.write(json.dumps(store[ticker], sort_keys=True) + "\n")
        os.replace(tmp_name, path)
    except BaseException:
        with contextlib.suppress(OSError):
            os.remove(tmp_name)
        raise


def _call_with_captured_stderr(fn, *args):
    """Run a resolution helper, capturing stderr so a 403/exception is visible
    even though the helper itself only prints and returns None on failure."""
    buf = io.StringIO()
    try:
        with contextlib.redirect_stderr(buf):
            result = fn(*args)
        error = None
    except Exception as exc:  # helpers are designed not to raise, but be defensive
        result = None
        error = f"{type(exc).__name__}: {exc}"
    captured = buf.getvalue().strip()
    detail = error or (captured[-500:] if captured else None)
    return result, detail


def attempt_resolution(rec: dict) -> None:
    """One resolution pass: MLB_R -> MLB_P -> ESPN, first-class attempt records."""
    player_id = rec["player_id"]
    game_date = rec["game_date"]
    player_name = rec.get("player_name")
    now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

    attempts = rec.setdefault("attempts", [])

    hits, detail = _call_with_captured_stderr(_fetch_mlb_hits, player_id, game_date, "R")
    attempts.append({"source": "MLB_R", "at": now, "result": hits, "detail": detail})
    source = "MLB_R" if hits is not None else None

    if hits is None:
        hits, detail = _call_with_captured_stderr(_fetch_mlb_hits, player_id, game_date, "P")
        attempts.append({"source": "MLB_P", "at": now, "result": hits, "detail": detail})
        source = "MLB_P" if hits is not None else None

    if hits is None and player_name:
        hits, detail = _call_with_captured_stderr(_espn_fetch_hits, player_name, game_date)
        attempts.append({"source": "ESPN", "at": now, "result": hits, "detail": detail})
        source = "ESPN" if hits is not None else None
    elif hits is None:
        attempts.append({"source": "ESPN", "at": now, "result": None, "detail": "skipped: no player_name"})

    rec["last_attempted_at"] = now
    rec.setdefault("first_attempted_at", now)
    rec["attempt_count"] = len(attempts)

    if hits is not None:
        rec["resolved"] = True
        rec["actual_hits"] = hits
        rec["resolution_source"] = source
    else:
        rec["resolved"] = False


def run_backfill(cycle_log_path: Path, store_path: Path, limit: int | None) -> dict:
    rows = load_cycle_log(cycle_log_path)
    grouped = group_by_ticker(rows)
    store = load_store(store_path)

    tickers = sorted(grouped.keys())
    if limit is not None:
        tickers = tickers[:limit]

    attempted_this_run = 0
    resolved_this_run = 0

    for i, ticker in enumerate(tickers, 1):
        meta = grouped[ticker]
        rec = store.get(ticker)
        if rec is None:
            rec = dict(meta)
            store[ticker] = rec
        else:
            # keep store's own attempt history; refresh cheap metadata from the log
            rec["n_cycle_rows"] = meta["n_cycle_rows"]
            rec["has_forecast"] = meta["has_forecast"] or rec.get("has_forecast", False)

        if rec.get("resolved"):
            continue

        attempt_resolution(rec)
        attempted_this_run += 1
        if rec.get("resolved"):
            resolved_this_run += 1

        if attempted_this_run % _CHECKPOINT_EVERY == 0:
            write_store(store_path, store)
            print(
                f"  ...checkpoint {i}/{len(tickers)} tickers scanned, "
                f"{attempted_this_run} attempted this run, {resolved_this_run} newly resolved",
                file=sys.stderr,
            )

    write_store(store_path, store)

    total_tickers = len(store)
    resolved_total = sum(1 for r in store.values() if r.get("resolved"))
    unresolved_total = total_tickers - resolved_total

    return {
        "cycle_log_rows": len(rows),
        "unique_tickers": total_tickers,
        "resolved_total": resolved_total,
        "unresolved_total": unresolved_total,
        "attempted_this_run": attempted_this_run,
        "resolved_this_run": resolved_this_run,
    }


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--cycle-log", type=Path, default=_DEFAULT_CYCLE_LOG)
    ap.add_argument("--store", type=Path, default=_DEFAULT_STORE)
    ap.add_argument("--pull", action="store_true", help="scp a fresh cycle log from the VPS first")
    ap.add_argument("--limit", type=int, default=None, help="only process the first N tickers (testing)")
    args = ap.parse_args()

    if args.pull:
        print(f"Pulling {_VPS_CYCLE_LOG_PATH} from {_VPS_ALIAS} -> {args.cycle_log}", file=sys.stderr)
        pull_vps_cycle_log(args.cycle_log)

    summary = run_backfill(args.cycle_log, args.store, args.limit)

    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
