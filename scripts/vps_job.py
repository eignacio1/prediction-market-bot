#!/usr/bin/env python3
"""Detached-job runner for READ-ONLY long work on the VPS (Wave 48.2 / T-632).

A launcher, not a scheduler: it creates no cron entry and needs none. One job = one directory on the VPS,
  <jobs>/<name>/{run.sh, start.json, pid, log, done.json}
  start.json  UTC start, argv, code sha (VPS git HEAD), rate cap, host
  pid         written by the wrapper itself ($$), so it is the real process-group leader
  done.json   completion marker with exit code; written by the wrapper, or by `stop` if the wrapper was killed

  launch <name> --rate-cap R -- <python3 scripts/x.py args...>
  status <name> | tail <name> [-n N] | stop <name> | list

Safety (checked locally on the commit being launched, BEFORE anything runs remotely):
  * argv must be `python3 <repo-relative .py under scripts/ or src/> [args]` -- no -c / -m, no shell metacharacters.
  * the script's transitive import closure (same-package, sibling-script and src package modules) must not import,
    nor mention as an identifier, any order / position / sizing / paper-trader / venue-execution code.
  * --rate-cap is required, <= 3.3 req/s (the Kalshi public cap); if the command carries its own --rate it must be <= cap.
    The cap is RECORDED and cross-checked against the command line; the job itself enforces its pacing.
  * a second launch of the same name is refused while the first is alive; a finished job's dir is moved aside.
"""
from __future__ import annotations

import argparse
import ast
import base64
import datetime as dt
import json
import re
import shlex
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PKG = "prediction_market_bot"
HOST = "prediction-market-vps"
REMOTE_REPO = "/opt/prediction-market-bot"
REMOTE_JOBS = f"{REMOTE_REPO}/exp_output/VPS_JOBS"
MAX_RATE = 3.3
NAME_RE = re.compile(r"^[a-z0-9][a-z0-9_-]{0,47}$")
META_RE = re.compile(r"[;&|`$<>()\\\n\r]")
FORBIDDEN_MODULES = ("kalshi_client", "paper_trader", "c4_risk_engine", "execution_bands", "venue_adapter",
                     "market_type_registry", "c5_execution", "pregame_shadow.runner", "run_t4_mlb_live",
                     "t4_execution_engine", "t4_mlb_execution_engine")
FORBIDDEN_NAMES = ("submit_order", "open_position", "exit_position", "place_order", "PaperTrader",
                   "kelly_fraction", "KELLY_T4", "DEFAULT_KELLY_FRACTION")


class Refused(Exception):
    pass


# ---------------------------------------------------------------- safety
def _imports(path: Path):
    for node in ast.walk(ast.parse(path.read_text())):
        if isinstance(node, ast.Import):
            yield from (a.name for a in node.names)
        elif isinstance(node, ast.ImportFrom):
            base = node.module or ""
            yield base
            yield from (f"{base}.{a.name}" if base else a.name for a in node.names)


def _identifiers(path: Path):
    for node in ast.walk(ast.parse(path.read_text())):
        if isinstance(node, ast.Name):
            yield node.id
        elif isinstance(node, ast.Attribute):
            yield node.attr
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            yield node.name
        elif isinstance(node, ast.arg):
            yield node.arg
        elif isinstance(node, ast.keyword) and node.arg:
            yield node.arg


def _module_file(mod: str, root: Path, script_dir: Path):
    parts = mod.split(".")
    cands = []
    if parts[0] == PKG:
        base = root / "src" / Path(*parts)
        cands += [base.with_suffix(".py"), base / "__init__.py"]
    else:
        cands += [script_dir / f"{parts[0]}.py"]       # sibling-script import (sys.path insert idiom)
    for c in cands:
        if c.exists():
            return c
    return None


def closure(entry: Path, root: Path):
    seen, stack = set(), [entry]
    while stack:
        f = stack.pop()
        if f in seen:
            continue
        seen.add(f)
        for m in _imports(f):
            mf = _module_file(m, root, entry.parent if f == entry else f.parent)
            if mf is None and f.parent != entry.parent:
                mf = _module_file(m, root, entry.parent)
            if mf:
                stack.append(mf)
    return seen


