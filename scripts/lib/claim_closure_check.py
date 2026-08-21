#!/usr/bin/env python3
"""
claim_closure_check.py — GG-199 / GG-188 class: detect SESSION_CLAIMS.md claims
with no matching CLOSED row for the same T-number.

GG-188 found this blind spot twice (T-463, T-465) and named the fix "Block I" —
this is that assertion. Root-cause note (GG-177): do NOT match rows by exact
timestamp equality (branch-creation time and claim-command time differ by
seconds-to-minutes, guaranteeing false negatives). This matches purely by
extracted T-NNN token and row order instead.

Scope note: the "CLOSED — ..." body convention was adopted on 2026-08-07
(first row: T-430). Claims before that date never used the convention and
would flood this check with false positives if included (a dry run against
the full file with no cutoff flagged 108/149 T-numbers). CUTOFF below is that
adoption date, not an arbitrary window.
"""
from __future__ import annotations

import re
from datetime import datetime, timezone
from pathlib import Path

CUTOFF = datetime(2026, 8, 7, tzinfo=timezone.utc)
BOUND_OTHER_T = 3  # distinct other T-numbers claimed after this one's last row

_ROW_RE = re.compile(r"^\|\s*(?P<ts>[^|]*)\|\s*(?P<idfield>[^|]*)\|\s*(?P<body>.*)\|\s*$")


def _parse_rows(lines: list[str]):
    rows = []
    for i, line in enumerate(lines):
        if not line.startswith("|"):
            continue
        stripped = line.strip()
        if stripped.startswith("| Timestamp") or set(stripped) <= {"|", "-", " "}:
            continue
        m = _ROW_RE.match(line)
        if not m:
            continue
        ts_raw = m.group("ts").strip()
        idfield = m.group("idfield")
        body = m.group("body").strip().lstrip("*").strip()
        t_ids = set(re.findall(r"T-\d+", idfield))
        if not t_ids:
            continue
        is_closed = body.startswith("CLOSED")
        try:
            ts = datetime.strptime(ts_raw[:19], "%Y-%m-%dT%H:%M:%S").replace(tzinfo=timezone.utc)
        except ValueError:
            ts = None
        rows.append((i, ts, t_ids, is_closed))
    return rows


def find_unclosed_claims(text: str, cutoff: datetime = CUTOFF, bound_other_t: int = BOUND_OTHER_T):
    """Return a sorted list of (t_number, first_line_no, other_t_count) for
    claims first seen at/after `cutoff` with no CLOSED row and at least
    `bound_other_t` distinct other T-numbers claimed since."""
    rows = _parse_rows(text.splitlines())

    info: dict[str, dict] = {}
    for idx, ts, t_ids, is_closed in rows:
        for t in t_ids:
            d = info.setdefault(t, {"first": idx, "last": idx, "closed": False, "first_ts": ts})
            d["first"] = min(d["first"], idx)
            d["last"] = max(d["last"], idx)
            if ts is not None and (d["first_ts"] is None or ts < d["first_ts"]):
                d["first_ts"] = ts
            if is_closed:
                d["closed"] = True

    alerts = []
    for t, d in info.items():
        if d["first_ts"] is None or d["first_ts"] < cutoff:
            continue
        if d["closed"]:
            continue
        others_after: set[str] = set()
        for idx, ts, t_ids, is_closed in rows:
            if idx > d["last"]:
                others_after |= (t_ids - {t})
        if len(others_after) >= bound_other_t:
            alerts.append((t, d["first"] + 1, len(others_after)))

    alerts.sort(key=lambda x: x[1])
    return alerts


def main(argv=None):
    import sys

    argv = argv if argv is not None else sys.argv[1:]
    path = Path(argv[0]) if argv else Path("04_EXECUTION/SESSION_CLAIMS.md")
    text = path.read_text()
    alerts = find_unclosed_claims(text)
    if alerts:
        print(
            f"  *** GG-199-CLASS ALERT: {len(alerts)} claim(s) with no CLOSED row after "
            f"{BOUND_OTHER_T}+ intervening claim(s) for other T-numbers (GG-188 class): ***"
        )
        for t, line_no, n in alerts:
            print(f"        - {t}: first claimed at line {line_no}, no CLOSED row; {n} other T-number(s) claimed since")
        print("      A 'MERGED: NO' or bare claim row is NOT a CLOSED row -- verify the work")
        print("      landed and either write a CLOSED row or register why it didn't.")
        return 1
    print("  OK -- no open claim exceeds the intervening-claim bound without a CLOSED row")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
