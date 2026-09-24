#!/usr/bin/env python3
"""GG-279 (OPEN) -- minimal deploy-vs-activation structural check.

A code fix can land in git, even fully migrate on-disk state, and still not
be active in a long-running service's process memory until that service is
restarted -- t4-mlb and pmbot-web-dashboard.service do not hot-reload.
GG-271 recurred for ~77h in exactly this way: the fix was merged and the
live data file migrated, but the running process kept executing pre-fix
bytecode, and nothing in session-start or close-out protocol checked for
this. GG-279 generalizes the incident and asks for a structural check;
its own Resolution field states the live wiring "is registered here and
left for a future session to design and build."

T-574 (2026-09-24), Deliverable 4: this module provides only the
comparison primitive -- given a service's process start time and the
commit timestamp(s) of its relevant source files, flag any commit newer
than the process start as "landed but not yet activated." Alarm-only,
matching assert_ledger_invariants.py's (Q7) convention: never a nonzero
exit code from this CLI on its own.

Deliberately out of scope here (SHORT tier, T-574 -- register as a gap
candidate for follow-up rather than build in-session): SSH/systemctl
enumeration of live services, and the source-path-per-service mapping
that decides which commits are "relevant" to a given service. Both are
real design decisions, not wiring, and GG-279 itself defers them.
"""
from __future__ import annotations

import argparse
import sys
from datetime import datetime, timezone


def parse_iso(ts: str) -> datetime:
    dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def landed_but_not_activated(service_start: str, commit_timestamps: list[str]) -> list[str]:
    """Commit timestamps strictly newer than service_start.

    A nonempty result means a relevant source change was committed after
    the service's own process last started -- landed in git, not yet
    active in that service's running memory (GG-279).
    """
    start = parse_iso(service_start)
    return [ts for ts in commit_timestamps if parse_iso(ts) > start]


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--service-start", required=True,
                    help="ISO-8601 timestamp, e.g. systemctl show -p ActiveEnterTimestamp")
    p.add_argument("--commit-ts", action="append", required=True, dest="commit_ts",
                    help="ISO-8601 commit timestamp; repeatable")
    args = p.parse_args()

    findings = landed_but_not_activated(args.service_start, args.commit_ts)
    if findings:
        print(f"LANDED_BUT_NOT_ACTIVATED: {len(findings)} commit(s) newer than "
              f"service start {args.service_start}", file=sys.stderr)
        for f in findings:
            print(f"  {f}", file=sys.stderr)
    else:
        print("OK: no given commit timestamps are newer than the given service start")
    return 0  # alarm-only -- never fails the run on its own


if __name__ == "__main__":
    sys.exit(main())
