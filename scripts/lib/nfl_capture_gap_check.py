"""GG-276 detector: zero KXNFL rows in a given day's price-archive file, during
NFL season, is an alarm. Alarm-only -- always exits 0; prints a finding either
way so a clean day is visibly confirmed rather than merely absent of output
(same pattern as CLAUDE.md's GG-108 NBA-log correction).

Usage: python3 scripts/lib/nfl_capture_gap_check.py [YYYY-MM-DD ...]
No args -> checks yesterday (UTC) only, the most recent day guaranteed complete.
"""
import json
import sys
from datetime import date, datetime, timedelta, timezone

ARCHIVE_DIR = "exp_output/PRICE_ARCHIVE"
NFL_SEASON_MONTHS = {9, 10, 11, 12, 1, 2}  # regular season through Super Bowl


def is_nfl_season(d: date) -> bool:
    return d.month in NFL_SEASON_MONTHS


def check_day(d: date) -> tuple[bool, str]:
    """Returns (alarm, message)."""
    path = f"{ARCHIVE_DIR}/prices_{d.isoformat()}.jsonl"
    in_season = is_nfl_season(d)
    try:
        kxnfl = 0
        total = 0
        with open(path) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                total += 1
                try:
                    row = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if str(row.get("series_ticker", "")).startswith("KXNFL"):
                    kxnfl += 1
    except FileNotFoundError:
        if in_season:
            return True, f"  *** GG-276-CLASS ALERT: {d.isoformat()} — no price archive file found at all (NFL season). ***"
        return False, f"  {d.isoformat()}: no archive file (off-season, not a concern)"

    if not in_season:
        return False, f"  {d.isoformat()}: total={total} kxnfl={kxnfl} (off-season by month, not a concern either way)"

    if kxnfl == 0:
        return True, (
            f"  *** GG-276-CLASS ALERT: {d.isoformat()} has {total} total rows but ZERO KXNFL rows "
            f"during NFL season. See GG-276 (2026-09-12 missing-Saturday cron gap) -- this is either "
            f"a repeat of that exact gap or a new capture failure. Check deploy/cron.conf's NFL block "
            f"day-of-week coverage against this date's weekday before assuming it's already fixed. ***"
        )
    return False, f"  {d.isoformat()}: total={total} kxnfl={kxnfl} OK"


def main() -> int:
    if len(sys.argv) > 1:
        days = [date.fromisoformat(a) for a in sys.argv[1:]]
    else:
        days = [(datetime.now(timezone.utc) - timedelta(days=1)).date()]

    any_alarm = False
    for d in days:
        alarm, msg = check_day(d)
        any_alarm = any_alarm or alarm
        print(msg)

    if any_alarm:
        print("  (alarm-only per operator directive -- exit code unaffected)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