def check_command(argv: list[str], rate_cap: float, root: Path = ROOT) -> Path:
    """Raise Refused unless argv is a read-only, rate-capped python script launch. Returns the script path."""
    if not (0 < rate_cap <= MAX_RATE):
        raise Refused(f"--rate-cap must be in (0, {MAX_RATE}] req/s, got {rate_cap}")
    if len(argv) < 2 or argv[0] not in ("python3", "python"):
        raise Refused("command must be: python3 <scripts/... or src/... .py> [args]")
    for t in argv:
        if META_RE.search(t):
            raise Refused(f"shell metacharacter in argument {t!r}")
    if argv[1] in ("-c", "-m") or argv[1].startswith("-"):
        raise Refused("python flags (-c/-m/...) are not allowed; name a script file")
    rel = Path(argv[1])
    if rel.is_absolute() or ".." in rel.parts or rel.parts[0] not in ("scripts", "src") or rel.suffix != ".py":
        raise Refused(f"script must be a repo-relative .py under scripts/ or src/, got {argv[1]!r}")
    script = root / rel
    if not script.exists():
        raise Refused(f"script not found in this checkout: {argv[1]}")
    for i, t in enumerate(argv):
        if t == "--rate" and i + 1 < len(argv):
            try:
                r = float(argv[i + 1])
            except ValueError:
                raise Refused(f"--rate value not numeric: {argv[i + 1]!r}")
            if r > rate_cap:
                raise Refused(f"command --rate {r} exceeds --rate-cap {rate_cap}")
        if t.startswith("--rate="):
            if float(t.split("=", 1)[1]) > rate_cap:
                raise Refused(f"command {t} exceeds --rate-cap {rate_cap}")
    for f in closure(script, root):
        for m in _imports(f):
            if any(b in m for b in FORBIDDEN_MODULES):
                raise Refused(f"{rel} -> {f.name} imports forbidden module {m!r} (order/sizing/execution path)")
        for n in _identifiers(f):
            if n in FORBIDDEN_NAMES:
                raise Refused(f"{rel} -> {f.name} references forbidden identifier {n!r}")
    return script


# ---------------------------------------------------------------- backends
class SshBackend:
    def __init__(self, host: str = HOST):
        self.host = host

    def run(self, script: str, timeout: int = 60):
        p = subprocess.run(["ssh", "-o", "ConnectTimeout=15", self.host, "bash -s"], input=script,
                           capture_output=True, text=True, timeout=timeout)
        return p.returncode, p.stdout, p.stderr


class LocalBackend:
    """Same remote scripts executed by local bash -- used by the tests and for dry runs."""

    def run(self, script: str, timeout: int = 60):
        p = subprocess.run(["bash", "-s"], input=script, capture_output=True, text=True, timeout=timeout)
        return p.returncode, p.stdout, p.stderr


# ---------------------------------------------------------------- remote scripts
def _utc() -> str:
    return dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def launch_script(name: str, argv: list[str], rate_cap: float, repo: str, jobs: str) -> str:
    cmd = shlex.join(argv)
    start = {"name": name, "argv": argv, "rate_cap_req_per_s": rate_cap, "launched_utc": _utc(),
             "code_sha": "__SHA__", "repo": repo, "host": "__HOST__"}
    start_b64 = base64.b64encode(json.dumps(start, sort_keys=True).encode()).decode()
    wrapper = (
        "#!/usr/bin/env bash\n"
        'J="$(cd "$(dirname "$0")" && pwd)"\n'
        '(echo $$ > "$J/pid.tmp" && mv "$J/pid.tmp" "$J/pid")\n'
        f"cd {shlex.quote(repo)} || exit 97\n"
        f"{cmd}\n"
        "rc=$?\n"
        "printf '{\"exit_code\": %s, \"finished_utc\": \"%s\"}\\n' \"$rc\" \"$(date -u +%FT%TZ)\" > \"$J/done.tmp\" && mv \"$J/done.tmp\" \"$J/done.json\"\n"
        "exit $rc\n")
    wrapper_b64 = base64.b64encode(wrapper.encode()).decode()
    script_rel = shlex.quote(argv[1])
    return f"""set -u
J={shlex.quote(jobs)}/{name}
mkdir -p {shlex.quote(jobs)}
test -f {shlex.quote(repo)}/{script_rel} || {{ echo "REFUSED: {argv[1]} not present on this host (deploy first)"; exit 4; }}
if [ -d "$J" ]; then
  if [ -f "$J/pid" ] && [ ! -f "$J/done.json" ] && kill -0 "$(cat "$J/pid")" 2>/dev/null; then
    echo "REFUSED: job {name} already running (pid $(cat "$J/pid"))"; exit 3
  fi
  mv "$J" "$J.$(date -u +%Y%m%dT%H%M%SZ).old"
fi
mkdir "$J" || {{ echo "REFUSED: could not create $J (concurrent launch?)"; exit 3; }}
SHA=$(git -C {shlex.quote(repo)} rev-parse HEAD 2>/dev/null || echo unknown)
echo {start_b64} | base64 -d | sed "s/__SHA__/$SHA/; s/__HOST__/$(hostname)/" > "$J/start.json"
echo {wrapper_b64} | base64 -d > "$J/run.sh"; chmod +x "$J/run.sh"
S=""; command -v setsid >/dev/null && S=setsid
{{ cd "$J" && $S nohup bash "$J/run.sh"; }} > "$J/log" 2>&1 < /dev/null &
for i in 1 2 3 4 5 6 7 8 9 10; do [ -f "$J/pid" ] && break; sleep 0.3; done
if [ -f "$J/pid" ]; then echo "LAUNCHED {name} pid=$(cat "$J/pid") sha=$SHA"; else echo "LAUNCHED {name} pid=unknown (wrapper not yet written)"; fi
"""


