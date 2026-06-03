#!/usr/bin/env python3
"""
scripts/poll_and_resolve_g1.py — Finals Game 1 Auto-Resolution

Polls ESPN every 60–90 seconds until the Finals game reaches STATUS_FINAL,
then automatically runs T-109 with no operator action:
  1. run_resolve_local.py      — resolve paper positions via nba_api (must run locally)
  2. fetch_kalshi_prices.py --portfolio  — sync VPS pregame files for EXP-017

Start before game tip-off (8:30 PM EDT = 5:30 PM PDT = 00:30 UTC Jun 4):
    cd /Users/earlignacio/Documents/Claude/Projects/Prediction\ Markets
    source .venv311/bin/activate
    nohup python3 scripts/poll_and_resolve_g1.py >> logs/auto_resolve_g1.log 2>&1 &
    echo "PID: $!"

Output goes to logs/auto_resolve_g1.log.
Script exits automatically after T-109 completes, or at 07:30 UTC fallback.

Fallback guarantee:
    If ESPN status detection fails for any reason, resolution is forced at
    07:30 UTC Jun 4 (= 3:30 AM EDT = well after any Finals game ends).
"""
from __future__ import annotations

import os
import subprocess
import sys
import time
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import requests

_PROJECT_ROOT = Path(__file__).parent.parent

_ESPN_SCOREBOARD  = "https://site.api.espn.com/apis/site/v2/sports/basketball/nba/scoreboard"
_ESPN_HEADERS     = {"User-Agent": "Mozilla/5.0"}

_STATUS_SCHEDULED   = "STATUS_SCHEDULED"
_STATUS_IN_PROGRESS = "STATUS_IN_PROGRESS"
_STATUS_FINAL       = "STATUS_FINAL"

# Fallback: run T-109 at the NEXT occurrence of 07:30 UTC after script start.
# Computed at startup so "start at 19:00 UTC → fallback = 07:30 UTC next morning."
# 07:30 UTC = 3:30 AM EDT — no Finals game runs past this.
_FALLBACK_HOUR_UTC = 7
_FALLBACK_MIN_UTC  = 30

# After this UTC hour, a STATUS_FINAL game that wasn't tracked through
# IN_PROGRESS (script started late / missed the transition) still triggers.
# 02:00 UTC = 10:00 PM EDT — earliest any Finals game could be FINAL.
_LATE_DETECTION_HOUR_UTC = 2


def _compute_fallback_dt() -> datetime:
    """Next occurrence of 07:30 UTC from now (always in the future)."""
    now = datetime.now(tz=timezone.utc)
    candidate = now.replace(hour=_FALLBACK_HOUR_UTC, minute=_FALLBACK_MIN_UTC,
                            second=0, microsecond=0)
    if candidate <= now:
        candidate += timedelta(days=1)
    return candidate


def _log(msg: str) -> None:
    ts = datetime.now(tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    print(f"[{ts}] {msg}", flush=True)


def _get_statuses() -> dict[str, str]:
    """Return {game_id: status_name} for today's NBA games (using local date)."""
    today = date.today().strftime("%Y%m%d")
    try:
        r = requests.get(
            _ESPN_SCOREBOARD,
            params={"dates": today, "limit": 20},
            headers=_ESPN_HEADERS,
            timeout=10,
        )
        r.raise_for_status()
        events = r.json().get("events", [])
        return {
            e["id"]: e.get("status", {}).get("type", {}).get("name", "UNKNOWN")
            for e in events
        }
    except Exception as exc:
        _log(f"ESPN fetch error: {exc}")
        return {}


def _run_t109() -> int:
    """
    Run the T-109 standing resolution procedure.
    Returns 0 on full success, non-zero if either step failed.
    """
    env_paper = {**os.environ, "BOT_ENV": "paper", "PYTHONPATH": "src"}
    env_base  = {**os.environ, "PYTHONPATH": "src"}
    cwd = str(_PROJECT_ROOT)

    _log("T-109 step 1/2: run_resolve_local.py ...")
    r1 = subprocess.run(
        [sys.executable, "src/prediction_market_bot/run_resolve_local.py"],
        cwd=cwd,
        env=env_paper,
    )
    _log(f"  exit code: {r1.returncode}")

    _log("T-109 step 2/2: fetch_kalshi_prices.py --portfolio ...")
    r2 = subprocess.run(
        [sys.executable, "src/prediction_market_bot/fetch_kalshi_prices.py", "--portfolio"],
        cwd=cwd,
        env=env_base,
    )
    _log(f"  exit code: {r2.returncode}")

    combined = r1.returncode | r2.returncode
    _log(f"T-109 complete — combined exit code: {combined}")
    return combined


def main() -> None:
    (_PROJECT_ROOT / "logs").mkdir(exist_ok=True)
    fallback_dt = _compute_fallback_dt()
    _log("poll_and_resolve_g1.py started — monitoring ESPN for STATUS_FINAL")
    _log(f"Fallback trigger: {fallback_dt.strftime('%Y-%m-%dT%H:%M:%SZ')} UTC")

    seen_in_progress: set[str] = set()

    while True:
        now = datetime.now(tz=timezone.utc)

        # Fallback: force resolution at the guaranteed post-game time
        if now >= fallback_dt:
            _log("FALLBACK TIME REACHED — running T-109 regardless of ESPN status")
            sys.exit(_run_t109())

        statuses = _get_statuses()

        if not statuses:
            _log("No games found — retrying in 60s")
            time.sleep(60)
            continue

        for game_id, status in statuses.items():
            if status == _STATUS_IN_PROGRESS:
                if game_id not in seen_in_progress:
                    _log(f"Game {game_id}: STATUS_IN_PROGRESS — tracking")
                    seen_in_progress.add(game_id)

            elif status == _STATUS_FINAL:
                if game_id in seen_in_progress:
                    # Normal path: tracked game went SCHEDULED→IN_PROGRESS→FINAL
                    _log(f"Game {game_id}: STATUS_FINAL — triggering T-109")
                    sys.exit(_run_t109())
                elif now.hour >= _LATE_DETECTION_HOUR_UTC:
                    # Script started after tip-off; missed IN_PROGRESS; still trigger
                    _log(
                        f"Game {game_id}: STATUS_FINAL (late detection, "
                        f"{now.hour:02d}:{now.minute:02d} UTC ≥ "
                        f"{_LATE_DETECTION_HOUR_UTC:02d}:00) — triggering T-109"
                    )
                    sys.exit(_run_t109())

        any_live = any(s == _STATUS_IN_PROGRESS for s in statuses.values())
        interval = 90 if any_live else 60
        _log(f"Statuses: {dict(statuses)} | next poll in {interval}s")
        time.sleep(interval)


if __name__ == "__main__":
    main()
