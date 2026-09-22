#!/usr/bin/env python3
"""GG-203/T-547 D5 -- alarm-only order-write parity detector.

GG-203 sat undetected for 10 days (2026-08-15 through 2026-08-24): every
`risk_eval_approved` event in audit_mlb_t4.jsonl was followed by a
`kalshi_order_failed` event, a 100% execution-layer failure rate, while
every other liveness probe (systemctl is-active, cycle-log recency, T1
player-match counts) reported healthy throughout. Nothing compared
approvals against execution outcomes directly. This script is that
comparison, made structural instead of something a session has to notice
by hand.

Counts are computed remotely over SSH against the VPS's own
audit_mlb_t4.jsonl -- the file is never pulled locally (it grows too fast
to sync cheaply; see GG-158's rsync age-gate rationale for the general
local-copy pattern this deliberately avoids).

ALARM-ONLY by operator directive, same convention as
scripts/assert_ledger_invariants.py: this script always exits 0. A defect
in the detector itself must never gate a session or a hook -- violations
are surfaced on stdout only.
"""
import argparse
import json
import shlex
import subprocess
import sys
from datetime import datetime, timedelta, timezone

VPS_HOST = "prediction-market-vps"
AUDIT_LOG = "/opt/prediction-market-bot/logs/audit_mlb_t4.jsonl"
ALARM_THRESHOLD = 0.90  # fraction of approvals that failed to execute


def count_events(date_str: str) -> tuple[int, int, bool]:
    """Returns (approved_count, failed_count, vps_reachable)."""
    remote_script = (
        "import json\n"
        "approved = 0\n"
        "failed = 0\n"
        "try:\n"
        f"    with open({AUDIT_LOG!r}) as f:\n"
        "        for line in f:\n"
        f"            if {date_str!r} not in line:\n"
        "                continue\n"
        "            try:\n"
        "                row = json.loads(line)\n"
        "            except json.JSONDecodeError:\n"
        "                continue\n"
        "            ts = row.get('timestamp', '')\n"
        f"            if not ts.startswith({date_str!r}):\n"
        "                continue\n"
        "            et = row.get('event_type', '')\n"
        "            if et == 'risk_eval_approved':\n"
        "                approved += 1\n"
        "            elif et == 'kalshi_order_failed':\n"
        "                failed += 1\n"
        "except FileNotFoundError:\n"
        "    pass\n"
        "print(json.dumps({'approved': approved, 'failed': failed}))\n"
    )
    # ssh concatenates trailing argv items with spaces and hands the result to
    # the remote shell as one string -- it does not preserve argv boundaries
    # the way a local exec would. Passing the python source as a *separate*
    # argv item (as an earlier version of this script did) gets it mangled
    # into multiple remote shell words. Build one single shell-quoted command
    # string instead so it survives that join intact.
    remote_command = "python3 -c " + shlex.quote(remote_script)
    try:
        result = subprocess.run(
            [
                "ssh", "-o", "ConnectTimeout=5", "-o", "BatchMode=yes",
                VPS_HOST, remote_command,
            ],
            capture_output=True, text=True, timeout=30,
        )
    except (subprocess.TimeoutExpired, OSError):
        return 0, 0, False
    if result.returncode != 0 or not result.stdout.strip():
        return 0, 0, False
    try:
        data = json.loads(result.stdout.strip().splitlines()[-1])
    except (json.JSONDecodeError, IndexError):
        return 0, 0, False
    return data.get("approved", 0), data.get("failed", 0), True


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--date", default=None,
        help="UTC date YYYY-MM-DD to check (default: yesterday UTC, i.e. the "
             "last complete day)",
    )
    args = parser.parse_args()

    date_str = args.date or (
        datetime.now(timezone.utc) - timedelta(days=1)
    ).strftime("%Y-%m-%d")

    approved, failed, reachable = count_events(date_str)

    print(f"GG-203 ORDER-WRITE PARITY CHECK — {date_str}")
    if not reachable:
        print("  UNREACHABLE — VPS unreachable or audit log missing; cannot assess this day.")
        sys.exit(0)

    if approved == 0:
        print(
            f"  approved=0 failed={failed} — no approvals this day, nothing to "
            f"compare (off-day/off-season, or T4 itself silent -- see the GG-163 "
            f"cycle-log probe for that failure mode instead)."
        )
        sys.exit(0)

    rate = failed / approved
    print(
        f"  risk_eval_approved={approved} kalshi_order_failed={failed} "
        f"failure_rate={rate:.1%}"
    )
    if rate >= ALARM_THRESHOLD:
        print(
            f"  *** GG-203-CLASS ALARM: {rate:.1%} of approved bets failed to "
            f"execute on {date_str} (threshold {ALARM_THRESHOLD:.0%}). ***"
        )
        print(
            "      This is the exact blind spot GG-203 sat in for 10 days "
            "undetected -- every"
        )
        print(
            "      other liveness probe reported healthy while execution "
            "silently failed. Do"
        )
        print(
            "      not dismiss this as noise; check kalshi_order_failed "
            "payload.error bodies"
        )
        print("      in audit_mlb_t4.jsonl directly.")
    else:
        print(f"  OK — failure rate below {ALARM_THRESHOLD:.0%} alarm threshold.")

    sys.exit(0)  # alarm-only: a detector defect must never gate a session/hook


if __name__ == "__main__":
    main()
