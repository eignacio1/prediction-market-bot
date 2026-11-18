"""W118.4 / B-102: disk growth and the days-to-90% alarm.

The box sat at 87% disk on 2026-11-18 and deploy/healthcheck.sh FAILs at 90%; a FAIL blocks every install (Hard Rule 14). A fixed
threshold only tells you after the fact, so this adds the rate: from the box's own history, how many days until 90%?

History sources (alarm-only; reads files, the only write is one sample line when ``--record`` is passed, as the healthcheck does):
  * logs/disk_samples.jsonl -- one {"ts","used_bytes","total_bytes","pct"} line per healthcheck run (this module writes it).
  * logs/health.log         -- every daily healthcheck run prints a date line then ``[OK|WARN|FAIL] disk NN% used``; this is the
                               history that already exists on the box today (integer percent, so coarse).
Samples win when they span >= 1 day; otherwise the health.log percentages are used.

WARN fires when the 7-day growth puts the disk at 90% within 14 days. A flat or shrinking disk, or too little history, is never an alarm
(reported as such, not hidden). Standalone: ``python -m prediction_market_bot.disk_guard <project dir> [--record]``.
"""
from __future__ import annotations

import json
import os
import re
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Iterable, Optional

FAIL_PCT = 90.0
WARN_WITHIN_DAYS = 14.0
WINDOW_DAYS = 7.0
MIN_SPAN_DAYS = 1.0
SAMPLES_REL = "logs/disk_samples.jsonl"
HEALTH_LOG_REL = "logs/health.log"
_HEALTH_HDR = "=== VPS Health Check"
_DISK_LINE = re.compile(r"^\[(?:OK|WARN|FAIL)\] disk (\d{1,3})% used")
Sample = tuple  # (datetime aware UTC, pct float, used_bytes int | None)


def _aware(dt: datetime) -> datetime:
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


def _parse_ts(s) -> Optional[datetime]:
    if not isinstance(s, str):
        return None
    s = s.strip().replace("Z", "+00:00")
    try:
        return _aware(datetime.fromisoformat(s))
    except ValueError:
        return None


def parse_health_log(text: str) -> list:
    """(ts, pct, None) per healthcheck run that printed a disk line. The date is the line after the ``=== VPS Health Check`` header."""
    out, ts, want_date = [], None, False
    for ln in text.splitlines():
        if ln.startswith(_HEALTH_HDR):
            ts, want_date = None, True
            continue
        if want_date:
            ts, want_date = _parse_ts(ln), False
            continue
        m = _DISK_LINE.match(ln)
        if m and ts is not None:
            out.append((ts, float(m.group(1)), None))
            ts = None  # one disk line per run
    return out


def parse_samples(text: str) -> list:
    out = []
    for ln in text.splitlines():
        try:
            r = json.loads(ln)
        except ValueError:
            continue
        ts = _parse_ts(r.get("ts")) if isinstance(r, dict) else None
        if ts is None or not isinstance(r.get("pct"), (int, float)):
            continue
        out.append((ts, float(r["pct"]), r.get("used_bytes") if isinstance(r.get("used_bytes"), int) else None))
    return out


def growth(samples: Iterable, now: datetime, window_days: float = WINDOW_DAYS) -> Optional[dict]:
    """Pct points per day over the window, first to last sample (None when under MIN_SPAN_DAYS of history or < 2 samples)."""
    now = _aware(now)
    pts = sorted((s for s in samples if now - timedelta(days=window_days) <= s[0] <= now), key=lambda s: s[0])
    if len(pts) < 2:
        return None
    first, last = pts[0], pts[-1]
    span = (last[0] - first[0]).total_seconds() / 86400.0
    if span < MIN_SPAN_DAYS:
        return None
    out = {"first_ts": first[0], "last_ts": last[0], "span_days": span, "n": len(pts),
           "pct_per_day": (last[1] - first[1]) / span}
    if first[2] is not None and last[2] is not None:
        out["bytes_per_day"] = (last[2] - first[2]) / span
    return out


