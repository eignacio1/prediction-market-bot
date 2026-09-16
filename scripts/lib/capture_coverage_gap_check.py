"""GG-280 detector: generalized capture-coverage gap check, superseding the
NFL-only GG-276 detector (formerly nfl_capture_gap_check.py). Alarms when any
in-season day-of-week produces zero rows for a sport that deploy/cron.conf's
own archiver lines say should have captured that day -- covering the *shape*
of the GG-261 (Wednesday/NFL) and GG-276 (Saturday/NFL) failure, not just the
one instance already found and fixed.

Day-of-week coverage per sport is derived by parsing deploy/cron.conf's own
archive_market_prices.py lines, not hardcoded -- a hardcoded day-of-week set
would just be a second copy of the exact defect this detector exists to catch
(a coverage set that silently drifts out of sync with the real cron block).
Season-months per sport are still a hardcoded fact (cron itself fires 365
days/year regardless of season; there's no way to derive "season" from a
crontab), analogous to the original script's NFL_SEASON_MONTHS.

Alarm-only -- always exits 0; prints a finding either way so a clean day is
visibly confirmed rather than merely absent of output (same pattern as
CLAUDE.md's GG-108 NBA-log correction).

Usage: python3 scripts/lib/capture_coverage_gap_check.py [YYYY-MM-DD ...]
No args -> checks yesterday (UTC) only, the most recent day guaranteed complete.
"""
import json
import re
import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

ARCHIVE_DIR = "exp_output/PRICE_ARCHIVE"
CRON_CONF = "deploy/cron.conf"

# Sport -> series-ticker prefix used to attribute an archived row to that sport.
SPORT_SERIES_PREFIX = {
    "NFL": "KXNFL",
    "MLB": "KXMLB",
}

# Sport -> calendar months considered in-season. This cannot be derived from
# cron.conf (the cron lines fire unconditionally year-round); it is the one
# fact this detector still hardcodes per sport.
SPORT_SEASON_MONTHS = {
    "NFL": {9, 10, 11, 12, 1, 2},   # regular season through Super Bowl
    "MLB": {3, 4, 5, 6, 7, 8, 9, 10},
}

# cron.conf's day-of-week field: 0=Sun..6=Sat. date.weekday() is 0=Mon..6=Sun.
def cron_dow(d: date) -> int:
    return (d.weekday() + 1) % 7


def parse_cron_coverage(cron_conf_path: str) -> dict[str, set[int]]:
    """Returns {sport: {cron-dow ints covered by an archive_market_prices.py
    line whose --series list includes that sport's prefix}}. A line whose dow
    field is '*' covers all 7 days for every sport it lists."""
    coverage: dict[str, set[int]] = {s: set() for s in SPORT_SERIES_PREFIX}
    text = Path(cron_conf_path).read_text()
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if "archive_market_prices.py" not in line:
            continue
        fields = line.split()
        if len(fields) < 5:
            continue
        dow_field = fields[4]
        if dow_field == "*":
            dows = set(range(7))
        else:
            dows = set()
            for part in dow_field.split(","):
                part = part.strip()
                if part.isdigit():
                    dows.add(int(part))
        series_match = re.search(r"--series\s+([^-][^\n]*?)(?:\s+--\S|$)", line)
        series_list = series_match.group(1).split() if series_match else []
        for sport, prefix in SPORT_SERIES_PREFIX.items():
            if any(s.startswith(prefix) for s in series_list):
                coverage[sport] |= dows
    return coverage


def check_day(d: date, coverage: dict[str, set[int]]) -> tuple[bool, list[str]]:
    """Returns (any_alarm, messages)."""
    dow = cron_dow(d)
    due_sports = [
        sport for sport, dows in coverage.items()
        if dow in dows and d.month in SPORT_SEASON_MONTHS.get(sport, set())
    ]
    path = f"{ARCHIVE_DIR}/prices_{d.isoformat()}.jsonl"

    if not due_sports:
        return False, [f"  {d.isoformat()}: no sport due for capture on this day-of-week/month (not a concern)"]

    counts = {sport: 0 for sport in due_sports}
    total = 0
    try:
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
                ticker = str(row.get("series_ticker", ""))
                for sport in due_sports:
                    if ticker.startswith(SPORT_SERIES_PREFIX[sport]):
                        counts[sport] += 1
    except FileNotFoundError:
        msgs = [
            f"  *** CAPTURE-GAP ALERT: {d.isoformat()} — no price archive file found at all, "
            f"but {', '.join(due_sports)} due for capture (cron.conf dow={dow}). "
            f"See GG-261/GG-276 (same failure shape). ***"
        ]
        return True, msgs

    any_alarm = False
    msgs = []
    for sport in due_sports:
        if counts[sport] == 0:
            any_alarm = True
            msgs.append(
                f"  *** CAPTURE-GAP ALERT: {d.isoformat()} has {total} total rows but ZERO {sport} rows "
                f"despite cron.conf covering dow={dow} for {sport}. See GG-261/GG-276 (same failure shape) "
                f"-- check deploy/cron.conf's {sport} block day-of-week coverage against this date's weekday. ***"
            )
        else:
            msgs.append(f"  {d.isoformat()}: {sport} total={total} rows={counts[sport]} OK")
    return any_alarm, msgs


def main() -> int:
    if len(sys.argv) > 1:
        days = [date.fromisoformat(a) for a in sys.argv[1:]]
    else:
        days = [(datetime.now(timezone.utc) - timedelta(days=1)).date()]

    coverage = parse_cron_coverage(CRON_CONF)
    any_alarm = False
    for d in days:
        alarm, msgs = check_day(d, coverage)
        any_alarm = any_alarm or alarm
        for m in msgs:
            print(m)

    if any_alarm:
        print("  (alarm-only per operator directive -- exit code unaffected)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
