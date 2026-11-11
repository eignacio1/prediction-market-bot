"""Fail-closed gate for the off-box MLB feature CSV refresh (W57.1 / GG-489).

Runs the SAME MLB_FEATURE_CSV_CONTRACT that PIPE-05/PIPE-06pre enforce (nothing relaxed) against a
freshly generated CSV, plus a floor on player count. Exit 0 only if the CSV would pass the live
pipelines. The GitHub Actions job pushes to the VPS only after this exits 0.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.parse
import urllib.request
from datetime import date, datetime, timedelta, timezone

import pandas as pd

from prediction_market_bot.c1_signal_ingestion.data_contracts import MLB_FEATURE_CSV_CONTRACT
from prediction_market_bot.c1_signal_ingestion.validators import validate

SCHEDULE_URL = "https://statsapi.mlb.com/api/v1/schedule"
MIN_PLAYERS = 300  # a throttled/partial fetch yielded 121 players; a full roster is ~470-575


def games_in_window(start: date, end: date, fetch=None) -> int | None:
    """Number of MLB games (any type) scheduled in [start, end]; None on any doubt (fail-closed)."""
    params = urllib.parse.urlencode({"sportId": 1, "startDate": start.isoformat(), "endDate": end.isoformat()})
    try:
        if fetch is not None:
            data = fetch(f"{SCHEDULE_URL}?{params}")
        else:
            req = urllib.request.Request(f"{SCHEDULE_URL}?{params}", headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=30) as r:
                data = json.load(r)
        return sum(len(b.get("games", [])) for b in data.get("dates", []))
    except Exception:
        return None


def off_season_skip(halts, window_days: int, today: date, fetch=None) -> str | None:
    """Reason string if the ONLY HALT is staleness and the schedule shows zero games in the
    staleness window (a genuine off-season); None otherwise. Never applies on game days."""
    if not halts or any(getattr(f, "check_type", "") != "staleness_halt" for f in halts):
        return None
    n = games_in_window(today - timedelta(days=window_days), today, fetch)
    if n != 0:
        return None
    return (f"off-season: staleness_halt is the only HALT and the MLB schedule shows 0 games in "
            f"{today - timedelta(days=window_days)}..{today}; CSV not regenerated or pushed")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("csv")
    ap.add_argument("--meta-out", required=True)
    ap.add_argument("--skip-off-season", action="store_true",
                    help="exit 0 with a written skip reason when staleness is the only HALT and the schedule has 0 games in the window")
    args = ap.parse_args()

    df = pd.read_csv(args.csv)
    result = validate(df, MLB_FEATURE_CSV_CONTRACT)
    halts = [f for f in result.failures if getattr(f.severity, "name", str(f.severity)).upper() == "HALT"]
    players = int(df["player_id"].nunique())
    max_date = str(df["game_date"].astype(str).max())
    for f in result.failures:
        print(f"contract: {f.check_type} [{getattr(f.severity, 'name', f.severity)}] {f.reason}")
    if halts and args.skip_off_season:
        reason = off_season_skip(halts, MLB_FEATURE_CSV_CONTRACT.freshness_halt_days or 7, datetime.now(timezone.utc).date())
        if reason:
            print(f"SKIP: {reason}")
            out = os.environ.get("GITHUB_OUTPUT")
            if out:
                with open(out, "a") as fh:
                    fh.write("skip=true\n")
            summ = os.environ.get("GITHUB_STEP_SUMMARY")
            if summ:
                with open(summ, "a") as fh:
                    fh.write(f"SKIPPED (clean): {reason}\n")
            return 0
    if halts:
        print(f"REFUSE: {len(halts)} HALT-severity contract failure(s); VPS CSV left untouched", file=sys.stderr)
        return 1
    if players < MIN_PLAYERS:
        print(f"REFUSE: only {players} players (< {MIN_PLAYERS}); partial fetch; VPS CSV left untouched", file=sys.stderr)
        return 1
    meta = {
        "generated_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "rows": len(df),
        "players": players,
        "max_game_date": max_date,
        "source": "github-actions mlb_features_sync.yml",
    }
    with open(args.meta_out, "w") as fh:
        json.dump(meta, fh)
    print(f"OK {meta}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