def days_to(threshold_pct: float, current_pct: float, pct_per_day: Optional[float]) -> Optional[float]:
    """Days until ``threshold_pct`` at a constant rate; 0 when already there; None when flat / shrinking / unknown."""
    if current_pct >= threshold_pct:
        return 0.0
    if pct_per_day is None or pct_per_day <= 0:
        return None
    return (threshold_pct - current_pct) / pct_per_day


def current_usage(proj: Path) -> dict:
    """Same percentage ``df -P`` prints (used / (used + avail), rounded up) plus the bytes behind it."""
    fake = os.environ.get("PMBOT_DISK_FAKE_PCT")      # tests/test_w118_4_disk.py only (same convention as the healthcheck's PMBOT_* overrides)
    if fake:
        return {"used_bytes": int(float(fake) * 1e9), "total_bytes": int(100e9), "avail_bytes": int((100 - float(fake)) * 1e9),
                "pct": float(fake)}
    st = os.statvfs(str(proj))
    total, free, avail = st.f_blocks * st.f_frsize, st.f_bfree * st.f_frsize, st.f_bavail * st.f_frsize
    used = total - free
    denom = used + avail
    pct = (-(-used * 100 // denom)) if denom else 0
    return {"used_bytes": used, "total_bytes": total, "avail_bytes": avail, "pct": float(pct)}


def load_history(proj: Path) -> tuple:
    """(samples_series, health_log_series) -- each may be empty."""
    def rd(rel):
        p = proj / rel
        try:
            return p.read_text(errors="replace") if p.exists() else ""
        except OSError:
            return ""
    return parse_samples(rd(SAMPLES_REL)), parse_health_log(rd(HEALTH_LOG_REL))


def assess(proj: Path, now: Optional[datetime] = None, usage: Optional[dict] = None) -> dict:
    now = _aware(now or datetime.now(timezone.utc))
    usage = usage or current_usage(proj)
    samples, health = load_history(proj)
    g, source = growth(samples, now), "disk_samples"
    if g is None:
        g, source = growth(health, now), "health_log"
    rate = g["pct_per_day"] if g else None
    d90 = days_to(FAIL_PCT, usage["pct"], rate)
    return {"now_pct": usage["pct"], "usage": usage, "growth": g, "source": source if g else None,
            "pct_per_day": rate, "days_to_90": d90,
            "warn": d90 is not None and d90 <= WARN_WITHIN_DAYS and usage["pct"] < FAIL_PCT}


def render(a: dict) -> str:
    g = a["growth"]
    if g is None:
        return "OK: disk %d%% used; not enough history for a growth rate yet (need >= 1 day of samples)" % a["now_pct"]
    rate = "%+.2f pct/day over %.1f d (%d samples, %s)" % (a["pct_per_day"], g["span_days"], g["n"], a["source"])
    if a["days_to_90"] is None:
        return "OK: disk %d%% used, %s - flat or shrinking, no 90%% date" % (a["now_pct"], rate)
    if a["now_pct"] >= FAIL_PCT:
        return "OK: disk %d%% used is at or past 90%% (the FAIL line says so); %s" % (a["now_pct"], rate)
    msg = "disk %d%% used, %s -> 90%% in %.1f days" % (a["now_pct"], rate, a["days_to_90"])
    return ("WARN: " if a["warn"] else "OK: ") + msg + (" (under %d days)" % WARN_WITHIN_DAYS if a["warn"] else "")


def record(proj: Path, now: datetime, usage: dict) -> None:
    p = proj / SAMPLES_REL
    row = {"ts": _aware(now).strftime("%Y-%m-%dT%H:%M:%SZ"), "pct": usage["pct"],
           "used_bytes": usage["used_bytes"], "total_bytes": usage["total_bytes"]}
    with open(p, "a", encoding="utf-8") as f:
        f.write(json.dumps(row) + "\n")


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    rec = "--record" in argv
    args = [a for a in argv if a != "--record"]
    proj = Path(args[0]) if args else Path.cwd()
    now = datetime.now(timezone.utc)
    usage = current_usage(proj)
    a = assess(proj, now, usage)         # the assessment reads history first, so this run's sample is not its own baseline
    print(render(a))
    if rec:
        try:
            record(proj, now, usage)
        except OSError as e:
            print("sample not recorded: %s" % e)
    return 0


if __name__ == "__main__":
    sys.exit(main())
