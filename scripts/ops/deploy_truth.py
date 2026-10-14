#!/usr/bin/env python3
"""W72.3 (GG-661 / GG-668): make "merge != deploy != activation" checkable by a machine.

Stdlib only (runs under the deploy cron, the daily healthcheck and the governance scan over ssh).

Subcommands
  marker set|clear|show   pending-restart marker for t4-mlb. vps_deploy.sh sets it when the restart policy
                          skips a restart (live game / game state unknown) and clears it when t4-mlb restarts;
                          the first no-live-game tick retries (deploy_restart_policy.py --pending).
  status  --outcome ...   deploy status file (STATE_DIR/deploy_status.json). Written by vps_deploy.sh on EVERY
                          outcome so a failed deploy is an alarm, not a log line.
  check                   one block of "DEPLOY TRUTH" lines: deploy status, pending marker, and per running
                          service whether the code it runs is older than box HEAD for files it uses.
                          ALARM when a service has run stale code for > --max-age-h (default 6h).

Alarm-only: `check` always exits 0 (the reader decides); lines start with OK / ALARM / UNKNOWN.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

MAX_AGE_H = 6.0
FETCH_FAIL_GRACE_S = 30 * 60          # a flaky fetch is normal; 30 min of it is not
OK_OUTCOMES = {"docs_only", "deployed", "pending_restart_done", "noop"}
DEFAULT_SERVICES = ("t4-mlb", "pmbot-web-dashboard")
# Services whose code is "anything the deploy restarts them for" (they restart on every code deploy).
BROAD_PREFIXES = ("src/", "scripts/web_dashboard.py")


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _iso(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def _parse_iso(s: str) -> datetime | None:
    try:
        return datetime.strptime(s, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    except (TypeError, ValueError):
        return None


def _read_json(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def _write_json(path: Path, obj: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(obj, indent=1) + "\n", encoding="utf-8")
    os.replace(tmp, path)


# ----- pending-restart marker ------------------------------------------------------------------------
def marker_path(state_dir: Path) -> Path:
    return state_dir / "t4_pending_restart.json"


def marker_set(state_dir: Path, verdict: str, sha: str, reason: str, now: datetime | None = None) -> dict:
    """Keep the ORIGINAL `since` if a marker already exists: age counts from the first skipped restart."""
    now = now or _now()
    cur = _read_json(marker_path(state_dir))
    rec = {"since": cur.get("since") or _iso(now), "last_skip": _iso(now),
           "verdict": verdict, "sha": sha, "reason": reason[:300]}
    _write_json(marker_path(state_dir), rec)
    return rec


def marker_clear(state_dir: Path) -> bool:
    try:
        marker_path(state_dir).unlink()
        return True
    except OSError:
        return False


# ----- deploy status ---------------------------------------------------------------------------------
def status_path(state_dir: Path) -> Path:
    return state_dir / "deploy_status.json"


def status_write(state_dir: Path, outcome: str, detail: str = "", now: datetime | None = None) -> dict:
    now = now or _now()
    prev = _read_json(status_path(state_dir))
    ok = outcome in OK_OUTCOMES
    rec = {"ts": _iso(now), "outcome": outcome, "ok": ok, "detail": detail[:300],
           "last_ok_ts": _iso(now) if ok else prev.get("last_ok_ts"),
           # when the current failing streak began (kept across repeats of the same failing state)
           "fail_since": None if ok else (prev.get("fail_since") or _iso(now))}
    _write_json(status_path(state_dir), rec)
    return rec


# ----- service code staleness ------------------------------------------------------------------------
def _git(proj: Path, *args: str) -> str | None:
    try:
        return subprocess.run(["git", *args], cwd=proj, capture_output=True, text=True, check=True,
                              timeout=60).stdout.strip()
    except (subprocess.SubprocessError, OSError):
        return None


def service_start(service: str, systemctl: str = "systemctl") -> datetime | None:
    """ActiveEnterTimestamp of a running unit, as UTC. None if not running / unreadable."""
    try:
        out = subprocess.run([systemctl, "show", service, "--property=ActiveState,ActiveEnterTimestamp"],
                             capture_output=True, text=True, timeout=20).stdout
    except (subprocess.SubprocessError, OSError):
        return None
    kv = dict(l.split("=", 1) for l in out.splitlines() if "=" in l)
    if kv.get("ActiveState") != "active" or not kv.get("ActiveEnterTimestamp"):
        return None
    ts = kv["ActiveEnterTimestamp"].strip()          # "Tue 2026-10-13 23:58:11 UTC"
    for fmt in ("%a %Y-%m-%d %H:%M:%S %Z", "%a %Y-%m-%d %H:%M:%S"):
        try:
            return datetime.strptime(ts, fmt).replace(tzinfo=timezone.utc)
        except ValueError:
            continue
    return None


def sha_at(proj: Path, start: datetime, decisions: list[dict]) -> tuple[str | None, str]:
    """The box HEAD when a process started. Exact when the deploy log has it, else the commit-date estimate."""
    best = None
    for d in decisions:
        t = _parse_iso(d.get("ts", ""))
        # the deploy record is written seconds AFTER the restart it caused; allow that skew
        if t and (t - start).total_seconds() <= 150 and d.get("after") and d.get("outcome") in (
                "deployed", "docs_only", "verify_failed", "pending_restart_done"):
            best = d["after"]
    if best:
        return best, "deploy_log"
    est = _git(proj, "rev-list", "-1", f"--before={_iso(start)}", "HEAD")
    return (est or None), "commit_date"


def load_decisions(path: Path) -> list[dict]:
    out = []
    try:
        for ln in path.read_text(encoding="utf-8").splitlines():
            try:
                out.append(json.loads(ln))
            except ValueError:
                continue
    except OSError:
        pass
    out.sort(key=lambda d: d.get("ts", ""))
    return out


def relevant_files(proj: Path, service: str) -> set[str] | tuple[str, ...]:
    if service == "t4-mlb":
        sys.path.insert(0, str(proj / "scripts"))
        try:
            import deploy_restart_policy as p
            return p.import_closure(proj)
        except Exception:                                  # noqa: BLE001 - unreadable closure = broad check
            return BROAD_PREFIXES
        finally:
            sys.path.pop(0)
    return BROAD_PREFIXES


def _hits(changed: list[str], rel) -> list[str]:
    if isinstance(rel, tuple):
        return [c for c in changed if c.startswith(rel)]
    return [c for c in changed if c in rel]


def staleness(proj: Path, state_dir: Path, services=DEFAULT_SERVICES, systemctl: str = "systemctl",
              now: datetime | None = None, max_age_h: float = MAX_AGE_H) -> list[dict]:
    now = now or _now()
    decisions = load_decisions(proj / "logs" / "vps_deploy_decisions.jsonl")
    head = _git(proj, "rev-parse", "HEAD") or ""
    rows = []
    for svc in services:
        start = service_start(svc, systemctl)
        if start is None:
            rows.append({"service": svc, "state": "NOT_RUNNING", "alarm": False})
            continue
        sha, how = sha_at(proj, start, decisions)
        if not sha:
            rows.append({"service": svc, "state": "UNKNOWN", "alarm": False, "start": _iso(start),
                         "detail": "could not resolve the box HEAD at process start"})
            continue
        changed = (_git(proj, "diff", "--name-only", sha, head) or "").splitlines() if sha != head else []
        hits = _hits(changed, relevant_files(proj, svc))
        row = {"service": svc, "start": _iso(start), "sha_running": sha[:8], "sha_head": head[:8],
               "sha_source": how, "stale_files": hits[:6], "n_stale_files": len(hits)}
        if not hits:
            row.update(state="CURRENT", alarm=False)
        else:
            t0 = _git(proj, "log", "--reverse", "--format=%ct", f"{sha}..{head}", "--", *hits[:50])
            first = int(t0.splitlines()[0]) if t0 else None
            age_h = (now.timestamp() - first) / 3600 if first else None
            row.update(state="STALE", age_h=round(age_h, 1) if age_h is not None else None,
                       alarm=bool(age_h is None or age_h > max_age_h))
        rows.append(row)
    return rows


# ----- check -----------------------------------------------------------------------------------------
def check(proj: Path, state_dir: Path, systemctl: str, max_age_h: float, now: datetime | None = None) -> list[str]:
    now = now or _now()
    out = []
    st = _read_json(status_path(state_dir))
    if not st:
        out.append("UNKNOWN deploy status: no status file yet (written by the next deploy tick)")
    elif st.get("ok"):
        out.append(f"OK deploy status: {st['outcome']} at {st['ts']}")
    else:
        since = _parse_iso(st.get("fail_since") or st.get("ts", "")) or now
        fail_s = (now - since).total_seconds()
        if st.get("outcome") == "fetch_failed" and fail_s < FETCH_FAIL_GRACE_S:
            out.append(f"OK deploy status: fetch failing {int(fail_s // 60)} min (inside {FETCH_FAIL_GRACE_S // 60} min grace)")
        else:
            out.append(f"ALARM deploy {st.get('outcome')} since {st.get('fail_since')} "
                       f"(last ok {st.get('last_ok_ts')}): {st.get('detail')}")
    mk = _read_json(marker_path(state_dir))
    if mk:
        since = _parse_iso(mk.get("since", "")) or now
        age_h = (now - since).total_seconds() / 3600
        tag = "ALARM" if age_h > max_age_h else "OK"
        out.append(f"{tag} t4-mlb restart PENDING {age_h:.1f}h (skipped {mk.get('last_skip')}: {mk.get('verdict')}); "
                   f"retried each tick, fires at the first no-live-game tick")
    for r in staleness(proj, state_dir, systemctl=systemctl, now=now, max_age_h=max_age_h):
        svc = r["service"]
        if r["state"] == "CURRENT":
            out.append(f"OK {svc} runs box HEAD code ({r['sha_head']}; started {r['start']})")
        elif r["state"] == "STALE":
            out.append(f"{'ALARM' if r['alarm'] else 'OK'} {svc} runs {r['sha_running']}, box HEAD {r['sha_head']}: "
                       f"{r['n_stale_files']} file(s) it uses changed ({', '.join(r['stale_files'][:3])}), "
                       f"{r.get('age_h')}h old (alarm > {max_age_h:g}h)")
        elif r["state"] == "NOT_RUNNING":
            out.append(f"OK {svc} not running (no code to be stale)")
        else:
            out.append(f"UNKNOWN {svc}: {r.get('detail')}")
    return out


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--proj", default=os.environ.get("PMBOT_DIR", "/opt/prediction-market-bot"))
    ap.add_argument("--state-dir", default=os.environ.get("PMBOT_STATE_DIR", "/var/lib/pmbot-deploy"))
    ap.add_argument("--systemctl", default=os.environ.get("PMBOT_SYSTEMCTL", "systemctl"))
    sub = ap.add_subparsers(dest="cmd", required=True)
    m = sub.add_parser("marker")
    m.add_argument("action", choices=["set", "clear", "show"])
    m.add_argument("--verdict", default="")
    m.add_argument("--sha", default="")
    m.add_argument("--reason", default="")
    s = sub.add_parser("status")
    s.add_argument("--outcome", required=True)
    s.add_argument("--detail", default="")
    c = sub.add_parser("check")
    c.add_argument("--max-age-h", type=float, default=MAX_AGE_H)
    a = ap.parse_args(argv)
    state, proj = Path(a.state_dir), Path(a.proj)
    if a.cmd == "marker":
        if a.action == "set":
            marker_set(state, a.verdict, a.sha, a.reason)
        elif a.action == "clear":
            marker_clear(state)
        else:
            print(json.dumps(_read_json(marker_path(state))))
    elif a.cmd == "status":
        status_write(state, a.outcome, a.detail)
    else:
        print("DEPLOY TRUTH (W72.3 / GG-661, GG-668: merge != deploy != activation; alarm-only):")
        for ln in check(proj, state, a.systemctl, a.max_age_h):
            print("  " + ln)
    return 0


if __name__ == "__main__":
    sys.exit(main())
