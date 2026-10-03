#!/usr/bin/env python3
"""Pure logic for scripts/arm_shadow_crons.sh (EXP-037 shadow cron arming).

Kept separate from the ssh wrapper so the guard (allowlist) and the crontab
merge can be unit-tested offline with fixtures. Reads/writes only stdin/stdout
and the files named on the command line. Installs nothing, runs nothing.

Subcommands:
  check-files [--allow PATH ...]   stdin: changed paths, one per line.
                                   exit 0 if all allowlisted, 1 listing offenders.
  dry-cmds CONF                    print one dry-run command per cron line in CONF.
  merge-crontab CRONTAB CONF       print CRONTAB with CONF's BEGIN/END block
                                   installed idempotently; no other line touched.
  next-fire CRONTAB_OR_CONF [NOW]  print next UTC fire time per cron line.
"""
from __future__ import annotations

import re
import sys
from datetime import datetime, timedelta, timezone

BEGIN = "# BEGIN EXP-037"
END = "# END EXP-037"

# Additive allowlist: path prefixes, plus exact-name patterns for shadow modules/scripts.
ALLOW_PREFIXES = (
    "src/prediction_market_bot/pregame_shadow/",
    "models/",
    "deploy/",
    "docs/",
    "tests/",
    "05_RESEARCH_EXPERIMENTS/",
    "11_MEMORY_HANDOFF/",
)
ALLOW_PATTERNS = (
    re.compile(r"^scripts/run_pregame_shadow[\w]*\.py$"),
    re.compile(r"^scripts/arm_shadow_crons\.(sh|py)$"),
    re.compile(r"^src/prediction_market_bot/[\w/]*(nfl|mlb|nhl)[\w]*shadow[\w]*\.py$"),
)


def offenders(paths: list[str], extra_allow: tuple[str, ...] = ()) -> list[str]:
    bad = []
    for p in paths:
        p = p.strip()
        if not p:
            continue
        if p in extra_allow:
            continue
        if p.startswith(ALLOW_PREFIXES) or any(rx.match(p) for rx in ALLOW_PATTERNS):
            continue
        bad.append(p)
    return bad


def cron_lines(conf_text: str) -> list[str]:
    """Job lines inside the BEGIN/END block (comments/blank excluded)."""
    inside, out = False, []
    for ln in conf_text.splitlines():
        if ln.strip() == BEGIN:
            inside = True
        elif ln.strip() == END:
            inside = False
        elif inside and ln.strip() and not ln.lstrip().startswith("#"):
            out.append(ln.rstrip())
    return out


def block(conf_text: str) -> list[str]:
    lines = conf_text.splitlines()
    try:
        i = next(k for k, l in enumerate(lines) if l.strip() == BEGIN)
        j = next(k for k, l in enumerate(lines) if l.strip() == END and k > i)
    except StopIteration:
        raise SystemExit("conf has no BEGIN/END EXP-037 markers")
    return [l.rstrip() for l in lines[i : j + 1]]


def command_of(line: str) -> str:
    return line.split(None, 5)[5]


def dry_command(line: str) -> str:
    """Command with side effects neutralised: no log redirect; run_pregame_shadow gets
    --dry-run; the settle script (no --dry-run flag) gets a throwaway ledger dir."""
    cmd = re.sub(r"\s>>\s*\S+\s+2>&1\s*$", "", command_of(line))
    if "run_pregame_shadow_settle.py" in cmd:
        return cmd + ' --ledger-dir "$(mktemp -d)"'
    if "run_pregame_shadow.py" in cmd:
        return cmd + " --dry-run"
    raise SystemExit(f"refusing to dry-run unrecognised job: {cmd}")


def merge_crontab(current: str, conf_text: str) -> str:
    new = block(conf_text)
    cur = current.splitlines()
    if BEGIN in [l.strip() for l in cur]:
        i = next(k for k, l in enumerate(cur) if l.strip() == BEGIN)
        j = next((k for k, l in enumerate(cur) if l.strip() == END and k > i), None)
        if j is None:
            raise SystemExit("crontab has BEGIN EXP-037 without END; refusing to edit")
        merged = cur[:i] + new + cur[j + 1 :]
    else:
        merged = cur + new
    return "\n".join(merged) + "\n"


def _field_matches(spec: str, value: int, lo: int) -> bool:
    for part in spec.split(","):
        if part == "*":
            return True
        if part.startswith("*/"):
            if (value - lo) % int(part[2:]) == 0:
                return True
        elif int(part) == value:
            return True
    return False


def next_fire(line: str, now: datetime) -> datetime:
    mi, hr, dom, mon, dow = line.split(None, 5)[:5]
    t = now.replace(second=0, microsecond=0) + timedelta(minutes=1)
    for _ in range(60 * 24 * 8):
        if (
            _field_matches(mi, t.minute, 0)
            and _field_matches(hr, t.hour, 0)
            and _field_matches(dom, t.day, 1)
            and _field_matches(mon, t.month, 1)
            and _field_matches(dow, (t.weekday() + 1) % 7, 0)
        ):
            return t
        t += timedelta(minutes=1)
    raise SystemExit(f"no fire time within 8 days for: {line}")


def main(argv: list[str]) -> int:
    if not argv:
        print(__doc__)
        return 2
    cmd, args = argv[0], argv[1:]
    if cmd == "check-files":
        extra = tuple(args[i + 1] for i, a in enumerate(args) if a == "--allow")
        bad = offenders(sys.stdin.read().splitlines(), extra)
        if bad:
            print("REFUSED: changed files outside the additive allowlist:", file=sys.stderr)
            for p in bad:
                print(f"  {p}", file=sys.stderr)
            return 1
        print("allowlist OK")
        return 0
    if cmd == "dry-cmds":
        for ln in cron_lines(open(args[0]).read()):
            print(dry_command(ln))
        return 0
    if cmd == "merge-crontab":
        sys.stdout.write(merge_crontab(open(args[0]).read(), open(args[1]).read()))
        return 0
    if cmd == "next-fire":
        now = (
            datetime.fromisoformat(args[1]).astimezone(timezone.utc)
            if len(args) > 1
            else datetime.now(timezone.utc)
        )
        for ln in cron_lines(open(args[0]).read()):
            print(f"{next_fire(ln, now):%Y-%m-%d %H:%M}Z  {command_of(ln).split('scripts/')[-1][:60]}")
        return 0
    print(f"unknown subcommand {cmd}", file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
