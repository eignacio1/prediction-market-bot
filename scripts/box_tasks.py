#!/usr/bin/env python3
"""W80R.1: the box bridge -- a narrow, allowlisted way for a cloud session to run NAMED jobs on the box and read the
result. Driven by .github/workflows/box_tasks.yml (GitHub Actions runners reach the box over ssh with VPS_SSH_KEY).

A request is a file 04_EXECUTION/BOX_TASKS/requests/<UTC>_<name>.toml pushed to main, holding exactly:
    task = "<name in TASKS>"
    note = "<why, <= 200 chars>"          (optional)
Nothing else in the request is read: no arguments, no paths, no shell. The command run is TASKS[task], verbatim, from
this file as it stands on main. The output (stdout+stderr, redacted, bounded) is written to
04_EXECUTION/BOX_TASKS/results/<same stem>.md and to the job summary.

Subcommands (the workflow uses these; tests import the functions):
  collect --before SHA --after SHA        list request files ADDED in that push range
  dispatch --task NAME [--note TEXT]      write a request file for a workflow_dispatch run, print its path
  run REQUEST --out RESULT [--key PATH]   validate, ssh, redact, write the result
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - py<3.11
    import tomli as tomllib  # type: ignore

ROOT = Path(__file__).resolve().parents[1]
REQ_DIR = "04_EXECUTION/BOX_TASKS/requests"
RES_DIR = "04_EXECUTION/BOX_TASKS/results"
HOST = "root@157.230.91.33"
BOX = "/opt/prediction-market-bot"
TIMEOUT_S = 900
MAX_OUT_BYTES = 60_000
NOTE_MAX = 200
NAME_RE = re.compile(r"^[a-z][a-z0-9_]{2,40}$")
STEM_RE = re.compile(r"^[0-9]{8}T[0-9]{4,6}Z_[a-z0-9_]{3,60}$")

PY = "PYTHONPATH=src:. venv/bin/python"
# Fixed allowlist: task name -> exact command, run in /opt/prediction-market-bot. Read tasks change nothing.
# capture_install refuses unless the SURFACE BUDGET reads GREEN (scripts/thin_capture_install.py, Hard Rule 14).
TASKS: dict[str, str] = {
    "budget_read": f"{PY} scripts/runtime_registry.py live --refresh; echo; tail -n 40 logs/health.log | grep '^===' | tail -1",
    "silent_arms_read": f"{PY} -m prediction_market_bot.pregame_shadow.silent_arms",
    "deploy_truth_read": "git log -1 --format='box HEAD %h %cI %s'; python3 scripts/ops/deploy_truth.py check",
    "capture_install": f"{PY} scripts/thin_capture_install.py install",
    "capture_readback": f"{PY} scripts/thin_capture_install.py readback",
    "thin_depth_stats": f"{PY} 12_EXPLORATORY/thin_markets/depth_stats.py",
    # W83.1: weekly NFL source-card capture (install is budget-gated; run = one-off backfill of this week's state)
    "source_capture_install": f"{PY} scripts/source_capture_install.py install",
    "source_capture_readback": f"{PY} scripts/source_capture_install.py readback",
    "source_capture_run": f"{PY} scripts/source_capture_nfl.py --log logs/source_capture_cron.log",
    "source_capture_uninstall": f"{PY} scripts/source_capture_install.py uninstall",
    "capture_uninstall": f"{PY} scripts/thin_capture_install.py uninstall",
    # W92.1: NBA/NHL price-archiver cron lines (install is budget-gated, backs up the crontab first)
    "archive_cron_install": f"{PY} scripts/archive_cron_install.py install",
    "archive_cron_readback": f"{PY} scripts/archive_cron_install.py readback",
    "archive_cron_uninstall": f"{PY} scripts/archive_cron_install.py uninstall",
    # W95.1: NBA engine (EXP-044 v1 + EXP-044b v2) refresh + runner cron lines (install is budget-gated)
    "nba_engine_cron_install": f"{PY} scripts/nba_engine_cron_install.py install",
    "nba_engine_cron_readback": f"{PY} scripts/nba_engine_cron_install.py readback",
    "nba_engine_cron_uninstall": f"{PY} scripts/nba_engine_cron_install.py uninstall",
    # W94.Q: read-only JSON for scripts/proof_calendar.py --input (engine cells + settle dates + archive game counts)
    "proof_calendar_read": f"{PY} scripts/proof_calendar.py --emit",
    "distance_read": (
        f"{PY} scripts/distance_to_optimum.py; echo; echo '--- forward-test report (tail)'; "
        "tail -n 60 logs/demo_fill_forward_report.log 2>&1"
    ),
    # W81.1: labelled forward-test read; writes to its own --out so the cron's report/cache are untouched
    "forward_report_read": (
        f"mkdir -p exp_output/FORWARD_TEST/w81_1 && {PY} scripts/demo_fill_forward_report.py "
        "--out exp_output/FORWARD_TEST/w81_1/demo_fill_forward_report.json --no-act; echo; "
        "python3 -c \"import json;r=json.load(open('exp_output/FORWARD_TEST/w81_1/demo_fill_forward_report.json'));"
        "print(json.dumps({k:r.get(k) for k in ('test_start_utc','topup_utc','assignment_check','tripped')},indent=1));"
        "[print(json.dumps(c)) for c in r['cells']]\""
    ),
    # W82.2: prints the JSON the report already wrote (the cron's, or a detached run's); never re-fetches fills
    "forward_verdict_read": (
        f"{PY} scripts/demo_fill_forward_report.py --print-json exp_output/FORWARD_TEST/w82_2/demo_fill_forward_report.json"
    ),
    # 2026-10-21: DigitalOcean PHP RCE notice (CVE-2026-109618/-109619). Read-only inventory: is PHP on the box, what listens.
    "php_inventory_read": (
        "echo '--- php binaries'; (command -v php php-fpm php-cgi 2>/dev/null; ls /usr/bin/php* /usr/sbin/php* 2>/dev/null) || true; "
        "echo '--- php packages'; (dpkg -l 2>/dev/null | grep -i -E '^ii +(php|libapache2-mod-php)' || echo 'no php packages'); "
        "echo '--- php processes'; (pgrep -a -f 'php' | grep -v pgrep || echo 'none running'); "
        "echo '--- web servers'; (dpkg -l 2>/dev/null | grep -E '^ii +(nginx|apache2|caddy|lighttpd) ' || echo 'no web server packages'); "
        "echo '--- listening tcp'; ss -tlnp 2>/dev/null | awk 'NR==1 || /LISTEN/'; "
        "echo '--- os'; grep PRETTY_NAME /etc/os-release"
    ),
    # 2026-10-21: the dashboards as the operator's tunnel sees them (status, bytes; the web section present on /visual).
    "dashboard_pages_read": (
        "for u in / /api/data /visual /project; do printf '%-10s ' \"$u\"; "
        "curl -s -o /dev/null -w '%{http_code} %{size_download}B %{time_total}s' --max-time 60 \"http://127.0.0.1:8050$u\"; echo; done; "
        "printf 'museweb sections on /visual: '; curl -s --max-time 60 http://127.0.0.1:8050/visual | grep -o 'id=.museweb.' | wc -l; "
        "systemctl show pmbot-web-dashboard.service -p NRestarts,ActiveState,MemoryCurrent,MemoryMax"
    ),
    "nba_opening_preflight": (
        "git log -1 --format='box HEAD %h %cI'; echo '--- ledgers'; "
        "ls -l --time-style=+%FT%T exp_output/PREGAME_SHADOW/NBA_*.jsonl exp_output/PREGAME_SHADOW_PRESEASON/*.jsonl "
        "exp_output/PREGAME_SHADOW_EXP040/*.jsonl 2>&1 | tail -n 60; "
        f"echo '--- flip check (regular-season ledgers)'; {PY} scripts/w59_3_nba_flip_check.py --ledger-dir exp_output/PREGAME_SHADOW; "
        f"echo '--- flip check (preseason ledgers)'; {PY} scripts/w59_3_nba_flip_check.py --ledger-dir exp_output/PREGAME_SHADOW_PRESEASON; "
        "echo '--- nba cron lines'; crontab -l | grep -n -i nba; "
        "echo '--- nba log tails'; for f in logs/nba_pregame_shadow_t1.log logs/nba_pregame_shadow_preseason.log "
        "logs/nba_player_points_shadow_t1.log logs/nba_autoflip.log; do echo \"== $f\"; tail -n 4 \"$f\" 2>&1; done; "
        "echo '--- CORRUPT_READ counts'; grep -c CORRUPT_READ logs/nba_*.log 2>/dev/null; "
        f"echo '--- silent arms'; {PY} -m prediction_market_bot.pregame_shadow.silent_arms"
    ),
}

_REDACT = [
    (re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----.*?-----END [A-Z ]*PRIVATE KEY-----", re.S), "[REDACTED PRIVATE KEY]"),
    (re.compile(r"(?im)^(\s*(?:export\s+)?[A-Z0-9_]*(?:KEY|SECRET|TOKEN|PASSWORD|PASSWD|CREDENTIAL)[A-Z0-9_]*\s*[=:]\s*).+$"),
     r"\1[REDACTED]"),
    (re.compile(r"(?i)\b(bearer|authorization:?)\s+[A-Za-z0-9._\-+/=]{8,}"), r"\1 [REDACTED]"),
    (re.compile(r"\b(?:ghp|gho|ghs|github_pat)_[A-Za-z0-9_]{20,}\b"), "[REDACTED TOKEN]"),
    (re.compile(r"\bsk-[A-Za-z0-9_\-]{20,}\b"), "[REDACTED TOKEN]"),
]


class BadRequest(ValueError):
    pass


def redact(text: str) -> str:
    for pat, rep in _REDACT:
        text = pat.sub(rep, text)
    return text


def bound(text: str, limit: int = MAX_OUT_BYTES) -> str:
    b = text.encode()
    if len(b) <= limit:
        return text
    head, tail = b[: limit // 2].decode(errors="ignore"), b[-limit // 2:].decode(errors="ignore")
    return f"{head}\n\n[... {len(b) - limit} bytes cut ...]\n\n{tail}"


def parse_request(path: Path) -> tuple[str, str]:
    """(task, note). Anything but the two allowed keys, an unknown task or a bad stem is refused."""
    if not STEM_RE.match(path.stem) or path.suffix != ".toml":
        raise BadRequest(f"request file name must be <UTC>_<name>.toml, got {path.name}")
    try:
        data = tomllib.loads(path.read_text())
    except (tomllib.TOMLDecodeError, UnicodeDecodeError) as e:
        raise BadRequest(f"not valid TOML: {e}") from e
    extra = set(data) - {"task", "note"}
    if extra:
        raise BadRequest(f"only 'task' and 'note' are read; refusing extra keys {sorted(extra)}")
    task, note = data.get("task"), data.get("note", "")
    if not isinstance(task, str) or task not in TASKS:
        raise BadRequest(f"task {task!r} is not in the allowlist {sorted(TASKS)}")
    if not isinstance(note, str) or len(note) > NOTE_MAX or any(ord(c) < 32 for c in note):
        raise BadRequest(f"note must be a single-line string <= {NOTE_MAX} chars")
    return task, note


def remote_command(task: str) -> str:
    return f"cd {BOX} && timeout {TIMEOUT_S} bash -c {_sh_quote(TASKS[task])}"


def _sh_quote(s: str) -> str:
    return "'" + s.replace("'", "'\"'\"'") + "'"


def ssh_run(task: str, key: str, runner=subprocess.run) -> tuple[int, str]:
    # -n + stdin=DEVNULL: ssh must never read the caller's stdin (in a `while read` loop it swallowed the remaining
    # request list, so a 3-request push ran only the first -- W80R.1 run 2).
    cmd = ["ssh", "-n", "-i", key, "-o", "StrictHostKeyChecking=no", "-o", "ConnectTimeout=15", "-o", "BatchMode=yes",
           HOST, remote_command(task)]
    try:
        r = runner(cmd, capture_output=True, text=True, timeout=TIMEOUT_S + 60, stdin=subprocess.DEVNULL)
        return r.returncode, (r.stdout or "") + (("\n[stderr]\n" + r.stderr) if r.stderr else "")
    except subprocess.TimeoutExpired:
        return 124, f"[bridge] timed out after {TIMEOUT_S + 60}s"


def render(request: Path, task: str, note: str, rc: int, output: str, now: datetime | None = None) -> str:
    now = now or datetime.now(timezone.utc)
    body = bound(redact(output)).replace("```", "``​`")
    return (f"# Box task `{task}` — {request.stem}\n\n"
            f"- request: `{request.as_posix()}`\n- note: {note or '(none)'}\n"
            f"- ran: {now:%Y-%m-%dT%H:%M:%SZ} on {HOST}:{BOX}\n- exit code: {rc}\n"
            f"- command (allowlisted, scripts/box_tasks.py): `{TASKS.get(task, '?')[:300]}`\n\n"
            f"```\n{body}\n```\n")


def run(request: Path, out: Path, key: str, runner=subprocess.run) -> int:
    try:
        task, note = parse_request(request)
    except BadRequest as e:
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(f"# Box task REFUSED — {request.name}\n\n{e}\n\nNothing was run on the box.\n")
        print(f"REFUSED {request.name}: {e}")
        return 0
    rc, output = ssh_run(task, key, runner)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(render(request, task, note, rc, output))
    print(f"ran {task} rc={rc} -> {out}")
    return 0


def collect(before: str, after: str, cwd: Path = ROOT) -> list[str]:
    if not before or set(before) == {"0"}:
        rng = [after]
        args = ["git", "show", "--name-only", "--diff-filter=A", "--format=", after]
    else:
        rng = [f"{before}..{after}"]
        args = ["git", "diff", "--name-only", "--diff-filter=A", *rng]
    out = subprocess.run(args, cwd=cwd, capture_output=True, text=True, check=True).stdout
    return sorted(p for p in out.split() if p.startswith(REQ_DIR + "/") and p.endswith(".toml"))


def dispatch(task: str, note: str, cwd: Path = ROOT, now: datetime | None = None) -> Path:
    if not NAME_RE.match(task or ""):
        raise BadRequest(f"bad task name {task!r}")
    now = now or datetime.now(timezone.utc)
    p = cwd / REQ_DIR / f"{now:%Y%m%dT%H%M%SZ}_{task}.toml"
    p.parent.mkdir(parents=True, exist_ok=True)
    note = (note or "")[:NOTE_MAX].replace('"', "'").replace("\\", "/")
    note = "".join(c for c in note if ord(c) >= 32)
    p.write_text(f'task = "{task}"\nnote = "{note}"\n')
    return p


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("collect"); c.add_argument("--before", default=""); c.add_argument("--after", required=True)
    d = sub.add_parser("dispatch"); d.add_argument("--task", required=True); d.add_argument("--note", default="")
    r = sub.add_parser("run"); r.add_argument("request"); r.add_argument("--out", required=True)
    r.add_argument("--key", default=str(Path.home() / ".ssh" / "id_ed25519_droplet"))
    a = ap.parse_args(argv)
    if a.cmd == "collect":
        print("\n".join(collect(a.before, a.after)))
        return 0
    if a.cmd == "dispatch":
        print(dispatch(a.task, a.note).relative_to(ROOT).as_posix())
        return 0
    return run(Path(a.request), Path(a.out), a.key)


if __name__ == "__main__":
    sys.exit(main())