def status_script(name: str, jobs: str) -> str:
    return f"""J={shlex.quote(jobs)}/{name}
[ -d "$J" ] || {{ echo "STATE: none"; exit 0; }}
if [ -f "$J/done.json" ]; then echo "STATE: finished $(cat "$J/done.json")"
elif [ -f "$J/pid" ] && kill -0 "$(cat "$J/pid")" 2>/dev/null; then echo "STATE: running pid=$(cat "$J/pid") up_s=$(ps -o etimes= -p "$(cat "$J/pid")" | tr -d ' ')"
else echo "STATE: died (no pid alive, no completion marker)"; fi
echo "START: $(cat "$J/start.json" 2>/dev/null)"
echo "LOG_BYTES: $(wc -c < "$J/log" 2>/dev/null)"
"""


def tail_script(name: str, jobs: str, n: int) -> str:
    return f'tail -n {int(n)} {shlex.quote(jobs)}/{name}/log 2>&1\n'


def stop_script(name: str, jobs: str) -> str:
    return f"""J={shlex.quote(jobs)}/{name}
[ -f "$J/pid" ] || {{ echo "STOP: no pid for {name}"; exit 1; }}
P=$(cat "$J/pid")
if [ -f "$J/done.json" ] || ! kill -0 "$P" 2>/dev/null; then echo "STOP: {name} not running"; exit 0; fi
kill -TERM -- "-$P" 2>/dev/null || kill -TERM "$P"
for i in 1 2 3 4 5 6 7 8 9 10; do kill -0 "$P" 2>/dev/null || break; sleep 0.5; done
kill -0 "$P" 2>/dev/null && {{ kill -KILL -- "-$P" 2>/dev/null || kill -KILL "$P"; }}
[ -f "$J/done.json" ] || printf '{{"exit_code": "stopped", "finished_utc": "%s"}}\\n' "$(date -u +%FT%TZ)" > "$J/done.json"
echo "STOPPED {name}"
"""


def list_script(jobs: str) -> str:
    return f'for d in {shlex.quote(jobs)}/*/; do [ -d "$d" ] && echo "$(basename "$d")"; done 2>/dev/null\n'


# ---------------------------------------------------------------- CLI
def main(argv=None, backend=None, root: Path = ROOT, repo: str = REMOTE_REPO, jobs: str = REMOTE_JOBS) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    pl = sub.add_parser("launch")
    pl.add_argument("name")
    pl.add_argument("--rate-cap", type=float, required=True, help=f"req/s ceiling for this job (<= {MAX_RATE})")
    for c in ("status", "stop"):
        sub.add_parser(c).add_argument("name")
    pt = sub.add_parser("tail")
    pt.add_argument("name")
    pt.add_argument("-n", type=int, default=40)
    sub.add_parser("list")
    argv = list(sys.argv[1:] if argv is None else argv)
    tail_cmd = []
    if "--" in argv:
        i = argv.index("--")
        argv, tail_cmd = argv[:i], argv[i + 1:]
    a = ap.parse_args(argv)
    be = backend or SshBackend()
    if a.cmd != "list" and not NAME_RE.match(a.name):
        print(f"REFUSED: bad job name {a.name!r} (lowercase letters, digits, - and _ only)")
        return 2
    if a.cmd == "launch":
        cmd = tail_cmd
        try:
            check_command(cmd, a.rate_cap, root)
        except Refused as e:
            print(f"REFUSED: {e}")
            return 2
        script = launch_script(a.name, cmd, a.rate_cap, repo, jobs)
    elif a.cmd == "status":
        script = status_script(a.name, jobs)
    elif a.cmd == "tail":
        script = tail_script(a.name, jobs, a.n)
    elif a.cmd == "stop":
        script = stop_script(a.name, jobs)
    else:
        script = list_script(jobs)
    rc, out, err = be.run(script)
    sys.stdout.write(out)
    if err.strip():
        sys.stderr.write(err)
    return rc


if __name__ == "__main__":
    sys.exit(main())
