#!/usr/bin/env python3
"""W62.3: remove the EXP-038 NBA PRESEASON cron block (BEGIN/END markers) and nothing else.

Default is a DRY RUN that prints the diff. --apply is refused before 2026-10-21 10:00 UTC (the preseason
smoke test must run through opening night 2026-10-20), unless --crontab-file points at a copy (test mode).

  crontab target : live `crontab -l` (or --crontab-file COPY). Backup written first; --apply installs the result.
  deploy mirror  : removes the same block from deploy/cron.conf and deletes deploy/cron.nba_shadow_preseason.
Edits no other line; aborts if the block is missing/duplicated or the result would differ by more than the block.
"""
from __future__ import annotations

import argparse
import datetime as dt
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BEGIN, END = "# BEGIN EXP-038 NBA PRESEASON", "# END EXP-038 NBA PRESEASON"
NOT_BEFORE = dt.datetime(2026, 10, 21, 10, 0, tzinfo=dt.timezone.utc)
# W69.2 --auto: every block removed from the live crontab by the date-guarded cron (EXP-039 preseason + this job itself).
AUTO_BLOCKS = [(BEGIN, END),
               ("# BEGIN EXP-039 NBA PLAYER POINTS PRESEASON", "# END EXP-039 NBA PLAYER POINTS PRESEASON"),
               ("# BEGIN W69.2 NBA PRESEASON RETIRE", "# END W69.2 NBA PRESEASON RETIRE")]


def strip_all(text: str) -> tuple[str, int]:
    """Idempotent: drop each AUTO_BLOCKS block if present (0 blocks is fine); a malformed pair aborts."""
    n = 0
    for b, e in AUTO_BLOCKS:
        lines = text.splitlines(keepends=True)
        bi = [i for i, l in enumerate(lines) if l.strip() == b]
        ei = [i for i, l in enumerate(lines) if l.strip() == e]
        if not bi and not ei:
            continue
        if len(bi) != 1 or len(ei) != 1 or ei[0] < bi[0]:
            raise SystemExit(f"ABORT: malformed block {b!r}: begin={len(bi)} end={len(ei)}")
        text = "".join(lines[:bi[0]] + lines[ei[0] + 1:])
        n += 1
    return text, n


def auto(a, now) -> int:
    """Cron entry: no-op before NOT_BEFORE; afterwards remove the preseason blocks + self from the crontab only."""
    if now < NOT_BEFORE:
        print(f"AUTO: {now.isoformat()} < {NOT_BEFORE.isoformat()}, no-op")
        return 0
    live = a.crontab_file is None
    cur = (subprocess.run(["crontab", "-l"], capture_output=True, text=True, check=True).stdout
           if live else Path(a.crontab_file).read_text())
    new, n = strip_all(cur)
    if n == 0:
        print("AUTO: nothing to remove (already retired)")
        return 0
    bk = Path(a.backup_dir) / f"crontab.backup.{now.strftime('%Y%m%dT%H%M%SZ')}"
    bk.parent.mkdir(parents=True, exist_ok=True)
    bk.write_text(cur)
    if live:
        subprocess.run(["crontab", "-"], input=new, text=True, check=True)
    else:
        Path(a.crontab_file).write_text(new)
    print(f"AUTO: removed {n} block(s); backup {bk}")
    return 0


def strip_block(text: str) -> tuple[str, list[str]]:
    lines = text.splitlines(keepends=True)
    b = [i for i, l in enumerate(lines) if l.strip() == BEGIN]
    e = [i for i, l in enumerate(lines) if l.strip() == END]
    if len(b) != 1 or len(e) != 1 or e[0] < b[0]:
        raise SystemExit(f"ABORT: expected exactly one {BEGIN!r}..{END!r} block, found begin={len(b)} end={len(e)}")
    removed = lines[b[0]:e[0] + 1]
    return "".join(lines[:b[0]] + lines[e[0] + 1:]), removed


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--crontab-file", help="operate on this crontab copy instead of the live crontab (test mode)")
    ap.add_argument("--deploy-dir", default=str(ROOT / "deploy"))
    ap.add_argument("--backup-dir", default=str(ROOT / "logs"))
    ap.add_argument("--auto", action="store_true", help="cron mode: date-guarded, idempotent, crontab only, both preseason blocks")
    ap.add_argument("--now", help="ISO UTC override, tests only")
    a = ap.parse_args(argv)
    now = dt.datetime.fromisoformat(a.now) if a.now else dt.datetime.now(dt.timezone.utc)
    if a.auto:
        return auto(a, now)
    if a.apply and not a.crontab_file and now < NOT_BEFORE:
        print(f"REFUSED: --apply on the live crontab before {NOT_BEFORE.isoformat()} (now {now.isoformat()})")
        return 2
    live = a.crontab_file is None
    cur = (subprocess.run(["crontab", "-l"], capture_output=True, text=True, check=True).stdout
           if live else Path(a.crontab_file).read_text())
    new, removed = strip_block(cur)
    print(f"block lines to remove: {len(removed)}; crontab {len(cur.splitlines())} -> {len(new.splitlines())} lines")
    dd = Path(a.deploy_dir)
    conf = dd / "cron.conf"
    new_conf = None
    if conf.exists() and BEGIN in conf.read_text():
        new_conf, _ = strip_block(conf.read_text())
    print(f"deploy mirror: cron.conf {'block present -> removed' if new_conf is not None else 'no block'}; "
          f"cron.nba_shadow_preseason {'present -> deleted' if (dd / 'cron.nba_shadow_preseason').exists() else 'absent'}")
    if not a.apply:
        print("DRY RUN (no changes). Re-run with --apply.")
        return 0
    bk = Path(a.backup_dir) / f"crontab.backup.{now.strftime('%Y%m%dT%H%M%SZ')}"
    bk.parent.mkdir(parents=True, exist_ok=True)
    bk.write_text(cur)
    print(f"backup: {bk}")
    if live:
        subprocess.run(["crontab", "-"], input=new, text=True, check=True)
    else:
        Path(a.crontab_file).write_text(new)
    if new_conf is not None:
        conf.write_text(new_conf)
    (dd / "cron.nba_shadow_preseason").unlink(missing_ok=True)
    print("APPLIED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
