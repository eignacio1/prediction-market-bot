#!/usr/bin/env python3
"""T-388 — bump-time behavioral-activation check for logic-epoch boundaries.

GG-124 found that stacking multiple `CURRENT_LOGIC_EPOCH` boundary bumps
within a short window blacks out `clean_n` monitoring across every active
band simultaneously (five bumps landed in ~5 days, 2026-07-14..18). GG-105/
T-387 separately found that a deploy landing does not mean the new logic is
*behaviorally* live: run_t4_mlb_live.py's ba_l10_shrunk fallback meant the
Jul-18 epoch-7 boundary was mis-anchored, because the production feature CSV
predated the merge and the new field was silently absent.

This script answers both questions at bump time, non-blocking (warn only,
per TODO_NEXT.md's T-388 proposed shape):

  (a) Stacking: has another boundary landed within the trailing window?
  (b) Activation: if the new logic depends on a production data field, is
      that field actually present (non-null) in the most recent artifact?

Usage:
    scripts/check_epoch_activation.py
    scripts/check_epoch_activation.py --field ba_l10_shrunk \\
        --artifact-glob "/opt/prediction-market-bot/exp_output/MLB/pregame_mlb_*.json"
    scripts/check_epoch_activation.py --skip-vps   # stacking check only, no SSH

Exit code: 0 if clean, 1 if any ALERT fired (stacking is warn-only and never
affects exit code, matching the non-blocking design in TODO_NEXT.md T-388).
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from prediction_market_bot.logic_epoch import (  # noqa: E402
    CURRENT_LOGIC_EPOCH,
    LogicEpochBoundary,
    get_boundaries,
)

# GG-124's own re-check math used "one full week from boundary start" as the
# horizon for judging whether clean_n accrual is back to normal — reused here
# as the trailing window for flagging boundary stacking.
STACKING_WINDOW_DAYS = 7


def check_stacking(
    boundaries: tuple[LogicEpochBoundary, ...] | None = None,
    now: datetime | None = None,
    window_days: int = STACKING_WINDOW_DAYS,
) -> list[str]:
    """Return a warning (0 or 1 items) if >1 boundary landed within the trailing window."""
    if boundaries is None:
        boundaries = get_boundaries()
    if now is None:
        now = datetime.now(timezone.utc)
    window_start = now - timedelta(days=window_days)
    recent = [b for b in boundaries if b.commit_utc >= window_start]
    if len(recent) <= 1:
        return []
    listed = ", ".join(f"epoch {b.epoch} ({b.resolving_gap}, {b.commit_utc.date()})" for b in recent)
    return [
        f"STACKING WARNING: {len(recent)} logic-epoch boundaries landed within the trailing "
        f"{window_days}d window ({window_start.date()} .. {now.date()}): {listed}. Per GG-124, "
        "stacked boundaries reset clean_n for every active band simultaneously and can produce an "
        "extended clean_n=0/UNDERPOWERED monitoring blackout across the whole pool. Not a blocker "
        "— confirm this bump is worth the accrual reset before committing it."
    ]


def check_field_activation(
    field: str,
    artifact_glob: str,
    host: str = "prediction-market-vps",
    timeout: int = 30,
) -> list[str]:
    """SSH to the VPS and confirm `field` is present/non-null in the most recently
    modified file matching `artifact_glob`. Returns ALERT strings; empty means pass."""
    remote_script = f"""
import glob, json, os, sys
files = sorted(glob.glob({artifact_glob!r}), key=os.path.getmtime)
if not files:
    print("NO_FILES")
    sys.exit(0)
path = files[-1]
with open(path) as f:
    data = json.load(f)
if isinstance(data, list):
    records = data
elif isinstance(data, dict):
    records = list(data.values())
else:
    records = []
total = len(records)
present = sum(1 for r in records if isinstance(r, dict) and r.get({field!r}) is not None)
print(f"{{path}}\\t{{total}}\\t{{present}}")
"""
    cmd = ["ssh", "-o", "ConnectTimeout=5", "-o", "BatchMode=yes", host, "python3", "-"]
    try:
        result = subprocess.run(cmd, input=remote_script, capture_output=True, text=True, timeout=timeout)
    except Exception as exc:
        return [f"ALERT: could not reach VPS ({host}) to verify field activation for '{field}': {exc}"]
    if result.returncode != 0:
        return [f"ALERT: remote activation check failed (exit {result.returncode}): {result.stderr.strip()}"]
    out = result.stdout.strip()
    if out == "NO_FILES":
        return [f"ALERT: no files matched {artifact_glob!r} on {host} — cannot verify '{field}' activation."]
    try:
        path, total_s, present_s = out.split("\t")
        total, present = int(total_s), int(present_s)
    except ValueError:
        return [f"ALERT: unexpected remote output for '{field}' check: {out!r}"]
    if total > 0 and present == 0:
        return [
            f"ALERT: {path} has {total} record(s) but ZERO with a non-null '{field}' field. This is "
            "the GG-105/T-387 failure mode (deploy landed but the artifact the new logic depends on "
            "does not carry the new field yet — deploy != behavioral activation). Do not treat this "
            "bump as behaviorally live until this check passes; trace the field's data-dependency "
            "chain (e.g. feature CSV -> pregame JSON -> runner) to find where it's dropped."
        ]
    return []


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--host", default="prediction-market-vps", help="SSH alias for the VPS")
    ap.add_argument("--field", help="Production data field the new/latest logic depends on, e.g. ba_l10_shrunk")
    ap.add_argument(
        "--artifact-glob",
        help="Remote glob for the artifact carrying --field, e.g. "
        "'/opt/prediction-market-bot/exp_output/MLB/pregame_mlb_*.json'",
    )
    ap.add_argument("--skip-vps", action="store_true", help="Run only the local stacking check (no SSH)")
    args = ap.parse_args(argv)

    boundaries = get_boundaries()
    print(f"CURRENT_LOGIC_EPOCH = {CURRENT_LOGIC_EPOCH} ({len(boundaries)} boundaries registered)")
    print()

    warnings = check_stacking(boundaries)
    for w in warnings:
        print(w)
        print()

    alerts: list[str] = []
    if args.field and not args.skip_vps:
        if not args.artifact_glob:
            print("ERROR: --field given without --artifact-glob", file=sys.stderr)
            return 2
        alerts = check_field_activation(args.field, args.artifact_glob, host=args.host)
        for a in alerts:
            print(a)
            print()
    elif args.field and args.skip_vps:
        print(f"(--skip-vps set: not verifying '{args.field}' against {args.artifact_glob!r})")

    if not warnings and not alerts:
        print("CLEAN — no stacking risk, no field-activation alert.")

    return 1 if alerts else 0


if __name__ == "__main__":
    raise SystemExit(main())
